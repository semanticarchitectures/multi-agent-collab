"""MCP Manager for connecting to and managing MCP servers."""

import asyncio
import json
from typing import Dict, List, Optional, Any
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from ..utils import get_logger, RetryConfig, async_retry_with_backoff, get_circuit_breaker_manager
from ..exceptions import (
    MCPConnectionError,
    MCPServerNotFoundError,
    ToolExecutionError,
    ToolNotFoundError,
    ToolTimeoutError,
    NetworkError,
    mcp_connection_error,
    tool_execution_error
)

logger = get_logger(__name__)


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
        self.circuit_breaker_manager = get_circuit_breaker_manager()

        # Retry configuration for MCP operations
        self.retry_config = RetryConfig(
            max_attempts=3,
            initial_delay=1.0,
            max_delay=10.0,
            exponential_base=2.0,
            jitter=True
        )

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

        Raises:
            MCPConnectionError: If connection fails after retries
        """
        logger.info(f"Connecting to MCP server: {server_name}")

        try:
            # Create server parameters
            server_params = StdioServerParameters(
                command=command,
                args=args,
                env=env or {}
            )

            # Connect to server (with timeout)
            stdio_transport = await asyncio.wait_for(
                self.exit_stack.enter_async_context(stdio_client(server_params)),
                timeout=30.0
            )

            # Create session
            read, write = stdio_transport
            session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )

            # Initialize session (with timeout)
            await asyncio.wait_for(session.initialize(), timeout=10.0)

            # Store session
            self.sessions[server_name] = session

            # Discover and cache tools
            await self._discover_tools(server_name)

            self._initialized = True
            logger.info(f"Successfully connected to {server_name}")
            return True

        except asyncio.TimeoutError as e:
            error_msg = f"Connection to {server_name} timed out"
            logger.error(error_msg)
            raise MCPConnectionError(
                error_msg,
                context={"server_name": server_name, "error": "timeout"}
            )
        except FileNotFoundError as e:
            error_msg = f"MCP server not found: {server_name}"
            logger.error(error_msg)
            raise MCPServerNotFoundError(
                error_msg,
                context={"server_name": server_name, "command": command, "args": args}
            )
        except Exception as e:
            error_msg = f"Failed to connect to {server_name}"
            logger.error(f"{error_msg}: {str(e)}", exc_info=True)
            raise mcp_connection_error(server_name, e)

    async def _discover_tools(self, server_name: str):
        """Discover available tools from a connected server.

        Args:
            server_name: Name of the server to query

        Raises:
            MCPConnectionError: If tool discovery fails
        """
        if server_name not in self.sessions:
            logger.warning(f"Cannot discover tools: {server_name} not connected")
            return

        try:
            session = self.sessions[server_name]
            tools_response = await asyncio.wait_for(
                session.list_tools(),
                timeout=10.0
            )

            # Cache tool information
            self.tools_cache[server_name] = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema,
                }
                for tool in tools_response.tools
            ]

            logger.info(f"Discovered {len(self.tools_cache[server_name])} tools from {server_name}")

        except asyncio.TimeoutError:
            error_msg = f"Tool discovery timed out for {server_name}"
            logger.error(error_msg)
            raise MCPConnectionError(
                error_msg,
                context={"server_name": server_name, "operation": "discover_tools"}
            )
        except Exception as e:
            error_msg = f"Error discovering tools from {server_name}"
            logger.error(f"{error_msg}: {str(e)}", exc_info=True)
            raise MCPConnectionError(
                error_msg,
                context={"server_name": server_name, "error": str(e)}
            )

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
        server_name: Optional[str] = None,
        timeout: float = 30.0
    ) -> Optional[Any]:
        """Call an MCP tool with circuit breaker protection and retry logic.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            server_name: Optional server name. If None, searches all servers.
            timeout: Operation timeout in seconds

        Returns:
            Tool result

        Raises:
            ToolNotFoundError: If tool doesn't exist
            ToolExecutionError: If tool execution fails
            CircuitBreakerOpenError: If circuit breaker is open for the server
        """
        # Find the server that has this tool
        target_session = None
        target_server_name = server_name

        if server_name and server_name in self.sessions:
            target_session = self.sessions[server_name]
        else:
            # Search for tool in all servers
            for srv_name, tools in self.tools_cache.items():
                if any(tool["name"] == tool_name for tool in tools):
                    target_session = self.sessions.get(srv_name)
                    target_server_name = srv_name
                    break

        if not target_session or not target_server_name:
            raise ToolNotFoundError(
                f"Tool '{tool_name}' not found in any connected server",
                context={
                    "tool_name": tool_name,
                    "available_servers": list(self.sessions.keys())
                }
            )

        # Get circuit breaker for this server
        breaker = self.circuit_breaker_manager.get_breaker(
            name=f"mcp_{target_server_name}",
            failure_threshold=5,
            recovery_timeout=60.0,
            timeout=timeout
        )

        logger.debug(f"Calling tool '{tool_name}' on {target_server_name}")

        try:
            # Call tool through circuit breaker
            async def _call():
                return await asyncio.wait_for(
                    target_session.call_tool(tool_name, arguments),
                    timeout=timeout
                )

            result = await breaker.call(_call)
            logger.debug(f"Tool '{tool_name}' executed successfully")
            return result

        except asyncio.TimeoutError:
            error_msg = f"Tool '{tool_name}' timed out after {timeout}s"
            logger.error(error_msg)
            raise ToolTimeoutError(
                error_msg,
                context={
                    "tool_name": tool_name,
                    "server_name": target_server_name,
                    "timeout_seconds": timeout
                }
            )
        except Exception as e:
            # Circuit breaker errors are already well-formatted
            if isinstance(e, (ToolExecutionError, ToolNotFoundError, ToolTimeoutError)):
                raise

            error_msg = f"Tool '{tool_name}' execution failed"
            logger.error(f"{error_msg}: {str(e)}", exc_info=True)
            raise ToolExecutionError(
                error_msg,
                context={
                    "tool_name": tool_name,
                    "server_name": target_server_name,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )

    async def close(self):
        """Close all server connections."""
        await self.exit_stack.aclose()
        self.sessions.clear()
        self.tools_cache.clear()
        self._initialized = False

    async def cleanup(self):
        """Alias for close() for convenience."""
        await self.close()

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
        True if successful, False if connection fails
    """
    manager = await get_mcp_manager()

    try:
        return await manager.connect_server(
            server_name="aerospace-mcp",
            command="uv",
            args=["--directory", aerospace_mcp_path, "run", "aerospace-mcp"],
            env=env
        )
    except (MCPConnectionError, MCPServerNotFoundError) as e:
        logger.warning(f"Failed to initialize aerospace-mcp: {str(e)}")
        return False


async def initialize_aviation_weather_mcp(
    aviation_weather_mcp_path: str,
    env: Optional[Dict[str, str]] = None
) -> bool:
    """Initialize connection to the Aviation Weather MCP server.

    Args:
        aviation_weather_mcp_path: Path to aviation-weather-mcp directory
        env: Optional environment variables

    Returns:
        True if successful, False if connection fails
    """
    manager = await get_mcp_manager()

    try:
        return await manager.connect_server(
            server_name="aviation-weather-mcp",
            command="uv",
            args=["--directory", aviation_weather_mcp_path, "run", "aviation-weather-mcp"],
            env=env
        )
    except (MCPConnectionError, MCPServerNotFoundError) as e:
        logger.warning(f"Failed to initialize aviation-weather-mcp: {str(e)}")
        return False


async def initialize_blevinstein_aviation_mcp(
    blevinstein_aviation_mcp_path: str,
    env: Optional[Dict[str, str]] = None
) -> bool:
    """Initialize connection to the Blevinstein Aviation MCP server.

    Args:
        blevinstein_aviation_mcp_path: Path to blevinstein aviation-mcp directory
        env: Optional environment variables

    Returns:
        True if successful, False if connection fails
    """
    manager = await get_mcp_manager()

    try:
        return await manager.connect_server(
            server_name="blevinstein-aviation-mcp",
            command="uv",
            args=["--directory", blevinstein_aviation_mcp_path, "run", "aviation-mcp"],
            env=env
        )
    except (MCPConnectionError, MCPServerNotFoundError) as e:
        logger.warning(f"Failed to initialize blevinstein-aviation-mcp: {str(e)}")
        return False


async def initialize_aircraft_sim_mcp(
    aircraft_sim_mcp_path: str,
    env: Optional[Dict[str, str]] = None
) -> bool:
    """Initialize connection to the Aircraft Simulator MCP server.

    Args:
        aircraft_sim_mcp_path: Path to aircraft-sim-mcp directory
        env: Optional environment variables

    Returns:
        True if successful, False if connection fails
    """
    manager = await get_mcp_manager()

    try:
        # Use the aircraft-sim-mcp's venv Python to ensure JSBSim is available
        venv_python = f"{aircraft_sim_mcp_path}/venv/bin/python"

        return await manager.connect_server(
            server_name="aircraft-sim-mcp",
            command=venv_python,
            args=["-m", "flight_simulator_mcp.server"],
            env={
                "PYTHONPATH": f"{aircraft_sim_mcp_path}/src",
                **(env or {})
            }
        )
    except (MCPConnectionError, MCPServerNotFoundError) as e:
        logger.warning(f"Failed to initialize aircraft-sim-mcp: {str(e)}")
        return False


async def initialize_all_aviation_mcps(
    aerospace_path: Optional[str] = None,
    aviation_weather_path: Optional[str] = None,
    blevinstein_aviation_path: Optional[str] = None,
    aircraft_sim_path: Optional[str] = None,
    env: Optional[Dict[str, str]] = None
) -> Dict[str, bool]:
    """Initialize all available aviation MCP servers.

    Args:
        aerospace_path: Path to aerospace-mcp directory (optional)
        aviation_weather_path: Path to aviation-weather-mcp directory (optional)
        blevinstein_aviation_path: Path to blevinstein aviation-mcp directory (optional)
        aircraft_sim_path: Path to aircraft-sim-mcp directory (optional)
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

    if aircraft_sim_path:
        results["aircraft-sim-mcp"] = await initialize_aircraft_sim_mcp(
            aircraft_sim_path, env
        )

    return results
