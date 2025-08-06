"""
Rate limiting utilities for FastAPI endpoints.
Simple in-memory rate limiting for development and testing.
"""

import time
from typing import Dict, Tuple
from collections import defaultdict, deque
from functools import wraps
from fastapi import HTTPException, status, Request
import structlog

logger = structlog.get_logger()

class InMemoryRateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self):
        # Store requests per IP: {ip: deque(timestamps)}
        self.requests: Dict[str, deque] = defaultdict(lambda: deque())
    
    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """
        Check if request is allowed based on rate limit.
        
        Args:
            key: Identifier (usually IP address)
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
            
        Returns:
            True if request is allowed, False otherwise
        """
        now = time.time()
        window_start = now - window_seconds
        
        # Get request timestamps for this key
        timestamps = self.requests[key]
        
        # Remove old timestamps outside the window
        while timestamps and timestamps[0] < window_start:
            timestamps.popleft()
        
        # Check if we're under the limit
        if len(timestamps) < max_requests:
            timestamps.append(now)
            return True
        
        return False

# Global rate limiter instance
rate_limiter = InMemoryRateLimiter()

def rate_limit(max_requests: int = 100, window_seconds: int = 60):
    """
    Rate limiting decorator for FastAPI endpoints.
    
    Args:
        max_requests: Maximum requests allowed per window
        window_seconds: Time window in seconds
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request object
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                # If no request object found, allow the request
                logger.warning("Rate limiter: No request object found, allowing request")
                return await func(*args, **kwargs)
            
            # Get client IP
            client_ip = request.client.host if request.client else "unknown"
            
            # Check rate limit
            if not rate_limiter.is_allowed(client_ip, max_requests, window_seconds):
                logger.warning(
                    "Rate limit exceeded",
                    client_ip=client_ip,
                    max_requests=max_requests,
                    window_seconds=window_seconds,
                    endpoint=request.url.path
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Max {max_requests} requests per {window_seconds} seconds."
                )
            
            # Request is allowed, proceed
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

# Convenience rate limiters for different endpoint types
def rate_limit_strict(func):
    """Strict rate limiting: 10 requests per minute."""
    return rate_limit(max_requests=10, window_seconds=60)(func)

def rate_limit_moderate(func):
    """Moderate rate limiting: 30 requests per minute."""
    return rate_limit(max_requests=30, window_seconds=60)(func)

def rate_limit_generous(func):
    """Generous rate limiting: 100 requests per minute."""
    return rate_limit(max_requests=100, window_seconds=60)(func)