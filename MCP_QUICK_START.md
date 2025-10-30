# MCP Quick Start Guide

## ✅ Verification Complete

Your agents **CAN** access the aerospace-mcp server! 

- ✅ 34 aerospace tools discovered
- ✅ Connection tested and working
- ✅ Tool execution verified

## Quick Commands

### 1. Verify MCP Connection (No API Key Needed)

```bash
python verify_mcp_connection.py
```

This checks:
- aerospace-mcp server location
- uv command availability
- MCP connection
- Tool discovery
- Tool execution

### 2. Run Aerospace Demo (Requires API Key)

```bash
# Set your API key first
export ANTHROPIC_API_KEY='your-key-here'

# Run the demo
python demo_aerospace.py
```

### 3. Interactive Mode with Aerospace Agents

```bash
# Set your API key
export ANTHROPIC_API_KEY='your-key-here'

# Start interactive session
python -m src.cli.main interactive --config configs/aerospace.yaml
```

## Example Conversations

Once in interactive mode, try these:

### Flight Planning
```
You: Hawk One, plan a flight from San Francisco to Tokyo using a Boeing 777
```

The aerospace agent will:
1. Search for SFO and NRT airports
2. Calculate the flight route
3. Estimate fuel requirements
4. Provide performance data

### Airport Search
```
You: What airports are available in London?
```

The agent will search the airport database and return all London airports.

### Distance Calculation
```
You: Calculate the distance from LAX to JFK
```

The agent will compute the great circle distance between the airports.

## Available Tools (34 Total)

### Most Useful Tools

| Tool | Purpose | Example |
|------|---------|---------|
| `search_airports` | Find airports by code or city | "Find airports in Paris" |
| `plan_flight` | Plan routes with fuel estimates | "Plan flight SFO to NRT" |
| `calculate_distance` | Great circle distance | "Distance from LAX to JFK" |
| `get_aircraft_performance` | Aircraft specs | "Performance of Boeing 777" |
| `get_atmosphere_profile` | Atmospheric data | "Atmosphere at 35,000 ft" |

### All Tool Categories

1. **Airport & Navigation** (4 tools)
   - Airport search, flight planning, distance calculation

2. **Aircraft Performance** (3 tools)
   - Performance data, fuel estimates, range calculations

3. **Atmospheric Science** (5 tools)
   - Pressure, temperature, density, wind models

4. **Coordinate Systems** (8 tools)
   - ECEF, ECI, geodetic transformations

5. **Orbital Mechanics** (6 tools)
   - Orbital parameters, trajectories, propagation

6. **Aerodynamics** (5 tools)
   - Lift, drag, airfoil analysis

7. **Rocket Science** (3 tools)
   - Trajectory optimization, staging, performance

## Configuration

### Using Aerospace Agents

Add to your YAML config:

```yaml
agents:
  - agent_id: aerospace_specialist
    callsign: "Hawk One"
    agent_type: base
    model: claude-sonnet-4-5-20250929
    system_prompt_file: prompts/pilot.yaml
    speaking_criteria:
      - type: keywords
        keywords:
          - flight
          - aircraft
          - airport
          - aerospace
          - navigation
          - trajectory
```

### Programmatic Usage

```python
import asyncio
from src.mcp.mcp_manager import initialize_aerospace_mcp, get_mcp_manager
from src.agents.aerospace_agent import AerospaceAgent

async def main():
    # Initialize MCP
    aerospace_path = "../aerospace-mcp"
    await initialize_aerospace_mcp(aerospace_path)
    
    # Create aerospace agent
    agent = AerospaceAgent(
        agent_id="aerospace_1",
        callsign="Hawk One"
    )
    
    # Use in your orchestrator...
    
asyncio.run(main())
```

## Troubleshooting

### Connection Issues

**Problem:** "Failed to connect to aerospace-mcp server"

**Solution:**
```bash
# Check server location
ls -la ../aerospace-mcp

# Install dependencies
cd ../aerospace-mcp
uv sync

# Test manually
uv run aerospace-mcp
```

### Missing uv Command

**Problem:** "'uv' command not found"

**Solution:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Missing MCP Package

**Problem:** "ModuleNotFoundError: No module named 'mcp'"

**Solution:**
```bash
pip install mcp
```

### API Key Issues

**Problem:** "ANTHROPIC_API_KEY environment variable not set"

**Solution:**
```bash
export ANTHROPIC_API_KEY='your-key-here'
```

## What's Working

✅ **MCP Server Connection**
- aerospace-mcp server running
- stdio transport working
- 34 tools discovered

✅ **Tool Execution**
- Successfully tested `search_airports`
- Returned airport data for SFO
- All tools accessible

✅ **Agent Integration**
- AerospaceAgent class available
- Configured with aerospace keywords
- Ready to use MCP tools

## What You Need

To actually use the agents (not just verify connection):

1. **Anthropic API Key**
   ```bash
   export ANTHROPIC_API_KEY='your-key-here'
   ```

2. **Run a demo or interactive session**
   ```bash
   python demo_aerospace.py
   # or
   python -m src.cli.main interactive --config configs/aerospace.yaml
   ```

## Next Steps

1. ✅ **Verified** - MCP connection working
2. 🔑 **Set API Key** - Export ANTHROPIC_API_KEY
3. 🚀 **Run Demo** - Try `python demo_aerospace.py`
4. 💬 **Interactive** - Chat with aerospace agents
5. 🛠️ **Customize** - Create your own aerospace missions

## Documentation

- **Full Verification Results**: `MCP_VERIFICATION_RESULTS.md`
- **MCP Integration Guide**: `docs/MCP_INTEGRATION.md`
- **Architecture**: `docs/ARCHITECTURE.md`

---

**Status**: ✅ MCP Connection Verified and Working!

Your agents are ready to access 34 aerospace engineering tools through the aerospace-mcp server.

