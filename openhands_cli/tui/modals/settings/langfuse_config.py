"""Langfuse configuration modal for OpenHands CLI settings."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Checkbox,
    Input,
    Label,
    Static,
)

from openhands_cli.stores.langfuse_store import LangfuseSettings, LangfuseStore
from openhands_cli.theme import OPENHANDS_THEME


class LangfuseConfigModal(ModalScreen[bool]):
    """Modal for configuring Langfuse tracing settings."""

    BINDINGS = [
        Binding("escape", "close", "Close", show=True),
    ]

    def __init__(self) -> None:
        """Initialize Langfuse config modal."""
        super().__init__()
        self.langfuse_store = LangfuseStore()
        self.current_settings = self.langfuse_store.load()

    def compose(self) -> ComposeResult:
        """Compose the Langfuse configuration modal."""
        with Container(id="langfuse-modal"):
            yield Static("Langfuse Tracing Configuration", id="modal-title")

            with Vertical(id="langfuse-form"):
                # Enable/Disable toggle
                yield Checkbox(
                    "Enable Langfuse Tracing",
                    value=self.current_settings.enabled,
                    id="langfuse-enabled",
                )

                # Description
                yield Static(
                    "Langfuse traces LLM calls, token usage, latency, and costs. "
                    "Data is sent to your local Langfuse server.",
                    id="langfuse-description",
                )

                # Langfuse Host
                with Container(classes="form-group"):
                    yield Label("Langfuse Host:", classes="form-label")
                    yield Input(
                        value=self.current_settings.host,
                        placeholder="http://localhost:3000",
                        id="langfuse-host",
                        classes="form-input",
                        disabled=not self.current_settings.enabled,
                    )

                # Public Key
                with Container(classes="form-group"):
                    yield Label("Public Key:", classes="form-label")
                    yield Input(
                        value=self.current_settings.public_key,
                        placeholder="pk-lf-...",
                        id="langfuse-public-key",
                        classes="form-input",
                        disabled=not self.current_settings.enabled,
                    )

                # Secret Key
                with Container(classes="form-group"):
                    yield Label("Secret Key:", classes="form-label")
                    yield Input(
                        value=self.current_settings.secret_key,
                        placeholder="sk-lf-...",
                        id="langfuse-secret-key",
                        classes="form-input",
                        password=True,
                        disabled=not self.current_settings.enabled,
                    )

                # Project Name
                with Container(classes="form-group"):
                    yield Label("Project Name:", classes="form-label")
                    yield Input(
                        value=self.current_settings.project_name,
                        placeholder="openhands-cli",
                        id="langfuse-project-name",
                        classes="form-input",
                        disabled=not self.current_settings.enabled,
                    )

                # Test Connection Button
                yield Button(
                    "Test Connection",
                    id="test-connection",
                    variant="primary",
                    disabled=not self.current_settings.enabled,
                )

                # Status message area
                yield Static("", id="langfuse-status")

                # Buttons
                with Container(id="modal-buttons"):
                    yield Button("Save", id="save", variant="success")
                    yield Button("Cancel", id="cancel", variant="default")

    def on_mount(self) -> None:
        """Handle modal mount."""
        self._update_form_state()

    def _update_form_state(self) -> None:
        """Update form enabled state based on checkbox."""
        enabled = self.query_one("#langfuse-enabled", Checkbox).value

        for widget_id in [
            "langfuse-host",
            "langfuse-public-key",
            "langfuse-secret-key",
            "langfuse-project-name",
            "test-connection",
        ]:
            widget = self.query_one(
                f"#{widget_id}", Input if widget_id != "test-connection" else Button
            )
            widget.disabled = not enabled

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle checkbox toggle."""
        if event.checkbox.id == "langfuse-enabled":
            self._update_form_state()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "cancel":
            self.dismiss(False)
            return

        if button_id == "test-connection":
            self._test_connection()
            return

        if button_id == "save":
            self._save_settings()
            return

    def _test_connection(self) -> None:
        """Test connection to Langfuse server."""
        status_widget = self.query_one("#langfuse-status", Static)

        # Gather settings from form
        settings = LangfuseSettings(
            enabled=True,
            host=self.query_one("#langfuse-host", Input).value,
            public_key=self.query_one("#langfuse-public-key", Input).value,
            secret_key=self.query_one("#langfuse-secret-key", Input).value,
            project_name=self.query_one("#langfuse-project-name", Input).value,
        )

        if not settings.is_valid():
            status_widget.update(
                f"[{OPENHANDS_THEME.error}]Invalid settings. Please fill in all fields.[/{OPENHANDS_THEME.error}]"
            )
            return

        status_widget.update("[dim]Testing connection...[/dim]")

        # Test connection
        success = self.langfuse_store.test_connection(settings)

        if success:
            status_widget.update(
                f"[{OPENHANDS_THEME.success}]✓ Connection successful![/{OPENHANDS_THEME.success}]"
            )
        else:
            status_widget.update(
                f"[{OPENHANDS_THEME.error}]✗ Connection failed. Check your settings.[/{OPENHANDS_THEME.error}]"
            )

    def _save_settings(self) -> None:
        """Save Langfuse settings."""
        status_widget = self.query_one("#langfuse-status", Static)

        # Gather settings from form
        enabled = self.query_one("#langfuse-enabled", Checkbox).value
        settings = LangfuseSettings(
            enabled=enabled,
            host=self.query_one("#langfuse-host", Input).value,
            public_key=self.query_one("#langfuse-public-key", Input).value,
            secret_key=self.query_one("#langfuse-secret-key", Input).value,
            project_name=self.query_one("#langfuse-project-name", Input).value,
        )

        # Validate
        if enabled and not settings.is_valid():
            status_widget.update(
                f"[{OPENHANDS_THEME.error}]Please fill in all required fields.[/{OPENHANDS_THEME.error}]"
            )
            return

        # Save
        self.langfuse_store.save(settings)

        if enabled:
            status_widget.update(
                f"[{OPENHANDS_THEME.success}]✓ Langfuse tracing enabled![/{OPENHANDS_THEME.success}]"
            )
        else:
            status_widget.update(
                f"[{OPENHANDS_THEME.warning}]Langfuse tracing disabled.[/{OPENHANDS_THEME.warning}]"
            )

        # Dismiss with error handling for Textual screen issues
        try:
            self.dismiss(enabled)
        except Exception:
            # If dismiss fails, schedule it for later
            self.call_later(self.dismiss, enabled)

    def action_close(self) -> None:
        """Close the modal."""
        self.dismiss(False)
