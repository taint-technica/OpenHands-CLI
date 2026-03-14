"""Integration tests for openhands_cli.ut_generation module.

Tests multiple modules working together through realistic scenarios.
"""

import pytest

from openhands_cli.ut_generation.generator import (
    derive_test_file_path,
    generate_unit_test_script,
    render_script,
    write_script,
)
from openhands_cli.ut_generation.utils import detect_language


class TestPythonPipelineIntegration:
    """Integration tests for the full Python pipeline."""

    def test_language_detection_to_test_path(self):
        """detect_language + derive_test_file_path work together."""
        source = "openhands_cli/ut_generation/utils.py"
        language = detect_language(source)
        assert language == "python"
        test_path = derive_test_file_path(source, language)
        assert isinstance(test_path, str)
        assert "test_utils.py" in test_path
        assert test_path.startswith("tests/")

    def test_python_render_script_with_real_placeholders(self):
        """render_script produces valid bash with Python-specific placeholders."""
        from openhands_cli.ut_generation import python_handler

        source = "src/mymodule.py"
        template, placeholders = python_handler.get_template_and_placeholders(
            source, 85, 5
        )
        result = render_script(template, placeholders)

        assert "#!/bin/bash" in result
        assert "src/mymodule.py" in result
        assert "test_mymodule.py" in result
        assert "pytest" in result
        assert "85" in result
        assert "5" in result
        # No remaining double braces from placeholders
        assert "{{SOURCE_FILE_PATH}}" not in result
        assert "{{TEST_FILE_PATH}}" not in result
        assert "{{TEST_COMMAND}}" not in result
        assert "{{EXPECTED_COVERAGE}}" not in result
        assert "{{MAX_ITERATIONS}}" not in result

    def test_python_rendered_script_has_valid_bash_array_syntax(self):
        """render_script converts {{X}} to {X} for bash array syntax."""
        from openhands_cli.ut_generation import python_handler

        template, placeholders = python_handler.get_template_and_placeholders(
            "src/foo.py", 85, 5
        )
        result = render_script(template, placeholders)

        # Bash: keploy gen "${KEPLOY_ARGS[@]}"
        assert "${KEPLOY_ARGS[@]}" in result
        # Bash: ${COVERAGE_REPORT_PATH:-coverage.xml}
        assert "${COVERAGE_REPORT_PATH:-coverage.xml}" in result

    def test_python_write_and_read_back(self, tmp_path, monkeypatch):
        """write_script produces a readable file with correct content."""
        monkeypatch.chdir(tmp_path)
        from openhands_cli.ut_generation import python_handler

        template, placeholders = python_handler.get_template_and_placeholders(
            "src/foo.py", 80, 3
        )
        content = render_script(template, placeholders)
        write_script(content)

        output = tmp_path / "Gen_UnitTest.sh"
        assert output.exists()
        script_text = output.read_text()
        assert "src/foo.py" in script_text
        assert "80" in script_text
        assert "3" in script_text

    def test_python_generate_script_creates_test_file_and_script(self, tmp_path, monkeypatch):
        """generate_unit_test_script creates both test file and Gen_UnitTest.sh."""
        monkeypatch.chdir(tmp_path)
        source = "src/mymodule.py"
        generate_unit_test_script(source, expected_coverage=80, max_iteration=3)

        script = tmp_path / "Gen_UnitTest.sh"
        assert script.exists()
        # Test file is created at derived path
        # Python: src/mymodule.py → tests/test_mymodule.py
        test_file = tmp_path / "tests" / "test_mymodule.py"
        assert test_file.exists()


class TestJavaPipelineIntegration:
    """Integration tests for the full Java pipeline."""

    def test_language_detection_to_test_path(self):
        """detect_language + derive_test_file_path work together for Java."""
        source = "src/main/java/com/example/UserService.java"
        language = detect_language(source)
        assert language == "java"
        test_path = derive_test_file_path(source, language)
        assert isinstance(test_path, str)
        assert "UserServiceTest.java" in test_path
        assert "src/test/java" in test_path

    def test_java_render_script_with_real_placeholders_maven(self, tmp_path, monkeypatch):
        """render_script produces valid bash with Java/Maven-specific placeholders."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pom.xml").touch()
        from openhands_cli.ut_generation import java_handler

        source = "src/main/java/com/example/Calculator.java"
        template, placeholders = java_handler.get_template_and_placeholders(source, 90, 6)
        result = render_script(template, placeholders)

        assert "#!/bin/bash" in result
        assert source in result
        assert "CalculatorTest.java" in result
        assert "90" in result
        assert "6" in result
        assert "jacoco" in result
        assert "mvn" in result
        assert "JAVA_HOME" in result
        # No remaining double-brace placeholders
        assert "{{SOURCE_FILE_PATH}}" not in result
        assert "{{JAVA_HOME}}" not in result
        assert "{{BUILD_CLEAN_COMMAND}}" not in result
        assert "{{COVERAGE_REPORT_PATH}}" not in result

    def test_java_rendered_script_has_valid_bash_array_syntax(self, tmp_path, monkeypatch):
        """render_script converts {{X}} to {X} for bash array syntax."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pom.xml").touch()
        from openhands_cli.ut_generation import java_handler

        template, placeholders = java_handler.get_template_and_placeholders(
            "src/main/java/Foo.java", 85, 5
        )
        result = render_script(template, placeholders)
        assert "${KEPLOY_ARGS[@]}" in result

    def test_java_generate_script_maven(self, tmp_path, monkeypatch):
        """generate_unit_test_script works for Java Maven project."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pom.xml").touch()

        source = "src/main/java/com/example/MyService.java"
        generate_unit_test_script(source, expected_coverage=85, max_iteration=5)

        script = tmp_path / "Gen_UnitTest.sh"
        assert script.exists()
        test_file = tmp_path / "src" / "test" / "java" / "com" / "example" / "MyServiceTest.java"
        assert test_file.exists()

    def test_java_generate_script_gradle(self, tmp_path, monkeypatch):
        """generate_unit_test_script works for Java Gradle project."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "build.gradle").touch()

        source = "src/main/java/Foo.java"
        generate_unit_test_script(source, expected_coverage=75, max_iteration=4)

        script = tmp_path / "Gen_UnitTest.sh"
        assert script.exists()
        content = script.read_text()
        assert "build/reports/jacoco" in content


class TestErrorHandlingIntegration:
    """Integration tests for error propagation through multiple layers."""

    def test_unsupported_extension_raises_in_generate(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with pytest.raises(ValueError, match="Unsupported file extension"):
            generate_unit_test_script("main.go")

    def test_java_no_build_tool_raises_in_generate(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with pytest.raises(ValueError, match="Cannot detect Java build tool"):
            generate_unit_test_script("src/main/java/Foo.java")

    def test_unsupported_language_in_derive_test_path(self):
        result = derive_test_file_path("main.rs", "rust")
        assert result is None

    def test_empty_extension_raises_value_error(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with pytest.raises(ValueError):
            generate_unit_test_script("Makefile")


class TestRenderScriptWithRealTemplates:
    """Integration tests for render_script with actual imported templates."""

    def test_python_template_all_placeholders_filled(self):
        from openhands_cli.instructions.utgen.scripts.python_template import (
            PYTHON_SCRIPT_TEMPLATE,
        )

        placeholders = {
            "SOURCE_FILE_PATH": "src/foo.py",
            "TEST_FILE_PATH": "tests/test_foo.py",
            "TEST_COMMAND": "uv run coverage run --include=src/foo.py -m pytest tests/test_foo.py && uv run coverage xml",
            "EXPECTED_COVERAGE": "85",
            "MAX_ITERATIONS": "5",
        }
        result = render_script(PYTHON_SCRIPT_TEMPLATE, placeholders)

        assert "src/foo.py" in result
        assert "tests/test_foo.py" in result
        assert "85" in result
        assert "5" in result
        # Bash syntax intact
        assert "${COVERAGE_REPORT_PATH:-coverage.xml}" in result
        assert "${KEPLOY_ARGS[@]}" in result

    def test_java_template_all_placeholders_filled(self):
        from openhands_cli.instructions.utgen.scripts.java_template import (
            JAVA_SCRIPT_TEMPLATE,
        )

        placeholders = {
            "SOURCE_FILE_PATH": "src/main/java/Foo.java",
            "TEST_FILE_PATH": "src/test/java/FooTest.java",
            "TEST_COMMAND": "mvn verify -P coverage -Dtest=FooTest",
            "EXPECTED_COVERAGE": "85",
            "MAX_ITERATIONS": "5",
            "JAVA_HOME": "/usr/lib/jvm/java-21-openjdk-amd64",
            "BUILD_CLEAN_COMMAND": "mvn clean",
            "COVERAGE_REPORT_PATH": "target/site/jacoco/jacoco.xml",
        }
        result = render_script(JAVA_SCRIPT_TEMPLATE, placeholders)

        assert "src/main/java/Foo.java" in result
        assert "FooTest" in result
        assert "mvn clean" in result
        assert "target/site/jacoco/jacoco.xml" in result
        assert "jacoco" in result
        assert "${KEPLOY_ARGS[@]}" in result
