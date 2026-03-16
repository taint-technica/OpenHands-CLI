from unittest.mock import patch

from openhands_cli.ut_generation import python_handler


class TestDeriveTestPath:
    def test_nested_path(self):
        result = python_handler.derive_test_path("src/foo/bar.py")
        assert result == "tests/src/foo/test_bar.py"

    def test_flat_file_uses_tests_prefix(self):
        result = python_handler.derive_test_path("bar.py")
        assert result == "tests/tests_bar.py"

    def test_flat_file_no_test_prefix(self):
        result = python_handler.derive_test_path("bar.py")
        assert not result.endswith("test_bar.py")

    def test_deep_nested_path(self):
        result = python_handler.derive_test_path("a/b/c/d/module.py")
        assert result == "tests/a/b/c/d/test_module.py"

    def test_single_dir_path(self):
        result = python_handler.derive_test_path("myapp/auth.py")
        assert result == "tests/myapp/test_auth.py"

    def test_preserves_module_path(self):
        result = python_handler.derive_test_path("myapp/services/auth.py")
        assert result == "tests/myapp/services/test_auth.py"

    def test_output_starts_with_tests(self):
        result = python_handler.derive_test_path("src/main.py")
        assert result.startswith("tests/")

    def test_output_ends_with_py(self):
        result = python_handler.derive_test_path("src/main.py")
        assert result.endswith(".py")


class TestBuildTestCommand:
    def test_starts_with_uv_run_coverage(self):
        cmd = python_handler.build_test_command("src/app.py", "tests/test_app.py")
        assert cmd.startswith("uv run coverage run")

    def test_contains_include_flag(self):
        cmd = python_handler.build_test_command("src/app.py", "tests/test_app.py")
        assert "--include=src/app.py" in cmd

    def test_contains_test_file(self):
        cmd = python_handler.build_test_command("src/app.py", "tests/test_app.py")
        assert "tests/test_app.py" in cmd

    def test_contains_pytest(self):
        cmd = python_handler.build_test_command("src/app.py", "tests/test_app.py")
        assert "-m pytest" in cmd

    def test_resets_addopts(self):
        cmd = python_handler.build_test_command("src/app.py", "tests/test_app.py")
        assert "-o addopts=" in cmd

    def test_ends_with_coverage_xml(self):
        cmd = python_handler.build_test_command("src/app.py", "tests/test_app.py")
        assert cmd.endswith("uv run coverage xml")

    def test_source_and_test_in_same_command(self):
        cmd = python_handler.build_test_command("myapp/utils.py", "tests/myapp/test_utils.py")
        assert "myapp/utils.py" in cmd
        assert "tests/myapp/test_utils.py" in cmd


class TestGetTemplateAndPlaceholders:
    def test_returns_tuple(self, common_params):
        result = python_handler.get_template_and_placeholders(
            "src/app.py", **common_params
        )
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_template_is_string(self, common_params):
        template, _ = python_handler.get_template_and_placeholders(
            "src/app.py", **common_params
        )
        assert isinstance(template, str)

    def test_placeholders_is_dict(self, common_params):
        _, placeholders = python_handler.get_template_and_placeholders(
            "src/app.py", **common_params
        )
        assert isinstance(placeholders, dict)

    def test_has_all_required_keys(self, common_params):
        _, placeholders = python_handler.get_template_and_placeholders(
            "src/app.py", **common_params
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
        }
        assert required_keys.issubset(placeholders.keys())

    def test_source_file_path_value(self, common_params):
        _, placeholders = python_handler.get_template_and_placeholders(
            "src/app.py", **common_params
        )
        assert placeholders["SOURCE_FILE_PATH"] == "src/app.py"

    def test_expected_coverage_is_string(self, common_params):
        _, placeholders = python_handler.get_template_and_placeholders(
            "src/app.py", **common_params
        )
        assert placeholders["EXPECTED_COVERAGE"] == "85"
        assert isinstance(placeholders["EXPECTED_COVERAGE"], str)

    def test_max_iterations_is_string(self, common_params):
        _, placeholders = python_handler.get_template_and_placeholders(
            "src/app.py", **common_params
        )
        assert placeholders["MAX_ITERATIONS"] == "5"
        assert isinstance(placeholders["MAX_ITERATIONS"], str)

    def test_api_key_value(self, common_params):
        _, placeholders = python_handler.get_template_and_placeholders(
            "src/app.py", **common_params
        )
        assert placeholders["API_KEY"] == "test-api-key"

    def test_llm_base_url_value(self, common_params):
        _, placeholders = python_handler.get_template_and_placeholders(
            "src/app.py", **common_params
        )
        assert placeholders["LLM_BASE_URL"] == "https://api.test.com/v1"

    def test_model_value(self, common_params):
        _, placeholders = python_handler.get_template_and_placeholders(
            "src/app.py", **common_params
        )
        assert placeholders["MODEL"] == "gpt-4o"

    def test_test_file_path_consistent_with_derive(self, common_params):
        _, placeholders = python_handler.get_template_and_placeholders(
            "src/app.py", **common_params
        )
        expected_test_path = python_handler.derive_test_path("src/app.py")
        assert placeholders["TEST_FILE_PATH"] == expected_test_path

    def test_template_uses_python_template(self, common_params):
        with patch(
            "openhands_cli.ut_generation.python_handler.PYTHON_SCRIPT_TEMPLATE",
            "MOCK_TEMPLATE",
        ):
            template, _ = python_handler.get_template_and_placeholders(
                "src/app.py", **common_params
            )
        assert template == "MOCK_TEMPLATE"
