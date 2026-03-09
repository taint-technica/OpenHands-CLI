"""
Keploy unit test generation module.

This package contains:
- constants.py: CLI arguments and trigger keywords
- scripts/: Bash script templates for Python and Java projects
- workflows.py: Workflow documentation for both platforms
- refactor_guides.py: Refactoring guidelines for generated tests

All content is compiled and protected by Nuitka.
"""

from openhands_cli.instructions.utgen.constants import (
    CLI_ARGUMENTS,
    KEPLOY_KEYWORDS,
)
from openhands_cli.instructions.utgen.refactor_guides import (
    JAVA_REFACTOR_GUIDE,
    PYTHON_REFACTOR_GUIDE,
)
from openhands_cli.instructions.utgen.scripts.java_template import (
    JAVA_SCRIPT_TEMPLATE,
)
from openhands_cli.instructions.utgen.scripts.python_template import (
    PYTHON_SCRIPT_TEMPLATE,
)
from openhands_cli.instructions.utgen.workflows import (
    JAVA_WORKFLOW,
    OVERALL_WORKFLOW,
    PYTHON_WORKFLOW,
)


__all__ = [
    # Constants
    "CLI_ARGUMENTS",
    "KEPLOY_KEYWORDS",
    # Scripts
    "PYTHON_SCRIPT_TEMPLATE",
    "JAVA_SCRIPT_TEMPLATE",
    # Workflows
    "PYTHON_WORKFLOW",
    "JAVA_WORKFLOW",
    "OVERALL_WORKFLOW",
    # Refactor
    "PYTHON_REFACTOR_GUIDE",
    "JAVA_REFACTOR_GUIDE",
]
