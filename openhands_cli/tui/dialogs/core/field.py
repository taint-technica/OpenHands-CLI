from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Input, Static

from openhands_cli.tui.dialogs.core.field_style import FIELD_STYLE


class Field(Vertical):
    DEFAULT_CSS = FIELD_STYLE

    def __init__(self, field_title: str, input_id: str):
        self.field_title = Static(content=field_title)
        self.input_field = Input(id=input_id)
        super().__init__()

    def compose(self) -> ComposeResult:
        yield self.field_title
        yield self.input_field
