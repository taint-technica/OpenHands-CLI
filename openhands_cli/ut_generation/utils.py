from pathlib import Path

from openhands_cli.ut_generation.config import LANGUAGE_MAP

__all__ = ["detect_language", "create_test_file_if_not_exists"]


def detect_language(source_file_path: str) -> str:
    """
    Detect programming language from file extension.

    Args:
        source_file_path: Path to the source file to analyze.

    Returns:
        Language identifier: 'python' for .py files, 'java' for .java files.

    Raises:
        ValueError: If the file extension is not supported (not .py or .java).
    """
    suffix = Path(source_file_path).suffix
    language = LANGUAGE_MAP.get(suffix)
    if language is None:
        raise ValueError(f"Unsupported file extension: {suffix}")
    return language


def create_test_file_if_not_exists(test_file_path: str) -> None:
    """
    Create empty test file and parent directories if they don't exist.

    Args:
        test_file_path: Path to the test file to create.
    """
    path = Path(test_file_path)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
