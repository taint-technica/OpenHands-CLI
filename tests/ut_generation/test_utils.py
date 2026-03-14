"""Unit tests for openhands_cli.ut_generation.utils module."""

import pytest

from openhands_cli.ut_generation.utils import (
    create_test_file_if_not_exists,
    detect_language,
)


class TestDetectLanguage:
    def test_python_extension(self):
        assert detect_language("foo.py") == "python"

    def test_java_extension(self):
        assert detect_language("Foo.java") == "java"

    def test_python_with_directory(self):
        assert detect_language("src/module/bar.py") == "python"

    def test_java_with_directory(self):
        assert detect_language("src/main/java/com/Example.java") == "java"

    def test_unsupported_extension_raises_value_error(self):
        with pytest.raises(ValueError, match="Unsupported file extension"):
            detect_language("script.js")

    def test_unsupported_go_raises_value_error(self):
        with pytest.raises(ValueError, match="Unsupported file extension"):
            detect_language("main.go")

    def test_unsupported_ts_raises_value_error(self):
        with pytest.raises(ValueError, match="Unsupported file extension"):
            detect_language("index.ts")

    def test_no_extension_raises_value_error(self):
        with pytest.raises(ValueError, match="Unsupported file extension"):
            detect_language("Makefile")

    def test_dotfile_raises_value_error(self):
        with pytest.raises(ValueError):
            detect_language(".env")

    def test_uppercase_extension_raises_value_error(self):
        # Extension matching is case-sensitive
        with pytest.raises(ValueError):
            detect_language("Main.JAVA")

    def test_error_message_includes_extension(self):
        with pytest.raises(ValueError, match=r"\.js"):
            detect_language("app.js")


class TestCreateTestFileIfNotExists:
    def test_creates_file_in_existing_directory(self, tmp_path):
        test_file = tmp_path / "test_module.py"
        create_test_file_if_not_exists(str(test_file))
        assert test_file.exists()

    def test_created_file_is_empty(self, tmp_path):
        test_file = tmp_path / "test_module.py"
        create_test_file_if_not_exists(str(test_file))
        assert test_file.read_text() == ""

    def test_creates_parent_directories(self, tmp_path):
        test_file = tmp_path / "a" / "b" / "c" / "test_deep.py"
        create_test_file_if_not_exists(str(test_file))
        assert test_file.exists()

    def test_creates_nested_directories(self, tmp_path):
        test_file = tmp_path / "tests" / "foo" / "test_bar.py"
        create_test_file_if_not_exists(str(test_file))
        assert (tmp_path / "tests" / "foo").is_dir()

    def test_does_not_overwrite_existing_file(self, tmp_path):
        test_file = tmp_path / "test_existing.py"
        existing_content = "# existing test content\n"
        test_file.write_text(existing_content)

        create_test_file_if_not_exists(str(test_file))

        assert test_file.read_text() == existing_content

    def test_idempotent_on_existing_file(self, tmp_path):
        test_file = tmp_path / "test_module.py"
        create_test_file_if_not_exists(str(test_file))
        create_test_file_if_not_exists(str(test_file))
        assert test_file.exists()

    def test_creates_java_test_file(self, tmp_path):
        test_file = tmp_path / "src" / "test" / "java" / "FooTest.java"
        create_test_file_if_not_exists(str(test_file))
        assert test_file.exists()
