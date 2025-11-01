"""MCP Manager for connecting to and managing MCP servers."""

import asyncio
import json
from typing import Dict, List, Optional, Any
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPManager:
    """Manages connections to MCP servers and tool discovery.

    This manager handles:
    - Connecting to MCP servers via stdio
    - Discovering available tools
    - Managing server lifecycle
    - Tool metadata caching
    """

    def __init__(self):
        """Initialize the MCP manager."""
        self.sessions: Dict[str, ClientSession] = {}
        self.tools_cache: Dict[str, List[Dict[str, Any]]] = {}
        self.exit_stack = AsyncExitStack()
        self._initialized = False

    async def connect_server(
        self,
        server_name: str,
        command: str,
        args: List[str],
        env: Optional[Dict[str, str]] = None
    ) -> bool:
        """Connect to an MCP server via stdio.

        Args:
            server_name: Name to identify this server
            command: Command to run the server (e.g., "uv")
            args: Arguments for the command (e.g., ["run", "aerospace-mcp"])
            env: Optional environment variables

        Returns:
            True if connection successful
        """
        try:
            # Create server parameters
            server_params = StdioServerParameters(
                command=command,
                args=args,
                env=env or {}
            )

            # Connect to server
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )

            # Create session
            read, write = stdio_transport
            session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )

            # Initialize session
            await session.initialize()

            # Store session
            self.sessions[server_name] = session

            # Discover and cache tools
            await self._discover_tools(server_name)

            self._initialized = True
            return True

        except Exception as e:
            print(f"Error connecting to {server_name}: {e}")
            return False

    async def _discover_tools(self, server_name: str):
        """Discover available tools from a connected server.

        Args:
            server_name: Name of the server to query
        """
        if server_name not in self.sessions:
            return

        try:
            session = self.sessions[server_name]
            tools_response = await session.list_tools()

            # Cache tool information
            self.tools_cache[server_name] = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema,
                }
                for tool in tools_response.tools
            ]

        except Exception as e:
            print(f"Error discovering tools from {server_name}: {e}")

    def get_available_tools(self, server_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of available tools.

        Args:
            server_name: Optional server to get tools from. If None, returns all tools.

        Returns:
            List of tool definitions
        """
        if server_name:
            return self.tools_cache.get(server_name, [])

        # Return all tools from all servers
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
        server_name: Optional[str] = None
    ) -> Optional[Any]:
        """Call an MCP tool.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            server_name: Optional server name. If None, searches all servers.

        Returns:
            Tool result or None if failed
        """
        # Find the server that has this tool
        target_session = None

        if server_name and server_name in self.sessions:
            target_session = self.sessions[server_name]
        else:
            # Search for tool in all servers
            for srv_name, tools in self.tools_cache.items():
                if any(tool["name"] == tool_name for tool in tools):
                    target_session = self.sessions.get(srv_name)
                    break

        if not target_session:
            print(f"Tool {tool_name} not found in any connected server")
            return None

        try:
            # Call the tool
            result = await target_session.call_tool(tool_name, arguments)
            return result

        except Exception as e:
            print(f"Error calling tool {tool_name}: {e}")
            return None

    async def close(self):
        """Close all server connections."""
        await self.exit_stack.aclose()
        self.sessions.clear()
        self.tools_cache.clear()
        self._initialized = False

    def is_initialized(self) -> bool:
        """Check if manager is initialized with at least one server.

        Returns:
            True if initialized
        """
        return self._initialized and len(self.sessions) > 0

    def get_server_names(self) -> List[str]:
        """Get list of connected server names.

        Returns:
            List of server names
        """
        return list(self.sessions.keys())


# Singleton instance
_mcp_manager: Optional[MCPManager] = None


async def get_mcp_manager() -> MCPManager:
    """Get or create the global MCP manager instance.

    Returns:
        MCPManager instance
    """
    global _mcp_manager
    if _mcp_manager is None:
        _mcp_manager = MCPManager()
    return _mcp_manager


async def initialize_aerospace_mcp(
    aerospace_mcp_path: str,
    env: Optional[Dict[str, str]] = None
) -> bool:
    """Initialize connection to the Aerospace MCP server.

    Args:
        aerospace_mcp_path: Path to aerospace-mcp directory
        env: Optional environment variables

    Returns:
        True if successful
    """
    manager = await get_mcp_manager()

    return await manager.connect_server(
        server_name="aerospace-mcp",
        command="uv",
        args=["--directory", aerospace_mcp_path, "run", "aerospace-mcp"],
        env=env
    )


async def initialize_aviation_weather_mcp(
    aviation_weather_mcp_path: str,
    env: Optional[Dict[str, str]] = None
) -> bool:
    """Initialize connection to the Aviation Weather MCP server.

    Args:
        aviation_weather_mcp_path: Path to aviation-weather-mcp directory
        env: Optional environment variables

    Returns:
        True if successful
    """
    manager = await get_mcp_manager()

    return await manager.connect_server(
        server_name="aviation-weather-mcp",
        command="uv",
        args=["--directory", aviation_weather_mcp_path, "run", "aviation-weather-mcp"],
        env=env
    )


async def initialize_blevinstein_aviation_mcp(
    blevinstein_aviation_mcp_path: str,
    env: Optional[Dict[str, str]] = None
) -> bool:
    """Initialize connection to the Blevinstein Aviation MCP server.

    Args:
        blevinstein_aviation_mcp_path: Path to blevinstein aviation-mcp directory
        env: Optional environment variables

    Returns:
        True if successful
    """
    manager = await get_mcp_manager()

    return await manager.connect_server(
        server_name="blevinstein-aviation-mcp",
        command="uv",
        args=["--directory", blevinstein_aviation_mcp_path, "run", "aviation-mcp"],
        env=env
    )


async def initialize_all_aviation_mcps(
    aerospace_path: Optional[str] = None,
    aviation_weather_path: Optional[str] = None,
    blevinstein_aviation_path: Optional[str] = None,
    env: Optional[Dict[str, str]] = None
) -> Dict[str, bool]:
    """Initialize all available aviation MCP servers.

    Args:
        aerospace_path: Path to aerospace-mcp directory (optional)
        aviation_weather_path: Path to aviation-weather-mcp directory (optional)
        blevinstein_aviation_path: Path to blevinstein aviation-mcp directory (optional)
        env: Optional environment variables

    Returns:
        Dictionary mapping server names to connection success status
    """
    results = {}

    if aerospace_path:
        results["aerospace-mcp"] = await initialize_aerospace_mcp(aerospace_path, env)

    if aviation_weather_path:
        results["aviation-weather-mcp"] = await initialize_aviation_weather_mcp(
            aviation_weather_path, env
        )

    if blevinstein_aviation_path:
        results["blevinstein-aviation-mcp"] = await initialize_blevinstein_aviation_mcp(
            blevinstein_aviation_path, env
        )

    return results
