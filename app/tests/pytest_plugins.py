"""
Custom pytest plugins for enhanced testing capabilities.

This module provides custom pytest plugins for specialized testing needs
including async testing, performance monitoring, and custom assertions.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional
import pytest
from _pytest.config import Config
from _pytest.nodes import Item
from _pytest.reports import TestReport
import structlog

logger = structlog.get_logger()


class AsyncioTimeoutPlugin:
    """Plugin to handle asyncio timeouts in tests."""
    
    def __init__(self, default_timeout: float = 30.0):
        self.default_timeout = default_timeout
    
    @pytest.hookimpl(tryfirst=True)
    def pytest_runtest_setup(self, item: Item) -> None:
        """Setup asyncio timeout for test."""
        if hasattr(item, 'obj') and asyncio.iscoroutinefunction(item.obj):
            timeout_marker = item.get_closest_marker('timeout')
            timeout = timeout_marker.args[0] if timeout_marker else self.default_timeout
            
            # Store timeout in item for later use
            item.timeout = timeout


class PerformanceMonitorPlugin:
    """Plugin to monitor test performance and memory usage."""
    
    def __init__(self):
        self.test_times: Dict[str, float] = {}
        self.slow_tests: List[Dict[str, Any]] = []
        self.memory_usage: Dict[str, int] = {}
    
    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item: Item, call) -> None:
        """Monitor test execution time and performance."""
        outcome = yield
        report: TestReport = outcome.get_result()
        
        if call.when == "call":
            # Record test execution time
            test_name = item.nodeid
            duration = report.duration
            self.test_times[test_name] = duration
            
            # Track slow tests (> 5 seconds)
            if duration > 5.0:
                self.slow_tests.append({
                    'name': test_name,
                    'duration': duration,
                    'outcome': report.outcome
                })
    
    def pytest_sessionfinish(self, session, exitstatus) -> None:
        """Report performance statistics at the end of session."""
        if self.slow_tests:
            print(f"\n{'='*50}")
            print("SLOW TESTS DETECTED:")
            print(f"{'='*50}")
            for test in sorted(self.slow_tests, key=lambda x: x['duration'], reverse=True):
                print(f"{test['name']}: {test['duration']:.2f}s ({test['outcome']})")
            print(f"{'='*50}")


class DatabaseStatePlugin:
    """Plugin to ensure database state consistency between tests."""
    
    def __init__(self):
        self.db_states: Dict[str, Any] = {}
    
    @pytest.hookimpl(tryfirst=True)
    def pytest_runtest_setup(self, item: Item) -> None:
        """Check if test requires database state management."""
        if item.get_closest_marker('database'):
            # Store database state before test
            self.db_states[item.nodeid] = self._capture_db_state()
    
    @pytest.hookimpl(trylast=True)
    def pytest_runtest_teardown(self, item: Item, nextitem: Optional[Item]) -> None:
        """Verify database state after test."""
        if item.get_closest_marker('database'):
            # Verify database was properly cleaned up
            current_state = self._capture_db_state()
            expected_state = self.db_states.get(item.nodeid)
            
            if expected_state != current_state:
                logger.warning(
                    "Database state changed after test",
                    test=item.nodeid,
                    expected=expected_state,
                    actual=current_state
                )
    
    def _capture_db_state(self) -> Dict[str, Any]:
        """Capture current database state for comparison."""
        # This would be implemented to capture relevant DB metrics
        # For now, return a placeholder
        return {
            'timestamp': time.time(),
            'connections': 0,  # Would get actual connection count
            'tables': [],      # Would get table names/counts
        }


class SecurityTestPlugin:
    """Plugin for security-focused testing."""
    
    def __init__(self):
        self.security_violations: List[Dict[str, Any]] = []
    
    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_call(self, item: Item) -> None:
        """Monitor for security test failures."""
        outcome = yield
        
        if item.get_closest_marker('security'):
            try:
                outcome.get_result()
            except Exception as e:
                # Log security test failures for analysis
                self.security_violations.append({
                    'test': item.nodeid,
                    'error': str(e),
                    'timestamp': time.time()
                })
                logger.warning(
                    "Security test failed",
                    test=item.nodeid,
                    error=str(e)
                )
    
    def pytest_sessionfinish(self, session, exitstatus) -> None:
        """Report security test results."""
        if self.security_violations:
            print(f"\n{'='*50}")
            print("SECURITY TEST VIOLATIONS:")
            print(f"{'='*50}")
            for violation in self.security_violations:
                print(f"Test: {violation['test']}")
                print(f"Error: {violation['error']}")
                print("-" * 50)


class APITestPlugin:
    """Plugin for API testing enhancements."""
    
    def __init__(self):
        self.api_calls: List[Dict[str, Any]] = []
        self.response_times: Dict[str, List[float]] = {}
    
    def record_api_call(self, method: str, endpoint: str, status_code: int, 
                       response_time: float, test_name: str) -> None:
        """Record API call metrics."""
        call_data = {
            'method': method,
            'endpoint': endpoint,
            'status_code': status_code,
            'response_time': response_time,
            'test_name': test_name,
            'timestamp': time.time()
        }
        self.api_calls.append(call_data)
        
        # Track response times by endpoint
        key = f"{method} {endpoint}"
        if key not in self.response_times:
            self.response_times[key] = []
        self.response_times[key].append(response_time)
    
    def pytest_sessionfinish(self, session, exitstatus) -> None:
        """Report API test statistics."""
        if self.api_calls:
            print(f"\n{'='*50}")
            print("API TEST STATISTICS:")
            print(f"{'='*50}")
            
            # Calculate average response times
            for endpoint, times in self.response_times.items():
                avg_time = sum(times) / len(times)
                max_time = max(times)
                min_time = min(times)
                print(f"{endpoint}:")
                print(f"  Calls: {len(times)}")
                print(f"  Avg Response Time: {avg_time:.3f}s")
                print(f"  Min Response Time: {min_time:.3f}s")
                print(f"  Max Response Time: {max_time:.3f}s")
                print("-" * 30)


# Register plugins
def pytest_configure(config: Config) -> None:
    """Configure custom plugins."""
    config.pluginmanager.register(AsyncioTimeoutPlugin(), "asyncio_timeout")
    config.pluginmanager.register(PerformanceMonitorPlugin(), "performance_monitor")
    config.pluginmanager.register(DatabaseStatePlugin(), "database_state")
    config.pluginmanager.register(SecurityTestPlugin(), "security_test")
    config.pluginmanager.register(APITestPlugin(), "api_test")


# Custom assertions
def assert_response_time(response_time: float, max_time: float = 1.0) -> None:
    """Assert API response time is within acceptable limits."""
    assert response_time <= max_time, f"Response time {response_time:.3f}s exceeds limit {max_time}s"


def assert_no_security_headers_missing(headers: Dict[str, str]) -> None:
    """Assert that required security headers are present."""
    required_headers = [
        'X-Content-Type-Options',
        'X-Frame-Options',
        'X-XSS-Protection',
        'Strict-Transport-Security'
    ]
    
    missing_headers = [h for h in required_headers if h not in headers]
    assert not missing_headers, f"Missing security headers: {missing_headers}"


def assert_audit_log_created(event_type: str, user_id: str, audit_logs: List[Any]) -> None:
    """Assert that an audit log entry was created for an event."""
    matching_logs = [
        log for log in audit_logs 
        if log.event_type == event_type and log.user_id == user_id
    ]
    assert matching_logs, f"No audit log found for event {event_type} by user {user_id}"


def assert_database_consistency(db_session, model_class, expected_count: int) -> None:
    """Assert database consistency after operations."""
    actual_count = db_session.query(model_class).count()
    assert actual_count == expected_count, \
        f"Expected {expected_count} {model_class.__name__} records, found {actual_count}"


# Make custom assertions available
pytest.assert_response_time = assert_response_time
pytest.assert_no_security_headers_missing = assert_no_security_headers_missing
pytest.assert_audit_log_created = assert_audit_log_created
pytest.assert_database_consistency = assert_database_consistency