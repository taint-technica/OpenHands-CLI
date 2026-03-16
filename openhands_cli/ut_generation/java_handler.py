import os
from pathlib import Path
from typing import Dict, Tuple

from loguru import logger

from openhands_cli.instructions.utgen.scripts.java_template import JAVA_SCRIPT_TEMPLATE
from openhands_cli.ut_generation.config import DEFAULT_JAVA_HOME


__all__ = ["get_template_and_placeholders"]


def derive_test_path(source_file_path: str) -> str:
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


def detect_build_tool() -> str:
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


def detect_java_home() -> str:
    """
    Get Java home directory path.

    Returns:
        Path to Java installation directory from JAVA_HOME environment variable, or DEFAULT_JAVA_HOME if not set.
    """
    return os.environ.get("JAVA_HOME") or DEFAULT_JAVA_HOME


def build_test_command(test_file_path: str, build_tool: str) -> str:
    """
    Build test command for Java projects with coverage.

    Args:
        test_file_path: Path to the test file.
        build_tool: Build tool identifier ('maven' or 'gradle').

    Returns:
        Shell command string for running tests with coverage.
    """
    if build_tool == "maven":
        # Extract simple class name from Java test file path
        classname = Path(test_file_path).stem
        return f"mvn verify -P coverage -Dtest={classname}"

    if build_tool == "gradle":
        # Extract fully qualified class name from Java test file path
        path = test_file_path.replace("src/test/java/", "").replace(".java", "")
        fq_classname = path.replace("/", ".")
        return f'./gradlew test jacocoTestReport --tests "{fq_classname}"'

    msg = f"Error: Not support for build tool {build_tool}"
    logger.error(msg)
    raise ValueError(msg)


def get_build_clean_command(build_tool: str) -> str:
    """
    Get build tool clean command.

    Args:
        build_tool: Build tool identifier ('maven' or 'gradle').

    Returns:
        Shell command string for cleaning build artifacts.
    """
    if build_tool == "maven":
        return "mvn clean"

    if build_tool == "gradle":
        if Path("gradlew").exists():
            return "chmod +x ./gradlew && ./gradlew clean"
        return "gradle clean"

    raise ValueError(f"Unsupported build tool: {build_tool}")


def get_coverage_report_path(build_tool: str) -> str:
    """
    Get coverage report XML path for build tool.

    Args:
        build_tool: Build tool identifier ('maven' or 'gradle').

    Returns:
        Path to the JaCoCo coverage report XML file.
    """
    if build_tool == "maven":
        return "target/site/jacoco/jacoco.xml"

    if build_tool == "gradle":
        return "build/reports/jacoco/test/jacocoTestReport.xml"

    msg = f"Error: Not support coverage report for build tool {build_tool}"
    logger.error(msg)
    raise ValueError(msg)


def get_template_and_placeholders(
    source_file_path: str,
    expected_coverage: int,
    max_iteration: int,
    api_key: str,
    llm_base_url: str,
    model: str,
) -> Tuple[str, Dict[str, str]]:
    """
    Generate the bash script template and placeholders for Java projects.

    Args:
        source_file_path: Path to the Java source file under test.
        expected_coverage: Target coverage percentage.
        max_iteration: Maximum iterations for Keploy AI to reach the target.
        api_key: API KEY for LLM.
        llm_base_url: LLM Base url.
        model: model name.

    Returns:
        A tuple containing:
            - str: The Java-specific bash script template.
            - dict: A mapping of placeholder keys to their concrete values,
              including Java-specific keys like 'JAVA_HOME', 'BUILD_CLEAN_COMMAND', and 'COVERAGE_REPORT_PATH'.

    Raises:
        ValueError: If neither pom.xml nor build.gradle can be found in the
            project root (propagated from build tool detection).
    """
    test_file_path = derive_test_path(source_file_path)
    build_tool = detect_build_tool()
    test_command = build_test_command(test_file_path, build_tool)

    coverage_report_path = get_coverage_report_path(build_tool)

    placeholders = {
        "SOURCE_FILE_PATH": source_file_path,
        "TEST_FILE_PATH": test_file_path,
        "TEST_COMMAND": test_command,
        "EXPECTED_COVERAGE": str(expected_coverage),
        "MAX_ITERATIONS": str(max_iteration),
        "JAVA_HOME": detect_java_home(),
        "BUILD_CLEAN_COMMAND": get_build_clean_command(build_tool),
        "COVERAGE_REPORT_PATH": coverage_report_path,
        "API_KEY": api_key,
        "LLM_BASE_URL": llm_base_url,
        "MODEL": model,
    }

    logger.info(f"Get template and placeholders for {source_file_path}")
    return JAVA_SCRIPT_TEMPLATE, placeholders
