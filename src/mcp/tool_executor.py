"""Tool executor for MCP tool calls from agents."""

import asyncio
import json
from typing import Dict, List, Optional, Any

from .mcp_manager import get_mcp_manager


class ToolExecutor:
    """Executes MCP tools requested by agents.

    Handles:
    - Tool argument parsing
    - Async tool execution
    - Result formatting
    - Error handling
    """

    def __init__(self):
        """Initialize the tool executor."""
        self.execution_history: List[Dict[str, Any]] = []

    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        agent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute an MCP tool.

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            agent_id: Optional ID of the agent calling the tool

        Returns:
            Dict with success status, result, and error info
        """
        try:
            manager = await get_mcp_manager()

            if not manager.is_initialized():
                return {
                    "success": False,
                    "error": "MCP manager not initialized",
                    "result": None
                }

            # Call the tool
            result = await manager.call_tool(tool_name, arguments)

            # Record execution
            execution_record = {
                "tool_name": tool_name,
                "arguments": arguments,
                "agent_id": agent_id,
                "success": result is not None,
                "result": result
            }
            self.execution_history.append(execution_record)

            if result is None:
                return {
                    "success": False,
                    "error": f"Tool {tool_name} returned no result",
                    "result": None
                }

            return {
                "success": True,
                "result": result,
                "error": None
            }

        except Exception as e:
            error_msg = f"Error executing tool {tool_name}: {str(e)}"
            return {
                "success": False,
                "error": error_msg,
                "result": None
            }

    async def execute_tools_batch(
        self,
        tool_calls: List[Dict[str, Any]],
        agent_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Execute multiple tools in parallel.

        Args:
            tool_calls: List of tool call dicts with 'name' and 'arguments'
            agent_id: Optional ID of the agent calling the tools

        Returns:
            List of execution results
        """
        tasks = [
            self.execute_tool(call["name"], call["arguments"], agent_id)
            for call in tool_calls
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to error dicts
        formatted_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                formatted_results.append({
                    "success": False,
                    "error": str(result),
                    "result": None,
                    "tool_name": tool_calls[i]["name"]
                })
            else:
                formatted_results.append(result)

        return formatted_results

    def get_execution_history(
        self,
        agent_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get tool execution history.

        Args:
            agent_id: Optional filter by agent ID
            limit: Maximum number of records to return

        Returns:
            List of execution records
        """
        history = self.execution_history

        if agent_id:
            history = [h for h in history if h.get("agent_id") == agent_id]

        return history[-limit:]

    def clear_history(self):
        """Clear execution history."""
        self.execution_history.clear()


# Singleton instance
_tool_executor: Optional[ToolExecutor] = None


def get_tool_executor() -> ToolExecutor:
    """Get or create the global tool executor instance.

    Returns:
        ToolExecutor instance
    """
    global _tool_executor
    if _tool_executor is None:
        _tool_executor = ToolExecutor()
    return _tool_executor
