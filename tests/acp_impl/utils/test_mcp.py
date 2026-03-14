"""Unit tests for openhands_cli.acp_impl.utils.mcp module."""

from acp.schema import (
    EnvVariable,
    HttpHeader,
    HttpMcpServer,
    SseMcpServer,
    StdioMcpServer,
)

from openhands_cli.acp_impl.utils.mcp import (
    _convert_env_to_dict,
    convert_acp_mcp_servers_to_agent_format,
)


class TestConvertEnvToDict:
    """Test cases for _convert_env_to_dict function."""

    def test_empty_env_list(self):
        """Test conversion of empty environment list."""
        result = _convert_env_to_dict([])
        assert result == {}

    def test_single_env_variable(self):
        """Test conversion of a single environment variable."""
        env = [{"name": "API_KEY", "value": "secret123"}]
        result = _convert_env_to_dict(env)
        assert result == {"API_KEY": "secret123"}

    def test_multiple_env_variables(self):
        """Test conversion of multiple environment variables."""
        env = [
            {"name": "API_KEY", "value": "secret123"},
            {"name": "DATABASE_URL", "value": "postgres://localhost"},
            {"name": "DEBUG", "value": "true"},
        ]
        result = _convert_env_to_dict(env)
        assert result == {
            "API_KEY": "secret123",
            "DATABASE_URL": "postgres://localhost",
            "DEBUG": "true",
        }

    def test_env_with_special_characters(self):
        """Test conversion of environment variables with special characters."""
        env = [
            {"name": "SECRET_VAR", "value": "p@$$w0rd!#%"},
            {
                "name": "CONNECTION_STRING",
                "value": "mongodb+srv://user:pass@host/?retryWrites=true",
            },
        ]
        result = _convert_env_to_dict(env)
        assert result == {
            "SECRET_VAR": "p@$$w0rd!#%",
            "CONNECTION_STRING": "mongodb+srv://user:pass@host/?retryWrites=true",
        }

    def test_env_with_empty_value(self):
        """Test conversion of environment variable with empty value."""
        env = [{"name": "EMPTY_VAR", "value": ""}]
        result = _convert_env_to_dict(env)
        assert result == {"EMPTY_VAR": ""}


class TestConvertAcpMcpServersToAgentFormat:
    """Test cases for convert_acp_mcp_servers_to_agent_format function."""

    def test_empty_server_list(self):
        """Test conversion of empty MCP server list."""
        result = convert_acp_mcp_servers_to_agent_format([])
        assert result == {}

    def test_stdio_mcp_server_conversion(self):
        """Test conversion of StdioMcpServer to agent format."""
        servers = [
            StdioMcpServer(
                name="stdio-server",
                command="python",
                args=["-m", "server_module"],
                env=[],
            )
        ]
        result = convert_acp_mcp_servers_to_agent_format(servers)

        assert "stdio-server" in result
        server_config = result["stdio-server"]
        assert server_config["command"] == "python"
        assert server_config["args"] == ["-m", "server_module"]
        assert server_config["transport"] == "stdio"
        assert "name" not in server_config

    def test_http_mcp_server_conversion(self):
        """Test conversion of HttpMcpServer to agent format."""
        servers = [
            HttpMcpServer(
                name="http-server",
                url="http://localhost:8000",
                type="http",
                headers=[],
            )
        ]
        result = convert_acp_mcp_servers_to_agent_format(servers)

        assert "http-server" in result
        server_config = result["http-server"]
        assert server_config["url"] == "http://localhost:8000"
        assert server_config["transport"] == "http"
        assert "name" not in server_config

    def test_sse_mcp_server_conversion(self):
        """Test conversion of SseMcpServer to agent format."""
        servers = [
            SseMcpServer(
                name="sse-server",
                url="http://localhost:8001",
                type="sse",
                headers=[],
            )
        ]
        result = convert_acp_mcp_servers_to_agent_format(servers)

        assert "sse-server" in result
        server_config = result["sse-server"]
        assert server_config["url"] == "http://localhost:8001"
        assert server_config["transport"] == "sse"
        assert "name" not in server_config

    def test_server_with_env_variables(self):
        """Test conversion of server with environment variables."""
        servers = [
            StdioMcpServer(
                name="server-with-env",
                command="python",
                args=["-m", "server"],
                env=[
                    EnvVariable(name="API_KEY", value="test-key"),
                    EnvVariable(name="LOG_LEVEL", value="DEBUG"),
                ],
            )
        ]
        result = convert_acp_mcp_servers_to_agent_format(servers)

        server_config = result["server-with-env"]
        assert server_config["env"] == {
            "API_KEY": "test-key",
            "LOG_LEVEL": "DEBUG",
        }
        assert server_config["transport"] == "stdio"

    def test_multiple_mixed_servers(self):
        """Test conversion of multiple servers of different types."""
        servers = [
            StdioMcpServer(
                name="stdio-tool",
                command="python",
                args=["-m", "stdio_impl"],
                env=[],
            ),
            HttpMcpServer(
                name="http-tool",
                url="http://localhost:8000",
                type="http",
                headers=[],
            ),
            SseMcpServer(
                name="sse-tool",
                url="http://localhost:8001",
                type="sse",
                headers=[],
            ),
        ]
        result = convert_acp_mcp_servers_to_agent_format(servers)

        assert len(result) == 3
        assert result["stdio-tool"]["transport"] == "stdio"
        assert result["stdio-tool"]["command"] == "python"
        assert result["http-tool"]["transport"] == "http"
        assert result["http-tool"]["url"] == "http://localhost:8000"
        assert result["sse-tool"]["transport"] == "sse"
        assert result["sse-tool"]["url"] == "http://localhost:8001"

    def test_server_preserves_all_fields(self):
        """Test that conversion preserves all server fields except name."""
        servers = [
            StdioMcpServer(
                name="full-server",
                command="node",
                args=["server.js", "--port", "9000"],
                env=[EnvVariable(name="NODE_ENV", value="production")],
            )
        ]
        result = convert_acp_mcp_servers_to_agent_format(servers)

        server_config = result["full-server"]
        assert server_config["command"] == "node"
        assert server_config["args"] == ["server.js", "--port", "9000"]
        assert server_config["env"] == {"NODE_ENV": "production"}
        assert server_config["transport"] == "stdio"
        assert "name" not in server_config

    def test_server_without_env(self):
        """Test conversion of server without environment variables."""
        servers = [
            HttpMcpServer(
                name="simple-http",
                url="https://api.example.com",
                type="http",
                headers=[],
            )
        ]
        result = convert_acp_mcp_servers_to_agent_format(servers)

        server_config = result["simple-http"]
        assert "env" not in server_config or server_config.get("env") is None or server_config.get("env") == {}
        assert server_config["transport"] == "http"

    def test_server_name_with_special_characters(self):
        """Test server with special characters in name."""
        servers = [
            StdioMcpServer(
                name="server-with_special.chars-123",
                command="python",
                args=["-m", "server"],
                env=[],
            )
        ]
        result = convert_acp_mcp_servers_to_agent_format(servers)

        assert "server-with_special.chars-123" in result
        assert result["server-with_special.chars-123"]["transport"] == "stdio"
