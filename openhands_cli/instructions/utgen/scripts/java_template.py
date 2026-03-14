"""
Keploy Gen bash script template for Java projects.

This script is imported by dev_skills.py to compose the skill content.
All content is compiled and protected by Nuitka.
"""

JAVA_SCRIPT_TEMPLATE = """\
#!/bin/bash

SOURCE_FILE_PATH="{{SOURCE_FILE_PATH}}"
TEST_FILE_PATH="{{TEST_FILE_PATH}}"
COVERAGE_REPORT_PATH="{{COVERAGE_REPORT_PATH}}"
COVERAGE_FORMAT="${{COVERAGE_FORMAT:-jacoco}}"
TEST_COMMAND="{{TEST_COMMAND}}"
EXPECTED_COVERAGE="${{EXPECTED_COVERAGE:-85}}"
MAX_ITERATIONS="${{MAX_ITERATIONS:-5}}"
LLM_BASE_URL="${{LLM_BASE_URL:-http://0.0.0.0:4000}}"
MODEL="${{MODEL:-claude-haiku-4-5}}"
LLM_API_VERSION="${{LLM_API_VERSION:-}}"
FUNCTION_UNDER_TEST="${{FUNCTION_UNDER_TEST:-}}"
FLAKINESS="${{FLAKINESS:-false}}"
SERVER_URL="${{SERVER_URL:-}}"
JAVA_HOME="{{JAVA_HOME}}"
BUILD_CLEAN_COMMAND="{{BUILD_CLEAN_COMMAND}}"

# Load ARCHITECTURE.md if exists, combine with user prompt
ADDITIONAL_PROMPT=""
[ -f "ARCHITECTURE.md" ] && ADDITIONAL_PROMPT="$(cat ARCHITECTURE.md)"
USER_PROMPT="{{ADDITIONAL_PROMPT}}"
[ -n "$USER_PROMPT" ] && ADDITIONAL_PROMPT="${{ADDITIONAL_PROMPT:+$ADDITIONAL_PROMPT\\n}}$USER_PROMPT"

export API_KEY="dummy"
export JAVA_HOME
export PATH="/usr/bin:/usr/local/bin:$PATH"

$BUILD_CLEAN_COMMAND

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

eval $KEPLOY_CMD
exit $?
"""
