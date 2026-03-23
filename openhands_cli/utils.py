"""Utility functions for LLM configuration in OpenHands CLI."""

import hashlib
import json
import os
import platform
import re
import urllib.error
import urllib.parse
import urllib.request
from argparse import Namespace
from collections import defaultdict
from pathlib import Path
from typing import Any

from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import HTML

from openhands.sdk import LLM, Agent, ImageContent, TextContent
from openhands.sdk.event import SystemPromptEvent
from openhands.sdk.event.base import Event
from openhands.sdk.tool import Tool
from openhands.tools.delegate import DelegateTool
from openhands.tools.file_editor import FileEditorTool
from openhands.tools.preset.default import get_default_condenser
from openhands.tools.task_tracker import TaskTrackerTool
from openhands.tools.terminal import TerminalTool


def abbreviate_number(n: int | float) -> str:
    """Abbreviate large numbers with K/M/B suffixes.

    Examples:
        1234 -> '1.23K'
        1200000 -> '1.2M'
        2500000000 -> '2.5B'
        999 -> '999'
    """
    n = int(n or 0)
    if n >= 1_000_000_000:
        val, suffix = n / 1_000_000_000, "B"
    elif n >= 1_000_000:
        val, suffix = n / 1_000_000, "M"
    elif n >= 1_000:
        val, suffix = n / 1_000, "K"
    else:
        return str(n)
    return f"{val:.2f}".rstrip("0").rstrip(".") + suffix


def format_cost(cost: float) -> str:
    """Format cost value for display.

    Returns '0.00' for zero or negative costs, otherwise formats to 4 decimal places.
    """
    if cost <= 0:
        return "0.00"
    return f"{cost:.4f}"


def get_os_description() -> str:
    system = platform.system() or "Unknown"

    if system == "Darwin":
        ver = platform.mac_ver()[0] or platform.release()
        return f"macOS {ver}".strip()

    if system == "Windows":
        release, version, *_ = platform.win32_ver()
        if release and version:
            return f"Windows {release} ({version})"
        return "Windows"

    if system == "Linux":
        kernel = platform.release()
        return f"Linux (kernel {kernel})" if kernel else "Linux"

    return platform.platform() or system


# Pattern to match OpenHands LLM proxy URLs (e.g., https://llm-proxy.app.all-hands.dev/)
# Must match the host part of the URL, not arbitrary path components
_LLM_PROXY_PATTERN = re.compile(r"^https?://llm-proxy\.[^.]+\.all-hands\.dev(?:/|$)")
_LOCAL_LITELLM_PROXY_PATTERN = re.compile(
    r"^https?://(?:localhost|127\.0\.0\.1|0\.0\.0\.0):4000(?:/|$)"
)
_LITELLM_PORT_PATTERN = re.compile(r"^https?://[^/]+:4000(?:/|$)")

# Best-effort in-process cache for key alias lookups to avoid repeated API calls.
_TRACE_USER_ID_CACHE: dict[str, str] = {}


def should_set_litellm_extra_body(model_name: str, base_url: str | None = None) -> bool:
    """
    Determine if litellm_extra_body should be set based on the model name or base URL.

    Set litellm_extra_body for:
    - Models with "openhands/" prefix
    - Any model using OpenHands LLM proxy (llm-proxy.*.all-hands.dev)

    This avoids issues with providers that don't support extra_body parameters.

    The SDK internally translates "openhands/" prefix to "litellm_proxy/"
    when making API calls.

    Args:
        model_name: Name of the LLM model
        base_url: Optional base URL for the LLM service

    Returns:
        True if litellm_extra_body should be set, False otherwise
    """
    if "openhands/" in model_name:
        return True

    if base_url and _LLM_PROXY_PATTERN.match(base_url):
        return True

    # Local LiteLLM proxy should also receive metadata for Langfuse filtering
    # (e.g. source:openhands, project:*, flow:*).
    if base_url and _LOCAL_LITELLM_PROXY_PATTERN.match(base_url):
        return True

    # Support local LiteLLM proxy via env var opt-in
    if os.environ.get("OPENHANDS_SEND_LLM_METADATA", "").lower() == "true":
        return True

    return False


def get_llm_metadata(
    model_name: str,
    llm_type: str,
    session_id: str | None = None,
    user_id: str | None = None,
    source: str = "openhands",
    flow: str | None = None,
    project_name: str | None = None,
) -> dict[str, Any]:
    """
    Generate LLM metadata for OpenHands CLI.

    Args:
        model_name: Name of the LLM model
        llm_type: LLM usage type (e.g. "agent", "condenser")
        session_id: Optional session identifier
        user_id: Optional user identifier
        source: Trace source tag (defaults to "openhands")
        flow: Optional flow tag (defaults to "chat")
        project_name: Optional project tag value; defaults to current folder name

    Returns:
        Dictionary containing metadata for LLM initialization
    """
    resolved_project = (
        project_name
        or os.environ.get("OPENHANDS_PROJECT_NAME")
        or Path.cwd().name
        or "unknown"
    )

    resolved_flow = flow or "chat"

    resolved_source = source or os.environ.get("OPENHANDS_TRACE_SOURCE", "openhands")
    resolved_invoker = os.environ.get("OPENHANDS_TRACE_INVOKER", "direct")
    resolved_env = os.environ.get("ENV", "dev")

    metadata = {
        "project": resolved_project,
        "source": resolved_source,
        "flow": resolved_flow,
        "component": llm_type,
        "model": model_name,
        "invoker": resolved_invoker,
        "env": resolved_env,
        "web_host": os.environ.get("WEB_HOST", "unspecified"),
        "tags": [resolved_project],
    }

    if session_id is not None:
        metadata["session_id"] = session_id

    if user_id is not None:
        metadata["trace_user_id"] = user_id
        metadata["user_id"] = user_id

    return metadata


def _normalize_litellm_admin_url(base_url: str) -> str:
    """Normalize a model base URL into LiteLLM admin URL root."""
    stripped = base_url.strip().rstrip("/")
    if stripped.endswith("/v1"):
        return stripped[: -len("/v1")]
    return stripped


def _is_litellm_proxy_url(base_url: str | None) -> bool:
    if not base_url:
        return False

    return bool(
        _LLM_PROXY_PATTERN.match(base_url)
        or _LOCAL_LITELLM_PROXY_PATTERN.match(base_url)
        or _LITELLM_PORT_PATTERN.match(base_url)
    )


def _lookup_litellm_key_alias(api_key: str, base_url: str) -> str | None:
    """Best-effort lookup of key alias from LiteLLM /key/info."""
    cache_key = f"{base_url}::{api_key}"
    if cache_key in _TRACE_USER_ID_CACHE:
        return _TRACE_USER_ID_CACHE[cache_key]

    admin_url = _normalize_litellm_admin_url(base_url)
    def _extract_alias(payload: Any) -> str | None:
        candidates: list[Any] = []
        if isinstance(payload, dict):
            candidates.extend(
                [
                    payload.get("key_alias"),
                    payload.get("key_name"),
                    payload.get("alias"),
                ]
            )
            info = payload.get("info")
            if isinstance(info, dict):
                candidates.extend(
                    [
                        info.get("key_alias"),
                        info.get("key_name"),
                        info.get("alias"),
                    ]
                )

        for candidate in candidates:
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
        return None

    def _call(url: str, bearer: str) -> Any | None:
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {bearer}"},
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                return json.loads(resp.read().decode("utf-8", errors="replace"))
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError):
            return None

    # Attempt 1: self lookup using the same key in Authorization header.
    payload = _call(f"{admin_url}/key/info", api_key)
    alias = _extract_alias(payload)
    if alias:
        _TRACE_USER_ID_CACHE[cache_key] = alias
        return alias

    # Attempt 2: admin lookup using ?key=<user-key> + admin bearer.
    admin_key = os.environ.get("OPENHANDS_LITELLM_ADMIN_KEY", "").strip()
    if admin_key and admin_key != api_key:
        encoded_key = urllib.parse.quote(api_key, safe="")
        payload = _call(f"{admin_url}/key/info?key={encoded_key}", admin_key)
        alias = _extract_alias(payload)
        if alias:
            _TRACE_USER_ID_CACHE[cache_key] = alias
            return alias

    return None


def derive_trace_user_id(api_key: str | None, base_url: str | None = None) -> str | None:
    """Derive a stable, non-secret user identifier for tracing/filtering.

    Resolution order:
    1) ``OPENHANDS_TRACE_USER_ID`` if explicitly set (manual override).
    2) ``OPENHANDS_TRACE_USER_MAP`` JSON object mapping API key -> user id.
    3) LiteLLM key alias from ``/key/info`` (if enabled + proxy URL is known).
    4) Deterministic fingerprint from API key (SHA-256, first 12 hex chars).

    The fallback fingerprint allows "one key = one user" filtering without
    exposing raw API keys in metadata.
    """
    explicit_user = os.environ.get("OPENHANDS_TRACE_USER_ID", "").strip()
    if explicit_user:
        return explicit_user

    mapping_raw = os.environ.get("OPENHANDS_TRACE_USER_MAP", "").strip()
    if mapping_raw and api_key:
        try:
            mapping = json.loads(mapping_raw)
            if isinstance(mapping, dict):
                mapped = mapping.get(api_key)
                if isinstance(mapped, str) and mapped.strip():
                    return mapped.strip()
        except json.JSONDecodeError:
            pass

    # Optional: derive user id from LiteLLM key alias.
    # Enabled by default; disable with OPENHANDS_USE_LITELLM_KEY_ALIAS=false.
    use_litellm_alias = os.environ.get("OPENHANDS_USE_LITELLM_KEY_ALIAS", "true")
    use_litellm_alias = use_litellm_alias.strip().lower() not in {
        "0",
        "false",
        "no",
    }
    if (
        use_litellm_alias
        and api_key
        and base_url
        and _is_litellm_proxy_url(base_url)
    ):
        alias = _lookup_litellm_key_alias(api_key=api_key, base_url=base_url)
        if alias:
            return alias

    if not api_key:
        return None

    # Avoid leaking full secrets: use a short deterministic fingerprint.
    digest = hashlib.sha256(api_key.encode("utf-8")).hexdigest()[:12]
    return f"user_{digest}"


def get_default_cli_tools() -> list[Tool]:
    """Get the default tool specifications for CLI mode (browser disabled)."""
    return [
        Tool(name=TerminalTool.name),
        Tool(name=FileEditorTool.name),
        Tool(name=TaskTrackerTool.name),
        Tool(name=DelegateTool.name),
    ]


def get_default_cli_agent(llm: LLM) -> Agent:
    """Create the default CLI agent with all tools (browser disabled)."""
    return Agent(
        llm=llm,
        tools=get_default_cli_tools(),
        system_prompt_kwargs={"cli_mode": True},
        condenser=get_default_condenser(
            llm=llm.model_copy(update={"usage_id": "condenser"})
        ),
    )


def create_seeded_instructions_from_args(args: Namespace) -> list[str] | None:
    """
    Build initial CLI input(s) from parsed arguments.
    """
    if getattr(args, "command", None) == "serve":
        return None

    # --file takes precedence over --task
    if getattr(args, "file", None):
        path = Path(args.file).expanduser()
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            print_formatted_text(HTML(f"<red>Failed to read file {path}: {exc}</red>"))
            raise SystemExit(1)

        initial_message = (
            "Starting this session with file context.\n\n"
            f"File path: {path}\n\n"
            "File contents:\n"
            "--------------------\n"
            f"{content}\n"
            "--------------------\n"
        )
        return [initial_message]

    if getattr(args, "task", None):
        return [args.task]

    return None


def extract_text_from_message_content(
    message_content: list[TextContent | ImageContent], has_exactly_one: bool = True
) -> str | None:
    """Extract text from message content for slash command detection.

    Args:
        message_content: Message content (typically a list of content blocks)

    Returns:
        The text content of first TextContent block, None otherwise
    """

    if len(message_content) == 0:
        return None

    if has_exactly_one and len(message_content) != 1:
        return None

    # Only accept single TextContent blocks for slash commands
    if not isinstance(message_content[0], TextContent):
        return None

    # Use SDK utility to extract text - content_to_str handles the conversion
    return message_content[0].text


def json_callback(event: Event) -> None:
    if isinstance(event, SystemPromptEvent):
        return

    data = event.model_dump()
    pretty_json = json.dumps(data, indent=2, sort_keys=True)
    print("--JSON Event--")
    print(pretty_json)


def get_current_wd() -> Path:
    cwd = Path.cwd()
    return cwd


def count_files_by_type(directory) -> dict:
    file_type_counts = defaultdict(int)
    for root, dirs, files in os.walk(directory):
        for file in files:
            _, ext = os.path.splitext(file)
            ret_ext = ext.lower()[1:] if ext else "no_extension"
            file_type_counts[ret_ext] += 1

    return dict(file_type_counts)


def get_project_type(count_types: dict) -> int:
    from openhands_cli.constants import CustomConstants

    python_count = count_types.get("py", 0)
    java_count = count_types.get("java", 0)

    if python_count >= java_count:
        return CustomConstants.PROJECT_TYPE_PYTHON
    elif java_count > 0:
        return CustomConstants.PROJECT_TYPE_JAVA
    return CustomConstants.PROJECT_TYPE_UNKNOWN


def get_shell_type() -> int:
    import os

    import psutil

    from openhands_cli.constants import CustomConstants

    parent = psutil.Process(os.getppid()).name().lower()

    if "powershell" in parent:
        return CustomConstants.SHELL_TYPE_PS
    elif "cmd" in parent:
        return CustomConstants.SHELL_TYPE_CMD
    else:
        return CustomConstants.SHELL_TYPE_OTHER
