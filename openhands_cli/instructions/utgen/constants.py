"""
Keploy configuration constants and default values.

These constants are used by the Keploy unit test generation skill
and associated scripts.
"""

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
