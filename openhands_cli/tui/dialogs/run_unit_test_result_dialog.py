"""Runh Unit Test Result dialog for OpenHands CLI."""

from textual import on
from textual.app import ComposeResult
from textual.widgets import Button

from openhands_cli.tui.dialogs.base_dialog import BaseDialog
from openhands_cli.tui.dialogs.core import ButtonBar, ScrollView, Title
from openhands_cli.tui.dialogs.run_unit_test_result_dialog_style import (
    RUN_UT_RESULT_DIALOG_STYLE,
)


class RunUnitTestResultDialog(BaseDialog):
    DEFAULT_CSS = RUN_UT_RESULT_DIALOG_STYLE

    def __init__(self, content: str, run_ut_result_dialog_scroll_view_id: str):
        self.scroll_view = ScrollView(
            content=content,
            id=run_ut_result_dialog_scroll_view_id,
        )
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Title("Run Unit test result")
        yield self.scroll_view
        with ButtonBar(id="run_unit_test_button_bar"):
            yield Button("Close", id="btn_hide")

    @on(Button.Pressed, "#btn_hide")
    def hide_dialog(self):
        """Hide the dialog button is pressed."""
        self.remove()
