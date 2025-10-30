# MCP Integration Guide

## Overview

The multi-agent collaboration system now integrates with Model Context Protocol (MCP) servers, enabling agents to access real tools and capabilities. The first integration is with the **Aerospace MCP** server, giving agents aerospace engineering capabilities.

## Architecture

### Components

**MCP Manager** (`src/mcp/mcp_manager.py`)
- Connects to MCP servers via stdio
- Discovers available tools
- Manages server lifecycle
- Caches tool metadata

**Tool Executor** (`src/mcp/tool_executor.py`)
- Executes MCP tools requested by agents
- Handles async tool execution
- Formats results
- Tracks execution history

**Aerospace Agent** (`src/agents/aerospace_agent.py`)
- Specialized agent with aerospace expertise
- Configured to use aerospace tools
- Responds to aviation/space-related keywords

## Installation

### Prerequisites

1. **Aerospace MCP Server** must be installed:
   ```bash
   cd /path/to/aerospace-mcp
   uv venv && source .venv/bin/activate
   uv sync
   ```

2. **MCP Python SDK** in multi-agent project:
   ```bash
   cd multi-agent-collab
   pip install -r requirements.txt  # includes mcp>=0.1.0
   ```

## Usage

### Running the Aerospace Demo

```bash
cd multi-agent-collab
export ANTHROPIC_API_KEY='your-key-here'
python demo_aerospace.py
```

This demonstrates:
- MCP server connection
- Tool discovery (30+ aerospace tools)
- Agents using tools for flight planning
- Multi-agent coordination with real capabilities

### Using in Your Code

```python
import asyncio
from src.mcp.mcp_manager import initialize_aerospace_mcp, get_mcp_manager
from src.agents.aerospace_agent import AerospaceAgent
from src.channel.shared_channel import SharedChannel
from src.orchestration.orchestrator import Orchestrator

async def main():
    # Initialize MCP connection
    await initialize_aerospace_mcp("/path/to/aerospace-mcp")

    # Create agents
    channel = SharedChannel()
    orchestrator = Orchestrator(channel=channel)

    aerospace = AerospaceAgent(
        agent_id="aerospace_1",
        callsign="Alpha One"
    )
    orchestrator.add_agent(aerospace)
    orchestrator.start()

    # Agents can now use MCP tools!
    orchestrator.run_turn(
        user_message="Plan a flight from New York to London"
    )

    # Cleanup
    manager = await get_mcp_manager()
    await manager.close()

asyncio.run(main())
```

## Available Tools

The Aerospace MCP server provides 30+ tools across these domains:

### Core Aviation
- `plan_flight` - Complete flight planning with fuel estimates
- `airports_by_city` - Search airport database
- `great_circle_distance` - Calculate distances
- `aircraft_performance` - Performance characteristics

### Atmospheric Science
- `atmosphere_properties` - Get atmospheric data
- `wind_triangle` - Calculate wind corrections
- `density_altitude` - Compute density altitude

### Coordinate Systems
- `lat_lon_to_ecef` - Geodetic to ECEF conversion
- `ecef_to_lat_lon` - ECEF to geodetic conversion
- `ned_offset` - Local tangent plane calculations

### Aerodynamics
- `wing_analysis` - Wing performance analysis
- `airfoil_polar` - Airfoil characteristics
- `induced_drag` - Drag calculations

### Propellers
- `propeller_performance` - Propeller analysis
- `advance_ratio` - Propeller metrics

### Rockets
- `rocket_trajectory_3dof` - 3DOF trajectory simulation
- `rocket_delta_v` - Delta-V calculations
- `specific_impulse` - Engine performance

### Orbital Mechanics
- `orbital_elements` - Orbital parameters
- `hohmann_transfer` - Transfer orbit calculations
- `orbital_period` - Period calculations

### Spacecraft
- `spacecraft_trajectory` - Trajectory optimization
- `reentry_heating` - Heating analysis

## Configuration

### Aerospace Squad Config

See `configs/aerospace.yaml` for a complete example:

```yaml
agents:
  - agent_id: aerospace_specialist
    callsign: "Hawk One"
    agent_type: aerospace
    speaking_criteria:
      - type: keywords
        keywords: [flight, aircraft, aerospace, orbital, ...]
```

### MCP Server Settings

The MCP manager automatically:
- Connects via stdio using `uv run`
- Discovers all available tools
- Caches tool schemas
- Handles async execution

## Adding More MCP Servers

To add additional MCP servers:

1. **Install the server:**
   ```bash
   # Example: weather MCP server
   cd ../weather-mcp
   uv sync
   ```

2. **Connect in code:**
   ```python
   manager = await get_mcp_manager()
   await manager.connect_server(
       server_name="weather-mcp",
       command="uv",
       args=["--directory", "/path/to/weather-mcp", "run", "weather-mcp"]
   )
   ```

3. **Create specialized agent:**
   ```python
   class WeatherAgent(BaseAgent):
       def __init__(self, ...):
           # Configure with weather-specific keywords
           speaking_criteria = KeywordCriteria([
               "weather", "temperature", "forecast", ...
           ])
   ```

## Tool Execution Flow

1. **Agent decides to use tool** (based on user message)
2. **Tool request sent** via MCP protocol
3. **MCP server executes** tool with given arguments
4. **Result returned** to agent
5. **Agent incorporates** result in response
6. **Response sent** to shared channel

## Debugging

### View Available Tools

```python
manager = await get_mcp_manager()
tools = manager.get_available_tools("aerospace-mcp")
for tool in tools:
    print(f"{tool['name']}: {tool['description']}")
```

### Check Tool Execution History

```python
from src.mcp.tool_executor import get_tool_executor

executor = get_tool_executor()
history = executor.get_execution_history(limit=10)
for record in history:
    print(f"Tool: {record['tool_name']}")
    print(f"Success: {record['success']}")
    print(f"Result: {record['result']}")
```

### Test MCP Connection

```bash
# Test aerospace-mcp server directly
cd aerospace-mcp
uv run aerospace-mcp

# Should start and wait for stdio input
# Press Ctrl+C to exit
```

## Limitations

- Currently supports stdio transport only
- Tools execute asynchronously (may add latency)
- No tool result caching yet
- Agent must explicitly request tool use in prompts

## Future Enhancements

- [ ] HTTP/SSE transport support
- [ ] Tool result caching
- [ ] Automatic tool selection by agents
- [ ] Multi-tool parallel execution
- [ ] Tool usage analytics
- [ ] Custom tool wrappers

## Safety Notes

**Aerospace MCP Disclaimer:**
All aerospace calculations are for educational/research purposes only. Never use for real flight planning or navigation. Not certified by any aviation authority.

## References

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Aerospace MCP Server](https://github.com/cheesejaguar/aerospace-mcp)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
