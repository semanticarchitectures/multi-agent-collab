#!/usr/bin/env python3
"""
Test Aircraft Simulator MCP Integration

This script verifies that the aircraft-sim-mcp server can be connected
and that its tools are available to agents.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.mcp.mcp_manager import get_mcp_manager, initialize_aircraft_sim_mcp


async def test_aircraft_sim_connection():
    """Test connection to aircraft simulator MCP server."""
    
    print("=" * 80)
    print("AIRCRAFT SIMULATOR MCP INTEGRATION TEST")
    print("=" * 80)
    print()
    
    # Determine path to aircraft-sim-mcp
    parent_dir = Path(__file__).parent.parent
    aircraft_sim_path = str(parent_dir / "aircraft-sim-mcp")
    
    print(f"📁 Aircraft Simulator Path: {aircraft_sim_path}")
    
    if not Path(aircraft_sim_path).exists():
        print(f"❌ ERROR: aircraft-sim-mcp not found at {aircraft_sim_path}")
        return False
    
    print(f"✓ Path exists")
    print()
    
    # Initialize connection
    print("🔧 Connecting to aircraft-sim-mcp server...")
    success = await initialize_aircraft_sim_mcp(aircraft_sim_path)
    
    if not success:
        print("❌ Failed to connect to aircraft-sim-mcp server")
        print()
        print("Troubleshooting steps:")
        print("1. Check if JSBSim is installed:")
        print(f"   cd {aircraft_sim_path}")
        print("   source venv/bin/activate")
        print("   python -c 'import jsbsim'")
        print()
        print("2. Try running the server manually:")
        print(f"   cd {aircraft_sim_path}")
        print("   source venv/bin/activate")
        print("   PYTHONPATH=src python -m flight_simulator_mcp.server")
        return False
    
    print("✅ Successfully connected to aircraft-sim-mcp!")
    print()
    
    # Get manager and list tools
    manager = await get_mcp_manager()
    
    print("📋 Available Tools:")
    print()
    
    tools = manager.get_available_tools("aircraft-sim-mcp")
    
    if not tools:
        print("⚠️  No tools found (this might indicate a connection issue)")
        return False
    
    print(f"Found {len(tools)} tools:")
    print()
    
    # Categorize tools
    control_tools = []
    monitoring_tools = []
    
    for tool in tools:
        tool_name = tool.get('name', 'unknown')
        tool_desc = tool.get('description', 'No description')
        
        if any(keyword in tool_name for keyword in ['set_', 'advance', 'reset']):
            control_tools.append((tool_name, tool_desc))
        else:
            monitoring_tools.append((tool_name, tool_desc))
    
    print("🎮 CONTROL TOOLS (Pilot/Co-pilot only):")
    for name, desc in control_tools:
        print(f"  • {name}")
        print(f"    {desc[:80]}...")
    
    print()
    print("📊 MONITORING TOOLS (All crew members):")
    for name, desc in monitoring_tools:
        print(f"  • {name}")
        print(f"    {desc[:80]}...")
    
    print()
    print("=" * 80)
    print("✅ INTEGRATION TEST PASSED!")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Run: python run_airdrop_mission.py")
    print("2. Ask agents to initialize the simulator:")
    print("   'Reset the simulator with a C-130 at 10,000 ft, heading 270, 200 knots'")
    print("3. Ask agents to monitor aircraft state:")
    print("   'What is our current position and altitude?'")
    print("4. Ask pilots to control the aircraft:")
    print("   'Set throttle to 75% on all engines'")
    print()
    
    # Cleanup
    await manager.cleanup()
    
    return True


async def main():
    """Main function."""
    try:
        success = await test_aircraft_sim_connection()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

