# Quick Start: Mission Snapshots

## What Are Mission Snapshots?

Mission snapshots let you **jump to any point in a mission** without simulating the entire flight. Perfect for:
- 🎯 **Training specific procedures** (e.g., practice airdrops without flying to the drop zone)
- ⚡ **Saving time** (skip transit, start at the action)
- 🔬 **Testing scenarios** (reproduce specific mission states)
- 🎓 **Focused learning** (practice one phase at a time)

## Quick Commands

### List Available Snapshots

```bash
# Airdrop mission snapshots
python run_airdrop_mission.py --list-snapshots

# Surveillance mission snapshots
python run_surveillance_mission.py --list-snapshots
```

### Start Mission from Snapshot

```bash
# Start airdrop mission ready for drop (most useful!)
python run_airdrop_mission.py --snapshot on_station_pre_drop

# Start airdrop mission during active drop
python run_airdrop_mission.py --snapshot drop_run_active

# Start surveillance mission already on patrol
python run_surveillance_mission.py --snapshot on_station_patrol
```

## Available Airdrop Snapshots

| Snapshot ID | Description | Best For |
|------------|-------------|----------|
| `pre_takeoff` | On ground, ready to depart | Full mission practice |
| `enroute_to_dz` | Flying to drop zone | Navigation practice |
| `on_station_pre_drop` | **Ready for drop run** | **Airdrop procedures** ⭐ |
| `drop_run_active` | First pallet released | Mid-drop procedures |
| `post_drop_observation` | All pallets dropped | Post-drop procedures |
| `return_to_base` | Heading home | Return/landing practice |

## Available Surveillance Snapshots

| Snapshot ID | Description | Best For |
|------------|-------------|----------|
| `departure` | Just airborne | Departure procedures |
| `on_station_patrol` | **In patrol area** | **Surveillance ops** ⭐ |

## Example Workflow

### Practice Airdrop Procedures

```bash
# 1. Start at drop zone (skip 40 minutes of transit)
python run_airdrop_mission.py --snapshot on_station_pre_drop

# 2. The simulator is already initialized at:
#    - Position: 2 NM east of drop zone
#    - Altitude: 1500 ft AGL
#    - Airspeed: 120 knots
#    - Heading: 270° (westbound for drop)
#    - All 6 pallets loaded

# 3. Interact with crew:
"Loadmaster, open the cargo door and prepare for drop"
"Pilot, begin the drop run"
"What is our current position relative to the drop zone?"
```

### Practice Surveillance Operations

```bash
# 1. Start already on station (skip 45 minutes)
python run_surveillance_mission.py --snapshot on_station_patrol

# 2. The simulator is already initialized at:
#    - Position: Center of patrol area
#    - Altitude: 5000 ft
#    - Airspeed: 180 knots
#    - In racetrack pattern

# 3. Interact with crew:
"Sensor operator, activate the radar and begin scanning"
"What vessels do you detect in the area?"
"Classify the contacts and report"
```

## What Happens When You Use a Snapshot?

1. **Snapshot loads** - Mission state is read from `configs/mission_snapshots.yaml`
2. **Simulator initializes** - Aircraft-sim-mcp is set to the exact position/state
3. **Context displayed** - You see mission phase, time, aircraft state
4. **Ready to go** - Start interacting immediately at that mission point

## Snapshot Details

Each snapshot includes:
- ✈️ **Aircraft position** (lat/lon/altitude/heading/airspeed)
- ⛽ **Aircraft state** (fuel, cargo, systems)
- 📍 **Mission phase** (where you are in the mission)
- ⏱️ **Time into mission** (how long you've been flying)
- 📋 **Next action** (what should happen next)

## Creating Custom Snapshots

Edit `configs/mission_snapshots.yaml`:

```yaml
my_custom_snapshot:
  name: "My Custom Starting Point"
  description: "Aircraft in a specific configuration"
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
  time_into_mission: "30 minutes"
  next_action: "Whatever you want to practice"
```

Then use it:
```bash
python run_airdrop_mission.py --snapshot my_custom_snapshot
```

## Tips

💡 **Most Useful Snapshots:**
- `on_station_pre_drop` - Practice the entire airdrop sequence
- `on_station_patrol` - Practice surveillance and vessel identification

💡 **Realistic State:**
- Fuel consumption is accurate to mission time
- Aircraft weight reflects cargo status
- Position matches mission geography

💡 **Combine with MCP Tools:**
- Use weather tools to check conditions
- Use aerospace tools for calculations
- Use simulator tools to control aircraft

## Troubleshooting

**Snapshot not found?**
```bash
# List available snapshots
python run_airdrop_mission.py --list-snapshots
```

**Simulator not initializing?**
- Check that aircraft-sim-mcp is running
- The mission will still work, just without live simulation

**Want to start from beginning?**
```bash
# Just run without --snapshot flag
python run_airdrop_mission.py
```

## Next Steps

1. ✅ Try `--list-snapshots` to see all options
2. ✅ Start with `on_station_pre_drop` or `on_station_patrol`
3. ✅ Practice specific procedures
4. ✅ Create your own custom snapshots

**Happy flying! 🚁**

