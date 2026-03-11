"""Fixtures for MCP utils tests."""

import pytest
from acp.schema import EnvVariable, HttpHeader, HttpMcpServer, SseMcpServer, StdioMcpServer


@pytest.fixture
def stdio_server():
    """Create a StdioMcpServer instance."""
    return StdioMcpServer(
        name="test_stdio",
        type="stdio",
        command="python -m test_module",
        args=[],
        env=[EnvVariable(name="DEBUG", value="true")],
    )


@pytest.fixture
def http_server():
    """Create an HttpMcpServer instance."""
    return HttpMcpServer(
        name="test_http",
        type="http",
        url="http://localhost:8000",
        headers=[HttpHeader(name="Authorization", value="Bearer token")],
    )


@pytest.fixture
def sse_server():
    """Create an SseMcpServer instance."""
    return SseMcpServer(
        name="test_sse",
        type="sse",
        url="http://localhost:9000/sse",
        headers=[],
    )
