"""Unit Test Result confirmation modal for OpenHands CLI."""

from textual import on
from textual.app import ComposeResult
from textual.widgets import Button

from openhands_cli.tui.dialogs.base_dialog import BaseDialog
from openhands_cli.tui.dialogs.core import ButtonBar, ScrollView, Title
from openhands_cli.tui.dialogs.ut_result_dialog_style import (
    UT_RESULT_DIALOG_STYLE,
)


class UnitTestResultDialog(BaseDialog):
    DEFAULT_CSS = UT_RESULT_DIALOG_STYLE

    def __init__(self, content: str, ut_result_dialog_scroll_view_id: str):
        self._scroll_view = ScrollView(
            content=content,
            ut_result_dialog_scroll_view_id=ut_result_dialog_scroll_view_id,
        )
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Title("Unit test result")
        yield self._scroll_view
        with ButtonBar(id="generate_single_unit_test_button_bar"):
            yield Button("Close", id="btn_hide")

    @on(Button.Pressed, "#btn_hide")
    def hide_dialog(self):
        """Hide the dialog button is pressed."""
        self.remove()
