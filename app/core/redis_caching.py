"""
Redis Caching Strategy for Healthcare Records

Advanced Redis caching implementation for production performance:
- Multi-layer caching with TTL management
- PHI-safe caching with encryption
- Cache invalidation strategies
- Session management and rate limiting
- Performance monitoring and optimization
- Cache warming and prefetching strategies

This module implements HIPAA-compliant caching that ensures
PHI data is properly encrypted even in cache layers.
"""

import asyncio
import json
import time
import uuid
import hashlib
import pickle
from typing import Dict, List, Optional, Any, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import structlog

import redis.asyncio as redis
from redis.asyncio import Redis
from redis.exceptions import RedisError, ConnectionError as RedisConnectionError

from app.core.config import get_settings
from app.core.security import EncryptionService

logger = structlog.get_logger()


class CacheKeyType(str, Enum):
    """Types of cache keys for organization."""
    PATIENT_LOOKUP = "patient_lookup"
    PATIENT_SEARCH = "patient_search"
    IMMUNIZATION_RECORD = "immunization_record"
    CLINICAL_DOCUMENT = "clinical_document"
    CONSENT_STATUS = "consent_status"
    SESSION_DATA = "session_data"
    RATE_LIMIT = "rate_limit"
    API_RESPONSE = "api_response"
    FHIR_VALIDATION = "fhir_validation"
    AUDIT_AGGREGATION = "audit_aggregation"


@dataclass
class CacheConfig:
    """Cache configuration for different data types."""
    key_type: CacheKeyType
    ttl_seconds: int
    encrypt_data: bool = False
    compress_data: bool = False
    invalidation_pattern: Optional[str] = None
    max_size: Optional[int] = None


class CacheStrategyManager:
    """Manages different caching strategies for healthcare data."""
    
    def __init__(self):
        self.settings = get_settings()
        self.encryption_service = EncryptionService()
        self.redis_client: Optional[Redis] = None
        
        # Cache configurations for different data types
        self.cache_configs = {
            CacheKeyType.PATIENT_LOOKUP: CacheConfig(
                key_type=CacheKeyType.PATIENT_LOOKUP,
                ttl_seconds=300,  # 5 minutes
                encrypt_data=True,  # PHI data must be encrypted
                compress_data=True,
                invalidation_pattern="patient:*",
                max_size=10000
            ),
            CacheKeyType.PATIENT_SEARCH: CacheConfig(
                key_type=CacheKeyType.PATIENT_SEARCH,
                ttl_seconds=120,  # 2 minutes (searches change frequently)
                encrypt_data=True,
                compress_data=True,
                invalidation_pattern="patient_search:*",
                max_size=5000
            ),
            CacheKeyType.IMMUNIZATION_RECORD: CacheConfig(
                key_type=CacheKeyType.IMMUNIZATION_RECORD,
                ttl_seconds=600,  # 10 minutes
                encrypt_data=True,
                compress_data=True,
                invalidation_pattern="immunization:*",
                max_size=20000
            ),
            CacheKeyType.CLINICAL_DOCUMENT: CacheConfig(
                key_type=CacheKeyType.CLINICAL_DOCUMENT,
                ttl_seconds=900,  # 15 minutes
                encrypt_data=True,
                compress_data=True,
                invalidation_pattern="document:*",
                max_size=15000
            ),
            CacheKeyType.CONSENT_STATUS: CacheConfig(
                key_type=CacheKeyType.CONSENT_STATUS,
                ttl_seconds=180,  # 3 minutes (consent can change)
                encrypt_data=True,
                compress_data=False,
                invalidation_pattern="consent:*",
                max_size=5000
            ),
            CacheKeyType.SESSION_DATA: CacheConfig(
                key_type=CacheKeyType.SESSION_DATA,
                ttl_seconds=1800,  # 30 minutes
                encrypt_data=True,
                compress_data=False,
                invalidation_pattern="session:*",
                max_size=50000
            ),
            CacheKeyType.RATE_LIMIT: CacheConfig(
                key_type=CacheKeyType.RATE_LIMIT,
                ttl_seconds=60,  # 1 minute
                encrypt_data=False,
                compress_data=False,
                invalidation_pattern="rate_limit:*",
                max_size=100000
            ),
            CacheKeyType.API_RESPONSE: CacheConfig(
                key_type=CacheKeyType.API_RESPONSE,
                ttl_seconds=30,  # 30 seconds
                encrypt_data=False,  # Non-PHI API responses
                compress_data=True,
                invalidation_pattern="api_response:*",
                max_size=10000
            ),
            CacheKeyType.FHIR_VALIDATION: CacheConfig(
                key_type=CacheKeyType.FHIR_VALIDATION,
                ttl_seconds=3600,  # 1 hour (validation results are stable)
                encrypt_data=False,
                compress_data=True,
                invalidation_pattern="fhir_validation:*",
                max_size=1000
            ),
            CacheKeyType.AUDIT_AGGREGATION: CacheConfig(
                key_type=CacheKeyType.AUDIT_AGGREGATION,
                ttl_seconds=300,  # 5 minutes
                encrypt_data=False,
                compress_data=True,
                invalidation_pattern="audit_agg:*",
                max_size=2000
            )
        }
    
    async def get_redis_client(self) -> Redis:
        """Get Redis client with connection pooling."""
        if self.redis_client is None:
            try:
                # Parse Redis URL
                redis_url = self.settings.redis_url or "redis://localhost:6379/0"
                
                # Create Redis client with optimized settings
                self.redis_client = redis.from_url(
                    redis_url,
                    encoding="utf-8",
                    decode_responses=False,  # Handle binary data for encryption
                    socket_timeout=5,
                    socket_connect_timeout=5,
                    socket_keepalive=True,
                    socket_keepalive_options={},
                    health_check_interval=30,
                    max_connections=20
                )
                
                # Test connection
                await self.redis_client.ping()
                logger.info("Redis connection established successfully")
                
            except Exception as e:
                logger.error("Failed to connect to Redis", error=str(e))
                raise
        
        return self.redis_client
    
    def _generate_cache_key(self, key_type: CacheKeyType, identifier: str, **kwargs) -> str:
        """Generate standardized cache key."""
        base_key = f"{key_type.value}:{identifier}"
        
        # Add additional parameters to key
        if kwargs:
            # Sort kwargs for consistent key generation
            sorted_params = sorted(kwargs.items())
            params_str = ":".join(f"{k}={v}" for k, v in sorted_params)
            base_key = f"{base_key}:{params_str}"
        
        # Hash long keys to prevent Redis key length issues
        if len(base_key) > 250:
            key_hash = hashlib.sha256(base_key.encode()).hexdigest()[:16]
            base_key = f"{key_type.value}:hashed:{key_hash}"
        
        return base_key
    
    async def _serialize_data(self, data: Any, config: CacheConfig) -> bytes:
        """Serialize data for caching with optional encryption and compression."""
        try:
            # Convert to JSON first
            if isinstance(data, (dict, list)):
                serialized = json.dumps(data, default=str)
            else:
                serialized = pickle.dumps(data)
            
            # Convert to bytes
            if isinstance(serialized, str):
                data_bytes = serialized.encode('utf-8')
            else:
                data_bytes = serialized
            
            # Compress if configured
            if config.compress_data:
                import gzip
                data_bytes = gzip.compress(data_bytes)
            
            # Encrypt if configured (for PHI data)
            if config.encrypt_data:
                data_bytes = await self.encryption_service.encrypt_data(data_bytes)
            
            return data_bytes
            
        except Exception as e:
            logger.error("Data serialization failed", error=str(e))
            raise
    
    async def _deserialize_data(self, data_bytes: bytes, config: CacheConfig) -> Any:
        """Deserialize cached data with decryption and decompression."""
        try:
            # Decrypt if needed
            if config.encrypt_data:
                data_bytes = await self.encryption_service.decrypt_data(data_bytes)
            
            # Decompress if needed
            if config.compress_data:
                import gzip
                data_bytes = gzip.decompress(data_bytes)
            
            # Deserialize
            try:
                # Try JSON first
                return json.loads(data_bytes.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Fall back to pickle
                return pickle.loads(data_bytes)
                
        except Exception as e:
            logger.error("Data deserialization failed", error=str(e))
            raise


class HealthcareRedisCache:
    """Main Redis cache interface for healthcare data."""
    
    def __init__(self):
        self.strategy_manager = CacheStrategyManager()
        self.hit_count = 0
        self.miss_count = 0
        self.error_count = 0
    
    async def get(self, key_type: CacheKeyType, identifier: str, **kwargs) -> Optional[Any]:
        """Get cached data with automatic deserialization."""
        try:
            redis_client = await self.strategy_manager.get_redis_client()
            config = self.strategy_manager.cache_configs[key_type]
            
            cache_key = self.strategy_manager._generate_cache_key(key_type, identifier, **kwargs)
            
            # Get data from Redis
            cached_data = await redis_client.get(cache_key)
            
            if cached_data is None:
                self.miss_count += 1
                return None
            
            # Deserialize data
            data = await self.strategy_manager._deserialize_data(cached_data, config)
            
            self.hit_count += 1
            logger.debug("Cache hit", key_type=key_type.value, identifier=identifier)
            
            return data
            
        except Exception as e:
            self.error_count += 1
            logger.error("Cache get failed", key_type=key_type.value, error=str(e))
            return None
    
    async def set(
        self,
        key_type: CacheKeyType,
        identifier: str,
        data: Any,
        ttl_override: Optional[int] = None,
        **kwargs
    ) -> bool:
        """Set cached data with automatic serialization."""
        try:
            redis_client = await self.strategy_manager.get_redis_client()
            config = self.strategy_manager.cache_configs[key_type]
            
            cache_key = self.strategy_manager._generate_cache_key(key_type, identifier, **kwargs)
            
            # Serialize data
            serialized_data = await self.strategy_manager._serialize_data(data, config)
            
            # Set TTL
            ttl = ttl_override or config.ttl_seconds
            
            # Store in Redis
            await redis_client.setex(cache_key, ttl, serialized_data)
            
            logger.debug("Cache set", key_type=key_type.value, identifier=identifier, ttl=ttl)
            
            return True
            
        except Exception as e:
            self.error_count += 1
            logger.error("Cache set failed", key_type=key_type.value, error=str(e))
            return False
    
    async def delete(self, key_type: CacheKeyType, identifier: str, **kwargs) -> bool:
        """Delete specific cached item."""
        try:
            redis_client = await self.strategy_manager.get_redis_client()
            
            cache_key = self.strategy_manager._generate_cache_key(key_type, identifier, **kwargs)
            
            result = await redis_client.delete(cache_key)
            
            logger.debug("Cache delete", key_type=key_type.value, identifier=identifier)
            
            return result > 0
            
        except Exception as e:
            self.error_count += 1
            logger.error("Cache delete failed", key_type=key_type.value, error=str(e))
            return False
    
    async def invalidate_pattern(self, key_type: CacheKeyType, pattern: Optional[str] = None) -> int:
        """Invalidate cache entries matching a pattern."""
        try:
            redis_client = await self.strategy_manager.get_redis_client()
            config = self.strategy_manager.cache_configs[key_type]
            
            # Use provided pattern or default from config
            invalidation_pattern = pattern or config.invalidation_pattern
            
            if not invalidation_pattern:
                logger.warning("No invalidation pattern available", key_type=key_type.value)
                return 0
            
            # Find matching keys
            keys = await redis_client.keys(invalidation_pattern)
            
            if keys:
                # Delete all matching keys
                deleted_count = await redis_client.delete(*keys)
                logger.info("Cache invalidation", pattern=invalidation_pattern, deleted_count=deleted_count)
                return deleted_count
            
            return 0
            
        except Exception as e:
            self.error_count += 1
            logger.error("Cache invalidation failed", pattern=invalidation_pattern, error=str(e))
            return 0
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        try:
            redis_client = await self.strategy_manager.get_redis_client()
            
            # Get Redis info
            redis_info = await redis_client.info()
            
            # Calculate hit rate
            total_requests = self.hit_count + self.miss_count
            hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "hit_count": self.hit_count,
                "miss_count": self.miss_count,
                "error_count": self.error_count,
                "hit_rate_percent": round(hit_rate, 2),
                "redis_connected_clients": redis_info.get("connected_clients", 0),
                "redis_used_memory": redis_info.get("used_memory_human", "0"),
                "redis_keyspace_hits": redis_info.get("keyspace_hits", 0),
                "redis_keyspace_misses": redis_info.get("keyspace_misses", 0),
                "redis_uptime_seconds": redis_info.get("uptime_in_seconds", 0)
            }
            
        except Exception as e:
            logger.error("Failed to get cache stats", error=str(e))
            return {"error": str(e)}


class SessionCache:
    """Specialized cache for user session management."""
    
    def __init__(self, redis_cache: HealthcareRedisCache):
        self.redis_cache = redis_cache
    
    async def create_session(self, user_id: str, session_data: Dict[str, Any]) -> str:
        """Create new user session."""
        session_id = str(uuid.uuid4())
        
        # Add metadata
        session_data.update({
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat()
        })
        
        success = await self.redis_cache.set(
            CacheKeyType.SESSION_DATA,
            session_id,
            session_data
        )
        
        if success:
            logger.info("Session created", user_id=user_id, session_id=session_id)
            return session_id
        else:
            raise Exception("Failed to create session")
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data."""
        return await self.redis_cache.get(CacheKeyType.SESSION_DATA, session_id)
    
    async def update_session_activity(self, session_id: str) -> bool:
        """Update session last activity timestamp."""
        session_data = await self.get_session(session_id)
        
        if session_data:
            session_data["last_activity"] = datetime.utcnow().isoformat()
            return await self.redis_cache.set(CacheKeyType.SESSION_DATA, session_id, session_data)
        
        return False
    
    async def invalidate_session(self, session_id: str) -> bool:
        """Invalidate specific session."""
        return await self.redis_cache.delete(CacheKeyType.SESSION_DATA, session_id)
    
    async def invalidate_user_sessions(self, user_id: str) -> int:
        """Invalidate all sessions for a user."""
        # This would require a more complex pattern matching
        # For now, we'll use a simple approach
        return await self.redis_cache.invalidate_pattern(
            CacheKeyType.SESSION_DATA,
            f"session_data:*user_id={user_id}*"
        )


class RateLimitCache:
    """Rate limiting using Redis."""
    
    def __init__(self, redis_cache: HealthcareRedisCache):
        self.redis_cache = redis_cache
    
    async def check_rate_limit(
        self,
        identifier: str,
        limit: int,
        window_seconds: int,
        increment: bool = True
    ) -> Tuple[bool, int, int]:
        """
        Check rate limit for identifier.
        
        Returns:
            (allowed, current_count, remaining_count)
        """
        try:
            redis_client = await self.redis_cache.strategy_manager.get_redis_client()
            
            # Use current timestamp window
            current_window = int(time.time()) // window_seconds
            cache_key = f"rate_limit:{identifier}:{current_window}"
            
            # Get current count
            current_count = await redis_client.get(cache_key)
            current_count = int(current_count) if current_count else 0
            
            # Check if limit exceeded
            if current_count >= limit:
                return False, current_count, 0
            
            # Increment counter if requested
            if increment:
                pipe = redis_client.pipeline()
                pipe.incr(cache_key)
                pipe.expire(cache_key, window_seconds)
                await pipe.execute()
                current_count += 1
            
            remaining = max(0, limit - current_count)
            
            return True, current_count, remaining
            
        except Exception as e:
            logger.error("Rate limit check failed", identifier=identifier, error=str(e))
            # Allow on error (fail open)
            return True, 0, limit


class CacheWarmingManager:
    """Manages cache warming and prefetching strategies."""
    
    def __init__(self, redis_cache: HealthcareRedisCache):
        self.redis_cache = redis_cache
    
    async def warm_patient_cache(self, patient_ids: List[str]) -> Dict[str, bool]:
        """Warm cache for frequently accessed patients."""
        results = {}
        
        # This would integrate with the patient service to prefetch data
        for patient_id in patient_ids:
            try:
                # Simulate cache warming (in real implementation, fetch from DB)
                cache_key = f"patient_lookup:{patient_id}"
                
                # Check if already cached
                existing = await self.redis_cache.get(CacheKeyType.PATIENT_LOOKUP, patient_id)
                
                if existing is None:
                    # In real implementation, fetch from database and cache
                    # For now, just mark as attempted
                    results[patient_id] = False
                else:
                    results[patient_id] = True
                    
            except Exception as e:
                logger.error("Cache warming failed", patient_id=patient_id, error=str(e))
                results[patient_id] = False
        
        return results
    
    async def warm_frequently_accessed_data(self) -> Dict[str, int]:
        """Warm cache for frequently accessed data patterns."""
        warming_results = {
            "patients_warmed": 0,
            "immunizations_warmed": 0,
            "documents_warmed": 0
        }
        
        # This would analyze access patterns and prefetch common queries
        # Implementation would integrate with analytics to identify hot data
        
        return warming_results


# =============================================================================
# MAIN CACHE INTERFACE
# =============================================================================

class HealthcareCacheManager:
    """Main interface for healthcare caching operations."""
    
    def __init__(self):
        self.redis_cache = HealthcareRedisCache()
        self.session_cache = SessionCache(self.redis_cache)
        self.rate_limit_cache = RateLimitCache(self.redis_cache)
        self.warming_manager = CacheWarmingManager(self.redis_cache)
    
    async def cache_patient_lookup(self, patient_id: str, patient_data: Dict[str, Any]) -> bool:
        """Cache patient lookup data."""
        return await self.redis_cache.set(CacheKeyType.PATIENT_LOOKUP, patient_id, patient_data)
    
    async def get_cached_patient(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Get cached patient data."""
        return await self.redis_cache.get(CacheKeyType.PATIENT_LOOKUP, patient_id)
    
    async def cache_patient_search(self, search_hash: str, search_results: Dict[str, Any]) -> bool:
        """Cache patient search results."""
        return await self.redis_cache.set(CacheKeyType.PATIENT_SEARCH, search_hash, search_results)
    
    async def get_cached_search(self, search_hash: str) -> Optional[Dict[str, Any]]:
        """Get cached search results."""
        return await self.redis_cache.get(CacheKeyType.PATIENT_SEARCH, search_hash)
    
    async def invalidate_patient_cache(self, patient_id: str) -> bool:
        """Invalidate all cache entries for a patient."""
        await self.redis_cache.delete(CacheKeyType.PATIENT_LOOKUP, patient_id)
        await self.redis_cache.invalidate_pattern(CacheKeyType.PATIENT_SEARCH, "patient_search:*")
        return True
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive cache performance metrics."""
        cache_stats = await self.redis_cache.get_cache_stats()
        
        return {
            "cache_performance": cache_stats,
            "configuration": {
                "total_cache_types": len(self.redis_cache.strategy_manager.cache_configs),
                "encryption_enabled": True,
                "compression_enabled": True,
                "ttl_ranges": {
                    "min_ttl": min(config.ttl_seconds for config in self.redis_cache.strategy_manager.cache_configs.values()),
                    "max_ttl": max(config.ttl_seconds for config in self.redis_cache.strategy_manager.cache_configs.values())
                }
            }
        }


# Global cache manager instance
cache_manager = HealthcareCacheManager()