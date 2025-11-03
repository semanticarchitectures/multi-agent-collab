#!/usr/bin/env python3
"""
Interactive Multi-Agent Aviation Demo

This demonstrates the key capabilities of the multi-agent collaboration system:
- Autonomous MCP tool use (34+ aviation tools)
- Directed communication (squad leader delegation)
- Agent memory and context
- Voice net protocol
- Multi-agent coordination

Scenario: Coast Guard Search and Rescue Mission Planning
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.base_agent import BaseAgent
from src.agents.squad_leader import SquadLeaderAgent
from src.channel.shared_channel import SharedChannel
from src.orchestration.orchestrator import Orchestrator
from src.mcp.mcp_manager import get_mcp_manager, initialize_aerospace_mcp
from src.state.state_manager import StateManager


class DemoRunner:
    """Runs the interactive demo."""

    def __init__(self):
        self.orchestrator = None
        self.state_manager = None
        self.mcp_manager = None

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
            "red": "\033[91m",
            "end": "\033[0m"
        }

        if color and color in colors:
            print(f"{colors[color]}[{sender}]: {content}{colors['end']}")
        else:
            print(f"[{sender}]: {content}")
        print()

    def print_section(self, title: str):
        """Print a section header."""
        print("\n" + "─" * 80)
        print(f"  {title}")
        print("─" * 80 + "\n")

    async def setup(self):
        """Initialize the demo environment."""
        self.print_header("🚁 MULTI-AGENT AVIATION DEMO 🚁")

        print("Scenario: Coast Guard Search and Rescue Mission Planning")
        print()
        print("You are the Mission Commander coordinating a multi-agent team")
        print("to plan a search and rescue operation.")
        print()

        # Initialize MCP
        self.print_section("Initializing Aviation Systems")

        base_path = Path(__file__).parent.parent
        aerospace_path = str(base_path / "aerospace-mcp")

        if Path(aerospace_path).exists():
            print("🔧 Connecting to aerospace-mcp server...")
            await initialize_aerospace_mcp(aerospace_path)
            self.mcp_manager = await get_mcp_manager()

            tools = self.mcp_manager.get_available_tools()
            print(f"✅ Connected! {len(tools)} aviation tools available")
            print(f"   (airport search, flight planning, distance calculations, etc.)")
        else:
            print("⚠️  aerospace-mcp not found - demo will run without real aviation data")
            self.mcp_manager = None

        print()

        # Create agents
        self.print_section("Assembling Your Team")

        # Squad Leader
        squad_leader = SquadLeaderAgent(
            agent_id="squad_leader",
            callsign="RESCUE-LEAD",
            mcp_manager=self.mcp_manager,
            system_prompt="""You are RESCUE-LEAD, the mission commander for Coast Guard SAR operations.
Your role: Coordinate the team, delegate tasks, and ensure mission success.
When delegating, use directed communication: "[Callsign], [task], over."
Keep responses professional and concise."""
        )

        # Flight Planner
        flight_planner = BaseAgent(
            agent_id="flight_planner",
            callsign="ALPHA-ONE",
            mcp_manager=self.mcp_manager,
            system_prompt="""You are ALPHA-ONE, the flight planning specialist.
Your expertise: Route planning, fuel calculations, airport selection.
Use your tools to provide accurate aviation data.
When you find important information, use MEMORIZE commands to save it."""
        )

        # Navigator
        navigator = BaseAgent(
            agent_id="navigator",
            callsign="ALPHA-TWO",
            mcp_manager=self.mcp_manager,
            system_prompt="""You are ALPHA-TWO, the navigation specialist.
Your expertise: Distance calculations, coordinate tracking, position reporting.
Provide precise navigation data using available tools.
Remember key waypoints and distances."""
        )

        # Weather Officer
        weather_officer = BaseAgent(
            agent_id="weather",
            callsign="ALPHA-THREE",
            system_prompt="""You are ALPHA-THREE, the weather and conditions officer.
Your expertise: Weather analysis, risk assessment, operational safety.
Provide weather briefings and safety recommendations.
Track weather changes and concerns."""
        )

        print("👥 Team Roster:")
        print(f"   • {squad_leader.callsign} - Mission Commander (Squad Leader)")
        print(f"   • {flight_planner.callsign} - Flight Planning Specialist")
        print(f"   • {navigator.callsign} - Navigation Specialist")
        print(f"   • {weather_officer.callsign} - Weather Officer")
        print()

        # Setup orchestration
        channel = SharedChannel()
        self.orchestrator = Orchestrator(channel=channel)
        self.orchestrator.add_agent(squad_leader)
        self.orchestrator.add_agent(flight_planner)
        self.orchestrator.add_agent(navigator)
        self.orchestrator.add_agent(weather_officer)
        self.orchestrator.start()

        # Initialize state manager
        self.state_manager = StateManager()
        await self.state_manager.initialize_db()

        print("✅ Team assembled and ready for tasking")
        print()

    async def run_scenario(self):
        """Run the demo scenario."""

        self.print_section("Mission Briefing")
        print("A distress call has been received from a vessel 150nm west of San Francisco.")
        print("Your task: Plan the search and rescue operation.")
        print()

        # Scenario acts
        acts = [
            {
                "title": "Act 1: Initial Assessment",
                "description": "Get the team oriented and assess the situation",
                "prompts": [
                    ("Commander", "All stations, this is Mission Command, we have a SAR mission. Rescue Lead, take charge and coordinate the team, over."),
                    ("Suggestion", "Try: 'Alpha One, search for airports near San Francisco suitable for SAR operations, over.'")
                ]
            },
            {
                "title": "Act 2: Mission Planning",
                "description": "Plan the flight and calculate requirements",
                "prompts": [
                    ("Suggestion", "Try asking Alpha One about specific airports"),
                    ("Suggestion", "Try: 'Alpha Two, calculate distance from San Francisco to the distress coordinates, over.'"),
                    ("Suggestion", "Try: 'Alpha Three, what weather considerations should we be aware of?'")
                ]
            },
            {
                "title": "Act 3: Team Coordination",
                "description": "See the squad leader delegate tasks",
                "prompts": [
                    ("Suggestion", "Try a broadcast: 'All units, provide status update, over.'"),
                    ("Suggestion", "Ask Rescue Lead to coordinate a specific task")
                ]
            }
        ]

        for act_num, act in enumerate(acts, 1):
            self.print_header(f"{act['title']}", "=")
            print(act['description'])
            print()

            for prompt_type, prompt_text in act['prompts']:
                if prompt_type == "Commander":
                    # Run this automatically
                    self.print_message("COMMAND", prompt_text, "yellow")
                    await self.send_and_display(prompt_text)
                else:
                    # Show as suggestion
                    print(f"💡 {prompt_text}")
                    print()

            # Interactive prompt
            while True:
                print("\nOptions:")
                print("  1. Send a message to the team")
                print("  2. View team memory/context")
                print("  3. Continue to next act")
                print("  4. Save session and exit")

                choice = input("\nYour choice (1-4): ").strip()

                if choice == "1":
                    message = input("\n📡 Your message: ").strip()
                    if message:
                        await self.send_and_display(message)
                elif choice == "2":
                    self.show_team_status()
                elif choice == "3":
                    break
                elif choice == "4":
                    await self.save_and_exit()
                    return False
                else:
                    print("Invalid choice. Please enter 1-4.")

        return True

    async def send_and_display(self, message: str):
        """Send message and display responses."""
        print()

        turn_result = await self.orchestrator.run_turn(
            user_message=message,
            max_agent_responses=3
        )

        if turn_result["agent_responses"]:
            for response in turn_result["agent_responses"]:
                callsign = response.sender_callsign or response.sender_id

                # Color code by agent type
                color = "green" if "LEAD" in callsign else "blue"

                self.print_message(callsign, response.content, color)
        else:
            print("⚠️  No response received")
            print()

    def show_team_status(self):
        """Display agent memory and status."""
        self.print_section("Team Status & Memory")

        agents = self.orchestrator.get_active_agents()

        for agent in agents:
            print(f"\n{agent.callsign}:")
            print("-" * 60)

            memory_summary = agent.get_memory_summary()
            total_items = sum(memory_summary.values())

            if total_items > 0:
                print(f"  Memory: {memory_summary['tasks']} tasks, {memory_summary['facts']} facts, "
                      f"{memory_summary['concerns']} concerns")

                # Show memory details
                if agent.memory.get('task_list'):
                    print(f"  Active Tasks:")
                    for task in agent.memory['task_list'][:3]:
                        print(f"    • {task}")

                if agent.memory.get('key_facts'):
                    print(f"  Key Facts:")
                    for key, value in list(agent.memory['key_facts'].items())[:3]:
                        print(f"    • {key}: {value}")
            else:
                print("  (No memory stored yet)")

        print()

    async def save_and_exit(self):
        """Save session and exit."""
        self.print_section("Saving Mission Data")

        session_id = f"sar-mission-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        agents = self.orchestrator.get_active_agents()
        success = await self.state_manager.save_session(
            session_id=session_id,
            channel=self.orchestrator.channel,
            agents=agents,
            metadata={
                "mission_type": "SAR",
                "timestamp": datetime.now().isoformat()
            }
        )

        if success:
            print(f"✅ Mission data saved as: {session_id}")
            print(f"   You can resume this session later")
            print()
            print(f"   To export: python -c \"")
            print(f"   import asyncio")
            print(f"   from src.state.state_manager import StateManager")
            print(f"   sm = StateManager()")
            print(f"   asyncio.run(sm.export_session('{session_id}', 'mission.txt', 'txt'))")
            print(f"   \"")
        else:
            print("❌ Failed to save session")

        print()

    async def run(self):
        """Run the complete demo."""
        try:
            await self.setup()

            print("\n" + "=" * 80)
            print("DEMO READY - You can now interact with your team!")
            print("=" * 80)
            print()
            print("Tips:")
            print("  • Use callsigns for directed communication: 'Alpha One, [task]'")
            print("  • Use 'All stations' for broadcasts")
            print("  • Squad leader will delegate if asked")
            print("  • Agents use real aviation tools when available")
            print("  • Agent memory persists across the session")
            print()

            input("Press Enter to begin the mission...")

            completed = await self.run_scenario()

            if completed:
                self.print_header("🎉 DEMO COMPLETE 🎉")
                print("Key Features Demonstrated:")
                print("  ✅ Autonomous tool use (agents used real aviation data)")
                print("  ✅ Directed communication (agents responded only when addressed)")
                print("  ✅ Squad leader delegation (coordinated the team)")
                print("  ✅ Agent memory (agents remembered important information)")
                print("  ✅ Voice net protocol (professional aviation communication)")
                print()

                save_choice = input("Would you like to save this session? (y/n): ").strip().lower()
                if save_choice == 'y':
                    await self.save_and_exit()

        except KeyboardInterrupt:
            print("\n\n⚠️  Demo interrupted")
            save_choice = input("Save session before exiting? (y/n): ").strip().lower()
            if save_choice == 'y':
                await self.save_and_exit()

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

        finally:
            # Cleanup
            if self.mcp_manager:
                await self.mcp_manager.cleanup()
            print("\n👋 Thanks for trying the multi-agent demo!")


async def main():
    """Main entry point."""
    demo = DemoRunner()
    await demo.run()


if __name__ == "__main__":
    asyncio.run(main())
