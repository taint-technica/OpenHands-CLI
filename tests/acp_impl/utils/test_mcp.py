"""Unit tests for MCP utilities in ACP implementation."""

import pytest
from acp.schema import EnvVariable, HttpMcpServer, SseMcpServer, StdioMcpServer

from openhands_cli.acp_impl.utils.mcp import (
    _convert_env_to_dict,
    convert_acp_mcp_servers_to_agent_format,
)


@pytest.fixture
def env_list_multiple():
    """Fixture providing a list of multiple environment variables."""
    return [
        {"name": "VAR1", "value": "value1"},
        {"name": "VAR2", "value": "value2"},
        {"name": "VAR3", "value": "value3"},
    ]


@pytest.fixture
def env_vars_pydantic():
    """Fixture providing Pydantic EnvVariable objects."""
    return [
        EnvVariable(name="PATH", value="/usr/bin"),
        EnvVariable(name="DEBUG", value="true"),
    ]


@pytest.fixture
def stdio_server_with_env(env_vars_pydantic):
    """Fixture providing a StdioMcpServer with environment variables."""
    return StdioMcpServer(
        name="test_stdio_server",
        command="/path/to/command",
        args=["arg1", "arg2"],
        env=env_vars_pydantic,
    )


class TestConvertEnvToDict:
    """Tests for _convert_env_to_dict function."""

    def test_should_convert_env_list_to_dict_when_valid_input(self, env_list_multiple):
        """Should convert list of env dicts to a single dictionary."""
        # Act
        result = _convert_env_to_dict(env_list_multiple)

        # Assert
        assert result == {"VAR1": "value1", "VAR2": "value2", "VAR3": "value3"}
        assert len(result) == 3

    def test_should_return_empty_dict_when_env_list_is_empty(self):
        """Should return empty dict for empty input list."""
        # Act
        result = _convert_env_to_dict([])

        # Assert
        assert result == {}
        assert isinstance(result, dict)

    def test_should_convert_single_env_var_when_list_has_one_element(self):
        """Should handle single environment variable correctly."""
        # Arrange
        env_list = [{"name": "SINGLE_VAR", "value": "single_value"}]

        # Act
        result = _convert_env_to_dict(env_list)

        # Assert
        assert result == {"SINGLE_VAR": "single_value"}
        assert len(result) == 1


class TestConvertAcpMcpServersToAgentFormat:
    """Tests for convert_acp_mcp_servers_to_agent_format function."""

    def test_should_convert_stdio_server_with_env_to_agent_format(
        self, stdio_server_with_env
    ):
        """Should convert StdioMcpServer with env vars to agent format."""
        # Act
        result = convert_acp_mcp_servers_to_agent_format([stdio_server_with_env])

        # Assert
        assert "test_stdio_server" in result
        assert result["test_stdio_server"]["transport"] == "stdio"
        assert result["test_stdio_server"]["command"] == "/path/to/command"
        assert result["test_stdio_server"]["args"] == ["arg1", "arg2"]
        assert result["test_stdio_server"]["env"] == {
            "PATH": "/usr/bin",
            "DEBUG": "true",
        }
        assert "name" not in result["test_stdio_server"]

    def test_should_convert_http_and_sse_servers_with_correct_transport_types(self):
        """Should set correct transport type for HTTP and SSE servers."""
        # Arrange
        http_server = HttpMcpServer(
            name="http_server",
            url="http://localhost:8000",
            headers=[],
            type="http",
        )
        sse_server = SseMcpServer(
            name="sse_server",
            url="http://localhost:9000",
            headers=[],
            type="sse",
        )

        # Act
        result = convert_acp_mcp_servers_to_agent_format([http_server, sse_server])

        # Assert
        assert result["http_server"]["transport"] == "http"
        assert result["http_server"]["url"] == "http://localhost:8000"
        assert result["sse_server"]["transport"] == "sse"
        assert result["sse_server"]["url"] == "http://localhost:9000"
        assert "name" not in result["http_server"]
        assert "name" not in result["sse_server"]

    def test_should_handle_servers_without_env_field(self):
        """Should handle servers that don't have env field."""
        # Arrange
        server_no_env = HttpMcpServer(
            name="no_env_server",
            url="http://localhost:8000",
            headers=[],
            type="http",
        )

        # Act
        result = convert_acp_mcp_servers_to_agent_format([server_no_env])

        # Assert
        assert "no_env_server" in result
        assert "env" not in result["no_env_server"]
        assert result["no_env_server"]["transport"] == "http"
        assert result["no_env_server"]["url"] == "http://localhost:8000"
        assert "name" not in result["no_env_server"]

    def test_should_return_empty_dict_when_server_list_is_empty(self):
        """Should return empty dict for empty server list."""
        # Act
        result = convert_acp_mcp_servers_to_agent_format([])

        # Assert
        assert result == {}
        assert isinstance(result, dict)

    def test_should_convert_all_server_types_with_correct_transport(self):
        """Should convert all server types and assign correct transport."""
        # Arrange
        stdio_server = StdioMcpServer(
            name="stdio_server",
            command="/path/to/command",
            args=["arg1"],
            env=[],
        )
        http_server = HttpMcpServer(
            name="http_server",
            url="http://localhost:8000",
            headers=[],
            type="http",
        )
        sse_server = SseMcpServer(
            name="sse_server",
            url="http://localhost:9000",
            headers=[],
            type="sse",
        )

        # Act
        result = convert_acp_mcp_servers_to_agent_format(
            [stdio_server, http_server, sse_server]
        )

        # Assert
        assert len(result) == 3
        assert result["stdio_server"]["transport"] == "stdio"
        assert result["http_server"]["transport"] == "http"
        assert result["sse_server"]["transport"] == "sse"
        assert "name" not in result["stdio_server"]
        assert "name" not in result["http_server"]
        assert "name" not in result["sse_server"]

    def test_should_convert_env_array_to_dict_in_server_config(self):
        """Should convert env array to dict format in server config."""
        # Arrange
        env_vars = [
            EnvVariable(name="VAR1", value="value1"),
            EnvVariable(name="VAR2", value="value2"),
            EnvVariable(name="VAR3", value="value3"),
        ]
        server = StdioMcpServer(
            name="test_server",
            command="/path/to/command",
            args=[],
            env=env_vars,
        )

        # Act
        result = convert_acp_mcp_servers_to_agent_format([server])

        # Assert
        assert "test_server" in result
        assert isinstance(result["test_server"]["env"], dict)
        assert result["test_server"]["env"] == {
            "VAR1": "value1",
            "VAR2": "value2",
            "VAR3": "value3",
        }
        assert result["test_server"]["transport"] == "stdio"

    def test_should_exclude_name_field_and_preserve_other_fields(self):
        """Should exclude name field while preserving other server fields."""
        # Arrange
        server = StdioMcpServer(
            name="my_server",
            command="/usr/bin/python",
            args=["--verbose", "--debug"],
            env=[EnvVariable(name="PATH", value="/usr/bin")],
        )

        # Act
        result = convert_acp_mcp_servers_to_agent_format([server])

        # Assert
        assert "my_server" in result
        server_config = result["my_server"]
        assert "name" not in server_config
        assert server_config["command"] == "/usr/bin/python"
        assert server_config["args"] == ["--verbose", "--debug"]
        assert server_config["env"] == {"PATH": "/usr/bin"}
        assert server_config["transport"] == "stdio"
