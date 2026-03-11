"""
Keploy unit test generation module.

This package contains:
- constants.py: Default values, CLI arguments, and trigger keywords
- scripts/: Bash script templates for Python and Java projects
- workflows.py: Workflow documentation for both platforms
- error_handling.py: Common issues and solutions

All content is compiled and protected by Nuitka.
"""

from openhands_cli.instructions.utgen.constants import (
    CLI_ARGUMENTS,
    DEFAULTS,
    JAVA_DEFAULTS,
    KEPLOY_KEYWORDS,
    PYTHON_DEFAULTS,
    GEN_SCRIPT_FILE,
)

from openhands_cli.instructions.utgen.error_handling import ERROR_HANDLING_GUIDE
from openhands_cli.instructions.utgen.scripts.java_template import JAVA_SCRIPT_TEMPLATE
from openhands_cli.instructions.utgen.scripts.python_template import (
    PYTHON_SCRIPT_TEMPLATE,
)
from openhands_cli.instructions.utgen.workflows import (
    JAVA_WORKFLOW,
    PYTHON_WORKFLOW,
    OVERALL_WORKFLOW,
)

__all__ = [
    # Constants
    "CLI_ARGUMENTS",
    "DEFAULTS",
    "PYTHON_DEFAULTS",
    "JAVA_DEFAULTS",
    "KEPLOY_KEYWORDS",
    "GEN_SCRIPT_FILE",
    # Scripts
    "PYTHON_SCRIPT_TEMPLATE",
    "JAVA_SCRIPT_TEMPLATE",
    # Workflows
    "PYTHON_WORKFLOW",
    "JAVA_WORKFLOW",
    "OVERALL_WORKFLOW",
    # Error handling
    "ERROR_HANDLING_GUIDE",
]
