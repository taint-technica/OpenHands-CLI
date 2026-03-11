"""
Keploy Gen bash script template for Java projects.

This script is imported by dev_skills.py to compose the skill content.
All content is compiled and protected by Nuitka.
"""

JAVA_SCRIPT_TEMPLATE = """\
#!/bin/bash

# ============================================================================
# Keploy Gen Script for Java Projects
# Fill in the placeholders below before running
# ============================================================================

# --- PLACEHOLDERS TO FILL ---
SOURCE_FILE_PATH="{{SOURCE_FILE_PATH}}"           # e.g., "src/main/java/com/example/service/MyService.java"
TEST_FILE_PATH="{{TEST_FILE_PATH}}"               # e.g., "src/test/java/com/example/service/MyServiceTest.java"
COVERAGE_REPORT_PATH="${{COVERAGE_REPORT_PATH:-target/site/jacoco/jacoco.xml}}"
COVERAGE_FORMAT="${{COVERAGE_FORMAT:-jacoco}}"
TEST_COMMAND="{{TEST_COMMAND}}"                   # e.g., "mvn verify -P coverage -Dtest=MyServiceTest"
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

# Set environment variables
export API_KEY="dummy"
export JAVA_HOME="${JAVA_HOME:-/usr/lib/jvm/java-21-openjdk-amd64}"
export PATH="/usr/bin:/usr/local/bin:$PATH"

# Clean Maven build
echo "Running mvn clean..."
mvn clean

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
echo "Keploy Gen - Java Project"
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
