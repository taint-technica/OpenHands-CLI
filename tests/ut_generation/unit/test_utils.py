import pytest

from openhands_cli.ut_generation.utils import create_test_file_if_not_exists, detect_language


class TestDetectLanguage:
    def test_python_extension(self):
        assert detect_language("main.py") == "python"

    def test_java_extension(self):
        assert detect_language("Main.java") == "java"

    def test_nested_python_path(self):
        assert detect_language("src/myapp/utils.py") == "python"

    def test_nested_java_path(self):
        assert detect_language("src/main/java/com/example/Service.java") == "java"

    def test_unsupported_go_extension(self):
        with pytest.raises(ValueError):
            detect_language("main.go")

    def test_unsupported_ts_extension(self):
        with pytest.raises(ValueError):
            detect_language("index.ts")

    def test_no_extension_raises(self):
        with pytest.raises(ValueError):
            detect_language("Makefile")

    def test_uppercase_extension_raises(self):
        with pytest.raises(ValueError):
            detect_language("Main.PY")

    def test_error_message_contains_extension(self):
        with pytest.raises(ValueError, match=r"\.go"):
            detect_language("main.go")

    def test_error_message_for_no_extension(self):
        with pytest.raises(ValueError):
            detect_language("Makefile")


class TestCreateTestFileIfNotExists:
    def test_creates_file(self, tmp_path):
        test_file = tmp_path / "tests" / "test_foo.py"
        create_test_file_if_not_exists(str(test_file))
        assert test_file.exists()

    def test_creates_parent_directories(self, tmp_path):
        test_file = tmp_path / "a" / "b" / "c" / "test_deep.py"
        create_test_file_if_not_exists(str(test_file))
        assert test_file.exists()
        assert test_file.parent.is_dir()

    def test_created_file_is_empty(self, tmp_path):
        test_file = tmp_path / "tests" / "test_foo.py"
        create_test_file_if_not_exists(str(test_file))
        assert test_file.read_text() == ""

    def test_noop_if_file_already_exists(self, tmp_path):
        test_file = tmp_path / "tests" / "test_foo.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("existing content")

        create_test_file_if_not_exists(str(test_file))

        assert test_file.read_text() == "existing content"

    def test_creates_deeply_nested_dirs(self, tmp_path):
        test_file = tmp_path / "a" / "b" / "c" / "d" / "e" / "test_deep.py"
        create_test_file_if_not_exists(str(test_file))
        assert test_file.exists()

    def test_idempotent_on_repeated_calls(self, tmp_path):
        test_file = tmp_path / "tests" / "test_foo.py"
        create_test_file_if_not_exists(str(test_file))
        create_test_file_if_not_exists(str(test_file))
        assert test_file.exists()
