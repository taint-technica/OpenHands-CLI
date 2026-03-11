"""
Keploy workflow documentation for Python and Java projects.

These strings provide quick reference guides for using Keploy gen.
"""

PYTHON_WORKFLOW = """
### Python Project Setup

1. **Check and install uv:**
    ```bash
    if ! command -v uv &> /dev/null; then
        echo "uv is NOT installed. Installing..."
        curl -LsSf https://astral.sh/uv/install.sh | sh

        [ -f "$HOME/.local/bin/env" ] && source "$HOME/.local/bin/env"
        [ -f "$HOME/.cargo/env" ] && source "$HOME/.cargo/env"

        if command -v uv &> /dev/null; then
            echo "SUCCESS: uv installed"
        else
            echo "ERROR: Installation failed"
            exit 1
        fi
    else
        echo "uv is already installed: $(uv --version)"
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

5. **Configuration other augments**
   
6. **Create/Update Gen_UnitTest.sh:**
    ```bash
    if [ -f "Gen_UnitTest.sh" ]; then
       echo "Updating existing Gen_UnitTest.sh..."
    else
        echo "Creating new Gen_UnitTest.sh..."
    fi

    cat > Gen_UnitTest.sh << 'EOF'
    #!/bin/bash
        //Keploy gen command here
    EOF

    chmod +x Gen_UnitTest.sh
    ```

7. **Excute keploy gen command**
"""

JAVA_WORKFLOW = """
### Java Project Setup (Maven)

1. **Environment Setup:**
    ```bash
    export API_KEY="dummy"
    //Auto-detect JAVA_HOME or set manually
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

5. **Configuration other augments**
   
6. **Create/Update Gen_UnitTest.sh:**
    ```bash
    if [ -f "Gen_UnitTest.sh" ]; then
       echo "Updating existing Gen_UnitTest.sh..."
    else
        echo "Creating new Gen_UnitTest.sh..."
    fi

    cat > Gen_UnitTest.sh << 'EOF'
    #!/bin/bash
        //Keploy gen command here
    EOF

    chmod +x Gen_UnitTest.sh
    ```

7. **Excute keploy gen command**
"""

OVERALL_WORKFLOW = """
### Step 1: Extract User Requirements
From user input, extract:
- Source file path to test
- Expected coverage
- Max iterations
- Model
- Function under test (optional)
- Flakiness check (optional)

### Step 2: Check architect.md
- Check if `architect.md` exists in the project root
- If not exists, use slash command `/analysis_architect_and_framework` to generate it
- Include architect.md content in `--additional-prompt` argument

### Step 3: Check/Create Test File
- Test file location follows source file structure but in test directory
- Python example: `src/service/file.py` → `tests/service/test_file.py`
- Java example: `src/main/java/com/example/Service.java` → `src/test/java/com/example/ServiceTest.java`
- If test file doesn't exist, create it as an **EMPTY FILE** (do NOT add any placeholder content)
- Use `touch <test_file_path>` to create empty file, or `> <test_file_path>` to overwrite with empty content
- **IMPORTANT:** Do NOT add class definitions, imports, or any placeholder text - Keploy will generate the content

### Step 4: Detect Project Type
- **Python**: Look for `pyproject.toml`, `setup.py`, `requirements.txt`, or `.py` files
- **Java**: Look for `pom.xml` (Maven) or `build.gradle` (Gradle)

### Step 5: Install Dependencies
- **Python**: `uv add pytest pytest-asyncio coverage`
- **Java (Maven)**: Ensure jacoco-maven-plugin in pom.xml
- **Java (Gradle)**: Ensure jacoco plugin in build.gradle

### Step 6: Create/Update Gen_UnitTest.sh Script
- Check if `Gen_UnitTest.sh` exists in project root
- If NOT exists: Create new file with Keploy gen command
- If exists: Update/overwrite with new command (do NOT create duplicate)
- Make script executable: `chmod +x Gen_UnitTest.sh`

### Step 7: Build Keploy Command
Construct the keploy gen command in file Gen_UnitTest.sh with:
- Project-appropriate paths and test command
- Correct coverage format (cobertura for Python, jacoco for Java)
- architect.md content in additional-prompt
- User-specified or default values for all arguments

### Step 8: Execute and Monitor
- Display full command before execution
- Show real-time logs during execution
- If errors occur, display complete error logs
- Provide clear error messages and suggestions
"""
