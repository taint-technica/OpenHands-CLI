import pytest
from pathlib import Path
from unittest.mock import patch

from openhands_cli.ut_generation.generator import (
    generate_unit_test_script,
    render_script,
    write_script,
)


class TestRenderScript:
    def test_replaces_single_placeholder(self):
        result = render_script("Hello {{NAME}}", {"NAME": "World"})
        assert result == "Hello World"

    def test_replaces_multiple_placeholders(self):
        result = render_script(
            "{{A}} and {{B}}",
            {"A": "foo", "B": "bar"},
        )
        assert result == "foo and bar"

    def test_bash_double_braces_become_single(self):
        result = render_script("echo ${{HOME}}", {})
        assert result == "echo ${HOME}"

    def test_placeholder_and_bash_brace_coexist(self):
        result = render_script("SOURCE={{SRC}} HOME=${{HOME}}", {"SRC": "app.py"})
        assert result == "SOURCE=app.py HOME=${HOME}"

    def test_value_with_special_chars(self):
        result = render_script("URL={{URL}}", {"URL": "https://api.example.com/v1"})
        assert result == "URL=https://api.example.com/v1"

    def test_value_with_path_separators(self):
        result = render_script("FILE={{FILE}}", {"FILE": "src/main/app.py"})
        assert result == "FILE=src/main/app.py"

    def test_empty_placeholders_only_unescapes_braces(self):
        result = render_script("${{VAR}}", {})
        assert result == "${VAR}"

    def test_multiple_occurrences_of_same_placeholder(self):
        result = render_script("{{X}} {{X}} {{X}}", {"X": "hello"})
        assert result == "hello hello hello"

    def test_returns_string(self):
        result = render_script("template", {})
        assert isinstance(result, str)


class TestWriteScript:
    def test_writes_content_to_default_path(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        write_script("#!/bin/bash\necho hello")
        output = tmp_path / "Gen_UnitTest.sh"
        assert output.exists()
        assert output.read_text() == "#!/bin/bash\necho hello"

    def test_writes_to_custom_path(self, tmp_path):
        custom_path = str(tmp_path / "custom_script.sh")
        write_script("content", custom_path)
        assert Path(custom_path).read_text() == "content"

    def test_creates_parent_directories(self, tmp_path):
        nested_path = str(tmp_path / "a" / "b" / "script.sh")
        write_script("content", nested_path)
        assert Path(nested_path).exists()

    def test_overwrites_existing_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        script = tmp_path / "Gen_UnitTest.sh"
        script.write_text("old content")
        write_script("new content")
        assert script.read_text() == "new content"


class TestGenerateUnitTestScript:
    def test_unsupported_extension_raises(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with pytest.raises(ValueError):
            generate_unit_test_script(
                "main.go", 85, 5, "key", "https://api.test.com", "gpt-4o"
            )

    def test_calls_detect_language(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with patch("openhands_cli.ut_generation.generator.detect_language") as mock_detect, \
             patch("openhands_cli.ut_generation.generator.python_handler") as mock_handler, \
             patch("openhands_cli.ut_generation.generator.create_test_file_if_not_exists"), \
             patch("openhands_cli.ut_generation.generator.write_script"):
            mock_detect.return_value = "python"
            mock_handler.get_template_and_placeholders.return_value = (
                "TEMPLATE",
                {"TEST_FILE_PATH": "tests/test_main.py"},
            )
            generate_unit_test_script(
                "src/main.py", 85, 5, "key", "https://api.test.com", "gpt-4o"
            )
        mock_detect.assert_called_once_with("src/main.py")

    def test_dispatches_to_python_handler(self, tmp_path, monkeypatch):
        from unittest.mock import MagicMock
        monkeypatch.chdir(tmp_path)
        mock_handler = MagicMock()
        mock_handler.get_template_and_placeholders.return_value = (
            "TEMPLATE",
            {"TEST_FILE_PATH": "tests/test_main.py"},
        )
        with patch("openhands_cli.ut_generation.generator.detect_language", return_value="python"), \
             patch("openhands_cli.ut_generation.generator.HANDLER", {"python": mock_handler}), \
             patch("openhands_cli.ut_generation.generator.create_test_file_if_not_exists"), \
             patch("openhands_cli.ut_generation.generator.write_script"):
            generate_unit_test_script(
                "src/main.py", 85, 5, "key", "https://api.test.com", "gpt-4o"
            )
        mock_handler.get_template_and_placeholders.assert_called_once()

    def test_creates_test_file_with_correct_path(self, tmp_path, monkeypatch):
        from unittest.mock import MagicMock
        monkeypatch.chdir(tmp_path)
        mock_handler = MagicMock()
        mock_handler.get_template_and_placeholders.return_value = (
            "TEMPLATE",
            {"TEST_FILE_PATH": "tests/my_test_path.py"},
        )
        with patch("openhands_cli.ut_generation.generator.detect_language", return_value="python"), \
             patch("openhands_cli.ut_generation.generator.HANDLER", {"python": mock_handler}), \
             patch("openhands_cli.ut_generation.generator.create_test_file_if_not_exists") as mock_create, \
             patch("openhands_cli.ut_generation.generator.write_script"):
            generate_unit_test_script(
                "src/main.py", 85, 5, "key", "https://api.test.com", "gpt-4o"
            )
        mock_create.assert_called_once_with("tests/my_test_path.py")

    def test_calls_write_script(self, tmp_path, monkeypatch):
        from unittest.mock import MagicMock
        monkeypatch.chdir(tmp_path)
        mock_handler = MagicMock()
        mock_handler.get_template_and_placeholders.return_value = (
            "{{KEY}} content",
            {"KEY": "rendered", "TEST_FILE_PATH": "tests/test_main.py"},
        )
        with patch("openhands_cli.ut_generation.generator.detect_language", return_value="python"), \
             patch("openhands_cli.ut_generation.generator.HANDLER", {"python": mock_handler}), \
             patch("openhands_cli.ut_generation.generator.create_test_file_if_not_exists"), \
             patch("openhands_cli.ut_generation.generator.write_script") as mock_write:
            generate_unit_test_script(
                "src/main.py", 85, 5, "key", "https://api.test.com", "gpt-4o"
            )
        mock_write.assert_called_once()
        written_content = mock_write.call_args[1]["content"]
        assert written_content == "rendered content"

    def test_language_not_in_handler_raises(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with patch("openhands_cli.ut_generation.generator.detect_language", return_value="rust"), \
             pytest.raises(ValueError, match="Unsupported"):
            generate_unit_test_script(
                "src/main.rs", 85, 5, "key", "https://api.test.com", "gpt-4o"
            )
