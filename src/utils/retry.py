"""
Retry logic with exponential backoff for handling transient failures.

This module provides decorators and utilities for retrying operations
that may fail due to transient errors (network issues, rate limits, etc.).
"""

import asyncio
import time
from functools import wraps
from typing import Callable, TypeVar, Any, Optional, Tuple, Type
import logging

from ..exceptions import RetryableError, APIRateLimitError, NetworkError

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: Tuple[Type[Exception], ...] = (RetryableError, APIRateLimitError, NetworkError)
    ):
        """
        Initialize retry configuration.

        Args:
            max_attempts: Maximum number of retry attempts
            initial_delay: Initial delay in seconds before first retry
            max_delay: Maximum delay in seconds between retries
            exponential_base: Base for exponential backoff (delay = initial_delay * base^attempt)
            jitter: Whether to add random jitter to avoid thundering herd
            retryable_exceptions: Tuple of exception types that should trigger retry
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for given attempt number using exponential backoff.

        Args:
            attempt: Attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        import random

        # Calculate exponential backoff
        delay = min(
            self.initial_delay * (self.exponential_base ** attempt),
            self.max_delay
        )

        # Add jitter to avoid thundering herd problem
        if self.jitter:
            delay = delay * (0.5 + random.random() * 0.5)

        return delay

    def should_retry(self, exception: Exception) -> bool:
        """
        Determine if an exception should trigger a retry.

        Args:
            exception: The exception that was raised

        Returns:
            True if should retry, False otherwise
        """
        return isinstance(exception, self.retryable_exceptions)


def retry_with_backoff(config: Optional[RetryConfig] = None):
    """
    Decorator for retrying synchronous functions with exponential backoff.

    Args:
        config: RetryConfig instance, or None to use defaults

    Example:
        @retry_with_backoff()
        def connect_to_server():
            # May raise NetworkError
            return make_connection()

        @retry_with_backoff(RetryConfig(max_attempts=5, initial_delay=2.0))
        def fetch_data():
            # Will retry up to 5 times with 2s initial delay
            return api_call()
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    # Check if we should retry this exception
                    if not config.should_retry(e):
                        logger.debug(
                            f"Exception {type(e).__name__} is not retryable, raising immediately"
                        )
                        raise

                    # Check if we have more attempts
                    if attempt < config.max_attempts - 1:
                        delay = config.calculate_delay(attempt)
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{config.max_attempts}): {str(e)}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"{func.__name__} failed after {config.max_attempts} attempts: {str(e)}"
                        )

            # All attempts exhausted, raise the last exception
            raise last_exception

        return wrapper
    return decorator


def async_retry_with_backoff(config: Optional[RetryConfig] = None):
    """
    Decorator for retrying async functions with exponential backoff.

    Args:
        config: RetryConfig instance, or None to use defaults

    Example:
        @async_retry_with_backoff()
        async def connect_to_server():
            # May raise NetworkError
            return await make_connection()

        @async_retry_with_backoff(RetryConfig(max_attempts=5))
        async def fetch_data():
            # Will retry up to 5 times
            return await api_call()
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(config.max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    # Check if we should retry this exception
                    if not config.should_retry(e):
                        logger.debug(
                            f"Exception {type(e).__name__} is not retryable, raising immediately"
                        )
                        raise

                    # Check if we have more attempts
                    if attempt < config.max_attempts - 1:
                        delay = config.calculate_delay(attempt)
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{config.max_attempts}): {str(e)}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"{func.__name__} failed after {config.max_attempts} attempts: {str(e)}"
                        )

            # All attempts exhausted, raise the last exception
            raise last_exception

        return wrapper
    return decorator


async def retry_async_operation(
    operation: Callable[..., Any],
    *args,
    config: Optional[RetryConfig] = None,
    **kwargs
) -> Any:
    """
    Retry an async operation with exponential backoff.

    This is a functional alternative to the decorator for cases where
    you can't use a decorator.

    Args:
        operation: Async callable to retry
        *args: Positional arguments for operation
        config: RetryConfig instance, or None to use defaults
        **kwargs: Keyword arguments for operation

    Returns:
        Result of the operation

    Raises:
        Last exception if all retries fail

    Example:
        result = await retry_async_operation(
            make_api_call,
            "arg1",
            config=RetryConfig(max_attempts=5),
            kwarg1="value"
        )
    """
    if config is None:
        config = RetryConfig()

    last_exception = None

    for attempt in range(config.max_attempts):
        try:
            return await operation(*args, **kwargs)
        except Exception as e:
            last_exception = e

            if not config.should_retry(e):
                raise

            if attempt < config.max_attempts - 1:
                delay = config.calculate_delay(attempt)
                logger.warning(
                    f"Operation failed (attempt {attempt + 1}/{config.max_attempts}): {str(e)}. "
                    f"Retrying in {delay:.2f}s..."
                )
                await asyncio.sleep(delay)

    raise last_exception


def retry_operation(
    operation: Callable[..., T],
    *args,
    config: Optional[RetryConfig] = None,
    **kwargs
) -> T:
    """
    Retry a synchronous operation with exponential backoff.

    This is a functional alternative to the decorator for cases where
    you can't use a decorator.

    Args:
        operation: Callable to retry
        *args: Positional arguments for operation
        config: RetryConfig instance, or None to use defaults
        **kwargs: Keyword arguments for operation

    Returns:
        Result of the operation

    Raises:
        Last exception if all retries fail

    Example:
        result = retry_operation(
            make_api_call,
            "arg1",
            config=RetryConfig(max_attempts=5),
            kwarg1="value"
        )
    """
    if config is None:
        config = RetryConfig()

    last_exception = None

    for attempt in range(config.max_attempts):
        try:
            return operation(*args, **kwargs)
        except Exception as e:
            last_exception = e

            if not config.should_retry(e):
                raise

            if attempt < config.max_attempts - 1:
                delay = config.calculate_delay(attempt)
                logger.warning(
                    f"Operation failed (attempt {attempt + 1}/{config.max_attempts}): {str(e)}. "
                    f"Retrying in {delay:.2f}s..."
                )
                time.sleep(delay)

    raise last_exception
