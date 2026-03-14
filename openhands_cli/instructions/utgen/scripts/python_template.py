"""
Keploy Gen bash script template for Python projects.

This script is imported by dev_skills.py to compose the skill content.
All content is compiled and protected by Nuitka.
"""

PYTHON_SCRIPT_TEMPLATE = """\
#!/bin/bash

ADDITIONAL_PROMPT=""
[ -f "architect.md" ] && ADDITIONAL_PROMPT="$(cat architect.md)"

[ -d ".venv" ] && source .venv/bin/activate

KEPLOY_ARGS=(
  --sourceFilePath="{{SOURCE_FILE_PATH}}"
  --testFilePath="{{TEST_FILE_PATH}}"
  --coverageReportPath="${{COVERAGE_REPORT_PATH:-coverage.xml}}"
  --coverageFormat="cobertura"
  --testCommand="{{TEST_COMMAND}}"
  --expected-coverage={{EXPECTED_COVERAGE}}
  --maxIterations={{MAX_ITERATIONS}}
)
[ -n "$ADDITIONAL_PROMPT" ] && KEPLOY_ARGS+=(--additional-prompt="$ADDITIONAL_PROMPT")

keploy gen "${{KEPLOY_ARGS[@]}}"
"""
