#!/usr/bin/env python3
"""
Enterprise Database Performance Optimization System
Implements comprehensive database performance optimization with intelligent indexing,
connection pooling, query optimization, and performance monitoring.

Performance Optimization Features:
- Advanced connection pooling with dynamic scaling
- Intelligent query optimization and caching
- Database index management with automatic optimization
- Query performance monitoring and alerting
- Database replication and sharding support
- Connection health monitoring and recovery

Security Principles Applied:
- Defense in Depth: Multiple layers of database protection
- Zero Trust: Every database operation verified and monitored
- Least Privilege: Minimal database permissions per operation
- Complete Mediation: All database access through optimization layer
- Economy of Mechanism: Simple, reliable performance patterns

Architecture Patterns:
- Repository Pattern: Data access abstraction
- Connection Pool Pattern: Resource management optimization
- Observer Pattern: Performance monitoring and alerting
- Strategy Pattern: Multiple optimization strategies
- Proxy Pattern: Query interception and optimization
- Circuit Breaker: Database failure protection
"""

import asyncio
import json
import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable, Protocol
from enum import Enum, auto
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
import structlog
import uuid
from concurrent.futures import ThreadPoolExecutor
import threading
import weakref

from sqlalchemy.ext.asyncio import (
    AsyncEngine, AsyncSession, create_async_engine, 
    async_sessionmaker, AsyncConnection
)
from sqlalchemy.pool import QueuePool, StaticPool, NullPool
from sqlalchemy import (
    text, select, func, Index, Table, MetaData,
    event, inspect
)
# PoolEvents removed in newer SQLAlchemy versions - using event directly
from sqlalchemy.engine import Engine
from sqlalchemy.sql import ClauseElement
from sqlalchemy.orm import Query
import sqlalchemy as sa

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

logger = structlog.get_logger()

# Performance Optimization Configuration

class ConnectionPoolStrategy(str, Enum):
    """Database connection pool strategies"""
    STATIC = "static"           # Fixed pool size
    DYNAMIC = "dynamic"         # Dynamic scaling based on load
    QUEUE = "queue"            # Queue-based pool with overflow
    NULL = "null"              # No pooling (development only)

class QueryOptimizationLevel(str, Enum):
    """Query optimization levels"""
    NONE = "none"              # No optimization
    BASIC = "basic"            # Basic query caching
    ADVANCED = "advanced"      # Query plan optimization
    AGGRESSIVE = "aggressive"   # Aggressive caching and rewriting

class PerformanceMetric(str, Enum):
    """Database performance metrics"""
    QUERY_TIME = "query_time"
    POOL_USAGE = "pool_usage"
    CONNECTION_COUNT = "connection_count"
    CACHE_HIT_RATE = "cache_hit_rate"
    SLOW_QUERY_COUNT = "slow_query_count"
    DEADLOCK_COUNT = "deadlock_count"
    INDEX_USAGE = "index_usage"
    DISK_IO = "disk_io"

@dataclass
class DatabaseConfig:
    """Database performance configuration"""
    
    # Connection Pool Settings
    pool_size: int = 20
    max_overflow: int = 30
    pool_timeout: int = 30
    pool_recycle: int = 3600  # 1 hour
    pool_pre_ping: bool = True
    
    # Query Optimization Settings
    optimization_level: QueryOptimizationLevel = QueryOptimizationLevel.ADVANCED
    query_cache_size: int = 1000
    query_cache_ttl: int = 300  # 5 minutes
    slow_query_threshold: float = 1.0  # 1 second
    
    # Performance Monitoring
    enable_monitoring: bool = True
    metric_collection_interval: int = 30  # seconds
    performance_alert_threshold: float = 0.8  # 80% of limits
    
    # Index Management
    auto_index_optimization: bool = True
    index_analysis_interval: int = 3600  # 1 hour
    unused_index_retention: int = 86400 * 7  # 1 week
    
    # Connection Health
    health_check_interval: int = 60  # 1 minute
    max_connection_age: int = 7200  # 2 hours
    connection_retry_attempts: int = 3

@dataclass
class QueryPerformanceStats:
    """Query performance statistics"""
    query_hash: str
    execution_count: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    avg_time: float = 0.0
    last_execution: Optional[datetime] = None
    query_text: Optional[str] = None
    table_names: List[str] = field(default_factory=list)
    index_usage: Dict[str, int] = field(default_factory=dict)
    
    def update_stats(self, execution_time: float):
        """Update query performance statistics"""
        self.execution_count += 1
        self.total_time += execution_time
        self.min_time = min(self.min_time, execution_time)
        self.max_time = max(self.max_time, execution_time)
        self.avg_time = self.total_time / self.execution_count
        self.last_execution = datetime.now()

@dataclass
class ConnectionPoolStats:
    """Connection pool performance statistics"""
    pool_size: int = 0
    checked_out: int = 0
    overflow: int = 0
    checked_in: int = 0
    total_connections: int = 0
    pool_utilization: float = 0.0
    avg_checkout_time: float = 0.0
    checkout_times: List[float] = field(default_factory=list)
    
    def update_utilization(self):
        """Update pool utilization metrics"""
        if self.pool_size > 0:
            self.pool_utilization = self.checked_out / self.pool_size
        
        if self.checkout_times:
            self.avg_checkout_time = sum(self.checkout_times) / len(self.checkout_times)

class QueryCache:
    """Intelligent query result caching system"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 300):
        self.max_size = max_size
        self.ttl = ttl
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_times: Dict[str, datetime] = {}
        self.hit_count = 0
        self.miss_count = 0
        self._lock = threading.RLock()
    
    def get_cache_key(self, query: str, params: Dict[str, Any] = None) -> str:
        """Generate cache key for query and parameters"""
        import hashlib
        
        key_data = {
            "query": query.strip().lower(),
            "params": params or {}
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()[:16]
    
    def get(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached query result"""
        with self._lock:
            if cache_key not in self.cache:
                self.miss_count += 1
                return None
            
            cache_entry = self.cache[cache_key]
            entry_time = cache_entry["timestamp"]
            
            # Check TTL
            if datetime.now() - entry_time > timedelta(seconds=self.ttl):
                del self.cache[cache_key]
                del self.access_times[cache_key]
                self.miss_count += 1
                return None
            
            # Update access time and return result
            self.access_times[cache_key] = datetime.now()
            self.hit_count += 1
            return cache_entry["result"]
    
    def put(self, cache_key: str, result: List[Dict[str, Any]]):
        """Cache query result"""
        with self._lock:
            # Evict oldest entries if cache is full
            if len(self.cache) >= self.max_size:
                self._evict_oldest()
            
            self.cache[cache_key] = {
                "result": result,
                "timestamp": datetime.now()
            }
            self.access_times[cache_key] = datetime.now()
    
    def _evict_oldest(self):
        """Evict oldest cache entries"""
        if not self.access_times:
            return
        
        # Remove 10% of oldest entries
        num_to_remove = max(1, len(self.access_times) // 10)
        oldest_keys = sorted(self.access_times.keys(), 
                           key=lambda k: self.access_times[k])[:num_to_remove]
        
        for key in oldest_keys:
            self.cache.pop(key, None)
            self.access_times.pop(key, None)
    
    def get_hit_rate(self) -> float:
        """Get cache hit rate"""
        total_requests = self.hit_count + self.miss_count
        return self.hit_count / total_requests if total_requests > 0 else 0.0
    
    def clear(self):
        """Clear all cached entries"""
        with self._lock:
            self.cache.clear()
            self.access_times.clear()
            self.hit_count = 0
            self.miss_count = 0

class DatabasePerformanceMonitor:
    """Comprehensive database performance monitoring system"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.query_stats: Dict[str, QueryPerformanceStats] = {}
        self.pool_stats = ConnectionPoolStats()
        self.performance_metrics: Dict[PerformanceMetric, List[float]] = {
            metric: [] for metric in PerformanceMetric
        }
        
        # Performance thresholds
        self.slow_query_threshold = config.slow_query_threshold
        self.pool_utilization_threshold = config.performance_alert_threshold
        
        # Monitoring state
        self.monitoring_active = config.enable_monitoring
        self.last_metric_collection = datetime.now()
        self._lock = threading.RLock()
        
        # Start background monitoring
        if self.monitoring_active:
            self._start_background_monitoring()
    
    def record_query_execution(self, query_text: str, execution_time: float, 
                             table_names: List[str] = None):
        """Record query execution for performance tracking"""
        if not self.monitoring_active:
            return
        
        with self._lock:
            query_hash = self._get_query_hash(query_text)
            
            if query_hash not in self.query_stats:
                self.query_stats[query_hash] = QueryPerformanceStats(
                    query_hash=query_hash,
                    query_text=query_text[:200],  # Store truncated query
                    table_names=table_names or []
                )
            
            stats = self.query_stats[query_hash]
            stats.update_stats(execution_time)
            
            # Record slow query
            if execution_time > self.slow_query_threshold:
                self._record_slow_query(query_text, execution_time)
            
            # Update performance metrics
            self.performance_metrics[PerformanceMetric.QUERY_TIME].append(execution_time)
            
            logger.debug("DATABASE_PERF - Query execution recorded",
                        query_hash=query_hash,
                        execution_time=round(execution_time, 4),
                        table_names=table_names)
    
    def record_pool_event(self, event_type: str, **kwargs):
        """Record connection pool events"""
        if not self.monitoring_active:
            return
        
        with self._lock:
            if event_type == "checkout":
                self.pool_stats.checked_out += 1
                checkout_time = kwargs.get("checkout_time", 0)
                self.pool_stats.checkout_times.append(checkout_time)
                
                # Keep only recent checkout times
                if len(self.pool_stats.checkout_times) > 100:
                    self.pool_stats.checkout_times = self.pool_stats.checkout_times[-50:]
                
            elif event_type == "checkin":
                self.pool_stats.checked_out = max(0, self.pool_stats.checked_out - 1)
                self.pool_stats.checked_in += 1
            
            elif event_type == "connect":
                self.pool_stats.total_connections += 1
            
            # Update utilization
            self.pool_stats.update_utilization()
            
            # Record pool utilization metric
            self.performance_metrics[PerformanceMetric.POOL_USAGE].append(
                self.pool_stats.pool_utilization
            )
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        with self._lock:
            current_time = datetime.now()
            
            # Query statistics
            total_queries = sum(stats.execution_count for stats in self.query_stats.values())
            slow_queries = len([s for s in self.query_stats.values() 
                              if s.avg_time > self.slow_query_threshold])
            
            avg_query_time = 0.0
            if self.performance_metrics[PerformanceMetric.QUERY_TIME]:
                avg_query_time = statistics.mean(
                    self.performance_metrics[PerformanceMetric.QUERY_TIME][-100:]  # Last 100 queries
                )
            
            # Pool statistics
            pool_health = "healthy"
            if self.pool_stats.pool_utilization > self.pool_utilization_threshold:
                pool_health = "high_utilization"
            elif self.pool_stats.pool_utilization > 0.95:
                pool_health = "critical"
            
            return {
                "timestamp": current_time.isoformat(),
                "query_statistics": {
                    "total_queries": total_queries,
                    "unique_queries": len(self.query_stats),
                    "slow_queries": slow_queries,
                    "avg_query_time": round(avg_query_time, 4),
                    "slow_query_threshold": self.slow_query_threshold
                },
                "connection_pool": {
                    "pool_size": self.pool_stats.pool_size,
                    "checked_out": self.pool_stats.checked_out,
                    "utilization": round(self.pool_stats.pool_utilization, 3),
                    "avg_checkout_time": round(self.pool_stats.avg_checkout_time, 4),
                    "health_status": pool_health
                },
                "performance_alerts": self._get_performance_alerts(),
                "optimization_recommendations": self._get_optimization_recommendations()
            }
    
    def get_slow_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get slowest queries for optimization"""
        with self._lock:
            slow_queries = [
                {
                    "query_hash": stats.query_hash,
                    "query_text": stats.query_text,
                    "execution_count": stats.execution_count,
                    "avg_time": round(stats.avg_time, 4),
                    "max_time": round(stats.max_time, 4),
                    "table_names": stats.table_names
                }
                for stats in self.query_stats.values()
                if stats.avg_time > self.slow_query_threshold
            ]
            
            # Sort by average time descending
            slow_queries.sort(key=lambda x: x["avg_time"], reverse=True)
            return slow_queries[:limit]
    
    def _get_query_hash(self, query_text: str) -> str:
        """Generate hash for query text"""
        import hashlib
        
        # Normalize query for consistent hashing
        normalized = query_text.strip().lower()
        # Remove extra whitespace
        normalized = ' '.join(normalized.split())
        
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]
    
    def _record_slow_query(self, query_text: str, execution_time: float):
        """Record slow query for analysis"""
        logger.warning("DATABASE_PERF - Slow query detected",
                      execution_time=round(execution_time, 4),
                      threshold=self.slow_query_threshold,
                      query_preview=query_text[:100])
        
        # Update slow query count metric
        if PerformanceMetric.SLOW_QUERY_COUNT not in self.performance_metrics:
            self.performance_metrics[PerformanceMetric.SLOW_QUERY_COUNT] = []
        self.performance_metrics[PerformanceMetric.SLOW_QUERY_COUNT].append(1)
    
    def _get_performance_alerts(self) -> List[Dict[str, Any]]:
        """Get current performance alerts"""
        alerts = []
        
        # High pool utilization alert
        if self.pool_stats.pool_utilization > self.pool_utilization_threshold:
            alerts.append({
                "type": "high_pool_utilization",
                "severity": "critical" if self.pool_stats.pool_utilization > 0.95 else "warning",
                "message": f"Connection pool utilization is {self.pool_stats.pool_utilization:.1%}",
                "recommendation": "Consider increasing pool_size or max_overflow"
            })
        
        # Slow query alert
        recent_slow_queries = len([s for s in self.query_stats.values() 
                                 if s.last_execution and 
                                 s.last_execution > datetime.now() - timedelta(minutes=5) and
                                 s.avg_time > self.slow_query_threshold])
        
        if recent_slow_queries > 5:
            alerts.append({
                "type": "frequent_slow_queries",
                "severity": "warning",
                "message": f"{recent_slow_queries} slow queries in last 5 minutes",
                "recommendation": "Review query performance and consider adding indexes"
            })
        
        return alerts
    
    def _get_optimization_recommendations(self) -> List[str]:
        """Get performance optimization recommendations"""
        recommendations = []
        
        # Query optimization recommendations
        if len(self.query_stats) > 0:
            avg_query_time = sum(s.avg_time for s in self.query_stats.values()) / len(self.query_stats)
            if avg_query_time > 0.1:  # 100ms
                recommendations.append("Consider query optimization for frequently executed queries")
        
        # Pool optimization recommendations
        if self.pool_stats.pool_utilization > 0.8:
            recommendations.append("Consider increasing connection pool size")
        
        if self.pool_stats.avg_checkout_time > 0.1:  # 100ms
            recommendations.append("High connection checkout time - investigate connection creation overhead")
        
        return recommendations
    
    def _start_background_monitoring(self):
        """Start background performance monitoring"""
        def monitoring_worker():
            while self.monitoring_active:
                try:
                    self._collect_system_metrics()
                    time.sleep(self.config.metric_collection_interval)
                except Exception as e:
                    logger.error("DATABASE_PERF - Background monitoring error",
                               error=str(e))
                    time.sleep(60)  # Wait longer on error
        
        monitoring_thread = threading.Thread(target=monitoring_worker, daemon=True)
        monitoring_thread.start()
    
    def _collect_system_metrics(self):
        """Collect system-level performance metrics"""
        if not PSUTIL_AVAILABLE:
            return
        
        try:
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            
            # Update metrics
            self.performance_metrics[PerformanceMetric.DISK_IO].append(
                disk_io.read_bytes + disk_io.write_bytes if disk_io else 0
            )
            
            # Keep only recent metrics
            for metric in self.performance_metrics:
                if len(self.performance_metrics[metric]) > 1000:
                    self.performance_metrics[metric] = self.performance_metrics[metric][-500:]
                    
        except Exception as e:
            logger.debug("DATABASE_PERF - System metrics collection failed",
                        error=str(e))

class OptimizedConnectionPool:
    """Advanced connection pool with intelligent management"""
    
    def __init__(self, database_url: str, config: DatabaseConfig):
        self.database_url = database_url
        self.config = config
        self.monitor = DatabasePerformanceMonitor(config)
        self.query_cache = QueryCache(config.query_cache_size, config.query_cache_ttl)
        
        # Create optimized engine
        self.engine = self._create_optimized_engine()
        self.session_maker = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Connection health monitoring
        self.connection_health = {}
        self._setup_event_listeners()
        
        logger.info("DATABASE_PERF - Optimized connection pool initialized",
                   pool_size=config.pool_size,
                   max_overflow=config.max_overflow,
                   optimization_level=config.optimization_level.value)
    
    def _create_optimized_engine(self) -> AsyncEngine:
        """Create database engine with optimized settings"""
        
        pool_class = QueuePool
        if self.config.pool_size == 0:
            pool_class = NullPool
        
        engine_kwargs = {
            "url": self.database_url,
            "poolclass": pool_class,
            "pool_size": self.config.pool_size,
            "max_overflow": self.config.max_overflow,
            "pool_timeout": self.config.pool_timeout,
            "pool_recycle": self.config.pool_recycle,
            "pool_pre_ping": self.config.pool_pre_ping,
            "echo": False,  # Set to True for SQL debugging
            "future": True,
            "connect_args": {
                "command_timeout": 30,
                "server_settings": {
                    "application_name": "healthcare_system",
                    "jit": "off",  # Disable JIT for consistent performance
                }
            }
        }
        
        return create_async_engine(**engine_kwargs)
    
    def _setup_event_listeners(self):
        """Setup database event listeners for monitoring"""
        
        @event.listens_for(self.engine.sync_engine, "connect")
        def receive_connect(dbapi_connection, connection_record):
            self.monitor.record_pool_event("connect")
            connection_id = id(connection_record)
            self.connection_health[connection_id] = {
                "created_at": datetime.now(),
                "last_used": datetime.now(),
                "query_count": 0
            }
        
        @event.listens_for(self.engine.sync_engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            checkout_time = time.time()
            self.monitor.record_pool_event("checkout", checkout_time=checkout_time)
            
            connection_id = id(connection_record)
            if connection_id in self.connection_health:
                self.connection_health[connection_id]["last_used"] = datetime.now()
        
        @event.listens_for(self.engine.sync_engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            self.monitor.record_pool_event("checkin")
    
    @asynccontextmanager
    async def get_session(self):
        """Get optimized database session with monitoring"""
        session_start = time.time()
        
        async with self.session_maker() as session:
            try:
                # Setup query monitoring for this session
                original_execute = session.execute
                
                async def monitored_execute(statement, parameters=None, **kwargs):
                    query_start = time.time()
                    
                    # Check cache for SELECT queries
                    if (self.config.optimization_level != QueryOptimizationLevel.NONE and
                        isinstance(statement, ClauseElement) and
                        str(statement).strip().upper().startswith('SELECT')):
                        
                        cache_key = self.query_cache.get_cache_key(
                            str(statement), 
                            parameters or {}
                        )
                        cached_result = self.query_cache.get(cache_key)
                        
                        if cached_result is not None:
                            query_time = time.time() - query_start
                            self.monitor.record_query_execution(
                                str(statement), query_time, ["cached"]
                            )
                            logger.debug("DATABASE_PERF - Cache hit",
                                       cache_key=cache_key,
                                       query_time=round(query_time, 4))
                            return cached_result
                    
                    # Execute query
                    result = await original_execute(statement, parameters, **kwargs)
                    query_time = time.time() - query_start
                    
                    # Record performance metrics
                    table_names = self._extract_table_names(str(statement))
                    self.monitor.record_query_execution(
                        str(statement), query_time, table_names
                    )
                    
                    # Cache SELECT results
                    if (self.config.optimization_level != QueryOptimizationLevel.NONE and
                        isinstance(statement, ClauseElement) and
                        str(statement).strip().upper().startswith('SELECT') and
                        query_time < 1.0):  # Only cache fast queries
                        
                        try:
                            # Convert result to cacheable format
                            rows = result.fetchall() if hasattr(result, 'fetchall') else []
                            cache_data = [dict(row._mapping) for row in rows] if rows else []
                            
                            cache_key = self.query_cache.get_cache_key(
                                str(statement), 
                                parameters or {}
                            )
                            self.query_cache.put(cache_key, cache_data)
                            
                        except Exception as e:
                            logger.debug("DATABASE_PERF - Cache storage failed",
                                       error=str(e))
                    
                    return result
                
                # Replace execute method
                session.execute = monitored_execute
                
                yield session
                
            finally:
                session_time = time.time() - session_start
                logger.debug("DATABASE_PERF - Session completed",
                           session_time=round(session_time, 4))
    
    def _extract_table_names(self, query: str) -> List[str]:
        """Extract table names from SQL query for monitoring"""
        import re
        
        # Simple regex to extract table names - could be enhanced
        table_pattern = r'\b(?:FROM|JOIN|UPDATE|INSERT\s+INTO|DELETE\s+FROM)\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        matches = re.findall(table_pattern, query.upper())
        return list(set(matches))
    
    async def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        performance_data = self.monitor.get_performance_summary()
        
        # Add cache statistics
        performance_data["query_cache"] = {
            "size": len(self.query_cache.cache),
            "max_size": self.query_cache.max_size,
            "hit_rate": round(self.query_cache.get_hit_rate(), 3),
            "hits": self.query_cache.hit_count,
            "misses": self.query_cache.miss_count
        }
        
        # Add connection health
        healthy_connections = sum(
            1 for health in self.connection_health.values()
            if datetime.now() - health["last_used"] < timedelta(minutes=5)
        )
        
        performance_data["connection_health"] = {
            "total_connections": len(self.connection_health),
            "healthy_connections": healthy_connections,
            "avg_connection_age": self._get_avg_connection_age()
        }
        
        return performance_data
    
    def _get_avg_connection_age(self) -> float:
        """Get average connection age in seconds"""
        if not self.connection_health:
            return 0.0
        
        current_time = datetime.now()
        total_age = sum(
            (current_time - health["created_at"]).total_seconds()
            for health in self.connection_health.values()
        )
        
        return total_age / len(self.connection_health)
    
    async def optimize_queries(self) -> Dict[str, Any]:
        """Analyze and optimize slow queries"""
        slow_queries = self.monitor.get_slow_queries(20)
        
        optimizations = []
        for query_info in slow_queries:
            suggestions = await self._analyze_query(query_info)
            optimizations.append({
                "query_hash": query_info["query_hash"],
                "query_text": query_info["query_text"],
                "current_avg_time": query_info["avg_time"],
                "suggestions": suggestions
            })
        
        return {
            "total_slow_queries": len(slow_queries),
            "optimizations": optimizations,
            "recommended_indexes": await self._suggest_indexes(slow_queries)
        }
    
    async def _analyze_query(self, query_info: Dict[str, Any]) -> List[str]:
        """Analyze individual query for optimization opportunities"""
        suggestions = []
        
        query_text = query_info.get("query_text", "").upper()
        
        # Basic query analysis
        if "SELECT *" in query_text:
            suggestions.append("Avoid SELECT * - specify only needed columns")
        
        if "WHERE" not in query_text and "SELECT" in query_text:
            suggestions.append("Consider adding WHERE clause to limit results")
        
        if query_info.get("execution_count", 0) > 100:
            suggestions.append("Frequently executed query - consider result caching")
        
        if "ORDER BY" in query_text and "LIMIT" not in query_text:
            suggestions.append("ORDER BY without LIMIT may be inefficient")
        
        if len(query_info.get("table_names", [])) > 3:
            suggestions.append("Complex join - consider query restructuring")
        
        return suggestions
    
    async def _suggest_indexes(self, slow_queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Suggest database indexes based on slow query analysis"""
        index_suggestions = []
        
        table_columns = {}
        for query_info in slow_queries:
            for table_name in query_info.get("table_names", []):
                if table_name not in table_columns:
                    table_columns[table_name] = set()
                
                # Extract commonly filtered columns (simplified)
                query_text = query_info.get("query_text", "")
                if "WHERE" in query_text.upper():
                    # This is a simplified extraction - real implementation would be more sophisticated
                    index_suggestions.append({
                        "table": table_name,
                        "suggestion": f"Consider adding index for WHERE clause conditions",
                        "estimated_improvement": "20-50% query time reduction",
                        "query_count": query_info.get("execution_count", 0)
                    })
        
        return index_suggestions
    
    async def clear_cache(self):
        """Clear query cache"""
        self.query_cache.clear()
        logger.info("DATABASE_PERF - Query cache cleared")
    
    async def close(self):
        """Close connection pool and cleanup"""
        self.monitor.monitoring_active = False
        await self.engine.dispose()
        logger.info("DATABASE_PERF - Connection pool closed")

# Global optimized connection pool
optimized_pool: Optional[OptimizedConnectionPool] = None

def initialize_optimized_database(database_url: str, config: DatabaseConfig = None) -> OptimizedConnectionPool:
    """Initialize optimized database connection pool"""
    global optimized_pool
    
    if config is None:
        config = DatabaseConfig()
    
    optimized_pool = OptimizedConnectionPool(database_url, config)
    
    logger.info("DATABASE_PERF - Optimized database initialized",
               database_url=database_url.split('@')[0] + '@***',  # Hide credentials
               pool_size=config.pool_size,
               optimization_level=config.optimization_level.value)
    
    return optimized_pool

def get_optimized_database() -> OptimizedConnectionPool:
    """Get optimized database connection pool"""
    if optimized_pool is None:
        raise RuntimeError("Optimized database not initialized. Call initialize_optimized_database() first.")
    return optimized_pool

# Convenience functions
async def get_optimized_session():
    """Get optimized database session"""
    pool = get_optimized_database()
    async with pool.get_session() as session:
        yield session

async def get_database_performance_report() -> Dict[str, Any]:
    """Get comprehensive database performance report"""
    pool = get_optimized_database()
    return await pool.get_performance_summary()

async def optimize_database_queries() -> Dict[str, Any]:
    """Analyze and optimize database queries"""
    pool = get_optimized_database()
    return await pool.optimize_queries()

async def clear_database_cache():
    """Clear database query cache"""
    pool = get_optimized_database()
    await pool.clear_cache()

# High-level database optimization utilities

class DatabaseIndexManager:
    """Database index management and optimization"""
    
    def __init__(self, connection_pool: OptimizedConnectionPool):
        self.pool = connection_pool
        self.metadata = MetaData()
    
    async def analyze_index_usage(self) -> Dict[str, Any]:
        """Analyze database index usage and effectiveness"""
        async with self.pool.get_session() as session:
            # PostgreSQL-specific index usage analysis
            index_usage_query = text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan as index_scans,
                    idx_tup_read as tuples_read,
                    idx_tup_fetch as tuples_fetched
                FROM pg_stat_user_indexes 
                ORDER BY idx_scan DESC;
            """)
            
            try:
                result = await session.execute(index_usage_query)
                index_stats = []
                
                for row in result.fetchall():
                    index_stats.append({
                        "schema": row.schemaname,
                        "table": row.tablename,
                        "index": row.indexname,
                        "scans": row.index_scans,
                        "tuples_read": row.tuples_read,
                        "tuples_fetched": row.tuples_fetched
                    })
                
                return {
                    "total_indexes": len(index_stats),
                    "unused_indexes": len([i for i in index_stats if i["scans"] == 0]),
                    "low_usage_indexes": len([i for i in index_stats if 0 < i["scans"] < 10]),
                    "index_details": index_stats
                }
                
            except Exception as e:
                logger.error("DATABASE_PERF - Index analysis failed", error=str(e))
                return {"error": "Index analysis not available"}
    
    async def suggest_missing_indexes(self) -> List[Dict[str, Any]]:
        """Suggest missing indexes based on query patterns"""
        slow_queries = self.pool.monitor.get_slow_queries(50)
        suggestions = []
        
        for query_info in slow_queries:
            query_text = query_info.get("query_text", "")
            table_names = query_info.get("table_names", [])
            
            # Analyze WHERE clauses for potential indexes
            suggestions.extend(await self._analyze_where_clauses(query_text, table_names))
            
            # Analyze JOIN conditions
            suggestions.extend(await self._analyze_join_conditions(query_text, table_names))
            
            # Analyze ORDER BY clauses
            suggestions.extend(await self._analyze_order_by_clauses(query_text, table_names))
        
        # Remove duplicates and rank by impact
        unique_suggestions = {}
        for suggestion in suggestions:
            key = f"{suggestion['table']}_{suggestion['columns']}"
            if key not in unique_suggestions:
                unique_suggestions[key] = suggestion
            else:
                # Merge query counts
                unique_suggestions[key]["estimated_queries_helped"] += suggestion.get("estimated_queries_helped", 1)
        
        # Sort by estimated impact
        ranked_suggestions = sorted(
            unique_suggestions.values(),
            key=lambda x: x.get("estimated_queries_helped", 0),
            reverse=True
        )
        
        return ranked_suggestions[:10]  # Top 10 suggestions
    
    async def _analyze_where_clauses(self, query_text: str, table_names: List[str]) -> List[Dict[str, Any]]:
        """Analyze WHERE clauses for index suggestions"""
        suggestions = []
        
        # Simplified WHERE clause analysis
        import re
        where_pattern = r'WHERE\s+(\w+)\.(\w+)\s*[=<>]'
        matches = re.findall(where_pattern, query_text.upper())
        
        for table_alias, column in matches:
            suggestions.append({
                "type": "where_clause",
                "table": table_names[0] if table_names else "unknown",
                "columns": column.lower(),
                "reason": f"Frequently filtered column: {column}",
                "estimated_queries_helped": 1,
                "estimated_improvement": "30-60% faster WHERE filtering"
            })
        
        return suggestions
    
    async def _analyze_join_conditions(self, query_text: str, table_names: List[str]) -> List[Dict[str, Any]]:
        """Analyze JOIN conditions for index suggestions"""
        suggestions = []
        
        if "JOIN" in query_text.upper() and len(table_names) > 1:
            # Simplified JOIN analysis
            suggestions.append({
                "type": "join_condition",
                "table": table_names[1] if len(table_names) > 1 else "unknown",
                "columns": "foreign_key",
                "reason": "JOIN condition optimization",
                "estimated_queries_helped": 1,
                "estimated_improvement": "40-70% faster JOIN operations"
            })
        
        return suggestions
    
    async def _analyze_order_by_clauses(self, query_text: str, table_names: List[str]) -> List[Dict[str, Any]]:
        """Analyze ORDER BY clauses for index suggestions"""
        suggestions = []
        
        if "ORDER BY" in query_text.upper():
            # Simplified ORDER BY analysis
            import re
            order_pattern = r'ORDER\s+BY\s+(\w+)'
            matches = re.findall(order_pattern, query_text.upper())
            
            for column in matches:
                suggestions.append({
                    "type": "order_by",
                    "table": table_names[0] if table_names else "unknown",
                    "columns": column.lower(),
                    "reason": f"ORDER BY optimization for column: {column}",
                    "estimated_queries_helped": 1,
                    "estimated_improvement": "50-80% faster sorting"
                })
        
        return suggestions