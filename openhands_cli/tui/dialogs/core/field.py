from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static

from openhands_cli.tui.dialogs.core.custom_input import CustomInput
from openhands_cli.tui.dialogs.core.field_style import FIELD_STYLE


class Field(Vertical):
    DEFAULT_CSS = FIELD_STYLE

    def __init__(self, field_title: str, input_id: str, input_class: list[str], input_default=""):
        self.field_title = Static(content=field_title)
        self.input_field = CustomInput(
            id=input_id,
            classes=" ".join(input_class),  # ✅ fix
        )
        self.input_field.value = input_default
        super().__init__()

    def compose(self) -> ComposeResult:
        yield self.field_title
        yield self.input_field
