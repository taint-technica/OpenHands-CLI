"""Exit confirmation modal for OpenHands CLI."""

from textual import on
from textual.app import ComposeResult
from textual.message import Message
from textual.widgets import Button, Input

from openhands_cli.tui.dialogs.base_dialog import BaseDialog
from openhands_cli.tui.dialogs.configure_sonar_scanner_dialog_style import (
    CONFIGURE_SONAR_SCANNER_DIALOG_STYLE,
)
from openhands_cli.tui.dialogs.core import ButtonBar, Field, Title


class ConfigureSonarScannerDialog(BaseDialog):
    DEFAULT_CSS = CONFIGURE_SONAR_SCANNER_DIALOG_STYLE

    class ConfigureSonarScannerEvent(Message):
        def __init__(self, config: dict):
            self.config = config
            super().__init__()

    def compose(self) -> ComposeResult:
        yield Title("Configure Sonar Scanner")
        yield Field(
            field_title="Project Name",
            input_id="config_sonar_scanner_project",
            input_class=["additive_input"],
        )
        yield Field(
            field_title="Inclusive source path",
            input_id="config_sonar_scanner_inclusive_path",
            input_class=["additive_input"],
        )
        yield Field(
            field_title="Exclusive path",
            input_id="config_sonar_scanner_exclusive_path",
            input_class=["additive_input"],
        )
        with ButtonBar(id="config_sonar_scanner_button_bar"):
            yield Button("Save", id="btn_save_config_sonar_scanner")
            yield Button("Close", id="btn_hide_config_sonar_scanner")

    @on(Button.Pressed, "#btn_save_config_sonar_scanner")
    def generate_test_case(self):
        """Called when the bell button is pressed."""
        project_name = self.query_one("#config_sonar_scanner_project", Input).value
        inclusive_path = self.query_one(
            "#config_sonar_scanner_inclusive_path", Input
        ).value
        exclusive_path = self.query_one(
            "#config_sonar_scanner_exclusive_path", Input
        ).value
        if not all(
            value.strip() for value in [project_name, inclusive_path, exclusive_path]
        ):
            self.notify("Please fill in all fields")
            return
        else:
            self.remove()
            try:
                config = {
                    "project_name": project_name,
                    "inclusive_path": inclusive_path,
                    "exclusive_path": exclusive_path,
                }
                self.post_message(self.ConfigureSonarScannerEvent(config=config))
            except ValueError:
                self.notify("Paths must be text")
                return

    @on(Button.Pressed, "#btn_hide_config_sonar_scanner")
    def hide_dialog(self):
        """Hide the dialog button is pressed."""
        self.remove()
