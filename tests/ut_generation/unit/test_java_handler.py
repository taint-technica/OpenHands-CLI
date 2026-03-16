import pytest
from unittest.mock import patch

from openhands_cli.ut_generation import java_handler
from openhands_cli.ut_generation.config import DEFAULT_JAVA_HOME


class TestDeriveTestPath:
    def test_simple_class(self):
        result = java_handler.derive_test_path("src/main/java/Foo.java")
        assert result == "src/test/java/FooTest.java"

    def test_with_package(self):
        result = java_handler.derive_test_path("src/main/java/com/example/Service.java")
        assert result == "src/test/java/com/example/ServiceTest.java"

    def test_appends_test_suffix(self):
        result = java_handler.derive_test_path("src/main/java/MyClass.java")
        assert "MyClassTest.java" in result

    def test_replaces_main_with_test_dir(self):
        result = java_handler.derive_test_path("src/main/java/Foo.java")
        assert "src/test/java" in result
        assert "src/main/java" not in result

    def test_path_without_main_java(self):
        result = java_handler.derive_test_path("other/path/Foo.java")
        assert result == "other/path/FooTest.java"

    def test_deep_package(self):
        result = java_handler.derive_test_path(
            "src/main/java/com/example/service/UserService.java"
        )
        assert result == "src/test/java/com/example/service/UserServiceTest.java"


class TestDetectBuildTool:
    def test_detects_maven(self, maven_project):
        assert java_handler.detect_build_tool() == "maven"

    def test_detects_gradle(self, gradle_project):
        assert java_handler.detect_build_tool() == "gradle"

    def test_detects_gradle_kts(self, tmp_path, monkeypatch):
        (tmp_path / "build.gradle.kts").write_text("plugins { id('java') }")
        monkeypatch.chdir(tmp_path)
        assert java_handler.detect_build_tool() == "gradle"

    def test_maven_takes_priority_over_gradle(self, tmp_path, monkeypatch):
        (tmp_path / "pom.xml").write_text("<project/>")
        (tmp_path / "build.gradle").write_text("plugins { id 'java' }")
        monkeypatch.chdir(tmp_path)
        assert java_handler.detect_build_tool() == "maven"

    def test_raises_when_no_build_file(self, empty_project):
        with pytest.raises(ValueError):
            java_handler.detect_build_tool()

    def test_error_message_mentions_build_files(self, empty_project):
        with pytest.raises(ValueError, match=r"pom\.xml|build\.gradle"):
            java_handler.detect_build_tool()


class TestDetectJavaHome:
    def test_returns_env_var_when_set(self, monkeypatch):
        monkeypatch.setenv("JAVA_HOME", "/custom/java")
        assert java_handler.detect_java_home() == "/custom/java"

    def test_returns_default_when_env_not_set(self, monkeypatch):
        monkeypatch.delenv("JAVA_HOME", raising=False)
        assert java_handler.detect_java_home() == DEFAULT_JAVA_HOME

    def test_empty_string_env_falls_back_to_default(self, monkeypatch):
        monkeypatch.setenv("JAVA_HOME", "")
        assert java_handler.detect_java_home() == DEFAULT_JAVA_HOME


class TestBuildTestCommand:
    def test_maven_command_format(self):
        cmd = java_handler.build_test_command(
            "src/test/java/FooTest.java", "maven"
        )
        assert cmd == "mvn verify -P coverage -Dtest=FooTest"

    def test_maven_uses_simple_class_name(self):
        cmd = java_handler.build_test_command(
            "src/test/java/com/example/ServiceTest.java", "maven"
        )
        assert "ServiceTest" in cmd
        assert "com.example" not in cmd

    def test_gradle_command_format(self):
        cmd = java_handler.build_test_command(
            "src/test/java/com/example/FooTest.java", "gradle"
        )
        assert "./gradlew test jacocoTestReport" in cmd
        assert '"com.example.FooTest"' in cmd

    def test_gradle_converts_path_to_fq_classname(self):
        cmd = java_handler.build_test_command(
            "src/test/java/com/example/service/UserServiceTest.java", "gradle"
        )
        assert '"com.example.service.UserServiceTest"' in cmd

    def test_unsupported_build_tool_raises(self):
        with pytest.raises(ValueError):
            java_handler.build_test_command("FooTest.java", "ant")

    def test_unsupported_tool_error_message_contains_tool_name(self):
        with pytest.raises(ValueError, match="ant"):
            java_handler.build_test_command("FooTest.java", "ant")


class TestGetBuildCleanCommand:
    def test_maven_clean(self):
        assert java_handler.get_build_clean_command("maven") == "mvn clean"

    def test_gradle_with_gradlew(self, gradle_project):
        cmd = java_handler.get_build_clean_command("gradle")
        assert cmd == "chmod +x ./gradlew && ./gradlew clean"

    def test_gradle_without_gradlew(self, gradle_project_no_wrapper):
        cmd = java_handler.get_build_clean_command("gradle")
        assert cmd == "gradle clean"

    def test_unsupported_tool_raises(self):
        with pytest.raises(ValueError):
            java_handler.get_build_clean_command("ant")


class TestGetCoverageReportPath:
    def test_maven_path(self):
        path = java_handler.get_coverage_report_path("maven")
        assert path == "target/site/jacoco/jacoco.xml"

    def test_gradle_path(self):
        path = java_handler.get_coverage_report_path("gradle")
        assert path == "build/reports/jacoco/test/jacocoTestReport.xml"

    def test_unsupported_tool_raises(self):
        with pytest.raises(ValueError):
            java_handler.get_coverage_report_path("ant")

    def test_returns_xml_file(self):
        assert java_handler.get_coverage_report_path("maven").endswith(".xml")
        assert java_handler.get_coverage_report_path("gradle").endswith(".xml")


class TestGetTemplateAndPlaceholders:
    def test_returns_tuple(self, maven_project, common_params):
        result = java_handler.get_template_and_placeholders(
            "src/main/java/Foo.java", **common_params
        )
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_template_is_string(self, maven_project, common_params):
        template, _ = java_handler.get_template_and_placeholders(
            "src/main/java/Foo.java", **common_params
        )
        assert isinstance(template, str)

    def test_has_all_required_keys(self, maven_project, common_params):
        _, placeholders = java_handler.get_template_and_placeholders(
            "src/main/java/Foo.java", **common_params
        )
        required_keys = {
            "SOURCE_FILE_PATH",
            "TEST_FILE_PATH",
            "TEST_COMMAND",
            "EXPECTED_COVERAGE",
            "MAX_ITERATIONS",
            "API_KEY",
            "LLM_BASE_URL",
            "MODEL",
            "JAVA_HOME",
            "BUILD_CLEAN_COMMAND",
            "COVERAGE_REPORT_PATH",
        }
        assert required_keys.issubset(placeholders.keys())

    def test_java_home_in_placeholders(self, maven_project, common_params, monkeypatch):
        monkeypatch.setenv("JAVA_HOME", "/custom/jdk")
        _, placeholders = java_handler.get_template_and_placeholders(
            "src/main/java/Foo.java", **common_params
        )
        assert placeholders["JAVA_HOME"] == "/custom/jdk"

    def test_expected_coverage_is_string(self, maven_project, common_params):
        _, placeholders = java_handler.get_template_and_placeholders(
            "src/main/java/Foo.java", **common_params
        )
        assert placeholders["EXPECTED_COVERAGE"] == "85"
        assert isinstance(placeholders["EXPECTED_COVERAGE"], str)

    def test_max_iterations_is_string(self, maven_project, common_params):
        _, placeholders = java_handler.get_template_and_placeholders(
            "src/main/java/Foo.java", **common_params
        )
        assert placeholders["MAX_ITERATIONS"] == "5"
        assert isinstance(placeholders["MAX_ITERATIONS"], str)

    def test_propagates_no_build_tool_error(self, empty_project, common_params):
        with pytest.raises(ValueError):
            java_handler.get_template_and_placeholders(
                "src/main/java/Foo.java", **common_params
            )

    def test_template_uses_java_template(self, maven_project, common_params):
        with patch(
            "openhands_cli.ut_generation.java_handler.JAVA_SCRIPT_TEMPLATE",
            "MOCK_JAVA_TEMPLATE",
        ):
            template, _ = java_handler.get_template_and_placeholders(
                "src/main/java/Foo.java", **common_params
            )
        assert template == "MOCK_JAVA_TEMPLATE"
