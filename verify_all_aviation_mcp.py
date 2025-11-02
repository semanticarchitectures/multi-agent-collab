#!/usr/bin/env python3
"""
Verify All Aviation MCP Servers

This script tests connections to all available aviation MCP servers:
- aerospace-mcp (Python/uv)
- aviation-mcp (Node.js/npx) - Blevinstein's aviation data server

It verifies that agents can access tools from all connected servers.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from src.mcp.mcp_manager import get_mcp_manager


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


async def verify_all_servers():
    """Verify all aviation MCP server connections."""
    
    print_header("Aviation MCP Servers Verification")
    
    # Define servers to check
    base_path = Path(__file__).parent.parent
    servers = {
        "aerospace-mcp": {
            "path": base_path / "aerospace-mcp",
            "command": "uv",
            "args_template": ["--directory", "{path}", "run", "aerospace-mcp"],
            "description": "Aerospace engineering calculations and flight planning"
        },
        "aviation-mcp": {
            "path": base_path / "aviation-mcp",
            "command": "npx",
            "args_template": ["-y", "aviation-mcp"],
            "description": "FAA aviation data (weather, NOTAMs, charts)",
            "env": {
                "FAA_CLIENT_ID": os.getenv("FAA_CLIENT_ID", ""),
                "FAA_CLIENT_SECRET": os.getenv("FAA_CLIENT_SECRET", ""),
                "API_NINJAS_KEY": os.getenv("API_NINJAS_KEY", "")
            }
        },
        "aviation-weather-mcp": {
            "path": base_path / "aviation-weather-mcp",
            "command": "python",
            "args_template": ["-m", "aviation_weather_mcp.server"],
            "description": "Aviation weather data from aviationweather.gov (METAR, TAF, PIREP, etc.)"
        }
    }
    
    # Check which servers exist
    print_status("Checking for available MCP servers...", "info")
    available_servers = {}
    missing_servers = []
    
    for server_name, server_info in servers.items():
        server_path = server_info["path"]
        if server_path.exists():
            print_status(f"{server_name}: Found at {server_path}", "success")
            print(f"  Description: {server_info['description']}")
            available_servers[server_name] = server_info
        else:
            print_status(f"{server_name}: Not found at {server_path}", "error")
            missing_servers.append(server_name)
    
    print(f"\n📊 Status: {len(available_servers)}/{len(servers)} servers found")
    
    if not available_servers:
        print_status("\nNo MCP servers found!", "error")
        print("\nPlease install at least one server:")
        print("  aerospace-mcp: https://github.com/yourusername/aerospace-mcp")
        print("  aviation-mcp: npm install -g aviation-mcp")
        return False
    
    # Connect to available servers
    print_header("Connecting to MCP Servers")
    
    manager = await get_mcp_manager()
    connection_results = {}
    
    for server_name, server_info in available_servers.items():
        print_status(f"Connecting to {server_name}...", "info")
        
        try:
            # Prepare arguments
            args = []
            for arg in server_info["args_template"]:
                if "{path}" in arg:
                    args.append(str(server_info["path"]))
                else:
                    args.append(arg)
            
            # Get environment variables
            env = server_info.get("env", None)
            
            # Connect
            success = await manager.connect_server(
                server_name=server_name,
                command=server_info["command"],
                args=args,
                env=env
            )
            
            connection_results[server_name] = success
            
            if success:
                print_status(f"Connected to {server_name}", "success")
            else:
                print_status(f"Failed to connect to {server_name}", "error")
                
        except Exception as e:
            print_status(f"Error connecting to {server_name}: {e}", "error")
            connection_results[server_name] = False
    
    # Count successful connections
    successful_connections = sum(1 for success in connection_results.values() if success)
    
    if successful_connections == 0:
        print_status("\nNo servers connected successfully!", "error")
        return False
    
    print(f"\n✅ Successfully connected to {successful_connections}/{len(available_servers)} servers")
    
    # Discover tools from all servers
    print_header("Discovering Tools")
    
    all_tools = {}
    total_tools = 0
    
    for server_name in connection_results:
        if connection_results[server_name]:
            print_status(f"Discovering tools from {server_name}...", "info")
            
            try:
                tools = manager.get_available_tools(server_name)
                all_tools[server_name] = tools
                total_tools += len(tools)
                
                print_status(f"Found {len(tools)} tools from {server_name}", "success")
                
                # Show sample tools
                if tools:
                    print(f"\n  Sample tools from {server_name}:")
                    for i, tool in enumerate(tools[:5], 1):
                        print(f"    {i}. {tool['name']}")
                        if 'description' in tool:
                            desc = tool['description'][:60] + "..." if len(tool['description']) > 60 else tool['description']
                            print(f"       {desc}")
                    
                    if len(tools) > 5:
                        print(f"    ... and {len(tools) - 5} more tools")
                    print()
                    
            except Exception as e:
                print_status(f"Error discovering tools from {server_name}: {e}", "error")
    
    print(f"📊 Total tools available: {total_tools} tools from {successful_connections} server(s)")
    
    # Test tool execution from each server
    print_header("Testing Tool Execution")
    
    test_results = {}
    
    # Test aerospace-mcp
    if "aerospace-mcp" in connection_results and connection_results["aerospace-mcp"]:
        print_status("Testing aerospace-mcp tool: search_airports", "info")
        try:
            result = await manager.call_tool(
                server_name="aerospace-mcp",
                tool_name="search_airports",
                arguments={"query": "SFO"}
            )
            
            if result and hasattr(result, 'content') and result.content:
                response_text = result.content[0].text
                print_status("aerospace-mcp tool execution successful", "success")
                print(f"  Result preview: {response_text[:100]}...")
                test_results["aerospace-mcp"] = True
            else:
                print_status("aerospace-mcp tool returned no result", "warning")
                test_results["aerospace-mcp"] = False
                
        except Exception as e:
            print_status(f"aerospace-mcp tool execution error: {e}", "error")
            test_results["aerospace-mcp"] = False
    
    # Test aviation-mcp
    if "aviation-mcp" in connection_results and connection_results["aviation-mcp"]:
        print_status("Testing aviation-mcp tool: get_metar", "info")
        try:
            # First, let's see what tools are available
            aviation_tools = all_tools.get("aviation-mcp", [])
            if aviation_tools:
                # Try to find a weather-related tool
                weather_tool = None
                for tool in aviation_tools:
                    if "metar" in tool['name'].lower() or "weather" in tool['name'].lower():
                        weather_tool = tool
                        break

                if weather_tool:
                    print(f"  Found tool: {weather_tool['name']}")
                    # Try calling it with a simple airport code
                    result = await manager.call_tool(
                        server_name="aviation-mcp",
                        tool_name=weather_tool['name'],
                        arguments={"ids": "KSFO"}  # Correct parameter name
                    )

                    if result and hasattr(result, 'content') and result.content:
                        response_text = result.content[0].text
                        print_status("aviation-mcp tool execution successful", "success")
                        print(f"  Result preview: {response_text[:100]}...")
                        test_results["aviation-mcp"] = True
                    else:
                        print_status("aviation-mcp tool returned no result", "warning")
                        test_results["aviation-mcp"] = False
                else:
                    print_status("No weather tool found in aviation-mcp", "warning")
                    test_results["aviation-mcp"] = False
            else:
                print_status("No tools discovered from aviation-mcp", "warning")
                test_results["aviation-mcp"] = False

        except Exception as e:
            print_status(f"aviation-mcp tool execution error: {e}", "error")
            print(f"  This may be expected if API keys are not configured")
            test_results["aviation-mcp"] = False

    # Test aviation-weather-mcp
    if "aviation-weather-mcp" in connection_results and connection_results["aviation-weather-mcp"]:
        print_status("Testing aviation-weather-mcp tool: get_metar", "info")
        try:
            result = await manager.call_tool(
                server_name="aviation-weather-mcp",
                tool_name="get_metar",
                arguments={"ids": "KSFO"}
            )

            if result and hasattr(result, 'content') and result.content:
                response_text = result.content[0].text
                print_status("aviation-weather-mcp tool execution successful", "success")
                print(f"  Result preview: {response_text[:150]}...")
                test_results["aviation-weather-mcp"] = True
            else:
                print_status("aviation-weather-mcp tool returned no result", "warning")
                test_results["aviation-weather-mcp"] = False

        except Exception as e:
            print_status(f"aviation-weather-mcp tool execution error: {e}", "error")
            test_results["aviation-weather-mcp"] = False
    
    # Final summary
    print_header("Verification Summary")
    
    print("📊 Connection Status:")
    for server_name, success in connection_results.items():
        status = "success" if success else "error"
        print_status(f"{server_name}: {'Connected' if success else 'Failed'}", status)
    
    print(f"\n📚 Tools Discovered:")
    for server_name, tools in all_tools.items():
        print(f"  • {server_name}: {len(tools)} tools")
    
    print(f"\n🧪 Tool Execution Tests:")
    for server_name, success in test_results.items():
        status = "success" if success else "warning"
        print_status(f"{server_name}: {'Passed' if success else 'Failed/Skipped'}", status)
    
    # Overall status
    all_passed = (
        successful_connections > 0 and
        total_tools > 0
    )
    
    if all_passed:
        print_header("✅ Verification Complete")
        print("Your agents can now access tools from the following servers:")
        for server_name in connection_results:
            if connection_results[server_name]:
                print(f"  ✅ {server_name}")
        
        print("\n🚀 Next Steps:")
        print("  1. Run the multi-server demo:")
        print("     python demo_agent_airport_search.py")
        print("  2. Use in interactive mode:")
        print("     python -m src.cli.main interactive --config configs/aerospace.yaml")
        
        if missing_servers:
            print(f"\n💡 Optional: Install additional servers for more functionality:")
            for server in missing_servers:
                print(f"  • {server}")
    else:
        print_header("⚠️  Verification Incomplete")
        print("Some issues were detected. Please review the errors above.")
    
    # Cleanup
    try:
        await manager.close()
    except Exception:
        pass
    
    return all_passed


async def main():
    """Main entry point."""
    try:
        success = await verify_all_servers()
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

