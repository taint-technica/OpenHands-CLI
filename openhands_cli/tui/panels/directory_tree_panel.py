from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Button, DirectoryTree

from openhands_cli.tui.panels.directory_tree_panel_style import (
    DIRECTORY_TREE_PANEL_STYLE,
)


class DirectoryTreePanel(Vertical):
    DEFAULT_CSS = DIRECTORY_TREE_PANEL_STYLE

    def __init__(self, root_path: str = ".", **kwargs):
        super().__init__(**kwargs)
        self.root_path = Path(root_path)

    def on_mount(self):
        self.add_class("hidden")
        self._refresh_timer = self.set_interval(2.0, self._poll_directory)

    def on_unmount(self) -> None:
        self._refresh_timer.stop()

    async def _poll_directory(self) -> None:
        if not self.has_class("hidden"):
            await self._tree.reload()

    def compose(self) -> ComposeResult:
        self._tree = DirectoryTree(path=self.root_path, id="directory_tree")
        yield Button("X", id="close_button")
        yield self._tree

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close_button":
            self.add_class("hidden")
