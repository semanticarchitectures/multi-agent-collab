#!/usr/bin/env python3
"""
Test Mission Snapshots

Simple test script to verify mission snapshot functionality.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from src.utils.mission_snapshots import MissionSnapshotManager
    
    print("=" * 80)
    print("MISSION SNAPSHOTS TEST")
    print("=" * 80)
    
    # Create manager
    manager = MissionSnapshotManager()
    
    # List mission types
    print("\n📋 Available Mission Types:")
    for mission_type in manager.list_mission_types():
        print(f"  • {mission_type}")
    
    # Test airdrop snapshots
    print("\n🪂 Airdrop Mission Snapshots:")
    print("-" * 80)
    
    for snapshot_id in manager.list_snapshots("airdrop_mission_snapshots"):
        snapshot = manager.get_snapshot("airdrop_mission_snapshots", snapshot_id)
        print(f"\n  ID: {snapshot_id}")
        print(f"  Name: {snapshot.name}")
        print(f"  Phase: {snapshot.mission_phase}")
        print(f"  Position: {snapshot.latitude:.4f}°N, {abs(snapshot.longitude):.4f}°W")
        print(f"  Altitude: {snapshot.altitude_msl:.0f} ft MSL")
        print(f"  Heading: {snapshot.heading:.0f}°, Airspeed: {snapshot.airspeed:.0f} kts")
        if snapshot.time_into_mission:
            print(f"  Time: {snapshot.time_into_mission}")
    
    # Test surveillance snapshots
    print("\n\n🔍 Surveillance Mission Snapshots:")
    print("-" * 80)
    
    for snapshot_id in manager.list_snapshots("surveillance_mission_snapshots"):
        snapshot = manager.get_snapshot("surveillance_mission_snapshots", snapshot_id)
        print(f"\n  ID: {snapshot_id}")
        print(f"  Name: {snapshot.name}")
        print(f"  Phase: {snapshot.mission_phase}")
        print(f"  Position: {snapshot.latitude:.4f}°N, {abs(snapshot.longitude):.4f}°W")
        print(f"  Altitude: {snapshot.altitude_msl:.0f} ft MSL")
    
    # Test snapshot conversion to simulator params
    print("\n\n🎮 Simulator Initialization Test:")
    print("-" * 80)
    
    snapshot = manager.get_snapshot("airdrop_mission_snapshots", "on_station_pre_drop")
    print(f"\nSnapshot: {snapshot.name}")
    print(f"\nInitialization Message:")
    print(f"  {snapshot.get_initialization_message()}")
    
    print(f"\nSimulator Parameters:")
    params = snapshot.to_simulator_init_params()
    for key, value in params.items():
        print(f"  {key}: {value}")
    
    print(f"\nContext Message:")
    print(snapshot.get_context_message())
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("=" * 80)
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\nMake sure you have installed the required dependencies:")
    print("  pip install pyyaml")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

