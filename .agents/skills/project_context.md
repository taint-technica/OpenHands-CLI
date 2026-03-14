---
name: project_context
triggers: []
description: Project-specific context and guidelines
---

# Project Context

## Repository Guidelines

This is the OpenHands-CLI project - a standalone terminal interface for interacting with the OpenHands agent.

## Project Structure

```
OpenHands-CLI/
├── openhands_cli/       # Core CLI/TUI code
│   ├── entrypoint.py    # Main entry point
│   ├── tui/             # Textual TUI components
│   ├── stores/          # State management
│   ├── instructions/    # Developer instructions (hardcoded)
│   └── ...
├── tests/               # Test suite
├── .agents/skills/      # Project skills (this folder)
└── .openhands/          # User configuration
```

## Development Workflow

1. **Setup**: `make install` or `uv sync`
2. **Lint**: `make lint` before committing
3. **Test**: `make test` for unit tests
4. **Build**: `./build_nuitka.sh` for Nuitka compilation

## Code Style

- Python 3.12+
- Ruff formatting (88-char line limit)
- Type hints required
- Double quotes for strings

## Testing

```bash
# Run all tests
make test

# Run snapshot tests
make test-snapshots

# Run binary tests
make test-binary
```

## Building for Distribution

### With Nuitka (Recommended for Protection)
```bash
./build_nuitka.sh
# or
python build_nuitka.py
```

### With PyInstaller
```bash
./build.sh --install-pyinstaller
```

## Key Files

- `openhands_cli/entrypoint.py`: Main CLI entry point
- `openhands_cli/stores/agent_store.py`: Agent configuration
- `openhands_cli/instructions/dev_skills.py`: Developer skills (hardcoded)
- `build_nuitka.sh`: Nuitka build script
