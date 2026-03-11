#!/bin/bash

# ============================================================================
# Keploy Gen Script for Python Projects - MCP Utils Testing
# ============================================================================

# --- CONFIGURATION ---
SOURCE_FILE_PATH="openhands_cli/acp_impl/utils/mcp.py"
TEST_FILE_PATH="tests/acp/utils/test_mcp.py"
COVERAGE_REPORT_PATH="coverage.xml"
COVERAGE_FORMAT="cobertura"
TEST_COMMAND="uv run coverage run --source=openhands_cli.acp_impl.utils.mcp -m pytest tests/acp/utils/test_mcp.py && uv run coverage xml"
EXPECTED_COVERAGE=85
MAX_ITERATIONS=5
LLM_BASE_URL="http://0.0.0.0:4000"
MODEL="claude-haiku-4-5"
FUNCTION_UNDER_TEST=""
FLAKINESS="false"
SERVER_URL=""
# ----------------------------

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "WARNING: .venv not found, skipping activation"
fi

# Set API key
export API_KEY="dummy"

# Build the keploy gen command
KEPLOY_CMD="keploy gen"
KEPLOY_CMD+=" --sourceFilePath=\"$SOURCE_FILE_PATH\""
KEPLOY_CMD+=" --testFilePath=\"$TEST_FILE_PATH\""
KEPLOY_CMD+=" --coverageReportPath=\"$COVERAGE_REPORT_PATH\""
KEPLOY_CMD+=" --coverageFormat=\"$COVERAGE_FORMAT\""
KEPLOY_CMD+=" --testCommand=\"$TEST_COMMAND\""
KEPLOY_CMD+=" --expected-coverage=$EXPECTED_COVERAGE"
KEPLOY_CMD+=" --maxIterations=$MAX_ITERATIONS"
KEPLOY_CMD+=" --llmBaseUrl=\"$LLM_BASE_URL\""
KEPLOY_CMD+=" --model=\"$MODEL\""

[ -n "$FUNCTION_UNDER_TEST" ] && KEPLOY_CMD+=" --function-under-test=\"$FUNCTION_UNDER_TEST\""
[ "$FLAKINESS" = "true" ] && KEPLOY_CMD+=" --flakiness"
[ -n "$SERVER_URL" ] && KEPLOY_CMD+=" --server-url=\"$SERVER_URL\""

# Display the command
echo "=========================================="
echo "Keploy Gen - Python Project (MCP Utils)"
echo "=========================================="
echo "Source File: $SOURCE_FILE_PATH"
echo "Test File: $TEST_FILE_PATH"
echo "Expected Coverage: $EXPECTED_COVERAGE%"
echo "Max Iterations: $MAX_ITERATIONS"
echo "Model: $MODEL"
echo "=========================================="

# Execute the command
eval $KEPLOY_CMD

# Capture exit code
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo "=========================================="
    echo "ERROR: Keploy gen failed with exit code $EXIT_CODE"
    echo "=========================================="
    exit $EXIT_CODE
else
    echo "=========================================="
    echo "SUCCESS: Keploy gen completed successfully"
    echo "=========================================="
fi