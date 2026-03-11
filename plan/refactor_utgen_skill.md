# Plan: Refactor KEPLOY_GEN_UNIT_TEST Skill

## Mục tiêu

Tối ưu và tách `KEPLOY_GEN_UNIT_TEST` trong `openhands_cli/instructions/dev_skills.py`:
- Giảm bớt nội dung trùng lặp/dư thừa trong skill content
- Tách bash script templates thành file riêng để dễ bảo trì
- Đảm bảo tương thích hoàn toàn với Nuitka build

---

## Phân tích vấn đề hiện tại

### Các phần trùng lặp trong skill hiện tại:

| Section | Trùng với | Hành động |
|---|---|---|
| `## Default Values` | Đã có trong `## Keploy Gen Command Arguments` | **Xóa** |
| `### 4. Complete Python Example` | Trùng nội dung với Script Template Python | **Xóa** |
| `### 6. Complete Java Example` | Trùng nội dung với Script Template Java | **Xóa** |
| `## Python Project Setup` & `## Java Project Setup` | Cấu trúc giống nhau, có thể gộp | **Gộp** |

### Kích thước hiện tại vs mục tiêu:
- `dev_skills.py` (phần KEPLOY skill): ~420 dòng → mục tiêu ~180 dòng
- `keploy_templates.py` (tạo mới): ~150 dòng

---

## Quyết định kỹ thuật: Python module vs Bash file

### Tại sao dùng Python module (`.py`) thay vì bash file (`.sh`)?

**Nuitka build command hiện tại:**
```bash
--include-package=openhands_cli
```

- Python `.py` files → được Nuitka compile thành machine code → **nội dung được bảo vệ**
- Bash `.sh` files (non-Python data) → cần thêm `--include-data-files` hoặc `--include-data-dir` vào build script → phức tạp hơn, và nội dung **không được mã hóa** trong binary
- Python string constants được compile cùng với `dev_skills.py` → cùng mức độ bảo vệ

**Kết luận:** Dùng Python module với string constants là lựa chọn tối ưu cho Nuitka compatibility.

---

## Cấu trúc file sau khi refactor

```
openhands_cli/instructions/
├── __init__.py              (không thay đổi)
├── dev_note.txt             (không thay đổi)
├── dev_skills.py            (sửa: import từ keploy_templates, rút gọn content)
└── keploy_templates.py      (TẠO MỚI: chứa bash script templates)
```

---

## Chi tiết thay đổi

### 1. TẠO MỚI: `openhands_cli/instructions/keploy_templates.py`

File chứa bash script templates dưới dạng Python string constants:

```python
"""
Keploy Gen bash script templates for Python and Java projects.
These are imported by dev_skills.py to compose the skill content.
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

source .venv/bin/activate
export API_KEY="dummy"

KEPLOY_CMD="keploy gen"
KEPLOY_CMD+=" --sourceFilePath=\\"$SOURCE_FILE_PATH\\""
KEPLOY_CMD+=" --testFilePath=\\"$TEST_FILE_PATH\\""
KEPLOY_CMD+=" --coverageReportPath=\\"$COVERAGE_REPORT_PATH\\""
KEPLOY_CMD+=" --coverageFormat=\\"$COVERAGE_FORMAT\\""
KEPLOY_CMD+=" --testCommand=\\"$TEST_COMMAND\\""
KEPLOY_CMD+=" --expected-coverage=$EXPECTED_COVERAGE"
KEPLOY_CMD+=" --maxIterations=$MAX_ITERATIONS"
[ -n "$LLM_BASE_URL" ] && KEPLOY_CMD+=" --llmBaseUrl=\\"$LLM_BASE_URL\\""
KEPLOY_CMD+=" --model=\\"$MODEL\\""
[ -n "$LLM_API_VERSION" ] && KEPLOY_CMD+=" --llm-api-version=\\"$LLM_API_VERSION\\""
[ -n "$ADDITIONAL_PROMPT" ] && KEPLOY_CMD+=" --additional-prompt=\\"$ADDITIONAL_PROMPT\\""
[ -n "$FUNCTION_UNDER_TEST" ] && KEPLOY_CMD+=" --function-under-test=\\"$FUNCTION_UNDER_TEST\\""
[ "$FLAKINESS" = "true" ] && KEPLOY_CMD+=" --flakiness"
[ -n "$SERVER_URL" ] && KEPLOY_CMD+=" --server-url=\\"$SERVER_URL\\""

echo "Command: $KEPLOY_CMD"
eval $KEPLOY_CMD
EXIT_CODE=$?
[ $EXIT_CODE -ne 0 ] && echo "ERROR: Keploy gen failed with exit code $EXIT_CODE" && exit $EXIT_CODE
echo "SUCCESS: Keploy gen completed successfully"
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

export API_KEY="dummy"
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
export PATH=/usr/bin:/usr/local/bin:$PATH

echo "Running mvn clean..."
mvn clean

KEPLOY_CMD="keploy gen"
KEPLOY_CMD+=" --sourceFilePath=\\"$SOURCE_FILE_PATH\\""
KEPLOY_CMD+=" --testFilePath=\\"$TEST_FILE_PATH\\""
KEPLOY_CMD+=" --coverageReportPath=\\"$COVERAGE_REPORT_PATH\\""
KEPLOY_CMD+=" --coverageFormat=\\"$COVERAGE_FORMAT\\""
KEPLOY_CMD+=" --testCommand=\\"$TEST_COMMAND\\""
KEPLOY_CMD+=" --expected-coverage=$EXPECTED_COVERAGE"
KEPLOY_CMD+=" --maxIterations=$MAX_ITERATIONS"
[ -n "$LLM_BASE_URL" ] && KEPLOY_CMD+=" --llmBaseUrl=\\"$LLM_BASE_URL\\""
KEPLOY_CMD+=" --model=\\"$MODEL\\""
[ -n "$LLM_API_VERSION" ] && KEPLOY_CMD+=" --llm-api-version=\\"$LLM_API_VERSION\\""
[ -n "$ADDITIONAL_PROMPT" ] && KEPLOY_CMD+=" --additional-prompt=\\"$ADDITIONAL_PROMPT\\""
[ -n "$FUNCTION_UNDER_TEST" ] && KEPLOY_CMD+=" --function-under-test=\\"$FUNCTION_UNDER_TEST\\""
[ "$FLAKINESS" = "true" ] && KEPLOY_CMD+=" --flakiness"
[ -n "$SERVER_URL" ] && KEPLOY_CMD+=" --server-url=\\"$SERVER_URL\\""

echo "Command: $KEPLOY_CMD"
eval $KEPLOY_CMD
EXIT_CODE=$?
[ $EXIT_CODE -ne 0 ] && echo "ERROR: Keploy gen failed with exit code $EXIT_CODE" && exit $EXIT_CODE
echo "SUCCESS: Keploy gen completed successfully"
"""
```

---

### 2. SỬA: `openhands_cli/instructions/dev_skills.py`

#### Thêm import ở đầu file (sau các import hiện có):
```python
from openhands_cli.instructions.keploy_templates import (
    PYTHON_SCRIPT_TEMPLATE,
    JAVA_SCRIPT_TEMPLATE,
)
```

#### Thay thế `KEPLOY_GEN_UNIT_TEST` Skill:

Thay `content="""..."""` thành `content=f"""..."""` với cấu trúc mới như sau:

```
# Keploy Unit Test Generation for Ubuntu

## Keploy Gen Command Arguments
(giữ nguyên phần này)

## Script Templates

### Python Project - Save as `run_keploy_gen_python.sh`:
{PYTHON_SCRIPT_TEMPLATE}

### Java Project - Save as `run_keploy_gen_java.sh`:
{JAVA_SCRIPT_TEMPLATE}

## Project Setup

### Python
- Install deps: `source .venv/bin/activate && uv add pytest pytest-asyncio coverage`
- Coverage config: `--coverageReportPath="coverage.xml" --coverageFormat="cobertura"`
- Test command pattern: `uv run coverage run --include=<src> -m pytest <test> && uv run coverage xml`

### Java (Maven)
- Env: `export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64`
- Coverage config: `--coverageReportPath="target/site/jacoco/jacoco.xml" --coverageFormat="jacoco"`
- Test command pattern: `mvn verify -P coverage -Dtest=<TestClassname>`
- Ensure jacoco-maven-plugin in pom.xml under `<profile id="coverage">`

## Workflow Steps
(giữ nguyên 7 bước)

## Error Handling
(giữ nguyên)

## Important Notes
(giữ nguyên, bỏ dòng trùng với script template notes)
```

---

## Thứ tự thực hiện

1. **Tạo** `openhands_cli/instructions/keploy_templates.py` với 2 string constants
2. **Sửa** `openhands_cli/instructions/dev_skills.py`:
   - Thêm import
   - Thay thế skill content (xóa phần dư, dùng f-string với template references)
3. **Verify** import hoạt động đúng
4. **Chạy tests** để đảm bảo không có regression

---

## Verification

```bash
# 1. Kiểm tra import và skill content được compose đúng
python -c "
from openhands_cli.instructions import get_dev_skills
skills = get_dev_skills()
k = next(s for s in skills if s.name == 'keploy_gen_unit_test')
print(f'Content length: {len(k.content)} chars')
print(f'Has bash shebang: {\"#!/bin/bash\" in k.content}')
print(f'Has Python template: {\"run_keploy_gen_python\" in k.content}')
print(f'Has Java template: {\"run_keploy_gen_java\" in k.content}')
"

# 2. Chạy test suite
uv run pytest tests/ -x -q

# 3. Kiểm tra get_dev_skills() trả về đúng 4 skills
python -c "
from openhands_cli.instructions import get_dev_skills
skills = get_dev_skills()
print([s.name for s in skills])
assert len(skills) == 4
"
```
