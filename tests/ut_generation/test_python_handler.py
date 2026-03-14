"""Unit tests for openhands_cli.ut_generation.python_handler module."""

from openhands_cli.ut_generation import python_handler


class TestDeriveTestPath:
    def test_simple_two_part_path(self):
        # src/bar.py → tests/test_bar.py (first part "src" removed)
        result = python_handler.derive_test_path("src/bar.py")
        assert result == "tests/test_bar.py"

    def test_three_part_path(self):
        # src/foo/bar.py → tests/foo/test_bar.py
        result = python_handler.derive_test_path("src/foo/bar.py")
        assert result == "tests/foo/test_bar.py"

    def test_deep_nested_path(self):
        result = python_handler.derive_test_path("src/a/b/c/module.py")
        assert result == "tests/a/b/c/test_module.py"

    def test_test_prefix_added_to_filename(self):
        result = python_handler.derive_test_path("pkg/utils.py")
        assert "test_utils.py" in result

    def test_result_starts_with_tests(self):
        result = python_handler.derive_test_path("openhands_cli/generator.py")
        assert result.startswith("tests/")

    def test_result_ends_with_py(self):
        result = python_handler.derive_test_path("src/module.py")
        assert result.endswith(".py")

    def test_preserves_intermediate_directories(self):
        result = python_handler.derive_test_path("openhands_cli/ut_generation/utils.py")
        assert "ut_generation" in result

    def test_two_level_module(self):
        result = python_handler.derive_test_path("openhands_cli/utils.py")
        assert result == "tests/test_utils.py"


class TestBuildTestCommand:
    def test_contains_coverage_run(self):
        cmd = python_handler.build_test_command("src/foo.py", "tests/test_foo.py")
        assert "coverage run" in cmd

    def test_contains_pytest(self):
        cmd = python_handler.build_test_command("src/foo.py", "tests/test_foo.py")
        assert "pytest" in cmd

    def test_contains_source_file(self):
        cmd = python_handler.build_test_command("src/mymodule.py", "tests/test_mymodule.py")
        assert "src/mymodule.py" in cmd

    def test_contains_test_file(self):
        cmd = python_handler.build_test_command("src/mymodule.py", "tests/test_mymodule.py")
        assert "tests/test_mymodule.py" in cmd

    def test_contains_coverage_xml(self):
        cmd = python_handler.build_test_command("src/foo.py", "tests/test_foo.py")
        assert "coverage xml" in cmd

    def test_uses_uv_run(self):
        cmd = python_handler.build_test_command("src/foo.py", "tests/test_foo.py")
        assert "uv run" in cmd

    def test_contains_include_flag(self):
        cmd = python_handler.build_test_command("src/foo.py", "tests/test_foo.py")
        assert "--include=src/foo.py" in cmd

    def test_full_command_format(self):
        cmd = python_handler.build_test_command("src/foo.py", "tests/test_foo.py")
        expected = (
            "uv run coverage run --include=src/foo.py "
            "-m pytest tests/test_foo.py && uv run coverage xml"
        )
        assert cmd == expected

    def test_is_string(self):
        cmd = python_handler.build_test_command("a.py", "test_a.py")
        assert isinstance(cmd, str)


class TestGetTemplateAndPlaceholders:
    def test_returns_tuple(self):
        result = python_handler.get_template_and_placeholders("src/foo.py", 85, 5)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_placeholders_has_source_file_path(self):
        _, placeholders = python_handler.get_template_and_placeholders("src/foo.py", 85, 5)
        assert placeholders["SOURCE_FILE_PATH"] == "src/foo.py"

    def test_placeholders_has_test_file_path(self):
        _, placeholders = python_handler.get_template_and_placeholders("src/foo.py", 85, 5)
        assert "TEST_FILE_PATH" in placeholders
        assert "test_foo.py" in placeholders["TEST_FILE_PATH"]

    def test_placeholders_has_test_command(self):
        _, placeholders = python_handler.get_template_and_placeholders("src/foo.py", 85, 5)
        assert "TEST_COMMAND" in placeholders
        assert "pytest" in placeholders["TEST_COMMAND"]

    def test_placeholders_expected_coverage(self):
        _, placeholders = python_handler.get_template_and_placeholders("src/foo.py", 90, 5)
        assert placeholders["EXPECTED_COVERAGE"] == "90"

    def test_placeholders_max_iterations(self):
        _, placeholders = python_handler.get_template_and_placeholders("src/foo.py", 85, 10)
        assert placeholders["MAX_ITERATIONS"] == "10"

    def test_expected_coverage_is_string(self):
        _, placeholders = python_handler.get_template_and_placeholders("src/foo.py", 75, 3)
        assert isinstance(placeholders["EXPECTED_COVERAGE"], str)

    def test_max_iterations_is_string(self):
        _, placeholders = python_handler.get_template_and_placeholders("src/foo.py", 85, 3)
        assert isinstance(placeholders["MAX_ITERATIONS"], str)

    def test_template_is_string(self):
        template, _ = python_handler.get_template_and_placeholders("src/foo.py", 85, 5)
        assert isinstance(template, str)

    def test_template_contains_bash_shebang(self):
        template, _ = python_handler.get_template_and_placeholders("src/foo.py", 85, 5)
        assert "#!/bin/bash" in template

    def test_template_contains_keploy_gen(self):
        template, _ = python_handler.get_template_and_placeholders("src/foo.py", 85, 5)
        assert "keploy gen" in template

    def test_five_required_placeholder_keys(self):
        _, placeholders = python_handler.get_template_and_placeholders("src/foo.py", 85, 5)
        required_keys = {
            "SOURCE_FILE_PATH",
            "TEST_FILE_PATH",
            "TEST_COMMAND",
            "EXPECTED_COVERAGE",
            "MAX_ITERATIONS",
        }
        assert required_keys.issubset(placeholders.keys())

    def test_default_coverage_used(self):
        _, placeholders = python_handler.get_template_and_placeholders("src/foo.py", 85, 5)
        assert placeholders["EXPECTED_COVERAGE"] == "85"
