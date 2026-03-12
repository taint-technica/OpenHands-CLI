# Architecture: MCP Utility Module

## Module Overview
`openhands_cli/acp_impl/utils/mcp.py` - Utility functions for converting MCP server configurations between ACP and Agent formats.

## Key Components

### Type Definitions
- `ACPMCPServerType`: Union type representing three MCP server implementations
  - `StdioMcpServer`: Standard I/O based MCP server
  - `HttpMcpServer`: HTTP-based MCP server  
  - `SseMcpServer`: Server-Sent Events based MCP server

### Functions

#### 1. `_convert_env_to_dict(env: Sequence[dict[str, str]]) -> dict[str, str]`
**Purpose**: Internal utility to transform environment variables from array format to dictionary format.

**Input Format**: List of dicts with 'name' and 'value' keys (serialized Pydantic EnvVariable objects)

**Output Format**: Dictionary mapping env var names to values

**Key Logic**:
- Iterates through env array
- Creates key-value mapping using 'name' and 'value' fields

#### 2. `convert_acp_mcp_servers_to_agent_format(mcp_servers: Sequence[ACPMCPServerType]) -> dict[str, dict[str, Any]]`
**Purpose**: Convert MCP servers from ACP Pydantic models to Agent format.

**Input**: List of MCP server Pydantic models from ACP

**Output**: Dictionary keyed by server name with Agent-compatible configuration

**Key Transformations**:
1. Serializes Pydantic model to dict using `model_dump()`
2. Extracts server name from dict
3. Removes 'name' field from config dict
4. Converts 'env' array to dict using helper function
5. Adds 'transport' field based on server instance type:
   - `StdioMcpServer` → `"stdio"`
   - `HttpMcpServer` → `"http"`
   - `SseMcpServer` → `"sse"`

## Testing Requirements

### Test Coverage Goals
- All code paths in both functions
- Different MCP server types (Stdio, Http, Sse)
- Empty environment variables
- Multiple servers in batch conversion
- Edge cases: None values, empty sequences

### Dependencies
- `acp.schema`: Pydantic models (StdioMcpServer, HttpMcpServer, SseMcpServer)

### Test Strategy
- Unit tests for `_convert_env_to_dict()` with various env formats
- Unit tests for `convert_acp_mcp_servers_to_agent_format()` with:
  - Each server type
  - Multiple servers
  - Varying env configurations
  - Empty inputs
