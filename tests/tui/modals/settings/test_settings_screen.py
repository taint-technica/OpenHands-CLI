"""Tests for SettingsScreen wiring.

These tests were updated to match the current Settings UI contract:
`SettingsTab` renders proxy/model/api-key fields and the dependency chain
enables/disables downstream fields based on fetched models.
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest
from textual.app import App, ComposeResult

from openhands.sdk import Agent, LLM
from openhands_cli.tui.modals.settings.settings_screen import SettingsScreen
import openhands_cli.tui.modals.settings.settings_screen as ss


class InMemoryAgentStore:
    """In-memory AgentStore replacement for UI tests."""

    def __init__(self) -> None:
        self._agent: Agent | None = None

    def save(self, agent: Agent) -> None:
        self._agent = agent

    def load_from_disk(self) -> Agent | None:
        return self._agent

    def load_or_create(
        self,
        session_id: str | None = None,
        *,
        env_overrides_enabled: bool = False,
        critic_disabled: bool = False,
    ) -> Agent | None:
        # `env_overrides_enabled` is accepted for backwards compatibility with
        # older test fixtures; it is not used by this in-memory store.
        return self._agent


class SettingsTestApp(App):
    """Minimal app that pushes SettingsScreen on mount."""

    def __init__(self, store: InMemoryAgentStore) -> None:
        super().__init__()
        self.settings_screen = SettingsScreen()
        self._store = store

    def compose(self) -> ComposeResult:
        yield from ()

    def on_mount(self) -> None:
        self.push_screen(self.settings_screen)


@pytest.fixture
def fake_agent_store(monkeypatch) -> InMemoryAgentStore:
    store = InMemoryAgentStore()
    monkeypatch.setattr(ss, "AgentStore", lambda: store)
    monkeypatch.setattr(
        "openhands_cli.tui.modals.settings.settings_screen.AgentStore",
        lambda: store,
    )
    return store


@pytest.fixture
async def app(fake_agent_store: InMemoryAgentStore):
    app = SettingsTestApp(fake_agent_store)
    async with app.run_test() as pilot:
        yield app, pilot


def _make_agent(
    *,
    model: str,
    api_key: str | None,
    base_url: str | None,
) -> Agent:
    return Agent(
        llm=LLM(
            model=model,
            api_key=api_key,
            base_url=base_url,
            usage_id="agent",
        )
    )


def test_is_initial_setup_required(
    fake_agent_store: InMemoryAgentStore,
):
    fake_agent_store._agent = None
    assert SettingsScreen.is_initial_setup_required() is True

    fake_agent_store.save(_make_agent(model="openai/gpt-4o", api_key="k", base_url=None))
    assert SettingsScreen.is_initial_setup_required() is False


@pytest.mark.asyncio
async def test_load_current_settings_populates_proxy_model_and_api_placeholder(
    app,
    fake_agent_store: InMemoryAgentStore,
):
    app_obj, _ = app
    agent = _make_agent(
        model="openai/gpt-4o-mini",
        api_key="test-api-key",
        base_url="https://api.example.com/v1",
    )
    fake_agent_store.save(agent)

    screen = app_obj.settings_screen
    screen.current_agent = fake_agent_store.load_from_disk()
    screen._load_current_settings()

    assert screen.proxy_url_input.value == "https://api.example.com/v1"
    assert screen.model_select.value == "openai/gpt-4o-mini"
    assert screen.api_key_input.value == ""
    assert "Current:" in screen.api_key_input.placeholder
    assert "leave empty to keep current" in screen.api_key_input.placeholder


@pytest.mark.asyncio
async def test_dependency_chain_enables_fields_when_fetched_models_present(app):
    app_obj, _ = app
    screen = app_obj.settings_screen

    # Precondition: model_select.value is set, but fetched_models empty => disabled
    screen.fetched_models = []
    selected_model = "openai/gpt-4o-mini"
    screen.model_select.set_options([(selected_model, selected_model)])
    screen.model_select.value = selected_model
    screen.proxy_url_input.value = screen.proxy_url_input.value or "http://localhost:4000"
    screen._update_field_dependencies()
    assert screen.model_select.disabled is True
    assert screen.memory_select.disabled is True

    # When fetched_models is provided, downstream fields should enable.
    screen.fetched_models = [selected_model]
    screen._update_field_dependencies()
    assert screen.model_select.disabled is False
    assert screen.memory_select.disabled is False
    assert screen.timeout_input.disabled is False


@pytest.mark.asyncio
async def test_fetch_models_requires_api_key(app):
    app_obj, _ = app
    screen = app_obj.settings_screen

    screen.proxy_url_input.value = "http://localhost:4000"
    screen.api_key_input.value = ""
    screen._show_message = Mock()

    await screen._on_fetch_models_button_pressed(Mock())

    screen._show_message.assert_called_once()
    args, kwargs = screen._show_message.call_args
    assert "Please enter API Key before fetching models" in args[0]
    assert kwargs.get("is_error") is True

