#!/usr/bin/env python3
"""
Live Dashboard Demo for Multi-Agent Collaboration

This demonstrates the real-time visual dashboard showing:
- Agent status and activity
- Message flow
- Agent memory
- Mission progress

Scenario: Coast Guard SAR Mission with Live Monitoring
"""

import asyncio
import sys
from pathlib import Path
from rich.live import Live
from rich.console import Console

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.base_agent import BaseAgent
from src.agents.squad_leader import SquadLeaderAgent
from src.channel.shared_channel import SharedChannel
from src.orchestration.orchestrator import Orchestrator
from src.ui.dashboard import create_dashboard
from src.mcp.mcp_manager import get_mcp_manager, initialize_aerospace_mcp


class DashboardDemo:
    """Runs the dashboard demonstration."""

    def __init__(self):
        self.dashboard = None
        self.orchestrator = None
        self.console = Console()
        self.live = None

    async def setup_mission(self):
        """Set up the multi-agent mission."""
        self.console.print("\n[bold cyan]🚁 Initializing Multi-Agent System...[/bold cyan]\n")

        # Initialize MCP if available
        base_path = Path(__file__).parent.parent
        aerospace_path = str(base_path / "aerospace-mcp")

        mcp_manager = None
        if Path(aerospace_path).exists():
            self.console.print("🔧 Connecting to aerospace-mcp...")
            await initialize_aerospace_mcp(aerospace_path)
            mcp_manager = await get_mcp_manager()
            tools = mcp_manager.get_available_tools()
            self.console.print(f"✅ {len(tools)} aviation tools available\n")
        else:
            self.console.print("⚠️  No MCP servers found (optional)\n")

        # Create agents
        squad_leader = SquadLeaderAgent(
            agent_id="leader",
            callsign="RESCUE-LEAD",
            mcp_manager=mcp_manager
        )

        flight_planner = BaseAgent(
            agent_id="planner",
            callsign="ALPHA-ONE",
            mcp_manager=mcp_manager,
            system_prompt="You are a flight planning specialist. Use tools to find airports and plan routes."
        )

        navigator = BaseAgent(
            agent_id="navigator",
            callsign="ALPHA-TWO",
            mcp_manager=mcp_manager,
            system_prompt="You are a navigation specialist. Calculate distances and track positions."
        )

        weather_officer = BaseAgent(
            agent_id="weather",
            callsign="ALPHA-THREE",
            system_prompt="You are a weather officer. Assess conditions and provide safety recommendations."
        )

        # Setup orchestration
        channel = SharedChannel()
        self.orchestrator = Orchestrator(channel=channel)
        self.orchestrator.add_agent(squad_leader)
        self.orchestrator.add_agent(flight_planner)
        self.orchestrator.add_agent(navigator)
        self.orchestrator.add_agent(weather_officer)
        self.orchestrator.start()

        # Create dashboard with agents
        agents = self.orchestrator.get_active_agents()
        self.dashboard = create_dashboard(agents)

        # Add initial system message
        self.dashboard.add_message(channel.messages[0])  # "Collaboration session started"

        self.console.print("[bold green]✅ System Ready![/bold green]")
        self.console.print("[dim]Starting live dashboard...[/dim]\n")

        await asyncio.sleep(2)  # Brief pause

    async def run_automated_demo(self):
        """Run an automated demonstration sequence."""

        # Demo messages to send
        demo_sequence = [
            {
                "message": "All stations, this is Command, we have a SAR mission 150 nautical miles west of San Francisco, over.",
                "pause": 3
            },
            {
                "message": "Rescue Lead, coordinate your team for SAR operations, over.",
                "pause": 5
            },
            {
                "message": "Alpha One, search for suitable airports near San Francisco for SAR staging, over.",
                "pause": 8
            },
            {
                "message": "Alpha Two, calculate distance from San Francisco International to the distress coordinates, over.",
                "pause": 8
            },
            {
                "message": "Alpha Three, assess weather conditions for the mission, over.",
                "pause": 6
            },
            {
                "message": "All stations, provide status update, over.",
                "pause": 10
            }
        ]

        for step in demo_sequence:
            # Send message
            turn_result = await self.orchestrator.run_turn(
                user_message=step["message"],
                max_agent_responses=3
            )

            # Add messages to dashboard
            if turn_result["user_message"]:
                self.dashboard.add_message(turn_result["user_message"])

            for response in turn_result["agent_responses"]:
                self.dashboard.add_message(response)

            # Update dashboard
            self.dashboard.update()

            # Pause
            await asyncio.sleep(step["pause"])

    async def run_interactive(self):
        """Run interactive mode with user input."""

        self.console.print("\n[bold yellow]Interactive Mode Enabled[/bold yellow]")
        self.console.print("[dim]Type messages to send to agents (Ctrl+C to exit)[/dim]\n")

        while True:
            try:
                # Get user input (note: this will pause the live display)
                message = await asyncio.get_event_loop().run_in_executor(
                    None, input, "Your message: "
                )

                if message.strip():
                    # Process message
                    turn_result = await self.orchestrator.run_turn(
                        user_message=message,
                        max_agent_responses=3
                    )

                    # Add to dashboard
                    if turn_result["user_message"]:
                        self.dashboard.add_message(turn_result["user_message"])

                    for response in turn_result["agent_responses"]:
                        self.dashboard.add_message(response)

                    # Update
                    self.dashboard.update()

            except EOFError:
                break

    async def run(self, mode: str = "auto"):
        """Run the dashboard demo.

        Args:
            mode: 'auto' for automated demo, 'interactive' for user input
        """
        try:
            # Setup
            await self.setup_mission()

            # Start live dashboard
            with Live(self.dashboard.layout, refresh_per_second=4, console=self.console) as live:
                self.live = live

                # Initial update
                self.dashboard.update()

                if mode == "auto":
                    # Run automated sequence
                    await self.run_automated_demo()

                    # Keep showing for a bit
                    self.console.print("\n[bold green]Demo complete! Dashboard will stay visible...[/bold green]")
                    self.console.print("[dim]Press Ctrl+C to exit[/dim]\n")

                    # Wait for interrupt
                    try:
                        while True:
                            await asyncio.sleep(1)
                            self.dashboard.update()
                    except KeyboardInterrupt:
                        pass

                else:
                    # Interactive mode
                    await self.run_interactive()

        except KeyboardInterrupt:
            self.console.print("\n\n[yellow]Dashboard stopped[/yellow]")

        except Exception as e:
            self.console.print(f"\n[bold red]Error: {e}[/bold red]")
            import traceback
            traceback.print_exc()

        finally:
            # Cleanup
            if self.orchestrator:
                mcp_manager = await get_mcp_manager() if Path(str(Path(__file__).parent.parent / "aerospace-mcp")).exists() else None
                if mcp_manager:
                    await mcp_manager.cleanup()

            self.console.print("\n[dim]Thanks for trying the dashboard demo![/dim]")


async def main():
    """Main entry point."""
    import sys

    # Check mode
    mode = "auto"
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        mode = "interactive"

    console = Console()

    console.print("\n[bold cyan]╔══════════════════════════════════════════════════════════╗[/bold cyan]")
    console.print("[bold cyan]║      MULTI-AGENT COLLABORATION - LIVE DASHBOARD      ║[/bold cyan]")
    console.print("[bold cyan]╚══════════════════════════════════════════════════════════╝[/bold cyan]")

    if mode == "auto":
        console.print("\n[bold]Automated Demo Mode[/bold]")
        console.print("Watch as agents collaborate in real-time!")
        console.print("[dim]Run with --interactive for interactive mode[/dim]")
    else:
        console.print("\n[bold]Interactive Mode[/bold]")
        console.print("You can send messages to the agents")

    console.print()

    demo = DashboardDemo()
    await demo.run(mode=mode)


if __name__ == "__main__":
    asyncio.run(main())
