"""Settings screen for OpenHands CLI using Textual.

This module provides a modern form-based settings interface that overlays
the main UI, allowing users to configure their settings including
LLM provider, model, API keys, and advanced options.
"""

from collections.abc import Callable
from typing import ClassVar

from textual import getters
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Input,
    Select,
    Static,
    TabbedContent,
    TabPane,
)

from openhands.sdk import LLMSummarizingCondenser
from openhands_cli.stores import AgentStore, CliSettings, CriticSettings
from openhands_cli.tui.modals.settings.components import (
    CliSettingsTab,
    CriticSettingsTab,
    SettingsTab,
)
from openhands_cli.tui.modals.settings.litellm_client import (
    fetch_available_models,
    test_proxy_connection,
)
from openhands_cli.tui.modals.settings.utils import SettingsFormData, save_settings


class SettingsScreen(ModalScreen):
    """A modal screen for configuring settings."""

    BINDINGS: ClassVar = [
        ("escape", "cancel", "Cancel"),
    ]

    CSS_PATH = "settings_screen.tcss"

    # New LiteLLM Proxy fields
    proxy_url_input: getters.query_one[Input] = getters.query_one("#proxy_url_input")
    fetch_models_button: getters.query_one[Button] = getters.query_one(
        "#fetch_models_button"
    )

    # Keep existing fields for compatibility
    provider_select: getters.query_one[Select] = getters.query_one("#provider_select")
    model_select: getters.query_one[Select] = getters.query_one("#model_select")
    custom_model_input: getters.query_one[Input] = getters.query_one(
        "#custom_model_input"
    )
    base_url_input: getters.query_one[Input] = getters.query_one("#base_url_input")
    api_key_input: getters.query_one[Input] = getters.query_one("#api_key_input")
    memory_select: getters.query_one[Select] = getters.query_one(
        "#memory_condensation_select"
    )
    timeout_input: getters.query_one[Input] = getters.query_one("#timeout_input")
    max_tokens_input: getters.query_one[Input] = getters.query_one("#max_tokens_input")
    max_size_input: getters.query_one[Input] = getters.query_one("#max_size_input")
    basic_section: getters.query_one[Container] = getters.query_one("#basic_section")
    advanced_section: getters.query_one[Container] = getters.query_one(
        "#advanced_section"
    )

    def __init__(
        self,
        on_settings_saved: Callable[[], None] | list[Callable[[], None]] | None = None,
        on_first_time_settings_cancelled: Callable[[], None] | None = None,
        **kwargs,
    ):
        """Initialize the settings screen.

        Args:
            on_settings_saved: Callback(s) to invoke when settings are saved
            on_first_time_settings_cancelled: Callback to invoke when settings are
                cancelled during first-time setup
        """
        super().__init__(**kwargs)
        self.agent_store = AgentStore()
        self.current_agent = self.agent_store.load_from_disk()
        self.message_widget = None
        self.is_initial_setup = SettingsScreen.is_initial_setup_required()
        self.fetched_models: list[str] = []

        # Convert single callback to list for uniform handling
        if on_settings_saved is None:
            self.on_settings_saved = []
        elif callable(on_settings_saved):
            self.on_settings_saved = [on_settings_saved]
        else:
            self.on_settings_saved = on_settings_saved

        self.on_first_time_settings_cancelled = on_first_time_settings_cancelled

    def compose(self) -> ComposeResult:
        """Create the settings form with tabs."""
        # Load CLI settings once for initializing both tabs
        cli_settings = CliSettings.load()

        with Container(id="settings_container"):
            yield Static("Settings", id="settings_title")

            # Message area for errors/success
            self.message_widget = Static("", id="message_area")
            yield self.message_widget

            # Tabbed content
            with TabbedContent(id="settings_tabs"):
                # Settings Tab
                with TabPane("Agent Settings", id="settings_tab"):
                    yield SettingsTab()

                # CLI Settings Tab - only show if not first-time setup
                if not self.is_initial_setup:
                    with TabPane("CLI Settings", id="cli_settings_tab"):
                        yield CliSettingsTab(initial_settings=cli_settings)

                    # Critic Settings Tab - only show if not first-time setup
                    with TabPane("Critic", id="critic_settings_tab"):
                        yield CriticSettingsTab(initial_settings=cli_settings.critic)

            # Buttons
            with Horizontal(id="button_container"):
                yield Button(
                    "Save",
                    variant="primary",
                    id="save_button",
                    classes="settings_button",
                )
                yield Button(
                    "Cancel",
                    variant="default",
                    id="cancel_button",
                    classes="settings_button",
                )

    def on_mount(self) -> None:
        """Initialize the form with current settings."""
        self._load_current_settings()
        self._update_field_dependencies()

    def on_show(self) -> None:
        """Reload settings when the screen is shown."""
        # Only reload if we don't have current settings loaded
        # This prevents unnecessary clearing when returning from modals
        if not self.current_agent:
            self._clear_form()
            self._load_current_settings()
            self._update_field_dependencies()

    def _clear_form(self) -> None:
        """Clear all form values before reloading."""
        self.api_key_input.value = ""
        self.api_key_input.placeholder = "Enter your API key"
        self.proxy_url_input.value = "http://localhost:4000"
        self.model_select.set_options([("Fetch models first", "")])
        self.model_select.disabled = True
        self.memory_select.value = True
        self.timeout_input.value = ""
        self.max_tokens_input.value = ""
        self.max_size_input.value = ""
        self.fetched_models = []

    def _has_existing_api_key(self) -> bool:
        """Check if there's an existing API key in the agent."""
        return bool(
            self.current_agent
            and self.current_agent.llm
            and self.current_agent.llm.api_key
        )

    def _load_current_settings(self) -> None:
        """Load current settings into the form."""
        if not self.current_agent:
            return

        llm = self.current_agent.llm

        # Set proxy URL (default to localhost:4000 if not set)
        self.proxy_url_input.value = llm.base_url or "http://localhost:4000"

        # Set model - will be populated after fetch if available
        if llm.model:
            # Pre-populate model select with current model
            self.model_select.set_options([(llm.model, llm.model)])
            self.model_select.value = llm.model

        # API Key (show masked version)
        if llm.api_key:
            key_value = (
                llm.api_key
                if isinstance(llm.api_key, str)
                else llm.api_key.get_secret_value()
            )
            self.api_key_input.placeholder = (
                f"Current: {key_value[:3]}*** (leave empty to keep current)"
            )
        else:
            # No API key set
            self.api_key_input.placeholder = "Enter your API key"

        # Memory Condensation
        self.memory_select.value = bool(self.current_agent.condenser)

        # Timeout (seconds) – show existing value if set
        if llm.timeout is not None:
            self.timeout_input.value = str(llm.timeout)
        else:
            self.timeout_input.value = ""

        # Max tokens (optional) – show existing value if set
        max_input = getattr(llm, "max_input_tokens", None)
        if max_input is not None:
            self.max_tokens_input.value = str(max_input)
        else:
            self.max_tokens_input.value = ""

        # Condenser max size (optional) – show existing value if set
        if (
            self.current_agent
            and self.current_agent.condenser
            and isinstance(self.current_agent.condenser, LLMSummarizingCondenser)
        ):
            self.max_size_input.value = str(self.current_agent.condenser.max_size)
        else:
            self.max_size_input.value = ""

        # Update field dependencies after loading all values
        self._update_field_dependencies()

    def _update_field_dependencies(self) -> None:
        """Update field enabled/disabled state based on dependency chain."""
        try:
            proxy_url = (
                self.proxy_url_input.value.strip()
                if hasattr(self.proxy_url_input, "value")
                else ""
            )
            selected_model = self.model_select.value
            has_selected_model = isinstance(selected_model, str) and bool(
                selected_model.strip()
            )
            has_model = (
                has_selected_model and self.fetched_models  # Must have fetched models
            )

            # Fetch button enabled if proxy URL is set
            self.fetch_models_button.disabled = not proxy_url

            # Model select enabled after fetch
            self.model_select.disabled = not has_model

            # API Key: always enabled (needed for fetch)
            self.api_key_input.disabled = False

            # Advanced settings enabled if model is selected
            self.timeout_input.disabled = not has_model
            self.max_tokens_input.disabled = not has_model
            self.max_size_input.disabled = not has_model

            # Memory Condensation enabled if model is selected
            self.memory_select.disabled = not has_model

        except Exception:
            # Silently handle errors during initialization
            pass

    def _show_message(self, message: str, is_error: bool = False) -> None:
        """Show a message to the user."""
        if self.message_widget:
            self.message_widget.update(message)
            self.message_widget.add_class(
                "error_message" if is_error else "success_message"
            )
            self.message_widget.remove_class(
                "success_message" if is_error else "error_message"
            )

    def _clear_message(self) -> None:
        """Clear the message area."""
        if self.message_widget:
            self.message_widget.update("")
            self.message_widget.remove_class("error_message")
            self.message_widget.remove_class("success_message")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "save_button":
            self._save_settings()
        elif event.button.id == "cancel_button":
            self._handle_cancel()
        elif event.button.id == "fetch_models_button":
            await self._on_fetch_models_button_pressed(event)

    async def _on_fetch_models_button_pressed(self, _event: Button.Pressed) -> None:
        """Handle fetch models button press."""
        proxy_url = self.proxy_url_input.value
        if not proxy_url:
            self._show_message("Please enter Proxy URL first", is_error=True)
            return

        api_key_input = self.api_key_input.value.strip()
        if not api_key_input:
            self._show_message(
                "Please enter API Key before fetching models", is_error=True
            )
            return

        self._show_message("Fetching models...", is_error=False)
        self.fetch_models_button.disabled = True

        try:
            # Test connection first
            connection_result = await test_proxy_connection(proxy_url)
            if not connection_result.get("success"):
                self._show_message(
                    f"Connection failed: {connection_result.get('error', 'Unknown')}",
                    is_error=True,
                )
                return

            # Fetch models
            self.fetched_models = await fetch_available_models(proxy_url, api_key_input)

            if not self.fetched_models:
                self._show_message(
                    "No models found. Check LiteLLM Proxy configuration.",
                    is_error=True,
                )
                return

            # Update model select
            options = [(model, model) for model in self.fetched_models]
            self.model_select.set_options(options)
            self.model_select.disabled = False

            self._show_message(
                f"Successfully fetched {len(self.fetched_models)} models",
                is_error=False,
            )

        except Exception as e:
            self._show_message(f"Error fetching models: {str(e)}", is_error=True)
        finally:
            self.fetch_models_button.disabled = False

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input field changes."""
        if event.input.id == "proxy_url_input":
            # Clear fetched models when proxy URL changes
            self.fetched_models = []
            self.model_select.set_options([("Fetch models first", "")])
            self.model_select.disabled = True
        elif event.input.id == "api_key_input":
            self._update_field_dependencies()
            self._clear_message()

    def action_cancel(self) -> None:
        """Handle escape key to cancel settings."""
        self._handle_cancel()

    def _handle_cancel(self) -> None:
        """Handle cancel action - delegate to appropriate callback."""
        self.dismiss(False)

        if self.on_first_time_settings_cancelled and self.is_initial_setup:
            self.on_first_time_settings_cancelled()

    def _save_settings(self) -> None:
        """Save the current settings."""
        proxy_url = self.proxy_url_input.value
        selected_model = self.model_select.value
        api_key_input = self.api_key_input.value

        # Validate required fields
        if not proxy_url:
            self._show_message("Please enter Proxy URL", is_error=True)
            return

        if not isinstance(selected_model, str) or not selected_model.strip():
            self._show_message("Please select a model", is_error=True)
            return

        model = selected_model.strip()

        if not api_key_input:
            self._show_message("Please enter API Key", is_error=True)
            return

        # Create form data (reuse existing SettingsFormData)
        form_data = SettingsFormData(
            mode="advanced",  # Always advanced mode now
            provider=None,  # Not used
            model=model,
            custom_model=model,  # Use model as custom_model
            base_url=proxy_url,
            api_key_input=api_key_input,
            memory_condensation_enabled=bool(self.memory_select.value),
            timeout=self.timeout_input.value,
            max_tokens=self.max_tokens_input.value,
            max_size=self.max_size_input.value,
        )

        # Preserve existing timeout if user entered invalid value
        if form_data.timeout is None and self.current_agent:
            form_data.timeout = getattr(self.current_agent.llm, "timeout", None)
        result = save_settings(form_data, self.current_agent)
        if not result.success:
            self._show_message(result.error_message or "Unknown error", is_error=True)
            return

        # Save CLI and Critic settings if not in initial setup mode
        if not self.is_initial_setup:
            try:
                # Get updated fields from each tab
                cli_settings_tab = self.query_one("#cli_settings_tab", TabPane)
                cli_tab = cli_settings_tab.query_one(CliSettingsTab)

                critic_settings_tab = self.query_one("#critic_settings_tab", TabPane)
                critic_tab = critic_settings_tab.query_one(CriticSettingsTab)

                # Load base settings and merge fields from both tabs
                base_settings = CliSettings.load()

                # Update the nested critic settings
                updated_critic = base_settings.critic.model_copy(
                    update=critic_tab.get_updated_fields()
                )

                merged_settings = base_settings.model_copy(
                    update={
                        **cli_tab.get_updated_fields(),
                        "critic": updated_critic,
                    }
                )

                merged_settings.save()

                # Update reactive state to refresh UI components
                self._update_critic_settings(updated_critic)
            except Exception as e:
                self._show_message(
                    f"Settings saved, but CLI settings failed: {str(e)}", is_error=True
                )
                return

        message = (
            "Settings saved successfully! Welcome to OpenHands CLI!"
            if self.is_initial_setup
            else "Settings saved successfully!"
        )
        self._show_message(message, is_error=False)
        # Invoke all callbacks if provided, then close screen
        for callback in self.on_settings_saved:
            try:
                callback()
            except Exception as e:
                self.notify(
                    f"Error occurred when saving settings: {e}", severity="error"
                )
        self.dismiss(True)

    def _update_critic_settings(self, critic_settings: CriticSettings) -> None:
        """Update reactive critic settings in ConversationContainer.

        This triggers automatic UI updates for all components bound to critic_settings.
        """
        try:
            from openhands_cli.tui.core.state import ConversationContainer

            container = self.app.query_one(ConversationContainer)
            container.set_critic_settings(critic_settings)
        except Exception:
            pass  # Container may not exist in all contexts

    @staticmethod
    def is_initial_setup_required() -> bool:
        """Check if initial setup is required.

        Returns:
            True if initial setup is needed (no existing settings), False otherwise.
        """
        agent_store = AgentStore()
        existing_agent = agent_store.load_or_create()
        return existing_agent is None
