"""
Event utilities for reliable async event testing.

Provides utilities to wait for event completion without timing dependencies.
Replaces unreliable asyncio.sleep() patterns with proper event synchronization.
"""

import asyncio
from typing import Optional, Callable, Any, List
from datetime import datetime, timedelta
import pytest


class EventCollector:
    """
    Collects events for testing without timing dependencies.

    Example:
        collector = EventCollector()
        event_bus.subscribe(EventType.USER_LOGIN, collector.collect)
        await event_bus.publish(event)
        await collector.wait_for_event(timeout=5.0)
        assert len(collector.events) == 1
    """

    def __init__(self):
        self.events: List[Any] = []
        self._event_received = asyncio.Event()
        self._expected_count: Optional[int] = None

    async def collect(self, event: Any) -> None:
        """Collect an event and signal receipt."""
        self.events.append(event)
        if self._expected_count is None or len(self.events) >= self._expected_count:
            self._event_received.set()

    async def wait_for_event(self, timeout: float = 5.0, count: Optional[int] = None) -> bool:
        """
        Wait for event(s) to be collected.

        Args:
            timeout: Maximum time to wait in seconds
            count: Expected number of events (optional)

        Returns:
            True if events received, False if timeout

        Raises:
            asyncio.TimeoutError: If timeout exceeded (configurable)
        """
        self._expected_count = count

        try:
            if count is not None:
                # Wait until we have the expected count
                while len(self.events) < count:
                    self._event_received.clear()
                    await asyncio.wait_for(
                        self._event_received.wait(),
                        timeout=timeout
                    )
            else:
                # Wait for at least one event
                await asyncio.wait_for(
                    self._event_received.wait(),
                    timeout=timeout
                )
            return True
        except asyncio.TimeoutError:
            return False

    def assert_received(self, count: Optional[int] = None, message: Optional[str] = None):
        """Assert that events were received."""
        if count is not None:
            assert len(self.events) == count, \
                message or f"Expected {count} events, got {len(self.events)}"
        else:
            assert len(self.events) > 0, \
                message or "Expected at least one event, got none"

    def clear(self):
        """Clear collected events."""
        self.events.clear()
        self._event_received.clear()


async def wait_for_event(
    event_check: Callable[[], bool],
    timeout: float = 5.0,
    check_interval: float = 0.01,
    error_message: Optional[str] = None
) -> bool:
    """
    Wait for a condition to become true without using sleep.

    Uses exponential backoff for efficient polling.

    Args:
        event_check: Callable that returns True when condition is met
        timeout: Maximum time to wait in seconds
        check_interval: Initial check interval in seconds
        error_message: Custom error message for timeout

    Returns:
        True if condition met, False if timeout

    Example:
        success = await wait_for_event(
            lambda: len(results) > 0,
            timeout=5.0,
            error_message="Results not populated"
        )
        assert success, "Timeout waiting for results"
    """
    start_time = asyncio.get_event_loop().time()
    current_interval = check_interval

    while True:
        if event_check():
            return True

        elapsed = asyncio.get_event_loop().time() - start_time
        if elapsed >= timeout:
            if error_message:
                raise asyncio.TimeoutError(error_message)
            return False

        # Exponential backoff with max interval of 0.1s
        await asyncio.sleep(min(current_interval, 0.1))
        current_interval *= 1.5


async def wait_for_event_with_timeout(
    event: asyncio.Event,
    timeout: float = 5.0,
    error_message: Optional[str] = None
) -> bool:
    """
    Wait for an asyncio.Event with timeout.

    Args:
        event: asyncio.Event to wait for
        timeout: Maximum time to wait in seconds
        error_message: Custom error message for timeout

    Returns:
        True if event set, False if timeout
    """
    try:
        await asyncio.wait_for(event.wait(), timeout=timeout)
        return True
    except asyncio.TimeoutError:
        if error_message:
            raise asyncio.TimeoutError(error_message)
        return False


@pytest.fixture
def event_collector():
    """Pytest fixture for EventCollector."""
    return EventCollector()


@pytest.fixture
def event_completion_fixture():
    """
    Pytest fixture that provides an event completion signal.

    Example:
        async def test_something(event_completion_fixture):
            event, signal_completion = event_completion_fixture

            async def handler():
                # do work
                signal_completion()

            asyncio.create_task(handler())
            await event.wait()  # Wait for completion
    """
    event = asyncio.Event()

    def signal_completion():
        event.set()

    return event, signal_completion


class AsyncContextManager:
    """
    Helper for testing async context managers without timing dependencies.

    Example:
        async with AsyncContextManager(timeout=5.0) as ctx:
            # Perform async operations
            await some_async_operation()
            ctx.mark_complete()
        # Will raise TimeoutError if not marked complete within timeout
    """

    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout
        self._completed = False
        self._task: Optional[asyncio.Task] = None

    async def __aenter__(self):
        self._completed = False
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._task:
            self._task.cancel()

        if not self._completed and exc_type is None:
            # Wait for completion or timeout
            try:
                await asyncio.wait_for(
                    self._wait_for_completion(),
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                raise asyncio.TimeoutError(
                    f"Context manager operation did not complete within {self.timeout}s"
                )

    async def _wait_for_completion(self):
        while not self._completed:
            await asyncio.sleep(0.01)

    def mark_complete(self):
        """Mark the operation as complete."""
        self._completed = True


def assert_no_timing_dependencies(test_func):
    """
    Decorator to assert that a test function does not use timing dependencies.

    This is a development aid to catch accidental use of sleep() in tests.
    """
    import functools
    import inspect

    @functools.wraps(test_func)
    async def wrapper(*args, **kwargs):
        # Check source code for sleep calls
        source = inspect.getsource(test_func)
        timing_patterns = [
            'asyncio.sleep',
            'time.sleep',
            'await sleep',
        ]

        found_patterns = [p for p in timing_patterns if p in source]

        if found_patterns:
            pytest.fail(
                f"Test {test_func.__name__} contains timing dependencies: {found_patterns}\n"
                f"Use event_utils instead of sleep() for reliable testing."
            )

        return await test_func(*args, **kwargs)

    return wrapper
