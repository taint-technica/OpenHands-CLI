---
name: openhands_cli_guide
triggers: ["openhands", "cli", "terminal"]
description: Guide for using OpenHands CLI
---

# OpenHands CLI Guide

## Overview
OpenHands CLI is a terminal-based interface for interacting with the OpenHands AI agent. It provides a powerful way to get coding assistance directly in your terminal.

## Quick Start

### Installation
```bash
# Using uv (recommended)
uv tool install openhands --python 3.12

# Or using pip
pip install openhands
```

### Basic Usage
```bash
# Start interactive mode
openhands

# Run a task directly
openhands -t "Write a Python function to sort a list"

# Headless mode (no TUI)
openhands --headless -t "Create a Flask app"
```

## Key Features

### 1. Interactive TUI Mode
- Full terminal user interface with Textual
- Real-time conversation with the agent
- View action history and metrics

### 2. Headless Mode
- Perfect for CI/CD pipelines
- Scriptable automation
- JSON output option

### 3. MCP Servers
Extend capabilities with Model Context Protocol servers:
```bash
# List configured servers
openhands mcp list

# Add a server
openhands mcp add <server-name> --transport stdio <command>
```

### 4. Confirmation Modes
Control how the agent handles actions:
```bash
# Default: ask for confirmation
openhands

# Auto-approve all actions
openhands --always-approve  # or --yolo

# LLM-based security analyzer
openhands --llm-approve
```

## Configuration

OpenHands CLI stores configuration under `~/.openhands/`:
- `agent_settings.json`: Agent configuration
- `cli_config.json`: CLI/TUI preferences
- `mcp.json`: MCP server configuration

## Tips for Best Results

1. **Be specific**: Provide clear, detailed task descriptions
2. **Context matters**: Run from the project directory
3. **Review changes**: Always review code changes before accepting
4. **Use headless for automation**: Perfect for CI/CD pipelines

## Common Commands

```bash
# Resume last conversation
openhands --resume --last

# View conversation history
openhands view <conversation-id>

# Login to OpenHands Cloud
openhands login

# Run web interface
openhands web
```

## Troubleshooting

### Issue: Terminal compatibility
```bash
# Set TTY interactive mode
export TTY_INTERACTIVE=1
```

### Issue: Missing environment variables
```bash
# Set required variables
export LLM_API_KEY=your-api-key
export LLM_MODEL=claude-sonnet-4-5-20250929
```

## Documentation
For complete documentation, visit: https://docs.openhands.dev/openhands/usage/cli
