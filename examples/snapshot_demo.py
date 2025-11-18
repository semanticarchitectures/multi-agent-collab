#!/usr/bin/env python3
"""
Mission Snapshot Demonstration

This script demonstrates how to use mission snapshots programmatically.
It shows how to:
1. Load snapshots
2. Display snapshot information
3. Initialize the simulator from a snapshot
4. Use snapshots in your own scripts
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.mission_snapshots import MissionSnapshotManager
from src.mcp.mcp_manager import get_mcp_manager, initialize_all_aviation_mcps


async def demo_list_snapshots():
    """Demonstrate listing available snapshots."""
    print("=" * 80)
    print("DEMO 1: Listing Available Snapshots")
    print("=" * 80)
    
    manager = MissionSnapshotManager()
    
    print("\nMission Types:")
    for mission_type in manager.list_mission_types():
        print(f"  • {mission_type}")
        
        print(f"\n  Snapshots for {mission_type}:")
        for snapshot_id in manager.list_snapshots(mission_type):
            snapshot = manager.get_snapshot(mission_type, snapshot_id)
            print(f"    - {snapshot_id}: {snapshot.name}")
    
    print()


async def demo_snapshot_details():
    """Demonstrate getting detailed snapshot information."""
    print("=" * 80)
    print("DEMO 2: Snapshot Details")
    print("=" * 80)
    
    manager = MissionSnapshotManager()
    snapshot = manager.get_snapshot("airdrop_mission_snapshots", "on_station_pre_drop")
    
    print(f"\nSnapshot: {snapshot.name}")
    print(f"Description: {snapshot.description}")
    print(f"Mission Phase: {snapshot.mission_phase}")
    print(f"Time into Mission: {snapshot.time_into_mission}")
    
    print(f"\nAircraft Configuration:")
    print(f"  Model: {snapshot.aircraft_model}")
    print(f"  Position: {snapshot.latitude:.4f}°N, {abs(snapshot.longitude):.4f}°W")
    print(f"  Altitude: {snapshot.altitude_msl:.0f} ft MSL")
    print(f"  Heading: {snapshot.heading:.0f}°")
    print(f"  Airspeed: {snapshot.airspeed:.0f} knots")
    
    print(f"\nAircraft State:")
    for key, value in snapshot.aircraft_state.items():
        print(f"  {key}: {value}")
    
    print(f"\nNext Action: {snapshot.next_action}")
    print()


async def demo_simulator_initialization():
    """Demonstrate converting snapshot to simulator parameters."""
    print("=" * 80)
    print("DEMO 3: Simulator Initialization")
    print("=" * 80)
    
    manager = MissionSnapshotManager()
    snapshot = manager.get_snapshot("airdrop_mission_snapshots", "on_station_pre_drop")
    
    print(f"\nSnapshot: {snapshot.name}")
    
    # Get initialization message
    init_message = snapshot.get_initialization_message()
    print(f"\nInitialization Message:")
    print(f"  {init_message}")
    
    # Get simulator parameters
    params = snapshot.to_simulator_init_params()
    print(f"\nSimulator Parameters:")
    for key, value in params.items():
        print(f"  {key}: {value}")
    
    print(f"\nContext Message:")
    print(snapshot.get_context_message())
    print()


async def demo_mission_progression():
    """Demonstrate mission progression through snapshots."""
    print("=" * 80)
    print("DEMO 4: Mission Progression")
    print("=" * 80)
    
    manager = MissionSnapshotManager()
    
    progression = [
        "pre_takeoff",
        "enroute_to_dz",
        "on_station_pre_drop",
        "drop_run_active",
        "post_drop_observation",
        "return_to_base"
    ]
    
    print("\nAirdrop Mission Progression:\n")
    
    for i, snapshot_id in enumerate(progression, 1):
        snapshot = manager.get_snapshot("airdrop_mission_snapshots", snapshot_id)
        
        print(f"{i}. {snapshot.name}")
        print(f"   Phase: {snapshot.mission_phase}")
        print(f"   Altitude: {snapshot.altitude_msl:.0f} ft MSL")
        print(f"   Airspeed: {snapshot.airspeed:.0f} knots")
        print(f"   Fuel: {snapshot.aircraft_state['fuel_lbs']} lbs")
        
        if 'pallets_remaining' in snapshot.aircraft_state:
            print(f"   Pallets: {snapshot.aircraft_state['pallets_remaining']} remaining")
        
        if snapshot.time_into_mission:
            print(f"   Time: {snapshot.time_into_mission}")
        
        print()


async def demo_custom_usage():
    """Demonstrate using snapshots in custom code."""
    print("=" * 80)
    print("DEMO 5: Custom Usage Example")
    print("=" * 80)
    
    print("\nExample: Starting a mission from a specific snapshot\n")
    
    print("```python")
    print("from src.utils.mission_snapshots import MissionSnapshotManager")
    print()
    print("# Create manager")
    print("manager = MissionSnapshotManager()")
    print()
    print("# Get a snapshot")
    print("snapshot = manager.get_snapshot(")
    print("    'airdrop_mission_snapshots',")
    print("    'on_station_pre_drop'")
    print(")")
    print()
    print("# Use in your mission script")
    print("if snapshot:")
    print("    # Initialize simulator")
    print("    params = snapshot.to_simulator_init_params()")
    print("    await client.call_tool('reset_simulation', params)")
    print("    ")
    print("    # Display context to crew")
    print("    print(snapshot.get_context_message())")
    print("    ")
    print("    # Start mission at this point")
    print("    # ... your mission code here ...")
    print("```")
    print()


async def main():
    """Run all demonstrations."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "MISSION SNAPSHOT DEMONSTRATION" + " " * 28 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    await demo_list_snapshots()
    await demo_snapshot_details()
    await demo_simulator_initialization()
    await demo_mission_progression()
    await demo_custom_usage()
    
    print("=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80)
    print("\nNext steps:")
    print("  1. Try: python run_airdrop_mission.py --list-snapshots")
    print("  2. Try: python run_airdrop_mission.py --snapshot on_station_pre_drop")
    print("  3. Read: QUICK_START_SNAPSHOTS.md")
    print("  4. Read: MISSION_SNAPSHOTS_GUIDE.md")
    print()


if __name__ == "__main__":
    asyncio.run(main())

