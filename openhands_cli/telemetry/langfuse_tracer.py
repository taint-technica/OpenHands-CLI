from __future__ import annotations

import json
import logging
import os
import re
import uuid
from atexit import register as _atexit_register
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from typing import Any

from dotenv import load_dotenv

from openhands_cli.locations import get_work_dir
from openhands_cli.utils import derive_trace_user_id


load_dotenv()
logger = logging.getLogger(__name__)

_ENV_ENABLED = "LANGFUSE_ENABLED"
_ENV_PUBLIC_KEY = "LANGFUSE_PUBLIC_KEY"
_ENV_SECRET_KEY = "LANGFUSE_SECRET_KEY"
_ENV_HOST = "LANGFUSE_HOST"

_DEFAULT_HOST = "https://cloud.langfuse.com"


def is_langfuse_enabled() -> bool:
    flag = os.environ.get(_ENV_ENABLED, "").strip().lower()
    has_keys = bool(os.environ.get(_ENV_PUBLIC_KEY) and os.environ.get(_ENV_SECRET_KEY))
    return flag in ("1", "true", "yes") and has_keys


def _now_dt() -> datetime:
    return datetime.now(UTC)


def _new_id() -> str:
    return str(uuid.uuid4())


def _get_project_path() -> str:
    return os.path.abspath(get_work_dir())


class _LangfuseRestClient:
    def __init__(self, public_key: str, secret_key: str, host: str) -> None:
        from langfuse.api.client import FernLangfuse

        self._client = FernLangfuse(
            base_url=host.rstrip("/"),
            username=public_key,
            password=secret_key,
        )
        self._executor = ThreadPoolExecutor(
            max_workers=2, thread_name_prefix="langfuse-ingest"
        )
        logger.debug("Langfuse REST client ready (host=%s)", host)

    def create_trace(
        self,
        *,
        trace_id: str,
        name: str,
        metadata: dict[str, Any] | None = None,
        session_id: str | None = None,
        tags: list[str] | None = None,
        user_id: str | None = None,
    ) -> None:
        from langfuse.api import IngestionEvent_TraceCreate, TraceBody

        ts = _now_dt()
        body = TraceBody(
            id=trace_id,
            name=name,
            timestamp=ts,
            metadata=metadata,
            sessionId=session_id,
            tags=tags,
            userId=user_id,
        )
        self._ingest(
            [
                IngestionEvent_TraceCreate(
                    id=_new_id(), timestamp=ts.isoformat(), body=body
                )
            ]
        )

    def start_span(
        self,
        *,
        trace_id: str,
        name: str,
        input: Any = None,
        metadata: dict[str, Any] | None = None,
        parent_observation_id: str | None = None,
    ) -> _SpanHandle:
        from langfuse.api import CreateSpanBody, IngestionEvent_SpanCreate

        span_id = _new_id()
        ts = _now_dt()
        body = CreateSpanBody(
            id=span_id,
            traceId=trace_id,
            name=name,
            startTime=ts,
            input=input,
            metadata=metadata,
            parentObservationId=parent_observation_id,
        )
        self._ingest(
            [
                IngestionEvent_SpanCreate(
                    id=_new_id(), timestamp=ts.isoformat(), body=body
                )
            ]
        )
        return _SpanHandle(client=self, span_id=span_id)

    def start_generation(
        self,
        *,
        trace_id: str,
        name: str,
        model: str = "unknown",
        input: Any = None,
        output: Any = None,
        usage_details: dict[str, int] | None = None,
        cost_details: dict[str, float] | None = None,
        metadata: dict[str, Any] | None = None,
        parent_observation_id: str | None = None,
    ) -> _GenerationHandle:
        from langfuse.api import CreateGenerationBody, IngestionEvent_GenerationCreate
        from langfuse.api.resources.commons.types.usage import Usage

        gen_id = _new_id()
        ts = _now_dt()

        usage_payload: dict[str, Any] | None = None
        if usage_details is not None:
            usage_payload = dict(usage_details)
        if cost_details is not None:
            usage_payload = usage_payload or {}
            if "input" in cost_details:
                usage_payload["input_cost"] = cost_details["input"]
            if "output" in cost_details:
                usage_payload["output_cost"] = cost_details["output"]
            if "total" in cost_details:
                usage_payload["total_cost"] = cost_details["total"]

        usage_obj = Usage(**usage_payload) if usage_payload is not None else None

        body = CreateGenerationBody(
            id=gen_id,
            traceId=trace_id,
            name=name,
            model=model,
            startTime=ts,
            input=input,
            output=output,
            usage=usage_obj,
            metadata=metadata,
            parentObservationId=parent_observation_id,
        )
        self._ingest(
            [
                IngestionEvent_GenerationCreate(
                    id=_new_id(), timestamp=ts.isoformat(), body=body
                )
            ]
        )
        return _GenerationHandle(client=self, gen_id=gen_id)

    def _ingest(self, events: list[Any]) -> None:
        self._executor.submit(self._send, events)

    def _send(self, events: list[Any]) -> None:
        try:
            resp = self._client.ingestion.batch(batch=events)
            logger.debug("Langfuse ingestion OK (%d event(s))", len(events))
            if resp.errors:
                for err in resp.errors:
                    logger.debug("Langfuse ingestion error: %s", err)
        except Exception as exc:  # noqa: BLE001
            logger.debug("Langfuse ingestion send error: %s", exc)

    def flush(self) -> None:
        self._executor.shutdown(wait=True)
        self._executor = ThreadPoolExecutor(
            max_workers=2, thread_name_prefix="langfuse-ingest"
        )

    def shutdown(self) -> None:
        self._executor.shutdown(wait=True)


class _SpanHandle:
    def __init__(self, client: _LangfuseRestClient, span_id: str) -> None:
        self._client = client
        self._id = span_id
        self._output: Any = None

    def update(self, output: Any = None) -> None:
        self._output = output

    def end(self) -> None:
        from langfuse.api import IngestionEvent_SpanUpdate, UpdateSpanBody

        ts = _now_dt()
        body = UpdateSpanBody(id=self._id, endTime=ts, output=self._output)
        self._client._ingest(
            [
                IngestionEvent_SpanUpdate(
                    id=_new_id(), timestamp=ts.isoformat(), body=body
                )
            ]
        )


class _GenerationHandle:
    def __init__(self, client: _LangfuseRestClient, gen_id: str) -> None:
        self._client = client
        self._id = gen_id

    def end(self) -> None:
        from langfuse.api import IngestionEvent_GenerationUpdate, UpdateGenerationBody

        ts = _now_dt()
        body = UpdateGenerationBody(id=self._id, endTime=ts)
        self._client._ingest(
            [
                IngestionEvent_GenerationUpdate(
                    id=_new_id(), timestamp=ts.isoformat(), body=body
                )
            ]
        )


# Module-level singleton
_rest_client: _LangfuseRestClient | None = None


def _get_rest_client() -> _LangfuseRestClient | None:
    global _rest_client
    if _rest_client is not None:
        return _rest_client
    try:
        client = _LangfuseRestClient(
            public_key=os.environ[_ENV_PUBLIC_KEY],
            secret_key=os.environ[_ENV_SECRET_KEY],
            host=os.environ.get(_ENV_HOST, _DEFAULT_HOST),
        )
        _rest_client = client
        _atexit_register(client.shutdown)
        return _rest_client
    except ImportError:
        logger.warning(
            "langfuse package not installed. "
            'Install with: pip install "openhands[langfuse]"'
        )
        return None
    except Exception as exc:
        logger.warning("Langfuse init failed: %s", exc)
        return None


class _LangfuseConversationTracer:
    def __init__(self, conversation_id: str, lf_client: _LangfuseRestClient) -> None:
        self._lf = lf_client
        self._conversation_id = conversation_id
        self._trace_id = conversation_id.replace("-", "").lower()[:32].ljust(32, "0")
        self._project_path = _get_project_path()
        self._project_name = os.path.basename(self._project_path.rstrip("/"))
        self._trace_source = (
            os.environ.get("OPENHANDS_TRACE_SOURCE", "openhands").strip() or "openhands"
        )
        self._trace_flow = (
            os.environ.get("OPENHANDS_TRACE_FLOW", "chat").strip() or "chat"
        )
        self._trace_user_id = self._detect_trace_user_id()
        self._default_model_name = self._detect_default_model_name()
        # Keep tags dedicated to project-only filtering (Langfuse UI expects
        # `project:<name>` tag format).
        trace_tags = [f"project:{self._project_name}"]
        trace_metadata = {
            "conversation_id": conversation_id,
            "project_path": self._project_path,
            "project_name": self._project_name,
            "project": self._project_name,
            "source": self._trace_source,
            "flow": self._trace_flow,
        }

        self._lf.create_trace(
            trace_id=self._trace_id,
            name="openhands",
            metadata=trace_metadata,
            session_id=self._project_path,
            tags=trace_tags,
            user_id=self._trace_user_id,
        )
        self._pending_tool_spans: dict[str, _SpanHandle] = {}

    def __call__(self, event: Any) -> None:
        try:
            self._dispatch(event)
        except Exception as exc:  # noqa: BLE001
            logger.debug(
                "Langfuse tracer error (event=%s): %s", type(event).__name__, exc
            )

    def _dispatch(self, event: Any) -> None:
        from openhands.sdk.event import (
            ActionEvent,
            LLMCompletionLogEvent,
            MessageEvent,
            ObservationEvent,
        )

        if isinstance(event, LLMCompletionLogEvent):
            self._on_llm_completion_log(event)
        elif isinstance(event, MessageEvent):
            self._on_message(event)
        elif isinstance(event, ActionEvent):
            self._on_action(event)
        elif isinstance(event, ObservationEvent):
            self._on_observation(event)

    def _on_message(self, event: Any) -> None:
        text = self._extract_message_text(event.llm_message)
        if event.source == "user":
            span = self._lf.start_span(
                trace_id=self._trace_id,
                name="user-message",
                input=text,
                metadata={"event_id": event.id},
            )
            span.end()
        else:
            gen = self._lf.start_generation(
                trace_id=self._trace_id,
                name="agent-message",
                model=self._default_model_name,
                output={"role": "assistant", "content": text},
                metadata={
                    "event_id": event.id,
                    "llm_response_id": getattr(event, "llm_response_id", None),
                    "model_name": self._default_model_name,
                },
            )
            gen.end()

    def _on_action(self, event: Any) -> None:
        tool_args: dict[str, Any] = {}
        if event.action is not None:
            try:
                tool_args = event.action.model_dump(exclude_none=True)
            except Exception:  # noqa: BLE001
                pass

        span = self._lf.start_span(
            trace_id=self._trace_id,
            name=f"tool:{event.tool_name}",
            input={"tool": event.tool_name, "args": tool_args},
            metadata={
                "event_id": event.id,
                "llm_response_id": getattr(event, "llm_response_id", None),
                "tool_call_id": str(getattr(event, "tool_call_id", "")),
            },
        )
        self._pending_tool_spans[event.id] = span

    def _on_observation(self, event: Any) -> None:
        action_id: str | None = getattr(event, "action_id", None)
        span = (
            self._pending_tool_spans.pop(action_id, None)
            if action_id is not None
            else None
        )

        result_parts: list[str] = []
        try:
            for item in event.observation.to_llm_content or []:
                if hasattr(item, "text"):
                    result_parts.append(item.text)
        except Exception:  # noqa: BLE001
            pass
        result = "\n".join(result_parts)

        if span is not None:
            span.update(output=result)
            span.end()
        else:
            orphan = self._lf.start_span(
                trace_id=self._trace_id,
                name=f"tool-result:{getattr(event, 'tool_name', 'unknown')}",
                metadata={"action_id": str(action_id or "")},
            )
            orphan.update(output=result)
            orphan.end()

    def _on_llm_completion_log(self, event: Any) -> None:
        try:
            log: dict[str, Any] = json.loads(event.log_data)
        except (json.JSONDecodeError, TypeError):
            return

        usage_raw: dict[str, Any] = log.get("usage") or {}
        prompt_tokens: int = usage_raw.get("prompt_tokens", 0)
        completion_tokens: int = usage_raw.get("completion_tokens", 0)
        total_tokens: int = usage_raw.get(
            "total_tokens", prompt_tokens + completion_tokens
        )

        cost: float | None = log.get("response_cost")
        if cost is None:
            cost = log.get("_response_cost")
        if cost is None:
            _hidden = log.get("_hidden_params")
            hidden: dict[str, Any] = _hidden if isinstance(_hidden, dict) else {}
            cost = hidden.get("response_cost")

        input_messages = log.get("messages")
        if input_messages is None:
            input_messages = log.get("prompt") or []

        output_msg: Any = None
        choices: list[Any] = log.get("choices") or []
        if choices and isinstance(choices[0], dict):
            output_msg = choices[0].get("message")

        resolved_model = self._resolve_model_name(
            log,
            event_model_name=getattr(event, "model_name", None),
        )
        if resolved_model == "unknown":
            resolved_model = self._default_model_name

        trace_user_id = self._extract_trace_user_id(log) or self._trace_user_id

        gen = self._lf.start_generation(
            trace_id=self._trace_id,
            name="llm-call",
            model=resolved_model,
            input=input_messages,
            output=output_msg,
            usage_details={
                "input": prompt_tokens,
                "output": completion_tokens,
                "total": total_tokens,
            },
            cost_details=({"total": cost} if cost is not None else None),
            metadata={
                "usage_id": event.usage_id,
                "response_cost_usd": cost,
                "model_name": resolved_model,
                "conversation_id": self._conversation_id,
                "project_path": self._project_path,
                "project_name": self._project_name,
                "project": self._project_name,
                "source": self._trace_source,
                "flow": self._trace_flow,
                "trace_user_id": trace_user_id,
            },
        )
        gen.end()

    @staticmethod
    def _resolve_model_name(
        log: dict[str, Any],
        event_model_name: str | None = None,
        filename: str | None = None,
    ) -> str:
        """Resolve model name from the richest available telemetry source."""

        for candidate in (
            _LangfuseConversationTracer._normalize_model_name(event_model_name),
            _LangfuseConversationTracer._extract_model_from_dict(
                log, ("model", "model_name", "custom_llm_provider")
            ),
            _LangfuseConversationTracer._extract_model_from_hidden_params(log),
            _LangfuseConversationTracer._extract_model_from_request_sections(log),
            _LangfuseConversationTracer._extract_model_from_filename(filename),
        ):
            if candidate is not None:
                return candidate

        return "unknown"

    @staticmethod
    def _normalize_model_name(value: Any) -> str | None:
        if not isinstance(value, str):
            return None
        stripped = value.strip()
        if not stripped or stripped.lower() == "unknown":
            return None
        return stripped

    @staticmethod
    def _extract_model_from_dict(
        data: dict[str, Any], keys: tuple[str, ...]
    ) -> str | None:
        for key in keys:
            model = _LangfuseConversationTracer._normalize_model_name(data.get(key))
            if model is not None:
                return model
        return None

    @staticmethod
    def _extract_model_from_hidden_params(log: dict[str, Any]) -> str | None:
        hidden = log.get("_hidden_params")
        if not isinstance(hidden, dict):
            return None
        return _LangfuseConversationTracer._extract_model_from_dict(
            hidden,
            ("model", "model_name", "hf_model_name"),
        )

    @staticmethod
    def _extract_model_from_request_sections(log: dict[str, Any]) -> str | None:
        for section_name in ("litellm_params", "request", "kwargs"):
            section = log.get(section_name)
            if isinstance(section, dict):
                model = _LangfuseConversationTracer._extract_model_from_dict(
                    section,
                    ("model", "model_name"),
                )
                if model is not None:
                    return model
        return None

    @staticmethod
    def _extract_model_from_filename(filename: str | None) -> str | None:
        if not filename:
            return None
        base = filename.removesuffix(".json")
        base = re.sub(r"-\d+\.\d+-[0-9a-f]+(?:-.+)?$", "", base)
        if not base:
            return None
        return _LangfuseConversationTracer._normalize_model_name(
            base.replace("__", "/")
        )

    @staticmethod
    def _extract_message_text(message: Any) -> str:
        parts: list[str] = []
        try:
            for item in message.content or []:
                if hasattr(item, "text") and item.text:
                    parts.append(item.text)
        except Exception:  # noqa: BLE001
            pass
        return "\n".join(parts)

    def _on_llm_log(self, filename: str, log_data: str) -> None:
        try:
            log: dict[str, Any] = json.loads(log_data)
        except (json.JSONDecodeError, TypeError):
            return

        usage_raw: dict[str, Any] = log.get("usage_summary") or {}
        prompt_tokens: int = usage_raw.get("prompt_tokens", 0)
        completion_tokens: int = usage_raw.get("completion_tokens", 0)
        total_tokens: int = prompt_tokens + completion_tokens

        cost: float | None = log.get("cost")

        input_messages = log.get("messages")
        if input_messages is None:
            input_messages = log.get("prompt") or []

        output_msg: Any = None
        resp = log.get("response")
        if isinstance(resp, dict):
            choices: list[Any] = resp.get("choices") or []
            if choices and isinstance(choices[0], dict):
                output_msg = choices[0].get("message")

        model_name = self._resolve_model_name(log, filename=filename)
        if model_name == "unknown":
            model_name = self._default_model_name

        try:
            gen = self._lf.start_generation(
                trace_id=self._trace_id,
                name="llm-call",
                model=model_name,
                input=input_messages,
                output=output_msg,
                usage_details={
                    "input": prompt_tokens,
                    "output": completion_tokens,
                    "total": total_tokens,
                },
                cost_details=({"total": cost} if cost is not None else None),
                metadata={
                    "response_cost_usd": cost,
                    "conversation_id": self._conversation_id,
                    "project_path": self._project_path,
                    "project_name": self._project_name,
                    "source": "llm-telemetry-hook",
                },
            )
            gen.end()
        except Exception as exc:  # noqa: BLE001
            logger.debug("Langfuse LLM log error: %s", exc)

    def enable_llm_hooks(self, agent: Any) -> None:
        """Enable ``log_completions`` on every LLM owned by *agent*."""
        try:
            for llm in agent.get_all_llms():
                object.__setattr__(llm, "log_completions", True)
                llm._telemetry.log_enabled = True
                llm._telemetry.set_log_completions_callback(self._on_llm_log)
        except Exception as exc:  # noqa: BLE001
            logger.debug("Failed to hook LLM telemetry: %s", exc)

    @staticmethod
    def _detect_default_model_name() -> str:
        """Best-effort fallback model name for telemetry events missing model."""
        try:
            from openhands_cli.locations import AGENT_SETTINGS_PATH, get_persistence_dir

            settings_path = os.path.join(get_persistence_dir(), AGENT_SETTINGS_PATH)
            with open(settings_path) as f:
                settings = json.load(f)
            persisted_model = _LangfuseConversationTracer._normalize_model_name(
                settings.get("llm", {}).get("model")
            )
            if persisted_model is not None:
                return persisted_model
        except Exception:
            pass

        env_model = _LangfuseConversationTracer._normalize_model_name(
            os.environ.get("LLM_MODEL")
        )
        if env_model is not None:
            return env_model

        return "unknown"

    @staticmethod
    def _detect_trace_user_id() -> str | None:
        # 1) Explicit override from env
        value = os.environ.get("OPENHANDS_TRACE_USER_ID")
        if value is not None:
            value = value.strip()
            if value:
                return value

        # 1.5) Derived value injected by AgentStore from active API key/alias.
        value = os.environ.get("OPENHANDS_TRACE_USER_ID_DERIVED")
        if value is not None:
            value = value.strip()
            if value:
                return value

        # 2) Derive from persisted agent API key (one key == one user)
        try:
            from openhands_cli.locations import AGENT_SETTINGS_PATH, get_persistence_dir

            settings_path = os.path.join(get_persistence_dir(), AGENT_SETTINGS_PATH)
            with open(settings_path) as f:
                settings = json.load(f)
            api_key = settings.get("llm", {}).get("api_key")
            base_url = settings.get("llm", {}).get("base_url")
            if isinstance(api_key, str):
                return derive_trace_user_id(api_key, base_url)
        except Exception:
            pass

        return None

    @staticmethod
    def _extract_trace_user_id(log: dict[str, Any]) -> str | None:
        """Best-effort extraction from LiteLLM completion log payload."""
        candidates: list[Any] = []
        for key in ("metadata", "litellm_extra_body", "extra_body"):
            block = log.get(key)
            if isinstance(block, dict):
                candidates.append(block)

        for block in candidates:
            # Direct metadata payload
            if "trace_user_id" in block and isinstance(block["trace_user_id"], str):
                value = block["trace_user_id"].strip()
                if value:
                    return value

            meta = block.get("metadata")
            if isinstance(meta, dict):
                value = meta.get("trace_user_id")
                if isinstance(value, str) and value.strip():
                    return value.strip()

        return None


def make_langfuse_callback(conversation_id: str | Any) -> Callable[[Any], None] | None:
    if not is_langfuse_enabled():
        return None

    client = _get_rest_client()
    if client is None:
        return None

    tracer = _LangfuseConversationTracer(
        conversation_id=str(conversation_id),
        lf_client=client,
    )
    return tracer
