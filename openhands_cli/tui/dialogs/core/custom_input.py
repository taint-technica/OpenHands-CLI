from textual import on
from textual.events import Focus
from textual.message import Message
from textual.widgets import Input


class CustomInput(Input):
    class InputFocused(Message):
        def __init__(self, focus_input_id: str):
            self.focus_input_id = focus_input_id
            super().__init__()

    def __init__(self, id: str, classes: str):
        super().__init__(id=id)
        self.add_class(classes)

    @on(Focus)
    def handle_focus(self):
        if self.id:
            self.post_message(self.InputFocused(self.id))
