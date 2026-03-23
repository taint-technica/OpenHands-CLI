"""Exit confirmation modal for OpenHands CLI."""

from textual import on
from textual.app import ComposeResult
from textual.message import Message
from textual.widgets import Button, Input

from openhands_cli.tui.dialogs.base_dialog import BaseDialog
from openhands_cli.tui.dialogs.core import ButtonBar, Field, Title
from openhands_cli.tui.dialogs.generate_single_unit_test_dialog_style import (
    GENERATE_SINGLE_UNIT_TEST_DIALOG_STYLE,
)


class GenerateSingleUnitTestDialog(BaseDialog):
    DEFAULT_CSS = GENERATE_SINGLE_UNIT_TEST_DIALOG_STYLE

    class GenerateSingleUnitTestEvent(Message):
        def __init__(self, config: dict):
            self.config = config
            super().__init__()

    def compose(self) -> ComposeResult:
        yield Title("Generate single unit tests")
        yield Field(field_title="File name", input_id="gen_single_ut_file_name")
        yield Field(
            field_title="Coverage Expectation (0-100%)", input_id="gen_single_ut_cov"
        )
        yield Field(field_title="Num. iterations", input_id="gen_single_ut_iter")
        with ButtonBar(id="generate_single_unit_test_button_bar"):
            yield Button("Generate unit tests", id="btn_gen_ut")
            yield Button("Close", id="btn_hide")

    @on(Button.Pressed, "#btn_gen_ut")
    def generate_test_case(self):
        """Called when the bell button is pressed."""
        src = self.query_one("#gen_single_ut_file_name", Input).value
        cov = self.query_one("#gen_single_ut_cov", Input).value
        num = self.query_one("#gen_single_ut_iter", Input).value
        if not all(value.strip() for value in [src, cov, num]):
            self.notify("Please fill in all fields")
            return
        else:
            try:
                config = {
                    "src_file_name": src,
                    "coverage_expect": int(cov),
                    "num_iteration": int(num),
                }
                self.post_message(self.GenerateSingleUnitTestEvent(config=config))
            except ValueError:
                self.notify("Coverage and iteration must be numbers")
                return

    @on(Button.Pressed, "#btn_hide")
    def hide_dialog(self):
        """Hide the dialog button is pressed."""
        self.remove()
