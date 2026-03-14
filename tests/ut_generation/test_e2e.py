"""End-to-end tests for openhands_cli.ut_generation module.

Tests the full generate_unit_test_script flow from source file path
to generated Gen_UnitTest.sh bash script on the filesystem.
"""

import pytest

from openhands_cli.ut_generation import generate_unit_test_script
from openhands_cli.ut_generation.config import OUTPUT_SCRIPT_NAME


class TestE2EPythonProject:
    """E2E tests simulating a real Python project."""

    def test_generates_script_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        generate_unit_test_script("src/calculator.py")
        assert (tmp_path / OUTPUT_SCRIPT_NAME).exists()

    def test_generated_script_starts_with_shebang(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        generate_unit_test_script("src/calculator.py")
        content = (tmp_path / OUTPUT_SCRIPT_NAME).read_text()
        assert content.startswith("#!/bin/bash")

    def test_generated_script_contains_source_path(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        generate_unit_test_script("src/calculator.py")
        content = (tmp_path / OUTPUT_SCRIPT_NAME).read_text()
        assert "src/calculator.py" in content

    def test_generated_script_contains_test_path(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        generate_unit_test_script("src/calculator.py")
        content = (tmp_path / OUTPUT_SCRIPT_NAME).read_text()
        assert "test_calculator.py" in content

    def test_generated_script_contains_expected_coverage(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        generate_unit_test_script("src/calculator.py", expected_coverage=92)
        content = (tmp_path / OUTPUT_SCRIPT_NAME).read_text()
        assert "92" in content

    def test_generated_script_contains_max_iterations(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        generate_unit_test_script("src/calculator.py", max_iteration=8)
        content = (tmp_path / OUTPUT_SCRIPT_NAME).read_text()
        assert "8" in content

    def test_generated_script_contains_keploy_gen(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        generate_unit_test_script("src/calculator.py")
        content = (tmp_path / OUTPUT_SCRIPT_NAME).read_text()
        assert "keploy gen" in content

    def test_generated_script_contains_pytest(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        generate_unit_test_script("src/calculator.py")
        content = (tmp_path / OUTPUT_SCRIPT_NAME).read_text()
        assert "pytest" in content

    def test_generated_script_contains_coverage_format_cobertura(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        generate_unit_test_script("src/calculator.py")
        content = (tmp_path / OUTPUT_SCRIPT_NAME).read_text()
        assert "cobertura" in content

    def test_generated_script_no_unreplaced_placeholders(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        generate_unit_test_script("src/calculator.py")
        content = (tmp_path / OUTPUT_SCRIPT_NAME).read_text()
        # None of the template placeholders should remain
        assert "{{SOURCE_FILE_PATH}}" not in content
        assert "{{TEST_FILE_PATH}}" not in content
        assert "{{TEST_COMMAND}}" not in content
        assert "{{EXPECTED_COVERAGE}}" not in content
        assert "{{MAX_ITERATIONS}}" not in content

    def test_generated_script_has_valid_bash_variable_syntax(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        generate_unit_test_script("src/calculator.py")
        content = (tmp_path / OUTPUT_SCRIPT_NAME).read_text()
        # Bash array expansion syntax
        assert "${KEPLOY_ARGS[@]}" in content
        # Bash default value syntax
        assert "${COVERAGE_REPORT_PATH:-coverage.xml}" in content

    def test_creates_empty_test_file_if_not_exists(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        generate_unit_test_script("src/calculator.py")
        # tests/test_calculator.py should be created
        test_file = tmp_path / "tests" / "test_calculator.py"
        assert test_file.exists()
        assert test_file.read_text() == ""

    def test_does_not_overwrite_existing_test_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        existing_tests = tmp_path / "tests"
        existing_tests.mkdir()
        test_file = existing_tests / "test_calculator.py"
        test_file.write_text("# existing tests\ndef test_add(): pass\n")

        generate_unit_test_script("src/calculator.py")

        assert "existing tests" in test_file.read_text()

    def test_default_coverage_85(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        generate_unit_test_script("src/calculator.py")
        content = (tmp_path / OUTPUT_SCRIPT_NAME).read_text()
        assert "--expected-coverage=85" in content

    def test_default_max_iteration_5(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        generate_unit_test_script("src/calculator.py")
        content = (tmp_path / OUTPUT_SCRIPT_NAME).read_text()
        assert "--maxIterations=5" in content

    def test_nested_module_creates_nested_test_dirs(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        generate_unit_test_script("openhands_cli/ut_generation/utils.py")
        test_file = tmp_path / "tests" / "ut_generation" / "test_utils.py"
        assert test_file.exists()

    def test_overwrites_existing_gen_script(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        generate_unit_test_script("src/module_a.py")
        generate_unit_test_script("src/module_b.py")
        content = (tmp_path / OUTPUT_SCRIPT_NAME).read_text()
        # Only the last call's content should be in the script
        assert "module_b.py" in content

    def test_uv_run_in_test_command(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        generate_unit_test_script("src/utils.py")
        content = (tmp_path / OUTPUT_SCRIPT_NAME).read_text()
        assert "uv run" in content

    def test_architect_md_check_in_script(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        generate_unit_test_script("src/utils.py")
        content = (tmp_path / OUTPUT_SCRIPT_NAME).read_text()
        assert "architect.md" in content

    def test_venv_activation_in_script(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        generate_unit_test_script("src/utils.py")
        content = (tmp_path / OUTPUT_SCRIPT_NAME).read_text()
        assert ".venv" in content


class TestE2EJavaMavenProject:
    """E2E tests simulating a real Java Maven project."""

    def test_generates_script_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pom.xml").touch()
        generate_unit_test_script("src/main/java/com/example/Calculator.java")
        assert (tmp_path / OUTPUT_SCRIPT_NAME).exists()

    def test_generated_script_starts_with_shebang(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pom.xml").touch()
        generate_unit_test_script("src/main/java/Calculator.java")
        content = (tmp_path / OUTPUT_SCRIPT_NAME).read_text()
        assert content.startswith("#!/bin/bash")

    def test_generated_script_contains_source_path(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pom.xml").touch()
        generate_unit_test_script("src/main/java/Calculator.java")
        content = (tmp_path / OUTPUT_SCRIPT_NAME).read_text()
        assert "src/main/java/Calculator.java" in content

    def test_generated_script_contains_test_path(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pom.xml").touch()
        generate_unit_test_script("src/main/java/Calculator.java")
        content = (tmp_path / OUTPUT_SCRIPT_NAME).read_text()
        assert "src/test/java/CalculatorTest.java" in content

    def test_generated_script_contains_mvn_verify(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pom.xml").touch()
        generate_unit_test_script("src/main/java/Calculator.java")
        content = (tmp_path / OUTPUT_SCRIPT_NAME).read_text()
        assert "mvn verify" in content

    def test_generated_script_contains_jacoco_coverage_format(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pom.xml").touch()
        generate_unit_test_script("src/main/java/Calculator.java")
        content = (tmp_path / OUTPUT_SCRIPT_NAME).read_text()
        assert "jacoco" in content

    def test_generated_script_contains_maven_jacoco_report_path(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pom.xml").touch()
        generate_unit_test_script("src/main/java/Calculator.java")
        content = (tmp_path / OUTPUT_SCRIPT_NAME).read_text()
        assert "target/site/jacoco/jacoco.xml" in content

    def test_generated_script_contains_mvn_clean(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pom.xml").touch()
        generate_unit_test_script("src/main/java/Calculator.java")
        content = (tmp_path / OUTPUT_SCRIPT_NAME).read_text()
        assert "mvn clean" in content

    def test_generated_script_contains_java_home_export(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pom.xml").touch()
        generate_unit_test_script("src/main/java/Calculator.java")
        content = (tmp_path / OUTPUT_SCRIPT_NAME).read_text()
        assert "JAVA_HOME" in content
        assert "export JAVA_HOME" in content

    def test_generated_script_no_unreplaced_placeholders(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pom.xml").touch()
        generate_unit_test_script("src/main/java/Calculator.java")
        content = (tmp_path / OUTPUT_SCRIPT_NAME).read_text()
        assert "{{SOURCE_FILE_PATH}}" not in content
        assert "{{TEST_FILE_PATH}}" not in content
        assert "{{TEST_COMMAND}}" not in content
        assert "{{JAVA_HOME}}" not in content
        assert "{{BUILD_CLEAN_COMMAND}}" not in content
        assert "{{COVERAGE_REPORT_PATH}}" not in content

    def test_creates_test_file_with_test_suffix(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pom.xml").touch()
        generate_unit_test_script("src/main/java/com/example/Calculator.java")
        test_file = (
            tmp_path / "src" / "test" / "java" / "com" / "example" / "CalculatorTest.java"
        )
        assert test_file.exists()

    def test_expected_coverage_in_generated_script(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pom.xml").touch()
        generate_unit_test_script("src/main/java/Foo.java", expected_coverage=70)
        content = (tmp_path / OUTPUT_SCRIPT_NAME).read_text()
        assert "70" in content

    def test_custom_java_home_from_env(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("JAVA_HOME", "/custom/java/home")
        (tmp_path / "pom.xml").touch()
        generate_unit_test_script("src/main/java/Foo.java")
        content = (tmp_path / OUTPUT_SCRIPT_NAME).read_text()
        assert "/custom/java/home" in content


class TestE2EJavaGradleProject:
    """E2E tests simulating a real Java Gradle project."""

    def test_generates_script_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "build.gradle").touch()
        generate_unit_test_script("src/main/java/Foo.java")
        assert (tmp_path / OUTPUT_SCRIPT_NAME).exists()

    def test_generated_script_contains_gradlew(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "build.gradle").touch()
        generate_unit_test_script("src/main/java/Foo.java")
        content = (tmp_path / OUTPUT_SCRIPT_NAME).read_text()
        assert "gradlew" in content

    def test_generated_script_contains_gradle_jacoco_report_path(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "build.gradle").touch()
        generate_unit_test_script("src/main/java/Foo.java")
        content = (tmp_path / OUTPUT_SCRIPT_NAME).read_text()
        assert "build/reports/jacoco/test/jacocoTestReport.xml" in content

    def test_gradle_kts_also_detected(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "build.gradle.kts").touch()
        generate_unit_test_script("src/main/java/Foo.java")
        assert (tmp_path / OUTPUT_SCRIPT_NAME).exists()

    def test_with_gradlew_wrapper(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "build.gradle").touch()
        (tmp_path / "gradlew").touch()
        generate_unit_test_script("src/main/java/Foo.java")
        content = (tmp_path / OUTPUT_SCRIPT_NAME).read_text()
        assert "chmod +x ./gradlew" in content


class TestE2EErrorScenarios:
    """E2E tests for error conditions."""

    def test_unsupported_extension_raises(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with pytest.raises(ValueError):
            generate_unit_test_script("main.go")

    def test_java_without_build_file_raises(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with pytest.raises(ValueError, match="Cannot detect Java build tool"):
            generate_unit_test_script("src/main/java/Foo.java")

    def test_typescript_file_raises(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with pytest.raises(ValueError):
            generate_unit_test_script("src/app.ts")

    def test_no_script_created_on_error(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        try:
            generate_unit_test_script("main.go")
        except ValueError:
            pass
        assert not (tmp_path / OUTPUT_SCRIPT_NAME).exists()


@pytest.mark.integration
class TestE2EPublicApiIntegration:
    """E2E tests verifying the public API exposed via __init__.py."""

    def test_public_api_generates_python_script(self, tmp_path, monkeypatch):
        from openhands_cli.ut_generation import generate_unit_test_script as public_api

        monkeypatch.chdir(tmp_path)
        public_api("src/service.py", expected_coverage=88, max_iteration=6)

        script = tmp_path / OUTPUT_SCRIPT_NAME
        assert script.exists()
        content = script.read_text()
        assert "src/service.py" in content
        assert "88" in content
        assert "6" in content

    def test_public_api_generates_java_maven_script(self, tmp_path, monkeypatch):
        from openhands_cli.ut_generation import generate_unit_test_script as public_api

        monkeypatch.chdir(tmp_path)
        (tmp_path / "pom.xml").touch()
        public_api("src/main/java/com/Service.java", expected_coverage=80, max_iteration=4)

        script = tmp_path / OUTPUT_SCRIPT_NAME
        assert script.exists()
        content = script.read_text()
        assert "src/main/java/com/Service.java" in content
        assert "ServiceTest.java" in content
        assert "mvn" in content
