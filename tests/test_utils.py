"""Tests for utility functions."""

import json
import os
from argparse import Namespace
from unittest.mock import Mock, patch

import pytest
from acp.schema import EnvVariable, StdioMcpServer

from openhands.sdk.event import MessageEvent, SystemPromptEvent
from openhands.sdk.llm import Message, TextContent
from openhands_cli.acp_impl.utils import convert_acp_mcp_servers_to_agent_format
from openhands_cli.utils import (
    abbreviate_number,
    create_seeded_instructions_from_args,
    extract_text_from_message_content,
    format_cost,
    get_default_cli_tools,
    get_llm_metadata,
    get_os_description,
    json_callback,
    should_set_litellm_extra_body,
)


def test_get_default_cli_tools_returns_expected_tools():
    """Test that get_default_cli_tools returns exactly the expected tools."""
    tools = get_default_cli_tools()
    tool_names = {t.name for t in tools}
    assert tool_names == {"terminal", "file_editor", "task_tracker", "delegate"}


def test_should_set_litellm_extra_body_for_openhands():
    """Test that litellm_extra_body is set for openhands models."""
    assert should_set_litellm_extra_body("openhands/claude-sonnet-4-5-20250929")
    assert should_set_litellm_extra_body("openhands/gpt-5-2025-08-07")
    assert should_set_litellm_extra_body("openhands/devstral-small-2507")


def test_should_set_litellm_extra_body_for_llm_proxy_base_url():
    """Test that litellm_extra_body is set for models using llm-proxy base URLs."""
    # Any model using llm-proxy.*.all-hands.dev should get metadata
    assert should_set_litellm_extra_body(
        "gpt-4", "https://llm-proxy.app.all-hands.dev/"
    )
    assert should_set_litellm_extra_body(
        "anthropic/claude-3", "https://llm-proxy.app.all-hands.dev/v1"
    )
    assert should_set_litellm_extra_body(
        "openai/gpt-4", "https://llm-proxy.staging.all-hands.dev/"
    )
    assert should_set_litellm_extra_body(
        "custom-model", "https://llm-proxy.dev.all-hands.dev/api"
    )


def test_should_not_set_litellm_extra_body_for_other_models():
    """Test that litellm_extra_body is not set for non-openhands models."""
    assert not should_set_litellm_extra_body("gpt-4")
    assert not should_set_litellm_extra_body("anthropic/claude-3")
    assert not should_set_litellm_extra_body("openai/gpt-4")
    assert not should_set_litellm_extra_body("cerebras/llama3.1-8b")
    assert not should_set_litellm_extra_body("vllm/model")
    assert not should_set_litellm_extra_body("dummy-model")
    assert not should_set_litellm_extra_body("litellm_proxy/gpt-4")


def test_should_not_set_litellm_extra_body_for_other_base_urls():
    """Test that litellm_extra_body is not set for non-OpenHands base URLs."""
    assert not should_set_litellm_extra_body("gpt-4", "https://api.openai.com/")
    assert not should_set_litellm_extra_body("claude-3", "https://api.anthropic.com/v1")
    assert not should_set_litellm_extra_body(
        "model", "https://example.com/llm-proxy.app.all-hands.dev/"
    )
    assert not should_set_litellm_extra_body("model", "https://all-hands.dev/")
    assert not should_set_litellm_extra_body("model", None)


def test_convert_acp_mcp_servers_empty_list():
    """Test converting empty list of MCP servers."""
    result = convert_acp_mcp_servers_to_agent_format([])
    assert result == {}


def test_convert_acp_mcp_servers_with_empty_env():
    """Test converting MCP server with empty env array."""
    servers = [
        StdioMcpServer(
            name="test-server",
            command="/usr/bin/node",
            args=["server.js"],
            env=[],
        )
    ]
    result = convert_acp_mcp_servers_to_agent_format(servers)

    assert "test-server" in result
    assert result["test-server"]["command"] == "/usr/bin/node"
    assert result["test-server"]["args"] == ["server.js"]
    assert result["test-server"]["env"] == {}
    assert result["test-server"]["transport"] == "stdio"
    assert "name" not in result["test-server"]


def test_convert_acp_mcp_servers_with_env_variables():
    """Test converting MCP server with env variables."""
    servers = [
        StdioMcpServer(
            name="test-server",
            command="/usr/bin/python",
            args=["-m", "server"],
            env=[
                EnvVariable(name="API_KEY", value="secret123"),
                EnvVariable(name="DEBUG", value="true"),
            ],
        )
    ]
    result = convert_acp_mcp_servers_to_agent_format(servers)

    assert "test-server" in result
    assert result["test-server"]["env"] == {
        "API_KEY": "secret123",
        "DEBUG": "true",
    }


def test_convert_acp_mcp_servers_multiple_servers():
    """Test converting multiple MCP servers."""
    servers = [
        StdioMcpServer(
            name="server1",
            command="/usr/bin/node",
            args=["server1.js"],
            env=[],
        ),
        StdioMcpServer(
            name="server2",
            command="/usr/bin/python",
            args=["-m", "server2"],
            env=[EnvVariable(name="KEY", value="value")],
        ),
    ]
    result = convert_acp_mcp_servers_to_agent_format(servers)

    assert len(result) == 2
    assert "server1" in result
    assert "server2" in result
    assert result["server1"]["env"] == {}
    assert result["server2"]["env"] == {"KEY": "value"}


def test_seeded_instructions_task_only():
    args = Namespace(command=None, task="Do something", file=None)
    assert create_seeded_instructions_from_args(args) == ["Do something"]


def test_seeded_instructions_file_only(tmp_path):
    path = tmp_path / "context.txt"
    path.write_text("hello", encoding="utf-8")

    args = Namespace(command=None, task=None, file=str(path))
    queued = create_seeded_instructions_from_args(args)

    assert isinstance(queued, list)
    assert len(queued) == 1
    assert "File path:" in queued[0]


class TestJsonCallback:
    """Minimal tests for json_callback function core behavior."""

    def test_json_callback_filters_system_events_and_outputs_others(self):
        """Test that SystemPromptEvent is filtered and other events output as JSON."""
        # Test SystemPromptEvent filtering
        system_event = SystemPromptEvent(
            system_prompt=TextContent(text="test prompt"), tools=[], source="agent"
        )

        with patch("builtins.print") as mock_print:
            json_callback(system_event)
            mock_print.assert_not_called()

        # Test non-system event JSON output
        message_event = MessageEvent(
            llm_message=Message(
                role="user", content=[TextContent(text="test message")]
            ),
            source="user",
        )

        with patch("builtins.print") as mock_print:
            json_callback(message_event)

            # Should have two print calls: header and JSON
            assert mock_print.call_count == 2
            mock_print.assert_any_call("--JSON Event--")

            # Verify valid JSON output
            json_output = mock_print.call_args_list[1][0][0]
            parsed_json = json.loads(json_output)
            assert isinstance(parsed_json, dict)

    def test_json_callback_real_message_event_processing(self):
        """Test json_callback with realistic MessageEvent processing."""
        event = MessageEvent(
            llm_message=Message(
                role="user", content=[TextContent(text="Hello, this is a test message")]
            ),
            source="user",
        )

        with patch("builtins.print") as mock_print:
            json_callback(event)

            # Verify the output structure
            assert mock_print.call_count == 2
            mock_print.assert_any_call("--JSON Event--")

            # Get and validate the JSON output
            json_output = mock_print.call_args_list[1][0][0]
            parsed_json = json.loads(json_output)

            # Verify essential fields are present
            assert "llm_message" in parsed_json
            assert "source" in parsed_json
            assert parsed_json["source"] == "user"

            # Check the message content structure
            llm_message = parsed_json["llm_message"]
            assert "content" in llm_message
            content = llm_message["content"]
            assert isinstance(content, list)
            assert len(content) > 0
            assert content[0]["text"] == "Hello, this is a test message"


# ============================================================================
# Tests for abbreviate_number()
# ============================================================================


class TestAbbreviateNumber:
    """Test abbreviate_number function."""

    def test_below_thousand(self):
        """Test that numbers below 1000 are returned as-is."""
        assert abbreviate_number(0) == "0"
        assert abbreviate_number(1) == "1"
        assert abbreviate_number(999) == "999"

    def test_thousands(self):
        """Test abbreviation of thousands."""
        assert abbreviate_number(1000) == "1K"
        assert abbreviate_number(1234) == "1.23K"
        assert abbreviate_number(10000) == "10K"
        assert abbreviate_number(999999) == "1000K"

    def test_millions(self):
        """Test abbreviation of millions."""
        assert abbreviate_number(1_000_000) == "1M"
        assert abbreviate_number(1_200_000) == "1.2M"
        assert abbreviate_number(5_500_000) == "5.5M"

    def test_billions(self):
        """Test abbreviation of billions."""
        assert abbreviate_number(1_000_000_000) == "1B"
        assert abbreviate_number(2_500_000_000) == "2.5B"

    def test_float_input(self):
        """Test with float inputs."""
        assert abbreviate_number(1000.5) == "1K"
        assert abbreviate_number(1234.9) == "1.23K"

    def test_trailing_zeros_stripped(self):
        """Test that trailing zeros are stripped."""
        assert abbreviate_number(1200000) == "1.2M"
        assert abbreviate_number(120000) == "120K"


# ============================================================================
# Tests for format_cost()
# ============================================================================


class TestFormatCost:
    """Test format_cost function."""

    def test_zero(self):
        """Test formatting of zero cost."""
        assert format_cost(0.0) == "0.00"

    def test_negative(self):
        """Test formatting of negative costs."""
        assert format_cost(-0.0001) == "0.00"
        assert format_cost(-1.5) == "0.00"

    def test_positive_small(self):
        """Test formatting of small positive costs."""
        assert format_cost(0.0001) == "0.0001"
        assert format_cost(0.001) == "0.0010"
        assert format_cost(0.01) == "0.0100"

    def test_positive_standard(self):
        """Test formatting of standard positive costs."""
        assert format_cost(1.0) == "1.0000"
        assert format_cost(1.5) == "1.5000"

    def test_positive_large(self):
        """Test formatting of large costs."""
        assert format_cost(100.5) == "100.5000"
        assert format_cost(999.9999) == "999.9999"

    def test_precision(self):
        """Test 4 decimal precision."""
        assert format_cost(0.123456) == "0.1235"
        assert format_cost(1.999999) == "2.0000"


# ============================================================================
# Tests for get_os_description()
# ============================================================================


class TestGetOsDescription:
    """Test get_os_description with mocked platform calls."""

    @patch("platform.system", return_value="Darwin")
    @patch("platform.mac_ver", return_value=("13.5.2", ("", "", ""), ""))
    def test_macos_with_version(self, mock_mac_ver, mock_system):
        """Test macOS description with version."""
        result = get_os_description()
        assert result == "macOS 13.5.2"

    @patch("platform.system", return_value="Darwin")
    @patch("platform.mac_ver", return_value=("", ("", "", ""), ""))
    @patch("platform.release", return_value="22.6.0")
    def test_macos_fallback_release(self, mock_release, mock_mac_ver, mock_system):
        """Test macOS description with fallback to release."""
        result = get_os_description()
        assert result == "macOS 22.6.0"

    @patch("platform.system", return_value="Windows")
    @patch("platform.win32_ver", return_value=("11", "22621", "", ""))
    def test_windows_with_info(self, mock_win32_ver, mock_system):
        """Test Windows description with release and version."""
        result = get_os_description()
        assert result == "Windows 11 (22621)"

    @patch("platform.system", return_value="Windows")
    @patch("platform.win32_ver", return_value=("", "", "", ""))
    def test_windows_no_info(self, mock_win32_ver, mock_system):
        """Test Windows description without info."""
        result = get_os_description()
        assert result == "Windows"

    @patch("platform.system", return_value="Linux")
    @patch("platform.release", return_value="6.1.0-linux")
    def test_linux_with_kernel(self, mock_release, mock_system):
        """Test Linux description with kernel version."""
        result = get_os_description()
        assert result == "Linux (kernel 6.1.0-linux)"

    @patch("platform.system", return_value="Linux")
    @patch("platform.release", return_value="")
    def test_linux_no_kernel(self, mock_release, mock_system):
        """Test Linux description without kernel version."""
        result = get_os_description()
        assert result == "Linux"

    @patch("platform.system", return_value="Unknown")
    @patch("platform.platform", return_value="Unknown-OS-Version")
    def test_unknown_os(self, mock_platform, mock_system):
        """Test unknown OS description."""
        result = get_os_description()
        assert result == "Unknown-OS-Version"


# ============================================================================
# Tests for get_llm_metadata()
# ============================================================================


class TestGetLlmMetadata:
    """Test get_llm_metadata function."""

    def test_basic(self):
        """Test basic metadata generation."""
        metadata = get_llm_metadata(
            model_name="gpt-4",
            llm_type="openai",
        )
        assert "tags" in metadata
        assert any("model:gpt-4" in tag for tag in metadata["tags"])
        assert any("type:openai" in tag for tag in metadata["tags"])

    def test_with_session_id(self):
        """Test with session ID."""
        metadata = get_llm_metadata(
            model_name="claude-3",
            llm_type="anthropic",
            session_id="session-123",
        )
        assert metadata.get("session_id") == "session-123"

    def test_with_user_id(self):
        """Test with user ID."""
        metadata = get_llm_metadata(
            model_name="gpt-4",
            llm_type="openai",
            user_id="user-456",
        )
        assert metadata.get("trace_user_id") == "user-456"

    def test_with_all_optional_fields(self):
        """Test with all optional fields."""
        metadata = get_llm_metadata(
            model_name="claude-sonnet",
            llm_type="anthropic",
            session_id="session-789",
            user_id="user-012",
        )
        assert metadata.get("session_id") == "session-789"
        assert metadata.get("trace_user_id") == "user-012"
        assert "trace_version" in metadata
        assert "tags" in metadata

    def test_without_optional_fields(self):
        """Test without optional fields."""
        metadata = get_llm_metadata(
            model_name="test",
            llm_type="test",
        )
        assert "session_id" not in metadata
        assert "trace_user_id" not in metadata

    @patch.dict(os.environ, {"WEB_HOST": "example.com"})
    def test_tags_structure(self):
        """Test metadata tags structure."""
        metadata = get_llm_metadata(
            model_name="test-model",
            llm_type="test-type",
        )
        tags = metadata["tags"]
        assert isinstance(tags, list)
        assert any("web_host:example.com" in tag for tag in tags)


# ============================================================================
# Tests for extract_text_from_message_content()
# ============================================================================


class TestExtractTextFromMessageContent:
    """Test extract_text_from_message_content function."""

    def test_empty_list(self):
        """Test with empty message content."""
        result = extract_text_from_message_content([])
        assert result is None

    def test_single_text_content(self):
        """Test with single TextContent block."""
        content = [TextContent(text="Hello world")]
        result = extract_text_from_message_content(content)
        assert result == "Hello world"

    def test_multiple_blocks_not_allowed(self):
        """Test that multiple blocks return None by default."""
        content = [
            TextContent(text="First"),
            TextContent(text="Second"),
        ]
        result = extract_text_from_message_content(content)
        assert result is None

    def test_multiple_blocks_allowed(self):
        """Test with multiple blocks when has_exactly_one=False."""
        content = [
            TextContent(text="First"),
            TextContent(text="Second"),
        ]
        result = extract_text_from_message_content(content, has_exactly_one=False)
        assert result == "First"

    def test_non_text_content(self):
        """Test with non-TextContent blocks."""
        mock_content = Mock()
        content = [mock_content]
        result = extract_text_from_message_content(content)
        assert result is None

    def test_empty_string(self):
        """Test with empty text content."""
        content = [TextContent(text="")]
        result = extract_text_from_message_content(content)
        assert result == ""

    def test_special_characters(self):
        """Test with special characters."""
        special_text = "Hello\nWorld\t!@#$%"
        content = [TextContent(text=special_text)]
        result = extract_text_from_message_content(content)
        assert result == special_text

    def test_unicode_content(self):
        """Test with unicode characters."""
        unicode_text = "Hello 世界 🌍 مرحبا мир"
        content = [TextContent(text=unicode_text)]
        result = extract_text_from_message_content(content)
        assert result == unicode_text


# ============================================================================
# Tests for create_seeded_instructions_from_args()
# ============================================================================


class TestCreateSeededInstructionsFromArgs:
    """Test create_seeded_instructions_from_args function."""

    def test_serve_command_returns_none(self):
        """Test that serve command returns None."""
        args = Namespace(command="serve", task=None, file=None)
        result = create_seeded_instructions_from_args(args)
        assert result is None

    def test_task_priority(self):
        """Test that task is used when file is not present."""
        args = Namespace(command=None, task="My task", file=None)
        result = create_seeded_instructions_from_args(args)
        assert result == ["My task"]

    def test_file_takes_precedence(self, tmp_path):
        """Test that file takes precedence over task."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("File content here", encoding="utf-8")

        args = Namespace(command=None, task="Task", file=str(file_path))
        result = create_seeded_instructions_from_args(args)

        assert result is not None
        assert len(result) == 1
        assert "File path:" in result[0]
        assert "File content here" in result[0]

    def test_file_not_found(self):
        """Test error handling when file not found."""
        args = Namespace(command=None, task=None, file="/nonexistent/path.txt")

        with pytest.raises(SystemExit) as exc_info:
            create_seeded_instructions_from_args(args)
        assert exc_info.value.code == 1

    def test_no_inputs(self):
        """Test when no task or file is provided."""
        args = Namespace(command=None, task=None, file=None)
        result = create_seeded_instructions_from_args(args)
        assert result is None

    def test_empty_task(self):
        """Test with empty task string."""
        args = Namespace(command=None, task="", file=None)
        result = create_seeded_instructions_from_args(args)
        assert result is None

    def test_file_format(self, tmp_path):
        """Test the format of file-based instructions."""
        file_path = tmp_path / "instructions.md"
        file_content = "# My Instructions\nDo something important"
        file_path.write_text(file_content, encoding="utf-8")

        args = Namespace(command=None, task=None, file=str(file_path))
        result = create_seeded_instructions_from_args(args)

        message = result[0]
        assert "Starting this session with file context" in message
        assert f"File path: {file_path}" in message
        assert "File contents:" in message
        assert file_content in message
        assert "--------------------" in message
