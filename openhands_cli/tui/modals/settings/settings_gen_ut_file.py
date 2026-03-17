from textual.app import App, ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label
from textual.containers import Vertical, Horizontal
from typing import ClassVar, Literal, cast


class GenUnitTestFileSettings(ModalScreen):

    """A modal screen for configuring settings."""

    BINDINGS: ClassVar = [
        ("escape", "cancel", "Cancel"),
    ]

    # CSS_PATH = "settings_screen.tcss"

    CSS = """
    GenUnitTestFileSettings {
        align: center middle;
    }
    #dialog {
        width: 100;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 2 4;
    }
    Input { margin-bottom: 1; }
    #buttons {
        margin-top: 1;
        align: right middle;
        height: auto;
    }
    Button { margin-left: 1; }
    """    

    # Pass parameters via __init__
    def __init__(self, proj_type: int):
        super().__init__()
        self.project_type = proj_type
        self.src_file_name = ""
        self.coverage_expect  = ""
        self.num_iteration  = ""

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("File Name, for etc. \"src/main/java/com/example/Greeting.java\" or \"backend/controller/api/routes/ranking.py\"")
            yield Input(value=self.src_file_name, placeholder="Enter source file name...", id="src_file_name")
            yield Label("Coverage expectation % (1-100)")
            yield Input(value=self.coverage_expect,  placeholder="Enter coverage expectation in percentage...",  id="coverage_expect")
            yield Label("Number of iteration")
            yield Input(value=self.num_iteration,  placeholder="Enter number of iteration...",  id="num_iteration")
            with Horizontal(id="buttons"):
                yield Button("Save",   variant="primary", id="save")
                yield Button("Cancel", variant="default", id="cancel")

    def on_mount(self) -> None :
        self.query_one("#src_file_name", Input).focus()
        
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            src_file_name = self.query_one("#src_file_name", Input).value
            coverage_expect  = self.query_one("#coverage_expect",  Input).value      
            num_iteration  = self.query_one("#num_iteration",  Input).value         
            self.dismiss({"project_type": self.project_type, "src_file_name": src_file_name, "coverage_expect": coverage_expect, "num_iteration": num_iteration})   
        else:
            self.dismiss(None)   # cancelled


