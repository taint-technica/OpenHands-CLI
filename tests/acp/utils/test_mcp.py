"""Unit tests for openhands_cli.acp_impl.utils.mcp module."""

import pytest
from acp.schema import HttpMcpServer, SseMcpServer, StdioMcpServer

from openhands_cli.acp_impl.utils.mcp import (
    _convert_env_to_dict,
    convert_acp_mcp_servers_to_agent_format,
)


class TestConvertEnvToDict:
    """Test suite for _convert_env_to_dict function."""

    def test_should_convert_single_env_var_to_dict(self):
        """Test conversion of single environment variable to dictionary."""
        # Arrange
        env_list = [{"name": "DEBUG", "value": "true"}]

        # Act
        result = _convert_env_to_dict(env_list)

        # Assert
        assert result == {"DEBUG": "true"}

    def test_should_convert_multiple_env_vars_to_dict(self):
        """Test conversion of multiple environment variables to dictionary."""
        # Arrange
        env_list = [
            {"name": "DEBUG", "value": "true"},
            {"name": "PORT", "value": "8000"},
            {"name": "HOST", "value": "localhost"},
        ]

        # Act
        result = _convert_env_to_dict(env_list)

        # Assert
        assert result == {
            "DEBUG": "true",
            "PORT": "8000",
            "HOST": "localhost",
        }

    def test_should_return_empty_dict_for_empty_env_list(self):
        """Test conversion of empty environment list returns empty dict."""
        # Arrange
        env_list = []

        # Act
        result = _convert_env_to_dict(env_list)

        # Assert
        assert result == {}

    def test_should_handle_env_vars_with_special_characters(self):
        """Test conversion of environment variables with special characters."""
        # Arrange
        env_list = [
            {"name": "CONN_STR", "value": "postgresql://user:pass@localhost/db"},
            {"name": "API_KEY", "value": "sk-1234567890abcdef!@#$%"},
        ]

        # Act
        result = _convert_env_to_dict(env_list)

        # Assert
        assert result == {
            "CONN_STR": "postgresql://user:pass@localhost/db",
            "API_KEY": "sk-1234567890abcdef!@#$%",
        }

    def test_should_handle_env_vars_with_empty_values(self):
        """Test conversion of environment variables with empty values."""
        # Arrange
        env_list = [
            {"name": "EMPTY_VAR", "value": ""},
            {"name": "NORMAL_VAR", "value": "value"},
        ]

        # Act
        result = _convert_env_to_dict(env_list)

        # Assert
        assert result == {
            "EMPTY_VAR": "",
            "NORMAL_VAR": "value",
        }


class TestConvertAcpMcpServersToAgentFormat:
    """Test suite for convert_acp_mcp_servers_to_agent_format function."""

    def test_should_convert_stdio_server_with_correct_transport(
        self, stdio_server
    ):
        """Test conversion of StdioMcpServer adds correct transport type."""
        # Arrange
        mcp_servers = [stdio_server]

        # Act
        result = convert_acp_mcp_servers_to_agent_format(mcp_servers)

        # Assert
        assert "test_stdio" in result
        assert result["test_stdio"]["transport"] == "stdio"
        assert result["test_stdio"]["command"] == "python -m test_module"

    def test_should_convert_http_server_with_correct_transport(self, http_server):
        """Test conversion of HttpMcpServer adds correct transport type."""
        # Arrange
        mcp_servers = [http_server]

        # Act
        result = convert_acp_mcp_servers_to_agent_format(mcp_servers)

        # Assert
        assert "test_http" in result
        assert result["test_http"]["transport"] == "http"
        assert result["test_http"]["url"] == "http://localhost:8000"

    def test_should_convert_sse_server_with_correct_transport(self, sse_server):
        """Test conversion of SseMcpServer adds correct transport type."""
        # Arrange
        mcp_servers = [sse_server]

        # Act
        result = convert_acp_mcp_servers_to_agent_format(mcp_servers)

        # Assert
        assert "test_sse" in result
        assert result["test_sse"]["transport"] == "sse"
        assert result["test_sse"]["url"] == "http://localhost:9000/sse"

    def test_should_convert_server_env_array_to_dict(self, stdio_server):
        """Test conversion of server env array format to dictionary format."""
        # Arrange
        mcp_servers = [stdio_server]

        # Act
        result = convert_acp_mcp_servers_to_agent_format(mcp_servers)

        # Assert
        assert "env" in result["test_stdio"]
        assert isinstance(result["test_stdio"]["env"], dict)
        assert result["test_stdio"]["env"] == {"DEBUG": "true"}

    def test_should_handle_empty_server_list(self):
        """Test conversion of empty server list returns empty dict."""
        # Arrange
        mcp_servers = []

        # Act
        result = convert_acp_mcp_servers_to_agent_format(mcp_servers)

        # Assert
        assert result == {}

    def test_should_convert_multiple_mixed_servers(
        self, stdio_server, http_server, sse_server
    ):
        """Test conversion of mixed server types in single call."""
        # Arrange
        mcp_servers = [stdio_server, http_server, sse_server]

        # Act
        result = convert_acp_mcp_servers_to_agent_format(mcp_servers)

        # Assert
        assert len(result) == 3
        assert result["test_stdio"]["transport"] == "stdio"
        assert result["test_http"]["transport"] == "http"
        assert result["test_sse"]["transport"] == "sse"

    def test_should_exclude_name_field_from_converted_config(self, stdio_server):
        """Test that name field is used as key and excluded from config."""
        # Arrange
        mcp_servers = [stdio_server]

        # Act
        result = convert_acp_mcp_servers_to_agent_format(mcp_servers)

        # Assert
        server_config = result["test_stdio"]
        assert "name" not in server_config
        assert "command" in server_config
        assert "env" in server_config

    def test_should_preserve_all_server_fields_except_name(self):
        """Test that all server fields are preserved except name."""
        # Arrange
        server = StdioMcpServer(
            name="test_server",
            type="stdio",
            command="test command",
            args=[],
            env=[
                {"name": "VAR1", "value": "value1"},
                {"name": "VAR2", "value": "value2"},
            ],
        )
        mcp_servers = [server]

        # Act
        result = convert_acp_mcp_servers_to_agent_format(mcp_servers)

        # Assert
        config = result["test_server"]
        assert config["command"] == "test command"
        assert config["env"] == {"VAR1": "value1", "VAR2": "value2"}
        assert config["transport"] == "stdio"
        assert "name" not in config

    def test_should_handle_http_server_with_empty_headers(self):
        """Test conversion of HttpMcpServer with empty headers list."""
        # Arrange
        server = HttpMcpServer(
            name="test_http_no_headers",
            type="http",
            url="http://localhost:3000",
            headers=[],
        )
        mcp_servers = [server]

        # Act
        result = convert_acp_mcp_servers_to_agent_format(mcp_servers)

        # Assert
        assert "test_http_no_headers" in result
        assert result["test_http_no_headers"]["headers"] == []

    def test_should_handle_servers_without_env(self):
        """Test conversion of servers without env field."""
        # Arrange
        server = HttpMcpServer(
            name="test_no_env",
            type="http",
            url="http://localhost:5000",
            headers=[],
        )
        mcp_servers = [server]

        # Act
        result = convert_acp_mcp_servers_to_agent_format(mcp_servers)

        # Assert
        assert "test_no_env" in result
        assert "env" not in result["test_no_env"]


class TestIntegrationScenarios:
    """Integration tests for complete MCP server conversion workflows."""

    def test_should_handle_real_world_mcp_server_configuration(self):
        """Test conversion with realistic MCP server configuration."""
        # Arrange
        servers = [
            StdioMcpServer(
                name="local-tool",
                type="stdio",
                command="/usr/bin/python3 /opt/mcp/tool.py",
                args=[],
                env=[
                    {"name": "LOG_LEVEL", "value": "INFO"},
                    {"name": "TIMEOUT", "value": "30"},
                ],
            ),
            HttpMcpServer(
                name="remote-api",
                type="http",
                url="https://api.example.com/mcp",
                headers=[
                    {"name": "Authorization", "value": "Bearer sk-12345"},
                    {"name": "Content-Type", "value": "application/json"},
                ],
            ),
        ]

        # Act
        result = convert_acp_mcp_servers_to_agent_format(servers)

        # Assert
        assert len(result) == 2
        assert result["local-tool"]["transport"] == "stdio"
        assert result["local-tool"]["env"] == {"LOG_LEVEL": "INFO", "TIMEOUT": "30"}
        assert result["remote-api"]["transport"] == "http"
        assert result["remote-api"]["url"] == "https://api.example.com/mcp"

    def test_should_maintain_header_structure_in_http_server(self):
        """Test that headers structure is preserved in HTTP server conversion."""
        # Arrange
        server = HttpMcpServer(
            name="api-server",
            type="http",
            url="http://localhost:8080",
            headers=[
                {"name": "X-Custom-Header", "value": "custom-value"},
                {"name": "Authorization", "value": "Bearer token123"},
            ],
        )
        mcp_servers = [server]

        # Act
        result = convert_acp_mcp_servers_to_agent_format(mcp_servers)

        # Assert
        headers = result["api-server"]["headers"]
        assert len(headers) == 2
        assert headers[0]["name"] == "X-Custom-Header"
        assert headers[1]["name"] == "Authorization"

    def test_should_handle_duplicate_env_var_names_last_value_wins(self):
        """Test behavior when env list has duplicate variable names."""
        # Arrange
        env_list = [
            {"name": "DUPLICATE", "value": "first"},
            {"name": "DUPLICATE", "value": "second"},
        ]

        # Act
        result = _convert_env_to_dict(env_list)

        # Assert
        assert result == {"DUPLICATE": "second"}