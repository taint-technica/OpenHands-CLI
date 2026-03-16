import re

import pytest
from unittest.mock import patch

from openhands_cli.ut_generation.generator import generate_unit_test_script


MOCK_PYTHON_TEMPLATE = (
    "#!/bin/bash\n"
    "SOURCE={{SOURCE_FILE_PATH}}\n"
    "TEST={{TEST_FILE_PATH}}\n"
    "CMD={{TEST_COMMAND}}\n"
    "COVERAGE={{EXPECTED_COVERAGE}}\n"
    "MAX_ITER={{MAX_ITERATIONS}}\n"
    "API_KEY={{API_KEY}}\n"
    "LLM_URL={{LLM_BASE_URL}}\n"
    "MODEL={{MODEL}}\n"
    "HOME=${{HOME}}\n"
)

MOCK_JAVA_TEMPLATE = (
    "#!/bin/bash\n"
    "SOURCE={{SOURCE_FILE_PATH}}\n"
    "TEST={{TEST_FILE_PATH}}\n"
    "CMD={{TEST_COMMAND}}\n"
    "COVERAGE={{EXPECTED_COVERAGE}}\n"
    "MAX_ITER={{MAX_ITERATIONS}}\n"
    "API_KEY={{API_KEY}}\n"
    "LLM_URL={{LLM_BASE_URL}}\n"
    "MODEL={{MODEL}}\n"
    "JAVA_HOME={{JAVA_HOME}}\n"
    "CLEAN={{BUILD_CLEAN_COMMAND}}\n"
    "REPORT={{COVERAGE_REPORT_PATH}}\n"
    "HOME=${{HOME}}\n"
)


@pytest.mark.integration
class TestPythonGenerationFlow:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        self.tmp_path = tmp_path

    def _run(self, source="src/myapp/utils.py", **overrides):
        params = {
            "expected_coverage": 85,
            "max_iteration": 5,
            "api_key": "test-api-key",
            "llm_base_url": "https://api.test.com/v1",
            "model": "gpt-4o",
        }
        params.update(overrides)
        with patch(
            "openhands_cli.ut_generation.python_handler.PYTHON_SCRIPT_TEMPLATE",
            MOCK_PYTHON_TEMPLATE,
        ):
            generate_unit_test_script(source, **params)

    def test_script_file_is_created(self):
        self._run()
        assert (self.tmp_path / "Gen_UnitTest.sh").exists()

    def test_script_contains_source_path(self):
        self._run(source="src/myapp/utils.py")
        content = (self.tmp_path / "Gen_UnitTest.sh").read_text()
        assert "src/myapp/utils.py" in content

    def test_script_contains_test_path(self):
        self._run(source="src/myapp/utils.py")
        content = (self.tmp_path / "Gen_UnitTest.sh").read_text()
        assert "tests/src/myapp/test_utils.py" in content

    def test_script_contains_coverage_value(self):
        self._run(expected_coverage=90)
        content = (self.tmp_path / "Gen_UnitTest.sh").read_text()
        assert "90" in content

    def test_script_contains_max_iterations(self):
        self._run(max_iteration=10)
        content = (self.tmp_path / "Gen_UnitTest.sh").read_text()
        assert "10" in content

    def test_script_contains_api_key(self):
        self._run(api_key="my-secret-key")
        content = (self.tmp_path / "Gen_UnitTest.sh").read_text()
        assert "my-secret-key" in content

    def test_script_contains_model(self):
        self._run(model="claude-opus-4-6")
        content = (self.tmp_path / "Gen_UnitTest.sh").read_text()
        assert "claude-opus-4-6" in content

    def test_bash_variables_preserved_in_script(self):
        self._run()
        content = (self.tmp_path / "Gen_UnitTest.sh").read_text()
        assert "${HOME}" in content

    def test_test_file_is_created(self):
        self._run(source="src/myapp/utils.py")
        test_file = self.tmp_path / "tests" / "src" / "myapp" / "test_utils.py"
        assert test_file.exists()

    def test_test_file_is_empty(self):
        self._run(source="src/myapp/utils.py")
        test_file = self.tmp_path / "tests" / "src" / "myapp" / "test_utils.py"
        assert test_file.read_text() == ""

    def test_test_file_not_overwritten_if_exists(self):
        test_file = self.tmp_path / "tests" / "src" / "myapp" / "test_utils.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("existing test content")

        self._run(source="src/myapp/utils.py")

        assert test_file.read_text() == "existing test content"

    def test_flat_python_file_uses_tests_prefix(self):
        self._run(source="utils.py")
        test_file = self.tmp_path / "tests" / "tests_utils.py"
        assert test_file.exists()

    def test_no_unreplaced_placeholders_in_script(self):
        self._run()
        content = (self.tmp_path / "Gen_UnitTest.sh").read_text()
        unreplaced = re.findall(r"\{\{[A-Z_]+\}\}", content)
        assert unreplaced == [], f"Unreplaced placeholders found: {unreplaced}"


@pytest.mark.integration
class TestJavaGenerationFlow:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        self.tmp_path = tmp_path

    def _run(self, source="src/main/java/com/example/Service.java", build_file="pom.xml", **overrides):
        (self.tmp_path / build_file).write_text("<project/>")
        params = {
            "expected_coverage": 85,
            "max_iteration": 5,
            "api_key": "test-api-key",
            "llm_base_url": "https://api.test.com/v1",
            "model": "gpt-4o",
        }
        params.update(overrides)
        with patch(
            "openhands_cli.ut_generation.java_handler.JAVA_SCRIPT_TEMPLATE",
            MOCK_JAVA_TEMPLATE,
        ):
            generate_unit_test_script(source, **params)

    def test_maven_script_is_created(self):
        self._run(build_file="pom.xml")
        assert (self.tmp_path / "Gen_UnitTest.sh").exists()

    def test_maven_script_contains_mvn_command(self):
        self._run(build_file="pom.xml")
        content = (self.tmp_path / "Gen_UnitTest.sh").read_text()
        assert "mvn verify" in content

    def test_gradle_script_contains_gradlew_command(self):
        (self.tmp_path / "gradlew").write_text("#!/bin/sh")
        (self.tmp_path / "pom.xml").unlink(missing_ok=True)
        (self.tmp_path / "build.gradle").write_text("plugins { id 'java' }")
        params = {
            "expected_coverage": 85,
            "max_iteration": 5,
            "api_key": "key",
            "llm_base_url": "https://api.test.com/v1",
            "model": "gpt-4o",
        }
        with patch(
            "openhands_cli.ut_generation.java_handler.JAVA_SCRIPT_TEMPLATE",
            MOCK_JAVA_TEMPLATE,
        ):
            generate_unit_test_script(
                "src/main/java/com/example/Service.java", **params
            )
        content = (self.tmp_path / "Gen_UnitTest.sh").read_text()
        assert "./gradlew test" in content

    def test_custom_java_home_in_script(self, monkeypatch):
        monkeypatch.setenv("JAVA_HOME", "/custom/jdk")
        self._run()
        content = (self.tmp_path / "Gen_UnitTest.sh").read_text()
        assert "/custom/jdk" in content

    def test_java_test_file_is_created(self):
        self._run(source="src/main/java/com/example/Service.java")
        test_file = self.tmp_path / "src" / "test" / "java" / "com" / "example" / "ServiceTest.java"
        assert test_file.exists()

    def test_no_unreplaced_placeholders_in_script(self):
        self._run()
        content = (self.tmp_path / "Gen_UnitTest.sh").read_text()
        unreplaced = re.findall(r"\{\{[A-Z_]+\}\}", content)
        assert unreplaced == [], f"Unreplaced placeholders found: {unreplaced}"

    def test_raises_when_no_build_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with pytest.raises(ValueError):
            generate_unit_test_script(
                "src/main/java/Foo.java", 85, 5, "key", "https://api.test.com", "gpt-4o"
            )
