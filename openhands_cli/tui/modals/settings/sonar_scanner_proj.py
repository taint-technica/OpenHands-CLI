from textual.app import App, ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label
from textual.containers import Vertical, Horizontal
from typing import ClassVar, Literal, cast


class SonarScannerSettings(ModalScreen):

    """A modal screen for configuring settings."""

    BINDINGS: ClassVar = [
        ("escape", "cancel", "Cancel"),
    ]

    # CSS_PATH = "settings_screen.tcss"

    CSS = """
    SonarScannerSettings {
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
        self.project_name = ""
        self.inclusive_path  = ""
        self.exclusive_path  = ""

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Project Name")
            yield Input(value=self.project_name, placeholder="Enter project name...", id="project_name")
            yield Label("Inclusive source path")
            yield Input(value=self.inclusive_path,  placeholder="Enter source path...",  id="inclusive_path")
            yield Label("Exclusive path")
            yield Input(value=self.exclusive_path,  placeholder="Enter exclusive source path...",  id="exclusive_path")
            with Horizontal(id="buttons"):
                yield Button("Save",   variant="primary", id="save")
                yield Button("Cancel", variant="default", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            proj_name = self.query_one("#project_name", Input).value
            inc_path  = self.query_one("#inclusive_path",  Input).value      
            excl_path  = self.query_one("#exclusive_path",  Input).value         
            self.dismiss({"project_type": self.project_type, "project_name": proj_name, "inclusive_path": inc_path, "exclusive_path": excl_path})   # Pass back with updated values
        else:
            self.dismiss(None)   # cancelled — pass nothing back


