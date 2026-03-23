import logging
import os
from pathlib import Path

from openhands_cli.instructions.utgen.scripts.java_template import JAVA_SCRIPT_TEMPLATE
from openhands_cli.ut_generation.config import DEFAULT_JAVA_HOME


__all__ = ["get_template_and_placeholders"]

logger = logging.getLogger(__name__)

MAIN_JAVA_DIR = "src/main/java/"
TEST_JAVA_DIR = "src/test/java/"


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
    source_path = Path(source_file_path)

    normalized = source_file_path.replace("\\", "/")
    if MAIN_JAVA_DIR in normalized:
        path_str = normalized.replace(MAIN_JAVA_DIR, TEST_JAVA_DIR)
        return path_str.replace(".java", "Test.java")

    # Fallback for non-standard Java layouts (single file or custom dirs)
    return str(source_path.with_name(f"{source_path.stem}Test.java"))


def detect_build_tool(source_file_path: str) -> tuple[str, Path]:
    """
    Detect Java build tool by checking for build configuration files.

    Checks in order:
    1. pom.xml → Maven
    2. build.gradle or build.gradle.kts → Gradle

    Args:
        source_file_path: Path to the Java source file. Build files are searched
            from this path upward to the filesystem root.

    Returns:
        Tuple of (build tool identifier, project root path).

    Raises:
        ValueError: If neither pom.xml nor build.gradle files are found.
    """
    current = Path(source_file_path).resolve().parent

    for candidate in [current, *current.parents]:
        if (candidate / "pom.xml").exists():
            return "maven", candidate

        if (candidate / "build.gradle").exists() or (
            candidate / "build.gradle.kts"
        ).exists():
            return "gradle", candidate

    raise ValueError(
        "Cannot detect Java build tool for "
        f"{source_file_path}: no pom.xml/build.gradle found in this directory or parent directories. "
        "Please run from a Maven/Gradle project root or add a build file first."
    )


def detect_java_home() -> str:
    """
    Get Java home directory path.

    Returns:
        Path to Java installation directory from JAVA_HOME environment variable, or DEFAULT_JAVA_HOME if not set.
    """
    return os.environ.get("JAVA_HOME") or DEFAULT_JAVA_HOME


def build_test_command(test_file_path: str, build_tool: str, project_root: Path) -> str:
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
        return f'cd "{project_root}" && mvn verify -P coverage -Dtest={classname}'

    if build_tool == "gradle":
        # Extract fully qualified class name from Java test file path
        normalized = test_file_path.replace("\\", "/")
        if TEST_JAVA_DIR in normalized:
            path = normalized.replace(TEST_JAVA_DIR, "").replace(".java", "")
            fq_classname = path.replace("/", ".")
        else:
            fq_classname = Path(test_file_path).stem

        gradle_cmd = "./gradlew" if (project_root / "gradlew").exists() else "gradle"
        return (
            f'cd "{project_root}" && '
            f'{gradle_cmd} test jacocoTestReport --tests "{fq_classname}"'
        )

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
    trace_source: str,
    trace_flow: str,
    project_name: str,
) -> tuple[str, dict[str, str]]:
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
    build_tool, project_root = detect_build_tool(source_file_path)
    test_command = build_test_command(test_file_path, build_tool, project_root)

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
        "TRACE_SOURCE": trace_source,
        "TRACE_FLOW": trace_flow,
        "PROJECT": project_name,
    }

    logger.info(f"Get template and placeholders for {source_file_path}")
    return JAVA_SCRIPT_TEMPLATE, placeholders
