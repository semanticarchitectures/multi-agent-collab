"""
Custom exception types for the multi-agent collaboration system.

These exceptions provide better context and error handling for different
failure scenarios throughout the system.
"""


class AgentSystemError(Exception):
    """Base exception for all agent system errors."""

    def __init__(self, message: str, context: dict = None):
        """
        Initialize exception with message and optional context.

        Args:
            message: Human-readable error message
            context: Optional dict with additional context (agent_id, tool_name, etc.)
        """
        self.message = message
        self.context = context or {}
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """Format error message with context."""
        msg = self.message
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            msg = f"{msg} ({context_str})"
        return msg


class MCPConnectionError(AgentSystemError):
    """
    Raised when unable to connect to an MCP server.

    Example:
        raise MCPConnectionError(
            "Failed to connect to MCP server",
            context={"server_name": "aerospace-mcp", "attempt": 3}
        )
    """
    pass


class MCPServerNotFoundError(MCPConnectionError):
    """
    Raised when an MCP server path doesn't exist.

    Example:
        raise MCPServerNotFoundError(
            "MCP server not found at path",
            context={"path": "/path/to/server"}
        )
    """
    pass


class ToolExecutionError(AgentSystemError):
    """
    Raised when a tool execution fails.

    Example:
        raise ToolExecutionError(
            "Tool execution failed",
            context={
                "agent_id": "alpha-one",
                "tool_name": "search_airports",
                "error": str(original_error)
            }
        )
    """
    pass


class ToolNotFoundError(ToolExecutionError):
    """
    Raised when an agent tries to use a tool that doesn't exist.

    Example:
        raise ToolNotFoundError(
            "Tool not found",
            context={
                "agent_id": "alpha-one",
                "tool_name": "nonexistent_tool",
                "available_tools": ["tool1", "tool2"]
            }
        )
    """
    pass


class ToolTimeoutError(ToolExecutionError):
    """
    Raised when a tool execution times out.

    Example:
        raise ToolTimeoutError(
            "Tool execution timed out",
            context={
                "agent_id": "alpha-one",
                "tool_name": "slow_tool",
                "timeout_seconds": 30
            }
        )
    """
    pass


class AgentResponseError(AgentSystemError):
    """
    Raised when agent response generation fails.

    Example:
        raise AgentResponseError(
            "Failed to generate response",
            context={
                "agent_id": "alpha-one",
                "error": "API rate limit exceeded"
            }
        )
    """
    pass


class APIRateLimitError(AgentResponseError):
    """
    Raised when hitting API rate limits.

    Example:
        raise APIRateLimitError(
            "API rate limit exceeded",
            context={
                "agent_id": "alpha-one",
                "retry_after": 60
            }
        )
    """
    pass


class StateError(AgentSystemError):
    """
    Raised when state save/load operations fail.

    Example:
        raise StateError(
            "Failed to save session",
            context={
                "session_id": "mission-001",
                "error": "Database connection failed"
            }
        )
    """
    pass


class SessionNotFoundError(StateError):
    """
    Raised when trying to load a session that doesn't exist.

    Example:
        raise SessionNotFoundError(
            "Session not found",
            context={"session_id": "nonexistent-session"}
        )
    """
    pass


class ChannelError(AgentSystemError):
    """
    Raised when message routing or channel operations fail.

    Example:
        raise ChannelError(
            "Failed to route message",
            context={
                "message_id": "msg-123",
                "error": "No agents available"
            }
        )
    """
    pass


class ConfigurationError(AgentSystemError):
    """
    Raised when configuration is invalid or missing required fields.

    Example:
        raise ConfigurationError(
            "Invalid agent configuration",
            context={
                "agent_id": "alpha-one",
                "missing_fields": ["system_prompt", "callsign"]
            }
        )
    """
    pass


class MemoryError(AgentSystemError):
    """
    Raised when agent memory operations fail.

    Example:
        raise MemoryError(
            "Invalid memory format",
            context={
                "agent_id": "alpha-one",
                "category": "key_facts",
                "error": "Expected dict format"
            }
        )
    """
    pass


# Retry-related exceptions

class RetryableError(AgentSystemError):
    """
    Base class for errors that should trigger a retry.

    This is used by retry logic to determine if an operation should be retried.
    """
    pass


class NetworkError(RetryableError):
    """
    Raised for transient network errors that should be retried.

    Example:
        raise NetworkError(
            "Network request failed",
            context={
                "url": "https://api.anthropic.com",
                "attempt": 2
            }
        )
    """
    pass


class CircuitBreakerOpenError(AgentSystemError):
    """
    Raised when circuit breaker is open and blocking requests.

    Example:
        raise CircuitBreakerOpenError(
            "Circuit breaker open for MCP server",
            context={
                "server_name": "aerospace-mcp",
                "failure_count": 5,
                "retry_after": 60
            }
        )
    """
    pass


# Helper functions for creating exceptions with context

def mcp_connection_error(server_name: str, error: Exception, attempt: int = 1) -> MCPConnectionError:
    """
    Create an MCPConnectionError with standardized context.

    Args:
        server_name: Name of the MCP server
        error: Original exception
        attempt: Connection attempt number

    Returns:
        MCPConnectionError with full context
    """
    return MCPConnectionError(
        f"Failed to connect to MCP server '{server_name}'",
        context={
            "server_name": server_name,
            "error": str(error),
            "attempt": attempt
        }
    )


def tool_execution_error(agent_id: str, tool_name: str, error: Exception) -> ToolExecutionError:
    """
    Create a ToolExecutionError with standardized context.

    Args:
        agent_id: ID of the agent executing the tool
        tool_name: Name of the tool that failed
        error: Original exception

    Returns:
        ToolExecutionError with full context
    """
    return ToolExecutionError(
        f"Tool '{tool_name}' execution failed for agent '{agent_id}'",
        context={
            "agent_id": agent_id,
            "tool_name": tool_name,
            "error": str(error),
            "error_type": type(error).__name__
        }
    )


def agent_response_error(agent_id: str, error: Exception) -> AgentResponseError:
    """
    Create an AgentResponseError with standardized context.

    Args:
        agent_id: ID of the agent
        error: Original exception

    Returns:
        AgentResponseError with full context
    """
    return AgentResponseError(
        f"Failed to generate response for agent '{agent_id}'",
        context={
            "agent_id": agent_id,
            "error": str(error),
            "error_type": type(error).__name__
        }
    )
