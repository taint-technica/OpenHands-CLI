"""
Keploy Gen bash script template for Python projects.

This script is imported by dev_skills.py to compose the skill content.
All content is compiled and protected by Nuitka.
"""

PYTHON_SCRIPT_TEMPLATE = """\
#!/bin/bash

export API_KEY="{{API_KEY}}"

# Trace taxonomy for downstream observability (OpenHands + Keploy split)
export OPENHANDS_TRACE_SOURCE="{{TRACE_SOURCE}}"
export OPENHANDS_TRACE_FLOW="{{TRACE_FLOW}}"
export OPENHANDS_PROJECT_NAME="{{PROJECT_NAME}}"
export OPENHANDS_TRACE_INVOKER="openhands"

ADDITIONAL_PROMPT=""
[ -f "ARCHITECTURE.md" ] && ADDITIONAL_PROMPT="$(cat ARCHITECTURE.md)"

unset VIRTUAL_ENV
[ -d ".venv" ] && source .venv/bin/activate

KEPLOY_ARGS=(
  --sourceFilePath="{{SOURCE_FILE_PATH}}"
  --testFilePath="{{TEST_FILE_PATH}}"
  --coverageReportPath="${{COVERAGE_REPORT_PATH:-coverage.xml}}"
  --coverageFormat="cobertura"
  --testCommand="{{TEST_COMMAND}}"
  --expected-coverage={{EXPECTED_COVERAGE}}
  --maxIterations={{MAX_ITERATIONS}}
  --llm-base-url={{LLM_BASE_URL}}
  --model={{MODEL}}
)
[ -n "$ADDITIONAL_PROMPT" ] && KEPLOY_ARGS+=(--additional-prompt="$ADDITIONAL_PROMPT")

keploy gen "${{KEPLOY_ARGS[@]}}"
"""
