"""
Unit test generation utility for Python and Java projects.

This module generates Keploy AI-powered unit test scripts by:
1. Detecting the source file language (Python/Java)
2. Deriving the appropriate test file path
3. Building language-specific test commands
4. Rendering a bash script template with placeholders
5. Writing the generated script to disk

Attributes:
    OUTPUT_SCRIPT_NAME: Default name for the generated bash script.
    DEFAULT_JAVA_HOME: Default Java installation path for Java projects.
"""

import os
from pathlib import Path

from openhands_cli.instructions.utgen.scripts.java_template import (
    JAVA_SCRIPT_TEMPLATE,
)
from openhands_cli.instructions.utgen.scripts.python_template import (
    PYTHON_SCRIPT_TEMPLATE,
)


OUTPUT_SCRIPT_NAME = "Gen_UnitTest.sh"
DEFAULT_JAVA_HOME = "/usr/lib/jvm/java-21-openjdk-amd64"

_LANGUAGE_MAP = {
    ".py": "python",
    ".java": "java",
}


def _detect_language(source_file_path: str) -> str:
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
    language = _LANGUAGE_MAP.get(suffix)
    if language is None:
        raise ValueError(f"Unsupported file extension: {suffix}")
    return language


def _derive_python_test_path(source_file_path: str) -> str:
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
    sub_parts = parts[1:]
    test_filename = f"test_{sub_parts[-1]}"
    return str(Path("tests", *sub_parts[:-1], test_filename))


def _derive_java_test_path(source_file_path: str) -> str:
    """
    Derive test file path for Java source file.

    Converts source file path from main to test directory and appends
    'Test' suffix to the class name.

    Args:
        source_file_path: Path to the Java source file in src/main/java/.

    Returns:
        Path to the corresponding test file in src/test/java/.
    """
    path_str = source_file_path.replace("src/main/java/", "src/test/java/")
    path_str = path_str.replace(".java", "Test.java")
    return path_str


def _derive_test_file_path(source_file_path: str, language: str) -> str:
    """
    Derive test file path based on programming language.

    Dispatches to language-specific path derivation function.

    Args:
        source_file_path: Path to the source file.
        language: Language identifier ('python' or 'java').

    Returns:
        Path to the corresponding test file.
    """
    if language == "python":
        return _derive_python_test_path(source_file_path)
    return _derive_java_test_path(source_file_path)


def _detect_java_build_tool() -> str:
    """
    Detect Java build tool by checking for build configuration files.

    Checks in order:
    1. pom.xml → Maven
    2. build.gradle or build.gradle.kts → Gradle

    Returns:
        Build tool identifier: 'maven' or 'gradle'.

    Raises:
        ValueError: If neither pom.xml nor build.gradle files are found.
    """
    if Path("pom.xml").exists():
        return "maven"
    if Path("build.gradle").exists() or Path("build.gradle.kts").exists():
        return "gradle"
    raise ValueError("Cannot detect Java build tool: no pom.xml or build.gradle found")


def _detect_java_home() -> str:
    """
    Get Java home directory path.

    Returns:
        Path to Java installation directory from JAVA_HOME environment
        variable, or DEFAULT_JAVA_HOME if not set.
    """
    return os.environ.get("JAVA_HOME", DEFAULT_JAVA_HOME)


def _build_test_command_python(source_file_path: str, test_file_path: str) -> str:
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
        f"-m pytest {test_file_path} && uv run coverage xml"
    )


def _extract_java_test_classname(test_file_path: str) -> str:
    """
    Extract simple class name from Java test file path.

    Args:
        test_file_path: Path to the Java test file.

    Returns:
        Class name without path or extension.
    """
    return Path(test_file_path).stem


def _extract_java_fully_qualified_classname(test_file_path: str) -> str:
    """
    Extract fully qualified class name from Java test file path.

    Args:
        test_file_path: Path to the Java test file under src/test/java/.

    Returns:
        Fully qualified class name with package prefix.
    """
    path = test_file_path.replace("src/test/java/", "").replace(".java", "")
    return path.replace("/", ".")


def _build_test_command_java(test_file_path: str, build_tool: str) -> str:
    """
    Build test command for Java projects with coverage.

    Args:
        test_file_path: Path to the test file.
        build_tool: Build tool identifier ('maven' or 'gradle').

    Returns:
        Shell command string for running tests with coverage.
    """
    if build_tool == "maven":
        classname = _extract_java_test_classname(test_file_path)
        return f"mvn verify -P coverage -Dtest={classname}"
    fq_classname = _extract_java_fully_qualified_classname(test_file_path)
    return f'./gradlew test jacocoTestReport --tests "{fq_classname}"'


def _get_build_clean_command(build_tool: str) -> str:
    """
    Get build tool clean command.

    Args:
        build_tool: Build tool identifier ('maven' or 'gradle').

    Returns:
        Shell command string for cleaning build artifacts.
    """
    if build_tool == "maven":
        return "mvn clean"
    if Path("gradlew").exists():
        return "chmod +x ./gradlew && ./gradlew clean"
    return "gradle clean"


def _get_coverage_report_path(build_tool: str) -> str:
    """
    Get coverage report XML path for build tool.

    Args:
        build_tool: Build tool identifier ('maven' or 'gradle').

    Returns:
        Path to the JaCoCo coverage report XML file.
    """
    if build_tool == "maven":
        return "target/site/jacoco/jacoco.xml"
    return "build/reports/jacoco/test/jacocoTestReport.xml"


def _create_test_file_if_not_exists(test_file_path: str) -> None:
    """
    Create empty test file and parent directories if they don't exist.

    Args:
        test_file_path: Path to the test file to create.
    """
    path = Path(test_file_path)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()


def _render_script(template: str, placeholders: dict[str, str]) -> str:
    """
    Render bash script template by replacing placeholders.

    Replaces all `{{KEY}}` patterns with corresponding values from the
    placeholders dictionary, then converts remaining `{{` to `{` and
    `}}` to `}` to handle bash variable escaping (e.g., `${{VAR}}` → `${VAR}`).

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


def _write_script(content: str, output_path: str = OUTPUT_SCRIPT_NAME) -> None:
    """
    Write rendered script content to output file.

    Args:
        content: Script content to write.
        output_path: Path to the output file. Defaults to OUTPUT_SCRIPT_NAME.
    """
    Path(output_path).write_text(content)


def generate_unit_test_script(
    source_file_path: str,
    expected_coverage: int = 85,
    max_iteration: int = 5,
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
    language = _detect_language(source_file_path)
    test_file_path = _derive_test_file_path(source_file_path, language)
    _create_test_file_if_not_exists(test_file_path)

    if language == "python":
        template = PYTHON_SCRIPT_TEMPLATE
        test_command = _build_test_command_python(source_file_path, test_file_path)
        placeholders = {
            "SOURCE_FILE_PATH": source_file_path,
            "TEST_FILE_PATH": test_file_path,
            "TEST_COMMAND": test_command,
            "EXPECTED_COVERAGE": str(expected_coverage),
            "MAX_ITERATIONS": str(max_iteration),
        }
    else:
        build_tool = _detect_java_build_tool()
        template = JAVA_SCRIPT_TEMPLATE
        test_command = _build_test_command_java(test_file_path, build_tool)
        placeholders = {
            "SOURCE_FILE_PATH": source_file_path,
            "TEST_FILE_PATH": test_file_path,
            "TEST_COMMAND": test_command,
            "EXPECTED_COVERAGE": str(expected_coverage),
            "MAX_ITERATIONS": str(max_iteration),
            "JAVA_HOME": _detect_java_home(),
            "BUILD_CLEAN_COMMAND": _get_build_clean_command(build_tool),
            "COVERAGE_REPORT_PATH": _get_coverage_report_path(build_tool),
        }

    content = _render_script(template, placeholders)
    _write_script(content)


if __name__ == "__main__":
    generate_unit_test_script(
        source_file_path="openhands_cli/acp_impl/utils/mcp.py",
        expected_coverage=85,
        max_iteration=5,
    )
