from textual.widgets import Static

from openhands_cli.tui.dialogs.core.title_style import TITLE_STYLE


class Title(Static):
    DEFAULT_CSS = TITLE_STYLE

    def __init__(self, content: str):
        super().__init__(content=content)
