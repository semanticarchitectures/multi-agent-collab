# Aviation MCP Servers Setup Guide

This guide will help you set up multiple aviation MCP servers for use with the multi-agent collaboration system.

## Overview

The system supports three aviation-focused MCP servers:

1. **aerospace-mcp** - Aerospace engineering calculations and flight planning
2. **aviation-weather-mcp** - Weather data, METAR/TAF decoding
3. **blevinstein/aviation-mcp** - General aviation utilities and tools

## Prerequisites

- Python 3.11+
- `uv` package manager
- Git

### Install `uv` Package Manager

If you don't have `uv` installed:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

After installation, restart your terminal or run:
```bash
source ~/.cargo/env
```

## MCP Server Installation

All MCP servers should be installed in the parent directory of this project for consistency.

```
agentDemo/
├── multi-agent-collab/       # This project
├── aerospace-mcp/            # Aerospace engineering tools
├── aviation-weather-mcp/     # Weather tools
└── aviation-mcp/             # General aviation tools (blevinstein)
```

### 1. aerospace-mcp

**Status:** ✅ Already installed

This server is already set up in your environment at:
```
/Users/kevinkelly/Documents/claude-projects/agentDemo/aerospace-mcp
```

**Tools provided (34+):**
- Flight planning and fuel calculations
- Airport database queries
- Atmospheric modeling
- Orbital mechanics
- Aerodynamic analysis
- Rocket trajectory optimization

### 2. aviation-weather-mcp

**Status:** ⚠️ Needs installation

This server provides aviation weather data and METAR/TAF decoding.

**Installation:**

```bash
# Navigate to parent directory
cd /Users/kevinkelly/Documents/claude-projects/agentDemo

# Clone the repository
# Note: Replace [repository] with actual repository URL
# Example repositories to check:
# - https://github.com/[username]/aviation-weather-mcp
# - https://github.com/mcp/aviation-weather
git clone https://github.com/[repository]/aviation-weather-mcp

# Navigate to the directory
cd aviation-weather-mcp

# Install dependencies
uv sync

# Test the server
uv run aviation-weather-mcp
```

**Expected tools:**
- `get_metar` - Retrieve current METAR reports
- `get_taf` - Get Terminal Area Forecasts
- `decode_metar` - Decode METAR into readable format
- `decode_taf` - Decode TAF into readable format
- Weather analysis and interpretation tools

**Finding the repository:**
If the repository URL is unknown, search for:
- GitHub: "aviation-weather-mcp"
- MCP Registry: https://github.com/modelcontextprotocol/servers

### 3. blevinstein/aviation-mcp

**Status:** ⚠️ Needs installation

This server provides general aviation utilities and tools.

**Installation:**

```bash
# Navigate to parent directory
cd /Users/kevinkelly/Documents/claude-projects/agentDemo

# Clone the repository
git clone https://github.com/blevinstein/aviation-mcp

# Navigate to the directory
cd aviation-mcp

# Install dependencies
uv sync

# Test the server
uv run aviation-mcp
```

**Expected tools:**
- Flight operations utilities
- Aviation data queries
- General aviation calculations
- Additional aviation support tools

**Repository:**
- GitHub: https://github.com/blevinstein/aviation-mcp

## Verification

After installing any MCP servers, run the verification script:

```bash
cd /Users/kevinkelly/Documents/claude-projects/agentDemo/multi-agent-collab
python verify_all_mcp_servers.py
```

This will:
- Check which servers are installed
- Verify `uv` is available
- Connect to each server
- Discover available tools
- Test basic tool execution
- Display summary of all capabilities

## Configuration

The MCP servers are configured in:
```
configs/aerospace.yaml
```

The configuration automatically detects which servers are available and uses them.

## Using the MCP Servers

### Quick Start

1. **Verify all servers:**
   ```bash
   python verify_all_mcp_servers.py
   ```

2. **Run the multi-aviation demo:**
   ```bash
   python demo_multi_aviation.py
   ```

3. **Interactive mode:**
   ```bash
   python -m src.cli.main interactive --config configs/aerospace.yaml
   ```

### In Your Code

```python
from src.mcp.mcp_manager import initialize_all_aviation_mcps, get_mcp_manager

# Initialize all available servers
results = await initialize_all_aviation_mcps(
    aerospace_path="../aerospace-mcp",
    aviation_weather_path="../aviation-weather-mcp",
    blevinstein_aviation_path="../aviation-mcp"
)

# Get the manager
manager = await get_mcp_manager()

# List all tools
all_tools = manager.get_available_tools()

# Call a specific tool
result = await manager.call_tool(
    tool_name="search_airports",
    arguments={"query": "JFK"}
)
```

## Troubleshooting

### Server won't connect

1. **Check the server exists:**
   ```bash
   ls -la /Users/kevinkelly/Documents/claude-projects/agentDemo/
   ```

2. **Verify dependencies are installed:**
   ```bash
   cd /path/to/mcp-server
   uv sync
   ```

3. **Test the server manually:**
   ```bash
   cd /path/to/mcp-server
   uv run [server-name]
   ```

### Missing tools

If expected tools aren't appearing:

1. **Check server version:**
   ```bash
   cd /path/to/mcp-server
   git pull
   uv sync
   ```

2. **Verify tool discovery:**
   ```bash
   python verify_all_mcp_servers.py
   ```

### Permission errors

If you get permission errors:

```bash
# Make scripts executable
chmod +x verify_all_mcp_servers.py
chmod +x demo_multi_aviation.py
```

## MCP Server Details

### Server Capabilities Matrix

| Feature | aerospace-mcp | aviation-weather-mcp | blevinstein/aviation-mcp |
|---------|---------------|---------------------|-------------------------|
| Flight Planning | ✅ | ❌ | ✅ |
| Weather Data | ❌ | ✅ | ❌ |
| Airport Database | ✅ | ❌ | ✅ |
| Performance Calc | ✅ | ❌ | ❌ |
| Atmospheric Data | ✅ | ✅ | ❌ |
| METAR/TAF | ❌ | ✅ | ❌ |
| Orbital Mechanics | ✅ | ❌ | ❌ |
| Aerodynamics | ✅ | ❌ | ❌ |

### Tool Count

- **aerospace-mcp:** 34+ tools
- **aviation-weather-mcp:** ~10-15 tools (estimated)
- **blevinstein/aviation-mcp:** Variable (depends on version)

## Next Steps

1. **Install missing servers** (aviation-weather-mcp and blevinstein/aviation-mcp)
2. **Run verification** to ensure all servers connect
3. **Try the demo** to see multi-server capabilities
4. **Build custom agents** that leverage all aviation tools

## Resources

- **MCP Documentation:** https://modelcontextprotocol.io/
- **MCP Server Registry:** https://github.com/modelcontextprotocol/servers
- **This Project's MCP Integration:** See `docs/MCP_INTEGRATION.md`

## Support

If you encounter issues:

1. Check this guide's troubleshooting section
2. Run `python verify_all_mcp_servers.py` for diagnostics
3. Review server logs in the terminal output
4. Check individual MCP server repositories for specific issues

---

**Note:** The system works with any combination of these servers. You don't need all three installed - it will automatically use whatever is available.
