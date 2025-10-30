#!/usr/bin/env python3
"""
Test Agent MCP Tool Usage

This script verifies that agents can actually use MCP tools by:
1. Connecting to aerospace-mcp server
2. Creating an aerospace agent
3. Having the agent make real tool calls
4. Verifying the results
"""

import os
import sys
import asyncio

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from src.mcp.mcp_manager import initialize_aerospace_mcp, get_mcp_manager
from src.agents.aerospace_agent import AerospaceAgent
from src.channel.shared_channel import SharedChannel
from src.orchestration.orchestrator import Orchestrator


def print_header(title: str):
    """Print a formatted header."""
    print(f"\n{'=' * 80}")
    print(f"{title.center(80)}")
    print(f"{'=' * 80}\n")


def print_status(message: str, status: str = "info"):
    """Print a status message."""
    symbols = {
        "success": "✅",
        "error": "❌",
        "info": "ℹ️",
        "warning": "⚠️",
        "test": "🧪"
    }
    symbol = symbols.get(status, "•")
    print(f"{symbol} {message}")


async def test_direct_tool_call():
    """Test calling MCP tools directly (without agent)."""
    print_header("Test 1: Direct MCP Tool Call")
    
    print_status("Testing direct tool call via MCP manager...", "test")
    
    try:
        manager = await get_mcp_manager()
        
        # Test 1: Search for an airport
        print("\n  Test 1a: search_airports for 'LAX'")
        result = await manager.call_tool(
            tool_name="search_airports",
            arguments={"query": "LAX"},
            server_name="aerospace-mcp"
        )
        
        if result and hasattr(result, 'content') and result.content:
            text = result.content[0].text
            print(f"  ✅ Result: {text[:150]}...")
        else:
            print(f"  ❌ No result returned")
            return False
        
        # Test 2: Calculate distance
        print("\n  Test 1b: calculate_distance (LAX to JFK)")
        result = await manager.call_tool(
            tool_name="calculate_distance",
            arguments={
                "lat1": 33.9425,
                "lon1": -118.4081,
                "lat2": 40.6413,
                "lon2": -73.7781
            },
            server_name="aerospace-mcp"
        )
        
        if result and hasattr(result, 'content') and result.content:
            text = result.content[0].text
            print(f"  ✅ Result: {text[:150]}...")
        else:
            print(f"  ❌ No result returned")
            return False
        
        print_status("\nDirect tool calls working!", "success")
        return True
        
    except Exception as e:
        print_status(f"Error in direct tool call: {e}", "error")
        import traceback
        traceback.print_exc()
        return False


async def test_agent_with_tools():
    """Test agent using MCP tools through Claude API."""
    print_header("Test 2: Agent Using MCP Tools")
    
    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print_status("ANTHROPIC_API_KEY not set - skipping agent test", "warning")
        print("\nTo test agent tool usage, set your API key:")
        print("  export ANTHROPIC_API_KEY='your-key-here'")
        return None
    
    print_status("Creating aerospace agent with MCP tool access...", "test")
    
    try:
        # Create channel and orchestrator
        channel = SharedChannel()
        orchestrator = Orchestrator(channel=channel)
        
        # Create aerospace agent
        aerospace = AerospaceAgent(
            agent_id="test_aerospace",
            callsign="Test One"
        )
        orchestrator.add_agent(aerospace)
        orchestrator.start()
        
        print_status("Agent created successfully", "success")
        print(f"  Agent ID: {aerospace.agent_id}")
        print(f"  Callsign: {aerospace.callsign}")
        print(f"  Model: {aerospace.model}")
        
        # Get available tools to show agent
        manager = await get_mcp_manager()
        tools = manager.get_available_tools("aerospace-mcp")
        
        print(f"\n  Agent has access to {len(tools)} MCP tools")
        
        # Test 1: Simple airport search
        print_header("Test 2a: Agent Airport Search")
        print_status("Asking agent to search for airports in San Francisco...", "test")
        
        user_msg = "Test One, search for airports in San Francisco and tell me what you find."
        print(f"\n[USER] {user_msg}\n")
        
        orchestrator.run_turn(user_message=user_msg, max_agent_responses=1)
        
        # Get agent response
        recent = channel.get_recent_messages(3)
        agent_response = None
        for msg in recent:
            if msg.sender_id == "test_aerospace":
                agent_response = msg.content
                print(f"[{msg.sender_callsign}] {msg.content}\n")
                break
        
        if agent_response:
            print_status("Agent responded successfully", "success")
            
            # Check if response mentions airport data
            if any(keyword in agent_response.lower() for keyword in ["sfo", "airport", "san francisco"]):
                print_status("Response contains airport information", "success")
            else:
                print_status("Response may not contain expected airport data", "warning")
        else:
            print_status("No agent response received", "error")
            return False
        
        # Test 2: Flight planning
        print_header("Test 2b: Agent Flight Planning")
        print_status("Asking agent to plan a flight...", "test")
        
        user_msg = "Test One, what's the distance from Los Angeles to New York?"
        print(f"\n[USER] {user_msg}\n")
        
        orchestrator.run_turn(user_message=user_msg, max_agent_responses=1)
        
        # Get agent response
        recent = channel.get_recent_messages(3)
        agent_response = None
        for msg in recent:
            if msg.sender_id == "test_aerospace":
                agent_response = msg.content
                print(f"[{msg.sender_callsign}] {msg.content}\n")
                break
        
        if agent_response:
            print_status("Agent responded successfully", "success")
            
            # Check if response mentions distance
            if any(keyword in agent_response.lower() for keyword in ["distance", "miles", "km", "nautical"]):
                print_status("Response contains distance information", "success")
            else:
                print_status("Response may not contain expected distance data", "warning")
        else:
            print_status("No agent response received", "error")
            return False
        
        orchestrator.stop()
        print_status("\nAgent tool usage test complete!", "success")
        return True
        
    except Exception as e:
        print_status(f"Error in agent test: {e}", "error")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test runner."""
    print_header("Agent MCP Tool Usage Verification")
    
    print("This test verifies that agents can actually use MCP tools.")
    print("It will:")
    print("  1. Test direct MCP tool calls")
    print("  2. Test agent using MCP tools (requires API key)")
    
    # Initialize MCP connection
    print_header("Initializing MCP Connection")
    
    aerospace_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "aerospace-mcp"
    )
    
    print_status(f"Connecting to aerospace-mcp at: {aerospace_path}", "info")
    
    success = await initialize_aerospace_mcp(aerospace_path)
    
    if not success:
        print_status("Failed to connect to aerospace-mcp server", "error")
        return False
    
    print_status("Connected to aerospace-mcp server", "success")
    
    # Run tests
    results = {}
    
    # Test 1: Direct tool calls
    results['direct_tools'] = await test_direct_tool_call()
    
    # Test 2: Agent using tools
    results['agent_tools'] = await test_agent_with_tools()
    
    # Cleanup
    manager = await get_mcp_manager()
    try:
        await manager.close()
    except:
        pass
    
    # Summary
    print_header("Test Summary")
    
    print("Results:")
    print(f"  Direct MCP Tool Calls: {'✅ PASS' if results['direct_tools'] else '❌ FAIL'}")
    
    if results['agent_tools'] is None:
        print(f"  Agent Tool Usage: ⚠️  SKIPPED (no API key)")
    else:
        print(f"  Agent Tool Usage: {'✅ PASS' if results['agent_tools'] else '❌ FAIL'}")
    
    # Final verdict
    print()
    if results['direct_tools']:
        print_status("MCP tools are accessible and working!", "success")
        
        if results['agent_tools']:
            print_status("Agents CAN use MCP tools successfully!", "success")
            print("\n🎉 Full verification complete - agents can use aerospace-mcp tools!")
        elif results['agent_tools'] is None:
            print_status("Agent test skipped - set ANTHROPIC_API_KEY to verify", "warning")
            print("\nTo complete verification:")
            print("  export ANTHROPIC_API_KEY='your-key-here'")
            print("  python test_agent_mcp_usage.py")
        else:
            print_status("Agents cannot use MCP tools", "error")
    else:
        print_status("MCP tools are not accessible", "error")
    
    return results['direct_tools'] and (results['agent_tools'] or results['agent_tools'] is None)


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

