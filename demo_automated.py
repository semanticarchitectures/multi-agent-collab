#!/usr/bin/env python3
"""
Automated Multi-Agent Aviation Demo

This is a non-interactive version of the demo that runs a pre-scripted
scenario to showcase the system without requiring user input.

Perfect for:
- Automated testing
- Screen recordings
- Quick demonstrations
- CI/CD validation
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.base_agent import BaseAgent
from src.agents.squad_leader import SquadLeaderAgent
from src.channel.shared_channel import SharedChannel
from src.orchestration.orchestrator import Orchestrator
from src.mcp.mcp_manager import get_mcp_manager, initialize_aerospace_mcp
from src.state.state_manager import StateManager


class AutomatedDemo:
    """Runs an automated demo with pre-scripted messages."""

    def __init__(self, delay_between_turns: float = 2.0, show_metrics: bool = True):
        self.orchestrator = None
        self.state_manager = None
        self.mcp_manager = None
        self.delay = delay_between_turns
        self.show_metrics = show_metrics

        # Metrics
        self.metrics = {
            "turns": 0,
            "responses": 0,
            "tool_calls": 0,
            "start_time": None,
            "end_time": None
        }

    def print_header(self, text: str, char: str = "="):
        """Print a formatted header."""
        width = 80
        print("\n" + char * width)
        print(text.center(width))
        print(char * width + "\n")

    def print_message(self, sender: str, content: str, color: str = ""):
        """Print a formatted message."""
        colors = {
            "blue": "\033[94m",
            "green": "\033[92m",
            "yellow": "\033[93m",
            "cyan": "\033[96m",
            "red": "\033[91m",
            "end": "\033[0m"
        }

        if color and color in colors:
            print(f"{colors[color]}[{sender}]: {content}{colors['end']}")
        else:
            print(f"[{sender}]: {content}")

    def print_section(self, title: str):
        """Print a section header."""
        print("\n" + "─" * 80)
        print(f"  {title}")
        print("─" * 80)

    async def setup(self):
        """Initialize the demo environment."""
        self.print_header("🚁 AUTOMATED MULTI-AGENT DEMO 🚁")

        print("Mode: Automated (no user input required)")
        print("Scenario: Coast Guard Search and Rescue Mission Planning")
        print()

        # Initialize MCP (with timeout)
        self.print_section("Initializing Aviation Systems")

        base_path = Path(__file__).parent.parent
        aerospace_path = str(base_path / "aerospace-mcp")

        try:
            if Path(aerospace_path).exists():
                print("🔧 Connecting to aerospace-mcp server...")

                # Try to connect with timeout
                try:
                    await asyncio.wait_for(
                        initialize_aerospace_mcp(aerospace_path),
                        timeout=10.0
                    )
                    self.mcp_manager = await get_mcp_manager()
                    tools = self.mcp_manager.get_available_tools()
                    print(f"✅ Connected! {len(tools)} aviation tools available")
                except asyncio.TimeoutError:
                    print("⚠️  Connection timeout - running without MCP tools")
                    self.mcp_manager = None
            else:
                print("⚠️  aerospace-mcp not found - running in mock mode")
                self.mcp_manager = None
        except Exception as e:
            print(f"⚠️  MCP initialization error: {e}")
            self.mcp_manager = None

        # Create agents
        self.print_section("Assembling Team")

        squad_leader = SquadLeaderAgent(
            agent_id="squad_leader",
            callsign="RESCUE-LEAD",
            mcp_manager=self.mcp_manager,
            system_prompt="""You are RESCUE-LEAD, the mission commander for Coast Guard SAR operations.
Your role: Coordinate the team, delegate tasks, ensure mission success.
Keep responses concise (2-3 sentences max).
Use directed communication: "[Callsign], [task], over." """
        )

        flight_planner = BaseAgent(
            agent_id="flight_planner",
            callsign="ALPHA-ONE",
            mcp_manager=self.mcp_manager,
            system_prompt="""You are ALPHA-ONE, flight planning specialist.
Expertise: Route planning, fuel calculations, airport selection.
Keep responses brief (2-3 sentences). Use tools when available."""
        )

        navigator = BaseAgent(
            agent_id="navigator",
            callsign="ALPHA-TWO",
            mcp_manager=self.mcp_manager,
            system_prompt="""You are ALPHA-TWO, navigation specialist.
Expertise: Distance calculations, coordinate tracking, position reporting.
Keep responses brief (2-3 sentences)."""
        )

        weather_officer = BaseAgent(
            agent_id="weather",
            callsign="ALPHA-THREE",
            system_prompt="""You are ALPHA-THREE, weather and conditions officer.
Expertise: Weather analysis, risk assessment, operational safety.
Keep responses brief (2-3 sentences)."""
        )

        print("👥 Team Roster:")
        print(f"   • {squad_leader.callsign} - Mission Commander")
        print(f"   • {flight_planner.callsign} - Flight Planning")
        print(f"   • {navigator.callsign} - Navigation")
        print(f"   • {weather_officer.callsign} - Weather")

        # Setup orchestration
        channel = SharedChannel()
        self.orchestrator = Orchestrator(channel=channel, context_window=10)
        self.orchestrator.add_agent(squad_leader)
        self.orchestrator.add_agent(flight_planner)
        self.orchestrator.add_agent(navigator)
        self.orchestrator.add_agent(weather_officer)
        self.orchestrator.start()

        # Initialize state manager
        self.state_manager = StateManager()
        await self.state_manager.initialize_db()

        print("\n✅ Demo initialized successfully")

    async def send_and_display(self, message: str, description: str = ""):
        """Send message and display responses."""
        self.metrics["turns"] += 1

        if description:
            print(f"\n💭 {description}")

        self.print_message("COMMAND", message, "yellow")

        start = time.time()

        try:
            turn_result = await asyncio.wait_for(
                self.orchestrator.run_turn(
                    user_message=message,
                    max_agent_responses=3
                ),
                timeout=45.0
            )

            elapsed = time.time() - start

            if turn_result["agent_responses"]:
                print()
                for response in turn_result["agent_responses"]:
                    self.metrics["responses"] += 1
                    callsign = response.sender_callsign or response.sender_id

                    # Color code by agent
                    if "LEAD" in callsign:
                        color = "green"
                    elif "ONE" in callsign:
                        color = "blue"
                    elif "TWO" in callsign:
                        color = "cyan"
                    else:
                        color = "blue"

                    self.print_message(callsign, response.content, color)

                print(f"\n⏱️  Response time: {elapsed:.2f}s")
            else:
                print("\n⚠️  No agent responses")

        except asyncio.TimeoutError:
            print("\n❌ Response timeout (45s)")

        # Delay before next turn
        if self.delay > 0:
            await asyncio.sleep(self.delay)

    async def run_scenario(self):
        """Run the automated scenario."""
        self.metrics["start_time"] = time.time()

        self.print_header("SCENARIO: Search and Rescue Mission")

        print("A distress call has been received from a vessel 150nm west of San Francisco.")
        print("The team must plan and coordinate the SAR operation.\n")

        await asyncio.sleep(1)

        # Define scenario turns
        turns = [
            {
                "message": "All stations, this is Mission Command, we have a SAR mission. Rescue Lead, take charge and coordinate the team, over.",
                "description": "Turn 1: Mission activation and squad leader tasking"
            },
            {
                "message": "Alpha One, search for suitable airports near San Francisco for SAR operations, over.",
                "description": "Turn 2: Request airport search from flight planner"
            },
            {
                "message": "Alpha Two, calculate the distance from San Francisco to coordinates 37.5N, 125.0W, over.",
                "description": "Turn 3: Request distance calculation from navigator"
            },
            {
                "message": "Alpha Three, what weather and safety considerations should we be aware of for this mission, over.",
                "description": "Turn 4: Request weather assessment"
            },
            {
                "message": "All stations, provide status update on your assigned tasks, over.",
                "description": "Turn 5: Broadcast status request to all agents"
            },
            {
                "message": "Rescue Lead, coordinate fuel planning and provide mission timeline recommendation, over.",
                "description": "Turn 6: Request squad leader coordination"
            }
        ]

        # Execute turns
        for i, turn in enumerate(turns, 1):
            self.print_section(f"Act {i} of {len(turns)}")
            await self.send_and_display(turn["message"], turn["description"])

        self.metrics["end_time"] = time.time()

    def show_team_memory(self):
        """Display agent memory summary."""
        self.print_section("Team Memory Summary")

        agents = self.orchestrator.get_active_agents()

        for agent in agents:
            memory_summary = agent.get_memory_summary()
            total_items = sum(memory_summary.values())

            print(f"\n{agent.callsign}:")

            if total_items > 0:
                print(f"  📊 Memory: {memory_summary['tasks']} tasks, "
                      f"{memory_summary['facts']} facts, "
                      f"{memory_summary['concerns']} concerns")

                if agent.memory.get('task_list')[:2]:
                    print(f"  Active Tasks:")
                    for task in agent.memory['task_list'][:2]:
                        print(f"    • {task}")

                if list(agent.memory.get('key_facts', {}).items())[:2]:
                    print(f"  Key Facts:")
                    for key, value in list(agent.memory['key_facts'].items())[:2]:
                        print(f"    • {key}: {value}")
            else:
                print("  (No memory stored)")

    def show_metrics(self):
        """Display demo metrics."""
        self.print_section("Demo Metrics")

        duration = self.metrics["end_time"] - self.metrics["start_time"]
        avg_per_turn = duration / self.metrics["turns"] if self.metrics["turns"] > 0 else 0

        print(f"Total Duration: {duration:.2f}s")
        print(f"Turns Executed: {self.metrics['turns']}")
        print(f"Agent Responses: {self.metrics['responses']}")
        print(f"Average per Turn: {avg_per_turn:.2f}s")
        print()

        # Orchestrator status
        status = self.orchestrator.get_status()
        print(f"Final State:")
        print(f"  • Active Agents: {status['agent_count']}")
        print(f"  • Messages: {status['message_count']}")
        print(f"  • Squad Leader: {'Yes' if status['has_squad_leader'] else 'No'}")

    async def save_session(self):
        """Save the demo session."""
        self.print_section("Saving Session")

        session_id = f"automated-demo-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        agents = self.orchestrator.get_active_agents()
        success = await self.state_manager.save_session(
            session_id=session_id,
            channel=self.orchestrator.channel,
            agents=agents,
            metadata={
                "demo_type": "automated",
                "duration": self.metrics["end_time"] - self.metrics["start_time"],
                "turns": self.metrics["turns"],
                "responses": self.metrics["responses"]
            }
        )

        if success:
            print(f"✅ Session saved: {session_id}")
        else:
            print("❌ Failed to save session")

    async def run(self):
        """Run the complete automated demo."""
        try:
            await self.setup()

            await asyncio.sleep(2)

            await self.run_scenario()

            # Show results
            self.show_team_memory()

            if self.show_metrics:
                self.show_metrics()

            await self.save_session()

            self.print_header("🎉 DEMO COMPLETE 🎉")

            print("Key Features Demonstrated:")
            print("  ✅ Multi-agent coordination")
            print("  ✅ Directed communication (agent addressing)")
            print("  ✅ Broadcast messages (all stations)")
            print("  ✅ Squad leader delegation")
            print("  ✅ Agent memory and context")
            print("  ✅ Session persistence")
            if self.mcp_manager:
                print("  ✅ Autonomous tool use (MCP integration)")
            print()

        except KeyboardInterrupt:
            print("\n\n⚠️  Demo interrupted by user")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

        finally:
            # Cleanup
            if self.mcp_manager:
                await self.mcp_manager.cleanup()

            print("👋 Demo finished!")


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Automated Multi-Agent Demo')
    parser.add_argument('--delay', type=float, default=2.0,
                       help='Delay between turns in seconds (default: 2.0)')
    parser.add_argument('--no-metrics', action='store_true',
                       help='Skip metrics display')
    parser.add_argument('--fast', action='store_true',
                       help='Fast mode (no delays)')

    args = parser.parse_args()

    delay = 0 if args.fast else args.delay
    show_metrics = not args.no_metrics

    demo = AutomatedDemo(delay_between_turns=delay, show_metrics=show_metrics)
    await demo.run()


if __name__ == "__main__":
    asyncio.run(main())
