"""
Mock MCP Manager for testing without actual MCP servers.

This provides a fake MCP manager that returns canned responses,
allowing for fast, deterministic tests without network calls.
"""

from typing import Dict, List, Optional, Any
from unittest.mock import AsyncMock


class MockMCPManager:
    """Mock MCP Manager for testing.

    This mock provides:
    - Predefined tool definitions
    - Canned tool responses
    - Configurable failures for error testing
    - No actual network calls
    """

    def __init__(self, should_fail: bool = False, tool_responses: Optional[Dict[str, Any]] = None):
        """
        Initialize mock MCP manager.

        Args:
            should_fail: If True, tool calls will fail
            tool_responses: Optional dict mapping tool names to responses
        """
        self.should_fail = should_fail
        self.tool_responses = tool_responses or {}

        # Track calls for verification
        self.tool_calls: List[Dict[str, Any]] = []

        # Default tool definitions
        self.tools_cache = {
            "mock-mcp": [
                {
                    "name": "search_airports",
                    "description": "Search for airports by query",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"}
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "get_weather",
                    "description": "Get weather for an airport",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "icao_code": {"type": "string"}
                        },
                        "required": ["icao_code"]
                    }
                },
                {
                    "name": "calculate_distance",
                    "description": "Calculate distance between two points",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "from_lat": {"type": "number"},
                            "from_lon": {"type": "number"},
                            "to_lat": {"type": "number"},
                            "to_lon": {"type": "number"}
                        },
                        "required": ["from_lat", "from_lon", "to_lat", "to_lon"]
                    }
                }
            ]
        }

        # Default responses
        self.default_responses = {
            "search_airports": MockToolResult(
                "Found 3 airports:\n1. KBOS - Logan International Airport\n2. KBED - Hanscom Field\n3. KOWD - Norwood Memorial Airport"
            ),
            "get_weather": MockToolResult(
                "Weather at KBOS: Clear skies, 15°C, Wind 10kt from 270°, Visibility 10SM"
            ),
            "calculate_distance": MockToolResult(
                "Distance: 237 nautical miles"
            )
        }

    def get_available_tools(self, server_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of available tools.

        Args:
            server_name: Optional server name filter

        Returns:
            List of tool definitions
        """
        if server_name:
            return self.tools_cache.get(server_name, [])

        # Return all tools
        all_tools = []
        for tools in self.tools_cache.values():
            all_tools.extend(tools)
        return all_tools

    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool information or None if not found
        """
        for tools in self.tools_cache.values():
            for tool in tools:
                if tool["name"] == tool_name:
                    return tool
        return None

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        server_name: Optional[str] = None,
        timeout: float = 30.0
    ) -> Optional[Any]:
        """Call a mock tool.

        Args:
            tool_name: Name of the tool
            arguments: Tool arguments
            server_name: Optional server name
            timeout: Operation timeout (ignored in mock)

        Returns:
            Mock tool result

        Raises:
            Exception: If should_fail is True
        """
        # Record the call
        self.tool_calls.append({
            "tool_name": tool_name,
            "arguments": arguments,
            "server_name": server_name
        })

        # Simulate failure if configured
        if self.should_fail:
            raise Exception(f"Mock failure: Tool {tool_name} failed")

        # Return custom response if provided
        if tool_name in self.tool_responses:
            response = self.tool_responses[tool_name]
            if callable(response):
                return response(arguments)
            return response

        # Return default response
        return self.default_responses.get(tool_name, MockToolResult("Mock tool result"))

    def is_initialized(self) -> bool:
        """Check if manager is initialized.

        Returns:
            Always True for mock
        """
        return True

    def get_server_names(self) -> List[str]:
        """Get list of connected server names.

        Returns:
            List of mock server names
        """
        return list(self.tools_cache.keys())

    def reset_calls(self):
        """Reset the call tracking list."""
        self.tool_calls = []

    def get_call_count(self, tool_name: Optional[str] = None) -> int:
        """Get number of tool calls.

        Args:
            tool_name: Optional filter by tool name

        Returns:
            Number of calls
        """
        if tool_name:
            return sum(1 for call in self.tool_calls if call["tool_name"] == tool_name)
        return len(self.tool_calls)

    def get_last_call(self) -> Optional[Dict[str, Any]]:
        """Get the last tool call.

        Returns:
            Last call dict or None
        """
        return self.tool_calls[-1] if self.tool_calls else None


class MockToolResult:
    """Mock MCP tool result."""

    def __init__(self, text: str):
        """Initialize mock result.

        Args:
            text: Result text
        """
        self.content = [MockContent(text)]


class MockContent:
    """Mock MCP content."""

    def __init__(self, text: str):
        """Initialize mock content.

        Args:
            text: Content text
        """
        self.text = text


def create_mock_mcp_manager(**kwargs) -> MockMCPManager:
    """
    Factory function to create a mock MCP manager.

    Args:
        **kwargs: Arguments passed to MockMCPManager

    Returns:
        MockMCPManager instance

    Example:
        # Normal mock
        mock = create_mock_mcp_manager()

        # Mock that fails
        mock = create_mock_mcp_manager(should_fail=True)

        # Mock with custom responses
        mock = create_mock_mcp_manager(
            tool_responses={
                "search_airports": MockToolResult("Custom airport response")
            }
        )
    """
    return MockMCPManager(**kwargs)
