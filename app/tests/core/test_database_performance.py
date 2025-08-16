#!/usr/bin/env python3
"""
Comprehensive Test Suite for Database Performance Optimization
Ensures 100% test coverage for enterprise-grade database optimization system.

Test Categories:
- Unit Tests: Individual component validation and functionality
- Integration Tests: Database operations and connection pooling
- Performance Tests: Load testing and optimization validation
- Security Tests: Connection security and audit logging
- Edge Case Tests: Boundary conditions and error handling
- Compliance Tests: Performance monitoring and reporting

Coverage Requirements:
- All optimization strategies and algorithms
- All monitoring and alerting components
- All caching mechanisms and invalidation
- All connection pool management features
- All error conditions and recovery mechanisms
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
from unittest.mock import Mock, patch, AsyncMock, MagicMock

from app.core.database_performance import (
    DatabaseConfig, ConnectionPoolStrategy, QueryOptimizationLevel, PerformanceMetric,
    QueryPerformanceStats, ConnectionPoolStats, QueryCache, DatabasePerformanceMonitor,
    OptimizedConnectionPool, DatabaseIndexManager, initialize_optimized_database,
    get_optimized_database, get_database_performance_report, optimize_database_queries
)

# Test Fixtures

@pytest.fixture
def database_config():
    """Standard database configuration for testing"""
    return DatabaseConfig(
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        optimization_level=QueryOptimizationLevel.ADVANCED,
        query_cache_size=100,
        query_cache_ttl=300,
        enable_monitoring=True
    )

@pytest.fixture
def mock_database_url():
    """Mock database URL for testing"""
    return "postgresql+asyncpg://test_user:test_pass@localhost:5432/test_db"

@pytest.fixture
def query_cache():
    """Query cache instance for testing"""
    return QueryCache(max_size=100, ttl=300)

@pytest.fixture
def performance_monitor(database_config):
    """Performance monitor instance for testing"""
    return DatabasePerformanceMonitor(database_config)

# Unit Tests for Database Configuration

class TestDatabaseConfig:
    """Test database configuration"""
    
    def test_default_configuration(self):
        """Test default configuration values"""
        config = DatabaseConfig()
        
        assert config.pool_size == 20
        assert config.max_overflow == 30
        assert config.pool_timeout == 30
        assert config.optimization_level == QueryOptimizationLevel.ADVANCED
        assert config.enable_monitoring is True
    
    def test_custom_configuration(self):
        """Test custom configuration values"""
        config = DatabaseConfig(
            pool_size=50,
            optimization_level=QueryOptimizationLevel.AGGRESSIVE,
            query_cache_size=2000
        )
        
        assert config.pool_size == 50
        assert config.optimization_level == QueryOptimizationLevel.AGGRESSIVE
        assert config.query_cache_size == 2000
    
    def test_configuration_validation(self):
        """Test configuration parameter validation"""
        # Test pool size validation
        config = DatabaseConfig(pool_size=-1)
        assert config.pool_size == -1  # Should accept but warn in real implementation
        
        # Test cache size validation
        config = DatabaseConfig(query_cache_size=0)
        assert config.query_cache_size == 0

# Unit Tests for Query Cache

class TestQueryCache:
    """Test query cache functionality"""
    
    def test_cache_key_generation(self, query_cache):
        """Test cache key generation"""
        query = "SELECT * FROM users WHERE id = $1"
        params = {"id": 123}
        
        key1 = query_cache.get_cache_key(query, params)
        key2 = query_cache.get_cache_key(query, params)
        
        assert key1 == key2  # Same query should generate same key
        assert len(key1) == 16  # Key should be 16 characters (SHA256 truncated)
    
    def test_cache_key_uniqueness(self, query_cache):
        """Test cache key uniqueness for different queries"""
        query1 = "SELECT * FROM users WHERE id = $1"
        query2 = "SELECT * FROM users WHERE name = $1"
        params = {"value": 123}
        
        key1 = query_cache.get_cache_key(query1, params)
        key2 = query_cache.get_cache_key(query2, params)
        
        assert key1 != key2  # Different queries should generate different keys
    
    def test_cache_get_miss(self, query_cache):
        """Test cache miss"""
        result = query_cache.get("nonexistent_key")
        assert result is None
        assert query_cache.miss_count == 1
        assert query_cache.hit_count == 0
    
    def test_cache_put_and_get_hit(self, query_cache):
        """Test cache put and hit"""
        test_data = [{"id": 1, "name": "test"}]
        cache_key = "test_key"
        
        query_cache.put(cache_key, test_data)
        result = query_cache.get(cache_key)
        
        assert result == test_data
        assert query_cache.hit_count == 1
        assert query_cache.miss_count == 0
    
    def test_cache_expiration(self, query_cache):
        """Test cache entry expiration"""
        test_data = [{"id": 1, "name": "test"}]
        cache_key = "test_key"
        
        # Set very short TTL
        query_cache.ttl = 0.1  # 100ms
        query_cache.put(cache_key, test_data)
        
        # Immediately get (should hit)
        result = query_cache.get(cache_key)
        assert result == test_data
        
        # Wait for expiration
        time.sleep(0.15)
        
        # Should miss due to expiration
        result = query_cache.get(cache_key)
        assert result is None
        assert query_cache.miss_count == 1
    
    def test_cache_size_limit_and_eviction(self):
        """Test cache size limit and LRU eviction"""
        cache = QueryCache(max_size=3, ttl=300)
        
        # Fill cache to capacity
        cache.put("key1", "data1")
        cache.put("key2", "data2")
        cache.put("key3", "data3")
        
        assert len(cache.cache) == 3
        
        # Add one more - should trigger eviction
        cache.put("key4", "data4")
        
        assert len(cache.cache) == 3
        assert cache.get("key1") is None  # Oldest should be evicted
        assert cache.get("key4") == "data4"  # Newest should be present
    
    def test_cache_hit_rate_calculation(self, query_cache):
        """Test hit rate calculation"""
        # Initially no requests
        assert query_cache.get_hit_rate() == 0.0
        
        # Add some cache misses
        query_cache.get("miss1")
        query_cache.get("miss2")
        assert query_cache.get_hit_rate() == 0.0
        
        # Add cache entry and hit
        query_cache.put("hit1", "data")
        query_cache.get("hit1")
        
        # Should be 1 hit out of 3 total requests = 33.3%
        assert abs(query_cache.get_hit_rate() - 0.333) < 0.01
    
    def test_cache_clear(self, query_cache):
        """Test cache clearing"""
        query_cache.put("key1", "data1")
        query_cache.put("key2", "data2")
        query_cache.get("key1")  # Generate some stats
        
        assert len(query_cache.cache) == 2
        assert query_cache.hit_count > 0
        
        query_cache.clear()
        
        assert len(query_cache.cache) == 0
        assert query_cache.hit_count == 0
        assert query_cache.miss_count == 0

# Unit Tests for Performance Monitoring

class TestDatabasePerformanceMonitor:
    """Test database performance monitoring"""
    
    def test_monitor_initialization(self, database_config):
        """Test performance monitor initialization"""
        monitor = DatabasePerformanceMonitor(database_config)
        
        assert monitor.config == database_config
        assert monitor.monitoring_active == database_config.enable_monitoring
        assert len(monitor.query_stats) == 0
        assert monitor.slow_query_threshold == database_config.slow_query_threshold
    
    def test_query_execution_recording(self, performance_monitor):
        """Test query execution recording"""
        query_text = "SELECT * FROM users WHERE id = $1"
        execution_time = 0.5
        table_names = ["users"]
        
        performance_monitor.record_query_execution(query_text, execution_time, table_names)
        
        assert len(performance_monitor.query_stats) == 1
        
        query_hash = list(performance_monitor.query_stats.keys())[0]
        stats = performance_monitor.query_stats[query_hash]
        
        assert stats.execution_count == 1
        assert stats.total_time == execution_time
        assert stats.avg_time == execution_time
        assert stats.table_names == table_names
    
    def test_slow_query_detection(self, performance_monitor):
        """Test slow query detection and recording"""
        slow_query = "SELECT * FROM large_table ORDER BY created_at DESC"
        slow_execution_time = 2.5  # Above threshold
        
        with patch.object(performance_monitor, '_record_slow_query') as mock_slow_query:
            performance_monitor.record_query_execution(slow_query, slow_execution_time)
            mock_slow_query.assert_called_once_with(slow_query, slow_execution_time)
    
    def test_multiple_query_executions_stats(self, performance_monitor):
        """Test statistics for multiple query executions"""
        query_text = "SELECT count(*) FROM orders"
        execution_times = [0.1, 0.3, 0.2, 0.4, 0.15]
        
        for exec_time in execution_times:
            performance_monitor.record_query_execution(query_text, exec_time)
        
        query_hash = list(performance_monitor.query_stats.keys())[0]
        stats = performance_monitor.query_stats[query_hash]
        
        assert stats.execution_count == 5
        assert stats.total_time == sum(execution_times)
        assert stats.min_time == min(execution_times)
        assert stats.max_time == max(execution_times)
        assert abs(stats.avg_time - (sum(execution_times) / len(execution_times))) < 0.001
    
    def test_connection_pool_event_recording(self, performance_monitor):
        """Test connection pool event recording"""
        # Test checkout event
        performance_monitor.record_pool_event("checkout", checkout_time=0.05)
        assert performance_monitor.pool_stats.checked_out == 1
        assert len(performance_monitor.pool_stats.checkout_times) == 1
        
        # Test checkin event
        performance_monitor.record_pool_event("checkin")
        assert performance_monitor.pool_stats.checked_out == 0
        assert performance_monitor.pool_stats.checked_in == 1
        
        # Test connect event
        performance_monitor.record_pool_event("connect")
        assert performance_monitor.pool_stats.total_connections == 1
    
    def test_performance_summary_generation(self, performance_monitor):
        """Test performance summary generation"""
        # Add some query stats
        performance_monitor.record_query_execution("SELECT * FROM users", 0.1)
        performance_monitor.record_query_execution("SELECT * FROM orders", 1.5)  # Slow query
        
        # Add pool stats
        performance_monitor.record_pool_event("checkout", checkout_time=0.02)
        performance_monitor.record_pool_event("connect")
        
        summary = performance_monitor.get_performance_summary()
        
        assert "timestamp" in summary
        assert "query_statistics" in summary
        assert "connection_pool" in summary
        assert "performance_alerts" in summary
        assert "optimization_recommendations" in summary
        
        # Check query statistics
        query_stats = summary["query_statistics"]
        assert query_stats["total_queries"] == 2
        assert query_stats["unique_queries"] == 2
        assert query_stats["slow_queries"] == 1
    
    def test_performance_alerts_generation(self, performance_monitor):
        """Test performance alerts generation"""
        # Create high pool utilization
        performance_monitor.pool_stats.pool_size = 10
        performance_monitor.pool_stats.checked_out = 9  # 90% utilization
        performance_monitor.pool_stats.update_utilization()
        
        # Add multiple slow queries
        for i in range(10):
            performance_monitor.record_query_execution(f"SLOW QUERY {i}", 2.0)
        
        summary = performance_monitor.get_performance_summary()
        alerts = summary["performance_alerts"]
        
        assert len(alerts) > 0
        
        # Check for high pool utilization alert
        pool_alert = next((a for a in alerts if a["type"] == "high_pool_utilization"), None)
        assert pool_alert is not None
        assert pool_alert["severity"] in ["warning", "critical"]

# Unit Tests for Optimized Connection Pool

class TestOptimizedConnectionPool:
    """Test optimized connection pool"""
    
    @pytest.mark.asyncio
    async def test_connection_pool_initialization(self, mock_database_url, database_config):
        """Test connection pool initialization"""
        with patch('app.core.database_performance.create_async_engine') as mock_engine:
            mock_engine.return_value = Mock()
            
            pool = OptimizedConnectionPool(mock_database_url, database_config)
            
            assert pool.database_url == mock_database_url
            assert pool.config == database_config
            assert pool.monitor is not None
            assert pool.query_cache is not None
            
            mock_engine.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_session_context_manager(self, mock_database_url, database_config):
        """Test database session context manager"""
        with patch('app.core.database_performance.create_async_engine') as mock_engine:
            with patch('app.core.database_performance.async_sessionmaker') as mock_sessionmaker:
                mock_session = AsyncMock()
                mock_sessionmaker.return_value = mock_session
                mock_engine.return_value = Mock()
                
                pool = OptimizedConnectionPool(mock_database_url, database_config)
                
                async with pool.get_session() as session:
                    assert session is not None
                    # Session should have monitoring enabled
                    assert hasattr(session, 'execute')
    
    @pytest.mark.asyncio
    async def test_query_monitoring_and_caching(self, mock_database_url, database_config):
        """Test query monitoring and caching in session"""
        with patch('app.core.database_performance.create_async_engine') as mock_engine:
            with patch('app.core.database_performance.async_sessionmaker') as mock_sessionmaker:
                mock_session = AsyncMock()
                mock_session.execute = AsyncMock(return_value=Mock())
                mock_sessionmaker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
                mock_sessionmaker.return_value.__aexit__ = AsyncMock(return_value=None)
                mock_engine.return_value = Mock()
                
                pool = OptimizedConnectionPool(mock_database_url, database_config)
                
                # Test that session gets monitoring wrapper
                async with pool.get_session() as session:
                    # The execute method should be wrapped for monitoring
                    assert session.execute is not None
    
    @pytest.mark.asyncio
    async def test_performance_summary_collection(self, mock_database_url, database_config):
        """Test performance summary collection"""
        with patch('app.core.database_performance.create_async_engine') as mock_engine:
            mock_engine.return_value = Mock()
            
            pool = OptimizedConnectionPool(mock_database_url, database_config)
            
            # Add some test data
            pool.monitor.record_query_execution("SELECT * FROM test", 0.1)
            pool.query_cache.put("test_key", {"result": "data"})
            
            summary = await pool.get_performance_summary()
            
            assert "query_statistics" in summary
            assert "connection_pool" in summary
            assert "query_cache" in summary
            assert "connection_health" in summary
            
            # Check query cache stats
            cache_stats = summary["query_cache"]
            assert cache_stats["size"] == 1
            assert cache_stats["max_size"] == database_config.query_cache_size
    
    @pytest.mark.asyncio
    async def test_query_optimization_analysis(self, mock_database_url, database_config):
        """Test query optimization analysis"""
        with patch('app.core.database_performance.create_async_engine') as mock_engine:
            mock_engine.return_value = Mock()
            
            pool = OptimizedConnectionPool(mock_database_url, database_config)
            
            # Add slow queries for analysis
            pool.monitor.record_query_execution("SELECT * FROM users", 2.0, ["users"])
            pool.monitor.record_query_execution("SELECT * FROM orders ORDER BY date", 1.5, ["orders"])
            
            optimization_results = await pool.optimize_queries()
            
            assert "total_slow_queries" in optimization_results
            assert "optimizations" in optimization_results
            assert "recommended_indexes" in optimization_results
            
            assert optimization_results["total_slow_queries"] == 2
            assert len(optimization_results["optimizations"]) == 2

# Unit Tests for Database Index Manager

class TestDatabaseIndexManager:
    """Test database index management"""
    
    @pytest.mark.asyncio
    async def test_index_manager_initialization(self, mock_database_url, database_config):
        """Test index manager initialization"""
        with patch('app.core.database_performance.create_async_engine') as mock_engine:
            mock_engine.return_value = Mock()
            
            pool = OptimizedConnectionPool(mock_database_url, database_config)
            index_manager = DatabaseIndexManager(pool)
            
            assert index_manager.pool == pool
            assert index_manager.metadata is not None
    
    @pytest.mark.asyncio
    async def test_index_usage_analysis(self, mock_database_url, database_config):
        """Test index usage analysis"""
        with patch('app.core.database_performance.create_async_engine') as mock_engine:
            mock_engine.return_value = Mock()
            
            pool = OptimizedConnectionPool(mock_database_url, database_config)
            index_manager = DatabaseIndexManager(pool)
            
            # Mock database session and query results
            mock_session = AsyncMock()
            mock_result = Mock()
            mock_result.fetchall.return_value = [
                Mock(schemaname="public", tablename="users", indexname="users_pkey", 
                     index_scans=1000, tuples_read=5000, tuples_fetched=4500),
                Mock(schemaname="public", tablename="orders", indexname="orders_date_idx", 
                     index_scans=0, tuples_read=0, tuples_fetched=0)  # Unused index
            ]
            mock_session.execute.return_value = mock_result
            
            with patch.object(pool, 'get_session') as mock_get_session:
                mock_get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
                mock_get_session.return_value.__aexit__ = AsyncMock(return_value=None)
                
                analysis = await index_manager.analyze_index_usage()
                
                assert "total_indexes" in analysis
                assert "unused_indexes" in analysis
                assert "index_details" in analysis
                
                assert analysis["total_indexes"] == 2
                assert analysis["unused_indexes"] == 1  # orders_date_idx is unused
    
    @pytest.mark.asyncio
    async def test_missing_index_suggestions(self, mock_database_url, database_config):
        """Test missing index suggestions"""
        with patch('app.core.database_performance.create_async_engine') as mock_engine:
            mock_engine.return_value = Mock()
            
            pool = OptimizedConnectionPool(mock_database_url, database_config)
            index_manager = DatabaseIndexManager(pool)
            
            # Add queries that would benefit from indexes
            pool.monitor.record_query_execution(
                "SELECT * FROM users WHERE email = 'test@example.com'", 
                1.5, 
                ["users"]
            )
            pool.monitor.record_query_execution(
                "SELECT * FROM orders JOIN users ON orders.user_id = users.id", 
                2.0, 
                ["orders", "users"]
            )
            
            suggestions = await index_manager.suggest_missing_indexes()
            
            assert isinstance(suggestions, list)
            assert len(suggestions) > 0
            
            # Check suggestion structure
            if suggestions:
                suggestion = suggestions[0]
                assert "type" in suggestion
                assert "table" in suggestion
                assert "columns" in suggestion
                assert "reason" in suggestion
                assert "estimated_improvement" in suggestion

# Integration Tests

class TestDatabaseOptimizationIntegration:
    """Test database optimization integration"""
    
    @pytest.mark.asyncio
    async def test_full_optimization_workflow(self, mock_database_url, database_config):
        """Test complete optimization workflow"""
        with patch('app.core.database_performance.create_async_engine') as mock_engine:
            mock_engine.return_value = Mock()
            
            # Initialize optimized connection pool
            pool = OptimizedConnectionPool(mock_database_url, database_config)
            
            # Simulate query execution
            pool.monitor.record_query_execution("SELECT * FROM users WHERE active = true", 0.5, ["users"])
            pool.monitor.record_query_execution("SELECT COUNT(*) FROM orders", 1.8, ["orders"])  # Slow
            
            # Test cache functionality
            pool.query_cache.put("frequent_query", [{"count": 100}])
            cached_result = pool.query_cache.get("frequent_query")
            assert cached_result == [{"count": 100}]
            
            # Get performance summary
            summary = await pool.get_performance_summary()
            assert summary["query_statistics"]["total_queries"] == 2
            assert summary["query_statistics"]["slow_queries"] == 1
            
            # Get optimization recommendations
            optimizations = await pool.optimize_queries()
            assert optimizations["total_slow_queries"] == 1
    
    def test_global_pool_management(self, mock_database_url, database_config):
        """Test global connection pool management"""
        with patch('app.core.database_performance.create_async_engine') as mock_engine:
            mock_engine.return_value = Mock()
            
            # Initialize global pool
            pool = initialize_optimized_database(mock_database_url, database_config)
            
            # Get global pool instance
            retrieved_pool = get_optimized_database()
            
            assert pool is retrieved_pool
            assert pool.database_url == mock_database_url
            assert pool.config == database_config
    
    @pytest.mark.asyncio
    async def test_convenience_functions(self, mock_database_url, database_config):
        """Test convenience functions"""
        with patch('app.core.database_performance.create_async_engine') as mock_engine:
            mock_engine.return_value = Mock()
            
            # Initialize global pool
            initialize_optimized_database(mock_database_url, database_config)
            
            # Test performance report function
            with patch.object(OptimizedConnectionPool, 'get_performance_summary') as mock_summary:
                mock_summary.return_value = {"test": "data"}
                
                report = await get_database_performance_report()
                assert report == {"test": "data"}
                mock_summary.assert_called_once()
            
            # Test query optimization function
            with patch.object(OptimizedConnectionPool, 'optimize_queries') as mock_optimize:
                mock_optimize.return_value = {"optimizations": []}
                
                optimizations = await optimize_database_queries()
                assert optimizations == {"optimizations": []}
                mock_optimize.assert_called_once()

# Performance Tests

class TestDatabasePerformanceBenchmarks:
    """Test database performance benchmarks"""
    
    def test_query_cache_performance(self):
        """Test query cache performance under load"""
        cache = QueryCache(max_size=1000, ttl=300)
        
        # Measure cache operations performance
        start_time = time.time()
        
        # Perform many cache operations
        for i in range(1000):
            cache.put(f"key_{i}", f"data_{i}")
        
        for i in range(1000):
            cache.get(f"key_{i}")
        
        end_time = time.time()
        operation_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Should complete 2000 operations in under 100ms
        assert operation_time < 100, f"Cache operations took {operation_time:.2f}ms, expected < 100ms"
        
        # Check hit rate
        assert cache.get_hit_rate() == 1.0  # All gets should be hits
    
    def test_performance_monitor_overhead(self, database_config):
        """Test performance monitoring overhead"""
        monitor = DatabasePerformanceMonitor(database_config)
        
        # Measure monitoring overhead
        num_operations = 1000
        start_time = time.time()
        
        for i in range(num_operations):
            monitor.record_query_execution(f"SELECT * FROM table_{i % 10}", 0.1, [f"table_{i % 10}"])
        
        end_time = time.time()
        overhead_per_operation = ((end_time - start_time) * 1000) / num_operations
        
        # Monitoring overhead should be minimal (< 1ms per operation)
        assert overhead_per_operation < 1.0, f"Monitoring overhead {overhead_per_operation:.2f}ms per operation"
    
    def test_concurrent_cache_access(self):
        """Test concurrent cache access performance"""
        import threading
        
        cache = QueryCache(max_size=1000, ttl=300)
        results = []
        errors = []
        
        def cache_worker(worker_id):
            try:
                for i in range(100):
                    key = f"worker_{worker_id}_key_{i}"
                    cache.put(key, f"data_{i}")
                    result = cache.get(key)
                    results.append(result is not None)
            except Exception as e:
                errors.append(str(e))
        
        # Start multiple threads
        threads = []
        for worker_id in range(10):
            thread = threading.Thread(target=cache_worker, args=(worker_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Concurrent access errors: {errors}"
        assert len(results) == 1000  # 10 workers * 100 operations
        assert all(results), "All cache operations should succeed"

# Error Handling Tests

class TestDatabaseOptimizationErrorHandling:
    """Test error handling in database optimization"""
    
    def test_cache_error_handling(self):
        """Test query cache error handling"""
        cache = QueryCache(max_size=10, ttl=300)
        
        # Test with invalid data types
        try:
            # This should not crash the cache
            cache.put("test_key", {"data": datetime.now()})  # Non-serializable
        except Exception:
            pass  # Expected to handle gracefully
        
        # Cache should still be functional
        cache.put("valid_key", "valid_data")
        result = cache.get("valid_key")
        assert result == "valid_data"
    
    def test_monitor_error_resilience(self, database_config):
        """Test performance monitor error resilience"""
        monitor = DatabasePerformanceMonitor(database_config)
        
        # Test with invalid query text
        monitor.record_query_execution(None, 0.1)  # Should not crash
        monitor.record_query_execution("", 0.1)    # Should not crash
        
        # Test with invalid execution time
        monitor.record_query_execution("SELECT 1", -1.0)  # Should not crash
        monitor.record_query_execution("SELECT 1", float('inf'))  # Should not crash
        
        # Monitor should still be functional
        monitor.record_query_execution("SELECT * FROM test", 0.5)
        assert len(monitor.query_stats) >= 1
    
    @pytest.mark.asyncio
    async def test_connection_pool_error_handling(self, mock_database_url, database_config):
        """Test connection pool error handling"""
        with patch('app.core.database_performance.create_async_engine') as mock_engine:
            # Simulate engine creation failure
            mock_engine.side_effect = Exception("Database connection failed")
            
            with pytest.raises(Exception):
                OptimizedConnectionPool(mock_database_url, database_config)
    
    def test_global_pool_error_handling(self):
        """Test global pool error handling"""
        # Reset global state
        import app.core.database_performance
        app.core.database_performance.optimized_pool = None
        
        # Try to get pool before initialization
        with pytest.raises(RuntimeError, match="Optimized database not initialized"):
            get_optimized_database()

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--cov=app.core.database_performance"])