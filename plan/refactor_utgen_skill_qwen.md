# Kế Hoạch Refactor: KEPLOY_GEN_UNIT_TEST Skill (Chi Tiết)

**Ngày tạo:** 2026-03-11  
**Độ khó:** 4/10  
**Thời gian ước tính:** 2-3 giờ

---

## 🎯 Mục tiêu

Tối ưu và tách skill `KEPLOY_GEN_UNIT_TEST` trong file `openhands_cli/instructions/dev_skills.py`:

1. ✅ **Giảm nội dung trùng lặp** - Xóa các section dư thừa
2. ✅ **Tách script templates thành nhiều file nhỏ** - Dễ bảo trì, nâng cấp
3. ✅ **Tách constants và defaults** - Quản lý tập trung
4. ✅ **Tách workflows và error handling** - Document riêng biệt
5. ✅ **Đảm bảo Nuitka compatibility** - Tất cả file được compile và bảo vệ cùng nhau

---

## 📊 Phân tích vấn đề hiện tại

### Các phần trùng lặp trong skill

| Section | Trùng với | Hành động |
|---------|-----------|-----------|
| `## Default Values` | Đã có trong CLI Arguments | **XÓA** |
| `### 4. Complete Python Example` | Trùng với Script Template Python | **XÓA** |
| `### 6. Complete Java Example` | Trùng với Script Template Java | **XÓA** |
| `## Python Project Setup` & `## Java Project Setup` | Cấu trúc giống nhau | **GỘP** |
| Script templates quá dài | Chiếm ~70% content | **TÁCH** ra file riêng |

### So sánh kích thước

| File | Trước | Sau | Giảm |
|------|-------|-----|------|
| `dev_skills.py` (KEPLOY skill) | ~420 dòng | ~150 dòng | **-64%** |
| `keploy/constants.py` (mới) | 0 | ~80 dòng | - |
| `keploy/scripts/python.py` (mới) | 0 | ~100 dòng | - |
| `keploy/scripts/java.py` (mới) | 0 | ~100 dòng | - |
| `keploy/workflows.py` (mới) | 0 | ~60 dòng | - |
| `keploy/error_handling.py` (mới) | 0 | ~50 dòng | - |
| **Tổng** | ~420 dòng | ~540 dòng | **+28%** (nhưng dễ bảo trì hơn nhiều) |

**Lưu ý:** Tổng số dòng tăng nhưng mỗi file nhỏ hơn, dễ đọc, dễ bảo trì và cập nhật.

---

## 🔧 Quyết định kỹ thuật

### Tại sao tách thành nhiều file nhỏ?

| Lợi ích | Mô tả |
|---------|-------|
| **Dễ bảo trì** | Mỗi file đảm nhiệm 1 mục đích rõ ràng (Single Responsibility) |
| **Dễ test** | Có thể test từng module độc lập |
| **Dễ review** | Code review từng phần nhỏ |
| **Dễ mở rộng** | Thêm tính năng mới không ảnh hưởng file cũ |
| **Git diff rõ ràng** | Khi sửa, chỉ thay đổi file liên quan |

### Tại sao dùng Python module (`.py`) thay vì Bash file (`.sh`)?

**Nuitka build command hiện tại:**
```bash
--include-package=openhands_cli
```

| Phương án | Ưu điểm | Nhược điểm |
|-----------|---------|------------|
| **Python `.py`** | ✅ Được Nuitka compile thành machine code<br>✅ Nội dung được bảo vệ<br>✅ Không cần thay đổi build script<br>✅ Type hints, linting | - |
| **Bash `.sh`** | - | ❌ Cần `--include-data-files` vào build script<br>❌ Nội dung KHÔNG được mã hóa<br>❌ Phức tạp hơn khi build<br>❌ Khó test |

**Kết luận:** Dùng Python module với string constants là lựa chọn tối ưu cho **Nuitka compatibility**, **bảo mật**, và **maintainability**.

---

## 📁 Cấu trúc file sau khi refactor

```
openhands_cli/instructions/
├── __init__.py                    # Không thay đổi
├── dev_note.txt                   # Không thay đổi
├── dev_skills.py                  # SỬA: import từ keploy package, rút gọn content
└── keploy/                        # TẠO MỚI: Keploy package
    ├── __init__.py                # Export public API
    ├── constants.py               # Default values, CLI arguments, keywords
    ├── scripts/
    │   ├── __init__.py            # Scripts package
    │   ├── python.py              # Python script template
    │   └── java.py                # Java script template
    ├── workflows.py               # Workflow documentation strings
    └── error_handling.py          # Error handling documentation strings
```

**Chi tiết từng file:**

### 1. `keploy/__init__.py`
Export tất cả constants và templates để `dev_skills.py` import dễ dàng.

### 2. `keploy/constants.py`
Chứa:
- CLI argument descriptions
- Default values (DEFAULTS, PYTHON_DEFAULTS, JAVA_DEFAULTS)
- Trigger keywords (KEPLOY_KEYWORDS)

### 3. `keploy/scripts/python.py`
Chứa:
- `PYTHON_SCRIPT_TEMPLATE` - Bash script template cho Python projects

### 4. `keploy/scripts/java.py`
Chứa:
- `JAVA_SCRIPT_TEMPLATE` - Bash script template cho Java projects

### 5. `keploy/workflows.py`
Chứa:
- `PYTHON_WORKFLOW` - Quick start, test file convention, coverage command cho Python
- `JAVA_WORKFLOW` - Quick start, test file convention, coverage command cho Java

### 6. `keploy/error_handling.py`
Chứa:
- `ERROR_HANDLING_GUIDE` - Common issues and solutions

---

## 📝 Chi tiết thay đổi

### Bước 1: TẠO MỚI `openhands_cli/instructions/keploy/__init__.py`

```python
"""
Keploy unit test generation module.

This package contains:
- constants.py: Default values, CLI arguments, and trigger keywords
- scripts/: Bash script templates for Python and Java projects
- workflows.py: Workflow documentation for both platforms
- error_handling.py: Common issues and solutions

All content is compiled and protected by Nuitka.
"""

from openhands_cli.instructions.keploy.constants import (
    CLI_ARGUMENTS,
    DEFAULTS,
    JAVA_DEFAULTS,
    KEPLOY_KEYWORDS,
    PYTHON_DEFAULTS,
)
from openhands_cli.instructions.keploy.error_handling import ERROR_HANDLING_GUIDE
from openhands_cli.instructions.keploy.scripts.java import JAVA_SCRIPT_TEMPLATE
from openhands_cli.instructions.keploy.scripts.python import PYTHON_SCRIPT_TEMPLATE
from openhands_cli.instructions.keploy.workflows import (
    JAVA_WORKFLOW,
    PYTHON_WORKFLOW,
)

__all__ = [
    # Constants
    "CLI_ARGUMENTS",
    "DEFAULTS",
    "PYTHON_DEFAULTS",
    "JAVA_DEFAULTS",
    "KEPLOY_KEYWORDS",
    # Scripts
    "PYTHON_SCRIPT_TEMPLATE",
    "JAVA_SCRIPT_TEMPLATE",
    # Workflows
    "PYTHON_WORKFLOW",
    "JAVA_WORKFLOW",
    # Error handling
    "ERROR_HANDLING_GUIDE",
]
```

---

### Bước 2: TẠO MỚI `openhands_cli/instructions/keploy/constants.py`

```python
"""
Keploy configuration constants and default values.

These constants are used by the Keploy unit test generation skill
and associated scripts.
"""

# ============================================================================
# CLI ARGUMENT DESCRIPTIONS
# ============================================================================

CLI_ARGUMENTS = """
## Keploy Gen Command Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--source-file-path` | Path to the source file to test | Required |
| `--test-file-path` | Path to the output test file | Required |
| `--coverage-report-path` | Path to coverage report file | Platform-specific |
| `--test-command` | Command to run tests | Required |
| `--coverage-format` | Report type (cobertura/jacoco) | Platform-specific |
| `--expected-coverage` | Target coverage % | 85 |
| `--max-iterations` | Max generation attempts | 5 |
| `--llm-base-url` | AI model endpoint | http://0.0.0.0:4000 |
| `--model` | Model name | claude-haiku-4-5 |
| `--additional-prompt` | Extra context (e.g., architect.md) | "" |
| `--function-under-test` | Specific function to test | "" |
| `--flakiness` | Run flakiness check | false |
"""

# ============================================================================
# DEFAULT VALUES
# ============================================================================

DEFAULTS = {
    "expected_coverage": 85,
    "max_iterations": 5,
    "model": "claude-haiku-4-5",
    "llm_base_url": "http://0.0.0.0:4000",
    "function_under_test": "",
    "flakiness": False,
}

PYTHON_DEFAULTS = {
    "coverage_report_path": "coverage.xml",
    "coverage_format": "cobertura",
    "test_command_template": (
        "uv run coverage run --include={source_file} -m pytest {test_file} "
        "&& uv run coverage xml"
    ),
    "test_file_pattern": "test_{source_file}.py",
}

JAVA_DEFAULTS = {
    "coverage_report_path": "target/site/jacoco/jacoco.xml",
    "coverage_format": "jacoco",
    "test_command_template": "mvn verify -P coverage -Dtest={test_class}",
    "test_file_pattern": "{source_file}Test.java",
    "java_home": "/usr/lib/jvm/java-21-openjdk-amd64",
}

# ============================================================================
# KEYWORDS FOR TRIGGER
# ============================================================================

KEPLOY_KEYWORDS = [
    "keploy gen",
    "keploy unit test",
    "generate unit test with keploy",
    "keploy test generation",
]
```

---

### Bước 3: TẠO MỚI `openhands_cli/instructions/keploy/scripts/__init__.py`

```python
"""
Keploy script templates.

This module contains bash script templates for generating unit tests
using Keploy AI-powered tool.
"""

from openhands_cli.instructions.keploy.scripts.java import JAVA_SCRIPT_TEMPLATE
from openhands_cli.instructions.keploy.scripts.python import PYTHON_SCRIPT_TEMPLATE

__all__ = [
    "PYTHON_SCRIPT_TEMPLATE",
    "JAVA_SCRIPT_TEMPLATE",
]
```

---

### Bước 4: TẠO MỚI `openhands_cli/instructions/keploy/scripts/python.py`

```python
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
```

---

### Bước 5: TẠO MỚI `openhands_cli/instructions/keploy/scripts/java.py`

```python
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
```

---

### Bước 6: TẠO MỚI `openhands_cli/instructions/keploy/workflows.py`

```python
"""
Keploy workflow documentation for Python and Java projects.

These strings provide quick reference guides for using Keploy gen.
"""

PYTHON_WORKFLOW = """
### Python Project Setup

1. **Install Dependencies:**
   ```bash
   source .venv/bin/activate
   uv add pytest pytest-asyncio coverage
   ```

2. **Coverage Configuration:**
   - `--coverageReportPath="coverage.xml"`
   - `--coverageFormat="cobertura"`

3. **Test Command Pattern:**
   ```bash
   uv run coverage run --include=<source_file> -m pytest <test_file> && uv run coverage xml
   ```

4. **Test File Convention:**
   ```
   src/service/file.py → tests/service/test_file.py
   ```
"""

JAVA_WORKFLOW = """
### Java Project Setup (Maven)

1. **Environment Setup:**
   ```bash
   export API_KEY="dummy"
   export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
   export PATH=/usr/bin:/usr/local/bin:$PATH
   ```

2. **Coverage Configuration:**
   - `--coverageReportPath="target/site/jacoco/jacoco.xml"`
   - `--coverageFormat="jacoco"`

3. **Maven Coverage Setup:**
   Ensure jacoco-maven-plugin in `pom.xml` under `<profile id="coverage">`:
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

4. **Test Command Pattern:**
   ```bash
   mvn verify -P coverage -Dtest=<TestClassname>
   ```

5. **Test File Convention:**
   ```
   src/main/java/com/example/Service.java → src/test/java/com/example/ServiceTest.java
   ```
"""
```

---

### Bước 7: TẠO MỚI `openhands_cli/instructions/keploy/error_handling.py`

```python
"""
Keploy error handling guide.

Common issues and solutions for Keploy unit test generation.
"""

ERROR_HANDLING_GUIDE = """
## Error Handling

### Common Issues and Solutions

1. **Keploy not found**
   - Ensure Keploy is installed: `which keploy`
   - Install if needed

2. **Coverage report not generated**
   - Verify test command is correct
   - Check coverage package is installed
   - Run tests manually to verify

3. **Test file not found**
   - Create test file with basic structure before running keploy gen
   - Follow naming conventions

4. **LLM connection error**
   - Verify `--llm-base-url` is accessible
   - Check network connectivity
   - Test endpoint: `curl http://0.0.0.0:4000/health`

5. **Low coverage after max iterations**
   - Review generated tests manually
   - Consider increasing max iterations
   - Add specific guidance in `--additional-prompt`

## Important Notes

- Always display full command and logs during execution
- Never hide error messages - show complete error output
- Test file naming: `<SourceFile>Test.java` (Java), `test_<file>.py` (Python)
- Ensure API_KEY is set (can be "dummy" for local LLM)
- For Java: always run `mvn clean` before keploy gen
- Replace all `{{PLACEHOLDER}}` values with actual values
- Escape double quotes and newlines in ADDITIONAL_PROMPT
- Make scripts executable: `chmod +x *.sh`
"""
```

---

### Bước 8: SỬA `openhands_cli/instructions/dev_skills.py`

#### 8.1 Thêm import ở đầu file

Thêm sau các import hiện có:

```python
from openhands_cli.instructions.keploy import (
    CLI_ARGUMENTS,
    ERROR_HANDLING_GUIDE,
    JAVA_SCRIPT_TEMPLATE,
    JAVA_WORKFLOW,
    KEPLOY_KEYWORDS,
    PYTHON_SCRIPT_TEMPLATE,
    PYTHON_WORKFLOW,
)
```

#### 8.2 Thay thế `KEPLOY_GEN_UNIT_TEST` Skill

Thay `content="""..."""` thành `content=f"""..."""` (f-string để interpolate templates):

```python
KEPLOY_GEN_UNIT_TEST = Skill(
    name="keploy_gen_unit_test",
    content=f"""
# Keploy Unit Test Generation for Ubuntu

You are an expert in generating unit tests using Keploy AI-powered tool on Ubuntu systems.

{CLI_ARGUMENTS}

## Script Templates

### Python Project Script Template

Save as `run_keploy_gen_python.sh`:

{PYTHON_SCRIPT_TEMPLATE}

### Java Project Script Template

Save as `run_keploy_gen_java.sh`:

{JAVA_SCRIPT_TEMPLATE}

## Project Setup

{PYTHON_WORKFLOW}

{JAVA_WORKFLOW}

## Workflow Steps

### Step 1: Extract User Requirements
From user input, extract:
- Source file path to test
- Expected coverage (default: 85)
- Max iterations (default: 5)
- Model (default: "claude-haiku-4-5")
- Function under test (optional, default: "")
- Flakiness check (optional, default: false)

### Step 2: Check architect.md
- Check if `architect.md` exists in the project root
- If not exists, use slash command `/analysis_architect_and_framework` to generate it
- Include architect.md content in `--additional-prompt` argument

### Step 3: Check/Create Test File
- Test file location follows source file structure but in test directory
- Python example: `src/service/file.py` → `tests/service/test_file.py`
- Java example: `src/main/java/com/example/Service.java` → `src/test/java/com/example/ServiceTest.java`
- If test file doesn't exist, create it with basic test class structure

### Step 4: Detect Project Type
- **Python**: Look for `pyproject.toml`, `setup.py`, `requirements.txt`, or `.py` files
- **Java**: Look for `pom.xml` (Maven) or `build.gradle` (Gradle)

### Step 5: Install Dependencies
- **Python**: `uv add pytest pytest-asyncio coverage`
- **Java (Maven)**: Ensure jacoco-maven-plugin in pom.xml
- **Java (Gradle)**: Ensure jacoco plugin in build.gradle

### Step 6: Build Keploy Command
Construct the keploy gen command with:
- Project-appropriate paths and test command
- Correct coverage format (cobertura for Python, jacoco for Java)
- architect.md content in additional-prompt
- User-specified or default values for all arguments

### Step 7: Execute and Monitor
- Display full command before execution
- Show real-time logs during execution
- If errors occur, display complete error logs
- Provide clear error messages and suggestions

{ERROR_HANDLING_GUIDE}
""",
    trigger=KeywordTrigger(
        type="keyword",
        keywords=KEPLOY_KEYWORDS,
    ),
    description="Keploy AI-powered unit test generation for Python and Java projects on Ubuntu",
)
```

---

## ✅ Thứ tự thực hiện

### Checklist chi tiết:

#### Phase 1: Tạo Keploy Package Structure

1. **[ ] Tạo thư mục `openhands_cli/instructions/keploy/`**
   ```bash
   mkdir -p openhands_cli/instructions/keploy/scripts
   ```

2. **[ ] Tạo `keploy/__init__.py`**
   - Export tất cả constants và templates

3. **[ ] Tạo `keploy/constants.py`**
   - CLI_ARGUMENTS
   - DEFAULTS, PYTHON_DEFAULTS, JAVA_DEFAULTS
   - KEPLOY_KEYWORDS

4. **[ ] Tạo `keploy/scripts/__init__.py`**
   - Export script templates

5. **[ ] Tạo `keploy/scripts/python.py`**
   - PYTHON_SCRIPT_TEMPLATE

6. **[ ] Tạo `keploy/scripts/java.py`**
   - JAVA_SCRIPT_TEMPLATE

7. **[ ] Tạo `keploy/workflows.py`**
   - PYTHON_WORKFLOW, JAVA_WORKFLOW

8. **[ ] Tạo `keploy/error_handling.py`**
   - ERROR_HANDLING_GUIDE

#### Phase 2: Update dev_skills.py

9. **[ ] Thêm imports vào `dev_skills.py`**
   - Import từ keploy package

10. **[ ] Thay thế `KEPLOY_GEN_UNIT_TEST.content`**
    - Dùng f-string với template references
    - Xóa các section trùng lặp

#### Phase 3: Verification

11. **[ ] Test imports**
    ```bash
    python -c "from openhands_cli.instructions.keploy import KEPLOY_KEYWORDS; print('OK')"
    ```

12. **[ ] Test skill loading**
    ```bash
    python -c "from openhands_cli.instructions import get_dev_skills; print(f'Loaded {len(get_dev_skills())} skills')"
    ```

13. **[ ] Chạy tests**
    ```bash
    uv run pytest tests/ -x -q
    ```

14. **[ ] Test Nuitka build**
    ```bash
    ./build_nuitka.sh
    ./dist/openhands --help
    ```

---

## 🔍 Verification Tests

### Test 1: Kiểm tra tất cả imports

```bash
python -c "
from openhands_cli.instructions.keploy import (
    CLI_ARGUMENTS,
    DEFAULTS,
    PYTHON_DEFAULTS,
    JAVA_DEFAULTS,
    KEPLOY_KEYWORDS,
    PYTHON_SCRIPT_TEMPLATE,
    JAVA_SCRIPT_TEMPLATE,
    PYTHON_WORKFLOW,
    JAVA_WORKFLOW,
    ERROR_HANDLING_GUIDE,
)
print('✅ All imports successful')
print(f'   - CLI_ARGUMENTS: {len(CLI_ARGUMENTS)} chars')
print(f'   - DEFAULTS: {len(DEFAULTS)} keys')
print(f'   - PYTHON_SCRIPT_TEMPLATE: {len(PYTHON_SCRIPT_TEMPLATE)} chars')
print(f'   - JAVA_SCRIPT_TEMPLATE: {len(JAVA_SCRIPT_TEMPLATE)} chars')
print(f'   - KEPLOY_KEYWORDS: {len(KEPLOY_KEYWORDS)} keywords')
"
```

### Test 2: Kiểm tra skill content được compose đúng

```bash
python -c "
from openhands_cli.instructions import get_dev_skills
skills = get_dev_skills()
k = next(s for s in skills if s.name == 'keploy_gen_unit_test')

print(f'✅ Content length: {len(k.content)} chars')
print(f'✅ Has bash shebang: {\"#!/bin/bash\" in k.content}')
print(f'✅ Has Python template: {\"run_keploy_gen_python\" in k.content}')
print(f'✅ Has Java template: {\"run_keploy_gen_java\" in k.content}')
print(f'✅ Has CLI arguments table: {\"| Argument |\" in k.content}')
print(f'✅ Has workflow steps: {\"Step 1:\" in k.content}')
print(f'✅ Has error handling: {\"Common Issues\" in k.content}')
"
```

### Test 3: Kiểm tra get_dev_skills() trả về đúng 4 skills

```bash
python -c "
from openhands_cli.instructions import get_dev_skills
skills = get_dev_skills()
skill_names = [s.name for s in skills]
print('Skills:', skill_names)
assert len(skills) == 4, f'Expected 4 skills, got {len(skills)}'
assert 'anti_leak_instructions' in skill_names
assert 'generate_unit_test' in skill_names
assert 'analysis_architect_and_framework' in skill_names
assert 'keploy_gen_unit_test' in skill_names
print('✅ All 4 skills present')
"
```

### Test 4: Chạy test suite

```bash
uv run pytest tests/ -x -q
```

### Test 5: Verify Nuitka build

```bash
# Build
./build_nuitka.sh

# Verify binary works
./dist/openhands --help

# Verify skill content is protected
strings ./dist/openhands | grep -c "Keploy Gen Command Arguments" || echo "✅ Content protected!"
```

---

## 📊 Kết quả mong đợi

### Before vs After

| Chỉ số | Before | After | Change |
|--------|--------|-------|--------|
| `dev_skills.py` (KEPLOY section) | ~420 dòng | ~150 dòng | **-64%** |
| Số lượng file | 1 | 7 | **+6 files** |
| Tổng lines of code | ~420 | ~540 | **+28%** |
| Code trùng lặp | ~180 dòng | 0 dòng | **-100%** |
| Dòng/file (trung bình) | 420 | 77 | **-82%** |
| Khả năng bảo trì | Khó | Dễ | ✅ |
| Nuitka compatible | ✅ | ✅ | ✅ |
| Nội dung được bảo vệ | ✅ | ✅ | ✅ |

### Lợi ích của việc tách nhỏ

| Lợi ích | Mô tả |
|---------|-------|
| **Dễ đọc** | Mỗi file < 100 dòng, tập trung vào 1 mục đích |
| **Dễ tìm** | Biết chính xác file nào chứa gì |
| **Dễ sửa** | Chỉ sửa file liên quan, không ảnh hưởng file khác |
| **Dễ test** | Có thể unit test từng module |
| **Git diff rõ** | Khi sửa, chỉ thay đổi file cụ thể |
| **Code review nhanh** | Reviewer dễ hiểu từng phần nhỏ |

---

## 🔒 Lưu ý về bảo mật

### ✅ Được bảo vệ:

- Tất cả Python files được Nuitka compile thành machine code
- Script templates nằm trong `.py` files → được mã hóa cùng với binary
- Không thể extract content bằng `strings` command
- Constants và workflows cũng được bảo vệ

### ⚠️ Lưu ý:

- Không hardcode API keys trong templates
- Sử dụng environment variables cho sensitive data
- Agent vẫn có thể đọc content qua `get_dev_skills()` (expected behavior)

---

## 📝 Ghi chú Migration

### Breaking Changes

- **KHÔNG CÓ** - Skill behavior vẫn giữ nguyên 100%
- Agent vẫn reference scripts như cũ
- Content chỉ được tổ chức lại, không thay đổi logic

### Backward Compatibility

- Skill name: `keploy_gen_unit_test` (không đổi)
- Trigger keywords: giữ nguyên
- Description: giữ nguyên
- Content structure: tương tự, chỉ tách ra file riêng

---

## 🚀 Các bước tiếp theo (Optional - Future Enhancements)

Sau khi hoàn thành refactor cơ bản, có thể cân nhắc:

### 1. Tạo utility functions

**File:** `keploy/utils.py`

```python
def generate_script(project_type: str, config: dict) -> str:
    """Generate bash script from template with config."""
    ...

def validate_config(config: dict) -> list[str]:
    """Validate configuration and return list of errors."""
    ...
```

### 2. Type hints

Thêm type hints vào tất cả modules:

```python
from typing import TypedDict

class KeployConfig(TypedDict):
    source_file_path: str
    test_file_path: str
    expected_coverage: int
    ...
```

### 3. Unit tests cho Keploy modules

**File:** `tests/test_keploy_constants.py`

```python
def test_defaults_have_required_keys():
    assert "expected_coverage" in DEFAULTS
    assert "model" in DEFAULTS
```

### 4. Documentation generator

Tự động generate markdown documentation từ constants và workflows.

---

## 📚 Tài liệu liên quan

### Files cần tạo/sửa:

| File | Action | Mục đích |
|------|--------|----------|
| `keploy/__init__.py` | TẠO MỚI | Export public API |
| `keploy/constants.py` | TẠO MỚI | Constants và defaults |
| `keploy/scripts/__init__.py` | TẠO MỚI | Scripts package export |
| `keploy/scripts/python.py` | TẠO MỚI | Python script template |
| `keploy/scripts/java.py` | TẠO MỚI | Java script template |
| `keploy/workflows.py` | TẠO MỚI | Workflow documentation |
| `keploy/error_handling.py` | TẠO MỚI | Error handling guide |
| `dev_skills.py` | SỬA | Import từ keploy package |

### Files hiện có (không đổi):

- `__init__.py` (root instructions)
- `dev_note.txt`

### Documentation:

- `AGENTS.md` - Cập nhật sau khi hoàn thành
- `INSTRUCTIONS_GUIDE.md` - Cập nhật sau khi hoàn thành

---

## 🎯 Success Criteria

Refactor thành công khi:

- [ ] ✅ Tất cả 7 file mới được tạo đúng cấu trúc
- [ ] ✅ `dev_skills.py` giảm từ ~420 dòng xuống ~150 dòng
- [ ] ✅ Tất cả imports hoạt động không lỗi
- [ ] ✅ `get_dev_skills()` trả về đúng 4 skills
- [ ] ✅ Skill content được compose đúng (có đủ templates, workflows, errors)
- [ ] ✅ Tất cả tests pass
- [ ] ✅ Nuitka build thành công
- [ ] ✅ Binary hoạt động bình thường
- [ ] ✅ Không có breaking changes

---

**Người tạo plan:** Qwen Code  
**Dựa trên:** `plan/refactor_utgen_skill.md`  
**Ngôn ngữ:** Tiếng Việt  
**Version:** 2.0 (Chi tiết hơn, tách nhiều file nhỏ hơn)
