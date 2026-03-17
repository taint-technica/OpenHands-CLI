import logging
from pathlib import Path
from typing import Dict

from openhands_cli.ut_generation import java_handler, python_handler
from openhands_cli.ut_generation.config import OUTPUT_SCRIPT_NAME
from openhands_cli.ut_generation.protocols import LanguageHandler
from openhands_cli.ut_generation.utils import (
    create_test_file_if_not_exists,
    detect_language,
)


logger = logging.getLogger(__name__)


HANDLER: Dict[str, LanguageHandler] = {"python": python_handler, "java": java_handler}


def render_script(template: str, placeholders: dict[str, str]) -> str:
    """
    Render bash script template by replacing placeholders.

    Args:
        template: Bash script template with `{{KEY}}` placeholders.
        placeholders: Dictionary mapping placeholder keys to replacement values.

    Returns:
        Rendered script content with all placeholders replaced.
    """
    content = template
    for key, value in placeholders.items():
        content = content.replace(f"{{{{{key}}}}}", value)
    return content.replace("{{", "{").replace("}}", "}")


def write_script(content: str, output_path: str = OUTPUT_SCRIPT_NAME) -> None:
    """
    Write rendered script content to output file.

    Args:
        content: Script content to write.
        output_path: Path to the output file. Defaults to OUTPUT_SCRIPT_NAME.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def generate_unit_test_script(
    source_file_path: str,
    expected_coverage: int,
    max_iteration: int,
    api_key: str,
    llm_base_url: str,
    model: str,
    trace_source: str = "keploy",
    trace_flow: str = "utgen",
    project_name: str | None = None,
) -> None:
    """
    Generate Keploy unit test script for given source file.

    Args:
        source_file_path: Path to the source file to generate tests for.
        expected_coverage: Target coverage percentage (default: 85).
        max_iteration: Maximum iterations for Keploy AI to reach coverage
            target (default: 5).

    Raises:
        ValueError: If the file extension is unsupported or Java build tool
            cannot be detected.
    """
    language = detect_language(source_file_path)
    handler = HANDLER.get(language)

    if not handler:
        raise ValueError(
            f"Unsupported programming language or extension for: {source_file_path}"
        )

    resolved_project = project_name or Path.cwd().name or "unknown"

    template, placeholder = handler.get_template_and_placeholders(
        source_file_path,
        expected_coverage,
        max_iteration,
        api_key,
        llm_base_url,
        model,
        trace_source,
        trace_flow,
        resolved_project,
    )

    create_test_file_if_not_exists(placeholder["TEST_FILE_PATH"])

    content = render_script(template=template, placeholders=placeholder)
    logger.info(f"Generate Keploy unit test script for {source_file_path}")
    write_script(content=content)
