"""
Keploy script templates.

This module contains bash script templates for generating unit tests
using Keploy AI-powered tool.
"""

from openhands_cli.instructions.utgen.scripts.java_template import JAVA_SCRIPT_TEMPLATE
from openhands_cli.instructions.utgen.scripts.python_template import (
    PYTHON_SCRIPT_TEMPLATE,
)


__all__ = [
    "PYTHON_SCRIPT_TEMPLATE",
    "JAVA_SCRIPT_TEMPLATE",
]
