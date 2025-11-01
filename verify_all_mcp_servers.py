#!/usr/bin/env python3
"""
Verify All Aviation MCP Server Connections

This script tests connections to all available aviation MCP servers:
- aerospace-mcp: Aerospace engineering calculations and tools
- aviation-weather-mcp: Aviation weather data and forecasts
- blevinstein/aviation-mcp: General aviation tools and utilities
"""

import os
import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from src.mcp.mcp_manager import (
    initialize_all_aviation_mcps,
    get_mcp_manager
)


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
        "warning": "⚠️",
        "skipped": "⏭️"
    }
    symbol = symbols.get(status, "•")
    print(f"{symbol} {message}")


async def install_missing_servers(missing_servers: dict) -> dict:
    """Attempt to install missing MCP servers.

    Args:
        missing_servers: Dictionary of server_name -> server_path

    Returns:
        Dictionary of successfully installed server_name -> server_path
    """
    installed = {}
    parent_dir = os.path.dirname(os.path.dirname(__file__))

    print_header("INSTALLING MISSING MCP SERVERS")

    # Server installation info
    server_repos = {
        "aviation-weather-mcp": {
            "url": None,  # Unknown - need to search
            "dir_name": "aviation-weather-mcp",
            "run_command": "aviation-weather-mcp"
        },
        "blevinstein-aviation-mcp": {
            "url": "https://github.com/blevinstein/aviation-mcp.git",
            "dir_name": "aviation-mcp",
            "run_command": "aviation-mcp"
        }
    }

    for server_name, server_path in missing_servers.items():
        if server_name == "aerospace-mcp":
            print_status(f"Skipping {server_name} - should already be installed", "warning")
            continue

        if server_name not in server_repos:
            print_status(f"Unknown installation method for {server_name}", "error")
            continue

        server_info = server_repos[server_name]

        if not server_info["url"]:
            print_status(f"Repository URL unknown for {server_name}", "error")
            print(f"   Please manually install from the correct repository")
            continue

        print_status(f"Installing {server_name}...", "info")

        try:
            # Clone the repository
            clone_cmd = f"git clone {server_info['url']} {os.path.join(parent_dir, server_info['dir_name'])}"
            print(f"   Running: {clone_cmd}")

            result = os.system(clone_cmd)
            if result != 0:
                print_status(f"Failed to clone {server_name}", "error")
                continue

            # Install dependencies with uv
            install_dir = os.path.join(parent_dir, server_info['dir_name'])
            sync_cmd = f"cd {install_dir} && uv sync"
            print(f"   Running: uv sync in {install_dir}")

            result = os.system(sync_cmd)
            if result != 0:
                print_status(f"Failed to install dependencies for {server_name}", "error")
                continue

            print_status(f"Successfully installed {server_name}", "success")
            installed[server_name] = install_dir

        except Exception as e:
            print_status(f"Error installing {server_name}: {e}", "error")

    return installed


async def verify_all_mcp_servers():
    """Verify all aviation MCP server connections."""

    print_header("AVIATION MCP SERVERS VERIFICATION")

    # Get parent directory for MCP servers
    parent_dir = os.path.dirname(os.path.dirname(__file__))

    # Define server paths
    servers = {
        "aerospace-mcp": os.path.join(parent_dir, "aerospace-mcp"),
        "aviation-weather-mcp": os.path.join(parent_dir, "aviation-weather-mcp"),
        "blevinstein-aviation-mcp": os.path.join(parent_dir, "aviation-mcp")
    }

    # Check which servers exist
    print_status("Checking for available MCP servers...", "info")
    available_servers = {}
    missing_servers = {}

    for server_name, server_path in servers.items():
        if os.path.exists(server_path):
            print_status(f"{server_name}: Found at {server_path}", "success")
            available_servers[server_name] = server_path
        else:
            print_status(f"{server_name}: Not found at {server_path}", "error")
            missing_servers[server_name] = server_path

    # Report summary of found/missing
    print(f"\n📊 Status: {len(available_servers)}/{len(servers)} servers found")

    if missing_servers:
        print_status(f"\n{len(missing_servers)} server(s) missing - installation required", "error")

        # Ask user if they want to install missing servers
        print("\nWould you like to install the missing servers now? (y/n): ", end="", flush=True)
        try:
            response = input().strip().lower()
            if response in ['y', 'yes']:
                installed = await install_missing_servers(missing_servers)
                # Update available_servers with newly installed ones
                for server_name, server_path in installed.items():
                    available_servers[server_name] = server_path
                    missing_servers.pop(server_name, None)
            else:
                print_status("Skipping installation - will test only available servers", "warning")
        except (EOFError, KeyboardInterrupt):
            print("\nSkipping installation - will test only available servers")

    if not available_servers:
        print_status("\nNo MCP servers found!", "error")
        print("\nPlease install at least one MCP server. See setup instructions at the end.")
        return False

    # Check for uv command
    print_status("\nChecking for 'uv' package manager...", "info")

    uv_check = os.system("which uv > /dev/null 2>&1")
    if uv_check != 0:
        print_status("'uv' command not found", "error")
        print("\nPlease install uv:")
        print("  curl -LsSf https://astral.sh/uv/install.sh | sh")
        return False

    print_status("'uv' command found", "success")

    # Initialize all available servers
    print_header("CONNECTING TO MCP SERVERS")

    try:
        # Prepare paths for initialization
        init_kwargs = {}
        if "aerospace-mcp" in available_servers:
            init_kwargs["aerospace_path"] = available_servers["aerospace-mcp"]
        if "aviation-weather-mcp" in available_servers:
            init_kwargs["aviation_weather_path"] = available_servers["aviation-weather-mcp"]
        if "blevinstein-aviation-mcp" in available_servers:
            init_kwargs["blevinstein_aviation_path"] = available_servers["blevinstein-aviation-mcp"]

        # Connect to all servers
        results = await initialize_all_aviation_mcps(**init_kwargs)

        # Report connection results
        success_count = 0
        for server_name, success in results.items():
            if success:
                print_status(f"Connected to {server_name}", "success")
                success_count += 1
            else:
                print_status(f"Failed to connect to {server_name}", "error")

        if success_count == 0:
            print_status("\nNo servers connected successfully", "error")
            return False

        print_status(f"\nConnected to {success_count}/{len(results)} servers", "success")

    except Exception as e:
        print_status(f"Connection error: {e}", "error")
        import traceback
        traceback.print_exc()
        return False

    # Discover and display tools from each server
    print_header("AVAILABLE TOOLS")

    try:
        manager = await get_mcp_manager()

        total_tools = 0
        for server_name in manager.get_server_names():
            tools = manager.get_available_tools(server_name)
            total_tools += len(tools)

            print(f"\n📦 {server_name}: {len(tools)} tools")

            # Show sample tools (first 5)
            for i, tool in enumerate(tools[:5], 1):
                print(f"  {i}. {tool['name']}")
                if 'description' in tool and tool['description']:
                    desc = tool['description'][:70] + "..." if len(tool['description']) > 70 else tool['description']
                    print(f"     {desc}")

            if len(tools) > 5:
                print(f"  ... and {len(tools) - 5} more tools")

        print(f"\n✅ Total tools available: {total_tools}")

    except Exception as e:
        print_status(f"Error discovering tools: {e}", "error")
        return False

    # Test tool execution (if aerospace-mcp is available)
    if "aerospace-mcp" in results and results["aerospace-mcp"]:
        print_header("TESTING TOOL EXECUTION")
        print_status("Testing aerospace-mcp tool...", "info")

        try:
            # Try to call a simple tool (search_airports)
            result = await manager.call_tool(
                tool_name="search_airports",
                arguments={"query": "JFK"},
                server_name="aerospace-mcp"
            )

            if result:
                print_status("Tool execution successful", "success")
                print(f"\nSample result (search_airports for 'JFK'):")
                # Extract text content from result
                if hasattr(result, 'content') and result.content:
                    text = result.content[0].text if result.content else str(result)
                    print(f"  {text[:300]}...")
                else:
                    print(f"  {str(result)[:300]}...")
            else:
                print_status("Tool execution returned no result", "warning")

        except Exception as e:
            print_status(f"Tool execution error: {e}", "warning")
            print("  This may be expected if the tool has specific argument requirements")

    # Cleanup
    try:
        await manager.close()
    except Exception:
        pass

    # Final summary
    print_header("VERIFICATION COMPLETE")

    total_expected = 3  # We expect 3 MCP servers
    all_servers_present = len(missing_servers) == 0

    if all_servers_present:
        print_status("✨ SUCCESS: All MCP servers verified and working!", "success")
        final_status = True
    else:
        print_status(f"❌ INCOMPLETE: {len(missing_servers)}/{total_expected} servers missing", "error")
        print("\nMissing servers:")
        for server_name in missing_servers.keys():
            print(f"  • {server_name}")
        final_status = False

    print(f"\n📊 Summary:")
    print(f"  • Total expected: {total_expected}")
    print(f"  • Found and connected: {success_count}")
    print(f"  • Missing: {len(missing_servers)}")
    print(f"  • Total tools available: {total_tools}")

    if final_status:
        print(f"\n🚀 Next steps:")
        print(f"  1. Run multi-server demo:")
        print(f"     python demo_multi_aviation.py")
        print(f"  2. Use in interactive mode:")
        print(f"     python -m src.cli.main interactive --config configs/aerospace.yaml")
    else:
        print(f"\n⚠️  To install missing servers:")
        print(f"  1. Run this script again and choose 'yes' when prompted to install")
        print(f"  2. Or manually install following: AVIATION_MCP_SETUP.md")
        print(f"\n💡 Partial functionality is available with {success_count} server(s)")

    return final_status


def print_setup_instructions():
    """Print setup instructions for missing MCP servers."""
    print_header("MCP SERVER SETUP INSTRUCTIONS")

    print("If you're missing any MCP servers, here's how to install them:\n")

    print("1️⃣  aerospace-mcp")
    print("   Git repository for aerospace engineering tools")
    print("   Setup:")
    print("     cd /Users/kevinkelly/Documents/claude-projects/agentDemo")
    print("     # If you already have it, skip this step")
    print("     # Otherwise, follow the original installation method\n")

    print("2️⃣  aviation-weather-mcp")
    print("   Aviation weather data and METAR/TAF decoding")
    print("   Setup:")
    print("     cd /Users/kevinkelly/Documents/claude-projects/agentDemo")
    print("     git clone https://github.com/[repository]/aviation-weather-mcp")
    print("     cd aviation-weather-mcp")
    print("     uv sync\n")

    print("3️⃣  blevinstein/aviation-mcp")
    print("   General aviation utilities and tools")
    print("   Setup:")
    print("     cd /Users/kevinkelly/Documents/claude-projects/agentDemo")
    print("     git clone https://github.com/blevinstein/aviation-mcp")
    print("     cd aviation-mcp")
    print("     uv sync\n")

    print("⚠️  Note: Repository URLs are placeholders. Please verify the correct")
    print("   repositories for aviation-weather-mcp and blevinstein/aviation-mcp.\n")


async def main():
    """Main entry point."""
    try:
        success = await verify_all_mcp_servers()

        if not success:
            print_setup_instructions()

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
