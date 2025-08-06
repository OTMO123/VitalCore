"""
Circuit Breaker Implementation for API Resilience

Implements circuit breaker pattern for external API calls and internal service protection.
Follows the security architecture requirements for DoS protection and service isolation.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable, Union
from enum import Enum
import structlog
from functools import wraps
import statistics

logger = structlog.get_logger(__name__)


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit tripped, failing fast
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open."""
    
    def __init__(self, service_name: str, state: CircuitState, last_failure_time: Optional[datetime] = None):
        self.service_name = service_name
        self.state = state
        self.last_failure_time = last_failure_time
        super().__init__(f"Circuit breaker for {service_name} is {state.value}")


class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: tuple = (Exception,),
        success_threshold: int = 3,
        timeout: float = 30.0,
        name: Optional[str] = None
    ):
        self.failure_threshold = failure_threshold  # Failures before opening
        self.recovery_timeout = recovery_timeout    # Seconds before attempting recovery
        self.expected_exception = expected_exception  # Exceptions that count as failures
        self.success_threshold = success_threshold  # Successes needed to close from half-open
        self.timeout = timeout                      # Request timeout
        self.name = name or "unnamed_service"


class CircuitBreaker:
    """
    Circuit breaker for protecting services from cascading failures.
    
    Implements the circuit breaker pattern with the following states:
    - CLOSED: Normal operation, all requests pass through
    - OPEN: Circuit tripped, requests fail fast
    - HALF_OPEN: Testing recovery, limited requests allowed
    """
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_success_time: Optional[datetime] = None
        self.response_times: list = []
        self.lock = asyncio.Lock()
        
        # Metrics
        self.total_requests = 0
        self.total_failures = 0
        self.total_successes = 0
        self.total_timeouts = 0
        self.total_circuit_opens = 0
        
        logger.info(
            "Circuit breaker initialized",
            service=self.config.name,
            failure_threshold=self.config.failure_threshold,
            recovery_timeout=self.config.recovery_timeout
        )
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
        
        Returns:
            Function result
        
        Raises:
            CircuitBreakerError: When circuit is open
            TimeoutError: When function times out
            Exception: Original function exceptions
        """
        async with self.lock:
            self.total_requests += 1
            
            # Check circuit state
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    logger.info(
                        "Circuit breaker transitioning to half-open",
                        service=self.config.name
                    )
                else:
                    logger.warning(
                        "Circuit breaker is open, failing fast",
                        service=self.config.name,
                        failure_count=self.failure_count,
                        last_failure=self.last_failure_time.isoformat() if self.last_failure_time else None
                    )
                    raise CircuitBreakerError(
                        self.config.name, 
                        self.state, 
                        self.last_failure_time
                    )
            
            # Execute function with timeout
            start_time = time.time()
            try:
                # Apply timeout if function is async
                if asyncio.iscoroutinefunction(func):
                    result = await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=self.config.timeout
                    )
                else:
                    result = func(*args, **kwargs)
                
                # Record success
                execution_time = time.time() - start_time
                await self._record_success(execution_time)
                
                return result
                
            except asyncio.TimeoutError as e:
                execution_time = time.time() - start_time
                await self._record_timeout(execution_time)
                logger.warning(
                    "Circuit breaker timeout",
                    service=self.config.name,
                    timeout=self.config.timeout,
                    execution_time=execution_time
                )
                raise TimeoutError(f"Function timeout after {self.config.timeout}s") from e
                
            except self.config.expected_exception as e:
                execution_time = time.time() - start_time
                await self._record_failure(execution_time, str(e))
                raise
    
    async def _record_success(self, execution_time: float):
        """Record successful execution."""
        self.total_successes += 1
        self.last_success_time = datetime.utcnow()
        self.response_times.append(execution_time)
        
        # Keep only last 100 response times
        if len(self.response_times) > 100:
            self.response_times = self.response_times[-100:]
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                logger.info(
                    "Circuit breaker closed after successful recovery",
                    service=self.config.name,
                    success_count=self.success_count
                )
        else:
            # Reset failure count on success in closed state
            self.failure_count = 0
        
        logger.debug(
            "Circuit breaker success recorded",
            service=self.config.name,
            execution_time=execution_time,
            state=self.state.value
        )
    
    async def _record_failure(self, execution_time: float, error_msg: str):
        """Record failed execution."""
        self.total_failures += 1
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        logger.warning(
            "Circuit breaker failure recorded",
            service=self.config.name,
            failure_count=self.failure_count,
            execution_time=execution_time,
            error=error_msg,
            state=self.state.value
        )
        
        # Check if we should open the circuit
        if (self.state == CircuitState.CLOSED and 
            self.failure_count >= self.config.failure_threshold):
            self.state = CircuitState.OPEN
            self.total_circuit_opens += 1
            logger.error(
                "Circuit breaker opened due to failures",
                service=self.config.name,
                failure_count=self.failure_count,
                threshold=self.config.failure_threshold
            )
        elif self.state == CircuitState.HALF_OPEN:
            # Return to open state on any failure during half-open
            self.state = CircuitState.OPEN
            logger.warning(
                "Circuit breaker returned to open state during recovery",
                service=self.config.name
            )
    
    async def _record_timeout(self, execution_time: float):
        """Record timeout as failure."""
        self.total_timeouts += 1
        await self._record_failure(execution_time, "timeout")
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if not self.last_failure_time:
            return True
        
        time_since_failure = datetime.utcnow() - self.last_failure_time
        return time_since_failure.total_seconds() >= self.config.recovery_timeout
    
    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state and metrics."""
        avg_response_time = (
            statistics.mean(self.response_times) if self.response_times else 0.0
        )
        
        success_rate = (
            self.total_successes / self.total_requests if self.total_requests > 0 else 0.0
        )
        
        return {
            "service_name": self.config.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "last_success_time": self.last_success_time.isoformat() if self.last_success_time else None,
            "metrics": {
                "total_requests": self.total_requests,
                "total_successes": self.total_successes,
                "total_failures": self.total_failures,
                "total_timeouts": self.total_timeouts,
                "total_circuit_opens": self.total_circuit_opens,
                "success_rate": round(success_rate, 3),
                "average_response_time": round(avg_response_time, 3),
                "current_response_times_count": len(self.response_times)
            },
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "success_threshold": self.config.success_threshold,
                "timeout": self.config.timeout
            }
        }
    
    async def reset(self):
        """Manually reset circuit breaker to closed state."""
        async with self.lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            logger.info(
                "Circuit breaker manually reset",
                service=self.config.name
            )


class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers."""
    
    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._lock = asyncio.Lock()
    
    async def get_breaker(
        self, 
        name: str, 
        config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreaker:
        """Get or create circuit breaker by name."""
        async with self._lock:
            if name not in self._breakers:
                if config is None:
                    config = CircuitBreakerConfig(name=name)
                self._breakers[name] = CircuitBreaker(config)
            
            return self._breakers[name]
    
    async def remove_breaker(self, name: str) -> bool:
        """Remove circuit breaker by name."""
        async with self._lock:
            if name in self._breakers:
                del self._breakers[name]
                return True
            return False
    
    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """Get states of all circuit breakers."""
        return {
            name: breaker.get_state() 
            for name, breaker in self._breakers.items()
        }
    
    async def reset_all(self):
        """Reset all circuit breakers."""
        async with self._lock:
            for breaker in self._breakers.values():
                await breaker.reset()
    
    def get_unhealthy_services(self) -> list:
        """Get list of services with open circuit breakers."""
        return [
            name for name, breaker in self._breakers.items()
            if breaker.state == CircuitState.OPEN
        ]


# Global registry instance
circuit_registry = CircuitBreakerRegistry()


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    expected_exception: tuple = (Exception,),
    success_threshold: int = 3,
    timeout: float = 30.0
):
    """
    Decorator for applying circuit breaker to functions.
    
    Args:
        name: Circuit breaker name
        failure_threshold: Failures before opening circuit
        recovery_timeout: Seconds before attempting recovery
        expected_exception: Exceptions that count as failures
        success_threshold: Successes needed to close circuit
        timeout: Function timeout in seconds
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            config = CircuitBreakerConfig(
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                expected_exception=expected_exception,
                success_threshold=success_threshold,
                timeout=timeout,
                name=name
            )
            
            breaker = await circuit_registry.get_breaker(name, config)
            return await breaker.call(func, *args, **kwargs)
        
        return wrapper
    return decorator


# Pre-configured circuit breakers for common services
async def get_iris_api_breaker() -> CircuitBreaker:
    """Get circuit breaker for IRIS API calls."""
    config = CircuitBreakerConfig(
        name="iris_api",
        failure_threshold=3,
        recovery_timeout=120,
        expected_exception=(Exception,),
        success_threshold=2,
        timeout=30.0
    )
    return await circuit_registry.get_breaker("iris_api", config)


async def get_database_breaker() -> CircuitBreaker:
    """Get circuit breaker for database operations."""
    config = CircuitBreakerConfig(
        name="database",
        failure_threshold=10,
        recovery_timeout=30,
        expected_exception=(Exception,),
        success_threshold=5,
        timeout=10.0
    )
    return await circuit_registry.get_breaker("database", config)


async def get_encryption_breaker() -> CircuitBreaker:
    """Get circuit breaker for encryption operations."""
    config = CircuitBreakerConfig(
        name="encryption_service",
        failure_threshold=15,
        recovery_timeout=60,
        expected_exception=(Exception,),
        success_threshold=3,
        timeout=5.0
    )
    return await circuit_registry.get_breaker("encryption_service", config)


async def get_event_bus_breaker() -> CircuitBreaker:
    """Get circuit breaker for event bus operations."""
    config = CircuitBreakerConfig(
        name="event_bus",
        failure_threshold=20,
        recovery_timeout=45,
        expected_exception=(Exception,),
        success_threshold=5,
        timeout=15.0
    )
    return await circuit_registry.get_breaker("event_bus", config)


# Backward compatibility
CircuitBreakerState = CircuitState
CircuitBreakerOpenError = CircuitBreakerError