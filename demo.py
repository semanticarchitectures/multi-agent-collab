#!/usr/bin/env python3
"""
Simple demo script showing 2 agents communicating via voice net protocol.

This demonstrates:
- Squad leader and specialist agent collaboration
- Voice net protocol communication
- Speaking criteria and response logic
- Multi-turn conversation flow
"""

import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from src.agents.base_agent import BaseAgent
from src.agents.squad_leader import SquadLeaderAgent
from src.agents.speaking_criteria import (
    KeywordCriteria,
    CompositeCriteria,
    DirectAddressCriteria
)
from src.channel.shared_channel import SharedChannel
from src.orchestration.orchestrator import Orchestrator


def print_separator(title=""):
    """Print a visual separator."""
    width = 80
    if title:
        print(f"\n{'=' * width}")
        print(f"{title.center(width)}")
        print(f"{'=' * width}\n")
    else:
        print(f"\n{'-' * width}\n")


def main():
    """Run the demo."""
    print_separator("MULTI-AGENT COLLABORATION DEMO")

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        print("Please set your Anthropic API key:")
        print("  export ANTHROPIC_API_KEY='your-key-here'")
        sys.exit(1)

    print("Initializing multi-agent system...")
    print("Creating shared communication channel...")

    # Create shared channel
    channel = SharedChannel()

    # Create orchestrator
    orchestrator = Orchestrator(channel=channel)

    print("Creating agents...\n")

    # Create squad leader
    leader = SquadLeaderAgent(
        agent_id="leader_1",
        callsign="Alpha Lead"
    )
    orchestrator.add_agent(leader)
    print(f"  ✓ Created {leader.callsign} (Squad Leader)")

    # Create specialist agent
    specialist_prompt = """You are a specialist agent focusing on data analysis and problem-solving.

ROLE:
- Analyze data and provide insights
- Respond when your expertise is needed
- Support the squad leader's mission
- Collaborate with other team members

EXPERTISE AREAS:
- Data analysis and interpretation
- Problem decomposition
- Pattern recognition
- Strategic recommendations"""

    specialist = BaseAgent(
        agent_id="specialist_1",
        callsign="Alpha One",
        system_prompt=specialist_prompt,
        speaking_criteria=CompositeCriteria([
            DirectAddressCriteria(),
            KeywordCriteria(["data", "analyze", "analysis", "problem", "pattern"])
        ])
    )
    orchestrator.add_agent(specialist)
    print(f"  ✓ Created {specialist.callsign} (Data Specialist)")

    orchestrator.start()

    print("\nAgents are ready. Beginning communication scenarios...")

    # Scenario 1: General question (squad leader responds)
    print_separator("SCENARIO 1: General Status Check")
    print("User asks a general question about status.")
    print("Expected: Squad leader responds\n")

    user_msg = "What's our current status?"
    print(f"[USER] {user_msg}\n")

    orchestrator.run_turn(user_message=user_msg)

    # Show responses
    recent = channel.get_recent_messages(3)
    for msg in recent:
        if msg.sender_id not in ["user", "system"]:
            print(f"[{msg.sender_callsign}] {msg.content}\n")

    input("Press Enter to continue to next scenario...")

    # Scenario 2: Direct address to specialist
    print_separator("SCENARIO 2: Direct Address to Specialist")
    print("User directly addresses the data specialist.")
    print("Expected: Specialist responds\n")

    user_msg = "Alpha One, I need you to analyze this data pattern we've been seeing."
    print(f"[USER] {user_msg}\n")

    orchestrator.run_turn(user_message=user_msg)

    # Show responses
    recent = channel.get_recent_messages(3)
    for msg in recent:
        if msg.sender_id not in ["user", "system"]:
            print(f"[{msg.sender_callsign}] {msg.content}\n")

    input("Press Enter to continue to next scenario...")

    # Scenario 3: Keyword trigger
    print_separator("SCENARIO 3: Keyword Trigger")
    print("User mentions keywords that trigger specialist response.")
    print("Expected: Specialist responds to expertise request\n")

    user_msg = "We have a problem with our data analysis pipeline. Need help analyzing the patterns."
    print(f"[USER] {user_msg}\n")

    orchestrator.run_turn(user_message=user_msg, max_agent_responses=2)

    # Show responses
    recent = channel.get_recent_messages(4)
    for msg in recent:
        if msg.sender_id not in ["user", "system"]:
            print(f"[{msg.sender_callsign}] {msg.content}\n")

    input("Press Enter to continue to next scenario...")

    # Scenario 4: Agent-to-agent communication
    print_separator("SCENARIO 4: Inter-Agent Communication")
    print("Squad leader asks specialist for status.")
    print("Expected: Specialist responds to leader\n")

    # Leader sends message
    leader_msg = channel.add_message(
        sender_id=leader.agent_id,
        content="Alpha One, this is Alpha Lead, requesting status on analysis task, over.",
        sender_callsign=leader.callsign
    )
    print(f"[{leader.callsign}] {leader_msg.content}\n")

    # Process specialist response
    orchestrator.process_responses(max_responses=1)

    # Show response
    recent = channel.get_recent_messages(2)
    for msg in recent:
        if msg.sender_id == specialist.agent_id:
            print(f"[{msg.sender_callsign}] {msg.content}\n")

    # Show full conversation history
    print_separator("FULL CONVERSATION HISTORY")
    print(channel.format_history(30))

    print_separator("DEMO COMPLETE")
    print("This demo showed:")
    print("  • Squad leader coordinating the team")
    print("  • Direct addressing using voice net protocol")
    print("  • Keyword-based response triggering")
    print("  • Inter-agent communication")
    print("  • Clear, structured communication patterns")
    print("\nThe system is ready for interactive use!")
    print("Try: python -m src.cli.main demo")
    print("Or:  python -m src.cli.main interactive")

    orchestrator.stop()


if __name__ == "__main__":
    main()
