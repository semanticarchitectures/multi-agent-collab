# Aviation MCP Servers Setup

## ✅ Successfully Configured MCP Servers

Your multi-agent collaboration system now has access to **2 aviation MCP servers** with **55 total tools**!

### 1. aerospace-mcp (34 tools)
**Description:** Aerospace engineering calculations and flight planning

**Location:** `/Users/kevinkelly/Documents/claude-projects/agentDemo/aerospace-mcp`

**Sample Tools:**
- `search_airports` - Search for airports by IATA code or city name
- `plan_flight` - Plan a flight route between two airports with performance estimates
- `calculate_distance` - Calculate great circle distance between two points
- `get_aircraft_performance` - Get performance estimates for an aircraft type
- `get_system_status` - Get system status and capabilities
- ... and 29 more tools

**Technology:** Python with FastMCP 2.11.3, MCP 1.13.1

### 2. aviation-mcp (21 tools)
**Description:** FAA aviation data (weather, NOTAMs, charts)

**Location:** `/Users/kevinkelly/Documents/claude-projects/agentDemo/aviation-mcp`

**Sample Tools:**
- `get_metar` - Retrieves current METAR data for weather stations
- `get_taf` - Retrieves TAF forecasts for weather stations
- `get_pirep` - Retrieves pilot reports (PIREPs) for a specific region
- `get_windtemp` - Retrieves wind and temperature data for specific altitudes
- `get_station_info` - Retrieves information about weather stations
- `get_notam` - Retrieves NOTAMs (Notices to Airmen)
- `get_chart` - Retrieves aviation charts
- `get_aircraft_info` - Retrieves aircraft information
- ... and 13 more tools

**Technology:** Node.js/TypeScript with npm package `aviation-mcp` v1.0.17

**Author:** Brian Levinstein

**API Keys (Optional):**
- `FAA_CLIENT_ID` - For NOTAM access (get from https://api.faa.gov/s/)
- `FAA_CLIENT_SECRET` - For NOTAM access
- `API_NINJAS_KEY` - For aircraft data (get from https://api-ninjas.com/)

Note: Weather and charts work without API keys!

---

## Configuration Files

### Claude Desktop Config
**Location:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "aerospace-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/kevinkelly/Documents/claude-projects/agentDemo/aerospace-mcp",
        "run",
        "aerospace-mcp"
      ]
    },
    "aviation-mcp": {
      "command": "npx",
      "args": [
        "-y",
        "aviation-mcp"
      ],
      "env": {
        "FAA_CLIENT_ID": "",
        "FAA_CLIENT_SECRET": "",
        "API_NINJAS_KEY": ""
      }
    }
  }
}
```

### Multi-Agent System Integration

The MCP servers are integrated into your multi-agent system via `src/mcp/mcp_manager.py`:

```python
from src.mcp.mcp_manager import get_mcp_manager

# Get the manager
manager = await get_mcp_manager()

# Connect to aerospace-mcp
await manager.connect_server(
    server_name="aerospace-mcp",
    command="uv",
    args=["--directory", "/path/to/aerospace-mcp", "run", "aerospace-mcp"]
)

# Connect to aviation-mcp
await manager.connect_server(
    server_name="aviation-mcp",
    command="npx",
    args=["-y", "aviation-mcp"],
    env={
        "FAA_CLIENT_ID": "",
        "FAA_CLIENT_SECRET": "",
        "API_NINJAS_KEY": ""
    }
)

# Get all tools from all servers
all_tools = manager.get_available_tools()

# Call a tool from a specific server
result = await manager.call_tool(
    server_name="aerospace-mcp",
    tool_name="search_airports",
    arguments={"query": "SFO"}
)
```

---

## Verification

### Run the Verification Script

```bash
python verify_all_aviation_mcp.py
```

**Expected Output:**
```
✅ aerospace-mcp: Connected
✅ aviation-mcp: Connected

📚 Tools Discovered:
  • aerospace-mcp: 34 tools
  • aviation-mcp: 21 tools

🧪 Tool Execution Tests:
✅ aerospace-mcp: Passed
✅ aviation-mcp: Passed
```

### Test Individual Servers

**Test aerospace-mcp:**
```bash
python demo_agent_airport_search.py
```

**Test aviation-mcp weather tools:**
```python
from src.mcp.mcp_manager import get_mcp_manager

manager = await get_mcp_manager()

# Connect to aviation-mcp
await manager.connect_server(
    server_name="aviation-mcp",
    command="npx",
    args=["-y", "aviation-mcp"]
)

# Get METAR for San Francisco
result = await manager.call_tool(
    server_name="aviation-mcp",
    tool_name="get_metar",
    arguments={"stationString": "KSFO"}
)
```

---

## Usage Examples

### Example 1: Search for Airports (aerospace-mcp)

```python
result = await manager.call_tool(
    server_name="aerospace-mcp",
    tool_name="search_airports",
    arguments={"query": "Los Angeles"}
)
```

**Result:**
```
Found 1 airport(s):

• LAX (KLAX) - Los Angeles International Airport
  City: Los Angeles, US
  Coordinates: 33.9425, -118.4081
  Timezone: America/Los_Angeles
```

### Example 2: Get Weather (aviation-mcp)

```python
result = await manager.call_tool(
    server_name="aviation-mcp",
    tool_name="get_metar",
    arguments={"stationString": "KSFO"}
)
```

**Result:** Current METAR data for San Francisco International

### Example 3: Plan a Flight (aerospace-mcp)

```python
result = await manager.call_tool(
    server_name="aerospace-mcp",
    tool_name="plan_flight",
    arguments={
        "origin": "KSFO",
        "destination": "KLAX"
    }
)
```

---

## Next Steps

### 1. Configure API Keys (Optional)

To enable NOTAM and aircraft data features in aviation-mcp:

1. **Get FAA API credentials:**
   - Visit https://api.faa.gov/s/
   - Register for an account
   - Create an application
   - Copy your Client ID and Client Secret

2. **Get API Ninjas key:**
   - Visit https://api-ninjas.com/
   - Sign up for a free account
   - Copy your API key

3. **Update the config:**
   ```bash
   # Edit the config file
   nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
   
   # Add your keys to the aviation-mcp env section
   ```

### 2. Integrate with Agents

Currently, agents can access MCP tools via direct calls, but **agent integration is not yet complete**.

To enable agents to use MCP tools through the Claude API:

1. Run the integration check:
   ```bash
   python verify_agent_tool_integration.py
   ```

2. Follow the instructions to implement the missing integration in `src/agents/base_agent.py`

### 3. Test the Multi-Server Setup

```bash
# Run the verification
python verify_all_aviation_mcp.py

# Test airport search
python demo_agent_airport_search.py

# Use in interactive mode (once agent integration is complete)
python -m src.cli.main interactive --config configs/aerospace.yaml
```

---

## Troubleshooting

### aerospace-mcp won't connect

1. **Check uv is installed:**
   ```bash
   which uv
   ```

2. **Check the server exists:**
   ```bash
   ls -la /Users/kevinkelly/Documents/claude-projects/agentDemo/aerospace-mcp
   ```

3. **Test manually:**
   ```bash
   cd /Users/kevinkelly/Documents/claude-projects/agentDemo/aerospace-mcp
   uv run aerospace-mcp
   ```

### aviation-mcp won't connect

1. **Check npx is installed:**
   ```bash
   which npx
   ```

2. **Install aviation-mcp globally:**
   ```bash
   npm install -g aviation-mcp
   ```

3. **Test manually:**
   ```bash
   npx -y aviation-mcp
   ```

### Tools return errors

- **aerospace-mcp:** Check that arguments match the tool schema
- **aviation-mcp:** Some tools require API keys (FAA_CLIENT_ID, etc.)
- Weather tools (METAR, TAF) should work without API keys

---

## Summary

✅ **2 MCP servers configured and verified**
✅ **55 total tools available**
✅ **Both servers connecting successfully**
✅ **Tool execution tested and working**
✅ **Claude Desktop config updated**

🚀 **Ready to use in your multi-agent system!**

📋 **Next:** Implement agent MCP tool integration (see `verify_agent_tool_integration.py`)

