#!/usr/bin/env python3
"""
Run HC-144 Airdrop Mission Interactive Session

This script:
1. Loads the HC-144 crew configuration
2. Presents the airdrop mission orders from configs/airdrop_mission.yaml
3. Tracks the 6 air drop pallets (200 lbs each)
4. Allows you to interact with the crew to execute the mission
"""

import asyncio
import os
import sys
from pathlib import Path
import yaml
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
                'notes': []
            }
    
    def get_status_table(self):
        """Generate a Rich table showing pallet status."""
        table = Table(title="Air Drop Pallet Status", show_header=True, header_style="bold magenta")
        table.add_column("Pallet ID", style="cyan", width=12)
        table.add_column("Seq", justify="center", width=4)
        table.add_column("Weight", justify="right", width=8)
        table.add_column("Contents", width=30)
        table.add_column("Status", justify="center", width=10)
        
        for pallet_id in sorted(self.pallets.keys()):
            pallet = self.pallets[pallet_id]
            status_color = {
                'LOADED': 'yellow',
                'RELEASED': 'blue',
                'DEPLOYED': 'green',
                'LANDED': 'bright_green'
            }.get(pallet['status'], 'white')
            
            table.add_row(
                pallet_id,
                str(pallet['sequence']),
                f"{pallet['weight']} lbs",
                pallet['contents'][:30],
                f"[{status_color}]{pallet['status']}[/{status_color}]"
            )
        
        return table
    
    def release_pallet(self, pallet_id):
        """Mark a pallet as released."""
        if pallet_id in self.pallets:
            self.pallets[pallet_id]['status'] = 'RELEASED'
            self.pallets[pallet_id]['release_time'] = asyncio.get_event_loop().time()
            return True
        return False
    
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
    
    # Flight Plan
    lines.append("## FLIGHT PLAN")
    lines.append(f"**Departure:** {mission_data['flight_plan']['departure']['airport']} RWY {mission_data['flight_plan']['departure']['runway']} at {mission_data['flight_plan']['departure']['departure_time']}")
    lines.append("")
    lines.append(f"**Route:** {' → '.join(mission_data['flight_plan']['route']['waypoints'])}")
    lines.append(f"- **Altitude:** {mission_data['flight_plan']['route']['altitude']}")
    lines.append(f"- **Airspeed:** {mission_data['flight_plan']['route']['airspeed']}")
    lines.append("")
    
    # Drop Zone
    lines.append("**Drop Zone:** {0}".format(mission_data['flight_plan']['drop_zone']['description']))
    lines.append(f"- **Coordinates:** {mission_data['flight_plan']['drop_zone']['coordinates']}")
    lines.append(f"- **Dimensions:** {mission_data['flight_plan']['drop_zone']['dimensions']}")
    lines.append(f"- **Surface:** {mission_data['flight_plan']['drop_zone']['surface']}")
    lines.append("")
    
    # Drop Parameters
    lines.append("**Drop Parameters:**")
    lines.append(f"- **Altitude:** {mission_data['flight_plan']['drop_parameters']['drop_altitude']}")
    lines.append(f"- **Airspeed:** {mission_data['flight_plan']['drop_parameters']['drop_airspeed']}")
    lines.append(f"- **Heading:** {mission_data['flight_plan']['drop_parameters']['drop_heading']}")
    lines.append(f"- **Release Interval:** {mission_data['flight_plan']['drop_parameters']['release_interval']}")
    lines.append("")
    
    lines.append(f"**Destination:** {mission_data['flight_plan']['destination']['airport']} RWY {mission_data['flight_plan']['destination']['runway']} ETA {mission_data['flight_plan']['destination']['estimated_arrival']}")
    lines.append("")
    lines.append(f"**Alternates:**")
    lines.append(f"- Primary: {mission_data['flight_plan']['alternates']['primary']}")
    lines.append(f"- Secondary: {mission_data['flight_plan']['alternates']['secondary']}")
    lines.append("")
    
    # Fuel
    lines.append("## FUEL")
    lines.append(f"- **Planned Load:** {mission_data['fuel']['planned_fuel_load']}")
    lines.append(f"- **Burn Rate:** {mission_data['fuel']['fuel_burn_rate']}")
    lines.append(f"- **Endurance:** {mission_data['fuel']['estimated_endurance']}")
    lines.append(f"- **Bingo Fuel:** {mission_data['fuel']['bingo_fuel']}")
    lines.append(f"- **Reserve:** {mission_data['fuel']['reserve_fuel']}")
    lines.append("")
    
    # Weather
    lines.append("## WEATHER")
    lines.append(f"**Drop Zone:** {mission_data['weather']['drop_zone_weather']['conditions']}, Winds {mission_data['weather']['drop_zone_weather']['winds']}, Vis {mission_data['weather']['drop_zone_weather']['visibility']}")
    lines.append("")
    
    # Mission Objectives
    lines.append("## MISSION OBJECTIVES")
    lines.append(f"**Primary:** {mission_data['mission_objectives']['primary']}")
    lines.append("")
    lines.append("**Secondary:**")
    for obj in mission_data['mission_objectives']['secondary']:
        lines.append(f"- {obj}")
    lines.append("")
    lines.append("**Success Criteria:**")
    for criteria in mission_data['mission_objectives']['success_criteria']:
        lines.append(f"- {criteria}")
    lines.append("")
    
    # Special Instructions
    lines.append("## SPECIAL INSTRUCTIONS")
    lines.append("")
    lines.append("**During Drop:**")
    for instruction in mission_data['special_instructions']['during_drop']:
        lines.append(f"- {instruction}")
    lines.append("")
    
    # Communications
    lines.append("## COMMUNICATIONS")
    lines.append(f"- **Departure:** {mission_data['communications']['departure_frequency']}")
    lines.append(f"- **Drop Zone:** {mission_data['communications']['drop_zone_frequency']}")
    lines.append(f"- **Ground Team:** {mission_data['communications']['ground_team_frequency']}")
    lines.append(f"- **Guard:** {mission_data['communications']['guard_frequency']}")
    lines.append("")
    
    # Risk Assessment
    lines.append("## RISK ASSESSMENT")
    lines.append(f"**Overall Risk Level:** {mission_data['risk_assessment']['overall_risk_level']}")
    lines.append("")
    lines.append("**Identified Hazards:**")
    for hazard in mission_data['risk_assessment']['identified_hazards']:
        lines.append(f"- {hazard}")
    lines.append("")
    lines.append("**Mitigation Measures:**")
    for measure in mission_data['risk_assessment']['mitigation_measures']:
        lines.append(f"- {measure}")
    lines.append("")
    
    # Approvals
    lines.append("## APPROVALS")
    lines.append(f"- **Operations Officer:** {mission_data['approvals']['operations_officer']}")
    lines.append(f"- **Maintenance Officer:** {mission_data['approvals']['maintenance_officer']}")
    lines.append(f"- **Commanding Officer:** {mission_data['approvals']['commanding_officer']}")
    lines.append("")
    lines.append("---")
    lines.append("**MISSION STATUS: APPROVED - READY FOR EXECUTION**")
    
    return "\n".join(lines)


async def main():
    """Main function to run the airdrop mission."""
    console.print(Panel.fit(
        "[bold cyan]USCG Air Station Cape Cod[/bold cyan]\n"
        "HC-144 Humanitarian Airdrop Mission\n"
        "Interactive Mission Execution Session",
        title="🪂 AIRDROP OPERATIONS 🪂"
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
        console.print(f"[green]Crew assembled: {len(orchestrator.agents)} personnel[/green]\n")
        for agent in orchestrator.agents.values():
            agent_type = "squad_leader" if isinstance(agent, SquadLeaderAgent) else "base"
            console.print(f"  • {agent.callsign} ({agent_type})")

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

        # Display agent responses (only the new ones from this turn)
        for msg in turn_result["agent_responses"]:
            console.print(f"\n[green]{msg.format_for_display()}[/green]\n")

        console.print("="*80 + "\n")
        console.print("[bold green]Mission Brief Complete - Interactive Session Active[/bold green]\n")
        console.print("You can now interact with the crew. Special commands:")
        console.print("  • [cyan]'status'[/cyan] - Show pallet status")
        console.print("  • [cyan]'release PALLET-XX'[/cyan] - Release a specific pallet")
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
                    console.print(f"[bold]Released: {pallet_tracker.get_released_count()} pallets[/bold]\n")
                    continue

                if user_input.lower().startswith('release '):
                    pallet_id = user_input[8:].strip().upper()
                    if pallet_tracker.release_pallet(pallet_id):
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

                # Display agent responses (only the new ones from this turn)
                for msg in turn_result["agent_responses"]:
                    console.print(f"\n[green]{msg.format_for_display()}[/green]\n")

            except KeyboardInterrupt:
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

        orchestrator.stop()
        console.print("\n[yellow]Mission session ended.[/yellow]")

        # Final pallet status
        console.print("\n[bold]Final Pallet Status:[/bold]")
        console.print(pallet_tracker.get_status_table())

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

