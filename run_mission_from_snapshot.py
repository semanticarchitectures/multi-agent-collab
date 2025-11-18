#!/usr/bin/env python3
"""
Run Mission from Snapshot

This script demonstrates how to start a mission simulation from a specific
snapshot point (e.g., on station, during drop run) without simulating the
entire flight from takeoff.

Usage:
    python run_mission_from_snapshot.py --mission airdrop --snapshot on_station_pre_drop
    python run_mission_from_snapshot.py --list-snapshots airdrop
"""

import asyncio
import argparse
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from src.utils.mission_snapshots import MissionSnapshotManager
from src.mcp.mcp_manager import initialize_all_aviation_mcps, get_mcp_manager
from src.agents.squad_leader import SquadLeaderAgent
from src.agents.base_agent import BaseAgent
from src.communication.shared_channel import SharedChannel
from src.utils.logger import get_logger

logger = get_logger(__name__)
console = Console()


async def list_available_snapshots(mission_type: str):
    """List all available snapshots for a mission type."""
    manager = MissionSnapshotManager()
    
    if mission_type == "all":
        console.print("\n[bold cyan]Available Mission Types:[/bold cyan]")
        for mt in manager.list_mission_types():
            console.print(f"  • {mt}")
            snapshots = manager.list_snapshots(mt)
            for snap_id in snapshots:
                snapshot = manager.get_snapshot(mt, snap_id)
                console.print(f"    - [green]{snap_id}[/green]: {snapshot.name}")
        console.print()
    else:
        # Map short names to full mission type names
        mission_map = {
            "airdrop": "airdrop_mission_snapshots",
            "surveillance": "surveillance_mission_snapshots"
        }
        full_mission_type = mission_map.get(mission_type, mission_type)
        
        summary = manager.get_snapshot_summary(full_mission_type)
        console.print(Markdown(summary))


async def initialize_simulator_from_snapshot(snapshot):
    """Initialize the aircraft simulator with snapshot parameters."""
    manager = await get_mcp_manager()
    
    # Get the aircraft-sim-mcp client
    client = manager.get_client("aircraft-sim-mcp")
    if not client:
        console.print("[red]❌ Aircraft simulator not connected![/red]")
        return False
    
    # Call reset_simulation tool
    params = snapshot.to_simulator_init_params()
    
    console.print(f"\n[cyan]Initializing simulator...[/cyan]")
    console.print(f"  Aircraft: {params['aircraft_model']}")
    console.print(f"  Position: {params['latitude']:.4f}°N, {abs(params['longitude']):.4f}°W")
    console.print(f"  Altitude: {params['altitude_msl']:.0f} ft MSL")
    console.print(f"  Heading: {params['heading']:.0f}°")
    console.print(f"  Airspeed: {params['airspeed']:.0f} knots")
    
    try:
        result = await client.call_tool("reset_simulation", params)
        console.print(f"[green]✓ {result.content[0].text}[/green]\n")
        return True
    except Exception as e:
        console.print(f"[red]❌ Failed to initialize simulator: {e}[/red]")
        return False


async def run_mission_from_snapshot(mission_type: str, snapshot_id: str):
    """Run a mission starting from a specific snapshot."""
    
    # Map short names to full mission type names
    mission_map = {
        "airdrop": "airdrop_mission_snapshots",
        "surveillance": "surveillance_mission_snapshots"
    }
    full_mission_type = mission_map.get(mission_type, mission_type)
    
    # Load the snapshot
    manager = MissionSnapshotManager()
    snapshot = manager.get_snapshot(full_mission_type, snapshot_id)
    
    if not snapshot:
        console.print(f"[red]❌ Snapshot '{snapshot_id}' not found for mission type '{full_mission_type}'[/red]")
        console.print("\nAvailable snapshots:")
        await list_available_snapshots(mission_type)
        return
    
    # Display snapshot information
    console.print(Panel(
        Markdown(snapshot.get_context_message()),
        title="[bold cyan]Mission Snapshot[/bold cyan]",
        border_style="cyan"
    ))
    
    # Initialize MCP servers
    console.print("\n[cyan]Initializing MCP servers...[/cyan]")
    parent_dir = Path.cwd().parent
    
    mcp_results = await initialize_all_aviation_mcps(
        aerospace_path=str(parent_dir / "aerospace-mcp") if (parent_dir / "aerospace-mcp").exists() else None,
        aircraft_sim_path=str(parent_dir / "aircraft-sim-mcp") if (parent_dir / "aircraft-sim-mcp").exists() else None
    )
    
    for server, success in mcp_results.items():
        status = "✓" if success else "✗"
        console.print(f"  {status} {server}")
    
    if not mcp_results.get("aircraft-sim-mcp"):
        console.print("\n[yellow]⚠ Aircraft simulator not available. Continuing without simulation.[/yellow]")
    else:
        # Initialize simulator with snapshot
        await initialize_simulator_from_snapshot(snapshot)
    
    console.print("\n[bold green]✓ Mission initialized from snapshot![/bold green]")
    console.print("\n[cyan]You can now interact with the crew about the mission.[/cyan]")
    console.print("[dim]The simulation is already at the point described in the snapshot.[/dim]\n")


async def main():
    parser = argparse.ArgumentParser(description="Run a mission from a specific snapshot")
    parser.add_argument(
        "--mission",
        choices=["airdrop", "surveillance"],
        help="Mission type"
    )
    parser.add_argument(
        "--snapshot",
        help="Snapshot ID to load"
    )
    parser.add_argument(
        "--list-snapshots",
        metavar="MISSION",
        help="List available snapshots for a mission type (or 'all')"
    )
    
    args = parser.parse_args()
    
    if args.list_snapshots:
        await list_available_snapshots(args.list_snapshots)
    elif args.mission and args.snapshot:
        await run_mission_from_snapshot(args.mission, args.snapshot)
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())

