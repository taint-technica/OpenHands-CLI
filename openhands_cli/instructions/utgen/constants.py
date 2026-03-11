"""
Keploy configuration constants and default values.

These constants are used by the Keploy unit test generation skill
and associated scripts.
"""

# ============================================================================
# CLI ARGUMENT DESCRIPTIONS
# ============================================================================

CLI_ARGUMENTS = """
## Keploy Gen Command Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--source-file-path` | Path to the source file to test | Required |
| `--test-file-path` | Path to the output test file | Required |
| `--coverage-report-path` | Path to coverage report file | Platform-specific |
| `--test-command` | Command to run tests | Required |
| `--coverage-format` | Report type (cobertura/jacoco) | Platform-specific |
| `--expected-coverage` | Target coverage % | 85 |
| `--max-iterations` | Max generation attempts | 5 |
| `--llm-base-url` | AI model endpoint | http://0.0.0.0:4000 |
| `--model` | Model name | claude-haiku-4-5 |
| `--additional-prompt` | Extra context (e.g., architect.md) | "" |
| `--function-under-test` | Specific function to test | "" |
| `--flakiness` | Run flakiness check | false |
"""

# ============================================================================
# DEFAULT VALUES
# ============================================================================

DEFAULTS = {
    "expected_coverage": 85,
    "max_iterations": 5,
    "model": "claude-haiku-4-5",
    "llm_base_url": "http://0.0.0.0:4000",
    "function_under_test": "",
    "flakiness": False,
}

PYTHON_DEFAULTS = {
    "coverage_report_path": "coverage.xml",
    "coverage_format": "cobertura",
    "test_command_template": (
        "uv run coverage run --include={source_file} -m pytest {test_file} "
        "&& uv run coverage xml"
    ),
    "test_file_pattern": "test_{source_file}.py",
}

JAVA_DEFAULTS = {
    "coverage_report_path": "target/site/jacoco/jacoco.xml",
    "coverage_format": "jacoco",
    "test_command_template": "mvn verify -P coverage -Dtest={test_class}",
    "test_file_pattern": "{source_file}Test.java",
    "java_home": "/usr/lib/jvm/java-21-openjdk-amd64",
}

GEN_SCRIPT_FILE = """
**ALWAYS use `Gen_UnitTest.sh` as the dedicated script file:**
- If `Gen_UnitTest.sh` does NOT exist → Create it
- If `Gen_UnitTest.sh` EXISTS → Update/overwrite content (do NOT create new file)
- This file contains Keploy Gen Script with Python and Java template
- NEVER create multiple script files (no Gen_UnitTest_1.sh, Gen_UnitTest_2.sh, etc.)
- ALWAYS make it executable: `chmod +x Gen_UnitTest.sh`
"""

# ============================================================================
# KEYWORDS FOR TRIGGER
# ============================================================================

KEPLOY_KEYWORDS = [
    "gen unit test",
    "unit test",
    "unit test generation",
    "keploy gen",
    "keploy unit test",
    "gen unit test with keploy",
    "generate unit test with keploy",
    "keploy test generation",
]
