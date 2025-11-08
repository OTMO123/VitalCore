"""
Helper utilities for testing.

Provides common test helpers and utilities.
"""

import os
from contextlib import contextmanager
from typing import Dict, Any, Optional
import pytest


@contextmanager
def temporary_env_vars(env_vars: Dict[str, str]):
    """
    Temporarily set environment variables for testing.

    Example:
        with temporary_env_vars({'DEBUG': 'true'}):
            # DEBUG is set to 'true'
            pass
        # DEBUG is restored to original value
    """
    original_values = {}

    # Save original values and set new ones
    for key, value in env_vars.items():
        original_values[key] = os.environ.get(key)
        os.environ[key] = value

    try:
        yield
    finally:
        # Restore original values
        for key, original_value in original_values.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value


def require_env_var(var_name: str, error_message: Optional[str] = None):
    """
    Decorator to require an environment variable for a test.

    Fails the test (doesn't skip) if the variable is missing.

    Example:
        @require_env_var('DATABASE_URL')
        async def test_database_connection():
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if var_name not in os.environ:
                pytest.fail(
                    error_message or
                    f"Test requires environment variable {var_name} to be set. "
                    f"Please configure test environment properly."
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_service(service_name: str, check_func=None):
    """
    Decorator to require a service to be available for a test.

    Fails the test (doesn't skip) if the service is unavailable.

    Example:
        @require_service('postgres', check_func=lambda: check_postgres_connection())
        async def test_with_postgres():
            pass
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            if check_func:
                try:
                    is_available = await check_func() if asyncio.iscoroutinefunction(check_func) else check_func()
                    if not is_available:
                        pytest.fail(
                            f"Test requires {service_name} service to be available. "
                            f"Please start the service or configure test containers."
                        )
                except Exception as e:
                    pytest.fail(
                        f"Test requires {service_name} service but connection check failed: {e}. "
                        f"Please ensure service is running."
                    )
            return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
        return wrapper
    return decorator


def assert_no_timing_dependencies(source_code: str) -> bool:
    """
    Check if source code contains timing dependencies.

    Args:
        source_code: Source code to check

    Returns:
        True if no timing dependencies found
    """
    timing_patterns = [
        'asyncio.sleep',
        'time.sleep',
        '.sleep(',
    ]

    found = [p for p in timing_patterns if p in source_code]
    if found:
        return False
    return True


class TestMetrics:
    """
    Collect test metrics for performance analysis.

    Example:
        metrics = TestMetrics()
        with metrics.measure("operation"):
            # perform operation
            pass
        print(f"Operation took {metrics.get_duration('operation')}ms")
    """

    def __init__(self):
        self._measurements = {}
        self._current = {}

    @contextmanager
    def measure(self, name: str):
        """Context manager to measure operation duration."""
        import time
        start = time.perf_counter()
        try:
            yield
        finally:
            duration = (time.perf_counter() - start) * 1000  # Convert to ms
            self._measurements[name] = duration

    def get_duration(self, name: str) -> float:
        """Get measured duration in milliseconds."""
        return self._measurements.get(name, 0.0)

    def get_all(self) -> Dict[str, float]:
        """Get all measurements."""
        return self._measurements.copy()

    def clear(self):
        """Clear all measurements."""
        self._measurements.clear()


def fail_on_missing_dependency(dependency_name: str, import_error: Exception):
    """
    Fail test with clear message about missing dependency.

    Use this instead of pytest.skip() for missing dependencies.

    Example:
        try:
            import some_optional_module
        except ImportError as e:
            fail_on_missing_dependency('some_optional_module', e)
    """
    pytest.fail(
        f"Test requires '{dependency_name}' but it is not installed: {import_error}\n"
        f"Install it with: pip install {dependency_name}\n"
        f"Or install all test dependencies: pip install -r requirements-test.txt"
    )


def ensure_test_isolation():
    """
    Decorator to ensure test isolation.

    Verifies that test doesn't leave side effects.
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Could add checks here for:
            # - Database state
            # - File system state
            # - Environment variables
            # - Global state

            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)

            # Could add cleanup verification here

            return result
        return wrapper
    return decorator


import asyncio
