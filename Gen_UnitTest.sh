#!/bin/bash

ADDITIONAL_PROMPT=""
[ -f "architect.md" ] && ADDITIONAL_PROMPT="$(cat architect.md)"

[ -d ".venv" ] && source .venv/bin/activate

KEPLOY_ARGS=(
  --sourceFilePath="openhands_cli/acp_impl/utils/mcp.py"
  --testFilePath="tests/acp_impl/utils/test_mcp.py"
  --coverageReportPath="${COVERAGE_REPORT_PATH:-coverage.xml}"
  --coverageFormat="cobertura"
  --testCommand="uv run coverage run --include=openhands_cli/acp_impl/utils/mcp.py -m pytest tests/acp_impl/utils/test_mcp.py && uv run coverage xml"
  --expected-coverage=85
  --maxIterations=5
)
[ -n "$ADDITIONAL_PROMPT" ] && KEPLOY_ARGS+=(--additional-prompt="$ADDITIONAL_PROMPT")

keploy gen "${KEPLOY_ARGS[@]}"
