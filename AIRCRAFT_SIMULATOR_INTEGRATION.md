# Aircraft Simulator MCP Integration Guide

This guide explains how to integrate the `aircraft-sim-mcp` server to provide simulated aircraft data for your multi-agent aviation missions.

## ✅ Status: FULLY INTEGRATED AND WORKING!

**Integration Code**: ✅ Complete
**Server Status**: ✅ Fixed and working
**Test Status**: ✅ All tests passing

### What Was Fixed

The `aircraft-sim-mcp` server had two issues that have been resolved:

1. **Import Error** - Fixed incorrect import:
   ```python
   # Before (broken):
   from mcp.server.fastmcp.prompts import base_context

   # After (fixed):
   from mcp.server.fastmcp import Context
   ```

2. **Missing Main Block** - Added `if __name__ == "__main__"` block to allow the server to run as a module

### Integration Complete

✅ Added `initialize_aircraft_sim_mcp()` function to `src/mcp/mcp_manager.py`
✅ Updated `initialize_all_aviation_mcps()` to include aircraft simulator
✅ Updated `run_airdrop_mission.py` to auto-connect to aircraft simulator
✅ Updated `run_surveillance_mission.py` to auto-connect to aircraft simulator
✅ Created integration test script (`test_aircraft_sim_integration.py`)
✅ Fixed server import errors
✅ Verified 14 tools are available and working

## Overview

The **aircraft-sim-mcp** server wraps the JSBSim high-fidelity flight dynamics engine, providing:
- **Physics-based flight simulation** (NASA/DoD quality)
- **Real-time telemetry** (position, attitude, airspeed, engines, fuel)
- **Flight controls** (throttle, elevator, aileron, rudder, flaps)
- **Role-based access control** (pilots can control, others can monitor)
- **Multi-agent coordination** for realistic crew operations

## What It Provides

### Available Aircraft Models
- **C-130 Hercules** - 4-engine turboprop cargo aircraft (perfect for airdrop missions)
- **Cessna 172** - Single-engine trainer aircraft
- More models can be added via JSBSim aircraft definitions

### MCP Tools Available

#### Control Tools (Pilot/Co-pilot only)
- `set_throttle` - Set engine throttle (0.0-1.0)
- `set_elevator` - Pitch control (-1.0 to 1.0)
- `set_aileron` - Roll control (-1.0 to 1.0)
- `set_rudder` - Yaw control (-1.0 to 1.0)
- `set_flaps` - Flap position (0.0-1.0)
- `set_wind` - Wind conditions (north/east components in knots)
- `advance_simulation` - Advance simulation time
- `reset_simulation` - Reset with new aircraft/conditions

#### Monitoring Tools (All crew members)
- `get_position` - Latitude, longitude, altitude MSL/AGL
- `get_attitude` - Pitch, roll, heading
- `get_airspeed` - Indicated, true, and ground speed
- `get_telemetry` - Complete aircraft state
- `get_engines` - Engine status (RPM, throttle, running)
- `get_fuel` - Fuel status (total, percentage)

### Role-Based Access Control

| Role | Control Tools | Monitoring Tools |
|------|---------------|------------------|
| Pilot | ✅ Full | ✅ Full |
| Co-pilot | ✅ Full | ✅ Full |
| Flight Engineer | ❌ None | ✅ Full |
| Loadmaster | ❌ None | ✅ Full |
| Navigator | ❌ None | ✅ Full |

## Installation

The `aircraft-sim-mcp` server is already installed in the parent directory at:
```
/Users/kevinkelly/Documents/claude-projects/agentDemo/aircraft-sim-mcp
```

### Verify Installation

```bash
cd ../aircraft-sim-mcp
source venv/bin/activate
python -c "import jsbsim; print('JSBSim installed:', jsbsim.__version__)"
```

### Run Tests

```bash
cd ../aircraft-sim-mcp
source venv/bin/activate
PYTHONPATH=src pytest tests/ -v
```

## Integration Status

✅ **ALREADY INTEGRATED** - The aircraft simulator MCP is now automatically initialized in:
- `run_airdrop_mission.py`
- `run_surveillance_mission.py`

The integration code in `src/mcp/mcp_manager.py` includes:
- `initialize_aircraft_sim_mcp()` - Connects to the simulator server
- `initialize_all_aviation_mcps()` - Now includes aircraft-sim-mcp

## Usage in Your Scripts

### Automatic Integration (Already Done)

Both mission scripts now automatically connect to the aircraft simulator:

```python
# This happens automatically when you run the scripts
mcp_results = await initialize_all_aviation_mcps(
    aerospace_path=aerospace_path if Path(aerospace_path).exists() else None,
    aviation_weather_path=aviation_weather_path if Path(aviation_weather_path).exists() else None,
    blevinstein_aviation_path=blevinstein_path if Path(blevinstein_path).exists() else None,
    aircraft_sim_path=aircraft_sim_path if Path(aircraft_sim_path).exists() else None
)
```

When you run the mission, you'll see:
```
Initializing MCP servers for aviation tools...
✓ Connected to aerospace-mcp
✓ Connected to aircraft-sim-mcp
```

### How Agents Use the Simulator

Agents with MCP access can now:

1. **Initialize a flight simulation**:
   ```
   "Reset the simulator with a C-130 at 10,000 ft MSL, heading 270°, 200 knots"
   ```

2. **Monitor aircraft state**:
   ```
   "What is our current position and altitude?"
   "Check engine status for all four engines"
   "What's our fuel remaining?"
   ```

3. **Control the aircraft** (pilots only):
   ```
   "Set throttle to 75% on all engines"
   "Set flaps to 50%"
   "Adjust elevator to maintain 5° pitch up"
   ```

4. **Advance simulation**:
   ```
   "Advance the simulation by 60 seconds"
   ```

## Example: Airdrop Mission with Simulator

When running `run_airdrop_mission.py`, agents can now:

1. **Pre-flight**: Initialize C-130 at departure airport
2. **Takeoff**: Set throttle, monitor airspeed and altitude
3. **En route**: Monitor position, fuel, engines
4. **Drop zone approach**: Reduce speed to 120 KIAS, descend to 1500 FT AGL
5. **Airdrop**: Monitor precise altitude/airspeed during pallet releases
6. **Post-drop**: Monitor CG shift, adjust trim
7. **Return**: Monitor fuel consumption, navigate back to base

## Testing the Integration

### Quick Test

Run the airdrop mission and ask the crew:

```bash
python run_airdrop_mission.py
```

Then type:
```
Reset the simulator with a C-130 at KFMH, 1000 ft MSL, heading 050, 150 knots
```

The agents should be able to use the simulator tools to initialize and monitor the aircraft.

### Check Available Tools

After connecting, you can verify tools are available:

```python
from src.mcp.mcp_manager import get_mcp_manager

manager = await get_mcp_manager()
tools = manager.get_available_tools("aircraft-sim-mcp")
print(f"Aircraft simulator tools: {len(tools)}")
for tool in tools:
    print(f"  - {tool['name']}: {tool.get('description', 'No description')}")
```

## Troubleshooting

### Server Won't Connect

1. **Check if JSBSim is installed**:
   ```bash
   cd ../aircraft-sim-mcp
   source venv/bin/activate
   python -c "import jsbsim"
   ```

2. **Check server can run**:
   ```bash
   cd ../aircraft-sim-mcp
   source venv/bin/activate
   PYTHONPATH=src python -m flight_simulator_mcp.server
   ```

3. **Check logs**:
   Look in `./logs/agent-YYYYMMDD.log` for MCP connection errors

### Tools Not Available

Check that the server is in the MCP manager's sessions:
```python
manager = await get_mcp_manager()
print(manager.sessions.keys())  # Should include 'aircraft-sim-mcp'
```

## Next Steps

1. **Test the integration**: Run `python run_airdrop_mission.py` and interact with the simulator
2. **Create simulator-specific missions**: Design missions that leverage real-time flight dynamics
3. **Add autopilot features**: Extend the simulator with autopilot modes
4. **Integrate with other tools**: Combine simulator data with weather, airports, flight planning

## Documentation

For more details on the aircraft simulator:
- **README**: `../aircraft-sim-mcp/README.md`
- **MCP Integration**: `../aircraft-sim-mcp/MCP_INTEGRATION.md`
- **Capabilities**: `../aircraft-sim-mcp/CAPABILITIES.md`
- **Examples**: `../aircraft-sim-mcp/examples/`

