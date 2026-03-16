"""
E2E tests: không mock gì, dùng template thật, verify kết quả trên filesystem thực.
"""
import re

import pytest

from openhands_cli.ut_generation.generator import generate_unit_test_script


def _no_unreplaced_placeholders(content: str) -> list[str]:
    return re.findall(r"\{\{[A-Z_]+\}\}", content)


@pytest.mark.integration
class TestPythonFilesystemE2E:
    @pytest.fixture(autouse=True)
    def isolated_dir(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        self.tmp = tmp_path

    def _generate(self, source="src/app/main.py", **overrides):
        params = {
            "expected_coverage": 80,
            "max_iteration": 3,
            "api_key": "e2e-test-key",
            "llm_base_url": "https://api.example.com/v1",
            "model": "gpt-4o",
        }
        params.update(overrides)
        generate_unit_test_script(source, **params)

    def test_gen_script_created_in_cwd(self):
        self._generate()
        assert (self.tmp / "Gen_UnitTest.sh").exists()

    def test_script_is_non_empty(self):
        self._generate()
        content = (self.tmp / "Gen_UnitTest.sh").read_text()
        assert len(content) > 0

    def test_script_starts_with_shebang(self):
        self._generate()
        content = (self.tmp / "Gen_UnitTest.sh").read_text()
        assert content.startswith("#!/bin/bash")

    def test_no_unreplaced_placeholders(self):
        self._generate()
        content = (self.tmp / "Gen_UnitTest.sh").read_text()
        assert _no_unreplaced_placeholders(content) == []

    def test_script_contains_api_key(self):
        self._generate(api_key="my-secret-api-key")
        content = (self.tmp / "Gen_UnitTest.sh").read_text()
        assert "my-secret-api-key" in content

    def test_script_contains_source_path(self):
        self._generate(source="src/app/main.py")
        content = (self.tmp / "Gen_UnitTest.sh").read_text()
        assert "src/app/main.py" in content

    def test_script_contains_uv_coverage_command(self):
        self._generate()
        content = (self.tmp / "Gen_UnitTest.sh").read_text()
        assert "uv run coverage run" in content

    def test_test_file_created_at_correct_path(self):
        self._generate(source="src/app/main.py")
        test_file = self.tmp / "tests" / "src" / "app" / "test_main.py"
        assert test_file.exists()

    def test_test_file_is_empty(self):
        self._generate(source="src/app/main.py")
        test_file = self.tmp / "tests" / "src" / "app" / "test_main.py"
        assert test_file.read_text() == ""

    def test_test_file_not_overwritten_on_second_call(self):
        test_file = self.tmp / "tests" / "src" / "app" / "test_main.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("# my existing tests\ndef test_foo(): pass\n")

        self._generate(source="src/app/main.py")

        assert "# my existing tests" in test_file.read_text()

    def test_script_overwritten_on_second_call(self):
        self._generate(api_key="first-key")
        self._generate(api_key="second-key")
        content = (self.tmp / "Gen_UnitTest.sh").read_text()
        assert "second-key" in content
        assert "first-key" not in content

    def test_flat_source_file_test_path(self):
        self._generate(source="utils.py")
        test_file = self.tmp / "tests" / "tests_utils.py"
        assert test_file.exists()

    def test_script_contains_expected_coverage(self):
        self._generate(expected_coverage=92)
        content = (self.tmp / "Gen_UnitTest.sh").read_text()
        assert "92" in content

    def test_script_contains_model(self):
        self._generate(model="claude-sonnet-4-6")
        content = (self.tmp / "Gen_UnitTest.sh").read_text()
        assert "claude-sonnet-4-6" in content

    def test_script_contains_llm_base_url(self):
        self._generate(llm_base_url="https://my-llm.company.com/api/v1")
        content = (self.tmp / "Gen_UnitTest.sh").read_text()
        assert "https://my-llm.company.com/api/v1" in content


@pytest.mark.integration
class TestJavaFilesystemE2E:
    @pytest.fixture(autouse=True)
    def isolated_dir(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        self.tmp = tmp_path

    def _generate_maven(self, source="src/main/java/com/example/Service.java", **overrides):
        (self.tmp / "pom.xml").write_text("<project/>")
        params = {
            "expected_coverage": 80,
            "max_iteration": 3,
            "api_key": "e2e-test-key",
            "llm_base_url": "https://api.example.com/v1",
            "model": "gpt-4o",
        }
        params.update(overrides)
        generate_unit_test_script(source, **params)

    def _generate_gradle(self, source="src/main/java/com/example/Service.java", **overrides):
        (self.tmp / "build.gradle").write_text("plugins { id 'java' }")
        (self.tmp / "gradlew").write_text("#!/bin/sh")
        params = {
            "expected_coverage": 80,
            "max_iteration": 3,
            "api_key": "e2e-test-key",
            "llm_base_url": "https://api.example.com/v1",
            "model": "gpt-4o",
        }
        params.update(overrides)
        generate_unit_test_script(source, **params)

    def test_maven_script_created(self):
        self._generate_maven()
        assert (self.tmp / "Gen_UnitTest.sh").exists()

    def test_maven_script_starts_with_shebang(self):
        self._generate_maven()
        content = (self.tmp / "Gen_UnitTest.sh").read_text()
        assert content.startswith("#!/bin/bash")

    def test_maven_script_contains_mvn_command(self):
        self._generate_maven()
        content = (self.tmp / "Gen_UnitTest.sh").read_text()
        assert "mvn verify" in content

    def test_gradle_script_contains_gradlew_command(self):
        self._generate_gradle()
        content = (self.tmp / "Gen_UnitTest.sh").read_text()
        assert "./gradlew test" in content

    def test_no_unreplaced_placeholders_maven(self):
        self._generate_maven()
        content = (self.tmp / "Gen_UnitTest.sh").read_text()
        assert _no_unreplaced_placeholders(content) == []

    def test_no_unreplaced_placeholders_gradle(self):
        self._generate_gradle()
        content = (self.tmp / "Gen_UnitTest.sh").read_text()
        assert _no_unreplaced_placeholders(content) == []

    def test_java_test_file_created_at_correct_path(self):
        self._generate_maven(source="src/main/java/com/example/UserService.java")
        test_file = (
            self.tmp / "src" / "test" / "java" / "com" / "example" / "UserServiceTest.java"
        )
        assert test_file.exists()

    def test_custom_java_home_in_script(self, monkeypatch):
        monkeypatch.setenv("JAVA_HOME", "/opt/custom-jdk-21")
        self._generate_maven()
        content = (self.tmp / "Gen_UnitTest.sh").read_text()
        assert "/opt/custom-jdk-21" in content

    def test_no_build_file_raises_and_no_script_created(self):
        with pytest.raises(ValueError):
            generate_unit_test_script(
                "src/main/java/Foo.java",
                80,
                3,
                "key",
                "https://api.example.com",
                "gpt-4o",
            )
        assert not (self.tmp / "Gen_UnitTest.sh").exists()

    def test_maven_script_contains_jacoco_report_path(self):
        self._generate_maven()
        content = (self.tmp / "Gen_UnitTest.sh").read_text()
        assert "jacoco" in content

    def test_gradle_script_contains_api_key(self):
        self._generate_gradle(api_key="gradle-secret-key")
        content = (self.tmp / "Gen_UnitTest.sh").read_text()
        assert "gradle-secret-key" in content
