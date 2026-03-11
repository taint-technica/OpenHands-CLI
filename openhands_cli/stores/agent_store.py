from __future__ import annotations

import json
import os
import re
from typing import Any

from prompt_toolkit import HTML, print_formatted_text

from openhands.sdk import (
    LLM,
    Agent,
    AgentContext,
    LLMSummarizingCondenser,
    LocalFileStore,
)
from openhands.sdk.context import load_project_skills
from openhands.sdk.conversation.persistence_const import BASE_STATE
from openhands.sdk.critic.base import CriticBase
from openhands.sdk.critic.impl.api import APIBasedCritic
from openhands.sdk.tool import Tool
from openhands_cli.instructions import get_dev_skills
from openhands_cli.locations import (
    AGENT_SETTINGS_PATH,
    get_conversations_dir,
    get_persistence_dir,
    get_work_dir,
)
from openhands_cli.mcp.mcp_utils import list_enabled_servers
from openhands_cli.stores.cli_settings import CliSettings
from openhands_cli.stores.langfuse_store import LangfuseStore
from openhands_cli.utils import (
    get_default_cli_tools,
    get_llm_metadata,
    get_os_description,
    should_set_litellm_extra_body,
)


def get_persisted_conversation_tools(conversation_id: str) -> list[Tool] | None:
    """Get tools from a persisted conversation's base_state.json.

    When resuming a conversation, we should use the tools that were available
    when the conversation was created, not the current default tools. This
    ensures consistency and prevents issues with tools that weren't available
    in the original conversation (e.g., delegate tool).

    Args:
        conversation_id: The conversation ID to look up

    Returns:
        List of Tool objects from the persisted conversation, or None if
        the conversation doesn't exist or can't be read
    """
    conversation_dir = os.path.join(get_conversations_dir(), conversation_id)
    base_state_path = os.path.join(conversation_dir, BASE_STATE)

    if not os.path.exists(base_state_path):
        return None

    try:
        with open(base_state_path) as f:
            state_data = json.load(f)

        # Extract tools from the persisted agent
        agent_data = state_data.get("agent", {})
        tools_data = agent_data.get("tools", [])

        if not tools_data:
            return None

        # Convert tool data to Tool objects
        return [Tool.model_validate(tool) for tool in tools_data]
    except (json.JSONDecodeError, KeyError, OSError):
        return None


def get_default_critic(llm: LLM, *, enable_critic: bool = True) -> CriticBase | None:
    """Auto-configure critic for All-Hands LLM proxy.

    When the LLM base_url matches `llm-proxy.*.all-hands.dev`, returns an
    APIBasedCritic configured with:
    - server_url: {base_url}/vllm
    - api_key: same as LLM
    - model_name: "critic"

    Returns None if base_url doesn't match, api_key is not set, or enable_critic
    is False.

    Args:
        llm: The LLM configuration
        enable_critic: Whether critic feature is enabled (from settings)
    """
    # Check if critic is enabled in settings
    if not enable_critic:
        return None

    base_url = llm.base_url
    api_key = llm.api_key
    if base_url is None or api_key is None:
        return None

    # Match: llm-proxy.{env}.all-hands.dev (e.g., staging, prod, eval, app)
    pattern = r"^https?://llm-proxy\.[^./]+\.all-hands\.dev"
    if not re.match(pattern, base_url):
        return None

    try:
        return APIBasedCritic(
            server_url=f"{base_url.rstrip('/')}/vllm",
            api_key=api_key,
            model_name="critic",
        )
    except Exception:
        # If critic creation fails, silently return None
        # This allows the CLI to continue working without critic
        return None


DEFAULT_LLM_BASE_URL = "https://llm-proxy.app.all-hands.dev/"


class AgentStore:
    """Single source of truth for persisting/retrieving AgentSpec."""

    def __init__(self) -> None:
        self.file_store = LocalFileStore(root=get_persistence_dir())

    def load_from_disk(self) -> Agent | None:
        """Load an agent configuration from disk storage.

        This method only loads the persisted agent configuration. It does not
        apply runtime configuration or create agents from environment variables.

        Returns:
            Raw Agent instance from disk, or None if no configuration exists
            or the file is corrupted.
        """
        try:
            str_spec = self.file_store.read(AGENT_SETTINGS_PATH)
            # Respects user choices persisted in agent_settings.json on disk.
            return Agent.model_validate_json(str_spec)
        except FileNotFoundError:
            return None
        except Exception:
            print_formatted_text(
                HTML("\n<red>Agent configuration file is corrupted!</red>")
            )
            return None

    def load_or_create(
        self,
        session_id: str | None = None,
        *,
        critic_disabled: bool = False,
    ) -> Agent | None:
        """Load an Agent and apply runtime configuration.

        Runtime configuration (tools, context, MCP, metadata, critic) is
        always applied last.

        Args:
            session_id: Optional session ID used for tool restoration and
                LLM metadata tagging.
            critic_disabled: If True, do not configure a critic.

        Returns:
            A fully configured Agent, or None if no persisted agent exists.
        """

        agent = self.load_from_disk()

        if agent is None:
            return None

        # Apply runtime configuration (tools, context, MCP, condenser, critic)
        return self._apply_runtime_config(
            agent,
            session_id,
            critic_disabled=critic_disabled,
        )

    def _resolve_tools(self, session_id: str | None) -> list[Tool]:
        tools = get_persisted_conversation_tools(session_id) if session_id else None
        return tools or get_default_cli_tools()

    def _with_llm_metadata(
        self, llm: LLM, *, session_id: str | None, llm_type: str
    ) -> LLM:
        if not should_set_litellm_extra_body(llm.model, llm.base_url):
            return llm
        return llm.model_copy(
            update={
                "litellm_extra_body": {
                    "metadata": get_llm_metadata(
                        model_name=llm.model,
                        llm_type=llm_type,
                        session_id=session_id,
                    )
                }
            }
        )

    def _build_agent_context(self) -> AgentContext:
        # Load developer-defined skills (hardcoded, compiled with Nuitka)
        dev_skills = get_dev_skills()

        # Load project skills (from .agents/skills/, .openhands/skills/)
        project_skills = load_project_skills(get_work_dir())

        # Combine skills: dev skills + project skills
        # User skills will be loaded separately via load_user_skills=True
        all_skills = dev_skills + project_skills

        system_suffix = "\n".join(
            [
                f"Your current working directory is: {get_work_dir()}",
                f"User operating system: {get_os_description()}",
            ]
        )
        return AgentContext(
            skills=all_skills,
            system_message_suffix=system_suffix,
            load_user_skills=True,
            load_public_skills=True,
        )

    def _enable_langfuse_callback(self, langfuse_store: LangfuseStore) -> None:
        """Enable Langfuse tracing for LiteLLM."""
        settings = langfuse_store.load()
        if not settings.is_valid():
            return

        # Set environment variables for Langfuse
        env_vars = settings.to_env_vars()
        for key, value in env_vars.items():
            os.environ[key] = value

        # Enable Langfuse callbacks for LiteLLM
        try:
            import litellm

            # Set Langfuse as success and failure callback
            litellm.success_callback = ["langfuse"]
            litellm.failure_callback = ["langfuse"]

            print_formatted_text(
                HTML(f"<dim>✓ Langfuse tracing enabled: {settings.host}</dim>")
            )
        except Exception as e:
            # Silently fail - Langfuse is optional
            print_formatted_text(HTML(f"<dim>⚠ Langfuse setup failed: {str(e)}</dim>"))

    def _maybe_build_condenser(
        self, agent: Agent, *, session_id: str | None
    ) -> LLMSummarizingCondenser | None:
        if not (
            agent.condenser and isinstance(agent.condenser, LLMSummarizingCondenser)
        ):
            return None

        condenser_llm = self._with_llm_metadata(
            agent.condenser.llm, session_id=session_id, llm_type="condenser"
        )

        return agent.condenser.model_copy(update={"llm": condenser_llm})

    def _apply_runtime_config(
        self,
        agent: Agent,
        session_id: str | None = None,
        *,
        critic_disabled: bool = False,
    ) -> Agent:
        updated_tools = self._resolve_tools(session_id)
        updated_llm = self._with_llm_metadata(
            agent.llm, session_id=session_id, llm_type="agent"
        )

        agent_context = self._build_agent_context()

        # Enable Langfuse tracing if configured
        langfuse_store = LangfuseStore()
        if langfuse_store.is_enabled():
            self._enable_langfuse_callback(langfuse_store)

        enabled_servers = list_enabled_servers()
        mcp_config = {"mcpServers": enabled_servers} if enabled_servers else {}

        condenser = self._maybe_build_condenser(agent, session_id=session_id)

        critic = None
        if not critic_disabled:
            cli_settings = CliSettings.load()
            critic = get_default_critic(
                updated_llm, enable_critic=cli_settings.critic.enable_critic
            )

        return agent.model_copy(
            update={
                "llm": updated_llm,
                "tools": updated_tools,
                "mcp_config": mcp_config,
                "agent_context": agent_context,
                "condenser": condenser,
                "critic": critic,
            }
        )

    def save(self, agent: Agent) -> None:
        serialized_spec = agent.model_dump_json(context={"expose_secrets": True})
        self.file_store.write(AGENT_SETTINGS_PATH, serialized_spec)

    def create_and_save_from_settings(
        self,
        llm_api_key: str,
        settings: dict[str, Any],
        default_model: str = "claude-sonnet-4-5-20250929",
    ) -> Agent:
        """Create an Agent instance from user settings and API key, then save it.

        Args:
            llm_api_key: The LLM API key to use
            settings: User settings dictionary (e.g., "llm_model", "llm_base_url")
            default_model: Default model to use if not specified in settings

        Returns:
            The created Agent instance
        """
        model = settings.get("llm_model", default_model)
        base_url = settings.get("llm_base_url")

        llm = LLM(
            model=model,
            api_key=llm_api_key,
            base_url=base_url,
            usage_id="agent",
        )

        condenser_llm = LLM(
            model=model,
            api_key=llm_api_key,
            base_url=base_url,
            usage_id="condenser",
        )

        condenser = LLMSummarizingCondenser(llm=condenser_llm)

        agent = Agent(
            llm=llm,
            tools=get_default_cli_tools(),
            mcp_config={},
            condenser=condenser,
            # Note: critic is NOT included here - it will be derived on-the-fly
        )

        # Save the agent configuration (without critic)
        self.save(agent)

        # Now add critic on-the-fly for the returned agent (not persisted)
        cli_settings = CliSettings.load()
        critic = get_default_critic(
            llm, enable_critic=cli_settings.critic.enable_critic
        )
        if critic is not None:
            agent = agent.model_copy(update={"critic": critic})

        return agent
