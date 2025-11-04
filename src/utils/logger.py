"""Centralized logging configuration for the multi-agent collaboration system.

This module provides structured logging with:
- Multiple log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Contextual information (agent_id, session_id, etc.)
- Console and file output options
- Configurable via environment variables
- Log rotation for production use

Usage:
    from src.utils.logger import get_logger

    logger = get_logger(__name__)
    logger.info("Agent started", extra={"agent_id": "alpha-one"})
    logger.error("Tool execution failed", extra={"tool_name": "search_airports", "error": str(e)})
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime


# Global configuration
_CONFIGURED = False
_LOG_DIR = None
_LOG_LEVEL = None


class ContextFilter(logging.Filter):
    """Add contextual information to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add default context if not present."""
        if not hasattr(record, 'agent_id'):
            record.agent_id = '-'
        if not hasattr(record, 'session_id'):
            record.session_id = '-'
        if not hasattr(record, 'tool_name'):
            record.tool_name = '-'
        return True


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        # Add color to level name
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname:8}{self.COLORS['RESET']}"

        return super().format(record)


def configure_logging(
    level: Optional[str] = None,
    log_to_file: bool = True,
    log_to_console: bool = True,
    log_dir: Optional[str] = None,
    log_file_name: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5
) -> None:
    """Configure the logging system.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
               Defaults to environment variable AGENT_LOG_LEVEL or INFO.
        log_to_file: Whether to log to file
        log_to_console: Whether to log to console
        log_dir: Directory for log files. Defaults to ./logs
        log_file_name: Name of log file. Defaults to agent-YYYYMMDD.log
        max_bytes: Maximum size of each log file before rotation
        backup_count: Number of backup files to keep
    """
    global _CONFIGURED, _LOG_DIR, _LOG_LEVEL

    if _CONFIGURED:
        return

    # Get log level from parameter or environment
    level = level or os.getenv('AGENT_LOG_LEVEL', 'INFO')
    _LOG_LEVEL = level.upper()

    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(_LOG_LEVEL)

    # Clear any existing handlers
    root_logger.handlers.clear()

    # Console handler with colors
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(_LOG_LEVEL)

        # Use colored formatter for console
        console_format = '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
        if os.getenv('AGENT_LOG_NO_COLOR', '').lower() != 'true':
            console_formatter = ColoredFormatter(
                console_format,
                datefmt='%H:%M:%S'
            )
        else:
            console_formatter = logging.Formatter(
                console_format,
                datefmt='%H:%M:%S'
            )

        console_handler.setFormatter(console_formatter)
        console_handler.addFilter(ContextFilter())
        root_logger.addHandler(console_handler)

    # File handler with rotation
    if log_to_file:
        # Create log directory
        if log_dir is None:
            log_dir = os.path.join(os.getcwd(), 'logs')

        _LOG_DIR = Path(log_dir)
        _LOG_DIR.mkdir(parents=True, exist_ok=True)

        # Generate log file name
        if log_file_name is None:
            timestamp = datetime.now().strftime('%Y%m%d')
            log_file_name = f'agent-{timestamp}.log'

        log_file_path = _LOG_DIR / log_file_name

        # Create rotating file handler
        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(_LOG_LEVEL)

        # Detailed format for file logs
        file_format = (
            '%(asctime)s | %(levelname)-8s | %(name)-30s | '
            '%(agent_id)-12s | %(session_id)-12s | %(tool_name)-20s | '
            '%(message)s'
        )
        file_formatter = logging.Formatter(
            file_format,
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        file_handler.setFormatter(file_formatter)
        file_handler.addFilter(ContextFilter())
        root_logger.addHandler(file_handler)

    # Silence noisy third-party loggers
    logging.getLogger('anthropic').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

    _CONFIGURED = True

    # Log that logging is configured
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured: level={_LOG_LEVEL}, file={log_to_file}, console={log_to_console}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance

    Example:
        logger = get_logger(__name__)
        logger.info("Processing started")
        logger.debug("Detailed info", extra={"agent_id": "alpha-one"})
    """
    # Auto-configure if not yet configured
    if not _CONFIGURED:
        configure_logging()

    return logging.getLogger(name)


# Convenience functions for common logging patterns

def log_agent_action(
    logger: logging.Logger,
    action: str,
    agent_id: str,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """Log an agent action with context.

    Args:
        logger: Logger instance
        action: Description of the action
        agent_id: Agent identifier
        details: Optional additional details
    """
    extra = {"agent_id": agent_id}
    if details:
        extra.update(details)

    logger.info(f"Agent action: {action}", extra=extra)


def log_tool_execution(
    logger: logging.Logger,
    tool_name: str,
    agent_id: str,
    success: bool,
    duration_ms: Optional[float] = None,
    error: Optional[str] = None
) -> None:
    """Log a tool execution with timing and result.

    Args:
        logger: Logger instance
        tool_name: Name of the tool
        agent_id: Agent identifier
        success: Whether execution succeeded
        duration_ms: Execution time in milliseconds
        error: Error message if failed
    """
    extra = {
        "agent_id": agent_id,
        "tool_name": tool_name
    }

    if success:
        msg = f"Tool executed successfully"
        if duration_ms is not None:
            msg += f" ({duration_ms:.2f}ms)"
        logger.info(msg, extra=extra)
    else:
        msg = f"Tool execution failed"
        if error:
            msg += f": {error}"
        logger.error(msg, extra=extra)


def log_mcp_connection(
    logger: logging.Logger,
    server_name: str,
    success: bool,
    tool_count: Optional[int] = None,
    error: Optional[str] = None
) -> None:
    """Log MCP server connection status.

    Args:
        logger: Logger instance
        server_name: Name of the MCP server
        success: Whether connection succeeded
        tool_count: Number of tools available (if successful)
        error: Error message if failed
    """
    if success:
        msg = f"Connected to MCP server '{server_name}'"
        if tool_count is not None:
            msg += f" ({tool_count} tools available)"
        logger.info(msg)
    else:
        msg = f"Failed to connect to MCP server '{server_name}'"
        if error:
            msg += f": {error}"
        logger.error(msg)


def log_session_event(
    logger: logging.Logger,
    event: str,
    session_id: str,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """Log a session-related event.

    Args:
        logger: Logger instance
        event: Event description (e.g., 'started', 'saved', 'loaded')
        session_id: Session identifier
        details: Optional additional details
    """
    extra = {"session_id": session_id}
    if details:
        extra.update(details)

    logger.info(f"Session {event}", extra=extra)


def log_error_with_context(
    logger: logging.Logger,
    error: Exception,
    context: Dict[str, Any],
    message: Optional[str] = None
) -> None:
    """Log an error with full context.

    Args:
        logger: Logger instance
        error: The exception that occurred
        context: Contextual information (agent_id, tool_name, etc.)
        message: Optional custom message
    """
    msg = message or f"{type(error).__name__}: {str(error)}"

    logger.error(
        msg,
        extra=context,
        exc_info=True  # Include stack trace
    )


def set_log_level(level: str) -> None:
    """Change the log level at runtime.

    Args:
        level: New log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    global _LOG_LEVEL

    level = level.upper()
    _LOG_LEVEL = level

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    for handler in root_logger.handlers:
        handler.setLevel(level)

    logger = get_logger(__name__)
    logger.info(f"Log level changed to {level}")


def get_log_dir() -> Optional[Path]:
    """Get the current log directory.

    Returns:
        Path to log directory, or None if not configured
    """
    return _LOG_DIR


def get_log_level() -> Optional[str]:
    """Get the current log level.

    Returns:
        Current log level string, or None if not configured
    """
    return _LOG_LEVEL


# Auto-configure on import if environment variable is set
if os.getenv('AGENT_AUTO_CONFIGURE_LOGGING', 'true').lower() == 'true':
    configure_logging()
