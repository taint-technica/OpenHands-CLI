#!/bin/bash

# ============================================================================
# Keploy Gen Script for OpenHands-CLI utils.py Testing
# ============================================================================

# --- Configuration ---
SOURCE_FILE_PATH="openhands_cli/utils.py"
TEST_FILE_PATH="tests/test_utils.py"
COVERAGE_REPORT_PATH="coverage.xml"
COVERAGE_FORMAT="cobertura"
TEST_COMMAND="uv run coverage run --include=openhands_cli/utils.py -m pytest tests/test_utils.py && uv run coverage xml"
EXPECTED_COVERAGE="80"
MAX_ITERATIONS="5"
LLM_BASE_URL="http://0.0.0.0:4000"
MODEL="claude-haiku-4-5"
ADDITIONAL_PROMPT="This is the OpenHands-CLI project. The utils.py file contains utility functions for LLM configuration and agent setup. Key functions to test: abbreviate_number (formats numbers with K/M/B suffixes), format_cost (formats cost values), get_os_description (returns OS info), should_set_litellm_extra_body (checks if litellm_extra_body should be set based on model/URL), get_llm_metadata (generates LLM metadata), get_default_cli_tools (returns default tool specifications), get_default_cli_agent (creates default CLI agent), create_seeded_instructions_from_args (builds initial CLI input from arguments), extract_text_from_message_content (extracts text from message content), and json_callback (prints events as JSON). Ensure comprehensive coverage of edge cases, boundary conditions, and error handling."
FUNCTION_UNDER_TEST=""
FLAKINESS="false"
SERVER_URL=""

# ---

# Set API key
export API_KEY="dummy"

# Activate virtual environment if needed
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

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
KEPLOY_CMD+=" --additional-prompt=\"$ADDITIONAL_PROMPT\""

[ -n "$FUNCTION_UNDER_TEST" ] && KEPLOY_CMD+=" --function-under-test=\"$FUNCTION_UNDER_TEST\""
[ "$FLAKINESS" = "true" ] && KEPLOY_CMD+=" --flakiness"
[ -n "$SERVER_URL" ] && KEPLOY_CMD+=" --server-url=\"$SERVER_URL\""

# Display the command
echo "=========================================="
echo "Keploy Gen - OpenHands-CLI utils.py"
echo "=========================================="
echo "Source File: $SOURCE_FILE_PATH"
echo "Test File: $TEST_FILE_PATH"
echo "Expected Coverage: $EXPECTED_COVERAGE%"
echo "Max Iterations: $MAX_ITERATIONS"
echo "Model: $MODEL"
echo "=========================================="
echo ""

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
