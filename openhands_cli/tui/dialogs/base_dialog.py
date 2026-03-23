"""Exit confirmation modal for OpenHands CLI."""

from textual.containers import Vertical
from textual.events import MouseDown, MouseMove, MouseUp

from openhands_cli.tui.dialogs.base_dialog_style import BASE_DIALOG_STYLE


class BaseDialog(Vertical):
    DEFAULT_CSS = BASE_DIALOG_STYLE
    _mouse_down_pos = None

    def on_mouse_down(self, event: MouseDown):
        self._mouse_down_pos = (event.screen_x, event.screen_y)

    def on_mouse_up(self, event: MouseUp):
        self._mouse_down_pos = None

    def on_mouse_move(self, event: MouseMove):
        if self._mouse_down_pos is not None:
            self.styles.offset = (event.screen_x - 40, event.screen_y - 4)
