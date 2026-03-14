"""Langfuse configuration storage for OpenHands CLI.

This module handles saving and loading Langfuse tracing configuration,
including API credentials and server settings.
"""

import json
import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class LangfuseSettings(BaseModel):
    """Settings for Langfuse tracing integration."""

    enabled: bool = False
    host: str = Field(default="http://localhost:3000", description="Langfuse server URL")
    public_key: str = Field(default="", description="Langfuse public key")
    secret_key: str = Field(default="", description="Langfuse secret key")
    project_name: str = Field(
        default="openhands-cli", description="Project name in Langfuse"
    )

    @field_validator("host")
    @classmethod
    def validate_host(cls, v: str) -> str:
        """Validate Langfuse host URL format."""
        if not v:
            return "http://localhost:3000"
        # Remove trailing slash if present
        return v.rstrip("/")

    @field_validator("public_key", "secret_key")
    @classmethod
    def validate_api_keys(cls, v: str) -> str:
        """Validate API keys are not empty when enabled."""
        return v or ""

    def is_valid(self) -> bool:
        """Check if settings are valid for Langfuse integration."""
        if not self.enabled:
            return True
        # If enabled, must have host and both keys
        return bool(self.host and self.public_key and self.secret_key)

    def to_env_vars(self) -> dict[str, str]:
        """Convert settings to environment variables for LiteLLM."""
        return {
            "LANGFUSE_HOST": self.host,
            "LANGFUSE_PUBLIC_KEY": self.public_key,
            "LANGFUSE_SECRET_KEY": self.secret_key,
            "LANGFUSE_PROJECT_NAME": self.project_name,
        }


class LangfuseStore:
    """Store for Langfuse configuration.

    Saves to ~/.openhands/langfuse_config.json
    """

    CONFIG_FILE = "langfuse_config.json"

    def __init__(self) -> None:
        """Initialize Langfuse store."""
        self.config_path = self._get_config_path()

    def _get_config_path(self) -> Path:
        """Get path to Langfuse config file."""
        # Use environment variable if set, otherwise use default
        persistence_dir = os.environ.get(
            "OPENHANDS_PERSISTENCE_DIR", os.path.expanduser("~/.openhands")
        )
        return Path(persistence_dir) / self.CONFIG_FILE

    def load(self) -> LangfuseSettings:
        """Load Langfuse settings from file.

        Returns:
            LangfuseSettings instance with loaded settings, or defaults if file
            doesn't exist
        """
        if not self.config_path.exists():
            return LangfuseSettings()

        try:
            with open(self.config_path) as f:
                data = json.load(f)
            return LangfuseSettings.model_validate(data)
        except (json.JSONDecodeError, ValueError, OSError):
            # If file is corrupted, return defaults
            return LangfuseSettings()

    def save(self, settings: LangfuseSettings) -> None:
        """Save Langfuse settings to file.

        Args:
            settings: LangfuseSettings instance to save
        """
        # Ensure the persistence directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.config_path, "w") as f:
            json.dump(settings.model_dump(), f, indent=2)

    def is_enabled(self) -> bool:
        """Check if Langfuse tracing is enabled and configured.

        Returns:
            True if Langfuse is enabled and has valid configuration
        """
        settings = self.load()
        return settings.enabled and settings.is_valid()

    def disable(self) -> None:
        """Disable Langfuse tracing."""
        settings = self.load()
        settings.enabled = False
        self.save(settings)

    def test_connection(self, settings: Optional[LangfuseSettings] = None) -> bool:
        """Test connection to Langfuse server.

        Args:
            settings: Optional settings to test. If None, loads from disk.

        Returns:
            True if connection successful, False otherwise
        """
        if settings is None:
            settings = self.load()

        if not settings.is_valid():
            return False

        try:
            import httpx

            # Test Langfuse public API health endpoint
            # Note: Langfuse 3.x uses /api/public/health instead of /api/health
            response = httpx.get(
                f"{settings.host}/api/public/health",
                timeout=5.0,
            )
            return response.status_code == 200
        except Exception:
            return False
