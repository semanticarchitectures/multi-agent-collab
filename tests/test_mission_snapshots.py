"""
Unit tests for mission snapshot functionality.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.mission_snapshots import MissionSnapshotManager, MissionSnapshot


class TestMissionSnapshotManager:
    """Test the MissionSnapshotManager class."""
    
    def test_manager_initialization(self):
        """Test that the manager initializes correctly."""
        manager = MissionSnapshotManager()
        assert manager is not None
        assert len(manager.snapshots) > 0
    
    def test_list_mission_types(self):
        """Test listing mission types."""
        manager = MissionSnapshotManager()
        mission_types = manager.list_mission_types()
        
        assert "airdrop_mission_snapshots" in mission_types
        assert "surveillance_mission_snapshots" in mission_types
    
    def test_list_airdrop_snapshots(self):
        """Test listing airdrop mission snapshots."""
        manager = MissionSnapshotManager()
        snapshots = manager.list_snapshots("airdrop_mission_snapshots")
        
        assert "pre_takeoff" in snapshots
        assert "on_station_pre_drop" in snapshots
        assert "drop_run_active" in snapshots
        assert "post_drop_observation" in snapshots
        assert "return_to_base" in snapshots
    
    def test_list_surveillance_snapshots(self):
        """Test listing surveillance mission snapshots."""
        manager = MissionSnapshotManager()
        snapshots = manager.list_snapshots("surveillance_mission_snapshots")
        
        assert "departure" in snapshots
        assert "on_station_patrol" in snapshots
    
    def test_get_snapshot(self):
        """Test getting a specific snapshot."""
        manager = MissionSnapshotManager()
        snapshot = manager.get_snapshot("airdrop_mission_snapshots", "on_station_pre_drop")
        
        assert snapshot is not None
        assert isinstance(snapshot, MissionSnapshot)
        assert snapshot.name == "On Station - Ready for Drop Run"
        assert snapshot.mission_phase == "ON_STATION_PRE_DROP"
    
    def test_get_nonexistent_snapshot(self):
        """Test getting a snapshot that doesn't exist."""
        manager = MissionSnapshotManager()
        snapshot = manager.get_snapshot("airdrop_mission_snapshots", "nonexistent")
        
        assert snapshot is None
    
    def test_get_snapshot_summary(self):
        """Test getting a summary of snapshots."""
        manager = MissionSnapshotManager()
        summary = manager.get_snapshot_summary("airdrop_mission_snapshots")
        
        assert "on_station_pre_drop" in summary
        assert "On Station - Ready for Drop Run" in summary


class TestMissionSnapshot:
    """Test the MissionSnapshot class."""
    
    def test_snapshot_attributes(self):
        """Test that snapshot has all required attributes."""
        manager = MissionSnapshotManager()
        snapshot = manager.get_snapshot("airdrop_mission_snapshots", "on_station_pre_drop")
        
        assert snapshot.name is not None
        assert snapshot.description is not None
        assert snapshot.aircraft_model is not None
        assert snapshot.latitude is not None
        assert snapshot.longitude is not None
        assert snapshot.altitude_msl is not None
        assert snapshot.heading is not None
        assert snapshot.airspeed is not None
        assert snapshot.aircraft_state is not None
        assert snapshot.mission_phase is not None
    
    def test_to_simulator_init_params(self):
        """Test conversion to simulator initialization parameters."""
        manager = MissionSnapshotManager()
        snapshot = manager.get_snapshot("airdrop_mission_snapshots", "on_station_pre_drop")
        
        params = snapshot.to_simulator_init_params()
        
        assert "aircraft_model" in params
        assert "latitude" in params
        assert "longitude" in params
        assert "altitude_msl" in params
        assert "heading" in params
        assert "airspeed" in params
        
        assert params["aircraft_model"] == "C130"
        assert params["latitude"] == 41.5500
        assert params["altitude_msl"] == 1515
        assert params["heading"] == 270
        assert params["airspeed"] == 120
    
    def test_get_initialization_message(self):
        """Test getting initialization message."""
        manager = MissionSnapshotManager()
        snapshot = manager.get_snapshot("airdrop_mission_snapshots", "on_station_pre_drop")
        
        message = snapshot.get_initialization_message()
        
        assert "C130" in message
        assert "41.5500" in message
        assert "1515" in message
        assert "270" in message
        assert "120" in message
    
    def test_get_context_message(self):
        """Test getting context message."""
        manager = MissionSnapshotManager()
        snapshot = manager.get_snapshot("airdrop_mission_snapshots", "on_station_pre_drop")
        
        context = snapshot.get_context_message()
        
        assert "On Station - Ready for Drop Run" in context
        assert "ON_STATION_PRE_DROP" in context
        assert "40 minutes" in context
        assert "Aircraft State" in context
    
    def test_all_airdrop_snapshots_valid(self):
        """Test that all airdrop snapshots are valid."""
        manager = MissionSnapshotManager()
        
        for snapshot_id in manager.list_snapshots("airdrop_mission_snapshots"):
            snapshot = manager.get_snapshot("airdrop_mission_snapshots", snapshot_id)
            
            # Check required fields
            assert snapshot.name is not None
            assert snapshot.aircraft_model is not None
            assert snapshot.latitude is not None
            assert snapshot.longitude is not None
            assert snapshot.altitude_msl >= 0
            assert 0 <= snapshot.heading <= 360
            assert snapshot.airspeed >= 0
            
            # Check simulator params can be generated
            params = snapshot.to_simulator_init_params()
            assert len(params) == 6
    
    def test_all_surveillance_snapshots_valid(self):
        """Test that all surveillance snapshots are valid."""
        manager = MissionSnapshotManager()
        
        for snapshot_id in manager.list_snapshots("surveillance_mission_snapshots"):
            snapshot = manager.get_snapshot("surveillance_mission_snapshots", snapshot_id)
            
            # Check required fields
            assert snapshot.name is not None
            assert snapshot.aircraft_model is not None
            assert snapshot.latitude is not None
            assert snapshot.longitude is not None
            assert snapshot.altitude_msl >= 0
            assert 0 <= snapshot.heading <= 360
            assert snapshot.airspeed >= 0

