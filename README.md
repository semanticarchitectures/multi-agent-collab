# Multi-Agent Collaboration System

A Python-based multi-agent collaboration system featuring voice net protocol communication, squad-based coordination, and MCP tool integration.

## Features

- **Multi-Agent Architecture**: 1-6 AI agents plus user communication via shared text channel
- **Squad Leader Coordination**: One agent acts as squad leader to coordinate team activities
- **Voice Net Protocol**: Pilot-ATC style communication with callsigns and structured messaging
- **MCP Integration**: System-wide MCP servers provide tools to all agents
- **State Management**: Save and restore session state
- **Flexible Configuration**: YAML-based configuration with Pydantic validation

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

```bash
# Run the demo with 2 agents
python -m src.cli.main demo

# Start interactive session
python -m src.cli.main start --config configs/default.yaml
```

## Architecture

- **Agents**: Base agent class with specialized squad leader subclass
- **Channel**: Shared communication channel with message history
- **MCP**: Tool integration via MCP Python SDK
- **Orchestration**: Coordinates agent turns and message flow
- **State**: SQLite-based persistence for session management

## Project Structure

```
multi-agent-collab/
├── src/
│   ├── agents/          # Agent implementations
│   ├── channel/         # Communication channel
│   ├── mcp/            # MCP tool integration
│   ├── orchestration/  # Agent coordination
│   ├── config/         # Configuration management
│   ├── state/          # State persistence
│   └── cli/            # Command-line interface
├── tests/              # Unit tests
├── configs/            # Configuration files
└── docs/               # Documentation
```

## Configuration

See `configs/default.yaml` for example configuration with agent definitions and system settings.

## Development

```bash
# Run tests
pytest

# Format code
black src tests

# Lint
ruff src tests
```

## License

MIT
