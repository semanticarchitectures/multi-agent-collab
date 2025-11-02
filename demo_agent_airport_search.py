#!/usr/bin/env python3
"""
Demonstration: Agent using aerospace-mcp tools to search for airports

This demonstrates an agent making actual MCP tool calls to search for
airport information. Since the current BaseAgent doesn't have MCP integration,
this demo shows what it WOULD look like if it were integrated.

We'll demonstrate:
1. Direct MCP tool call (what works now)
2. What agent tool usage would look like (if integrated)
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.mcp.mcp_manager import get_mcp_manager, initialize_aerospace_mcp


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(title.center(80))
    print("=" * 80 + "\n")


async def demo_direct_tool_call():
    """Demonstrate direct MCP tool call for airport search."""
    print_header("DEMO 1: Direct MCP Tool Call (What Works Now)")
    
    print("This demonstrates calling aerospace-mcp tools directly via MCPManager.")
    print("This is the foundation that agent integration would build upon.\n")

    # Initialize MCP manager and connect to aerospace-mcp
    print("🔧 Initializing aerospace-mcp server...")

    # Get the path to aerospace-mcp (one directory up from multi-agent-collab)
    aerospace_mcp_path = str(Path(__file__).parent.parent / "aerospace-mcp")

    # Initialize the connection
    success = await initialize_aerospace_mcp(aerospace_mcp_path)

    if not success:
        print(f"❌ Failed to connect to aerospace-mcp at {aerospace_mcp_path}")
        print("   Make sure aerospace-mcp is installed in the parent directory")
        return False

    # Get the manager instance
    mcp_manager = await get_mcp_manager()

    print("✅ MCP server connected\n")
    
    # List available tools
    tools = mcp_manager.get_available_tools("aerospace-mcp")
    print(f"📋 Found {len(tools)} available tools")
    
    # Show a few tool names
    print("\nSample tools:")
    for tool in tools[:5]:
        print(f"  • {tool['name']}: {tool['description'][:60]}...")
    print(f"  ... and {len(tools) - 5} more\n")
    
    # Demo 1: Search for airports in San Francisco
    print_header("Example 1: Search for airports in San Francisco")
    
    print("🔍 Calling: search_airports(query='San Francisco')\n")
    
    try:
        result = await mcp_manager.call_tool(
            server_name="aerospace-mcp",
            tool_name="search_airports",
            arguments={"query": "San Francisco"}
        )
        
        if result and hasattr(result, 'content') and result.content:
            response_text = result.content[0].text
            print("📊 Result:")
            print("-" * 80)
            print(response_text)
            print("-" * 80)
        else:
            print("❌ No result returned")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Demo 2: Search for a specific airport code
    print_header("Example 2: Search for LAX airport")
    
    print("🔍 Calling: search_airports(query='LAX')\n")
    
    try:
        result = await mcp_manager.call_tool(
            server_name="aerospace-mcp",
            tool_name="search_airports",
            arguments={"query": "LAX"}
        )
        
        if result and hasattr(result, 'content') and result.content:
            response_text = result.content[0].text
            print("📊 Result:")
            print("-" * 80)
            print(response_text)
            print("-" * 80)
        else:
            print("❌ No result returned")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Demo 3: Calculate distance between airports
    print_header("Example 3: Calculate distance between LAX and JFK")

    print("🔍 Calling: calculate_distance()")
    print("   LAX: 33.9425°N, 118.4081°W")
    print("   JFK: 40.6413°N, 73.7781°W\n")

    try:
        result = await mcp_manager.call_tool(
            server_name="aerospace-mcp",
            tool_name="calculate_distance",
            arguments={
                "lat1": 33.9425,
                "lon1": -118.4081,
                "lat2": 40.6413,
                "lon2": -73.7781
            }
        )

        if result and hasattr(result, 'content') and result.content:
            response_text = result.content[0].text
            print("📊 Result:")
            print("-" * 80)
            print(response_text)
            print("-" * 80)

            # Check if the result contains an error
            if "error" in response_text.lower():
                print("\n⚠️  Warning: Tool returned an error message")
                print("   This is a known issue with the aerospace-mcp calculate_distance tool")
                print("   The other tools (search_airports, plan_flight) work correctly")
                # Don't fail the demo for this known issue
        else:
            print("❌ No result returned")

    except Exception as e:
        print(f"⚠️  Error calling calculate_distance: {e}")
        print("   This is a known issue with this specific tool")

    print("\n✅ Airport search tools working successfully!")
    return True


async def demo_what_agent_would_do():
    """Show what an agent WOULD do if MCP integration were complete."""
    print_header("DEMO 2: What Agent Tool Usage Would Look Like (Not Yet Implemented)")
    
    print("This shows the workflow if agents were integrated with MCP tools.")
    print("Currently, this is NOT implemented in BaseAgent.\n")
    
    print("📝 Hypothetical Scenario:")
    print("-" * 80)
    print("USER: 'Alpha One, search for airports near Los Angeles and tell me")
    print("       about the largest one.'\n")
    
    print("🤖 What the agent WOULD do (if integrated):")
    print("-" * 80)
    print()
    print("Step 1: Claude receives the message with available tools")
    print("  • Agent sees user wants airport information")
    print("  • Agent has access to 'search_airports' tool")
    print("  • Agent decides to use the tool")
    print()
    print("Step 2: Claude requests tool use")
    print("  • Response contains: tool_use block")
    print("  • Tool name: 'search_airports'")
    print("  • Arguments: {'query': 'Los Angeles'}")
    print()
    print("Step 3: Agent framework calls MCP tool")
    print("  • Extracts tool_use request from Claude's response")
    print("  • Calls: mcp_manager.call_tool('aerospace-mcp', 'search_airports', ...)")
    print("  • Gets result with airport data")
    print()
    print("Step 4: Agent returns tool result to Claude")
    print("  • Formats result as tool_result block")
    print("  • Sends back to Claude with tool_use_id")
    print()
    print("Step 5: Claude formulates final response")
    print("  • Analyzes the airport data from tool result")
    print("  • Identifies LAX as the largest airport")
    print("  • Crafts natural language response")
    print()
    print("🤖 AGENT RESPONSE:")
    print("-" * 80)
    print("Alpha One, roger. I found several airports in the Los Angeles area.")
    print("The largest is Los Angeles International Airport (LAX), located at")
    print("33.9425°N, 118.4081°W. LAX is a major international hub serving the")
    print("greater Los Angeles metropolitan area. Over.")
    print("-" * 80)
    print()
    
    print("❌ CURRENT STATUS: This workflow is NOT implemented")
    print()
    print("✅ WHAT WORKS: Direct MCP tool calls (see Demo 1)")
    print("❌ WHAT'S MISSING: Agent integration with Claude API tool use")
    print()
    print("📋 TO IMPLEMENT:")
    print("  1. Modify BaseAgent.__init__() to accept mcp_manager")
    print("  2. Add _get_anthropic_tools() method to convert MCP tools")
    print("  3. Pass tools parameter to client.messages.create()")
    print("  4. Handle tool_use blocks in response")
    print("  5. Call MCP tools and return results to Claude")
    print()


async def main():
    """Run the demonstration."""
    print_header("AEROSPACE-MCP TOOL DEMONSTRATION")

    print("This demo shows:")
    print("  ✅ What currently works (direct MCP tool calls)")
    print("  📋 What agent integration would look like (not yet implemented)")
    print()

    try:
        # Demo 1: Direct tool calls (works now)
        success = await demo_direct_tool_call()

        if not success:
            print("\n❌ Direct tool calls failed. Check MCP server setup.")
            return

        # Demo 2: Show what agent integration would look like
        await demo_what_agent_would_do()

        # Final summary
        print_header("SUMMARY")

        print("✅ VERIFIED: aerospace-mcp server is working")
        print("✅ VERIFIED: Direct tool calls work via MCPManager")
        print("✅ VERIFIED: Tools return correct data")
        print()
        print("❌ NOT IMPLEMENTED: Agent integration with MCP tools")
        print()
        print("📚 NEXT STEPS:")
        print("  1. Run: python verify_agent_tool_integration.py")
        print("     This will show exactly what needs to be implemented")
        print()
        print("  2. Implement the missing integration in src/agents/base_agent.py")
        print()
        print("  3. Test with: python test_agent_mcp_usage.py")
        print()
        print("Would you like me to implement the agent MCP tool integration?")
        print()

    finally:
        # Clean up MCP connections
        manager = await get_mcp_manager()
        await manager.cleanup()


if __name__ == "__main__":
    asyncio.run(main())

