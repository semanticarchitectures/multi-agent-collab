"""
Unit tests for circuit breaker pattern.

Tests circuit breaker functionality including:
- State transitions (CLOSED → OPEN → HALF_OPEN → CLOSED)
- Failure threshold handling
- Recovery timeout
- Success threshold
- CircuitBreakerManager
- Global manager singleton
- Decorator usage
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch

from src.utils.circuit_breaker import (
    CircuitState,
    CircuitBreaker,
    CircuitBreakerManager,
    get_circuit_breaker_manager,
    circuit_breaker
)
from src.exceptions import CircuitBreakerOpenError


class TestCircuitState:
    """Test CircuitState enum."""

    def test_circuit_state_values(self):
        """Test circuit state enum values."""
        assert CircuitState.CLOSED.value == "closed"
        assert CircuitState.OPEN.value == "open"
        assert CircuitState.HALF_OPEN.value == "half_open"


class TestCircuitBreakerInitialization:
    """Test CircuitBreaker initialization."""

    def test_circuit_breaker_defaults(self):
        """Test default configuration."""
        breaker = CircuitBreaker(name="test")

        assert breaker.name == "test"
        assert breaker.failure_threshold == 5
        assert breaker.recovery_timeout == 60.0
        assert breaker.success_threshold == 2
        assert breaker.timeout == 30.0
        assert breaker.state == CircuitState.CLOSED
        assert breaker.is_closed is True
        assert breaker.is_open is False

    def test_circuit_breaker_custom_values(self):
        """Test custom configuration."""
        breaker = CircuitBreaker(
            name="custom",
            failure_threshold=3,
            recovery_timeout=30.0,
            success_threshold=1,
            timeout=10.0
        )

        assert breaker.name == "custom"
        assert breaker.failure_threshold == 3
        assert breaker.recovery_timeout == 30.0
        assert breaker.success_threshold == 1
        assert breaker.timeout == 10.0


class TestCircuitBreakerStates:
    """Test circuit breaker state properties."""

    def test_state_property(self):
        """Test state property."""
        breaker = CircuitBreaker("test")
        assert breaker.state == CircuitState.CLOSED

    def test_is_closed_property(self):
        """Test is_closed property."""
        breaker = CircuitBreaker("test")
        assert breaker.is_closed is True

        breaker._state = CircuitState.OPEN
        assert breaker.is_closed is False

    def test_is_open_property(self):
        """Test is_open property."""
        breaker = CircuitBreaker("test")
        assert breaker.is_open is False

        breaker._state = CircuitState.OPEN
        assert breaker.is_open is True


class TestCircuitBreakerSuccess:
    """Test successful operations."""

    @pytest.mark.asyncio
    async def test_successful_call_in_closed_state(self):
        """Test successful call when circuit is closed."""
        breaker = CircuitBreaker("test")

        async def successful_func():
            return "success"

        result = await breaker.call(successful_func)

        assert result == "success"
        assert breaker.state == CircuitState.CLOSED
        assert breaker._failure_count == 0

    @pytest.mark.asyncio
    async def test_successful_call_with_arguments(self):
        """Test successful call with arguments."""
        breaker = CircuitBreaker("test")

        async def func_with_args(a, b, c=None):
            return f"{a}-{b}-{c}"

        result = await breaker.call(func_with_args, "x", "y", c="z")

        assert result == "x-y-z"


class TestCircuitBreakerFailures:
    """Test failure handling."""

    @pytest.mark.asyncio
    async def test_single_failure_doesnt_open_circuit(self):
        """Test that single failure doesn't open circuit."""
        breaker = CircuitBreaker("test", failure_threshold=3)

        async def failing_func():
            raise ValueError("test error")

        with pytest.raises(ValueError):
            await breaker.call(failing_func)

        assert breaker.state == CircuitState.CLOSED
        assert breaker._failure_count == 1

    @pytest.mark.asyncio
    async def test_multiple_failures_open_circuit(self):
        """Test that multiple failures open circuit."""
        breaker = CircuitBreaker("test", failure_threshold=3)

        async def failing_func():
            raise ValueError("test error")

        # Fail 3 times to reach threshold
        for i in range(3):
            with pytest.raises(ValueError):
                await breaker.call(failing_func)

        assert breaker.state == CircuitState.OPEN
        assert breaker._failure_count == 3

    @pytest.mark.asyncio
    async def test_open_circuit_blocks_requests(self):
        """Test that open circuit blocks requests."""
        breaker = CircuitBreaker("test", failure_threshold=2)

        async def failing_func():
            raise ValueError("test error")

        # Fail twice to open circuit
        for i in range(2):
            with pytest.raises(ValueError):
                await breaker.call(failing_func)

        assert breaker.state == CircuitState.OPEN

        # Next call should be blocked
        async def any_func():
            return "success"

        with pytest.raises(CircuitBreakerOpenError, match="is open"):
            await breaker.call(any_func)

    @pytest.mark.asyncio
    async def test_success_resets_failure_count(self):
        """Test that success resets failure count."""
        breaker = CircuitBreaker("test", failure_threshold=3)

        async def failing_func():
            raise ValueError("test error")

        async def success_func():
            return "success"

        # Fail once
        with pytest.raises(ValueError):
            await breaker.call(failing_func)

        assert breaker._failure_count == 1

        # Succeed
        await breaker.call(success_func)

        assert breaker._failure_count == 0
        assert breaker.state == CircuitState.CLOSED


class TestCircuitBreakerRecovery:
    """Test circuit recovery (HALF_OPEN state)."""

    @pytest.mark.asyncio
    async def test_recovery_after_timeout(self):
        """Test transition to HALF_OPEN after timeout."""
        breaker = CircuitBreaker(
            "test",
            failure_threshold=2,
            recovery_timeout=0.1  # Short timeout for testing
        )

        async def failing_func():
            raise ValueError("test error")

        # Open the circuit
        for i in range(2):
            with pytest.raises(ValueError):
                await breaker.call(failing_func)

        assert breaker.state == CircuitState.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(0.15)

        # Next call should transition to HALF_OPEN
        async def success_func():
            return "success"

        result = await breaker.call(success_func)

        assert result == "success"
        assert breaker.state == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_successful_recovery_closes_circuit(self):
        """Test that successful recovery closes circuit."""
        breaker = CircuitBreaker(
            "test",
            failure_threshold=2,
            recovery_timeout=0.1,
            success_threshold=2  # Need 2 successes
        )

        async def failing_func():
            raise ValueError("test error")

        # Open the circuit
        for i in range(2):
            with pytest.raises(ValueError):
                await breaker.call(failing_func)

        assert breaker.state == CircuitState.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(0.15)

        async def success_func():
            return "success"

        # First success - should be in HALF_OPEN
        result1 = await breaker.call(success_func)
        assert breaker.state == CircuitState.HALF_OPEN

        # Second success - should close circuit
        result2 = await breaker.call(success_func)
        assert breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_failed_recovery_reopens_circuit(self):
        """Test that failed recovery reopens circuit."""
        breaker = CircuitBreaker(
            "test",
            failure_threshold=2,
            recovery_timeout=0.1
        )

        async def failing_func():
            raise ValueError("test error")

        # Open the circuit
        for i in range(2):
            with pytest.raises(ValueError):
                await breaker.call(failing_func)

        assert breaker.state == CircuitState.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(0.15)

        # Fail during recovery test - should reopen
        with pytest.raises(ValueError):
            await breaker.call(failing_func)

        assert breaker.state == CircuitState.OPEN


class TestCircuitBreakerTimeout:
    """Test operation timeout handling."""

    @pytest.mark.asyncio
    async def test_timeout_triggers_failure(self):
        """Test that timeout is treated as failure."""
        breaker = CircuitBreaker("test", timeout=0.1, failure_threshold=2)

        async def slow_func():
            await asyncio.sleep(1.0)  # Will timeout
            return "never reached"

        # First timeout
        with pytest.raises(asyncio.TimeoutError):
            await breaker.call(slow_func)

        assert breaker._failure_count == 1

        # Second timeout should open circuit
        with pytest.raises(asyncio.TimeoutError):
            await breaker.call(slow_func)

        assert breaker.state == CircuitState.OPEN


class TestCircuitBreakerReset:
    """Test manual circuit reset."""

    @pytest.mark.asyncio
    async def test_manual_reset(self):
        """Test manually resetting circuit."""
        breaker = CircuitBreaker("test", failure_threshold=2)

        async def failing_func():
            raise ValueError("test error")

        # Open the circuit
        for i in range(2):
            with pytest.raises(ValueError):
                await breaker.call(failing_func)

        assert breaker.state == CircuitState.OPEN
        assert breaker._failure_count == 2

        # Reset manually
        await breaker.reset()

        assert breaker.state == CircuitState.CLOSED
        assert breaker._failure_count == 0
        assert breaker._success_count == 0
        assert breaker._last_failure_time is None


class TestCircuitBreakerStats:
    """Test circuit breaker statistics."""

    def test_get_stats_closed(self):
        """Test stats when circuit is closed."""
        breaker = CircuitBreaker("test")

        stats = breaker.get_stats()

        assert stats["name"] == "test"
        assert stats["state"] == "closed"
        assert stats["failure_count"] == 0
        assert stats["success_count"] == 0
        assert stats["time_until_retry"] == 0.0

    @pytest.mark.asyncio
    async def test_get_stats_open(self):
        """Test stats when circuit is open."""
        breaker = CircuitBreaker("test", failure_threshold=1)

        async def failing_func():
            raise ValueError("test error")

        with pytest.raises(ValueError):
            await breaker.call(failing_func)

        stats = breaker.get_stats()

        assert stats["name"] == "test"
        assert stats["state"] == "open"
        assert stats["failure_count"] == 1
        assert stats["time_until_retry"] > 0


class TestCircuitBreakerManager:
    """Test CircuitBreakerManager."""

    def test_manager_initialization(self):
        """Test manager initialization."""
        manager = CircuitBreakerManager()
        assert len(manager._breakers) == 0

    def test_get_breaker_creates_new(self):
        """Test getting breaker creates new instance."""
        manager = CircuitBreakerManager()

        breaker = manager.get_breaker("test1")

        assert breaker.name == "test1"
        assert "test1" in manager._breakers

    def test_get_breaker_returns_existing(self):
        """Test getting breaker returns existing instance."""
        manager = CircuitBreakerManager()

        breaker1 = manager.get_breaker("test1")
        breaker2 = manager.get_breaker("test1")

        assert breaker1 is breaker2

    def test_get_breaker_custom_config(self):
        """Test getting breaker with custom config."""
        manager = CircuitBreakerManager()

        breaker = manager.get_breaker(
            "test1",
            failure_threshold=3,
            recovery_timeout=30.0
        )

        assert breaker.failure_threshold == 3
        assert breaker.recovery_timeout == 30.0

    @pytest.mark.asyncio
    async def test_reset_all(self):
        """Test resetting all breakers."""
        manager = CircuitBreakerManager()

        breaker1 = manager.get_breaker("test1", failure_threshold=1)
        breaker2 = manager.get_breaker("test2", failure_threshold=1)

        async def failing_func():
            raise ValueError("test")

        # Open both circuits
        with pytest.raises(ValueError):
            await breaker1.call(failing_func)
        with pytest.raises(ValueError):
            await breaker2.call(failing_func)

        assert breaker1.state == CircuitState.OPEN
        assert breaker2.state == CircuitState.OPEN

        # Reset all
        await manager.reset_all()

        assert breaker1.state == CircuitState.CLOSED
        assert breaker2.state == CircuitState.CLOSED

    def test_get_all_stats(self):
        """Test getting stats for all breakers."""
        manager = CircuitBreakerManager()

        breaker1 = manager.get_breaker("test1")
        breaker2 = manager.get_breaker("test2")

        stats = manager.get_all_stats()

        assert "test1" in stats
        assert "test2" in stats
        assert stats["test1"]["name"] == "test1"
        assert stats["test2"]["name"] == "test2"


class TestGlobalManager:
    """Test global circuit breaker manager."""

    def test_get_global_manager_singleton(self):
        """Test global manager is singleton."""
        manager1 = get_circuit_breaker_manager()
        manager2 = get_circuit_breaker_manager()

        assert manager1 is manager2

    def test_global_manager_persistence(self):
        """Test global manager persists breakers."""
        manager = get_circuit_breaker_manager()

        breaker1 = manager.get_breaker("persistent")

        # Get manager again
        manager2 = get_circuit_breaker_manager()
        breaker2 = manager2.get_breaker("persistent")

        assert breaker1 is breaker2


class TestCircuitBreakerDecorator:
    """Test circuit breaker decorator."""

    @pytest.mark.asyncio
    async def test_decorator_protects_function(self):
        """Test decorator protects function."""
        call_count = 0

        @circuit_breaker("test_decorator", failure_threshold=2)
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("fail")
            return "success"

        # First two calls should fail and open circuit
        with pytest.raises(ValueError):
            await test_func()
        with pytest.raises(ValueError):
            await test_func()

        # Third call should be blocked
        with pytest.raises(CircuitBreakerOpenError):
            await test_func()

    @pytest.mark.asyncio
    async def test_decorator_with_arguments(self):
        """Test decorator with function arguments."""
        @circuit_breaker("test_args")
        async def test_func(a, b, c=None):
            return f"{a}-{b}-{c}"

        result = await test_func("x", "y", c="z")
        assert result == "x-y-z"

    @pytest.mark.asyncio
    async def test_decorator_custom_config(self):
        """Test decorator with custom configuration."""
        @circuit_breaker(
            "test_custom",
            failure_threshold=1,
            timeout=0.5
        )
        async def test_func():
            raise ValueError("fail")

        # Single failure should open circuit
        with pytest.raises(ValueError):
            await test_func()

        # Next call should be blocked
        with pytest.raises(CircuitBreakerOpenError):
            await test_func()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
