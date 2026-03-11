"""
Keploy Gen bash script template for Python projects.

This script is imported by dev_skills.py to compose the skill content.
All content is compiled and protected by Nuitka.
"""

PYTHON_SCRIPT_TEMPLATE = """\
#!/bin/bash

# ============================================================================
# Keploy Gen Script for Python Projects
# Fill in the placeholders below before running
# ============================================================================

# --- PLACEHOLDERS TO FILL ---
SOURCE_FILE_PATH="{{SOURCE_FILE_PATH}}"           # e.g., "backend/service/resume_evaluation.py"
TEST_FILE_PATH="{{TEST_FILE_PATH}}"               # e.g., "test/test_single_file/test_resume_evaluation.py"
COVERAGE_REPORT_PATH="${{COVERAGE_REPORT_PATH:-coverage.xml}}"
COVERAGE_FORMAT="${{COVERAGE_FORMAT:-cobertura}}"
TEST_COMMAND="{{TEST_COMMAND}}"                   # e.g., "uv run coverage run --include=<src> -m pytest <test> && uv run coverage xml"
EXPECTED_COVERAGE="${{EXPECTED_COVERAGE:-85}}"
MAX_ITERATIONS="${{MAX_ITERATIONS:-5}}"
LLM_BASE_URL="${{LLM_BASE_URL:-http://0.0.0.0:4000}}"
MODEL="${{MODEL:-claude-haiku-4-5}}"
LLM_API_VERSION="${{LLM_API_VERSION:-}}"
ADDITIONAL_PROMPT="{{ADDITIONAL_PROMPT}}"
FUNCTION_UNDER_TEST="${{FUNCTION_UNDER_TEST:-}}"
FLAKINESS="${{FLAKINESS:-false}}"
SERVER_URL="${{SERVER_URL:-}}"
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
KEPLOY_CMD+=" --sourceFilePath=\\"$SOURCE_FILE_PATH\\""
KEPLOY_CMD+=" --testFilePath=\\"$TEST_FILE_PATH\\""
KEPLOY_CMD+=" --coverageReportPath=\\"$COVERAGE_REPORT_PATH\\""
KEPLOY_CMD+=" --coverageFormat=\\"$COVERAGE_FORMAT\\""
KEPLOY_CMD+=" --testCommand=\\"$TEST_COMMAND\\""
KEPLOY_CMD+=" --expected-coverage=$EXPECTED_COVERAGE"
KEPLOY_CMD+=" --maxIterations=$MAX_ITERATIONS"
KEPLOY_CMD+=" --llmBaseUrl=\\"$LLM_BASE_URL\\""
KEPLOY_CMD+=" --model=\\"$MODEL\\""

[ -n "$LLM_API_VERSION" ] && KEPLOY_CMD+=" --llm-api-version=\\"$LLM_API_VERSION\\""
[ -n "$ADDITIONAL_PROMPT" ] && KEPLOY_CMD+=" --additional-prompt=\\"$ADDITIONAL_PROMPT\\""
[ -n "$FUNCTION_UNDER_TEST" ] && KEPLOY_CMD+=" --function-under-test=\\"$FUNCTION_UNDER_TEST\\""
[ "$FLAKINESS" = "true" ] && KEPLOY_CMD+=" --flakiness"
[ -n "$SERVER_URL" ] && KEPLOY_CMD+=" --server-url=\\"$SERVER_URL\\""

# Display the command
echo "=========================================="
echo "Keploy Gen - Python Project"
echo "=========================================="
echo "Command: $KEPLOY_CMD"
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
"""
