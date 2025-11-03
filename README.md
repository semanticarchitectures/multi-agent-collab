# 🚁 Multi-Agent Collaboration System

A production-ready multi-agent collaboration system for aviation operations, featuring autonomous tool use, directed communication, persistent memory, and realistic military voice net protocol.

**Status:** Week 1 Complete (P0 & P1) ✅ | Week 2 In Progress

## 🎯 Key Features

### ✅ Autonomous Tool Use (P0)
- **34+ Aviation MCP Tools**: Agents autonomously use real aviation data
- **Tool Use Loop**: Full Claude API tool use integration
- **Dynamic Discovery**: Tools automatically available to agents
- Works with multiple MCP servers (aerospace-mcp, aviation-weather-mcp, etc.)

### ✅ Directed Communication (P0)
- **Voice Net Protocol**: Military-style radio communication
- **Intelligent Routing**: Agents respond only when addressed
- **Broadcast Support**: "All stations" messages reach entire team
- **Squad Leader Delegation**: Commander can assign tasks to specific agents

### ✅ Agent Memory & Context (P1)
- **Persistent Memory**: 5 categories (tasks, facts, decisions, concerns, notes)
- **MEMORIZE Commands**: Agents update memory mid-conversation
- **Context Injection**: Memory automatically appears in prompts
- **Memory API**: Update, clear, and query agent memory

### ✅ State Persistence (P1)
- **SQLite Sessions**: Save/load complete mission state
- **Full Restoration**: Messages + agent memory + configurations
- **Export Capability**: JSON or readable text format
- **Session Management**: List, load, and delete saved missions

### 🎯 Multi-Agent Architecture
- **1-6 Agents**: Scalable team coordination
- **Squad Leader**: Special coordination role
- **Specialist Roles**: Flight planner, navigator, weather officer, etc.
- **Shared Channel**: All agents communicate on shared voice net

## 🚀 Quick Start

### Installation
```bash
# Clone and install
pip install -r requirements.txt

# Set API key
export ANTHROPIC_API_KEY='your-key-here'
```

### Interactive Demo (Recommended)
```bash
python demo_interactive.py
```

**What you'll see:**
- 🎯 Realistic Coast Guard SAR mission scenario
- 👥 4 agents (Squad Leader + 3 specialists)
- 🎮 Interactive control - you direct the mission
- 🛠️ Agents using real aviation tools
- 💬 Directed communication in action
- 🧠 Agent memory persisting across conversation

**Time:** 10-15 minutes

### Quick Validation Tests
```bash
# Test autonomous tool use (3 min)
python test_autonomous_tool_use.py

# Test memory & persistence (2 min)
python test_memory_and_persistence.py

# Test directed communication (2 min)
python test_directed_communication.py
```

### Simple Airport Search Demo
```bash
# Quick 1-minute demo
python demo_agent_airport_search.py
```

**See [DEMO_GUIDE.md](DEMO_GUIDE.md) for detailed demo instructions and talking points.**

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
