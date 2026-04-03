from rich.text import Text
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static

from openhands_cli.tui.dialogs.core.scroll_view_style import SCROLL_VIEW_STYLE


class ScrollView(VerticalScroll):
    DEFAULT_CSS = SCROLL_VIEW_STYLE

    def __init__(self, content: str, ut_result_dialog_scroll_view_id: str):
        self._lines: list[str] = [content] if content else []
        self._view = Static()
        super().__init__(id=ut_result_dialog_scroll_view_id)

    def compose(self) -> ComposeResult:
        yield self._view

    def update(self, content: str) -> None:
        self._lines.append(content)
        self._view.update(Text("\n".join(self._lines)))
        self.scroll_end(animate=False)
