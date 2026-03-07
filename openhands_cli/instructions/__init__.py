"""
Instructions module for OpenHands CLI.

This module provides developer-defined skills that are hardcoded and
compiled with Nuitka for protection. Users can still add their own
skills via markdown files in designated directories.

Usage:
    from openhands_cli.instructions import get_dev_skills

    skills = get_dev_skills()
    # Returns list of Skill objects defined by developers
"""

from openhands_cli.instructions.dev_skills import get_dev_skills

__all__ = ["get_dev_skills"]
