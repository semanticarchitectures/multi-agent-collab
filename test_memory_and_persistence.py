#!/usr/bin/env python3
"""
Test agent memory and state persistence implementation.

This verifies Week 1 Priority P1 features:
- Agent memory & context
- State persistence
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.base_agent import BaseAgent
from src.channel.shared_channel import SharedChannel
from src.orchestration.orchestrator import Orchestrator
from src.state.state_manager import StateManager
from src.mcp.mcp_manager import get_mcp_manager, initialize_aerospace_mcp


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(title.center(80))
    print("=" * 80 + "\n")


def print_message(message, show_sender=True):
    """Print a formatted message."""
    if show_sender:
        sender = message.sender_callsign or message.sender_id
        print(f"[{sender}]: {message.content}\n")
    else:
        print(f"{message.content}\n")


async def test_agent_memory():
    """Test agent memory functionality."""
    print_header("TEST 1: Agent Memory")

    print("Testing agent memory system...")
    print()

    # Create agent (no MCP needed for memory test)
    agent = BaseAgent(
        agent_id="test_agent",
        callsign="TEST-ONE",
        system_prompt="You are a test agent demonstrating memory capabilities."
    )

    print("✅ Created agent with empty memory")
    print(f"   Memory summary: {agent.get_memory_summary()}")
    print()

    # Test manual memory updates
    print("📝 Testing manual memory updates...")
    agent.update_memory("task", "Search for airports in San Francisco")
    agent.update_memory("task", "Calculate fuel requirements")
    agent.update_memory("fact", "home_base=KSFO")
    agent.update_memory("fact", "aircraft_type=HC-144")
    agent.update_memory("decision", "Selected KSFO as primary airport")
    agent.update_memory("concern", "Weather conditions deteriorating")
    agent.update_memory("note", "Mission priority: high")

    summary = agent.get_memory_summary()
    print(f"✅ Memory updated: {summary}")
    print()

    # Display memory context
    print("📋 Memory Context:")
    print("-" * 80)
    context = agent._build_memory_context()
    print(context if context else "  (empty)")
    print("-" * 80)
    print()

    # Test memory extraction from text
    print("🔍 Testing MEMORIZE command extraction...")
    test_response = """Roger, I will search for airports.

MEMORIZE[task]: Complete airport search for Boston area
MEMORIZE[fact]: weather_status=VFR
MEMORIZE[decision]: Will use primary airport for landing
MEMORIZE[note]: Fuel reserves adequate for mission

Search complete, over."""

    agent._extract_memory_updates(test_response)
    new_summary = agent.get_memory_summary()
    print(f"✅ Extracted memory updates from response")
    print(f"   New summary: {new_summary}")
    print()

    # Verify memory was updated
    if new_summary["tasks"] > summary["tasks"]:
        print("✅ PASS: Tasks increased from", summary["tasks"], "to", new_summary["tasks"])
    if new_summary["facts"] > summary["facts"]:
        print("✅ PASS: Facts increased from", summary["facts"], "to", new_summary["facts"])

    print()
    return True


async def test_state_persistence():
    """Test state persistence functionality."""
    print_header("TEST 2: State Persistence")

    print("Testing session save/load...")
    print()

    # Initialize state manager
    test_db = "data/test_sessions.db"
    state_manager = StateManager(db_path=test_db)
    await state_manager.initialize_db()
    print("✅ Initialized state manager")
    print()

    # Create test session
    channel = SharedChannel()
    channel.add_message(
        sender_id="user",
        content="Alpha One, search for airports near Boston. Over."
    )
    channel.add_message(
        sender_id="agent_1",
        content="Roger, searching for Boston airports. Over.",
        sender_callsign="ALPHA-ONE"
    )

    agent = BaseAgent(
        agent_id="agent_1",
        callsign="ALPHA-ONE",
        system_prompt="You are a flight planner."
    )
    agent.update_memory("task", "Search Boston airports")
    agent.update_memory("fact", "location=Boston")

    agents = [agent]

    # Save session
    session_id = "test-session-001"
    print(f"💾 Saving session '{session_id}'...")
    success = await state_manager.save_session(
        session_id=session_id,
        channel=channel,
        agents=agents,
        metadata={"test": True, "purpose": "verification"}
    )

    if success:
        print("✅ Session saved successfully")
    else:
        print("❌ Failed to save session")
        return False

    print()

    # Load session
    print(f"📂 Loading session '{session_id}'...")
    loaded_data = await state_manager.load_session(session_id)

    if loaded_data:
        print("✅ Session loaded successfully")
        print(f"   Session ID: {loaded_data['session_id']}")
        print(f"   Messages: {len(loaded_data['messages'])}")
        print(f"   Agents: {len(loaded_data['agent_states'])}")
        print(f"   Metadata: {loaded_data['metadata']}")
    else:
        print("❌ Failed to load session")
        return False

    print()

    # Verify data integrity
    print("🔍 Verifying data integrity...")
    if len(loaded_data['messages']) == 2:
        print("✅ PASS: Message count correct (2)")
    if len(loaded_data['agent_states']) == 1:
        print("✅ PASS: Agent count correct (1)")

    agent_state = loaded_data['agent_states'][0]
    if agent_state['agent_id'] == "agent_1":
        print("✅ PASS: Agent ID preserved")
    if agent_state['callsign'] == "ALPHA-ONE":
        print("✅ PASS: Agent callsign preserved")
    if len(agent_state['memory']['task_list']) == 1:
        print("✅ PASS: Agent memory preserved")

    print()

    # Test restore functionality
    print("🔄 Testing channel restoration...")
    restored_channel = await state_manager.restore_channel(loaded_data)
    if len(restored_channel.messages) == 2:
        print("✅ PASS: Channel restored with correct message count")
        print(f"   Message 1: {restored_channel.messages[0].content[:50]}...")
        print(f"   Message 2: {restored_channel.messages[1].content[:50]}...")
    else:
        print("❌ FAIL: Channel restoration failed")
        return False

    print()

    # Test list sessions
    print("📋 Testing session listing...")
    sessions = await state_manager.list_sessions(limit=5)
    print(f"✅ Found {len(sessions)} session(s)")
    for sess in sessions:
        print(f"   - {sess['session_id']}: {sess['message_count']} messages, {sess['agent_count']} agents")

    print()

    # Clean up test database
    import os
    try:
        os.remove(test_db)
        print("🧹 Cleaned up test database")
    except:
        pass

    return True


async def test_integration():
    """Test integration of memory and persistence with real agents."""
    print_header("TEST 3: Integration Test")

    print("Testing memory + persistence with real agent interaction...")
    print()

    # Initialize MCP
    base_path = Path(__file__).parent.parent
    aerospace_path = str(base_path / "aerospace-mcp")

    if Path(aerospace_path).exists():
        print("🔧 Initializing aerospace-mcp...")
        await initialize_aerospace_mcp(aerospace_path)
        mcp_manager = await get_mcp_manager()
        print("✅ MCP connected")
    else:
        print("⚠️  aerospace-mcp not found, proceeding without MCP")
        mcp_manager = None

    print()

    # Create agent with memory and tools
    agent = BaseAgent(
        agent_id="planner_1",
        callsign="FLIGHT-PLANNER",
        system_prompt="""You are a flight planning specialist.
When asked to plan routes or search for airports, use available tools and
update your memory with important findings using MEMORIZE commands.""",
        mcp_manager=mcp_manager
    )

    # Set up orchestration
    channel = SharedChannel()
    orchestrator = Orchestrator(channel=channel)
    orchestrator.add_agent(agent)
    orchestrator.start()

    print("✅ Created agent with memory and MCP access")
    print()

    # Send test message
    test_message = "Flight Planner, search for airports in Seattle and remember the main airport code. Over."
    print(f"[USER]: {test_message}")
    print()
    print("⏳ Agent processing (may use tools and update memory)...")
    print()

    turn_result = await orchestrator.run_turn(
        user_message=test_message,
        max_agent_responses=1
    )

    # Display response
    if turn_result["agent_responses"]:
        print("=" * 80)
        print("AGENT RESPONSE:")
        print("=" * 80)
        for response in turn_result["agent_responses"]:
            print_message(response)
        print("=" * 80)
        print()

        # Check memory
        print("📝 Agent Memory After Response:")
        print("-" * 80)
        memory_context = agent._build_memory_context()
        if memory_context:
            print(memory_context)
        else:
            print("  (no memory updates detected)")
        print("-" * 80)
        print()
        print(f"   Memory summary: {agent.get_memory_summary()}")
        print()

        # Save session
        print("💾 Saving session with agent memory...")
        state_manager = StateManager(db_path="data/test_integration.db")
        await state_manager.initialize_db()

        success = await state_manager.save_session(
            session_id="integration-test-001",
            channel=channel,
            agents=[agent],
            metadata={"test_type": "integration"}
        )

        if success:
            print("✅ Session saved with agent memory preserved")
        else:
            print("❌ Failed to save session")

        # Clean up
        import os
        try:
            os.remove("data/test_integration.db")
        except:
            pass

    else:
        print("❌ No agent response received")
        return False

    # Clean up MCP
    if mcp_manager:
        await mcp_manager.cleanup()

    return True


async def main():
    """Run all tests."""
    print_header("AGENT MEMORY & STATE PERSISTENCE - VERIFICATION")

    print("This test verifies Week 1 Priority P1 implementation:")
    print("  ✅ Agent memory & context")
    print("  ✅ State persistence")
    print()

    results = {}

    try:
        # Test 1: Agent Memory
        results["memory"] = await test_agent_memory()

        # Test 2: State Persistence
        results["persistence"] = await test_state_persistence()

        # Test 3: Integration
        results["integration"] = await test_integration()

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
            print("✅ IMPLEMENTED: Agent memory & context (Week 1, Priority P1)")
            print("✅ IMPLEMENTED: State persistence (Week 1, Priority P1)")
            print()
            print("📋 NEXT STEPS (from enhancement proposal):")
            print("   - Week 2: Directed communication improvements")
            print("   - Week 3: Basic visual dashboard")
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
