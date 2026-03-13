"""Unit tests for openhands_cli.ut_generation.java_handler module."""

import pytest

from openhands_cli.ut_generation import java_handler
from openhands_cli.ut_generation.config import DEFAULT_JAVA_HOME


class TestDeriveTestPath:
    def test_simple_class(self):
        result = java_handler.derive_test_path("src/main/java/Foo.java")
        assert result == "src/test/java/FooTest.java"

    def test_nested_package(self):
        result = java_handler.derive_test_path("src/main/java/com/example/Bar.java")
        assert result == "src/test/java/com/example/BarTest.java"

    def test_deep_nested_package(self):
        result = java_handler.derive_test_path("src/main/java/com/example/service/UserService.java")
        assert result == "src/test/java/com/example/service/UserServiceTest.java"

    def test_replaces_main_with_test(self):
        result = java_handler.derive_test_path("src/main/java/MyClass.java")
        assert "src/test/java/" in result
        assert "src/main/java/" not in result

    def test_appends_test_suffix(self):
        result = java_handler.derive_test_path("src/main/java/Calculator.java")
        assert result.endswith("CalculatorTest.java")

    def test_returns_string(self):
        result = java_handler.derive_test_path("src/main/java/Foo.java")
        assert isinstance(result, str)


class TestDetectBuildTool:
    def test_detects_maven_with_pom_xml(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pom.xml").touch()
        assert java_handler.detect_build_tool() == "maven"

    def test_detects_gradle_with_build_gradle(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "build.gradle").touch()
        assert java_handler.detect_build_tool() == "gradle"

    def test_detects_gradle_with_build_gradle_kts(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "build.gradle.kts").touch()
        assert java_handler.detect_build_tool() == "gradle"

    def test_maven_takes_priority_over_gradle(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pom.xml").touch()
        (tmp_path / "build.gradle").touch()
        assert java_handler.detect_build_tool() == "maven"

    def test_raises_value_error_when_no_build_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with pytest.raises(ValueError, match="Cannot detect Java build tool"):
            java_handler.detect_build_tool()

    def test_error_message_mentions_pom_and_gradle(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with pytest.raises(ValueError, match="pom.xml"):
            java_handler.detect_build_tool()


class TestDetectJavaHome:
    def test_returns_env_variable_when_set(self, monkeypatch):
        monkeypatch.setenv("JAVA_HOME", "/custom/java/home")
        assert java_handler.detect_java_home() == "/custom/java/home"

    def test_returns_default_when_env_not_set(self, monkeypatch):
        monkeypatch.delenv("JAVA_HOME", raising=False)
        assert java_handler.detect_java_home() == DEFAULT_JAVA_HOME

    def test_returns_string(self):
        result = java_handler.detect_java_home()
        assert isinstance(result, str)

    def test_empty_env_var_returns_empty(self, monkeypatch):
        monkeypatch.setenv("JAVA_HOME", "")
        # os.environ.get returns "" which is falsy, but the function returns it as-is
        result = java_handler.detect_java_home()
        assert result == ""


class TestBuildTestCommand:
    def test_maven_command_format(self):
        cmd = java_handler.build_test_command("src/test/java/FooTest.java", "maven")
        assert cmd == "mvn verify -P coverage -Dtest=FooTest"

    def test_maven_uses_classname(self):
        cmd = java_handler.build_test_command("src/test/java/com/example/BarTest.java", "maven")
        assert cmd is not None
        assert "BarTest" in cmd
        assert cmd == "mvn verify -P coverage -Dtest=BarTest"

    def test_maven_contains_verify(self):
        cmd = java_handler.build_test_command("src/test/java/FooTest.java", "maven")
        assert cmd is not None
        assert "mvn verify" in cmd

    def test_maven_contains_coverage_profile(self):
        cmd = java_handler.build_test_command("src/test/java/FooTest.java", "maven")
        assert cmd is not None
        assert "-P coverage" in cmd

    def test_gradle_command_contains_gradlew(self):
        cmd = java_handler.build_test_command("src/test/java/FooTest.java", "gradle")
        assert cmd is not None
        assert "./gradlew" in cmd

    def test_gradle_command_contains_jacoco(self):
        cmd = java_handler.build_test_command("src/test/java/FooTest.java", "gradle")
        assert cmd is not None
        assert "jacocoTestReport" in cmd

    def test_gradle_command_contains_tests_flag(self):
        cmd = java_handler.build_test_command("src/test/java/FooTest.java", "gradle")
        assert cmd is not None
        assert "--tests" in cmd

    def test_gradle_derives_class_from_path(self):
        cmd = java_handler.build_test_command("src/test/java/com/example/FooTest.java", "gradle")
        # After replace("src/test/java/", "").replace(".java", "") → "com/example/FooTest"
        # After replace("/", "") → "comexampleFooTest"
        assert cmd is not None
        assert "comexampleFooTest" in cmd

    def test_unknown_build_tool_returns_none(self):
        result = java_handler.build_test_command("src/test/java/FooTest.java", "ant")
        assert result is None

    def test_maven_returns_string(self):
        cmd = java_handler.build_test_command("src/test/java/FooTest.java", "maven")
        assert isinstance(cmd, str)

    def test_gradle_returns_string(self):
        cmd = java_handler.build_test_command("src/test/java/FooTest.java", "gradle")
        assert isinstance(cmd, str)


class TestGetBuildCleanCommand:
    def test_maven_returns_mvn_clean(self):
        result = java_handler.get_build_clean_command("maven")
        assert result == "mvn clean"

    def test_gradle_without_gradlew_returns_gradle_clean(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = java_handler.get_build_clean_command("gradle")
        assert result == "gradle clean"

    def test_gradle_with_gradlew_returns_chmod_command(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "gradlew").touch()
        result = java_handler.get_build_clean_command("gradle")
        assert result == "chmod +x ./gradlew && ./gradlew clean"

    def test_unknown_tool_without_gradlew_returns_gradle_clean(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = java_handler.get_build_clean_command("ant")
        assert result == "gradle clean"

    def test_unknown_tool_with_gradlew_returns_chmod_command(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "gradlew").touch()
        result = java_handler.get_build_clean_command("ant")
        assert result == "chmod +x ./gradlew && ./gradlew clean"

    def test_returns_string(self):
        result = java_handler.get_build_clean_command("maven")
        assert isinstance(result, str)


class TestGetCoverageReportPath:
    def test_maven_path(self):
        result = java_handler.get_coverage_report_path("maven")
        assert result == "target/site/jacoco/jacoco.xml"

    def test_gradle_path(self):
        result = java_handler.get_coverage_report_path("gradle")
        assert result == "build/reports/jacoco/test/jacocoTestReport.xml"

    def test_unknown_tool_returns_none(self):
        result = java_handler.get_coverage_report_path("ant")
        assert result is None

    def test_maven_path_is_xml(self):
        result = java_handler.get_coverage_report_path("maven")
        assert isinstance(result, str)
        assert result.endswith(".xml")

    def test_gradle_path_is_xml(self):
        result = java_handler.get_coverage_report_path("gradle")
        assert isinstance(result, str)
        assert result.endswith(".xml")

    def test_maven_contains_jacoco(self):
        result = java_handler.get_coverage_report_path("maven")
        assert isinstance(result, str)
        assert "jacoco" in result

    def test_gradle_contains_jacoco(self):
        result = java_handler.get_coverage_report_path("gradle")
        assert isinstance(result, str)
        assert "jacoco" in result


class TestGetTemplateAndPlaceholders:
    def test_returns_tuple(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pom.xml").touch()
        result = java_handler.get_template_and_placeholders(
            "src/main/java/Foo.java", 85, 5
        )
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_placeholders_source_file_path(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pom.xml").touch()
        _, placeholders = java_handler.get_template_and_placeholders(
            "src/main/java/Foo.java", 85, 5
        )
        assert placeholders["SOURCE_FILE_PATH"] == "src/main/java/Foo.java"

    def test_placeholders_test_file_path(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pom.xml").touch()
        _, placeholders = java_handler.get_template_and_placeholders(
            "src/main/java/Foo.java", 85, 5
        )
        assert placeholders["TEST_FILE_PATH"] == "src/test/java/FooTest.java"

    def test_placeholders_expected_coverage(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pom.xml").touch()
        _, placeholders = java_handler.get_template_and_placeholders(
            "src/main/java/Foo.java", 90, 5
        )
        assert placeholders["EXPECTED_COVERAGE"] == "90"

    def test_placeholders_max_iterations(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pom.xml").touch()
        _, placeholders = java_handler.get_template_and_placeholders(
            "src/main/java/Foo.java", 85, 7
        )
        assert placeholders["MAX_ITERATIONS"] == "7"

    def test_placeholders_java_home_present(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pom.xml").touch()
        _, placeholders = java_handler.get_template_and_placeholders(
            "src/main/java/Foo.java", 85, 5
        )
        assert "JAVA_HOME" in placeholders

    def test_placeholders_build_clean_command_present(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pom.xml").touch()
        _, placeholders = java_handler.get_template_and_placeholders(
            "src/main/java/Foo.java", 85, 5
        )
        assert "BUILD_CLEAN_COMMAND" in placeholders
        assert "mvn clean" == placeholders["BUILD_CLEAN_COMMAND"]

    def test_placeholders_coverage_report_path_maven(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pom.xml").touch()
        _, placeholders = java_handler.get_template_and_placeholders(
            "src/main/java/Foo.java", 85, 5
        )
        assert placeholders["COVERAGE_REPORT_PATH"] == "target/site/jacoco/jacoco.xml"

    def test_placeholders_coverage_report_path_gradle(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "build.gradle").touch()
        _, placeholders = java_handler.get_template_and_placeholders(
            "src/main/java/Foo.java", 85, 5
        )
        assert (
            placeholders["COVERAGE_REPORT_PATH"]
            == "build/reports/jacoco/test/jacocoTestReport.xml"
        )

    def test_raises_when_no_build_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with pytest.raises(ValueError):
            java_handler.get_template_and_placeholders(
                "src/main/java/Foo.java", 85, 5
            )

    def test_template_is_string(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pom.xml").touch()
        template, _ = java_handler.get_template_and_placeholders(
            "src/main/java/Foo.java", 85, 5
        )
        assert isinstance(template, str)

    def test_template_contains_shebang(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pom.xml").touch()
        template, _ = java_handler.get_template_and_placeholders(
            "src/main/java/Foo.java", 85, 5
        )
        assert "#!/bin/bash" in template

    def test_eight_required_placeholder_keys(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pom.xml").touch()
        _, placeholders = java_handler.get_template_and_placeholders(
            "src/main/java/Foo.java", 85, 5
        )
        required_keys = {
            "SOURCE_FILE_PATH",
            "TEST_FILE_PATH",
            "TEST_COMMAND",
            "EXPECTED_COVERAGE",
            "MAX_ITERATIONS",
            "JAVA_HOME",
            "BUILD_CLEAN_COMMAND",
            "COVERAGE_REPORT_PATH",
        }
        assert required_keys.issubset(placeholders.keys())
