# Quick Start: Autonomous Tool Use

## ✅ Implementation Complete!

Your multi-agent system now has **autonomous MCP tool use** - the critical P0 feature!

---

## What Changed

### Agents Can Now Use Tools Automatically

**Before:**
```python
# Agents could only generate text responses
agent = BaseAgent(agent_id="test", callsign="ALPHA", system_prompt="...")
response = agent.generate_response(channel)  # Just text, no tools
```

**After:**
```python
# Agents autonomously use MCP tools
mcp_manager = await get_mcp_manager()
agent = BaseAgent(
    agent_id="test",
    callsign="ALPHA",
    system_prompt="...",
    mcp_manager=mcp_manager  # ← New parameter
)
response = await agent.generate_response(channel)  # ← Now async, uses tools!
```

---

## Quick Test

Run this to see it in action:

```bash
python test_autonomous_tool_use.py
```

**What it does:**
1. Connects to aerospace-mcp server (34 aviation tools)
2. Creates an agent with tool access
3. Asks agent to search for airports
4. Agent autonomously uses `search_airports` tool
5. Agent returns detailed airport information

**Expected output:**
```
✅ Connected to 1 server(s): aerospace-mcp
📋 Total tools available: 34

[USER]: Alpha One, search for airports near San Francisco...

[ALPHA ONE]: San Francisco International Airport (SFO/KSFO)
- IATA Code: SFO
- ICAO Code: KSFO
- Coordinates: 37.6188°N, 122.3754°W
- Timezone: America/Los_Angeles

✅ VERIFICATION PASSED!
```

---

## How to Use in Your Code

### 1. Initialize MCP Manager

```python
import asyncio
from src.mcp.mcp_manager import get_mcp_manager, initialize_aerospace_mcp

async def main():
    # Connect to MCP server
    await initialize_aerospace_mcp("/path/to/aerospace-mcp")

    # Get manager instance
    mcp_manager = await get_mcp_manager()
```

### 2. Create Agents with Tool Access

```python
from src.agents.base_agent import BaseAgent

agent = BaseAgent(
    agent_id="planner_1",
    callsign="FLIGHT-PLANNER",
    system_prompt="You are a flight planning specialist...",
    mcp_manager=mcp_manager  # Pass the manager
)
```

### 3. Use in Orchestrator

```python
from src.orchestration.orchestrator import Orchestrator

orchestrator = Orchestrator()
orchestrator.add_agent(agent)

# Run async
turn_result = await orchestrator.run_turn(
    user_message="Search for airports in Boston"
)
```

### 4. Clean Up

```python
# Always clean up at the end
await mcp_manager.cleanup()
```

---

## Complete Example

```python
#!/usr/bin/env python3
import asyncio
from pathlib import Path
from src.agents.base_agent import BaseAgent
from src.channel.shared_channel import SharedChannel
from src.orchestration.orchestrator import Orchestrator
from src.mcp.mcp_manager import get_mcp_manager, initialize_aerospace_mcp

async def main():
    # 1. Initialize MCP
    aerospace_path = str(Path(__file__).parent.parent / "aerospace-mcp")
    await initialize_aerospace_mcp(aerospace_path)
    mcp_manager = await get_mcp_manager()

    # 2. Create agent with tools
    agent = BaseAgent(
        agent_id="navigator",
        callsign="NAV-ONE",
        system_prompt="You are a navigation specialist.",
        mcp_manager=mcp_manager
    )

    # 3. Set up orchestration
    channel = SharedChannel()
    orchestrator = Orchestrator(channel=channel)
    orchestrator.add_agent(agent)
    orchestrator.start()

    # 4. Send message
    result = await orchestrator.run_turn(
        user_message="Nav One, find airports near Seattle. Over."
    )

    # 5. Print response
    for response in result["agent_responses"]:
        print(f"[{response.sender_callsign}]: {response.content}")

    # 6. Clean up
    await mcp_manager.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Important: Async/Await Required

All agent methods are now async:

```python
# ❌ OLD - No longer works
response = agent.generate_response(channel)
message = agent.respond(channel)
turn_result = orchestrator.run_turn(user_message)

# ✅ NEW - Required
response = await agent.generate_response(channel)
message = await agent.respond(channel)
turn_result = await orchestrator.run_turn(user_message)
```

---

## Available Tools (aerospace-mcp)

Your agents have access to 34 aviation tools:

**Flight Planning:**
- `search_airports` - Find airports by code/city
- `plan_flight` - Plan routes with fuel estimates
- `calculate_distance` - Great circle distance

**Performance:**
- `get_aircraft_performance` - Aircraft data
- `calculate_fuel_required` - Fuel calculations
- `estimate_flight_time` - Time estimates

**And 28 more!**

List all tools:
```python
mcp_manager = await get_mcp_manager()
tools = mcp_manager.get_available_tools()
for tool in tools:
    print(f"{tool['name']}: {tool['description']}")
```

---

## Troubleshooting

### "Connection closed" errors for other MCP servers

**Issue:** aviation-weather-mcp and blevinstein-aviation-mcp fail to connect

**Solution:** Not critical - aerospace-mcp (34 tools) works perfectly. Other servers have Python version conflicts.

**Workaround:** Use only aerospace-mcp for now

### "RuntimeError: This event loop is already running"

**Issue:** Trying to use `asyncio.run()` inside an async function

**Solution:**
```python
# ❌ Wrong
async def my_function():
    asyncio.run(other_async_function())

# ✅ Correct
async def my_function():
    await other_async_function()
```

### Agent not using tools

**Checklist:**
1. Did you pass `mcp_manager` to agent?
2. Is MCP manager initialized? (`mcp_manager.is_initialized()`)
3. Are you using `await`?
4. Is system prompt clear about when to use tools?

---

## Next Steps

**Week 1 Priorities (from proposal):**
- [x] ✅ Autonomous tool use (DONE!)
- [ ] Agent memory & context
- [ ] State persistence

**Week 2 Priorities:**
- [ ] Directed communication improvements
- [ ] Basic visual dashboard

See `Documents/Integrated Enhancement Proposal_ Multi-Agent Aviation Demo.md` for full roadmap.

---

## Files to Check

**Implementation:**
- `src/agents/base_agent.py` - Core tool use logic
- `src/agents/squad_leader.py` - Updated for async
- `src/orchestration/orchestrator.py` - Async orchestration
- `src/mcp/mcp_manager.py` - MCP connection management

**Testing:**
- `test_autonomous_tool_use.py` - Comprehensive verification
- `IMPLEMENTATION_COMPLETE.md` - Full technical details

**Documentation:**
- `AVIATION_MCP_COMPLETE.md` - MCP server setup
- `docs/ARCHITECTURE.md` - System architecture

---

## Questions?

Run the test to see it working:
```bash
python test_autonomous_tool_use.py
```

Check implementation details:
```bash
cat IMPLEMENTATION_COMPLETE.md
```

Verify MCP servers:
```bash
python verify_all_aviation_mcp.py
```

🎉 **Enjoy your autonomous tool-using agents!**
