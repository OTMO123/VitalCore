"""
Monitoring and metrics module for IRIS API Integration System.
"""

import time
import functools
from typing import Dict, Any, Callable, Optional
from collections import defaultdict, Counter
from datetime import datetime
import structlog

logger = structlog.get_logger()


class MetricsCollector:
    """Simple metrics collector for monitoring system performance."""
    
    def __init__(self):
        self.counters = Counter()
        self.gauges = {}
        self.histograms = defaultdict(list)
        self.timers = {}
        
    def increment(self, metric_name: str, value: int = 1, tags: Optional[Dict[str, str]] = None):
        """Increment a counter metric."""
        key = self._build_key(metric_name, tags)
        self.counters[key] += value
        
    def set_gauge(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Set a gauge metric."""
        key = self._build_key(metric_name, tags)
        self.gauges[key] = value
        
    def record_histogram(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a value in histogram."""
        key = self._build_key(metric_name, tags)
        self.histograms[key].append(value)
        
    def start_timer(self, metric_name: str, tags: Optional[Dict[str, str]] = None) -> str:
        """Start a timer and return timer ID."""
        timer_id = f"{metric_name}_{time.time()}"
        key = self._build_key(metric_name, tags)
        self.timers[timer_id] = {
            'key': key,
            'start_time': time.time(),
            'tags': tags or {}
        }
        return timer_id
        
    def stop_timer(self, timer_id: str):
        """Stop timer and record duration."""
        if timer_id in self.timers:
            timer_info = self.timers.pop(timer_id)
            duration = time.time() - timer_info['start_time']
            self.record_histogram(timer_info['key'], duration)
            return duration
        return None
        
    def _build_key(self, metric_name: str, tags: Optional[Dict[str, str]] = None) -> str:
        """Build metric key with tags."""
        if tags:
            tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
            return f"{metric_name},{tag_str}"
        return metric_name
        
    def track_operation(self, operation_name: str):
        """Decorator to track operation metrics."""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                timer_id = self.start_timer(f"operation_duration", {
                    'operation': operation_name
                })
                
                try:
                    result = await func(*args, **kwargs)
                    self.increment(f"operation_calls", tags={
                        'operation': operation_name,
                        'status': 'success'
                    })
                    return result
                except Exception as e:
                    self.increment(f"operation_calls", tags={
                        'operation': operation_name,
                        'status': 'error',
                        'error_type': e.__class__.__name__
                    })
                    raise
                finally:
                    self.stop_timer(timer_id)
            
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                timer_id = self.start_timer(f"operation_duration", {
                    'operation': operation_name
                })
                
                try:
                    result = func(*args, **kwargs)
                    self.increment(f"operation_calls", tags={
                        'operation': operation_name,
                        'status': 'success'
                    })
                    return result
                except Exception as e:
                    self.increment(f"operation_calls", tags={
                        'operation': operation_name,
                        'status': 'error',
                        'error_type': e.__class__.__name__
                    })
                    raise
                finally:
                    self.stop_timer(timer_id)
            
            # Return appropriate wrapper based on function type
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
                
        return decorator
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics."""
        histogram_summary = {}
        for key, values in self.histograms.items():
            if values:
                histogram_summary[key] = {
                    'count': len(values),
                    'min': min(values),
                    'max': max(values),
                    'avg': sum(values) / len(values)
                }
                
        return {
            'counters': dict(self.counters),
            'gauges': self.gauges,
            'histograms': histogram_summary,
            'active_timers': len(self.timers)
        }


def trace_method(operation_name: str = None, tags: Optional[Dict[str, str]] = None):
    """
    Decorator to trace method execution time and log performance metrics.
    
    Args:
        operation_name: Custom operation name (defaults to function name)
        tags: Additional tags for metrics
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            
            # Start metrics
            timer_id = metrics.start_timer(f"method_duration", {
                'operation': op_name,
                **(tags or {})
            })
            
            try:
                # Execute function
                result = await func(*args, **kwargs)
                
                # Record success
                metrics.increment("method_calls", tags={
                    'operation': op_name,
                    'status': 'success',
                    **(tags or {})
                })
                
                return result
                
            except Exception as e:
                # Record failure
                metrics.increment("method_calls", tags={
                    'operation': op_name,
                    'status': 'error',
                    'error_type': e.__class__.__name__,
                    **(tags or {})
                })
                
                logger.error(
                    "Method execution failed",
                    operation=op_name,
                    error=str(e),
                    duration=time.time() - start_time
                )
                raise
                
            finally:
                # Stop timer
                duration = metrics.stop_timer(timer_id)
                
                # Log performance
                logger.debug(
                    "Method execution completed",
                    operation=op_name,
                    duration=duration
                )
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            
            # Start metrics
            timer_id = metrics.start_timer(f"method_duration", {
                'operation': op_name,
                **(tags or {})
            })
            
            try:
                # Execute function
                result = func(*args, **kwargs)
                
                # Record success
                metrics.increment("method_calls", tags={
                    'operation': op_name,
                    'status': 'success',
                    **(tags or {})
                })
                
                return result
                
            except Exception as e:
                # Record failure
                metrics.increment("method_calls", tags={
                    'operation': op_name,
                    'status': 'error',
                    'error_type': e.__class__.__name__,
                    **(tags or {})
                })
                
                logger.error(
                    "Method execution failed",
                    operation=op_name,
                    error=str(e),
                    duration=time.time() - start_time
                )
                raise
                
            finally:
                # Stop timer
                duration = metrics.stop_timer(timer_id)
                
                # Log performance
                logger.debug(
                    "Method execution completed",
                    operation=op_name,
                    duration=duration
                )
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
            
    return decorator


def log_performance(operation: str, duration: float, tags: Optional[Dict[str, str]] = None):
    """Log performance metrics for an operation."""
    metrics.record_histogram("operation_duration", duration, {
        'operation': operation,
        **(tags or {})
    })
    
    logger.info(
        "Performance metric recorded",
        operation=operation,
        duration=duration,
        tags=tags
    )


def health_check() -> Dict[str, Any]:
    """Get system health check information."""
    return {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'metrics_summary': metrics.get_metrics_summary(),
        'uptime_seconds': time.time() - _start_time
    }


# Global metrics instance
metrics = MetricsCollector()
_start_time = time.time()

# Import asyncio at the end to avoid circular imports
import asyncio