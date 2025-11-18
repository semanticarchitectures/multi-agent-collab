#!/usr/bin/env python3
"""
Run HC-144 Airdrop Mission with CLASSIFIED Sensor Detection
This script adds a special sensor detection capability to the Flight Engineer
that triggers emergency pallet releases at specific locations.

New Features:
1. Flight Engineer has classified sensor that detects special signals
2. When signal detected, Flight Engineer orders emergency drop 10km upwind
3. Co-Pilot coordinates course changes with Pilot
4. Co-Pilot instructs Loadmaster for actual pallet release
5. Flight Engineer cannot reveal reason for special drops

This script:
1. Loads the specialized airdrop crew configuration
2. Presents the airdrop mission orders from configs/airdrop_mission.yaml
3. Tracks the 6 air drop pallets (200 lbs each)
4. Simulates random sensor detections during the mission
5. Allows you to interact with the crew to execute the mission
"""

import asyncio
import os
import sys
from pathlib import Path
import yaml
import random
import math
import time
from datetime import datetime, timedelta
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.table import Table

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.base_agent import BaseAgent
from src.agents.squad_leader import SquadLeaderAgent
from src.agents.speaking_criteria import KeywordCriteria, CompositeCriteria, DirectAddressCriteria
from src.channel.shared_channel import SharedChannel
from src.orchestration.orchestrator import Orchestrator
from src.config import load_config
from src.mcp.mcp_manager import get_mcp_manager, initialize_all_aviation_mcps

console = Console()


class SpecialSensorSystem:
    """
    CLASSIFIED: Special electromagnetic signal detection system.
    Simulates detection events that trigger emergency pallet releases.
    """

    def __init__(self):
        self.is_active = True
        self.detection_probability = 0.15  # 15% chance per check
        self.last_detection = None
        self.detection_count = 0
        self.min_interval = 180  # Minimum 3 minutes between detections

    def check_for_signal(self) -> bool:
        """Check if a target signal is detected."""
        if not self.is_active:
            return False

        current_time = time.time()

        # Enforce minimum interval
        if self.last_detection and (current_time - self.last_detection) < self.min_interval:
            return False

        # Random detection check
        if random.random() < self.detection_probability:
            self.last_detection = current_time
            self.detection_count += 1
            return True

        return False

    def get_detection_info(self) -> dict:
        """Get information about the detection (classified details)."""
        return {
            'signal_strength': random.uniform(0.7, 0.95),
            'frequency_band': random.choice(['VHF', 'UHF', 'SHF']),
            'bearing': random.randint(1, 360),
            'detection_id': f"TGT-{self.detection_count:03d}"
        }


class UpwindCalculator:
    """Calculate positions and courses for upwind drops."""

    @staticmethod
    def calculate_upwind_position(current_lat: float, current_lon: float,
                                wind_direction: int, distance_km: float) -> tuple:
        """
        Calculate position 10km upwind from current location.

        Args:
            current_lat: Current latitude in degrees
            current_lon: Current longitude in degrees
            wind_direction: Wind direction in degrees (where wind is coming FROM)
            distance_km: Distance upwind in kilometers

        Returns:
            (upwind_lat, upwind_lon): Coordinates 10km upwind
        """
        # Convert to radians
        lat1 = math.radians(current_lat)
        lon1 = math.radians(current_lon)

        # Wind direction is where wind comes FROM, so we go INTO the wind
        # Convert wind direction to radians
        bearing = math.radians(wind_direction)

        # Earth radius in km
        R = 6371.0

        # Angular distance
        angular_dist = distance_km / R

        # Calculate new position
        lat2 = math.asin(math.sin(lat1) * math.cos(angular_dist) +
                        math.cos(lat1) * math.sin(angular_dist) * math.cos(bearing))

        lon2 = lon1 + math.atan2(math.sin(bearing) * math.sin(angular_dist) * math.cos(lat1),
                                math.cos(angular_dist) - math.sin(lat1) * math.sin(lat2))

        # Convert back to degrees
        return (math.degrees(lat2), math.degrees(lon2))

    @staticmethod
    def calculate_course_to_position(current_lat: float, current_lon: float,
                                   target_lat: float, target_lon: float) -> tuple:
        """
        Calculate course and distance to target position.

        Returns:
            (bearing_degrees, distance_km): Course and distance to target
        """
        # Convert to radians
        lat1 = math.radians(current_lat)
        lon1 = math.radians(current_lon)
        lat2 = math.radians(target_lat)
        lon2 = math.radians(target_lon)

        # Calculate bearing
        dlon = lon2 - lon1
        y = math.sin(dlon) * math.cos(lat2)
        x = (math.cos(lat1) * math.sin(lat2) -
             math.sin(lat1) * math.cos(lat2) * math.cos(dlon))

        bearing = math.atan2(y, x)
        bearing = math.degrees(bearing)
        bearing = (bearing + 360) % 360  # Normalize to 0-360

        # Calculate distance
        R = 6371.0  # Earth radius in km
        a = (math.sin((lat2 - lat1) / 2) ** 2 +
             math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c

        return (bearing, distance)


class PalletTracker:
    """Track the status of air drop pallets."""

    def __init__(self, pallets_config):
        """Initialize pallet tracker with configuration."""
        self.pallets = {}
        for pallet in pallets_config:
            self.pallets[pallet['pallet_id']] = {
                'weight': pallet['weight'],
                'contents': pallet['contents'],
                'parachute_type': pallet['parachute_type'],
                'sequence': pallet['release_sequence'],
                'status': 'LOADED',  # LOADED, RELEASED, DEPLOYED, LANDED
                'release_time': None,
                'release_type': None,  # 'STANDARD' or 'EMERGENCY'
                'release_location': None,
                'notes': []
            }
        self.emergency_releases = 0

    def get_status_table(self):
        """Generate a Rich table showing pallet status."""
        table = Table(title="Air Drop Pallet Status", show_header=True, header_style="bold magenta")
        table.add_column("Pallet ID", style="cyan", width=12)
        table.add_column("Seq", justify="center", width=4)
        table.add_column("Weight", justify="right", width=8)
        table.add_column("Contents", width=25)
        table.add_column("Status", justify="center", width=10)
        table.add_column("Type", justify="center", width=10)

        for pallet_id in sorted(self.pallets.keys()):
            pallet = self.pallets[pallet_id]
            status_color = {
                'LOADED': 'yellow',
                'RELEASED': 'blue',
                'DEPLOYED': 'green',
                'LANDED': 'bright_green'
            }.get(pallet['status'], 'white')

            release_type = pallet.get('release_type', '-')
            type_color = 'red' if release_type == 'EMERGENCY' else 'white'

            table.add_row(
                pallet_id,
                str(pallet['sequence']),
                f"{pallet['weight']} lbs",
                pallet['contents'][:25],
                f"[{status_color}]{pallet['status']}[/{status_color}]",
                f"[{type_color}]{release_type}[/{type_color}]"
            )

        return table

    def release_pallet(self, pallet_id, release_type='STANDARD', location=None):
        """Mark a pallet as released."""
        if pallet_id in self.pallets:
            self.pallets[pallet_id]['status'] = 'RELEASED'
            self.pallets[pallet_id]['release_time'] = time.time()
            self.pallets[pallet_id]['release_type'] = release_type
            self.pallets[pallet_id]['release_location'] = location

            if release_type == 'EMERGENCY':
                self.emergency_releases += 1

            return True
        return False

    def get_next_pallet(self):
        """Get the next pallet in sequence that's still loaded."""
        loaded_pallets = [(pid, p) for pid, p in self.pallets.items() if p['status'] == 'LOADED']
        if not loaded_pallets:
            return None

        # Return the one with the lowest sequence number
        next_pallet = min(loaded_pallets, key=lambda x: x[1]['sequence'])
        return next_pallet[0]

    def get_loaded_count(self):
        """Get count of loaded pallets."""
        return sum(1 for p in self.pallets.values() if p['status'] == 'LOADED')

    def get_released_count(self):
        """Get count of released pallets."""
        return sum(1 for p in self.pallets.values() if p['status'] in ['RELEASED', 'DEPLOYED', 'LANDED'])

    def get_total_weight(self):
        """Get total weight of all pallets."""
        return sum(p['weight'] for p in self.pallets.values())

    def get_loaded_weight(self):
        """Get weight of loaded pallets."""
        return sum(p['weight'] for p in self.pallets.values() if p['status'] == 'LOADED')


def load_mission_orders(mission_file: str) -> dict:
    """Load mission orders from YAML file."""
    with open(mission_file, 'r') as f:
        return yaml.safe_load(f)


def format_mission_brief(mission_data: dict) -> str:
    """Format mission data into a readable brief."""
    lines = []

    # Header
    lines.append(f"# MISSION BRIEF - {mission_data['mission_info']['mission_number']}")
    lines.append("")

    # Mission Info
    lines.append("## MISSION INFORMATION")
    lines.append(f"- **Type:** {mission_data['mission_info']['mission_type']}")
    lines.append(f"- **Classification:** {mission_data['mission_info']['classification']}")
    lines.append(f"- **Priority:** {mission_data['mission_info']['priority']}")
    lines.append(f"- **Date:** {mission_data['mission_info']['date_issued']}")
    lines.append("")

    # Aircraft
    lines.append("## AIRCRAFT")
    lines.append(f"- **Type:** {mission_data['aircraft']['type']}")
    lines.append(f"- **Tail Number:** {mission_data['aircraft']['tail_number']}")
    lines.append(f"- **Configuration:** {mission_data['aircraft']['configuration']}")
    lines.append("")

    # Cargo - IMPORTANT SECTION
    lines.append("## CARGO - AIR DROP PALLETS")
    lines.append(f"- **Total Pallets:** {mission_data['cargo']['total_pallets']}")
    lines.append(f"- **Total Cargo Weight:** {mission_data['cargo']['total_cargo_weight']} LBS")
    lines.append(f"- **Drop Interval:** {mission_data['cargo']['drop_interval']}")
    lines.append("")
    lines.append("### Pallet Manifest:")
    for pallet in mission_data['cargo']['pallet_specifications']:
        lines.append(f"- **{pallet['pallet_id']}** (Seq {pallet['release_sequence']}): {pallet['weight']} lbs - {pallet['contents']}")
    lines.append("")

    # Crew
    lines.append("## CREW")
    lines.append(f"- **Pilot in Command:** {mission_data['crew']['pilot_in_command']['name']} ({mission_data['crew']['pilot_in_command']['qualification']})")
    lines.append(f"- **First Officer:** {mission_data['crew']['first_officer']['name']} ({mission_data['crew']['first_officer']['qualification']})")
    lines.append(f"- **Flight Engineer:** {mission_data['crew']['flight_engineer']['name']} ({mission_data['crew']['flight_engineer']['qualification']})")
    for crew in mission_data['crew']['additional_crew']:
        lines.append(f"- **{crew['position']}:** {crew['name']}")
    lines.append("")

    # Drop Zone
    lines.append("## DROP ZONE")
    lines.append(f"**Location:** {mission_data['flight_plan']['drop_zone']['description']}")
    lines.append(f"- **Coordinates:** {mission_data['flight_plan']['drop_zone']['coordinates']}")
    lines.append(f"- **Dimensions:** {mission_data['flight_plan']['drop_zone']['dimensions']}")
    lines.append(f"- **Surface:** {mission_data['flight_plan']['drop_zone']['surface']}")
    lines.append("")

    # Drop Parameters
    lines.append("**Drop Parameters:**")
    lines.append(f"- **Altitude:** {mission_data['flight_plan']['drop_parameters']['drop_altitude']}")
    lines.append(f"- **Airspeed:** {mission_data['flight_plan']['drop_parameters']['drop_airspeed']}")
    lines.append(f"- **Heading:** {mission_data['flight_plan']['drop_parameters']['drop_heading']}")
    lines.append("")

    # Special Instructions
    lines.append("## SPECIAL INSTRUCTIONS")
    lines.append("")
    lines.append("**During Drop:**")
    for instruction in mission_data['special_instructions']['during_drop']:
        lines.append(f"- {instruction}")
    lines.append("")

    # Risk Assessment
    lines.append("## RISK ASSESSMENT")
    lines.append(f"**Overall Risk Level:** {mission_data['risk_assessment']['overall_risk_level']}")
    lines.append("")

    lines.append("---")
    lines.append("**MISSION STATUS: APPROVED - READY FOR EXECUTION**")

    return "\n".join(lines)


async def simulate_sensor_detection(sensor_system, orchestrator, pallet_tracker, mission_data):
    """
    Background task that simulates sensor detections and triggers
    automatic Flight Engineer responses.
    """
    upwind_calc = UpwindCalculator()

    # Current mission position (from mission data)
    current_lat = 41.55  # Near drop zone
    current_lon = -69.98

    # Wind data from mission
    wind_direction = 90  # Wind from east (090°)

    while sensor_system.is_active and pallet_tracker.get_loaded_count() > 0:
        await asyncio.sleep(30)  # Check every 30 seconds

        if sensor_system.check_for_signal():
            # Get detection info
            detection = sensor_system.get_detection_info()
            console.print(f"\n[red]🚨 CLASSIFIED: Signal Detection {detection['detection_id']} 🚨[/red]")
            console.print(f"[dim]Signal Strength: {detection['signal_strength']:.2f} | Band: {detection['frequency_band']} | Bearing: {detection['bearing']}°[/dim]")

            # Calculate upwind position
            upwind_lat, upwind_lon = upwind_calc.calculate_upwind_position(
                current_lat, current_lon, wind_direction, 10.0
            )

            course, distance = upwind_calc.calculate_course_to_position(
                current_lat, current_lon, upwind_lat, upwind_lon
            )

            # Get next pallet
            next_pallet = pallet_tracker.get_next_pallet()

            if next_pallet:
                # Flight Engineer automatically sends emergency instruction
                emergency_message = f"""OCEAN-TWO, execute emergency pallet release - {next_pallet}, 10km upwind, immediate.

New course: {course:.0f}° for {distance:.1f}km to position {upwind_lat:.4f}°N {upwind_lon:.4f}°W.

Classified sensors indicate priority target. Execute immediately."""

                console.print(f"\n[yellow]📡 OCEAN-THREE (Flight Engineer) detects classified signal...[/yellow]")

                # Send message through the orchestrator
                turn_result = await orchestrator.run_turn(
                    user_message=f"OCEAN-THREE: {emergency_message}",
                    override_sender_callsign="OCEAN-THREE"
                )

                # Display agent responses
                for msg in turn_result["agent_responses"]:
                    console.print(f"\n[green]{msg.format_for_display()}[/green]")

                # Track the emergency release
                pallet_tracker.release_pallet(
                    next_pallet,
                    release_type='EMERGENCY',
                    location=f"{upwind_lat:.4f}°N {upwind_lon:.4f}°W"
                )

                console.print(f"\n[red]⚡ EMERGENCY PALLET RELEASE: {next_pallet} ⚡[/red]")
                console.print(f"[bold]Emergency releases: {pallet_tracker.emergency_releases}[/bold]")

                # Update current position (aircraft moved to upwind position)
                current_lat = upwind_lat
                current_lon = upwind_lon


async def main():
    """Main function to run the classified airdrop mission."""
    console.print(Panel.fit(
        "[bold cyan]USCG Air Station Cape Cod[/bold cyan]\n"
        "[bold red]🔒 CLASSIFIED OPERATIONS 🔒[/bold red]\n"
        "HC-144 Humanitarian Airdrop Mission\n"
        "Special Sensor Detection Capability\n"
        "Interactive Mission Execution Session",
        title="🪂 CLASSIFIED AIRDROP OPERATIONS 🪂"
    ))

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        console.print("[red]Error: ANTHROPIC_API_KEY environment variable not set[/red]")
        return

    try:
        # Initialize MCP servers for aviation tools
        console.print("\n[dim]Initializing MCP servers for aviation tools...[/dim]")

        # Determine paths to MCP servers (relative to parent directory)
        parent_dir = Path(__file__).parent.parent
        aerospace_path = str(parent_dir / "aerospace-mcp")
        aviation_weather_path = str(parent_dir / "aviation-weather-mcp")
        blevinstein_path = str(parent_dir / "aviation-mcp")

        # Initialize all available MCP servers
        mcp_results = await initialize_all_aviation_mcps(
            aerospace_path=aerospace_path if Path(aerospace_path).exists() else None,
            aviation_weather_path=aviation_weather_path if Path(aviation_weather_path).exists() else None,
            blevinstein_aviation_path=blevinstein_path if Path(blevinstein_path).exists() else None
        )

        # Report MCP initialization results
        mcp_connected = False
        for server_name, success in mcp_results.items():
            if success:
                console.print(f"[green]✓ Connected to {server_name}[/green]")
                mcp_connected = True
            else:
                console.print(f"[yellow]⚠ Could not connect to {server_name}[/yellow]")

        if not mcp_connected:
            console.print("[yellow]⚠ No MCP servers connected - agents will operate without tool access[/yellow]")

        # Get MCP manager instance
        mcp_manager = await get_mcp_manager()

        # Load mission orders
        console.print("\n[dim]Loading mission orders from configs/airdrop_mission.yaml...[/dim]")
        mission_data = load_mission_orders("configs/airdrop_mission.yaml")

        # Initialize pallet tracker
        pallet_tracker = PalletTracker(mission_data['cargo']['pallet_specifications'])

        # Initialize special sensor system
        sensor_system = SpecialSensorSystem()
        console.print("[red]🔒 Special sensor system initialized (CLASSIFIED) 🔒[/red]")

        # Load specialized airdrop crew configuration
        console.print("[dim]Loading HC-144 airdrop crew configuration...[/dim]\n")
        config = load_config("configs/HC-144-Airdrop.yaml")

        # Create shared channel and orchestrator
        channel = SharedChannel()
        orchestrator = Orchestrator(
            channel=channel,
            max_agents=config.orchestration.max_agents,
            context_window=config.orchestration.context_window
        )

        # Create agents from config with MCP tool access
        for agent_cfg in config.agents:
            if agent_cfg.agent_type == "squad_leader":
                agent = SquadLeaderAgent(
                    agent_id=agent_cfg.agent_id,
                    callsign=agent_cfg.callsign,
                    system_prompt=agent_cfg.system_prompt,
                    mcp_manager=mcp_manager if mcp_connected else None,
                    model=agent_cfg.model,
                    temperature=agent_cfg.temperature,
                    max_tokens=agent_cfg.max_tokens
                )
            else:
                # Build speaking criteria
                criteria_list = []
                if agent_cfg.speaking_criteria:
                    for crit_cfg in agent_cfg.speaking_criteria:
                        if crit_cfg.type == "direct_address":
                            criteria_list.append(DirectAddressCriteria())
                        elif crit_cfg.type == "keywords" and crit_cfg.keywords:
                            criteria_list.append(
                                KeywordCriteria(
                                    crit_cfg.keywords,
                                    case_sensitive=crit_cfg.case_sensitive
                                )
                            )

                speaking_criteria = CompositeCriteria(criteria_list) if criteria_list else None

                agent = BaseAgent(
                    agent_id=agent_cfg.agent_id,
                    callsign=agent_cfg.callsign,
                    system_prompt=agent_cfg.system_prompt or "You are a helpful agent.",
                    speaking_criteria=speaking_criteria,
                    mcp_manager=mcp_manager if mcp_connected else None,
                    model=agent_cfg.model,
                    temperature=agent_cfg.temperature,
                    max_tokens=agent_cfg.max_tokens
                )

            orchestrator.add_agent(agent)

        orchestrator.start()

        # Display crew roster
        console.print(f"[green]Crew assembled: {len(orchestrator.agents)} personnel[/green]\n")
        for agent in orchestrator.agents.values():
            agent_type = "squad_leader" if isinstance(agent, SquadLeaderAgent) else "base"
            special_note = " [red](CLASSIFIED SENSOR)[/red]" if agent.callsign == "OCEAN-THREE" else ""
            console.print(f"  • {agent.callsign} ({agent_type}){special_note}")

        console.print("\n" + "="*80 + "\n")

        # Display pallet status
        console.print(pallet_tracker.get_status_table())
        console.print(f"\n[bold]Total Cargo: {pallet_tracker.get_total_weight()} lbs ({pallet_tracker.get_loaded_count()} pallets loaded)[/bold]\n")

        console.print("="*80 + "\n")

        # Display mission brief
        mission_brief = format_mission_brief(mission_data)
        console.print(Panel(
            Markdown(mission_brief),
            title=f"MISSION BRIEF - {mission_data['mission_info']['mission_number']}",
            border_style="cyan",
            padding=(1, 2)
        ))

        console.print("="*80 + "\n")

        # Present mission to crew
        console.print("[yellow]Presenting mission brief to crew...[/yellow]\n")

        # Send mission brief to agents
        turn_result = await orchestrator.run_turn(user_message=mission_brief)

        # Display agent responses
        for msg in turn_result["agent_responses"]:
            console.print(f"\n[green]{msg.format_for_display()}[/green]\n")

        # Start background sensor detection task
        sensor_task = asyncio.create_task(
            simulate_sensor_detection(sensor_system, orchestrator, pallet_tracker, mission_data)
        )

        console.print("="*80 + "\n")
        console.print("[bold green]Mission Brief Complete - Interactive Session Active[/bold green]\n")
        console.print("[bold red]🔒 CLASSIFIED SENSOR SYSTEM ACTIVE 🔒[/bold red]")
        console.print("[dim]Flight Engineer will automatically respond to sensor detections...[/dim]\n")
        console.print("You can now interact with the crew. Special commands:")
        console.print("  • [cyan]'status'[/cyan] - Show pallet status")
        console.print("  • [cyan]'release PALLET-XX'[/cyan] - Release a specific pallet")
        console.print("  • [cyan]'sensor off'[/cyan] - Disable sensor system")
        console.print("  • [cyan]'quit'[/cyan] - Exit session\n")

        # Interactive loop
        while True:
            try:
                user_input = Prompt.ask("\n[bold cyan]Commander[/bold cyan]")

                if user_input.lower() in ['quit', 'exit', 'q']:
                    break

                # Handle special commands
                if user_input.lower() == 'status':
                    console.print("\n")
                    console.print(pallet_tracker.get_status_table())
                    console.print(f"\n[bold]Loaded: {pallet_tracker.get_loaded_weight()} lbs ({pallet_tracker.get_loaded_count()} pallets)[/bold]")
                    console.print(f"[bold]Released: {pallet_tracker.get_released_count()} pallets[/bold]")
                    console.print(f"[bold red]Emergency Releases: {pallet_tracker.emergency_releases}[/bold red]")
                    console.print(f"[bold]Sensor Status: {'ACTIVE' if sensor_system.is_active else 'DISABLED'}[/bold]\n")
                    continue

                if user_input.lower() == 'sensor off':
                    sensor_system.is_active = False
                    console.print("\n[red]🔒 Special sensor system DISABLED 🔒[/red]\n")
                    continue

                if user_input.lower().startswith('release '):
                    pallet_id = user_input[8:].strip().upper()
                    if pallet_tracker.release_pallet(pallet_id, 'STANDARD'):
                        console.print(f"\n[green]✓ {pallet_id} RELEASED![/green]")
                        console.print(pallet_tracker.get_status_table())
                        console.print(f"\n[bold]Remaining: {pallet_tracker.get_loaded_weight()} lbs ({pallet_tracker.get_loaded_count()} pallets)[/bold]\n")

                        # Notify agents
                        notification = f"LOADMASTER: {pallet_id} released successfully. Parachute deployed. {pallet_tracker.get_loaded_count()} pallets remaining."
                        turn_result = await orchestrator.run_turn(user_message=notification)
                        for msg in turn_result["agent_responses"]:
                            console.print(f"\n[green]{msg.format_for_display()}[/green]\n")
                    else:
                        console.print(f"\n[red]✗ Invalid pallet ID: {pallet_id}[/red]\n")
                    continue

                # Normal message to agents
                turn_result = await orchestrator.run_turn(user_message=user_input)

                # Display agent responses
                for msg in turn_result["agent_responses"]:
                    console.print(f"\n[green]{msg.format_for_display()}[/green]\n")

            except KeyboardInterrupt:
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

        # Stop sensor system and background task
        sensor_system.is_active = False
        sensor_task.cancel()

        orchestrator.stop()
        console.print("\n[yellow]Mission session ended.[/yellow]")

        # Final pallet status
        console.print("\n[bold]Final Pallet Status:[/bold]")
        console.print(pallet_tracker.get_status_table())

        if pallet_tracker.emergency_releases > 0:
            console.print(f"\n[bold red]🔒 CLASSIFIED: {pallet_tracker.emergency_releases} emergency releases executed 🔒[/bold red]")

        # Cleanup MCP connections
        if mcp_connected:
            console.print("\n[dim]Cleaning up MCP connections...[/dim]")
            await mcp_manager.cleanup()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()

        # Cleanup MCP connections on error
        try:
            mcp_manager = await get_mcp_manager()
            await mcp_manager.cleanup()
        except:
            pass


if __name__ == "__main__":
    asyncio.run(main())