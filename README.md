# Multi-Agent Collaboration System

A Python-based multi-agent collaboration system featuring voice net protocol communication, squad-based coordination, and MCP tool integration.

## Features

- **Multi-Agent Architecture**: 1-6 AI agents plus user communication via shared text channel
- **Squad Leader Coordination**: One agent acts as squad leader to coordinate team activities
- **Voice Net Protocol**: Pilot-ATC style communication with callsigns and structured messaging
- **🚀 MCP Integration**: Agents can use real tools via Model Context Protocol
  - **Aerospace MCP**: 30+ aerospace engineering tools (flight planning, performance, orbits, etc.)
  - Extensible to any MCP server
- **State Management**: Save and restore session state
- **Flexible Configuration**: YAML-based configuration with Pydantic validation

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Basic Demo
```bash
# Run the demo with 2 agents
python -m src.cli.main demo

# Start interactive session
python -m src.cli.main start --config configs/default.yaml
```

### Aerospace MCP Demo
```bash
# NEW: Multi-agent system with real aerospace engineering tools!
export ANTHROPIC_API_KEY='your-key-here'
python demo_aerospace.py
```

This demonstrates agents using 30+ real aerospace tools via MCP:
- Flight planning with fuel estimates
- Aircraft performance calculations
- Airport database queries
- Atmospheric modeling
- Orbital mechanics
- And much more!

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

See example configurations:
- `configs/default.yaml` - Basic 2-agent setup
- `configs/demo.yaml` - 4-agent specialized squad
- `configs/aerospace.yaml` - Aerospace engineering team with MCP tools

## MCP Integration

The system now integrates with Model Context Protocol servers! Agents can access real tools and capabilities:

**Current Integration: Aerospace MCP**
- Flight planning and navigation
- Aircraft performance analysis
- Atmospheric modeling
- Orbital mechanics calculations
- Aerodynamic analysis
- Rocket trajectory optimization

See `docs/MCP_INTEGRATION.md` for full documentation on:
- How to connect MCP servers
- Available tools
- Creating MCP-powered agents
- Adding new servers

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
