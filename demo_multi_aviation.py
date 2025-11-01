#!/usr/bin/env python3
"""
Multi-Aviation MCP Integration Demo

Demonstrates multi-agent collaboration with multiple aviation MCP servers:
- aerospace-mcp: Engineering calculations and flight planning
- aviation-weather-mcp: Weather data and METAR/TAF
- blevinstein/aviation-mcp: General aviation utilities

Features:
- Squad leader coordinating missions
- Aerospace specialist with access to all aviation tools
- Real-world aviation scenarios
- Voice net protocol communications
"""

import os
import sys
import asyncio

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from src.agents.squad_leader import SquadLeaderAgent
from src.agents.aerospace_agent import AerospaceAgent
from src.channel.shared_channel import SharedChannel
from src.orchestration.orchestrator import Orchestrator
from src.mcp.mcp_manager import initialize_all_aviation_mcps, get_mcp_manager


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
    """Run the multi-aviation MCP integration demo."""
    print_separator("MULTI-AVIATION MCP INTEGRATION DEMO")

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        print("Please set your Anthropic API key:")
        print("  export ANTHROPIC_API_KEY='your-key-here'")
        sys.exit(1)

    print("Initializing multi-agent aerospace system...")
    print("Connecting to Aviation MCP servers...\n")

    # Get parent directory for MCP servers
    parent_dir = os.path.dirname(os.path.dirname(__file__))

    # Define server paths
    aerospace_path = os.path.join(parent_dir, "aerospace-mcp")
    aviation_weather_path = os.path.join(parent_dir, "aviation-weather-mcp")
    blevinstein_aviation_path = os.path.join(parent_dir, "aviation-mcp")

    # Check which servers exist
    servers_to_connect = {}
    if os.path.exists(aerospace_path):
        servers_to_connect["aerospace_path"] = aerospace_path
    if os.path.exists(aviation_weather_path):
        servers_to_connect["aviation_weather_path"] = aviation_weather_path
    if os.path.exists(blevinstein_aviation_path):
        servers_to_connect["blevinstein_aviation_path"] = blevinstein_aviation_path

    if not servers_to_connect:
        print("❌ No MCP servers found")
        print("Please run: python verify_all_mcp_servers.py")
        sys.exit(1)

    # Initialize all available servers
    results = await initialize_all_aviation_mcps(**servers_to_connect)

    # Report connection results
    connected_servers = []
    for server_name, success in results.items():
        if success:
            print(f"✅ Connected to {server_name}")
            connected_servers.append(server_name)
        else:
            print(f"⚠️  Failed to connect to {server_name}")

    if not connected_servers:
        print("\n❌ No servers connected successfully")
        sys.exit(1)

    # Show available tools
    manager = await get_mcp_manager()
    total_tools = sum(len(manager.get_available_tools(srv)) for srv in connected_servers)
    print(f"✅ Discovered {total_tools} total tools from {len(connected_servers)} servers\n")

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

    print("\nAgents are ready. Beginning aviation mission scenarios...")

    # Scenario 1: Flight planning
    print_separator("SCENARIO 1: Flight Planning with Weather")
    print("User requests comprehensive flight planning with weather check.")
    print("Expected: Agent uses aerospace-mcp for planning\n")

    user_msg = "Hawk One, plan a flight from San Francisco (SFO) to Los Angeles (LAX). Also check current weather at both airports."
    print(f"[USER] {user_msg}\n")

    orchestrator.run_turn(user_message=user_msg)

    # Show responses
    recent = channel.get_recent_messages(5)
    for msg in recent:
        if msg.sender_id not in ["user", "system"]:
            print(f"[{msg.sender_callsign}] {msg.content}\n")

    input("Press Enter to continue to next scenario...")

    # Scenario 2: Weather analysis
    if "aviation-weather-mcp" in connected_servers:
        print_separator("SCENARIO 2: Aviation Weather Analysis")
        print("User asks for detailed weather information.")
        print("Expected: Agent uses aviation-weather-mcp for METAR/TAF\n")

        user_msg = "Get me the current METAR and TAF for John F. Kennedy International (KJFK)."
        print(f"[USER] {user_msg}\n")

        orchestrator.run_turn(user_message=user_msg)

        # Show responses
        recent = channel.get_recent_messages(5)
        for msg in recent[-3:]:
            if msg.sender_id not in ["user", "system"]:
                print(f"[{msg.sender_callsign}] {msg.content}\n")

        input("Press Enter to continue to next scenario...")

    # Scenario 3: Complex mission coordination
    print_separator("SCENARIO 3: Multi-Tool Mission Analysis")
    print("User asks for comprehensive pre-flight briefing.")
    print("Expected: Agent coordinates multiple MCP tools\n")

    user_msg = "I need a complete pre-flight briefing for a flight from Chicago O'Hare (KORD) to Denver (KDEN). Include route, weather, and any performance considerations."
    print(f"[USER] {user_msg}\n")

    orchestrator.run_turn(user_message=user_msg, max_agent_responses=2)

    # Show responses
    recent = channel.get_recent_messages(8)
    for msg in recent[-5:]:
        if msg.sender_id not in ["user", "system"]:
            print(f"[{msg.sender_callsign}] {msg.content}\n")

    input("Press Enter to continue to next scenario...")

    # Scenario 4: Capabilities overview
    print_separator("SCENARIO 4: System Capabilities")
    print("User asks about available tools.")
    print("Expected: Squad leader and specialist coordinate\n")

    user_msg = "What aviation analysis capabilities are available?"
    print(f"[USER] {user_msg}\n")

    orchestrator.run_turn(user_message=user_msg, max_agent_responses=2)

    # Show responses
    recent = channel.get_recent_messages(5)
    for msg in recent[-4:]:
        if msg.sender_id not in ["user", "system"]:
            print(f"[{msg.sender_callsign}] {msg.content}\n")

    # Show full conversation history
    print_separator("FULL MISSION TRANSCRIPT")
    print(channel.format_history(40))

    # Summary
    print_separator("DEMO COMPLETE")
    print("This demonstration showed:")
    print("  ✓ Multi-agent collaboration")
    print("  ✓ Multiple MCP server integration")
    print("  ✓ Real aviation engineering and weather tools")
    print("  ✓ Voice net protocol communications")
    print("  ✓ Squad-based coordination")

    print(f"\nConnected MCP Servers ({len(connected_servers)}):")
    for server_name in connected_servers:
        tool_count = len(manager.get_available_tools(server_name))
        print(f"  • {server_name}: {tool_count} tools")

    print("\nYour multi-agent system now has comprehensive aviation capabilities:")
    print("  • Flight planning and navigation")
    print("  • Weather reports and forecasts")
    print("  • Aircraft performance analysis")
    print("  • Atmospheric modeling")
    print("  • Airport database queries")
    print("  • And much more!")

    print("\nThe agents can assist with real-world aviation operations!")

    # Cleanup
    orchestrator.stop()
    await manager.close()


if __name__ == "__main__":
    asyncio.run(main())
