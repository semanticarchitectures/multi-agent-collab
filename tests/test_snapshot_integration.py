"""
Integration tests for mission snapshot functionality with MCP simulator.
"""

import pytest
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.mission_snapshots import MissionSnapshotManager
from src.mcp.mcp_manager import get_mcp_manager, initialize_all_aviation_mcps


@pytest.mark.asyncio
class TestSnapshotSimulatorIntegration:
    """Test integration between snapshots and the aircraft simulator."""
    
    async def test_snapshot_to_simulator_params(self):
        """Test that snapshot parameters are correctly formatted for simulator."""
        manager = MissionSnapshotManager()
        snapshot = manager.get_snapshot("airdrop_mission_snapshots", "on_station_pre_drop")
        
        params = snapshot.to_simulator_init_params()
        
        # Verify all required parameters are present
        required_params = ["aircraft_model", "latitude", "longitude", "altitude_msl", "heading", "airspeed"]
        for param in required_params:
            assert param in params, f"Missing required parameter: {param}"
        
        # Verify parameter types
        assert isinstance(params["aircraft_model"], str)
        assert isinstance(params["latitude"], (int, float))
        assert isinstance(params["longitude"], (int, float))
        assert isinstance(params["altitude_msl"], (int, float))
        assert isinstance(params["heading"], (int, float))
        assert isinstance(params["airspeed"], (int, float))
        
        # Verify parameter ranges
        assert -90 <= params["latitude"] <= 90
        assert -180 <= params["longitude"] <= 180
        assert params["altitude_msl"] >= 0
        assert 0 <= params["heading"] <= 360
        assert params["airspeed"] >= 0
    
    async def test_all_snapshots_have_valid_simulator_params(self):
        """Test that all snapshots can generate valid simulator parameters."""
        manager = MissionSnapshotManager()
        
        for mission_type in manager.list_mission_types():
            for snapshot_id in manager.list_snapshots(mission_type):
                snapshot = manager.get_snapshot(mission_type, snapshot_id)
                
                # Should not raise an exception
                params = snapshot.to_simulator_init_params()
                
                # Verify structure
                assert len(params) == 6
                assert all(key in params for key in ["aircraft_model", "latitude", "longitude", "altitude_msl", "heading", "airspeed"])
    
    async def test_snapshot_initialization_message_format(self):
        """Test that initialization messages are properly formatted."""
        manager = MissionSnapshotManager()
        
        for mission_type in manager.list_mission_types():
            for snapshot_id in manager.list_snapshots(mission_type):
                snapshot = manager.get_snapshot(mission_type, snapshot_id)
                
                message = snapshot.get_initialization_message()
                
                # Message should contain key information
                assert "Reset the simulator" in message
                assert snapshot.aircraft_model in message
                assert "ft MSL" in message
                assert "knots" in message
    
    async def test_snapshot_context_message_completeness(self):
        """Test that context messages contain all necessary information."""
        manager = MissionSnapshotManager()
        snapshot = manager.get_snapshot("airdrop_mission_snapshots", "on_station_pre_drop")
        
        context = snapshot.get_context_message()
        
        # Should contain mission snapshot header
        assert "Mission Snapshot" in context
        assert snapshot.name in context
        
        # Should contain mission phase
        assert "Mission Phase" in context
        assert snapshot.mission_phase in context
        
        # Should contain aircraft state
        assert "Aircraft State" in context
        
        # Should contain time if available
        if snapshot.time_into_mission:
            assert "Time into Mission" in context
            assert snapshot.time_into_mission in context
        
        # Should contain next action if available
        if snapshot.next_action:
            assert "Next Action" in context
            assert snapshot.next_action in context
    
    async def test_airdrop_snapshot_progression(self):
        """Test that airdrop snapshots represent logical mission progression."""
        manager = MissionSnapshotManager()
        
        # Define expected progression
        progression = [
            "pre_takeoff",
            "enroute_to_dz",
            "on_station_pre_drop",
            "drop_run_active",
            "post_drop_observation",
            "return_to_base"
        ]
        
        snapshots = []
        for snapshot_id in progression:
            snapshot = manager.get_snapshot("airdrop_mission_snapshots", snapshot_id)
            assert snapshot is not None, f"Missing snapshot: {snapshot_id}"
            snapshots.append(snapshot)
        
        # Verify altitude progression makes sense
        # Should be low at takeoff, climb, then descend for drop, then climb again
        assert snapshots[0].altitude_msl < 500  # Pre-takeoff on ground
        assert snapshots[1].altitude_msl > snapshots[0].altitude_msl  # Climbing
        assert snapshots[2].altitude_msl < snapshots[1].altitude_msl  # Descending to drop altitude
        assert snapshots[4].altitude_msl > snapshots[3].altitude_msl  # Climbing after drop
        
        # Verify airspeed progression
        assert snapshots[0].airspeed == 0  # Stationary on ground
        assert snapshots[2].airspeed == 120  # Drop airspeed
        assert snapshots[3].airspeed == 120  # Maintaining drop airspeed
        
        # Verify pallets remaining decreases
        assert snapshots[2].aircraft_state["pallets_remaining"] == 6  # Before drop
        assert snapshots[3].aircraft_state["pallets_remaining"] == 5  # One dropped
        assert snapshots[4].aircraft_state["pallets_remaining"] == 0  # All dropped
    
    async def test_fuel_consumption_progression(self):
        """Test that fuel decreases logically through mission snapshots."""
        manager = MissionSnapshotManager()
        
        # Get snapshots with time progression
        pre_takeoff = manager.get_snapshot("airdrop_mission_snapshots", "pre_takeoff")
        enroute = manager.get_snapshot("airdrop_mission_snapshots", "enroute_to_dz")
        on_station = manager.get_snapshot("airdrop_mission_snapshots", "on_station_pre_drop")
        post_drop = manager.get_snapshot("airdrop_mission_snapshots", "post_drop_observation")
        rtb = manager.get_snapshot("airdrop_mission_snapshots", "return_to_base")
        
        # Fuel should decrease over time
        assert pre_takeoff.aircraft_state["fuel_lbs"] > enroute.aircraft_state["fuel_lbs"]
        assert enroute.aircraft_state["fuel_lbs"] > on_station.aircraft_state["fuel_lbs"]
        assert on_station.aircraft_state["fuel_lbs"] > post_drop.aircraft_state["fuel_lbs"]
        assert post_drop.aircraft_state["fuel_lbs"] > rtb.aircraft_state["fuel_lbs"]
    
    async def test_geographic_progression(self):
        """Test that aircraft position changes logically through mission."""
        manager = MissionSnapshotManager()
        
        pre_takeoff = manager.get_snapshot("airdrop_mission_snapshots", "pre_takeoff")
        enroute = manager.get_snapshot("airdrop_mission_snapshots", "enroute_to_dz")
        on_station = manager.get_snapshot("airdrop_mission_snapshots", "on_station_pre_drop")
        
        # Should move from KFMH toward drop zone
        # KFMH is around 41.65°N, 70.52°W
        # Drop zone is around 41.55°N, 69.98°W (east and south)
        
        # Latitude should decrease (moving south)
        assert pre_takeoff.latitude > on_station.latitude
        
        # Longitude should increase (moving east, less negative)
        assert pre_takeoff.longitude < on_station.longitude

