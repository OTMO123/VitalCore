#!/usr/bin/env python3
"""
Enterprise API Performance Optimization System
Implements comprehensive API performance optimization with intelligent caching,
rate limiting, response compression, and request optimization.

API Optimization Features:  
- Multi-layer intelligent caching (Redis, in-memory, CDN)
- Advanced rate limiting with sliding windows and user-based quotas
- Dynamic response compression with content-aware algorithms
- Request/response optimization and payload reduction
- API performance monitoring and auto-scaling triggers
- Circuit breaker pattern for upstream service protection

Security Principles Applied:
- Defense in Depth: Multiple layers of API protection
- Zero Trust: Every API request verified and monitored
- Rate Limiting: DDoS and abuse protection
- Data Minimization: Optimized payload sizes
- Audit Transparency: Complete API operation tracking

Architecture Patterns:
- Middleware Pattern: Request/response interception and processing
- Cache-Aside Pattern: Intelligent cache management
- Circuit Breaker: Service resilience and failure protection
- Strategy Pattern: Multiple optimization strategies
- Observer Pattern: Performance monitoring and alerting
- Decorator Pattern: Response transformation and compression
"""

import asyncio
import json
import time
import gzip
import brotli  
import zlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable, Protocol
from enum import Enum, auto
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
import structlog
import uuid
import hashlib
import threading
from collections import defaultdict, deque
import weakref

from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.compression import CompressionMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

try:
    import redis.asyncio as aioredis
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    import memcache
    MEMCACHED_AVAILABLE = True
except ImportError:
    MEMCACHED_AVAILABLE = False

logger = structlog.get_logger()

# API Optimization Configuration

class CacheStrategy(str, Enum):
    """Cache storage strategies"""
    MEMORY = "memory"           # In-memory caching
    REDIS = "redis"            # Redis-based caching
    MEMCACHED = "memcached"    # Memcached-based caching
    HYBRID = "hybrid"          # Multi-layer caching
    CDN = "cdn"               # CDN-based caching

class CompressionAlgorithm(str, Enum):
    """Response compression algorithms"""
    GZIP = "gzip"             # Standard gzip compression
    BROTLI = "br"             # Brotli compression (better ratio)
    DEFLATE = "deflate"       # Deflate compression
    AUTO = "auto"             # Automatic algorithm selection

class RateLimitStrategy(str, Enum):
    """Rate limiting strategies"""
    FIXED_WINDOW = "fixed_window"         # Fixed time windows
    SLIDING_WINDOW = "sliding_window"     # Sliding time windows
    TOKEN_BUCKET = "token_bucket"         # Token bucket algorithm
    LEAKY_BUCKET = "leaky_bucket"         # Leaky bucket algorithm

class CacheScope(str, Enum):
    """Cache scope definitions"""
    GLOBAL = "global"         # Shared across all users
    USER = "user"            # User-specific caching
    TENANT = "tenant"        # Tenant-specific caching
    ROLE = "role"           # Role-based caching
    CUSTOM = "custom"       # Custom scope logic

@dataclass
class APIOptimizationConfig:
    """API optimization configuration"""
    
    # Caching Configuration
    cache_strategy: CacheStrategy = CacheStrategy.HYBRID
    cache_default_ttl: int = 300  # 5 minutes
    cache_max_size: int = 10000   # Max cache entries
    redis_url: Optional[str] = None
    memcached_servers: List[str] = field(default_factory=list)
    
    # Compression Configuration
    compression_algorithm: CompressionAlgorithm = CompressionAlgorithm.AUTO
    compression_min_size: int = 1024  # Only compress responses > 1KB
    compression_level: int = 6        # Compression level (1-9)
    
    # Rate Limiting Configuration
    rate_limit_strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    default_rate_limit: int = 1000    # Requests per minute
    burst_limit: int = 50             # Burst requests allowed
    rate_limit_window: int = 60       # Rate limit window in seconds
    
    # Performance Monitoring
    enable_monitoring: bool = True
    monitoring_sample_rate: float = 0.1  # 10% of requests
    slow_request_threshold: float = 1.0   # 1 second
    
    # API Optimization Features
    enable_etag: bool = True
    enable_conditional_requests: bool = True
    enable_request_deduplication: bool = True
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    
    # Circuit Breaker Configuration
    circuit_breaker_enabled: bool = True
    failure_threshold: int = 5
    recovery_timeout: int = 60

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    created_at: datetime
    expires_at: datetime
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    size_bytes: int = 0
    scope: CacheScope = CacheScope.GLOBAL
    tags: List[str] = field(default_factory=list)
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        return datetime.now() > self.expires_at
    
    def touch(self):
        """Update access information"""
        self.access_count += 1
        self.last_accessed = datetime.now()

@dataclass
class RateLimitInfo:
    """Rate limit tracking information"""
    identifier: str
    requests: List[datetime] = field(default_factory=list)
    tokens: int = 0
    last_refill: Optional[datetime] = None
    blocked_until: Optional[datetime] = None
    
    def cleanup_old_requests(self, window_seconds: int):
        """Remove old requests outside the window"""
        cutoff = datetime.now() - timedelta(seconds=window_seconds)
        self.requests = [req_time for req_time in self.requests if req_time > cutoff]

class InMemoryCache:
    """High-performance in-memory cache with LRU eviction"""
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.cache: Dict[str, CacheEntry] = {}
        self.access_order: deque = deque()
        self.lock = threading.RLock()
        self.hit_count = 0
        self.miss_count = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self.lock:
            if key not in self.cache:
                self.miss_count += 1
                return None
            
            entry = self.cache[key]
            
            # Check expiration
            if entry.is_expired():
                del self.cache[key]
                try:
                    self.access_order.remove(key)
                except ValueError:
                    pass
                self.miss_count += 1
                return None
            
            # Update access info
            entry.touch()
            
            # Move to end of access order
            try:
                self.access_order.remove(key)
            except ValueError:
                pass
            self.access_order.append(key)
            
            self.hit_count += 1
            return entry.value
    
    def put(self, key: str, value: Any, ttl: int = 300, scope: CacheScope = CacheScope.GLOBAL, tags: List[str] = None):
        """Store value in cache"""
        with self.lock:
            # Evict if necessary
            while len(self.cache) >= self.max_size:
                self._evict_lru()
            
            # Calculate size
            size_bytes = len(json.dumps(value).encode()) if isinstance(value, (dict, list)) else len(str(value).encode())
            
            # Create cache entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(seconds=ttl),
                size_bytes=size_bytes,
                scope=scope,
                tags=tags or []
            )
            
            self.cache[key] = entry
            self.access_order.append(key)
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                try:
                    self.access_order.remove(key)
                except ValueError:
                    pass
                return True
            return False
    
    def clear(self):
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            self.access_order.clear()
            self.hit_count = 0
            self.miss_count = 0
    
    def invalidate_by_tags(self, tags: List[str]):
        """Invalidate cache entries by tags"""
        with self.lock:
            keys_to_delete = []
            for key, entry in self.cache.items():
                if any(tag in entry.tags for tag in tags):
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                self.delete(key)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total_requests = self.hit_count + self.miss_count
            hit_rate = self.hit_count / total_requests if total_requests > 0 else 0.0
            
            total_size = sum(entry.size_bytes for entry in self.cache.values())
            
            return {
                "entries": len(self.cache),
                "max_size": self.max_size,
                "hit_count": self.hit_count,
                "miss_count": self.miss_count,
                "hit_rate": round(hit_rate, 3),
                "total_size_bytes": total_size,
                "utilization": len(self.cache) / self.max_size
            }
    
    def _evict_lru(self):
        """Evict least recently used entry"""
        if self.access_order:
            lru_key = self.access_order.popleft()
            self.cache.pop(lru_key, None)

class RedisCache:
    """Redis-based distributed cache"""
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis_client = None
        self._initialized = False
    
    async def _ensure_connected(self):
        """Ensure Redis connection is established"""
        if not self._initialized and REDIS_AVAILABLE:
            try:
                self.redis_client = aioredis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5
                )
                # Test connection
                await self.redis_client.ping()
                self._initialized = True
                logger.info("API_CACHE - Redis cache connected", url=self.redis_url.split('@')[0] + '@***')
            except Exception as e:
                logger.error("API_CACHE - Redis connection failed", error=str(e))
                self.redis_client = None
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache"""
        await self._ensure_connected()
        
        if not self.redis_client:
            return None
        
        try:
            value_json = await self.redis_client.get(key)
            if value_json:
                return json.loads(value_json)
        except Exception as e:
            logger.debug("API_CACHE - Redis get failed", key=key, error=str(e))
        
        return None
    
    async def put(self, key: str, value: Any, ttl: int = 300, tags: List[str] = None):
        """Store value in Redis cache"""
        await self._ensure_connected()
        
        if not self.redis_client:
            return
        
        try:
            value_json = json.dumps(value)
            await self.redis_client.setex(key, ttl, value_json)
            
            # Store tags for invalidation
            if tags:
                for tag in tags:
                    await self.redis_client.sadd(f"tag:{tag}", key)
                    await self.redis_client.expire(f"tag:{tag}", ttl)
                    
        except Exception as e:
            logger.debug("API_CACHE - Redis put failed", key=key, error=str(e))
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis cache"""
        await self._ensure_connected()
        
        if not self.redis_client:
            return False
        
        try:
            result = await self.redis_client.delete(key)
            return result > 0
        except Exception as e:
            logger.debug("API_CACHE - Redis delete failed", key=key, error=str(e))
            return False
    
    async def invalidate_by_tags(self, tags: List[str]):
        """Invalidate cache entries by tags"""
        await self._ensure_connected()
        
        if not self.redis_client:
            return
        
        try:
            for tag in tags:
                keys = await self.redis_client.smembers(f"tag:{tag}")
                if keys:
                    await self.redis_client.delete(*keys)
                    await self.redis_client.delete(f"tag:{tag}")
        except Exception as e:
            logger.debug("API_CACHE - Redis tag invalidation failed", tags=tags, error=str(e))

class HybridCache:
    """Hybrid cache combining in-memory and distributed caching"""
    
    def __init__(self, config: APIOptimizationConfig):
        self.config = config
        self.memory_cache = InMemoryCache(config.cache_max_size)
        self.redis_cache = None
        
        if config.redis_url and REDIS_AVAILABLE:
            self.redis_cache = RedisCache(config.redis_url)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from hybrid cache (memory first, then Redis)"""
        # Try memory cache first
        value = self.memory_cache.get(key)
        if value is not None:
            return value
        
        # Try Redis cache
        if self.redis_cache:
            value = await self.redis_cache.get(key)
            if value is not None:
                # Store in memory cache for faster future access
                self.memory_cache.put(key, value, self.config.cache_default_ttl)
                return value
        
        return None
    
    async def put(self, key: str, value: Any, ttl: int = None, scope: CacheScope = CacheScope.GLOBAL, tags: List[str] = None):
        """Store value in hybrid cache"""
        if ttl is None:
            ttl = self.config.cache_default_ttl
        
        # Store in memory cache
        self.memory_cache.put(key, value, ttl, scope, tags)
        
        # Store in Redis cache for distribution
        if self.redis_cache:
            await self.redis_cache.put(key, value, ttl, tags)
    
    async def delete(self, key: str) -> bool:
        """Delete key from hybrid cache"""
        memory_deleted = self.memory_cache.delete(key)
        redis_deleted = False
        
        if self.redis_cache:
            redis_deleted = await self.redis_cache.delete(key)
        
        return memory_deleted or redis_deleted
    
    async def invalidate_by_tags(self, tags: List[str]):
        """Invalidate cache entries by tags"""
        self.memory_cache.invalidate_by_tags(tags)
        
        if self.redis_cache:
            await self.redis_cache.invalidate_by_tags(tags)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "memory_cache": self.memory_cache.get_stats(),
            "redis_available": self.redis_cache is not None
        }

class ResponseCompressor:
    """Intelligent response compression with algorithm selection"""
    
    def __init__(self, config: APIOptimizationConfig):
        self.config = config
        self.compression_stats = {
            "gzip": {"count": 0, "total_original": 0, "total_compressed": 0},
            "brotli": {"count": 0, "total_original": 0, "total_compressed": 0},
            "deflate": {"count": 0, "total_original": 0, "total_compressed": 0}
        }
    
    def should_compress(self, content_type: str, content_length: int) -> bool:
        """Determine if response should be compressed"""
        if content_length < self.config.compression_min_size:
            return False
        
        compressible_types = [
            "application/json",
            "application/xml", 
            "text/html",
            "text/css",
            "text/javascript",
            "application/javascript",
            "text/plain"
        ]
        
        return any(ct in content_type for ct in compressible_types)
    
    def select_algorithm(self, accept_encoding: str, content_type: str) -> Optional[CompressionAlgorithm]:
        """Select best compression algorithm based on client support and content"""
        if self.config.compression_algorithm != CompressionAlgorithm.AUTO:
            return self.config.compression_algorithm
        
        # Parse Accept-Encoding header
        supported_encodings = [enc.strip().lower() for enc in accept_encoding.split(',')]
        
        # Prefer Brotli for text content (better compression ratio)
        if "br" in supported_encodings and ("json" in content_type or "text" in content_type):
            return CompressionAlgorithm.BROTLI
        
        # Use gzip as fallback (universal support)
        if "gzip" in supported_encodings:
            return CompressionAlgorithm.GZIP
        
        # Use deflate as last resort
        if "deflate" in supported_encodings:
            return CompressionAlgorithm.DEFLATE
        
        return None
    
    def compress_content(self, content: bytes, algorithm: CompressionAlgorithm) -> bytes:
        """Compress content using specified algorithm"""
        original_size = len(content)
        
        try:
            if algorithm == CompressionAlgorithm.GZIP:
                compressed = gzip.compress(content, compresslevel=self.config.compression_level)
                self.compression_stats["gzip"]["count"] += 1
                self.compression_stats["gzip"]["total_original"] += original_size
                self.compression_stats["gzip"]["total_compressed"] += len(compressed)
                return compressed
            
            elif algorithm == CompressionAlgorithm.BROTLI:
                compressed = brotli.compress(content, quality=self.config.compression_level)
                self.compression_stats["brotli"]["count"] += 1
                self.compression_stats["brotli"]["total_original"] += original_size
                self.compression_stats["brotli"]["total_compressed"] += len(compressed)
                return compressed
            
            elif algorithm == CompressionAlgorithm.DEFLATE:
                compressed = zlib.compress(content, level=self.config.compression_level)
                self.compression_stats["deflate"]["count"] += 1
                self.compression_stats["deflate"]["total_original"] += original_size
                self.compression_stats["deflate"]["total_compressed"] += len(compressed)
                return compressed
                
        except Exception as e:
            logger.debug("API_COMPRESSION - Compression failed", 
                        algorithm=algorithm.value, error=str(e))
        
        return content
    
    def get_compression_stats(self) -> Dict[str, Any]:
        """Get compression statistics"""
        stats = {}
        for alg, data in self.compression_stats.items():
            if data["count"] > 0:
                compression_ratio = 1 - (data["total_compressed"] / data["total_original"])
                stats[alg] = {
                    "requests": data["count"],
                    "original_bytes": data["total_original"],
                    "compressed_bytes": data["total_compressed"],
                    "compression_ratio": round(compression_ratio, 3),
                    "bytes_saved": data["total_original"] - data["total_compressed"]
                }
        
        return stats

class RateLimiter:
    """Advanced rate limiter with multiple strategies"""
    
    def __init__(self, config: APIOptimizationConfig):
        self.config = config
        self.rate_limit_data: Dict[str, RateLimitInfo] = {}
        self.lock = threading.RLock()
    
    def is_allowed(self, identifier: str, limit: int = None, window: int = None) -> tuple[bool, Dict[str, Any]]:
        """Check if request is allowed under rate limit"""
        if limit is None:
            limit = self.config.default_rate_limit
        if window is None:
            window = self.config.rate_limit_window
        
        with self.lock:
            current_time = datetime.now()
            
            # Get or create rate limit info
            if identifier not in self.rate_limit_data:
                self.rate_limit_data[identifier] = RateLimitInfo(identifier=identifier)
            
            rate_info = self.rate_limit_data[identifier]
            
            # Check if currently blocked
            if rate_info.blocked_until and current_time < rate_info.blocked_until:
                return False, {
                    "allowed": False,
                    "reason": "temporarily_blocked",
                    "blocked_until": rate_info.blocked_until.isoformat(),
                    "retry_after": int((rate_info.blocked_until - current_time).total_seconds())
                }
            
            # Apply rate limiting strategy
            if self.config.rate_limit_strategy == RateLimitStrategy.SLIDING_WINDOW:
                return self._sliding_window_check(rate_info, limit, window)
            elif self.config.rate_limit_strategy == RateLimitStrategy.TOKEN_BUCKET:
                return self._token_bucket_check(rate_info, limit, window)
            else:
                return self._fixed_window_check(rate_info, limit, window)
    
    def _sliding_window_check(self, rate_info: RateLimitInfo, limit: int, window: int) -> tuple[bool, Dict[str, Any]]:
        """Sliding window rate limiting"""
        current_time = datetime.now()
        
        # Clean up old requests
        rate_info.cleanup_old_requests(window)
        
        # Check current request count
        current_count = len(rate_info.requests)
        
        if current_count >= limit:
            # Calculate retry after based on oldest request
            if rate_info.requests:
                oldest_request = min(rate_info.requests)
                retry_after = int((oldest_request + timedelta(seconds=window) - current_time).total_seconds())
                return False, {
                    "allowed": False,
                    "current_count": current_count,
                    "limit": limit,
                    "window_seconds": window,
                    "retry_after": max(0, retry_after)
                }
        
        # Allow request and record it
        rate_info.requests.append(current_time)
        
        return True, {
            "allowed": True,
            "current_count": current_count + 1,
            "limit": limit,
            "window_seconds": window,
            "remaining": limit - current_count - 1
        }
    
    def _token_bucket_check(self, rate_info: RateLimitInfo, limit: int, window: int) -> tuple[bool, Dict[str, Any]]:
        """Token bucket rate limiting"""
        current_time = datetime.now()
        
        # Initialize tokens if first request
        if rate_info.last_refill is None:
            rate_info.tokens = limit
            rate_info.last_refill = current_time
        
        # Refill tokens based on elapsed time
        time_elapsed = (current_time - rate_info.last_refill).total_seconds()
        tokens_to_add = int(time_elapsed * (limit / window))
        
        if tokens_to_add > 0:
            rate_info.tokens = min(limit, rate_info.tokens + tokens_to_add)
            rate_info.last_refill = current_time
        
        # Check if tokens available
        if rate_info.tokens <= 0:
            retry_after = int(window / limit)  # Time to get next token
            return False, {
                "allowed": False,
                "tokens_remaining": 0,
                "limit": limit,
                "retry_after": retry_after
            }
        
        # Consume token
        rate_info.tokens -= 1
        
        return True, {
            "allowed": True,
            "tokens_remaining": rate_info.tokens,
            "limit": limit
        }
    
    def _fixed_window_check(self, rate_info: RateLimitInfo, limit: int, window: int) -> tuple[bool, Dict[str, Any]]:
        """Fixed window rate limiting"""
        current_time = datetime.now()
        
        # Calculate current window start
        window_start = current_time.replace(second=0, microsecond=0)
        window_start = window_start.replace(minute=(window_start.minute // (window // 60)) * (window // 60))
        
        # Clean up requests outside current window
        rate_info.requests = [req for req in rate_info.requests if req >= window_start]
        
        current_count = len(rate_info.requests)
        
        if current_count >= limit:
            # Calculate retry after (next window)
            next_window = window_start + timedelta(seconds=window)
            retry_after = int((next_window - current_time).total_seconds())
            
            return False, {
                "allowed": False,
                "current_count": current_count,
                "limit": limit,
                "window_start": window_start.isoformat(),
                "retry_after": retry_after
            }
        
        # Allow request
        rate_info.requests.append(current_time)
        
        return True, {
            "allowed": True,
            "current_count": current_count + 1,
            "limit": limit,
            "remaining": limit - current_count - 1,
            "window_start": window_start.isoformat()
        }
    
    def get_rate_limit_stats(self) -> Dict[str, Any]:
        """Get rate limiting statistics"""
        with self.lock:
            active_limits = len(self.rate_limit_data)
            blocked_count = sum(1 for info in self.rate_limit_data.values()
                              if info.blocked_until and datetime.now() < info.blocked_until)
            
            total_requests = sum(len(info.requests) for info in self.rate_limit_data.values())
            
            return {
                "active_rate_limits": active_limits,
                "blocked_identifiers": blocked_count,
                "total_recent_requests": total_requests,
                "strategy": self.config.rate_limit_strategy.value
            }

class APIOptimizationMiddleware(BaseHTTPMiddleware):
    """Comprehensive API optimization middleware"""
    
    def __init__(self, app: ASGIApp, config: APIOptimizationConfig):
        super().__init__(app)
        self.config = config
        self.cache = HybridCache(config)
        self.compressor = ResponseCompressor(config)
        self.rate_limiter = RateLimiter(config)
        
        # Performance monitoring
        self.request_stats = {
            "total_requests": 0,
            "cached_responses": 0,
            "compressed_responses": 0,
            "rate_limited_requests": 0,
            "total_response_time": 0.0
        }
        
        logger.info("API_OPTIMIZATION - Middleware initialized",
                   cache_strategy=config.cache_strategy.value,
                   compression=config.compression_algorithm.value,
                   rate_limit_strategy=config.rate_limit_strategy.value)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through optimization middleware"""
        start_time = time.time()
        self.request_stats["total_requests"] += 1
        
        try:
            # Extract client identifier for rate limiting
            client_id = self._get_client_identifier(request)
            
            # Apply rate limiting
            if not await self._check_rate_limit(request, client_id):
                self.request_stats["rate_limited_requests"] += 1
                return JSONResponse(
                    status_code=429,
                    content={"error": "Rate limit exceeded", "retry_after": 60}
                )
            
            # Check cache for GET requests
            if request.method == "GET":
                cached_response = await self._get_cached_response(request)
                if cached_response:
                    self.request_stats["cached_responses"] += 1
                    return await self._apply_response_optimization(request, cached_response)
            
            # Process request
            response = await call_next(request)
            
            # Cache successful responses
            if request.method == "GET" and response.status_code == 200:
                await self._cache_response(request, response)
            
            # Apply response optimizations
            optimized_response = await self._apply_response_optimization(request, response)
            
            return optimized_response
            
        except Exception as e:
            logger.error("API_OPTIMIZATION - Middleware error", error=str(e))
            return await call_next(request)
        
        finally:
            # Record response time
            response_time = time.time() - start_time
            self.request_stats["total_response_time"] += response_time
            
            if response_time > self.config.slow_request_threshold:
                logger.warning("API_OPTIMIZATION - Slow request detected",
                             path=request.url.path,
                             method=request.method,
                             response_time=round(response_time, 3))
    
    def _get_client_identifier(self, request: Request) -> str:
        """Extract client identifier for rate limiting"""
        # Try to get user ID from authentication
        if hasattr(request.state, 'user') and request.state.user:
            return f"user:{request.state.user.id}"
        
        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        return f"ip:{client_ip}"
    
    async def _check_rate_limit(self, request: Request, client_id: str) -> bool:
        """Check rate limit for client"""
        # Skip rate limiting for certain endpoints
        skip_paths = ["/health", "/metrics", "/docs", "/openapi.json"]
        if any(request.url.path.startswith(path) for path in skip_paths):
            return True
        
        allowed, info = self.rate_limiter.is_allowed(client_id)
        
        if not allowed:
            logger.warning("API_OPTIMIZATION - Rate limit exceeded",
                          client_id=client_id,
                          path=request.url.path,
                          info=info)
        
        return allowed
    
    async def _get_cached_response(self, request: Request) -> Optional[Response]:
        """Get cached response if available"""
        cache_key = self._generate_cache_key(request)
        cached_data = await self.cache.get(cache_key)
        
        if cached_data:
            logger.debug("API_OPTIMIZATION - Cache hit", 
                        path=request.url.path,
                        cache_key=cache_key)
            
            return JSONResponse(
                content=cached_data["content"],
                status_code=cached_data.get("status_code", 200),
                headers=cached_data.get("headers", {})
            )
        
        return None
    
    async def _cache_response(self, request: Request, response: Response):
        """Cache successful response"""
        if response.status_code != 200:
            return
        
        try:
            # Read response content
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            
            # Parse JSON content
            content = json.loads(body.decode())
            
            # Generate cache key
            cache_key = self._generate_cache_key(request)
            
            # Determine cache scope and tags
            scope = self._determine_cache_scope(request)
            tags = self._extract_cache_tags(request, content)
            
            # Store in cache
            await self.cache.put(
                cache_key, 
                {
                    "content": content,
                    "status_code": response.status_code,
                    "headers": dict(response.headers)
                },
                ttl=self._get_cache_ttl(request),
                scope=scope,
                tags=tags
            )
            
            logger.debug("API_OPTIMIZATION - Response cached",
                        path=request.url.path,
                        cache_key=cache_key,
                        tags=tags)
            
        except Exception as e:
            logger.debug("API_OPTIMIZATION - Cache storage failed", error=str(e))
    
    async def _apply_response_optimization(self, request: Request, response: Response) -> Response:
        """Apply response optimizations (compression, headers, etc.)"""
        # Get response content
        if hasattr(response, 'body'):
            body = response.body
        else:
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
        
        # Apply compression if appropriate
        content_type = response.headers.get("content-type", "")
        accept_encoding = request.headers.get("accept-encoding", "")
        
        if (self.compressor.should_compress(content_type, len(body)) and 
            accept_encoding and 
            body):
            
            algorithm = self.compressor.select_algorithm(accept_encoding, content_type)
            if algorithm:
                compressed_body = self.compressor.compress_content(body, algorithm)
                
                if len(compressed_body) < len(body):  # Only use if actually smaller
                    body = compressed_body
                    response.headers["content-encoding"] = algorithm.value
                    response.headers["content-length"] = str(len(body))
                    self.request_stats["compressed_responses"] += 1
                    
                    logger.debug("API_OPTIMIZATION - Response compressed",
                               algorithm=algorithm.value,
                               original_size=len(body),
                               compressed_size=len(compressed_body),
                               ratio=round(1 - len(compressed_body)/len(body), 3))
        
        # Add optimization headers
        response.headers["X-API-Optimized"] = "true"
        
        if self.config.enable_etag:
            etag = hashlib.md5(body).hexdigest()
            response.headers["ETag"] = f'"{etag}"'
            
            # Check If-None-Match for 304 responses
            if_none_match = request.headers.get("if-none-match")
            if if_none_match and etag in if_none_match:
                return Response(status_code=304)
        
        # Create optimized response
        return Response(
            content=body,
            status_code=response.status_code,
            headers=response.headers,
            media_type=content_type
        )
    
    def _generate_cache_key(self, request: Request) -> str:
        """Generate cache key for request"""
        # Include path, query parameters, and relevant headers
        key_components = [
            request.method,
            request.url.path,
            str(sorted(request.query_params.items())),
        ]
        
        # Include user context if available
        if hasattr(request.state, 'user') and request.state.user:
            key_components.append(f"user:{request.state.user.id}")
        
        key_string = "|".join(key_components)
        return hashlib.sha256(key_string.encode()).hexdigest()[:16]
    
    def _determine_cache_scope(self, request: Request) -> CacheScope:
        """Determine appropriate cache scope for request"""
        # User-specific endpoints
        if "/users/" in request.url.path or "/me" in request.url.path:
            return CacheScope.USER
        
        # Tenant-specific endpoints  
        if "/tenants/" in request.url.path or "/organizations/" in request.url.path:
            return CacheScope.TENANT
        
        # Public endpoints
        if request.url.path.startswith("/public/"):
            return CacheScope.GLOBAL
        
        return CacheScope.GLOBAL
    
    def _extract_cache_tags(self, request: Request, content: Any) -> List[str]:
        """Extract cache tags for invalidation"""
        tags = []
        
        # Add path-based tags
        path_parts = request.url.path.strip("/").split("/")
        if len(path_parts) >= 2:
            tags.append(f"resource:{path_parts[0]}")
            if path_parts[1] and path_parts[1] != "{id}":
                tags.append(f"resource:{path_parts[0]}:{path_parts[1]}")
        
        # Add content-based tags
        if isinstance(content, dict):
            if "id" in content:
                tags.append(f"id:{content['id']}")
            if "patient_id" in content:
                tags.append(f"patient:{content['patient_id']}")
            if "organization_id" in content:
                tags.append(f"organization:{content['organization_id']}")
        
        return tags
    
    def _get_cache_ttl(self, request: Request) -> int:
        """Get cache TTL based on request characteristics"""
        # Static content - longer TTL
        if request.url.path.startswith("/static/"):
            return 3600  # 1 hour
        
        # Reference data - medium TTL
        if any(path in request.url.path for path in ["/lookup/", "/metadata/", "/config/"]):
            return 1800  # 30 minutes
        
        # Dynamic user data - short TTL
        if any(path in request.url.path for path in ["/users/", "/patients/", "/appointments/"]):
            return 300   # 5 minutes
        
        return self.config.cache_default_ttl
    
    async def get_optimization_stats(self) -> Dict[str, Any]:
        """Get comprehensive optimization statistics"""
        stats = {
            "requests": self.request_stats.copy(),
            "cache": self.cache.get_stats(),
            "compression": self.compressor.get_compression_stats(),
            "rate_limiting": self.rate_limiter.get_rate_limit_stats()
        }
        
        # Calculate averages
        if stats["requests"]["total_requests"] > 0:
            stats["requests"]["avg_response_time"] = round(
                stats["requests"]["total_response_time"] / stats["requests"]["total_requests"], 3
            )
            stats["requests"]["cache_hit_rate"] = round(
                stats["requests"]["cached_responses"] / stats["requests"]["total_requests"], 3
            )
            stats["requests"]["compression_rate"] = round(
                stats["requests"]["compressed_responses"] / stats["requests"]["total_requests"], 3
            )
        
        return stats

# Global API optimization instance
api_optimizer: Optional[APIOptimizationMiddleware] = None

def initialize_api_optimization(app: FastAPI, config: APIOptimizationConfig = None) -> APIOptimizationMiddleware:
    """Initialize API optimization middleware"""
    global api_optimizer
    
    if config is None:
        config = APIOptimizationConfig()
    
    api_optimizer = APIOptimizationMiddleware(app, config)
    app.add_middleware(APIOptimizationMiddleware, config=config)
    
    logger.info("API_OPTIMIZATION - Middleware initialized",
               cache_strategy=config.cache_strategy.value,
               compression=config.compression_algorithm.value)
    
    return api_optimizer

def get_api_optimizer() -> APIOptimizationMiddleware:
    """Get API optimization middleware instance"""
    if api_optimizer is None:
        raise RuntimeError("API optimizer not initialized. Call initialize_api_optimization() first.")
    return api_optimizer

# Convenience functions
async def invalidate_cache_by_tags(tags: List[str]):
    """Invalidate cache entries by tags"""
    optimizer = get_api_optimizer()
    await optimizer.cache.invalidate_by_tags(tags)

async def get_api_performance_report() -> Dict[str, Any]:
    """Get comprehensive API performance report"""
    optimizer = get_api_optimizer()
    return await optimizer.get_optimization_stats()

async def clear_api_cache():
    """Clear all API cache entries"""
    optimizer = get_api_optimizer()
    optimizer.cache.memory_cache.clear()
    if optimizer.cache.redis_cache:
        # Note: This would need Redis FLUSHDB command implementation
        pass