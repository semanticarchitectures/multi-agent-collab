"""
Unit tests for retry logic with exponential backoff.

Tests retry functionality including:
- RetryConfig
- Exponential backoff calculation
- Jitter
- Exception filtering
- Sync and async decorators
- Functional retry APIs
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, call

from src.utils.retry import (
    RetryConfig,
    retry_with_backoff,
    async_retry_with_backoff,
    retry_operation,
    retry_async_operation
)
from src.exceptions import RetryableError, APIRateLimitError, NetworkError


class TestRetryConfig:
    """Test RetryConfig class."""

    def test_retry_config_defaults(self):
        """Test default configuration values."""
        config = RetryConfig()

        assert config.max_attempts == 3
        assert config.initial_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True
        assert RetryableError in config.retryable_exceptions
        assert APIRateLimitError in config.retryable_exceptions
        assert NetworkError in config.retryable_exceptions

    def test_retry_config_custom_values(self):
        """Test configuration with custom values."""
        config = RetryConfig(
            max_attempts=5,
            initial_delay=2.0,
            max_delay=30.0,
            exponential_base=3.0,
            jitter=False,
            retryable_exceptions=(ValueError, TypeError)
        )

        assert config.max_attempts == 5
        assert config.initial_delay == 2.0
        assert config.max_delay == 30.0
        assert config.exponential_base == 3.0
        assert config.jitter is False
        assert config.retryable_exceptions == (ValueError, TypeError)

    def test_calculate_delay_without_jitter(self):
        """Test delay calculation without jitter."""
        config = RetryConfig(
            initial_delay=1.0,
            exponential_base=2.0,
            max_delay=60.0,
            jitter=False
        )

        # Attempt 0: 1.0 * 2^0 = 1.0
        assert config.calculate_delay(0) == 1.0

        # Attempt 1: 1.0 * 2^1 = 2.0
        assert config.calculate_delay(1) == 2.0

        # Attempt 2: 1.0 * 2^2 = 4.0
        assert config.calculate_delay(2) == 4.0

        # Attempt 3: 1.0 * 2^3 = 8.0
        assert config.calculate_delay(3) == 8.0

    def test_calculate_delay_with_max_delay(self):
        """Test that delay respects max_delay."""
        config = RetryConfig(
            initial_delay=1.0,
            exponential_base=2.0,
            max_delay=5.0,
            jitter=False
        )

        # Would be 8.0, but capped at 5.0
        assert config.calculate_delay(3) == 5.0

        # Would be 16.0, but capped at 5.0
        assert config.calculate_delay(4) == 5.0

    def test_calculate_delay_with_jitter(self):
        """Test that jitter reduces delay."""
        config = RetryConfig(
            initial_delay=10.0,
            exponential_base=2.0,
            max_delay=60.0,
            jitter=True
        )

        # With jitter, delay should be between 50% and 100% of base delay
        delay = config.calculate_delay(0)
        assert 5.0 <= delay <= 10.0

        delay = config.calculate_delay(1)
        assert 10.0 <= delay <= 20.0

    def test_should_retry_retryable_exception(self):
        """Test that retryable exceptions are identified."""
        config = RetryConfig()

        assert config.should_retry(NetworkError("test"))
        assert config.should_retry(APIRateLimitError("test"))
        assert config.should_retry(RetryableError("test"))

    def test_should_retry_non_retryable_exception(self):
        """Test that non-retryable exceptions are not retried."""
        config = RetryConfig()

        assert not config.should_retry(ValueError("test"))
        assert not config.should_retry(KeyError("test"))
        assert not config.should_retry(Exception("test"))

    def test_should_retry_custom_exceptions(self):
        """Test should_retry with custom exception list."""
        config = RetryConfig(retryable_exceptions=(ValueError, TypeError))

        assert config.should_retry(ValueError("test"))
        assert config.should_retry(TypeError("test"))
        assert not config.should_retry(KeyError("test"))
        assert not config.should_retry(NetworkError("test"))


class TestRetryWithBackoffDecorator:
    """Test sync retry decorator."""

    def test_retry_success_first_attempt(self):
        """Test successful call on first attempt."""
        mock_func = Mock(return_value="success")

        @retry_with_backoff()
        def test_func():
            return mock_func()

        result = test_func()

        assert result == "success"
        assert mock_func.call_count == 1

    def test_retry_success_after_failures(self):
        """Test success after transient failures."""
        mock_func = Mock(side_effect=[
            NetworkError("fail 1"),
            NetworkError("fail 2"),
            "success"
        ])

        @retry_with_backoff(RetryConfig(initial_delay=0.01))
        def test_func():
            return mock_func()

        result = test_func()

        assert result == "success"
        assert mock_func.call_count == 3

    def test_retry_exhausts_attempts(self):
        """Test that all attempts are exhausted before raising."""
        mock_func = Mock(side_effect=NetworkError("persistent failure"))

        @retry_with_backoff(RetryConfig(max_attempts=3, initial_delay=0.01))
        def test_func():
            return mock_func()

        with pytest.raises(NetworkError, match="persistent failure"):
            test_func()

        assert mock_func.call_count == 3

    def test_retry_non_retryable_exception_raised_immediately(self):
        """Test that non-retryable exceptions are raised immediately."""
        mock_func = Mock(side_effect=ValueError("not retryable"))

        @retry_with_backoff(RetryConfig(max_attempts=3))
        def test_func():
            return mock_func()

        with pytest.raises(ValueError, match="not retryable"):
            test_func()

        # Should only try once
        assert mock_func.call_count == 1

    def test_retry_with_custom_config(self):
        """Test retry with custom configuration."""
        mock_func = Mock(side_effect=[
            ValueError("fail"),
            "success"
        ])

        @retry_with_backoff(RetryConfig(
            max_attempts=5,
            initial_delay=0.01,
            retryable_exceptions=(ValueError,)
        ))
        def test_func():
            return mock_func()

        result = test_func()

        assert result == "success"
        assert mock_func.call_count == 2

    def test_retry_with_arguments(self):
        """Test retry with function arguments."""
        mock_func = Mock(side_effect=[
            NetworkError("fail"),
            "success"
        ])

        @retry_with_backoff(RetryConfig(initial_delay=0.01))
        def test_func(a, b, c=None):
            return mock_func(a, b, c)

        result = test_func(1, 2, c=3)

        assert result == "success"
        mock_func.assert_called_with(1, 2, 3)


class TestAsyncRetryWithBackoffDecorator:
    """Test async retry decorator."""

    @pytest.mark.asyncio
    async def test_async_retry_success_first_attempt(self):
        """Test successful async call on first attempt."""
        async def test_func():
            return "success"

        @async_retry_with_backoff()
        async def wrapped():
            return await test_func()

        result = await wrapped()

        assert result == "success"

    @pytest.mark.asyncio
    async def test_async_retry_success_after_failures(self):
        """Test async success after transient failures."""
        call_count = 0

        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise NetworkError(f"fail {call_count}")
            return "success"

        @async_retry_with_backoff(RetryConfig(initial_delay=0.01))
        async def wrapped():
            return await test_func()

        result = await wrapped()

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_async_retry_exhausts_attempts(self):
        """Test async retry exhausts all attempts."""
        async def test_func():
            raise NetworkError("persistent failure")

        @async_retry_with_backoff(RetryConfig(max_attempts=3, initial_delay=0.01))
        async def wrapped():
            return await test_func()

        with pytest.raises(NetworkError, match="persistent failure"):
            await wrapped()

    @pytest.mark.asyncio
    async def test_async_retry_non_retryable_exception(self):
        """Test async non-retryable exceptions raised immediately."""
        call_count = 0

        async def test_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("not retryable")

        @async_retry_with_backoff(RetryConfig(max_attempts=3))
        async def wrapped():
            return await test_func()

        with pytest.raises(ValueError, match="not retryable"):
            await wrapped()

        assert call_count == 1

    @pytest.mark.asyncio
    async def test_async_retry_with_arguments(self):
        """Test async retry with function arguments."""
        results = []

        async def test_func(a, b, c=None):
            results.append((a, b, c))
            if len(results) < 2:
                raise NetworkError("fail")
            return "success"

        @async_retry_with_backoff(RetryConfig(initial_delay=0.01))
        async def wrapped(a, b, c=None):
            return await test_func(a, b, c)

        result = await wrapped(1, 2, c=3)

        assert result == "success"
        assert results == [(1, 2, 3), (1, 2, 3)]


class TestRetryOperation:
    """Test functional sync retry API."""

    def test_retry_operation_success(self):
        """Test retry_operation with successful call."""
        mock_func = Mock(return_value="success")

        result = retry_operation(mock_func, "arg1", kwarg1="val1")

        assert result == "success"
        mock_func.assert_called_once_with("arg1", kwarg1="val1")

    def test_retry_operation_with_failures(self):
        """Test retry_operation with transient failures."""
        mock_func = Mock(side_effect=[
            NetworkError("fail 1"),
            NetworkError("fail 2"),
            "success"
        ])

        result = retry_operation(
            mock_func,
            config=RetryConfig(initial_delay=0.01)
        )

        assert result == "success"
        assert mock_func.call_count == 3

    def test_retry_operation_exhausts_attempts(self):
        """Test retry_operation exhausts all attempts."""
        mock_func = Mock(side_effect=NetworkError("persistent"))

        with pytest.raises(NetworkError, match="persistent"):
            retry_operation(
                mock_func,
                config=RetryConfig(max_attempts=3, initial_delay=0.01)
            )

        assert mock_func.call_count == 3

    def test_retry_operation_non_retryable(self):
        """Test retry_operation with non-retryable exception."""
        mock_func = Mock(side_effect=ValueError("not retryable"))

        with pytest.raises(ValueError, match="not retryable"):
            retry_operation(mock_func)

        assert mock_func.call_count == 1

    def test_retry_operation_default_config(self):
        """Test retry_operation with default config."""
        mock_func = Mock(side_effect=[NetworkError("fail"), "success"])

        result = retry_operation(mock_func)

        assert result == "success"


class TestRetryAsyncOperation:
    """Test functional async retry API."""

    @pytest.mark.asyncio
    async def test_retry_async_operation_success(self):
        """Test retry_async_operation with successful call."""
        async def test_func(arg1, kwarg1=None):
            return f"{arg1}-{kwarg1}"

        result = await retry_async_operation(
            test_func,
            "arg1",
            kwarg1="val1"
        )

        assert result == "arg1-val1"

    @pytest.mark.asyncio
    async def test_retry_async_operation_with_failures(self):
        """Test retry_async_operation with transient failures."""
        call_count = 0

        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise NetworkError(f"fail {call_count}")
            return "success"

        result = await retry_async_operation(
            test_func,
            config=RetryConfig(initial_delay=0.01)
        )

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_async_operation_exhausts_attempts(self):
        """Test retry_async_operation exhausts all attempts."""
        async def test_func():
            raise NetworkError("persistent")

        with pytest.raises(NetworkError, match="persistent"):
            await retry_async_operation(
                test_func,
                config=RetryConfig(max_attempts=3, initial_delay=0.01)
            )

    @pytest.mark.asyncio
    async def test_retry_async_operation_non_retryable(self):
        """Test retry_async_operation with non-retryable exception."""
        call_count = 0

        async def test_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("not retryable")

        with pytest.raises(ValueError, match="not retryable"):
            await retry_async_operation(test_func)

        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_async_operation_default_config(self):
        """Test retry_async_operation with default config."""
        call_count = 0

        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise NetworkError("fail")
            return "success"

        result = await retry_async_operation(test_func)

        assert result == "success"


class TestRetryTimings:
    """Test retry timing behavior."""

    @patch('time.sleep')
    def test_retry_respects_delay(self, mock_sleep):
        """Test that retry delays are respected."""
        mock_func = Mock(side_effect=[
            NetworkError("fail 1"),
            NetworkError("fail 2"),
            "success"
        ])

        @retry_with_backoff(RetryConfig(
            initial_delay=1.0,
            exponential_base=2.0,
            jitter=False,
            max_attempts=3
        ))
        def test_func():
            return mock_func()

        result = test_func()

        assert result == "success"
        # Should sleep 1.0s after first failure, 2.0s after second
        assert mock_sleep.call_count == 2
        calls = mock_sleep.call_args_list
        assert calls[0][0][0] == 1.0
        assert calls[1][0][0] == 2.0

    @pytest.mark.asyncio
    async def test_async_retry_respects_delay(self):
        """Test that async retry delays are respected."""
        delays = []

        # Patch asyncio.sleep to capture delays
        original_sleep = asyncio.sleep

        async def mock_sleep(delay):
            delays.append(delay)
            await original_sleep(0)  # Actually sleep for 0 to yield

        call_count = 0

        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise NetworkError(f"fail {call_count}")
            return "success"

        with patch('asyncio.sleep', side_effect=mock_sleep):
            @async_retry_with_backoff(RetryConfig(
                initial_delay=1.0,
                exponential_base=2.0,
                jitter=False,
                max_attempts=3
            ))
            async def wrapped():
                return await test_func()

            result = await wrapped()

        assert result == "success"
        assert len(delays) == 2
        assert delays[0] == 1.0
        assert delays[1] == 2.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
