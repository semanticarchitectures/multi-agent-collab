#!/usr/bin/env python3
"""
Aerospace MCP Integration Demo

Demonstrates multi-agent collaboration with real aerospace engineering tools
via the Model Context Protocol (MCP).

Features:
- Squad leader coordinating aerospace missions
- Aerospace specialist with MCP tool access
- Real flight planning and aircraft performance calculations
- Voice net protocol communications
"""

import os
import sys
import asyncio

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from src.agents.squad_leader import SquadLeaderAgent
from src.agents.aerospace_agent import AerospaceAgent
from src.agents.speaking_criteria import KeywordCriteria, CompositeCriteria, DirectAddressCriteria
from src.channel.shared_channel import SharedChannel
from src.orchestration.orchestrator import Orchestrator
from src.mcp.mcp_manager import initialize_aerospace_mcp, get_mcp_manager


def print_separator(title=""):
    """Print a visual separator."""
    width = 80
    if title:
        print(f"\n{'=' * width}")
        print(f"{title.center(width)}")
        print(f"{'=' * width}\n")
    else:
        print(f"\n{'-' * width}\n")


async def main():
    """Run the aerospace MCP integration demo."""
    print_separator("AEROSPACE MCP INTEGRATION DEMO")

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        print("Please set your Anthropic API key:")
        print("  export ANTHROPIC_API_KEY='your-key-here'")
        sys.exit(1)

    print("Initializing multi-agent aerospace system...")
    print("Connecting to Aerospace MCP server...\n")

    # Initialize MCP connection
    aerospace_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "aerospace-mcp"
    )

    success = await initialize_aerospace_mcp(aerospace_path)

    if not success:
        print("❌ Failed to connect to Aerospace MCP server")
        print(f"   Make sure the server is available at: {aerospace_path}")
        sys.exit(1)

    print("✅ Connected to Aerospace MCP server")

    # Show available tools
    manager = await get_mcp_manager()
    tools = manager.get_available_tools("aerospace-mcp")
    print(f"✅ Discovered {len(tools)} aerospace tools\n")

    # Create shared channel
    channel = SharedChannel()

    # Create orchestrator
    orchestrator = Orchestrator(channel=channel)

    print("Creating agents...\n")

    # Create squad leader
    leader = SquadLeaderAgent(
        agent_id="leader",
        callsign="Hawk Lead"
    )
    orchestrator.add_agent(leader)
    print(f"  ✓ Created {leader.callsign} (Squad Leader)")

    # Create aerospace specialist
    aerospace = AerospaceAgent(
        agent_id="aerospace_specialist",
        callsign="Hawk One"
    )
    orchestrator.add_agent(aerospace)
    print(f"  ✓ Created {aerospace.callsign} (Aerospace Specialist)")

    orchestrator.start()

    print("\nAgents are ready. Beginning aerospace mission scenarios...")

    # Scenario 1: Flight planning request
    print_separator("SCENARIO 1: Flight Planning Mission")
    print("User requests flight plan from San Francisco to Tokyo.")
    print("Expected: Aerospace specialist uses MCP tools\n")

    user_msg = "Hawk One, I need a flight plan from San Francisco to Tokyo using a Boeing 777-300ER."
    print(f"[USER] {user_msg}\n")

    orchestrator.run_turn(user_message=user_msg)

    # Show responses
    recent = channel.get_recent_messages(5)
    for msg in recent:
        if msg.sender_id not in ["user", "system"]:
            print(f"[{msg.sender_callsign}] {msg.content}\n")

    print("\n[INFO] The aerospace agent has access to these MCP tools:")
    print("  • plan_flight - Calculate flight plans with fuel estimates")
    print("  • airports_by_city - Search for airports")
    print("  • And 30+ other aerospace analysis tools\n")

    input("Press Enter to continue to next scenario...")

    # Scenario 2: Airport information
    print_separator("SCENARIO 2: Airport Intelligence Request")
    print("User asks about airports in a specific city.")
    print("Expected: Aerospace specialist queries airport database\n")

    user_msg = "What airports are available in London?"
    print(f"[USER] {user_msg}\n")

    orchestrator.run_turn(user_message=user_msg)

    # Show responses
    recent = channel.get_recent_messages(5)
    for msg in recent[-3:]:
        if msg.sender_id not in ["user", "system"]:
            print(f"[{msg.sender_callsign}] {msg.content}\n")

    input("Press Enter to continue to next scenario...")

    # Scenario 3: Squad coordination
    print_separator("SCENARIO 3: Mission Coordination")
    print("User asks general question about capabilities.")
    print("Expected: Squad leader coordinates response\n")

    user_msg = "What aerospace analysis capabilities do we have?"
    print(f"[USER] {user_msg}\n")

    orchestrator.run_turn(user_message=user_msg, max_agent_responses=2)

    # Show responses
    recent = channel.get_recent_messages(5)
    for msg in recent[-4:]:
        if msg.sender_id not in ["user", "system"]:
            print(f"[{msg.sender_callsign}] {msg.content}\n")

    # Show full conversation history
    print_separator("FULL MISSION TRANSCRIPT")
    print(channel.format_history(30))

    print_separator("DEMO COMPLETE")
    print("This demonstration showed:")
    print("  ✓ Multi-agent collaboration")
    print("  ✓ MCP server integration")
    print("  ✓ Real aerospace engineering tools")
    print("  ✓ Voice net protocol communications")
    print("  ✓ Squad-based coordination")
    print("\nYour multi-agent system is now capable of:")
    print("  • Flight planning and navigation")
    print("  • Aircraft performance analysis")
    print("  • Atmospheric modeling")
    print("  • Orbital mechanics calculations")
    print("  • Aerodynamic analysis")
    print("  • And much more!")
    print("\nThe agents can now assist with real aerospace engineering tasks!")

    # Cleanup
    orchestrator.stop()
    await manager.close()


if __name__ == "__main__":
    asyncio.run(main())
