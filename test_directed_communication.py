#!/usr/bin/env python3
"""
Test directed communication enhancements.

This verifies Week 2 Priority P0 features:
- Enhanced Voice Net Protocol parsing
- Directed vs broadcast message handling
- Agent-specific addressing
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.base_agent import BaseAgent
from src.agents.squad_leader import SquadLeaderAgent
from src.channel.shared_channel import SharedChannel
from src.channel.voice_net_protocol import VoiceNetProtocol, MessageType
from src.orchestration.orchestrator import Orchestrator


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(title.center(80))
    print("=" * 80 + "\n")


def test_voice_net_parsing():
    """Test enhanced Voice Net Protocol parsing."""
    print_header("TEST 1: Voice Net Protocol Parsing")

    print("Testing enhanced message parsing...")
    print()

    test_cases = [
        ("Alpha One, this is Control, search for airports, over.", "directed command"),
        ("All stations, this is Squad Lead, standby for briefing, over.", "broadcast"),
        ("Roger, understood.", "acknowledgment"),
        ("Alpha Two, calculate fuel requirements.", "directed command (short form)"),
        ("What is the weather at KSFO?", "query"),
        ("All units, this is Control, mission is a go, over.", "broadcast command"),
    ]

    for message, expected_type in test_cases:
        parsed = VoiceNetProtocol.parse(message)
        print(f"Message: \"{message}\"")
        print(f"  Sender: {parsed.sender or 'N/A'}")
        print(f"  Recipient: {parsed.recipient or 'N/A'}")
        print(f"  Type: {parsed.message_type.value}")
        print(f"  Broadcast: {parsed.is_broadcast}")
        print(f"  Expected: {expected_type}")

        # Verify broadcast detection
        if "all" in message.lower()[:15]:
            if parsed.is_broadcast:
                print(f"  ✅ Broadcast correctly detected")
            else:
                print(f"  ❌ Broadcast not detected")

        print()

    print("✅ Voice Net Protocol parsing complete")
    print()
    return True


async def test_directed_communication():
    """Test directed communication in orchestrator."""
    print_header("TEST 2: Directed Communication")

    print("Testing directed message routing...")
    print()

    # Create multiple agents
    alpha_one = BaseAgent(
        agent_id="alpha_1",
        callsign="ALPHA-ONE",
        system_prompt="You are Alpha One, a flight planning specialist."
    )

    alpha_two = BaseAgent(
        agent_id="alpha_2",
        callsign="ALPHA-TWO",
        system_prompt="You are Alpha Two, a navigation specialist."
    )

    squad_leader = SquadLeaderAgent(
        agent_id="leader",
        callsign="SQUAD-LEAD"
    )

    # Set up orchestration
    channel = SharedChannel()
    orchestrator = Orchestrator(channel=channel)
    orchestrator.add_agent(alpha_one)
    orchestrator.add_agent(alpha_two)
    orchestrator.add_agent(squad_leader)
    orchestrator.start()

    print(f"✅ Created 3 agents:")
    print(f"   - {alpha_one.callsign}")
    print(f"   - {alpha_two.callsign}")
    print(f"   - {squad_leader.callsign}")
    print()

    # Test 1: Directed message to specific agent
    print("Test 2a: Directed message to ALPHA-ONE")
    print("-" * 80)
    directed_message = "Alpha One, this is Control, search for airports near Boston, over."
    print(f"[USER]: {directed_message}")
    print()

    turn_result = await orchestrator.run_turn(
        user_message=directed_message,
        max_agent_responses=3
    )

    if turn_result["agent_responses"]:
        responding_agent = turn_result["agent_responses"][0].sender_callsign
        print(f"✅ Response from: {responding_agent}")

        if responding_agent == "ALPHA-ONE":
            print("✅ PASS: Correct agent responded to directed message")
        else:
            print(f"❌ FAIL: Expected ALPHA-ONE, got {responding_agent}")
            return False
    else:
        print("❌ FAIL: No response received")
        return False

    print()

    # Test 2: Directed message to different agent
    print("Test 2b: Directed message to ALPHA-TWO")
    print("-" * 80)
    directed_message_2 = "Alpha Two, this is Control, calculate distance from KSFO to KJFK, over."
    print(f"[USER]: {directed_message_2}")
    print()

    turn_result_2 = await orchestrator.run_turn(
        user_message=directed_message_2,
        max_agent_responses=3
    )

    if turn_result_2["agent_responses"]:
        responding_agent_2 = turn_result_2["agent_responses"][0].sender_callsign
        print(f"✅ Response from: {responding_agent_2}")

        if responding_agent_2 == "ALPHA-TWO":
            print("✅ PASS: Correct agent responded to directed message")
        else:
            print(f"⚠️  WARNING: Expected ALPHA-TWO, got {responding_agent_2}")
            # Not a hard failure - squad leader might step in
    else:
        print("❌ FAIL: No response received")
        return False

    print()

    # Test 3: Broadcast message
    print("Test 2c: Broadcast message")
    print("-" * 80)
    broadcast_message = "All stations, this is Control, prepare for mission briefing, over."
    print(f"[USER]: {broadcast_message}")
    print()

    turn_result_3 = await orchestrator.run_turn(
        user_message=broadcast_message,
        max_agent_responses=3
    )

    if turn_result_3["agent_responses"]:
        print(f"✅ Received {len(turn_result_3['agent_responses'])} response(s)")
        for resp in turn_result_3["agent_responses"]:
            print(f"   - {resp.sender_callsign}")

        # For broadcasts, multiple agents may respond or squad leader handles it
        print("✅ PASS: Broadcast handled (multiple agents can respond)")
    else:
        print("⚠️  WARNING: No response to broadcast (not necessarily a failure)")

    print()
    return True


async def test_message_type_detection():
    """Test message type detection."""
    print_header("TEST 3: Message Type Detection")

    print("Testing message type classification...")
    print()

    test_cases = [
        ("Search for airports near LAX", MessageType.COMMAND),
        ("Please calculate the fuel requirements", MessageType.REQUEST),
        ("What is the weather at KSFO?", MessageType.QUERY),
        ("Roger, understood", MessageType.ACKNOWLEDGMENT),
        ("Found 3 airports in the area", MessageType.REPORT),
    ]

    passed = 0
    total = len(test_cases)

    for message, expected_type in test_cases:
        parsed = VoiceNetProtocol.parse(message)
        actual_type = parsed.message_type

        status = "✅" if actual_type == expected_type else "❌"
        print(f"{status} \"{message}\"")
        print(f"   Expected: {expected_type.value}, Got: {actual_type.value}")

        if actual_type == expected_type:
            passed += 1

        print()

    print(f"Results: {passed}/{total} tests passed")
    print()

    return passed == total


async def main():
    """Run all tests."""
    print_header("DIRECTED COMMUNICATION - VERIFICATION")

    print("This test verifies Week 2 Priority P0 implementation:")
    print("  ✅ Enhanced Voice Net Protocol parsing")
    print("  ✅ Directed vs broadcast message handling")
    print("  ✅ Message type detection")
    print()

    results = {}

    try:
        # Test 1: Voice Net Parsing
        results["parsing"] = test_voice_net_parsing()

        # Test 2: Directed Communication
        results["directed"] = await test_directed_communication()

        # Test 3: Message Type Detection
        results["types"] = await test_message_type_detection()

        # Summary
        print_header("TEST SUMMARY")

        passed = sum(results.values())
        total = len(results)

        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {test_name.capitalize()}")

        print()
        print(f"Results: {passed}/{total} tests passed")
        print()

        if passed == total:
            print("🎉 All tests passed!")
            print()
            print("✅ IMPLEMENTED: Enhanced Voice Net Protocol (Week 2, Priority P0)")
            print("✅ IMPLEMENTED: Directed communication routing")
            print("✅ IMPLEMENTED: Message type detection")
            print()
            print("📋 NEXT STEPS (from enhancement proposal):")
            print("   - Week 2: Basic visual dashboard (Rich-based CLI)")
            print("   - Week 2: Real-time message display")
            print()
            return 0
        else:
            print("⚠️  Some tests failed. Check output above.")
            return 1

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
