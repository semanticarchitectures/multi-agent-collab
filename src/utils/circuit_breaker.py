"""
Circuit breaker pattern implementation for preventing cascading failures.

The circuit breaker monitors for failures and "opens" to prevent further
requests when a failure threshold is reached. After a timeout period,
it transitions to "half-open" to test if the service has recovered.

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Too many failures, requests are blocked
- HALF_OPEN: Testing recovery, limited requests allowed
"""

import asyncio
import time
from enum import Enum
from typing import Callable, TypeVar, Any, Optional
from functools import wraps
import logging

from ..exceptions import CircuitBreakerOpenError

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Blocking requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    """
    Circuit breaker for protecting against cascading failures.

    When failures reach a threshold, the circuit "opens" and blocks requests
    for a timeout period. After the timeout, it enters "half-open" state to
    test if the service has recovered.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        success_threshold: int = 2,
        timeout: float = 30.0
    ):
        """
        Initialize circuit breaker.

        Args:
            name: Name of the circuit (for logging)
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            success_threshold: Consecutive successes needed to close circuit from half-open
            timeout: Operation timeout in seconds
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.timeout = timeout

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (blocking requests)."""
        return self._state == CircuitState.OPEN

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (allowing requests)."""
        return self._state == CircuitState.CLOSED

    async def call(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        """
        Execute a function through the circuit breaker.

        Args:
            func: Async function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result of the function

        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Any exception raised by func
        """
        async with self._lock:
            # Check if we should attempt recovery
            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    logger.info(f"Circuit breaker '{self.name}' entering HALF_OPEN state for recovery test")
                    self._state = CircuitState.HALF_OPEN
                    self._success_count = 0
                else:
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker '{self.name}' is open",
                        context={
                            "name": self.name,
                            "failure_count": self._failure_count,
                            "retry_after": self._time_until_retry()
                        }
                    )

        # Execute the operation
        try:
            # Add timeout to prevent hanging
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.timeout
            )
            await self._on_success()
            return result
        except asyncio.TimeoutError as e:
            logger.warning(f"Circuit breaker '{self.name}' operation timed out after {self.timeout}s")
            await self._on_failure(e)
            raise
        except Exception as e:
            await self._on_failure(e)
            raise

    async def _on_success(self):
        """Handle successful operation."""
        async with self._lock:
            self._failure_count = 0

            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                logger.debug(
                    f"Circuit breaker '{self.name}' success in HALF_OPEN "
                    f"({self._success_count}/{self.success_threshold})"
                )

                if self._success_count >= self.success_threshold:
                    logger.info(f"Circuit breaker '{self.name}' closing after successful recovery")
                    self._state = CircuitState.CLOSED
                    self._success_count = 0

    async def _on_failure(self, exception: Exception):
        """Handle failed operation."""
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            logger.warning(
                f"Circuit breaker '{self.name}' failure "
                f"({self._failure_count}/{self.failure_threshold}): {str(exception)}"
            )

            if self._state == CircuitState.HALF_OPEN:
                # Failed during recovery test, go back to OPEN
                logger.warning(f"Circuit breaker '{self.name}' failed recovery test, reopening")
                self._state = CircuitState.OPEN
                self._success_count = 0

            elif self._failure_count >= self.failure_threshold:
                # Threshold reached, open the circuit
                logger.error(
                    f"Circuit breaker '{self.name}' OPENING after {self._failure_count} failures. "
                    f"Will retry in {self.recovery_timeout}s"
                )
                self._state = CircuitState.OPEN

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self._last_failure_time is None:
            return False
        return time.time() - self._last_failure_time >= self.recovery_timeout

    def _time_until_retry(self) -> float:
        """Calculate seconds until retry is allowed."""
        if self._last_failure_time is None:
            return 0.0
        elapsed = time.time() - self._last_failure_time
        remaining = max(0.0, self.recovery_timeout - elapsed)
        return remaining

    async def reset(self):
        """Manually reset the circuit breaker to CLOSED state."""
        async with self._lock:
            logger.info(f"Circuit breaker '{self.name}' manually reset to CLOSED")
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None

    def get_stats(self) -> dict:
        """
        Get circuit breaker statistics.

        Returns:
            Dict with state, failure count, etc.
        """
        return {
            "name": self.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "time_until_retry": self._time_until_retry() if self.is_open else 0.0
        }


class CircuitBreakerManager:
    """
    Manager for multiple circuit breakers.

    Provides a central place to access and manage circuit breakers
    for different services (e.g., one per MCP server).
    """

    def __init__(self):
        """Initialize circuit breaker manager."""
        self._breakers: dict[str, CircuitBreaker] = {}

    def get_breaker(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        success_threshold: int = 2,
        timeout: float = 30.0
    ) -> CircuitBreaker:
        """
        Get or create a circuit breaker by name.

        Args:
            name: Unique name for the circuit breaker
            failure_threshold: Number of failures before opening
            recovery_timeout: Seconds to wait before recovery test
            success_threshold: Successes needed to close from half-open
            timeout: Operation timeout in seconds

        Returns:
            CircuitBreaker instance
        """
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                success_threshold=success_threshold,
                timeout=timeout
            )
        return self._breakers[name]

    async def reset_all(self):
        """Reset all circuit breakers to CLOSED state."""
        for breaker in self._breakers.values():
            await breaker.reset()

    def get_all_stats(self) -> dict[str, dict]:
        """
        Get statistics for all circuit breakers.

        Returns:
            Dict mapping breaker names to their stats
        """
        return {
            name: breaker.get_stats()
            for name, breaker in self._breakers.items()
        }


# Global circuit breaker manager instance
_global_manager: Optional[CircuitBreakerManager] = None


def get_circuit_breaker_manager() -> CircuitBreakerManager:
    """
    Get the global circuit breaker manager instance.

    Returns:
        CircuitBreakerManager singleton
    """
    global _global_manager
    if _global_manager is None:
        _global_manager = CircuitBreakerManager()
    return _global_manager


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    success_threshold: int = 2,
    timeout: float = 30.0
):
    """
    Decorator to protect an async function with a circuit breaker.

    Args:
        name: Name for this circuit breaker
        failure_threshold: Failures before opening circuit
        recovery_timeout: Seconds before recovery test
        success_threshold: Successes to close from half-open
        timeout: Operation timeout in seconds

    Example:
        @circuit_breaker("mcp_server", failure_threshold=3)
        async def call_mcp_server():
            return await make_request()
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            manager = get_circuit_breaker_manager()
            breaker = manager.get_breaker(
                name=name,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                success_threshold=success_threshold,
                timeout=timeout
            )
            return await breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator
