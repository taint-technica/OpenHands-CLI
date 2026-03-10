"""Tests for openhands_cli.telemetry.langfuse_tracer.

Uses the official Langfuse REST API client (FernLangfuse). All HTTP calls
are intercepted with ``unittest.mock`` so no real server is needed.
"""

from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_env(
    *,
    enabled: str = "true",
    public_key: str = "pk-lf-test",
    secret_key: str = "sk-lf-test",
    host: str = "https://langfuse.example.com",
) -> dict[str, str]:
    return {
        "LANGFUSE_ENABLED": enabled,
        "LANGFUSE_PUBLIC_KEY": public_key,
        "LANGFUSE_SECRET_KEY": secret_key,
        "LANGFUSE_HOST": host,
    }


def _make_rest_client_mock() -> tuple[MagicMock, MagicMock, MagicMock]:
    """Return (rest_client, span_handle, gen_handle)."""
    rest_client = MagicMock()
    span_handle = MagicMock()
    gen_handle = MagicMock()
    rest_client.start_span.return_value = span_handle
    rest_client.start_generation.return_value = gen_handle
    return rest_client, span_handle, gen_handle


# ---------------------------------------------------------------------------
# is_langfuse_enabled
# ---------------------------------------------------------------------------


class TestIsLangfuseEnabled:
    def test_enabled_when_all_set(self):
        from openhands_cli.telemetry.langfuse_tracer import is_langfuse_enabled

        with patch.dict(os.environ, _make_env()):
            assert is_langfuse_enabled() is True

    @pytest.mark.parametrize("flag", ["1", "true", "True", "TRUE", "yes"])
    def test_truthy_flags(self, flag: str):
        from openhands_cli.telemetry.langfuse_tracer import is_langfuse_enabled

        with patch.dict(os.environ, _make_env(enabled=flag)):
            assert is_langfuse_enabled() is True

    @pytest.mark.parametrize("flag", ["false", "0", "", "no", "off"])
    def test_falsy_flags(self, flag: str):
        from openhands_cli.telemetry.langfuse_tracer import is_langfuse_enabled

        with patch.dict(os.environ, _make_env(enabled=flag)):
            assert is_langfuse_enabled() is False

    def test_disabled_when_public_key_missing(self):
        from openhands_cli.telemetry.langfuse_tracer import is_langfuse_enabled

        with patch.dict(os.environ, _make_env()):
            os.environ.pop("LANGFUSE_PUBLIC_KEY", None)
            assert is_langfuse_enabled() is False

    def test_disabled_when_secret_key_missing(self):
        from openhands_cli.telemetry.langfuse_tracer import is_langfuse_enabled

        with patch.dict(os.environ, _make_env()):
            os.environ.pop("LANGFUSE_SECRET_KEY", None)
            assert is_langfuse_enabled() is False


# ---------------------------------------------------------------------------
# _LangfuseConversationTracer
# ---------------------------------------------------------------------------


class TestLangfuseConversationTracer:
    def _make_tracer(self):
        from openhands_cli.telemetry.langfuse_tracer import _LangfuseConversationTracer

        rest_client, span_handle, gen_handle = _make_rest_client_mock()
        tracer = _LangfuseConversationTracer(
            conversation_id="11111111-1111-1111-1111-111111111111",
            lf_client=rest_client,
        )
        return tracer, rest_client, span_handle, gen_handle

    def test_trace_created_on_init(self):
        _, rest_client, _, _ = self._make_tracer()
        rest_client.create_trace.assert_called_once()
        call_kwargs = rest_client.create_trace.call_args.kwargs
        assert call_kwargs["trace_id"] == "1" * 32
        assert call_kwargs["metadata"]["project_path"]
        assert call_kwargs["metadata"]["project_name"]
        assert call_kwargs["session_id"] == call_kwargs["metadata"]["project_path"]
        assert call_kwargs["tags"] == [
            f"project:{call_kwargs['metadata']['project_name']}"
        ]

    def _make_message_event(self, source: str, text: str) -> MagicMock:
        evt = MagicMock()
        evt.source = source
        evt.id = "evt-1"
        content_item = MagicMock()
        content_item.text = text
        evt.llm_message.content = [content_item]
        return evt

    def test_user_message_creates_span(self):
        tracer, rest_client, span_handle, _ = self._make_tracer()
        evt = self._make_message_event("user", "hello")

        tracer._on_message(evt)

        rest_client.start_span.assert_called_once()
        assert rest_client.start_span.call_args.kwargs["name"] == "user-message"
        span_handle.end.assert_called_once()

    def test_agent_message_creates_generation(self):
        tracer, rest_client, _, gen_handle = self._make_tracer()
        evt = self._make_message_event("agent", "here is my answer")

        tracer._on_message(evt)

        rest_client.start_generation.assert_called_once()
        assert rest_client.start_generation.call_args.kwargs["name"] == "agent-message"
        gen_handle.end.assert_called_once()

    def test_action_opens_pending_span(self):
        tracer, rest_client, _, _ = self._make_tracer()

        action_evt = MagicMock()
        action_evt.id = "act-1"
        action_evt.tool_name = "bash"
        action_evt.action = None

        tracer._on_action(action_evt)

        rest_client.start_span.assert_called_once()
        assert "act-1" in tracer._pending_tool_spans

    def test_observation_closes_pending_span(self):
        tracer, _, span_handle, _ = self._make_tracer()

        action_evt = MagicMock()
        action_evt.id = "act-1"
        action_evt.tool_name = "bash"
        action_evt.action = None
        tracer._on_action(action_evt)

        obs_evt = MagicMock()
        obs_evt.action_id = "act-1"
        content = MagicMock()
        content.text = "output text"
        obs_evt.observation.to_llm_content = [content]

        tracer._on_observation(obs_evt)

        span_handle.update.assert_called_once_with(output="output text")
        span_handle.end.assert_called_once()
        assert "act-1" not in tracer._pending_tool_spans

    def test_orphan_observation_creates_standalone_span(self):
        tracer, rest_client, span_handle, _ = self._make_tracer()

        obs_evt = MagicMock()
        obs_evt.action_id = "unknown-id"
        obs_evt.observation.to_llm_content = []

        tracer._on_observation(obs_evt)

        rest_client.start_span.assert_called_once()
        span_handle.update.assert_called_once()
        span_handle.end.assert_called_once()

    def test_llm_completion_log_creates_generation(self):
        tracer, rest_client, _, gen_handle = self._make_tracer()

        log_data = json.dumps(
            {
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 20,
                    "total_tokens": 30,
                },
                "response_cost": 0.0012,
                "messages": [{"role": "user", "content": "hi"}],
                "choices": [{"message": {"role": "assistant", "content": "hello"}}],
            }
        )
        evt = MagicMock()
        evt.log_data = log_data
        evt.model_name = "anthropic/claude-3-haiku"
        evt.usage_id = "u-1"

        tracer._on_llm_completion_log(evt)

        rest_client.start_generation.assert_called_once()
        kwargs = rest_client.start_generation.call_args.kwargs
        assert kwargs["model"] == "anthropic/claude-3-haiku"
        assert kwargs["usage_details"]["input"] == 10
        assert abs(kwargs["cost_details"]["total"] - 0.0012) < 1e-9
        gen_handle.end.assert_called_once()

    def test_unknown_event_type_is_ignored(self):
        tracer, rest_client, _, _ = self._make_tracer()

        tracer(MagicMock(spec=object))  # should not raise

        rest_client.start_span.assert_not_called()
        rest_client.start_generation.assert_not_called()


# ---------------------------------------------------------------------------
# make_langfuse_callback  (public factory)
# ---------------------------------------------------------------------------


class TestMakeLangfuseCallback:
    def test_returns_none_when_disabled(self):
        import openhands_cli.telemetry.langfuse_tracer as mod
        from openhands_cli.telemetry.langfuse_tracer import make_langfuse_callback

        with patch.dict(os.environ, _make_env(enabled="false")):
            mod._rest_client = None
            result = make_langfuse_callback("conv-123")

        assert result is None

    def test_returns_callable_when_enabled(self):
        import openhands_cli.telemetry.langfuse_tracer as mod
        from openhands_cli.telemetry.langfuse_tracer import make_langfuse_callback

        rest_client, _, _ = _make_rest_client_mock()

        with patch(
            "openhands_cli.telemetry.langfuse_tracer._LangfuseRestClient",
            return_value=rest_client,
        ):
            with patch.dict(os.environ, _make_env()):
                mod._rest_client = None
                cb = make_langfuse_callback("conv-456")

        assert callable(cb)

    def test_callback_has_enable_llm_hooks(self):
        import openhands_cli.telemetry.langfuse_tracer as mod
        from openhands_cli.telemetry.langfuse_tracer import make_langfuse_callback

        rest_client, _, _ = _make_rest_client_mock()

        with patch(
            "openhands_cli.telemetry.langfuse_tracer._LangfuseRestClient",
            return_value=rest_client,
        ):
            with patch.dict(os.environ, _make_env()):
                mod._rest_client = None
                cb = make_langfuse_callback("conv-789")

        assert hasattr(cb, "enable_llm_hooks")
