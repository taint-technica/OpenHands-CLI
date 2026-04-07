"""Input area container for status lines and input field.

This container is docked to the bottom of ConversationContainer (as a sibling of
ScrollableContent) and handles slash command execution.

Widget Hierarchy:
    ConversationManager (ancestor - messages bubble here)
    └── ConversationContainer(#conversation_state)
        ├── ScrollableContent(#scroll_view)  ← sibling, content rendered here
        └── InputAreaContainer(#input_area)  ← docked to bottom
            ├── WorkingStatusLine
            ├── InputField  ← posts messages
            └── InfoStatusLine

Message Flow:
    - SlashCommandSubmitted → InputAreaContainer posts operation messages
    - All messages bubble up to ConversationManager (ancestor)

Data Binding:
    - loaded_resources: Bound from ConversationContainer for /skills command
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from textual import on
from textual.containers import Container
from textual.reactive import var

from openhands_cli.tui.core.commands import show_help, show_skills, show_scanner_config_progress, show_generate_single_unit_test_progress
from openhands_cli.tui.messages import SlashCommandSubmitted

from openhands_cli.tui.dialogs import (
    ConfigureSonarScannerDialog,
    GenerateSingleUnitTestDialog,
)


if TYPE_CHECKING:
    from openhands_cli.tui.content.resources import LoadedResourcesInfo
    from openhands_cli.tui.textual_app import OpenHandsApp
    from openhands_cli.tui.widgets.main_display import ScrollableContent


class InputAreaContainer(Container):
    """Container for the input area that handles slash commands.

    InputAreaContainer posts operation messages (CreateConversation, etc.)
    that bubble up to ConversationManager, which is an ancestor in the
    widget hierarchy.

    SendMessage messages from InputField also bubble up to
    ConversationManager automatically.

    Reactive Properties:
        loaded_resources: Bound from ConversationContainer, used by /skills command.
    """

    # Reactive property bound from ConversationContainer
    loaded_resources: var[LoadedResourcesInfo | None] = var(None)

    @property
    def scroll_view(self) -> ScrollableContent:
        """Get the sibling scrollable content area."""
        from openhands_cli.tui.widgets.main_display import ScrollableContent

        # scroll_view is a sibling - query from parent (ConversationContainer)
        assert self.parent is not None, "InputAreaContainer must have a parent"
        return self.parent.query_one("#scroll_view", ScrollableContent)

    @on(SlashCommandSubmitted)
    def _on_slash_command_submitted(self, event: SlashCommandSubmitted) -> None:
        """Handle slash commands by routing to appropriate handlers.

        Routes to ConversationManager for conversation operations,
        or to app-level handlers for UI operations.
        """
        event.stop()

        match event.command:
            case "help":
                self._command_help()
            case "new":
                self._command_new()
            case "history":
                self._command_history()
            case "settings":
                self._command_settings()
            case "confirm":
                self._command_confirm()
            case "condense":
                self._command_condense()
            case "skills":
                self._command_skills()
            case "feedback":
                self._command_feedback()
            case "exit":
                self._command_exit()
            case "code_tree":
                self._command_code_tree()
            case "analysis_architect_and_framework":
                # Send to agent for processing (not handled by TUI)
                self._command_send_to_agent(event.command)
            case "code_analysis":
                # Send to agent for processing (not handled by TUI)
                self._command_send_to_agent(event.command)
            case "open_project":
                self._command_open_project()
            case "open_unit_tests_modal":
                self._command_open_unit_tests_modal()
            case "generate_single_unit_test":
                self._command_generate_single_unit_test()
            case "configure_sonar_scanner":
                self._command_configure_sonar_scanner()
            case "run_unit_test":
                self._command_run_unit_test()
            case "post_sonarqube_server":
                self._command_post_sonarqube_server()
            case _:
                self.app.notify(
                    title="Unknown Command",
                    message=f"Unknown command: /{event.command}",
                    severity="warning",
                )

    # ---- Command Methods ----

    def _command_help(self) -> None:
        """Handle the /help command to display available commands."""
        show_help(self.scroll_view)

    def _command_new(self) -> None:
        """Handle the /new command to start a new conversation."""
        from openhands_cli.tui.core import CreateConversation

        # Message bubbles up to ConversationManager (ancestor)
        self.post_message(CreateConversation())

    def _command_history(self) -> None:
        """Handle the /history command to show conversation history panel."""

        app = cast("OpenHandsApp", self.app)
        app.action_toggle_history()

    def _command_settings(self) -> None:
        """Handle the /settings command to open settings modal."""
        app = cast("OpenHandsApp", self.app)
        app.action_open_settings()

    def _command_confirm(self) -> None:
        """Handle the /confirm command to show confirmation settings modal."""
        from openhands_cli.tui.core import SetConfirmationPolicy
        from openhands_cli.tui.modals.confirmation_modal import (
            ConfirmationSettingsModal,
        )

        app = cast("OpenHandsApp", self.app)

        # Get current confirmation policy from state
        current_policy = app.conversation_state.confirmation_policy

        # Callback posts message that bubbles up to ConversationManager
        def on_policy_selected(policy):
            self.post_message(SetConfirmationPolicy(policy))

        confirmation_modal = ConfirmationSettingsModal(
            current_policy=current_policy,
            on_policy_selected=on_policy_selected,
        )
        app.push_screen(confirmation_modal)

    def _command_condense(self) -> None:
        """Handle the /condense command to condense conversation history."""
        from openhands_cli.tui.core import CondenseConversation

        # Message bubbles up to ConversationManager (ancestor)
        self.post_message(CondenseConversation())

    def _command_skills(self) -> None:
        """Handle the /skills command to display loaded resources."""
        # loaded_resources is bound from ConversationContainer via data_bind
        if self.loaded_resources:
            show_skills(self.scroll_view, self.loaded_resources)
            self.scroll_view.scroll_end(animate=False)

    def _command_feedback(self) -> None:
        """Handle the /feedback command to open feedback form in browser."""
        import webbrowser

        feedback_url = "https://forms.gle/chHc5VdS3wty5DwW6"
        webbrowser.open(feedback_url)
        self.app.notify(
            title="Feedback",
            message="Opening feedback form in your browser...",
            severity="information",
        )

    def _command_exit(self) -> None:
        """Handle the /exit command with optional confirmation."""
        from openhands_cli.tui.modals.exit_modal import ExitConfirmationModal

        app = cast("OpenHandsApp", self.app)

        if app.exit_confirmation:
            app.push_screen(ExitConfirmationModal())
        else:
            app.exit()

    def _command_code_tree(self) -> None:
        """Handle the /code_tree command to toggle the code tree panel."""
        app = cast("OpenHandsApp", self.app)
        app.action_toggle_code_tree()

    def _command_send_to_agent(self, command: str) -> None:
        """Send a command to the agent for processing.

        Some commands (like /analysis_architect_and_framework) should be
        handled by the ACP agent, not by the TUI. This method sends the
        command as a regular message so the agent can process it.

        Args:
            command: The command name (without leading /)
        """
        from openhands_cli.tui.messages import SendMessage

        # Send the full command as a message to the agent
        self.post_message(SendMessage(content=f"/{command}"))

    def _command_generate_single_unit_test(self) -> None:
        """Generate Unit Test for a single file."""
        project_type = show_generate_single_unit_test_progress(self.scroll_view)
        app = cast("OpenHandsApp", self.app)
        app = cast("OpenHandsApp", self.app)
        if not app.query("#generate_single_ut_dialog"):
            app.conversation_manager.mount(
                GenerateSingleUnitTestDialog(id="generate_single_ut_dialog")
            )

    def _command_configure_sonar_scanner(self) -> None:
        """Create sonar scanner configuration file."""
        app = cast("OpenHandsApp", self.app)
        if not app.query("#config_sonar_scanner_dialog"):
            from pathlib import Path

            sonar_properties_path = "sonar-project.properties"
            file_path = Path(sonar_properties_path)
            file_path.touch(exist_ok=True)
            sonar_config_dict = {}
            TARGET_KEYS = {"projectName", "sources", "exclusions"}

            with file_path.open(encoding="utf-8") as f:
                for line in f:
                    line = line.strip()

                    # skip empty lines and comments
                    if not line or line.startswith("#"):
                        continue

                    # split only once
                    if "=" not in line:
                        continue  # skip invalid lines safely

                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()

                    # remove "sonar." prefix safely
                    if key.startswith("sonar."):
                        key = key.removeprefix("sonar.")

                        if key in TARGET_KEYS:
                            if key == "projectName":
                                sonar_config_dict["project_name"] = value
                            else:
                                sonar_config_dict[key] = value

            from openhands_cli.utils import (
                count_files_by_type,
                get_current_wd,
                get_project_type,
            )

            cpath = get_current_wd()
            count_file_types = count_files_by_type(cpath)
            project_type = get_project_type(count_file_types)
            sonar_config_dict["project_type"] = project_type

            app.conversation_manager.mount(
                ConfigureSonarScannerDialog(
                    id="config_sonar_scanner_dialog",
                    sonar_config_dict=sonar_config_dict,
                )
            )

    def _command_run_unit_test(self) -> None:
        """Run Unit Test for SonarQube."""
        from openhands_cli.utils import get_current_wd, count_files_by_type, get_project_type
        cpath = get_current_wd()
        count_file_types = count_files_by_type(cpath)
        proj_type = get_project_type(count_file_types)
        
        app = cast("OpenHandsApp", self.app)
        app.action_run_unit_test(proj_type)
        return

    def _command_post_sonarqube_server(self) -> None:
        """Posting Unit Test result to SonarQube Server."""
        from openhands_cli.utils import get_current_wd, count_files_by_type, get_project_type
        cpath = get_current_wd()
        count_file_types = count_files_by_type(cpath)
        proj_type = get_project_type(count_file_types)
        
        app = cast("OpenHandsApp", self.app)
        app.action_post_sonarqube_server(proj_type)
        return

    def _command_open_project(self) -> None:
        """Handle the /open_project command to open the project tree view."""
        app = cast("OpenHandsApp", self.app)

        app.query_one("#directory_tree_panel").remove_class("hidden")

    def _command_open_unit_tests_modal(self) -> None:
        """Handle the /open_unit_tests_modal command to open unit test generation modal."""
        app = cast("OpenHandsApp", self.app)
        # Dialogs are mounted dynamically instead of being part of the initial layout.
        # Unlike core UI components (e.g., directory tree) which are always present and
        # simply shown/hidden, dialogs are transient and may vary in number and type.
        # Pre-defining all dialogs in the main layout (even as hidden) would be inefficient
        # and less scalable as the app grows. Therefore, we only mount the dialog when needed,
        # and reuse it if it already exists.

        #if not app.query("#ut_dialog"):
        #    app.conversation_manager.mount(UnitTestsDialog(id="ut_dialog"))
