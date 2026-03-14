"""
Keploy Gen bash script template for Java projects.

This script is imported by dev_skills.py to compose the skill content.
All content is compiled and protected by Nuitka.
"""

JAVA_SCRIPT_TEMPLATE = """\
#!/bin/bash

ADDITIONAL_PROMPT=""
[ -f "ARCHITECTURE.md" ] && ADDITIONAL_PROMPT="$(cat ARCHITECTURE.md)"

export JAVA_HOME="{{JAVA_HOME}}"
export PATH="/usr/bin:/usr/local/bin:$PATH"

{{BUILD_CLEAN_COMMAND}}

KEPLOY_ARGS=(
  --sourceFilePath="{{SOURCE_FILE_PATH}}"
  --testFilePath="{{TEST_FILE_PATH}}"
  --coverageReportPath="{{COVERAGE_REPORT_PATH}}"
  --coverageFormat="jacoco"
  --testCommand="{{TEST_COMMAND}}"
  --expected-coverage={{EXPECTED_COVERAGE}}
  --maxIterations={{MAX_ITERATIONS}}
)
[ -n "$ADDITIONAL_PROMPT" ] && KEPLOY_ARGS+=(--additional-prompt="$ADDITIONAL_PROMPT")

keploy gen "${{KEPLOY_ARGS[@]}}"
"""
