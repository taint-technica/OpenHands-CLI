"""Command definitions and handlers for OpenHands CLI.

This module contains all available commands, their descriptions,
and the logic for handling command execution.
"""

from __future__ import annotations

from textual.containers import VerticalScroll
from textual.widgets import Static
from textual_autocomplete import DropdownItem

from openhands_cli.theme import OPENHANDS_THEME
from openhands_cli.tui.content.resources import LoadedResourcesInfo


UNKNOWN_PROJECT_TEXT = "UNKNOWN Project type\n"


# Available commands with descriptions after the command
COMMANDS = [
    DropdownItem(main="/help - Display available commands"),
    DropdownItem(main="/new - Start a new conversation"),
    DropdownItem(main="/history - Toggle conversation history"),
    DropdownItem(main="/settings - Open settings"),
    DropdownItem(main="/confirm - Configure confirmation settings"),
    DropdownItem(main="/condense - Condense conversation history"),
    DropdownItem(main="/skills - View loaded skills, hooks, and MCPs"),
    DropdownItem(main="/feedback - Send anonymous feedback about CLI"),
    DropdownItem(main="/exit - Exit the application"),
    DropdownItem(main="/code_tree - Toggle project code tree panel"),
    DropdownItem(
        main="/analysis_architect_and_framework - Analyze code architecture and framework structure"
    ),
    DropdownItem(main="/code_analysis - Analysis your code"),
    DropdownItem(
        main="/generate_single_unit_test - Generate Unit Test for a single file"
    ),
    DropdownItem(
        main="/configure_sonar_scanner - Create a Sonar Scanner configuration file"
    ),
    DropdownItem(main="/run_unit_test - Run Unit Test for Sonar report"),
    DropdownItem(
        main="/post_sonarqube_server - Posting Unit Test result and source coverage to SonarQube server"
    ),
]


def get_valid_commands() -> set[str]:
    """Extract valid command names from COMMANDS list.

    Returns:
        Set of valid command strings (e.g., {"/help", "/exit"})
    """
    valid_commands = set()
    for command_item in COMMANDS:
        command_text = str(command_item.main)
        # Extract command part (before " - " if present)
        if " - " in command_text:
            command = command_text.split(" - ")[0]
        else:
            command = command_text
        valid_commands.add(command)
    return valid_commands


def is_valid_command(user_input: str) -> bool:
    """Check if user input is an exact match for a valid command.

    Args:
        user_input: The user's input string

    Returns:
        True if input exactly matches a valid command, False otherwise
    """
    return user_input in get_valid_commands()


def show_help(scroll_view: VerticalScroll) -> None:
    """Display help information in the scrollable content area.

    Args:
        scroll_view: The VerticalScroll widget to mount help content to
    """
    primary = OPENHANDS_THEME.primary
    secondary = OPENHANDS_THEME.secondary

    help_text = f"""
[bold {primary}]OpenHands CLI Help[/bold {primary}]
[dim]Available commands:[/dim]

  [{secondary}]/help[/{secondary}] - Display available commands
  [{secondary}]/new[/{secondary}] - Start a new conversation
  [{secondary}]/history[/{secondary}] - Toggle conversation history
  [{secondary}]/settings[/{secondary}] - Open settings
  [{secondary}]/confirm[/{secondary}] - Configure confirmation settings
  [{secondary}]/condense[/{secondary}] - Condense conversation history
  [{secondary}]/skills[/{secondary}] - View loaded skills, hooks, and MCPs
  [{secondary}]/feedback[/{secondary}] - Send anonymous feedback about CLI
  [{secondary}]/exit[/{secondary}] - Exit the application
  [{secondary}]/code_tree[/{secondary}] - Toggle project code tree panel
  [{secondary}]/analysis_architect_and_framework[/{secondary}] - Analyze code architecture and framework structure
  [{secondary}]/code_analysis[/{secondary}] - Analyze code for unit test friendliness
  [{secondary}]/generate_single_unit_test[/{secondary}] - Generate Unit Test for a single file
  [{secondary}]/configure_sonar_scanner[/{secondary}] - Create a Sonar Scanner configuration file
  [{secondary}]/run_unit_test[/{secondary}] - Run Unit Test for Sonar report
  [{secondary}]/post_sonarqube_server[/{secondary}] - Posting Unit Test result and source coverage to SonarQube server

[dim]Tips:[/dim]
  • Type / and press Tab to see command suggestions
  • Use arrow keys to navigate through suggestions
  • Press Enter to select a command
  • Use Ctrl+T to quickly toggle code tree panel
  • In code tree panel: arrow keys to navigate, Enter to mention file
"""
    help_widget = Static(help_text, classes="help-message")
    scroll_view.mount(help_widget)


def show_skills(
    scroll_view: VerticalScroll, loaded_resources: LoadedResourcesInfo
) -> None:
    """Display loaded skills, hooks, and MCPs information in the scroll view.

    Args:
        scroll_view: The VerticalScroll widget to mount skills content to
        loaded_resources: Information about loaded resources
    """
    primary = OPENHANDS_THEME.primary

    # Build the skills text using the get_details method
    lines = [f"\n[bold {primary}]Loaded Resources[/bold {primary}]"]
    lines.append(f"[dim]Summary:[/dim] {loaded_resources.get_summary()}\n")
    details = loaded_resources.get_details()
    if details and details != "No resources loaded":
        lines.append(details)
    else:
        lines.append("[dim]No skills, hooks, or MCPs loaded.[/dim]")
    skills_text = "\n".join(lines)

    skills_widget = Static(skills_text, classes="skills-message")
    scroll_view.mount(skills_widget)


def show_generate_single_unit_test_progress(scroll_view: VerticalScroll) -> int:
    """Display generating a single Unit test progress in the scroll view.
    Args:
        scroll_view: The VerticalScroll widget to mount content to
    """
    from openhands_cli.constants import CustomConstants
    from openhands_cli.utils import (
        count_files_by_type,
        get_current_wd,
        get_project_type,
    )

    primary = OPENHANDS_THEME.primary
    lines = [f"\n[bold {primary}]Reading project...[/bold {primary}]"]
    lines.append("[dim]Summary:[/dim] Generating GenUnit_Test.sh\n")
    cpath = get_current_wd()
    lines.append(f"Current directory: {cpath}\n")

    count_file_types = count_files_by_type(cpath)

    proj_type = get_project_type(count_file_types)
    match proj_type:
        case CustomConstants.PROJECT_TYPE_PYTHON:
            lines.append("PYTHON Project\n")
        case CustomConstants.PROJECT_TYPE_JAVA:
            lines.append("JAVA Project\n")
        case CustomConstants.PROJECT_TYPE_UNKNOWN:
            lines.append(UNKNOWN_PROJECT_TEXT)

    skills_widget = Static("\n".join(lines), classes="skills-message")
    scroll_view.mount(skills_widget)
    return proj_type


def show_scanner_config_progress(scroll_view: VerticalScroll) -> int:
    """Display sonar scanner progress in the scroll view.
    Args:
        scroll_view: The VerticalScroll widget to mount content to
    """
    from openhands_cli.constants import CustomConstants
    from openhands_cli.utils import (
        count_files_by_type,
        get_current_wd,
        get_project_type,
    )

    primary = OPENHANDS_THEME.primary
    lines = [f"\n[bold {primary}]Reading project...[/bold {primary}]"]
    lines.append("[dim]Summary:[/dim] Generating sonar-project.properties\n")
    cpath = get_current_wd()
    lines.append(f"Current directory: {cpath}\n")

    count_file_types = count_files_by_type(cpath)

    proj_type = get_project_type(count_file_types)
    match proj_type:
        case CustomConstants.PROJECT_TYPE_PYTHON:
            lines.append("PYTHON Project\n")
        case CustomConstants.PROJECT_TYPE_JAVA:
            lines.append("JAVA Project\n")
        case CustomConstants.PROJECT_TYPE_UNKNOWN:
            lines.append(UNKNOWN_PROJECT_TEXT)

    skills_widget = Static("\n".join(lines), classes="skills-message")
    scroll_view.mount(skills_widget)
    return proj_type


def generate_unit_test_gen_script(
    scroll_view: VerticalScroll, config_table: dict
) -> bool:
    import os
    from pathlib import Path

    from openhands_cli.ut_generation import generate_unit_test_script

    if not validate_unit_test_gen_input(scroll_view, config_table):
        return False

    lines = []
    lines.append("Generating UT script...\n")

    # Get LLM configuration
    import json

    from openhands_cli.stores import AgentStore

    agent_store = AgentStore()
    config_str = agent_store.load_config_raw()
    api_key = ""
    llm_base_url = ""
    base_model = ""
    if config_str:
        config_dict = json.loads(config_str)
        api_key = config_dict["llm"]["api_key"]
        llm_base_url = config_dict["llm"]["base_url"]
        base_model = config_dict["llm"]["model"]

    keploy_model_alias = os.environ.get("KEPLOY_LLM_MODEL_ALIAS", "").strip()
    effective_keploy_model = keploy_model_alias or base_model

    trace_project = Path.cwd().name or "unknown"
    lines.append(
        f"Trace taxonomy: source=keploy, flow=utgen, project={trace_project}\n"
    )
    lines.append(f"Keploy model: {effective_keploy_model}\n")

    try:
        generate_unit_test_script(
            config_table.get("src_file_name") or "",
            config_table.get("coverage_expect") or 85,
            config_table.get("num_iteration") or 5,
            api_key,
            llm_base_url,
            effective_keploy_model,
            trace_source="keploy",
            trace_flow="utgen",
            project_name=trace_project,
        )
    except ValueError as e:
        lines.append(f"Failed to generate script: {e}\n")
        skills_widget = Static("\n".join(lines), classes="skills-message")
        scroll_view.mount(skills_widget)
        return False

    skills_widget = Static("\n".join(lines), classes="skills-message")
    scroll_view.mount(skills_widget)
    return True


def validate_unit_test_gen_input(
    scroll_view: VerticalScroll, config_table: dict
) -> bool:
    import os
    from pathlib import Path

    src_file = config_table.get("src_file_name")
    if not src_file or not os.path.isfile(src_file):
        skills_widget = Static(
            f'File "{src_file}" does not exist ! Exiting.\n', classes="skills-message"
        )
        scroll_view.mount(skills_widget)
        return False

    allowed_suffixes = {".py", ".java"}
    suffix = Path(src_file).suffix.lower()
    if suffix not in allowed_suffixes:
        skills_widget = Static(
            f'Unsupported source file "{src_file}" (extension: "{suffix or "(none)"}"). '
            "Only .py or .java are supported. Exiting.\n",
            classes="skills-message",
        )
        scroll_view.mount(skills_widget)
        return False

    coverage_expect = config_table.get("coverage_expect")
    try:
        coverage_int = int(str(coverage_expect))
    except (TypeError, ValueError):
        coverage_int = -1
    if coverage_int not in range(1, 100):
        skills_widget = Static(
            f'Coverage "{coverage_expect}" is invalid ! Exiting.\n',
            classes="skills-message",
        )
        scroll_view.mount(skills_widget)
        return False

    num_iteration = config_table.get("num_iteration")
    try:
        num_iteration_int = int(str(num_iteration))
    except (TypeError, ValueError):
        num_iteration_int = -1
    if num_iteration_int < 1:
        skills_widget = Static(
            f'Number of iteration "{num_iteration}" is invalid ! Exiting.\n',
            classes="skills-message",
        )
        scroll_view.mount(skills_widget)
        return False

    return True


def generate_py_scanner_config(scroll_view: VerticalScroll, config_table: dict) -> bool:
    import os
    import uuid

    from openhands_cli.constants import CustomConstants
    from openhands_cli.utils import get_current_wd

    cpath = get_current_wd()
    filepath = os.path.join(cpath, "sonar-project.properties")
    lines = []
    lines.append(f"Creating File: {filepath}")

    if os.path.exists(filepath):
        lines.append(f"File {filepath} already exist ! Exiting...")
        skills_widget = Static("\n".join(lines), classes="skills-message")
        scroll_view.mount(skills_widget)
        return False

    with open(filepath, "w") as fd:
        fd.write(f"sonar.projectName={config_table.get('project_name')}\n")
        id_str = str(uuid.uuid4())
        fd.write(f"sonar.projectKey={id_str}\n")
        fd.write("sonar.projectVersion=1.0\n\n")

        proj_type = config_table.get("project_type")
        match proj_type:
            case CustomConstants.PROJECT_TYPE_PYTHON:
                # Source code location
                fd.write(f"sonar.sources={config_table.get('inclusive_path')}\n")
                fd.write(
                    f"sonar.exclusions=**/__pycache__/**,**/.pytest_cache/**, **/.venv/**, {config_table.get('exclusive_path')}\n"
                )
                fd.write("sonar.coverage.exclusions=**/__init__.py, tests/**/*.py\n\n")
                # Test file location
                fd.write("sonar.tests=tests\n")
                fd.write("sonar.test.inclusions=tests/**/*.py\n\n")
                # Language specification
                fd.write("sonar.language=py\n")
                fd.write("sonar.sourceEncoding=UTF-8\n\n")
                # Coverage and unit test reports
                fd.write("sonar.python.coverage.reportPaths=src-coverage.xml\n")
                fd.write("sonar.python.xunit.reportPath=ut-results.xml\n")
            case CustomConstants.PROJECT_TYPE_JAVA:
                # Source code location
                fd.write("sonar.sources=src/main/java\n")
                fd.write(
                    f"sonar.exclusions=**/.idea/**,**/.mvn/**,**/target/**, {config_table.get('exclusive_path')}\n"
                )
                fd.write("sonar.coverage.exclusions=src/test/**/*.java\n\n")
                # Test file location
                fd.write("sonar.tests=src/test/java\n")
                fd.write("sonar.test.inclusions=src/test/java/**/*.java\n")
                # Java specification
                fd.write("sonar.java.binaries=target/classes\n")
                fd.write("sonar.java.test.binaries=target/test-classes\n\n")
                fd.write(
                    "sonar.coverage.jacoco.xmlReportPaths=target/site/jacoco/jacoco.xml\n"
                )
                fd.write("sonar.junit.reportPaths=target/surefire-reports\n\n")
                # Language specification
                fd.write("sonar.language=java\n")
                fd.write("sonar.sourceEncoding=UTF-8\n")
            case CustomConstants.PROJECT_TYPE_UNKNOWN:
                lines.append(UNKNOWN_PROJECT_TEXT)

    lines.append(f"File {filepath} created successfully.")
    skills_widget = Static("\n".join(lines), classes="skills-message")
    scroll_view.mount(skills_widget)
    return True


def run_unit_test_progress(scroll_view: VerticalScroll, proj_type: int) -> bool:
    import subprocess

    from openhands_cli.constants import CustomConstants
    from openhands_cli.utils import get_current_wd

    retval = True
    lines = []

    cpath = get_current_wd()
    lines.append(f"Running Unit Test for entire project in {cpath}\n")

    match proj_type:
        case CustomConstants.PROJECT_TYPE_PYTHON:
            lines.append("Running for Python project, please wait...\n")
            with open("unit_test_result.log", "w") as fd:
                subprocess.run(
                    [
                        "uv",
                        "run",
                        "pytest",
                        "--verbose",
                        "--cov=.",
                        "--cov-report=xml:src-coverage.xml",
                        "--cov-report=html:htmlcov",
                        "--cov-report=term",
                        "--junit-xml=ut-results.xml",
                    ],
                    cwd=cpath,
                    stdout=fd,
                    stderr=fd,
                )
            lines.append("Run completed, check unit_test_result.log for details.\n")
        case CustomConstants.PROJECT_TYPE_JAVA:
            lines.append("Running for Java project, please wait...\n")
            with open("unit_test_result.log", "w") as fd:
                subprocess.run(
                    ["mvn", "clean", "verify", "-Pcoverage"],
                    cwd=cpath,
                    stdout=fd,
                    stderr=fd,
                )
            lines.append("Run completed, check unit_test_result.log for details.\n")
        case CustomConstants.PROJECT_TYPE_UNKNOWN:
            lines.append("Unknow project type.\n")
            retval = False

    skills_widget = Static("\n".join(lines), classes="skills-message")
    scroll_view.mount(skills_widget)
    # scroll_view.scroll_end(animate=False)
    return retval


def post_sonarqube_server_progress(app) -> None:
    import os
    import subprocess

    from openhands_cli.tui.widgets.input_area import InputAreaContainer

    input_area = app.query_one(InputAreaContainer)
    scroll_view = input_area.scroll_view

    app.notify(
        title="Posting result",
        message="Posting Unit Test result and source coverage to SonarQube server. Please wait...\n",
        severity="information",
    )

    # Setup environment variable before running
    sonar_token = os.environ.get("SONAR_TOKEN", "").strip()
    sonar_host = os.environ.get("SONAR_HOST_URL", "http://localhost:9000").strip()

    if not sonar_token:
        scroll_view.mount(
            Static(
                "SONAR_TOKEN is not set. Export SONAR_TOKEN before posting results.\n",
                classes="skills-message",
            )
        )
        app.notify(
            title="Missing Sonar token",
            message="Set SONAR_TOKEN environment variable first.",
            severity="error",
        )
        return

    run_env = dict(os.environ)
    run_env["SONAR_TOKEN"] = sonar_token

    with open("post_sonarqube_server_result.log", "w") as fd:
        subprocess.run(
            [
                "sonar-scanner",
                f"-Dsonar.host.url={sonar_host}",
                "-Dsonar.scm.disabled=true",
                "-Dsonar.filesize.limit=150",
            ],
            env=run_env,
            stdout=fd,
            stderr=fd,
        )

    after_widget = Static(
        "Posting has completed, check post_sonarqube_server_result.log for details.\n",
        classes="skills-message",
    )
    scroll_view.mount(after_widget)
