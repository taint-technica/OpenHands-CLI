"""Unit tests for openhands_cli.ut_generation.generator module."""

from openhands_cli.ut_generation.config import OUTPUT_SCRIPT_NAME
from openhands_cli.ut_generation.generator import (
    derive_test_file_path,
    render_script,
    write_script,
)


class TestRenderScript:
    def test_replaces_single_placeholder(self):
        template = "Hello {{NAME}}!"
        result = render_script(template, {"NAME": "World"})
        assert result == "Hello World!"

    def test_replaces_multiple_placeholders(self):
        template = "{{GREETING}} {{NAME}}!"
        result = render_script(template, {"GREETING": "Hello", "NAME": "World"})
        assert result == "Hello World!"

    def test_double_braces_become_single(self):
        # After placeholders, remaining {{ → { and }} → }
        template = "array[${{INDEX}}]"
        result = render_script(template, {})
        assert result == "array[${INDEX}]"

    def test_bash_variable_syntax_preserved(self):
        # ${VAR} in bash - template uses ${{VAR}}
        template = 'echo "${{HOME}}"'
        result = render_script(template, {})
        assert result == 'echo "${HOME}"'

    def test_coverage_report_path_bash_default(self):
        # The Python template has ${{COVERAGE_REPORT_PATH:-coverage.xml}}
        template = '${{COVERAGE_REPORT_PATH:-coverage.xml}}'
        result = render_script(template, {})
        assert result == '${COVERAGE_REPORT_PATH:-coverage.xml}'

    def test_placeholder_not_in_dict_remains_intact_after_double_brace_collapse(self):
        # Placeholder not in dict: {{UNKNOWN}} → first pass no change, then {{ → { }} → }
        template = "{{UNKNOWN}}"
        result = render_script(template, {})
        assert result == "{UNKNOWN}"

    def test_empty_template(self):
        result = render_script("", {"KEY": "value"})
        assert result == ""

    def test_empty_placeholders(self):
        result = render_script("no placeholders here", {})
        assert result == "no placeholders here"

    def test_placeholder_value_with_spaces(self):
        template = "--testCommand={{TEST_COMMAND}}"
        result = render_script(template, {"TEST_COMMAND": "uv run pytest tests/"})
        assert result == "--testCommand=uv run pytest tests/"

    def test_placeholder_with_path(self):
        template = "--sourceFilePath={{SOURCE_FILE_PATH}}"
        result = render_script(template, {"SOURCE_FILE_PATH": "src/main/java/Foo.java"})
        assert result == "--sourceFilePath=src/main/java/Foo.java"

    def test_returns_string(self):
        result = render_script("{{KEY}}", {"KEY": "val"})
        assert isinstance(result, str)

    def test_keploy_args_array_syntax(self):
        # keploy gen "${{KEPLOY_ARGS[@]}}" in template → keploy gen "${KEPLOY_ARGS[@]}"
        template = 'keploy gen "${{KEPLOY_ARGS[@]}}"'
        result = render_script(template, {})
        assert result == 'keploy gen "${KEPLOY_ARGS[@]}"'

    def test_multiple_occurrences_of_same_placeholder(self):
        template = "{{X}} and {{X}}"
        result = render_script(template, {"X": "hello"})
        assert result == "hello and hello"


class TestWriteScript:
    def test_writes_content_to_default_path(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        write_script("#!/bin/bash\necho hello")
        output = tmp_path / OUTPUT_SCRIPT_NAME
        assert output.exists()
        assert output.read_text() == "#!/bin/bash\necho hello"

    def test_writes_content_to_custom_path(self, tmp_path):
        custom_path = str(tmp_path / "custom_script.sh")
        write_script("content here", output_path=custom_path)
        assert (tmp_path / "custom_script.sh").read_text() == "content here"

    def test_overwrites_existing_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        output = tmp_path / OUTPUT_SCRIPT_NAME
        output.write_text("old content")
        write_script("new content")
        assert output.read_text() == "new content"

    def test_writes_multiline_content(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        content = "#!/bin/bash\nline1\nline2\n"
        write_script(content)
        output = tmp_path / OUTPUT_SCRIPT_NAME
        assert output.read_text() == content

    def test_empty_content(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        write_script("")
        output = tmp_path / OUTPUT_SCRIPT_NAME
        assert output.read_text() == ""


class TestDeriveTestFilePath:
    def test_python_language(self):
        result = derive_test_file_path("src/foo.py", "python")
        assert result is not None
        assert "test_foo.py" in result

    def test_java_language(self):
        result = derive_test_file_path("src/main/java/Foo.java", "java")
        assert result == "src/test/java/FooTest.java"

    def test_unsupported_language_returns_none(self):
        result = derive_test_file_path("main.go", "go")
        assert result is None

    def test_empty_language_returns_none(self):
        result = derive_test_file_path("file.rs", "")
        assert result is None

    def test_python_result_starts_with_tests(self):
        result = derive_test_file_path("pkg/module.py", "python")
        assert isinstance(result, str)
        assert result.startswith("tests/")

    def test_java_result_has_test_suffix(self):
        result = derive_test_file_path("src/main/java/Calculator.java", "java")
        assert isinstance(result, str)
        assert result.endswith("CalculatorTest.java")

    def test_returns_string_for_python(self):
        result = derive_test_file_path("src/foo.py", "python")
        assert isinstance(result, str)

    def test_returns_string_for_java(self):
        result = derive_test_file_path("src/main/java/Foo.java", "java")
        assert isinstance(result, str)
