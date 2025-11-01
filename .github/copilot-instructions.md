# Multi-Agent Collaboration System - AI Agent Instructions

## Architecture Overview

This is a **multi-agent system** where 1-6 AI agents communicate via a shared text channel using **Voice Net Protocol** (pilot-ATC style communication with callsigns). One agent acts as squad leader to coordinate activities. Agents can access real tools via **Model Context Protocol (MCP)** integration.

**Core Flow**: `User Message → Orchestrator → SharedChannel → Agent.should_respond() → Agent.generate_response() → SharedChannel`

## Key Components & Patterns

### 1. Agent Architecture (`src/agents/`)
- **BaseAgent**: All agents inherit from this - handles Claude API, speaking criteria, voice net protocol
- **SquadLeaderAgent**: Specialized coordinator with enhanced response logic  
- **AerospaceAgent**: MCP-enabled agent with aerospace tool access
- **Speaking Criteria**: Determines when agents respond (DirectAddress, Keywords, Questions, etc.)

```python
# Agent creation pattern
agent = BaseAgent(
    agent_id="pilot", 
    callsign="Hawk One",
    system_prompt="...",
    speaking_criteria=CompositeCriteria([...])
)
```

### 2. Voice Net Protocol (`src/channel/voice_net_protocol.py`)
Messages follow aviation radio format: `"Recipient, this is Sender, message content, over"`
- Parses sender/recipient callsigns automatically
- Supports "Roger/Copy" acknowledgments
- Handles broadcast vs direct addressing

### 3. MCP Integration (`src/mcp/`)
**Critical**: MCP servers must be connected before agent creation
- `MCPManager`: Connects to MCP servers via stdio, discovers tools
- `ToolExecutor`: Executes tools requested by agents, formats results
- Pattern: `await mcp_manager.connect_server(name, command, args)`

### 4. Configuration System (`src/config/`)
**External Prompt Pattern**: Reference reusable prompts from `configs/prompts/`
```yaml
agents:
  - agent_id: pilot
    system_prompt_file: prompts/pilot.yaml  # Loads external prompt
    speaking_criteria:
      - type: keywords
        keywords: [flight, navigate]
```

## Development Workflows

### Running Demos
```bash
# Basic demo (no MCP)
python -m src.cli.main demo

# Aerospace MCP demo (requires ANTHROPIC_API_KEY)
python demo_aerospace.py

# Interactive session
python -m src.cli.main interactive --config configs/aerospace.yaml
```

### MCP Server Setup
MCP servers run as separate processes. For aerospace-mcp:
```bash
cd /path/to/aerospace-mcp && uv run aerospace-mcp
```
Configure in Claude Desktop config or connect programmatically via `MCPManager`.

### Testing
- Tests use pytest with async support (`pytest-asyncio`)
- Focus on unit testing individual components (voice protocol, speaking criteria)
- Integration tests in root directory (`test_*.py` files)

## Project-Specific Conventions

### Agent Communication
- Always use callsigns in messages: `"Tower, this is Hawk One"`
- Squad leader has special coordination responsibilities
- Agents filter responses via speaking criteria (avoid chatty behavior)

### MCP Tool Integration
- Tools are discovered automatically on server connection
- Agents reference tools by name in system prompts
- Results formatted as JSON for agent consumption
- **Important**: Aerospace MCP provides 30+ tools (flight planning, performance, orbital mechanics)

### Configuration Management
- YAML configs with Pydantic validation (`src/config/schema.py`)
- Support for external prompt files reduces duplication
- Environment-specific configs: `default.yaml`, `aerospace.yaml`, `demo.yaml`

### Error Handling Patterns
- MCP connections fail gracefully, agents work without tools
- Missing API keys cause early exit with helpful messages
- Rich console formatting for user-facing output

## Key Files to Understand

- `src/orchestration/orchestrator.py`: Core message flow coordination
- `src/channel/shared_channel.py`: Message history and context management  
- `configs/aerospace.yaml`: Complete MCP-enabled agent configuration
- `demo_aerospace.py`: Full integration example with real tools
- `src/agents/speaking_criteria.py`: Response filtering logic

## Integration Points

**MCP Servers**: Currently aerospace-mcp, aviation-weather-mcp, extensible to any MCP server
**Claude API**: All agents use Anthropic's Claude models (configurable model/temperature)
**State Management**: SQLite-based persistence (see `src/state/`)
**CLI**: Click-based with Rich formatting (`src/cli/main.py`)