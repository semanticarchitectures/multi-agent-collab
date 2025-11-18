#!/usr/bin/env python3
"""
Run HC-144 Surveillance Mission Interactive Session

This script:
1. Loads the HC-144 crew configuration
2. Presents the surveillance mission orders from configs/surveillance_mission.yaml
3. Allows you to interact with the crew to execute the mission
4. Supports starting from mission snapshots (e.g., --snapshot on_station_patrol)
"""

import asyncio
import os
import sys
from pathlib import Path
import yaml
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.base_agent import BaseAgent
from src.agents.squad_leader import SquadLeaderAgent
from src.agents.speaking_criteria import KeywordCriteria, CompositeCriteria, DirectAddressCriteria
from src.channel.shared_channel import SharedChannel
from src.orchestration.orchestrator import Orchestrator
from src.config import load_config
from src.mcp.mcp_manager import get_mcp_manager, initialize_all_aviation_mcps
from src.utils.mission_snapshots import MissionSnapshotManager

console = Console()


def load_mission_orders(mission_file: str) -> dict:
    """Load mission orders from YAML file."""
    with open(mission_file, 'r') as f:
        return yaml.safe_load(f)


def format_mission_brief(mission_data: dict) -> str:
    """Format mission data into a brief for the crew."""
    brief = f"""# MISSION BRIEF - {mission_data['mission_info']['mission_number']}

## MISSION INFORMATION
- **Type:** {mission_data['mission_info']['mission_type']}
- **Classification:** {mission_data['mission_info']['classification']}
- **Priority:** {mission_data['mission_info']['priority']}
- **Date:** {mission_data['mission_info']['date_issued']}

## AIRCRAFT
- **Type:** {mission_data['aircraft']['type']}
- **Tail Number:** {mission_data['aircraft']['tail_number']}
- **Configuration:** {mission_data['aircraft']['configuration']}

## CREW
- **Pilot in Command:** {mission_data['crew']['pilot_in_command']['name']} ({mission_data['crew']['pilot_in_command']['qualification']})
- **First Officer:** {mission_data['crew']['first_officer']['name']} ({mission_data['crew']['first_officer']['qualification']})
- **Flight Engineer:** {mission_data['crew']['flight_engineer']['name']} ({mission_data['crew']['flight_engineer']['qualification']})
"""
    
    for crew_member in mission_data['crew']['additional_crew']:
        brief += f"- **{crew_member['position']}:** {crew_member['name']}\n"
    
    brief += f"""
## FLIGHT PLAN
**Departure:** {mission_data['flight_plan']['departure']['airport']} RWY {mission_data['flight_plan']['departure']['runway']} at {mission_data['flight_plan']['departure']['departure_time']}

**Route:** {' → '.join(mission_data['flight_plan']['route']['waypoints'])}
- Altitude: {mission_data['flight_plan']['route']['altitude']}
- Airspeed: {mission_data['flight_plan']['route']['airspeed']}

**Mission Area:** {mission_data['flight_plan']['mission_area']['description']}
- Center: {mission_data['flight_plan']['mission_area']['center_point']}
- Radius: {mission_data['flight_plan']['mission_area']['radius']}
- Altitude Block: {mission_data['flight_plan']['mission_area']['altitude_block']}
- Loiter Time: {mission_data['flight_plan']['mission_area']['loiter_time']}
- Pattern: {mission_data['flight_plan']['mission_area']['pattern']}

**Destination:** {mission_data['flight_plan']['destination']['airport']} RWY {mission_data['flight_plan']['destination']['runway']} ETA {mission_data['flight_plan']['destination']['estimated_arrival']}

**Alternates:** 
- Primary: {mission_data['flight_plan']['alternates']['primary']}
- Secondary: {mission_data['flight_plan']['alternates']['secondary']}

## FUEL
- **Planned Load:** {mission_data['fuel']['planned_fuel_load']}
- **Burn Rate:** {mission_data['fuel']['fuel_burn_rate']}
- **Endurance:** {mission_data['fuel']['estimated_endurance']}
- **Bingo Fuel:** {mission_data['fuel']['bingo_fuel']}
- **Reserve:** {mission_data['fuel']['reserve_fuel']}

## WEATHER
**Departure:** {mission_data['weather']['departure_weather']['conditions']}, Winds {mission_data['weather']['departure_weather']['winds']}, Vis {mission_data['weather']['departure_weather']['visibility']}, Ceiling {mission_data['weather']['departure_weather']['ceiling']}

**Mission Area:** {mission_data['weather']['mission_area_weather']['conditions']}, Winds {mission_data['weather']['mission_area_weather']['winds']}, Vis {mission_data['weather']['mission_area_weather']['visibility']}, Sea State {mission_data['weather']['mission_area_weather']['sea_state']}

## MISSION OBJECTIVES
**Primary:** {mission_data['mission_objectives']['primary']}

**Secondary:**
"""
    for obj in mission_data['mission_objectives']['secondary']:
        brief += f"- {obj}\n"
    
    brief += "\n**Success Criteria:**\n"
    for criteria in mission_data['mission_objectives']['success_criteria']:
        brief += f"- {criteria}\n"
    
    brief += "\n## SPECIAL INSTRUCTIONS\n"
    for instruction in mission_data['special_instructions']:
        brief += f"- {instruction}\n"
    
    brief += f"""
## COMMUNICATIONS
- **Departure:** {mission_data['communications']['departure_frequency']}
- **En Route:** {', '.join(mission_data['communications']['en_route_frequencies'])}
- **Mission:** {mission_data['communications']['mission_frequency']}
- **Guard:** {mission_data['communications']['guard_frequency']}

## RISK ASSESSMENT
**Overall Risk Level:** {mission_data['risk_assessment']['overall_risk_level']}

**Identified Hazards:**
"""
    for hazard in mission_data['risk_assessment']['identified_hazards']:
        brief += f"- {hazard}\n"
    
    brief += "\n**Mitigation Measures:**\n"
    for measure in mission_data['risk_assessment']['mitigation_measures']:
        brief += f"- {measure}\n"
    
    brief += f"""
## APPROVALS
- **Operations Officer:** {mission_data['approvals']['operations_officer']}
- **Maintenance Officer:** {mission_data['approvals']['maintenance_officer']}
- **Commanding Officer:** {mission_data['approvals']['commanding_officer']}

---
**MISSION STATUS:** APPROVED - READY FOR EXECUTION
"""
    
    return brief


async def initialize_simulator_from_snapshot(snapshot):
    """Initialize the aircraft simulator with snapshot parameters."""
    manager = await get_mcp_manager()

    # Get the aircraft-sim-mcp client
    client = manager.get_client("aircraft-sim-mcp")
    if not client:
        console.print("[yellow]⚠ Aircraft simulator not connected - skipping initialization[/yellow]")
        return False

    # Call reset_simulation tool
    params = snapshot.to_simulator_init_params()

    console.print(f"\n[cyan]Initializing simulator from snapshot...[/cyan]")
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
        console.print(f"[yellow]⚠ Failed to initialize simulator: {e}[/yellow]")
        return False


async def main(snapshot_id=None):
    """Run the surveillance mission interactive session.

    Args:
        snapshot_id: Optional snapshot ID to start from (e.g., 'on_station_patrol')
    """

    console.print(Panel.fit(
        "[bold cyan]HC-144 Surveillance Mission[/bold cyan]\n"
        "Interactive Mission Execution Session",
        title="USCG Air Station Cape Cod"
    ))

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        console.print("[red]Error: ANTHROPIC_API_KEY environment variable not set[/red]")
        return

    # Load snapshot if specified
    snapshot = None
    if snapshot_id:
        try:
            snapshot_manager = MissionSnapshotManager()
            snapshot = snapshot_manager.get_snapshot("surveillance_mission_snapshots", snapshot_id)

            if not snapshot:
                console.print(f"[red]Error: Snapshot '{snapshot_id}' not found[/red]")
                console.print("\nAvailable snapshots:")
                for sid in snapshot_manager.list_snapshots("surveillance_mission_snapshots"):
                    s = snapshot_manager.get_snapshot("surveillance_mission_snapshots", sid)
                    console.print(f"  • [green]{sid}[/green]: {s.name}")
                return

            # Display snapshot information
            console.print(Panel(
                Markdown(snapshot.get_context_message()),
                title="[bold cyan]Starting from Mission Snapshot[/bold cyan]",
                border_style="cyan"
            ))
        except Exception as e:
            console.print(f"[red]Error loading snapshot: {e}[/red]")
            return

    try:
        # Initialize MCP servers for aviation tools
        console.print("\n[dim]Initializing MCP servers for aviation tools...[/dim]")

        # Determine paths to MCP servers (relative to parent directory)
        parent_dir = Path(__file__).parent.parent
        aerospace_path = str(parent_dir / "aerospace-mcp")
        aviation_weather_path = str(parent_dir / "aviation-weather-mcp")
        blevinstein_path = str(parent_dir / "aviation-mcp")
        aircraft_sim_path = str(parent_dir / "aircraft-sim-mcp")

        # Initialize all available MCP servers
        mcp_results = await initialize_all_aviation_mcps(
            aerospace_path=aerospace_path if Path(aerospace_path).exists() else None,
            aviation_weather_path=aviation_weather_path if Path(aviation_weather_path).exists() else None,
            blevinstein_aviation_path=blevinstein_path if Path(blevinstein_path).exists() else None,
            aircraft_sim_path=aircraft_sim_path if Path(aircraft_sim_path).exists() else None
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

        # Initialize simulator from snapshot if provided
        if snapshot:
            await initialize_simulator_from_snapshot(snapshot)

        # Load mission orders
        console.print("\n[dim]Loading mission orders from configs/surveillance_mission.yaml...[/dim]")
        mission_data = load_mission_orders("configs/surveillance_mission.yaml")

        # Load HC-144 crew configuration
        console.print("[dim]Loading HC-144 crew configuration...[/dim]\n")
        config = load_config("configs/HC-144.yaml")

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
        console.print(f"[green]Crew assembled: {orchestrator.get_agent_count()} personnel[/green]\n")
        for agent in orchestrator.get_active_agents():
            console.print(f"  • {agent.callsign} ({agent.get_agent_type()})")
        
        console.print("\n" + "="*80 + "\n")
        
        # Format and display mission brief
        mission_brief = format_mission_brief(mission_data)
        console.print(Markdown(mission_brief))
        
        console.print("\n" + "="*80 + "\n")
        
        # Present mission brief to the crew
        console.print("[bold yellow]Presenting mission brief to crew...[/bold yellow]\n")
        
        brief_message = f"""Mission Brief for {mission_data['mission_info']['mission_number']}:

This is a {mission_data['mission_info']['mission_type']} mission departing {mission_data['flight_plan']['departure']['airport']} at {mission_data['flight_plan']['departure']['departure_time']}.

Primary Objective: {mission_data['mission_objectives']['primary']}

Mission Area: {mission_data['flight_plan']['mission_area']['description']}
Location: {mission_data['flight_plan']['mission_area']['center_point']}, Radius {mission_data['flight_plan']['mission_area']['radius']}
Loiter Time: {mission_data['flight_plan']['mission_area']['loiter_time']}

Aircraft: {mission_data['aircraft']['type']} (Tail {mission_data['aircraft']['tail_number']})
Fuel: {mission_data['fuel']['planned_fuel_load']}, Endurance {mission_data['fuel']['estimated_endurance']}

Weather: Mission area {mission_data['weather']['mission_area_weather']['conditions']}, Winds {mission_data['weather']['mission_area_weather']['winds']}

Risk Level: {mission_data['risk_assessment']['overall_risk_level']}

Crew, acknowledge receipt of mission brief and provide your initial assessment."""
        
        turn_result = await orchestrator.run_turn(user_message=brief_message)

        # Display crew responses (only the new ones from this turn)
        for msg in turn_result["agent_responses"]:
            console.print(f"\n[green]{msg.format_for_display()}[/green]")
        
        console.print("\n" + "="*80 + "\n")
        console.print("[bold cyan]Mission Brief Complete - Interactive Session Active[/bold cyan]\n")
        console.print("[dim]You can now interact with the crew. Type 'quit' to exit.[/dim]\n")
        
        # Interactive loop
        while True:
            try:
                user_input = Prompt.ask("[bold blue]Commander[/bold blue]")
                
                if user_input.lower() in ["quit", "exit", "q"]:
                    break
                
                if not user_input.strip():
                    continue
                
                # Send message and get responses
                turn_result = await orchestrator.run_turn(user_message=user_input)

                # Display agent responses (only the new ones from this turn)
                for msg in turn_result["agent_responses"]:
                    console.print(f"\n[green]{msg.format_for_display()}[/green]\n")
            
            except KeyboardInterrupt:
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
        
        orchestrator.stop()
        console.print("\n[yellow]Mission session ended.[/yellow]")

        # Cleanup MCP connections
        if mcp_connected:
            console.print("[dim]Cleaning up MCP connections...[/dim]")
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
    parser = argparse.ArgumentParser(
        description="Run HC-144 Surveillance Mission",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start mission from beginning
  python run_surveillance_mission.py

  # Start mission already on station in patrol area
  python run_surveillance_mission.py --snapshot on_station_patrol

  # List available snapshots
  python run_surveillance_mission.py --list-snapshots
        """
    )
    parser.add_argument(
        "--snapshot",
        help="Start from a specific mission snapshot (e.g., on_station_patrol)"
    )
    parser.add_argument(
        "--list-snapshots",
        action="store_true",
        help="List available mission snapshots"
    )

    args = parser.parse_args()

    if args.list_snapshots:
        # List available snapshots
        try:
            snapshot_manager = MissionSnapshotManager()
            console.print("\n[bold cyan]Available Surveillance Mission Snapshots:[/bold cyan]\n")
            for snapshot_id in snapshot_manager.list_snapshots("surveillance_mission_snapshots"):
                snapshot = snapshot_manager.get_snapshot("surveillance_mission_snapshots", snapshot_id)
                console.print(f"[green]{snapshot_id}[/green]")
                console.print(f"  Name: {snapshot.name}")
                console.print(f"  Phase: {snapshot.mission_phase}")
                if snapshot.time_into_mission:
                    console.print(f"  Time: {snapshot.time_into_mission}")
                console.print(f"  Description: {snapshot.description}\n")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    else:
        asyncio.run(main(snapshot_id=args.snapshot))

