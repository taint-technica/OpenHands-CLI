"""RunnerFactory - builds ConversationRunner instances with required dependencies.

This module exists to keep ConversationManager lightweight.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import TYPE_CHECKING

from textual.message_pump import MessagePump
from textual.notifications import SeverityLevel

from openhands.sdk.event.base import Event
from openhands_cli.telemetry.langfuse_tracer import make_langfuse_callback
from openhands_cli.tui.widgets.richlog_visualizer import (
    DEFAULT_AGENT_NAME,
)


if TYPE_CHECKING:
    from openhands_cli.tui.core.conversation_runner import ConversationRunner
    from openhands_cli.tui.core.state import ConversationContainer
    from openhands_cli.tui.textual_app import OpenHandsApp
    from openhands_cli.tui.widgets.main_display import ScrollableContent


NotificationCallback = Callable[[str, str, SeverityLevel], None]
ScrollViewProvider = Callable[[], "ScrollableContent"]
AppProvider = Callable[[], "OpenHandsApp"]


class RunnerFactory:
    def __init__(
        self,
        *,
        state: ConversationContainer,
        app_provider: AppProvider,
        scroll_view_provider: ScrollViewProvider,
        json_mode: bool,
        env_overrides_enabled: bool,
        critic_disabled: bool,
    ) -> None:
        self._state = state
        self._app_provider = app_provider
        self._scroll_view_provider = scroll_view_provider
        self._json_mode = json_mode
        self._env_overrides_enabled = env_overrides_enabled
        self._critic_disabled = critic_disabled

    def create(
        self,
        conversation_id: uuid.UUID,
        *,
        message_pump: MessagePump,
        notification_callback: NotificationCallback,
    ) -> ConversationRunner:
        from openhands_cli.tui.core.conversation_runner import ConversationRunner
        from openhands_cli.tui.widgets.richlog_visualizer import ConversationVisualizer
        from openhands_cli.utils import json_callback

        app = self._app_provider()

        # Visualizer reads cli_settings directly when needed via self.cli_settings
        visualizer = ConversationVisualizer(
            self._scroll_view_provider(),
            app,
            name=DEFAULT_AGENT_NAME,
        )

        event_callback: Callable[[Event], None] | None = (
            json_callback if self._json_mode else None
        )

        # Attach Langfuse tracer if enabled (env-controlled, zero overhead when off)
        lf_callback = make_langfuse_callback(conversation_id)
        if lf_callback is not None:
            if event_callback is not None:
                _prev = event_callback

                def _combined(
                    evt: Event, _a: Callable = _prev, _b: Callable = lf_callback
                ) -> None:
                    _a(evt)
                    _b(evt)

                event_callback = _combined
            else:
                event_callback = lf_callback

        runner = ConversationRunner(
            conversation_id,
            state=self._state,
            message_pump=message_pump,
            notification_callback=notification_callback,
            visualizer=visualizer,
            event_callback=event_callback,
            env_overrides_enabled=self._env_overrides_enabled,
            critic_disabled=self._critic_disabled,
        )

        # Hook Langfuse into LLM telemetry for cost/token tracking
        # Must happen after runner.conversation is created (which has the agent)
        if lf_callback is not None and hasattr(lf_callback, "enable_llm_hooks"):
            conversation = runner.conversation
            agent = getattr(conversation, "agent", None)
            if agent is not None:
                lf_callback.enable_llm_hooks(agent)  # type: ignore[union-attr]

        # Attach conversation to state for metrics reading
        self._state.attach_conversation_state(runner.conversation.state)
        return runner
