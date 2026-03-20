"""Exit confirmation modal for OpenHands CLI."""

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.events import MouseDown, MouseMove, MouseUp
from textual.message import Message
from textual.widgets import Button, Input, Static

from openhands_cli.tui.messages import (
    SendStaticMessage,
)
from openhands_cli.tui.modals.unit_tests_modal_style import UNIT_TESTS_MODAL_STYLE


class UnitTestsModal(Vertical):
    class GenerateTestsClicked(Message):
        """Message sent when the Run Tests button is clicked."""

        pass

    DEFAULT_CSS = UNIT_TESTS_MODAL_STYLE
    _mouse_down_pos = None

    def on_mouse_down(self, event: MouseDown):
        self._mouse_down_pos = (event.screen_x, event.screen_y)

    def on_mouse_up(self, event: MouseUp):
        self._mouse_down_pos = None

    def on_mouse_move(self, event: MouseMove):
        if self._mouse_down_pos is not None:
            self.styles.offset = (event.screen_x - 40, event.screen_y - 4)

    def _on_mount(self, event):
        self.add_class("hidden")
        return super()._on_mount(event)

    def compose(self) -> ComposeResult:
        yield Static("Generate unit tests")
        yield Input(id="unit_test_location")

        with Horizontal(id="unit_test_button_field"):
            yield Button("Generate unit tests", id="btn_pass")
            yield Button("Close", id="btn_hide")

    @on(Button.Pressed, "#btn_pass")
    def generate_test_case(self):
        """Called when the bell button is pressed."""
        self.post_message(SendStaticMessage(content="respect"))

    @on(Button.Pressed, "#btn_hide")
    def hide_modal(self):
        """Called when the 'toggle dark' button is pressed."""
        self.add_class("hidden")
