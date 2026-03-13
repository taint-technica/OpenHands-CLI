"""Unit tests for openhands_cli.gen_unit_test module."""
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from openhands_cli.gen_unit_test import (
    OUTPUT_SCRIPT_NAME,
    _build_test_command_java,
    _build_test_command_python,
    _create_test_file_if_not_exists,
    _detect_java_build_tool,
    _detect_java_home,
    _detect_language,
    _derive_java_test_path,
    _derive_python_test_path,
    _derive_test_file_path,
    _extract_java_fully_qualified_classname,
    _extract_java_test_classname,
    _get_build_clean_command,
    _get_coverage_report_path,
    _render_script,
    _write_script,
    generate_unit_test_script,
)


# ---------------------------------------------------------------------------
# _detect_language
# ---------------------------------------------------------------------------


def test_detect_language_python():
    assert _detect_language("openhands_cli/utils/mcp.py") == "python"


def test_detect_language_java():
    assert _detect_language("src/main/java/com/example/Foo.java") == "java"


def test_detect_language_unsupported():
    with pytest.raises(ValueError, match="Unsupported file extension"):
        _detect_language("src/main/Foo.ts")


# ---------------------------------------------------------------------------
# _derive_python_test_path
# ---------------------------------------------------------------------------


def test_derive_python_test_path_standard():
    result = _derive_python_test_path("openhands_cli/acp_impl/utils/mcp.py")
    assert result == str(Path("tests/acp_impl/utils/test_mcp.py"))


def test_derive_python_test_path_single_level():
    result = _derive_python_test_path("mypackage/utils.py")
    assert result == str(Path("tests/test_utils.py"))


def test_derive_python_test_path_deep():
    result = _derive_python_test_path("src/a/b/c/foo.py")
    assert result == str(Path("tests/a/b/c/test_foo.py"))


# ---------------------------------------------------------------------------
# _derive_java_test_path
# ---------------------------------------------------------------------------


def test_derive_java_test_path_standard():
    result = _derive_java_test_path(
        "src/main/java/com/example/service/ContactService.java"
    )
    assert result == "src/test/java/com/example/service/ContactServiceTest.java"


def test_derive_java_test_path_simple():
    result = _derive_java_test_path("src/main/java/com/example/Foo.java")
    assert result == "src/test/java/com/example/FooTest.java"


# ---------------------------------------------------------------------------
# _derive_test_file_path
# ---------------------------------------------------------------------------


def test_derive_test_file_path_dispatches_python():
    result = _derive_test_file_path("pkg/a/foo.py", "python")
    assert result == str(Path("tests/a/test_foo.py"))


def test_derive_test_file_path_dispatches_java():
    result = _derive_test_file_path(
        "src/main/java/com/example/Bar.java", "java"
    )
    assert result == "src/test/java/com/example/BarTest.java"


# ---------------------------------------------------------------------------
# _detect_java_build_tool
# ---------------------------------------------------------------------------


def test_detect_java_build_tool_maven(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pom.xml").write_text("<project/>")
    assert _detect_java_build_tool() == "maven"


def test_detect_java_build_tool_gradle(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "build.gradle").write_text("plugins {}")
    assert _detect_java_build_tool() == "gradle"


def test_detect_java_build_tool_gradle_kts(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "build.gradle.kts").write_text("plugins {}")
    assert _detect_java_build_tool() == "gradle"


def test_detect_java_build_tool_not_found(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="Cannot detect Java build tool"):
        _detect_java_build_tool()


def test_detect_java_build_tool_maven_takes_priority(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pom.xml").write_text("<project/>")
    (tmp_path / "build.gradle").write_text("plugins {}")
    assert _detect_java_build_tool() == "maven"


# ---------------------------------------------------------------------------
# _detect_java_home
# ---------------------------------------------------------------------------


def test_detect_java_home_from_env():
    with patch.dict(os.environ, {"JAVA_HOME": "/custom/jdk"}):
        assert _detect_java_home() == "/custom/jdk"


def test_detect_java_home_default():
    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop("JAVA_HOME", None)
        result = _detect_java_home()
    assert result == "/usr/lib/jvm/java-21-openjdk-amd64"


# ---------------------------------------------------------------------------
# _build_test_command_python
# ---------------------------------------------------------------------------


def test_build_test_command_python():
    cmd = _build_test_command_python(
        "openhands_cli/utils/mcp.py", "tests/utils/test_mcp.py"
    )
    assert cmd == (
        "uv run coverage run --include=openhands_cli/utils/mcp.py "
        "-m pytest tests/utils/test_mcp.py && uv run coverage xml"
    )


# ---------------------------------------------------------------------------
# _extract_java_test_classname / _extract_java_fully_qualified_classname
# ---------------------------------------------------------------------------


def test_extract_java_test_classname():
    result = _extract_java_test_classname(
        "src/test/java/com/example/service/ContactServiceTest.java"
    )
    assert result == "ContactServiceTest"


def test_extract_java_fully_qualified_classname():
    result = _extract_java_fully_qualified_classname(
        "src/test/java/com/example/service/ContactServiceTest.java"
    )
    assert result == "com.example.service.ContactServiceTest"


# ---------------------------------------------------------------------------
# _build_test_command_java
# ---------------------------------------------------------------------------


def test_build_test_command_java_maven():
    cmd = _build_test_command_java(
        "src/test/java/com/example/service/ContactServiceTest.java", "maven"
    )
    assert cmd == "mvn verify -P coverage -Dtest=ContactServiceTest"


def test_build_test_command_java_gradle():
    cmd = _build_test_command_java(
        "src/test/java/com/example/service/ContactServiceTest.java", "gradle"
    )
    assert cmd == (
        './gradlew test jacocoTestReport --tests '
        '"com.example.service.ContactServiceTest"'
    )


# ---------------------------------------------------------------------------
# _get_build_clean_command
# ---------------------------------------------------------------------------


def test_get_build_clean_command_maven():
    assert _get_build_clean_command("maven") == "mvn clean"


def test_get_build_clean_command_gradle_with_wrapper(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "gradlew").write_text("#!/bin/bash")
    assert _get_build_clean_command("gradle") == (
        "chmod +x ./gradlew && ./gradlew clean"
    )


def test_get_build_clean_command_gradle_no_wrapper(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert _get_build_clean_command("gradle") == "gradle clean"


# ---------------------------------------------------------------------------
# _get_coverage_report_path
# ---------------------------------------------------------------------------


def test_get_coverage_report_path_maven():
    assert _get_coverage_report_path("maven") == "target/site/jacoco/jacoco.xml"


def test_get_coverage_report_path_gradle():
    assert _get_coverage_report_path("gradle") == (
        "build/reports/jacoco/test/jacocoTestReport.xml"
    )


# ---------------------------------------------------------------------------
# _create_test_file_if_not_exists
# ---------------------------------------------------------------------------


def test_create_test_file_creates_file_and_dirs(tmp_path):
    test_path = str(tmp_path / "tests" / "a" / "b" / "test_foo.py")
    _create_test_file_if_not_exists(test_path)
    assert Path(test_path).exists()
    assert Path(test_path).read_text() == ""


def test_create_test_file_does_not_overwrite_existing(tmp_path):
    test_path = tmp_path / "tests" / "test_foo.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text("existing content")
    _create_test_file_if_not_exists(str(test_path))
    assert test_path.read_text() == "existing content"


# ---------------------------------------------------------------------------
# _render_script
# ---------------------------------------------------------------------------


def test_render_script_replaces_placeholders():
    template = 'SOURCE="{{SOURCE_FILE_PATH}}" TEST="{{TEST_FILE_PATH}}"'
    result = _render_script(
        template,
        {"SOURCE_FILE_PATH": "src/foo.py", "TEST_FILE_PATH": "tests/test_foo.py"},
    )
    assert result == 'SOURCE="src/foo.py" TEST="tests/test_foo.py"'


def test_render_script_converts_escaped_braces():
    template = 'VAR="${{VAR:-default}}"'
    result = _render_script(template, {})
    assert result == 'VAR="${VAR:-default}"'


def test_render_script_array_expansion():
    template = 'keploy gen "${{ARGS[@]}}"'
    result = _render_script(template, {})
    assert result == 'keploy gen "${ARGS[@]}"'


# ---------------------------------------------------------------------------
# _write_script
# ---------------------------------------------------------------------------


def test_write_script_creates_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_script("#!/bin/bash\necho hello")
    content = (tmp_path / OUTPUT_SCRIPT_NAME).read_text()
    assert content == "#!/bin/bash\necho hello"


def test_write_script_overwrites_existing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / OUTPUT_SCRIPT_NAME).write_text("old content")
    _write_script("new content")
    assert (tmp_path / OUTPUT_SCRIPT_NAME).read_text() == "new content"


# ---------------------------------------------------------------------------
# generate_unit_test_script — integration
# ---------------------------------------------------------------------------


def test_generate_python_script(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    generate_unit_test_script("openhands_cli/acp_impl/utils/mcp.py", 85, 5)

    script = (tmp_path / OUTPUT_SCRIPT_NAME).read_text()
    assert '--sourceFilePath="openhands_cli/acp_impl/utils/mcp.py"' in script
    assert '--testFilePath="tests/acp_impl/utils/test_mcp.py"' in script
    assert "--coverageFormat=\"cobertura\"" in script
    assert "--expected-coverage=85" in script
    assert "--maxIterations=5" in script
    assert "uv run coverage run" in script
    assert "LLM_BASE_URL" not in script
    assert "{{" not in script

    test_file = tmp_path / "tests" / "acp_impl" / "utils" / "test_mcp.py"
    assert test_file.exists()


def test_generate_python_script_custom_coverage(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    generate_unit_test_script("pkg/foo.py", 90, 3)

    script = (tmp_path / OUTPUT_SCRIPT_NAME).read_text()
    assert "--expected-coverage=90" in script
    assert "--maxIterations=3" in script


def test_generate_java_maven_script(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pom.xml").write_text("<project/>")

    generate_unit_test_script(
        "src/main/java/com/example/service/ContactService.java", 90, 3
    )

    script = (tmp_path / OUTPUT_SCRIPT_NAME).read_text()
    assert '--testFilePath="src/test/java/com/example/service/ContactServiceTest.java"' in script
    assert '--testCommand="mvn verify -P coverage -Dtest=ContactServiceTest"' in script
    assert '--coverageReportPath="target/site/jacoco/jacoco.xml"' in script
    assert "--coverageFormat=\"jacoco\"" in script
    assert "--expected-coverage=90" in script
    assert "mvn clean" in script
    assert "{{" not in script

    test_file = (
        tmp_path
        / "src/test/java/com/example/service/ContactServiceTest.java"
    )
    assert test_file.exists()


def test_generate_java_gradle_script(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "build.gradle").write_text("plugins {}")

    generate_unit_test_script(
        "src/main/java/com/example/Foo.java", 80, 10
    )

    script = (tmp_path / OUTPUT_SCRIPT_NAME).read_text()
    assert 'com.example.FooTest' in script
    assert '--coverageReportPath="build/reports/jacoco/test/jacocoTestReport.xml"' in script
    assert "--expected-coverage=80" in script
    assert "--maxIterations=10" in script


def test_generate_script_overwrites_existing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / OUTPUT_SCRIPT_NAME).write_text("old content")
    generate_unit_test_script("pkg/bar.py", 85, 5)
    script = (tmp_path / OUTPUT_SCRIPT_NAME).read_text()
    assert "old content" not in script
    assert "keploy gen" in script


def test_generate_unsupported_extension_raises(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="Unsupported file extension"):
        generate_unit_test_script("src/main.ts", 85, 5)
