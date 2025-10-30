#!/usr/bin/env python3
"""
Simple verification script to check if agents can use MCP tools.

This script performs a code inspection to determine if the agent
integration with MCP tools is implemented.
"""

import inspect
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.base_agent import BaseAgent


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(title.center(80))
    print("=" * 80 + "\n")


def check_agent_tool_integration():
    """Check if BaseAgent is integrated with MCP tools."""
    print_header("AGENT MCP TOOL INTEGRATION VERIFICATION")
    
    print("Inspecting BaseAgent class for MCP tool integration...\n")
    
    # Check 1: Does __init__ accept mcp_manager?
    print("CHECK 1: Does BaseAgent.__init__() accept mcp_manager parameter?")
    init_source = inspect.getsource(BaseAgent.__init__)
    if "mcp_manager" in init_source:
        print("  ✅ PASS: __init__() has mcp_manager parameter")
        has_mcp_param = True
    else:
        print("  ❌ FAIL: __init__() does NOT have mcp_manager parameter")
        has_mcp_param = False
    
    # Check 2: Does generate_response pass tools to Claude API?
    print("\nCHECK 2: Does generate_response() pass tools to Claude API?")
    gen_source = inspect.getsource(BaseAgent.generate_response)
    if "tools=" in gen_source:
        print("  ✅ PASS: generate_response() passes 'tools' parameter")
        has_tools_param = True
    else:
        print("  ❌ FAIL: generate_response() does NOT pass 'tools' parameter")
        has_tools_param = False
    
    # Check 3: Does it handle tool_use responses?
    print("\nCHECK 3: Does generate_response() handle tool_use responses?")
    if "tool_use" in gen_source:
        print("  ✅ PASS: generate_response() handles tool_use blocks")
        has_tool_handling = True
    else:
        print("  ❌ FAIL: generate_response() does NOT handle tool_use blocks")
        has_tool_handling = False
    
    # Check 4: Is there a method to convert MCP tools to Anthropic format?
    print("\nCHECK 4: Is there a method to convert MCP tools to Anthropic format?")
    methods = [name for name in dir(BaseAgent) if not name.startswith('_')]
    tool_conversion_methods = [m for m in methods if 'tool' in m.lower() and 'anthropic' in m.lower()]
    
    if tool_conversion_methods:
        print(f"  ✅ PASS: Found tool conversion methods: {tool_conversion_methods}")
        has_conversion = True
    else:
        # Check for any method with 'tool' in the name
        tool_methods = [m for m in methods if 'tool' in m.lower()]
        if tool_methods:
            print(f"  ⚠️  PARTIAL: Found tool-related methods: {tool_methods}")
            print(f"     But no explicit Anthropic conversion method")
            has_conversion = False
        else:
            print("  ❌ FAIL: No tool conversion methods found")
            has_conversion = False
    
    # Summary
    print_header("SUMMARY")
    
    checks_passed = sum([has_mcp_param, has_tools_param, has_tool_handling, has_conversion])
    total_checks = 4
    
    print(f"Checks passed: {checks_passed}/{total_checks}\n")
    
    if checks_passed == total_checks:
        print("✅ CONCLUSION: Agents ARE integrated with MCP tools!")
        print("   All necessary components are in place.")
        return True
    elif checks_passed == 0:
        print("❌ CONCLUSION: Agents are NOT integrated with MCP tools!")
        print("   No integration components found.")
        print()
        print_what_needs_to_be_done()
        return False
    else:
        print("⚠️  CONCLUSION: Partial integration detected!")
        print(f"   {checks_passed} out of {total_checks} checks passed.")
        print("   Integration may be incomplete or in progress.")
        print()
        if not has_tools_param:
            print_what_needs_to_be_done()
        return False


def print_what_needs_to_be_done():
    """Print detailed instructions on what needs to be implemented."""
    print_header("WHAT NEEDS TO BE IMPLEMENTED")
    
    print("To enable agents to use MCP tools, modify src/agents/base_agent.py:\n")
    
    print("1️⃣  ADD mcp_manager to __init__:")
    print("   " + "-" * 70)
    print("   def __init__(")
    print("       self,")
    print("       ...,")
    print("       mcp_manager: Optional['MCPManager'] = None  # ADD THIS")
    print("   ):")
    print("       ...")
    print("       self.mcp_manager = mcp_manager  # ADD THIS")
    print()
    
    print("2️⃣  ADD method to convert MCP tools to Anthropic format:")
    print("   " + "-" * 70)
    print("   def _get_anthropic_tools(self) -> Optional[List[Dict[str, Any]]]:")
    print("       '''Convert MCP tools to Anthropic tool format.'''")
    print("       if not self.mcp_manager:")
    print("           return None")
    print("       ")
    print("       mcp_tools = self.mcp_manager.get_available_tools()")
    print("       if not mcp_tools:")
    print("           return None")
    print("       ")
    print("       # Convert MCP format to Anthropic format")
    print("       # Key difference: inputSchema -> input_schema")
    print("       anthropic_tools = []")
    print("       for tool in mcp_tools:")
    print("           anthropic_tools.append({")
    print("               'name': tool['name'],")
    print("               'description': tool['description'],")
    print("               'input_schema': tool['inputSchema']  # Note: underscore")
    print("           })")
    print("       return anthropic_tools")
    print()
    
    print("3️⃣  MODIFY generate_response() to pass tools to Claude API:")
    print("   " + "-" * 70)
    print("   def generate_response(self, channel, context_window=20):")
    print("       ...")
    print("       # Get tools if MCP manager is available")
    print("       tools = self._get_anthropic_tools()  # ADD THIS")
    print("       ")
    print("       # Pass tools to Claude API")
    print("       response = self.client.messages.create(")
    print("           model=self.model,")
    print("           max_tokens=self.max_tokens,")
    print("           system=self._build_system_prompt(),")
    print("           messages=messages,")
    print("           tools=tools  # ADD THIS (only if tools is not None)")
    print("       )")
    print()
    
    print("4️⃣  ADD tool use handling in generate_response():")
    print("   " + "-" * 70)
    print("   # After getting initial response, check for tool use")
    print("   while any(block.type == 'tool_use' for block in response.content")
    print("             if hasattr(block, 'type')):")
    print("       ")
    print("       # Extract tool use requests")
    print("       tool_results = []")
    print("       for block in response.content:")
    print("           if hasattr(block, 'type') and block.type == 'tool_use':")
    print("               # Call MCP tool")
    print("               result = await self.mcp_manager.call_tool(")
    print("                   server_name='aerospace-mcp',  # or get from config")
    print("                   tool_name=block.name,")
    print("                   arguments=block.input")
    print("               )")
    print("               ")
    print("               # Format result for Claude")
    print("               tool_results.append({")
    print("                   'type': 'tool_result',")
    print("                   'tool_use_id': block.id,")
    print("                   'content': result.content[0].text")
    print("               })")
    print("       ")
    print("       # Continue conversation with tool results")
    print("       messages.append({'role': 'assistant', 'content': response.content})")
    print("       messages.append({'role': 'user', 'content': tool_results})")
    print("       ")
    print("       # Get next response from Claude")
    print("       response = self.client.messages.create(...)")
    print()
    
    print("5️⃣  UPDATE agent creation to pass MCPManager:")
    print("   " + "-" * 70)
    print("   # In your agent creation code:")
    print("   from src.mcp.mcp_manager import get_mcp_manager")
    print("   ")
    print("   mcp_manager = await get_mcp_manager()")
    print("   agent = BaseAgent(")
    print("       callsign='Alpha One',")
    print("       ...,")
    print("       mcp_manager=mcp_manager  # Pass it here")
    print("   )")
    print()
    
    print("📚 REFERENCE:")
    print("   See Anthropic docs: https://docs.anthropic.com/en/docs/build-with-claude/tool-use")
    print()


if __name__ == "__main__":
    result = check_agent_tool_integration()
    sys.exit(0 if result else 1)

