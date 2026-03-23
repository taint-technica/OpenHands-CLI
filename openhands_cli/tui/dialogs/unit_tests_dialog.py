"""Exit confirmation modal for OpenHands CLI."""

from textual import on
from textual.app import ComposeResult
from textual.widgets import Button

from openhands_cli.tui.dialogs.base_dialog import BaseDialog
from openhands_cli.tui.dialogs.core import ButtonBar, Field, Title
from openhands_cli.tui.dialogs.unit_tests_dialog_style import UNIT_TESTS_DIALOG_STYLE
from openhands_cli.tui.messages import (
    SendStaticMessage,
)


class UnitTestsDialog(BaseDialog):
    DEFAULT_CSS = UNIT_TESTS_DIALOG_STYLE

    def compose(self) -> ComposeResult:
        yield Title("Generate unit tests")
        yield Field(field_title="File name")

        with ButtonBar():
            yield Button("Generate unit tests", id="btn_pass")
            yield Button("Close", id="btn_hide")

    @on(Button.Pressed, "#btn_pass")
    def generate_test_case(self):
        """Called when the bell button is pressed."""
        self.post_message(SendStaticMessage(content="respect"))

    @on(Button.Pressed, "#btn_hide")
    def hide_dialog(self):
        """Hide the dialog button is pressed."""
        self.remove()
