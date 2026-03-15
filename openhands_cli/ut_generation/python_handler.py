from pathlib import Path
from typing import Dict, Tuple

from loguru import logger

from openhands_cli.instructions.utgen.scripts.python_template import (
    PYTHON_SCRIPT_TEMPLATE,
)

__all__ = ["get_template_and_placeholders"]


def derive_test_path(source_file_path: str) -> str:
    """
    Derive test file path for Python source file.

    Converts source file path to test file path following the convention:
    - Source: `<module_path>/<filename>.py`
    - Test: `tests/<module_path>/test_<filename>.py`

    Args:
        source_file_path: Path to the Python source file.

    Returns:
        Path to the corresponding test file.
    """
    parts = Path(source_file_path).parts
    if len(parts) == 1:
        test_filename = f"tests_{parts[0]}"
        return str(Path("tests", test_filename))

    test_filename = f"test_{parts[-1]}"
    return str(Path("tests", *parts[:-1], test_filename))


def build_test_command(source_file_path: str, test_file_path: str) -> str:
    """
    Build pytest coverage command for Python projects.

    Args:
        source_file_path: Path to the source file under test.
        test_file_path: Path to the test file.

    Returns:
        Shell command string that runs pytest with coverage and generates
        Cobertura XML report.
    """
    return (
        f"uv run coverage run --include={source_file_path} "
        f"-m pytest {test_file_path} -o addopts= && uv run coverage xml"
    )


def get_template_and_placeholders(
    source_file_path: str, expected_coverage: int, max_iteration: int
) -> Tuple[str, Dict[str, str]]:
    test_file_path = derive_test_path(source_file_path)
    test_command = build_test_command(source_file_path, test_file_path)

    placeholders = {
        "SOURCE_FILE_PATH": source_file_path,
        "TEST_FILE_PATH": test_file_path,
        "TEST_COMMAND": test_command,
        "EXPECTED_COVERAGE": str(expected_coverage),
        "MAX_ITERATIONS": str(max_iteration),
    }

    logger.info(f"Get template and placeholders for {source_file_path}")
    return PYTHON_SCRIPT_TEMPLATE, placeholders
