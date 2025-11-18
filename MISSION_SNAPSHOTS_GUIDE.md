# Mission Snapshots Guide

## Overview

**Mission Snapshots** allow you to start a simulation at a specific point in a mission without having to simulate the entire flight from takeoff. This is useful for:

- **Training specific mission phases** (e.g., practicing airdrop procedures without flying to the drop zone)
- **Testing scenarios** (e.g., testing post-drop procedures)
- **Debugging** (e.g., reproducing issues at a specific mission point)
- **Time efficiency** (e.g., skipping transit time to focus on critical mission phases)

## Quick Start

### List Available Snapshots

```bash
# List all snapshots for all missions
python run_mission_from_snapshot.py --list-snapshots all

# List snapshots for airdrop mission
python run_mission_from_snapshot.py --list-snapshots airdrop

# List snapshots for surveillance mission
python run_mission_from_snapshot.py --list-snapshots surveillance
```

### Run Mission from Snapshot

```bash
# Start airdrop mission at "on station, ready for drop"
python run_mission_from_snapshot.py --mission airdrop --snapshot on_station_pre_drop

# Start airdrop mission during active drop run
python run_mission_from_snapshot.py --mission airdrop --snapshot drop_run_active

# Start surveillance mission already on station
python run_mission_from_snapshot.py --mission surveillance --snapshot on_station_patrol
```

## Available Snapshots

### Airdrop Mission Snapshots

1. **pre_takeoff** - Pre-Takeoff at Otis ANGB
   - Aircraft loaded with cargo, crew briefed, ready for departure
   - All 6 pallets loaded
   - Engines not running
   - Use this to practice the entire mission from start

2. **enroute_to_dz** - Enroute to Drop Zone
   - Climbing out, heading toward drop zone
   - 15 minutes into mission
   - Use this to skip takeoff and practice navigation to drop zone

3. **on_station_pre_drop** - On Station - Ready for Drop Run
   - Established at drop altitude (1500 ft AGL)
   - Approaching initial point for drop run
   - All 6 pallets still loaded
   - 40 minutes into mission
   - **Most useful for practicing airdrop procedures**

4. **drop_run_active** - Drop Run - First Pallet Released
   - On drop run heading
   - First pallet just released, 5 remaining
   - Cargo door open
   - Use this to practice mid-drop procedures

5. **post_drop_observation** - Post-Drop Observation
   - All pallets released
   - Climbing turn to observe results
   - Cargo door secured
   - Use this to practice post-drop procedures and documentation

6. **return_to_base** - Return to Base
   - Mission complete, heading back to Otis ANGB
   - Use this to practice return and landing procedures

### Surveillance Mission Snapshots

1. **departure** - Departure from Otis ANGB
   - Just airborne, climbing out
   - Use this to practice departure procedures

2. **on_station_patrol** - On Station - Patrol Area
   - Established in racetrack pattern over surveillance area
   - Radar and sensors active
   - 45 minutes into mission
   - **Most useful for practicing surveillance operations**

## How It Works

### 1. Snapshot Configuration

Snapshots are defined in `configs/mission_snapshots.yaml`. Each snapshot includes:

- **Position**: Latitude, longitude, altitude, heading, airspeed
- **Aircraft State**: Fuel, cargo, engines, etc.
- **Mission Phase**: What phase of the mission you're in
- **Context**: Time into mission, next actions

Example snapshot:
```yaml
on_station_pre_drop:
  name: "On Station - Ready for Drop Run"
  description: "Established at drop altitude, approaching initial point for drop run"
  aircraft_model: "C130"
  position:
    latitude: 41.5500
    longitude: -69.9667
    altitude_msl: 1515
    heading: 270
    airspeed: 120
  aircraft_state:
    engines_running: true
    cargo_loaded: true
    pallets_remaining: 6
    fuel_lbs: 5400
  mission_phase: "ON_STATION_PRE_DROP"
  time_into_mission: "40 minutes"
  next_action: "Open cargo door and begin drop run"
```

### 2. Snapshot Loading

The `MissionSnapshotManager` class loads snapshots from the YAML file and provides methods to:
- List available snapshots
- Get specific snapshots
- Convert snapshots to simulator initialization parameters

### 3. Simulator Initialization

When you run a mission from a snapshot:
1. The snapshot is loaded from the configuration
2. The aircraft simulator is initialized with the snapshot's position and state
3. The mission context is displayed to the crew
4. You can immediately start interacting with the crew at that mission phase

## Using Snapshots in Your Own Scripts

### Basic Usage

```python
from src.utils.mission_snapshots import MissionSnapshotManager

# Create manager
manager = MissionSnapshotManager()

# Get a snapshot
snapshot = manager.get_snapshot("airdrop_mission_snapshots", "on_station_pre_drop")

# Get simulator initialization message
init_message = snapshot.get_initialization_message()
# "Reset the simulator with a C130 at 41.5500°N, 69.9667°W, 1515 ft MSL, heading 270°, 120 knots"

# Get context message for the crew
context = snapshot.get_context_message()
print(context)
```

### Integration with MCP Simulator

```python
from src.mcp.mcp_manager import get_mcp_manager

# Get the simulator client
manager = await get_mcp_manager()
client = manager.get_client("aircraft-sim-mcp")

# Initialize simulator from snapshot
params = snapshot.to_simulator_init_params()
result = await client.call_tool("reset_simulation", params)
```

### Integration with Mission Scripts

You can modify `run_airdrop_mission.py` or `run_surveillance_mission.py` to accept a `--snapshot` parameter:

```python
# Add to argument parser
parser.add_argument("--snapshot", help="Start from a specific mission snapshot")

# In main function
if args.snapshot:
    manager = MissionSnapshotManager()
    snapshot = manager.get_snapshot("airdrop_mission_snapshots", args.snapshot)
    
    # Initialize simulator
    # ... (see run_mission_from_snapshot.py for full example)
```

## Creating Custom Snapshots

To create your own snapshots:

1. **Edit** `configs/mission_snapshots.yaml`
2. **Add a new snapshot** under the appropriate mission type
3. **Define the snapshot parameters**:
   - `name`: Short descriptive name
   - `description`: What this snapshot represents
   - `aircraft_model`: Aircraft type (e.g., "C130")
   - `position`: Lat/lon/alt/heading/airspeed
   - `aircraft_state`: Fuel, cargo, systems state
   - `mission_phase`: Phase identifier
   - `time_into_mission`: (optional) How far into the mission
   - `next_action`: (optional) What should happen next

Example:
```yaml
my_custom_snapshot:
  name: "My Custom Starting Point"
  description: "Aircraft in a specific configuration I want to test"
  aircraft_model: "C130"
  position:
    latitude: 41.5000
    longitude: -70.0000
    altitude_msl: 2000
    heading: 180
    airspeed: 150
  aircraft_state:
    engines_running: true
    fuel_lbs: 5000
  mission_phase: "CUSTOM_PHASE"
```

## Benefits

✅ **Save Time** - Skip transit phases and jump to critical mission points
✅ **Focused Training** - Practice specific procedures without full mission overhead
✅ **Reproducibility** - Start from the same point every time for testing
✅ **Flexibility** - Create custom snapshots for any scenario you need
✅ **Realistic State** - Snapshots include fuel burn, weight changes, and mission context

## Next Steps

1. Try running a mission from a snapshot
2. Experiment with different snapshots to see how they work
3. Create your own custom snapshots for specific training scenarios
4. Integrate snapshot support into your mission scripts

