"""
Keploy workflow documentation for Python and Java projects.

These strings provide quick reference guides for using Keploy gen.
"""

PYTHON_WORKFLOW = """
### Python Project Setup

1. **Check and install uv:**
    ```bash
    if ! command -v uv &> /dev/null; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
        [ -f "$HOME/.local/bin/env" ] && source "$HOME/.local/bin/env"
        [ -f "$HOME/.cargo/env" ] && source "$HOME/.cargo/env"
    fi
    ```

2. **Install Dependencies:**
   ```bash
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    else
        uv venv .venv
        source .venv/bin/activate
    fi
    uv sync
    uv add pip pytest pytest-asyncio coverage
    export API_KEY="dummy"
    ```

3. **Coverage Configuration**
    - `--coverageReportPath="coverage.xml"`
    - `--coverageFormat="cobertura"`

4. **Test Command Pattern:**
    ```bash
   uv run coverage run --include=<source_file> -m pytest <test_file> && uv run coverage xml
   ```
"""

JAVA_WORKFLOW = """
### Java Project Setup

#### Detect Build Tool & Fill Placeholders

Read the project to determine the build tool, then fill in the script template placeholders accordingly:

**`{{JAVA_HOME}}`** — detect Java version from project config:
- Maven: check `<java.version>` or `<maven.compiler.source>` in `pom.xml`
- Gradle: check `sourceCompatibility` / `javaVersion` in `build.gradle`
- Map version to path: `11` → `/usr/lib/jvm/java-11-openjdk-amd64`, `17` → `/usr/lib/jvm/java-17-openjdk-amd64`, `21` → `/usr/lib/jvm/java-21-openjdk-amd64`
- If unspecified, default to `/usr/lib/jvm/java-21-openjdk-amd64`

**`{{BUILD_CLEAN_COMMAND}}`** — based on build file present:
| Build file | Command |
|---|---|
| `pom.xml` | `mvn clean` |
| `gradlew` + `build.gradle` | `chmod +x ./gradlew && ./gradlew clean` |
| `build.gradle` (no wrapper) | `gradle clean` |

**`{{COVERAGE_REPORT_PATH}}`** — based on build tool:
| Build tool | Path |
|---|---|
| Maven | `target/site/jacoco/jacoco.xml` |
| Gradle | `build/reports/jacoco/test/jacocoTestReport.xml` |

#### Coverage Plugin Setup

**Maven** — ensure jacoco-maven-plugin in `pom.xml` under `<profile id="coverage">`:
```xml
<profile>
    <id>coverage</id>
    <dependencies>
        <dependency>
            <groupId>org.jacoco</groupId>
            <artifactId>jacoco-maven-plugin</artifactId>
            <version>0.8.11</version>
        </dependency>
    </dependencies>
</profile>
```

**Gradle** — ensure jacoco plugin in `build.gradle`:
```groovy
plugins {
    id 'jacoco'
}
jacocoTestReport {
    reports { xml.required = true }
}
```

#### Test Command Pattern

**Maven:**
```bash
mvn verify -P coverage -Dtest=<TestClassname>
```

**Gradle:**
```bash
./gradlew test jacocoTestReport --tests "<package.TestClassname>"
```
"""

OVERALL_WORKFLOW = """
### Step 1: Extract User Requirements
From user input, extract: source file path, expected coverage, max iterations, model, function under test (optional), flakiness check (optional).

### Step 2: Check architect.md
- If `architect.md` doesn't exist, use `/analysis_architect_and_framework` to generate it
- Include architect.md content in `--additional-prompt` argument

### Step 3: Check/Create Test File
- Python: `src/service/file.py` → `tests/service/test_file.py`
- Java: `src/main/java/com/example/Service.java` → `src/test/java/com/example/ServiceTest.java`
- If test file doesn't exist, create as **empty file** (`touch <path>`) — do NOT add placeholder content

### Step 4: Detect Project Type
- **Python**: Look for `pyproject.toml`, `setup.py`, `requirements.txt`, or `.py` files
- **Java**: Look for `pom.xml` (Maven) or `build.gradle` (Gradle)

### Step 5: Install Dependencies
- **Python**: `uv add pytest pytest-asyncio coverage`
- **Java (Maven)**: Ensure jacoco-maven-plugin in pom.xml
- **Java (Gradle)**: Ensure jacoco plugin in build.gradle

### Step 6: Create/Update Gen_UnitTest.sh Script
- Filename is **always** `Gen_UnitTest.sh` — NEVER append source name or any suffix (e.g. `Gen_UnitTest_mcp.sh` is WRONG)
- If NOT exists → create it; if exists → overwrite it — do NOT create a second file
- Copy the script template exactly — do NOT add extra `echo` lines, comments, or any content not in the template
- Make executable: `chmod +x Gen_UnitTest.sh`

### Step 7: Build Keploy Command by Fill Template Placeholders
- Replace every `{{PLACEHOLDER}}` in the template with actual values:                                                                                       
-- Project-appropriate paths and test command
-- Correct coverage format (cobertura for Python, jacoco for Java)
-- For Java: fill `{{JAVA_HOME}}`, `{{BUILD_CLEAN_COMMAND}}`, `{{COVERAGE_REPORT_PATH}}` per project build tool
-- architect.md content in additional-prompt
-- User-specified or default values for all arguments

### Step 8: Execute and Monitor
- Display full command before execution
- Show real-time logs and complete error output

### Step 9: Refactor Generated Tests (REQUIRED)
After Keploy generates tests, ONLY refactor — do NOT add new test cases.

### Step 10: Summary (REQUIRED — Final Step)
After refactoring, create a summary markdown file then **stop** — do NOT add any further tasks or commands.

**Summary file path rule** — strip source root, prepend `summary/`, prefix filename with `summary_`:
- Python: `openhands_cli/acp_impl/utils/mcp.py` → `summary/acp_impl/utils/summary_mcp.md`
- Java: `src/main/java/com/example/Service.java` → `summary/com/example/summary_Service.md`

Run `mkdir -p <dir>` before creating the file.

**File structure:**
```markdown
# Source Code Evaluation: <filename>

## Overview
- Source / Test file, test count, coverage achieved vs expected

## Coverage Breakdown
Per-function coverage status and which test cases cover it.

## Code Quality Assessment
Observed during test generation:
- Testability (DI, side effects, global state)
- Functions that were difficult to test and why
- Edge cases covered (null, empty, boundary, exceptions)
- Functions with low/no coverage and reasons

## Recommendations
Actionable improvements to source code quality and testability.
```

After writing the file, confirm to user: file path, coverage result, test count.

**This is the end of the workflow. Wait for the user's next instruction.**

### Troubleshooting
- **Coverage not generated**: Verify test command, check coverage package installed, run tests manually
- **Test file not found**: Create empty test file before running keploy gen, follow naming conventions
- **Low coverage after max iterations**: Review tests manually, increase max iterations, add guidance via `--additional-prompt`
- **Java**: Always run `mvn clean` before keploy gen
- Replace all `{{PLACEHOLDER}}` values with actual values; escape double quotes and newlines in ADDITIONAL_PROMPT
"""
