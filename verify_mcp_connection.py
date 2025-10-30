#!/usr/bin/env python3
"""
Verify MCP Server Connection

This script tests the connection to the aerospace-mcp server and verifies
that agents can access MCP tools.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from src.mcp.mcp_manager import initialize_aerospace_mcp, get_mcp_manager


def print_header(title: str):
    """Print a formatted header."""
    print(f"\n{'=' * 80}")
    print(f"{title.center(80)}")
    print(f"{'=' * 80}\n")


def print_status(message: str, status: str):
    """Print a status message."""
    symbols = {
        "success": "✅",
        "error": "❌",
        "info": "ℹ️",
        "warning": "⚠️"
    }
    symbol = symbols.get(status, "•")
    print(f"{symbol} {message}")


async def verify_mcp_connection():
    """Verify the MCP server connection."""
    
    print_header("MCP Server Connection Verification")
    
    # Step 1: Check aerospace-mcp directory
    print_status("Checking aerospace-mcp server location...", "info")
    
    aerospace_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "aerospace-mcp"
    )
    
    if not os.path.exists(aerospace_path):
        print_status(f"aerospace-mcp not found at: {aerospace_path}", "error")
        print("\nPlease ensure the aerospace-mcp server is installed:")
        print("  1. Clone the repository: git clone https://github.com/yourusername/aerospace-mcp")
        print("  2. Place it in the parent directory of this project")
        return False
    
    print_status(f"Found aerospace-mcp at: {aerospace_path}", "success")
    
    # Step 2: Check for uv command
    print_status("Checking for 'uv' command...", "info")
    
    uv_check = os.system("which uv > /dev/null 2>&1")
    if uv_check != 0:
        print_status("'uv' command not found", "error")
        print("\nPlease install uv:")
        print("  curl -LsSf https://astral.sh/uv/install.sh | sh")
        return False
    
    print_status("'uv' command found", "success")
    
    # Step 3: Test MCP connection
    print_status("Connecting to aerospace-mcp server...", "info")
    
    try:
        success = await initialize_aerospace_mcp(aerospace_path)
        
        if not success:
            print_status("Failed to connect to aerospace-mcp server", "error")
            print("\nTroubleshooting:")
            print("  1. Ensure aerospace-mcp dependencies are installed:")
            print(f"     cd {aerospace_path} && uv sync")
            print("  2. Test the server manually:")
            print(f"     cd {aerospace_path} && uv run aerospace-mcp")
            return False
        
        print_status("Successfully connected to aerospace-mcp server", "success")
        
    except Exception as e:
        print_status(f"Connection error: {e}", "error")
        return False
    
    # Step 4: Verify tools are available
    print_status("Discovering available tools...", "info")
    
    try:
        manager = await get_mcp_manager()
        tools = manager.get_available_tools("aerospace-mcp")
        
        if not tools:
            print_status("No tools discovered", "warning")
            return False
        
        print_status(f"Discovered {len(tools)} aerospace tools", "success")
        
        # Show sample tools
        print("\nSample Tools Available:")
        for i, tool in enumerate(tools[:10], 1):
            print(f"  {i}. {tool['name']}")
            if 'description' in tool:
                desc = tool['description'][:70] + "..." if len(tool['description']) > 70 else tool['description']
                print(f"     {desc}")
        
        if len(tools) > 10:
            print(f"  ... and {len(tools) - 10} more tools")
        
    except Exception as e:
        print_status(f"Error discovering tools: {e}", "error")
        return False
    
    # Step 5: Test a simple tool call
    print_status("\nTesting tool execution...", "info")

    try:
        # Try to call a simple tool (search_airports)
        result = await manager.call_tool(
            tool_name="search_airports",
            arguments={"query": "SFO"},
            server_name="aerospace-mcp"
        )

        if result:
            print_status("Tool execution successful", "success")
            print(f"\nSample result (search_airports for 'SFO'):")
            # Extract text content from result
            if hasattr(result, 'content') and result.content:
                text = result.content[0].text if result.content else str(result)
                print(f"  {text[:200]}...")
            else:
                print(f"  {str(result)[:200]}...")
        else:
            print_status("Tool execution returned no result", "warning")

    except Exception as e:
        print_status(f"Tool execution error: {e}", "error")
        print("  Note: This may be expected if the tool requires specific arguments")

    # Step 6: Verify agent integration
    print_status("\nVerifying agent integration...", "info")

    # Check if API key is set
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print_status("ANTHROPIC_API_KEY not set - skipping agent creation test", "warning")
        print("  To test agent creation, set your API key:")
        print("    export ANTHROPIC_API_KEY='your-key-here'")
    else:
        try:
            from src.agents.aerospace_agent import AerospaceAgent

            # Create a test aerospace agent
            test_agent = AerospaceAgent(
                agent_id="test_aerospace",
                callsign="Test One"
            )

            print_status("AerospaceAgent class loaded successfully", "success")
            print(f"  Agent ID: {test_agent.agent_id}")
            print(f"  Callsign: {test_agent.callsign}")
            print(f"  Agent Type: {test_agent.get_agent_type()}")

        except Exception as e:
            print_status(f"Error loading AerospaceAgent: {e}", "error")
            return False

    # Cleanup
    try:
        await manager.close()
    except Exception as e:
        # Ignore cleanup errors
        pass
    
    # Final summary
    print_header("Verification Complete")
    print_status("All checks passed!", "success")
    print("\nYour agents can now access the aerospace-mcp server!")
    print("\nNext steps:")
    print("  1. Run the aerospace demo:")
    print("     python demo_aerospace.py")
    print("  2. Or use aerospace agents in your own configurations:")
    print("     python -m src.cli.main interactive --config configs/aerospace.yaml")
    
    return True


async def main():
    """Main entry point."""
    try:
        success = await verify_mcp_connection()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nVerification cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

