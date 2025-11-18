"""
Mission Snapshot Utilities

Provides functionality to load and apply mission snapshots, allowing simulations
to start at specific points in a mission (e.g., on station, during drop run)
without simulating the entire flight from takeoff.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class MissionSnapshot:
    """Represents a snapshot of mission state at a specific point in time."""
    
    name: str
    description: str
    aircraft_model: str
    latitude: float
    longitude: float
    altitude_msl: float
    heading: float
    airspeed: float
    aircraft_state: Dict[str, Any]
    mission_phase: str
    time_into_mission: Optional[str] = None
    next_action: Optional[str] = None
    
    def to_simulator_init_params(self) -> Dict[str, Any]:
        """Convert snapshot to parameters for reset_simulation tool."""
        return {
            "aircraft_model": self.aircraft_model,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "altitude_msl": self.altitude_msl,
            "heading": self.heading,
            "airspeed": self.airspeed
        }
    
    def get_initialization_message(self) -> str:
        """Get a formatted message for initializing the simulator with this snapshot."""
        return (
            f"Reset the simulator with a {self.aircraft_model} at "
            f"{self.latitude:.4f}°N, {abs(self.longitude):.4f}°W, "
            f"{self.altitude_msl:.0f} ft MSL, "
            f"heading {self.heading:.0f}°, "
            f"{self.airspeed:.0f} knots"
        )
    
    def get_context_message(self) -> str:
        """Get a formatted context message describing the mission state."""
        msg = f"**Mission Snapshot: {self.name}**\n\n"
        msg += f"{self.description}\n\n"
        msg += f"**Mission Phase:** {self.mission_phase}\n"
        
        if self.time_into_mission:
            msg += f"**Time into Mission:** {self.time_into_mission}\n"
        
        msg += f"\n**Aircraft State:**\n"
        for key, value in self.aircraft_state.items():
            formatted_key = key.replace('_', ' ').title()
            msg += f"  - {formatted_key}: {value}\n"
        
        if self.next_action:
            msg += f"\n**Next Action:** {self.next_action}\n"
        
        return msg


class MissionSnapshotManager:
    """Manages loading and accessing mission snapshots."""
    
    def __init__(self, snapshots_file: str = "configs/mission_snapshots.yaml"):
        """
        Initialize the snapshot manager.
        
        Args:
            snapshots_file: Path to the YAML file containing mission snapshots
        """
        self.snapshots_file = Path(snapshots_file)
        self.snapshots: Dict[str, Dict[str, MissionSnapshot]] = {}
        self._load_snapshots()
    
    def _load_snapshots(self):
        """Load snapshots from the YAML file."""
        if not self.snapshots_file.exists():
            raise FileNotFoundError(f"Snapshots file not found: {self.snapshots_file}")
        
        with open(self.snapshots_file, 'r') as f:
            data = yaml.safe_load(f)
        
        # Parse each mission type's snapshots
        for mission_type, snapshots_dict in data.items():
            self.snapshots[mission_type] = {}
            
            for snapshot_id, snapshot_data in snapshots_dict.items():
                # Extract position data
                pos = snapshot_data['position']
                
                # Create snapshot object
                snapshot = MissionSnapshot(
                    name=snapshot_data['name'],
                    description=snapshot_data['description'],
                    aircraft_model=snapshot_data['aircraft_model'],
                    latitude=pos['latitude'],
                    longitude=pos['longitude'],
                    altitude_msl=pos['altitude_msl'],
                    heading=pos['heading'],
                    airspeed=pos['airspeed'],
                    aircraft_state=snapshot_data['aircraft_state'],
                    mission_phase=snapshot_data['mission_phase'],
                    time_into_mission=snapshot_data.get('time_into_mission'),
                    next_action=snapshot_data.get('next_action')
                )
                
                self.snapshots[mission_type][snapshot_id] = snapshot
    
    def get_snapshot(self, mission_type: str, snapshot_id: str) -> Optional[MissionSnapshot]:
        """
        Get a specific snapshot.
        
        Args:
            mission_type: Type of mission (e.g., 'airdrop_mission_snapshots')
            snapshot_id: ID of the snapshot (e.g., 'on_station_pre_drop')
        
        Returns:
            MissionSnapshot object or None if not found
        """
        return self.snapshots.get(mission_type, {}).get(snapshot_id)
    
    def list_snapshots(self, mission_type: str) -> List[str]:
        """
        List all available snapshots for a mission type.
        
        Args:
            mission_type: Type of mission
        
        Returns:
            List of snapshot IDs
        """
        return list(self.snapshots.get(mission_type, {}).keys())
    
    def list_mission_types(self) -> List[str]:
        """List all available mission types."""
        return list(self.snapshots.keys())
    
    def get_snapshot_summary(self, mission_type: str) -> str:
        """
        Get a formatted summary of all snapshots for a mission type.
        
        Args:
            mission_type: Type of mission
        
        Returns:
            Formatted string with snapshot information
        """
        if mission_type not in self.snapshots:
            return f"No snapshots found for mission type: {mission_type}"
        
        summary = f"**Available Snapshots for {mission_type}:**\n\n"
        
        for snapshot_id, snapshot in self.snapshots[mission_type].items():
            summary += f"**{snapshot_id}** - {snapshot.name}\n"
            summary += f"  {snapshot.description}\n"
            summary += f"  Phase: {snapshot.mission_phase}\n"
            if snapshot.time_into_mission:
                summary += f"  Time: {snapshot.time_into_mission}\n"
            summary += "\n"
        
        return summary

