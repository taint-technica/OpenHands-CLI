# Developer Instructions Guide

This guide explains how to add and manage developer-defined instructions (skills) in OpenHands CLI.

## Quick Start

### For Linux Users

```bash
# 1. Install build dependencies
sudo apt-get update && sudo apt-get install -y patchelf

# 2. Add your hardcoded instructions
vim openhands_cli/instructions/dev_skills.py

# 3. Build with Nuitka
./build_nuitka.sh

# 4. Test the binary
./dist/openhands --help
```

### For macOS Users

```bash
# 1. Install Xcode command line tools
xcode-select --install

# 2. Add your hardcoded instructions
vim openhands_cli/instructions/dev_skills.py

# 3. Build with Nuitka
./build_nuitka.sh

# 4. Test the binary
./dist/openhands --help
```

**Note:** Nuitka compilation takes 3-5 minutes for the first build. The resulting binary is standalone and cannot be easily decompiled.

---

## Overview

OpenHands CLI supports two types of skills:

## Langfuse Trace Filtering (OpenHands + Keploy)

This project uses a unified tracing strategy:

- Default Langfuse view shows **all traces combined**.
- You can then filter by tags for focused analysis.

### Standard tags

- `project:<name>`
- `source:openhands` or `source:keploy`
- `flow:chat` or `flow:utgen`
- `component:agent` or `component:condenser`

### Expected behavior

- OpenHands chat traces are tagged with `source:openhands`.
- Keploy unit-test generation traces are intended to use `source:keploy`.
- Filtering by `project:*` still includes both sources unless `source:*` is also applied.

### Practical filters in Langfuse

- All traces for project: `project:OpenHands-CLI`
- OpenHands only: `project:OpenHands-CLI` + `source:openhands`
- Keploy only: `project:OpenHands-CLI` + `source:keploy`

This preserves a professional default dashboard (aggregate view first), while enabling source-level drill-down when needed.

### 1. **Dev Skills (Hardcoded)** 📝
- Defined in Python code by developers
- Compiled with Nuitka for protection
- **Cannot be read by end users** after compilation
- Located in: `openhands_cli/instructions/dev_skills.py`

### 2. **User Skills (Markdown Files)** 📄
- Defined by users in markdown format
- Stored in designated directories
- **Can be read and modified by users**
- Locations:
  - `~/.openhands/skills/*.md` (home directory)
  - `{project}/.agents/skills/*.md` (project directory)
  - `{project}/.openhands/skills/*.md` (legacy)

## Adding Dev Skills (Hardcoded Instructions)

### Step 1: Edit `dev_skills.py`

Open `openhands_cli/instructions/dev_skills.py` and add your skill:

```python
from openhands.sdk.context import Skill
from openhands.sdk.context.skills.trigger import KeywordTrigger

# Always-active skill (goes into REPO_CONTEXT)
MY_CUSTOM_INSTRUCTION = Skill(
    name="my_custom_instruction",
    content="""
## Your Proprietary Instructions

This content will be compiled and protected.
Users cannot read it after Nuitka compilation.

### Your Secret Guidelines
1. Never expose API keys
2. Always validate inputs
3. ... (your proprietary content)
""",
    trigger=None,  # Always active
    description="My custom instructions",
)

# Trigger-based skill (activated by keywords)
MY_TRIGGERED_SKILL = Skill(
    name="my_triggered_skill",
    content="""
## Specialized Knowledge

This skill is only injected when user mentions keywords.
""",
    trigger=KeywordTrigger(keywords=["keyword1", "keyword2", "special"]),
    description="Specialized knowledge base",
)
```

### Step 2: Update `get_dev_skills()`

Add your skill to the return list:

```python
def get_dev_skills() -> list[Skill]:
    """Get all developer-defined skills."""
    return [
        CORE_CODING_INSTRUCTIONS,
        SECURITY_GUIDELINES,
        MY_CUSTOM_INSTRUCTION,  # ← Add your skill here
        MY_TRIGGERED_SKILL,     # ← Add your skill here
        # ... other skills
    ]
```

### Step 3: Install Build Dependencies (Linux only)

Nuitka requires `patchelf` on Linux for creating standalone binaries:

```bash
# Ubuntu/Debian
sudo apt-get update && sudo apt-get install -y patchelf

# Fedora/RHEL
sudo dnf install -y patchelf

# Verify installation
patchelf --version  # Should show version 0.18.0 or higher
```

**Note:** If you don't have `patchelf` installed, the build script will warn you and provide instructions.

### Step 4: Build with Nuitka

Compile the CLI to protect your instructions:

```bash
# Using shell script (recommended)
./build_nuitka.sh

# Or using Python script
python build_nuitka.py
```

This creates a binary in `dist/openhands` that cannot be easily decompiled.

**Build time:** First build takes 3-5 minutes. Subsequent builds are faster.

**Output size:** ~50-100MB (compressed with UPX)

## Adding User Skills (Markdown Files)

Users can add their own skills without modifying code:

### Create Skill File

```markdown
---
name: my-custom-skill
triggers: ["custom", "special"]
description: My custom skill for specific tasks
---

## My Custom Skill Content

This skill will be loaded automatically when user mentions:
- "custom"
- "special"

### Instructions

1. Do this first
2. Then do that
3. Finally, complete the task
```

### Save to Directory

Save the file to one of these locations:
- `~/.openhands/skills/my-custom-skill.md`
- `{project}/.agents/skills/my-custom-skill.md`

The CLI will automatically scan and load these skills at runtime.

## Skill Types Explained

### Always-Active Skills (`trigger=None`)

These skills are **always included** in the system prompt under `<REPO_CONTEXT>`:

```python
ALWAYS_ACTIVE = Skill(
    name="always_active",
    content="This is always in the prompt...",
    trigger=None,  # ← None means always active
)
```

**Use case:** Core instructions, base guidelines, fundamental principles.

### Trigger-Based Skills (`KeywordTrigger`)

These skills are **only injected** when user mentions specific keywords:

```python
TRIGGERED_SKILL = Skill(
    name="triggered_skill",
    content="This appears only when triggered...",
    trigger=KeywordTrigger(keywords=["python", "coding", "development"]),
)
```

**Use case:** Specialized knowledge, domain-specific guidance, optional context.

## Best Practices

### For Dev Skills

1. **Keep it secret**: Put proprietary algorithms, trade secrets, and competitive advantages in dev skills
2. **Use triggers wisely**: Trigger-based skills keep prompts clean and only activate when needed
3. **Test before compiling**: Run `python -c "from openhands_cli.instructions import get_dev_skills; print(get_dev_skills())"` to verify
4. **Document internally**: Add comments in `dev_skills.py` for your team

### For User Skills

1. **Provide examples**: Include example skill files in your documentation
2. **Clear naming**: Use descriptive skill names and triggers
3. **Organize by topic**: Group related skills in the same directory

## Verification

### Check Skills Are Loaded

```bash
# Test that dev skills load correctly
uv run python -c "from openhands_cli.instructions import get_dev_skills; skills = get_dev_skills(); print(f'Loaded {len(skills)} skills')"

# Test full integration
uv run python -c "from openhands_cli.stores.agent_store import AgentStore; store = AgentStore(); agent = store.load_or_create(); print(f'Agent has {len(agent.agent_context.skills)} skills')"
```

### Verify Protection

After building with Nuitka:

```bash
# Try to find your instructions (should fail)
strings dist/openhands | grep -i "your-secret-keyword"

# Should output nothing if properly protected
```

## Troubleshooting

### Issue: Skills not loading

**Solution:** Check that `get_dev_skills()` is called in `agent_store.py`:

```python
# openhands_cli/stores/agent_store.py
from openhands_cli.instructions import get_dev_skills

def _build_agent_context(self) -> AgentContext:
    dev_skills = get_dev_skills()  # ← Must be here
    project_skills = load_project_skills(get_work_dir())
    all_skills = dev_skills + project_skills
    # ...
```

### Issue: Trigger not working

**Solution:** Verify trigger keywords match exactly (case-sensitive):

```python
# Wrong: keywords don't match
trigger=KeywordTrigger(keywords=["Python"])  # Only matches "Python"

# Right: include variations
trigger=KeywordTrigger(keywords=["python", "Python", "PYTHON"])
```

### Issue: Build fails with Nuitka

**Solution 1:** Check C compiler is installed:

```bash
# Ubuntu/Debian
sudo apt-get install build-essential

# macOS
xcode-select --install

# Windows
# Install MSVC or MinGW
```

**Solution 2:** Install patchelf (Linux only, required for standalone mode):

```bash
# Ubuntu/Debian
sudo apt-get install patchelf

# Fedora/RHEL
sudo dnf install patchelf

# Verify
patchelf --version
```

**Solution 3:** Install Nuitka if not found:

```bash
# Using uv (recommended for this project)
uv add --dev nuitka zstandard

# Or using pip
pip install nuitka zstandard
```

## Example Use Cases

### 1. Company Coding Standards

```python
COMPANY_STANDARDS = Skill(
    name="company_coding_standards",
    content="""
    ## ACME Corp Coding Standards
    
    1. All functions must have type hints
    2. Use our internal logging framework
    3. Follow our security guidelines (document XYZ)
    4. ... (your proprietary standards)
    """,
    trigger=None,  # Always active
)
```

### 2. Proprietary Framework Knowledge

```python
INTERNAL_FRAMEWORK = Skill(
    name="internal_framework",
    content="""
    ## ACME Internal Framework
    
    Our secret framework uses these patterns:
    - Special authentication flow (patent pending)
    - Custom ORM with specific syntax
    - ... (proprietary knowledge)
    """,
    trigger=KeywordTrigger(keywords=["framework", "internal", "acme"]),
)
```

### 3. Domain-Specific Expertise

```python
FINANCIAL_EXPERTISE = Skill(
    name="financial_expertise",
    content="""
    ## Financial Domain Knowledge
    
    Our proprietary financial models and algorithms:
    - Risk calculation formula (trade secret)
    - Compliance rules (internal documentation)
    - ... (domain expertise)
    """,
    trigger=KeywordTrigger(keywords=["financial", "finance", "banking", "compliance"]),
)
```

## Security Notes

⚠️ **Important:** While Nuitka compilation provides strong protection:

- ✅ Users cannot easily read your instructions
- ✅ Binary cannot be easily decompiled
- ✅ `strings` command won't reveal content
- ⚠️  **But** instructions are still sent to LLM API
- ⚠️  **But** determined attackers might extract via memory analysis

**For maximum security:**
1. Don't include extremely sensitive information (API keys, passwords)
2. Use encryption for highly sensitive data
3. Consider server-side injection for top-secret instructions

## Additional Resources

- [OpenHands Skills Documentation](https://docs.openhands.dev/overview/skills)
- [Nuitka Documentation](https://nuitka.net/doc/Manual.html)
- [OpenHands SDK GitHub](https://github.com/OpenHands/software-agent-sdk)
