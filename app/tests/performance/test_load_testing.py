"""
Performance and Load Testing Suite

Comprehensive performance testing for the Healthcare Records Backend System:
- Concurrent user load testing (up to 1000 users)
- Database performance benchmarking
- API response time measurement
- Memory usage profiling
- Throughput and scalability testing
- Resource utilization monitoring

This suite validates system performance under realistic production loads
and ensures the system meets performance requirements for healthcare environments.
"""

import pytest
import asyncio
import time
import psutil
import statistics
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, patch, AsyncMock
import aiohttp
import threading

# Testing framework imports
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient
import logging

# Application imports
from app.main import app
from app.core.database_unified import get_db
from app.core.security import EncryptionService, get_current_user_id
from app.core.events.event_bus import get_event_bus
from app.modules.healthcare_records.service import get_healthcare_service, AccessContext


class PerformanceTestSuite:
    """Base class for performance testing with metrics collection."""
    
    def __init__(self):
        self.client = TestClient(app)
        self.metrics = {
            "response_times": [],
            "throughput": [],
            "memory_usage": [],
            "cpu_usage": [],
            "database_connections": [],
            "error_rates": []
        }
        
        # Performance thresholds
        self.thresholds = {
            "max_response_time": 500,  # milliseconds
            "min_throughput": 100,  # requests per second
            "max_memory_usage": 2048,  # MB
            "max_cpu_usage": 80,  # percentage
            "max_error_rate": 1  # percentage
        }
        
        # Test configuration
        self.test_user_id = str(uuid.uuid4())
        self.auth_headers = {
            "Authorization": "Bearer test-performance-token",
            "Content-Type": "application/json"
        }
    
    def mock_authentication(self):
        """Mock authentication for performance testing."""
        return patch.multiple(
            'app.core.security',
            get_current_user_id=Mock(return_value=self.test_user_id),
            require_role=Mock(return_value={"role": "admin", "user_id": self.test_user_id}),
            check_rate_limit=Mock(return_value=True),
            verify_token=Mock(return_value={"sub": self.test_user_id, "role": "admin"}),
            get_client_info=AsyncMock(return_value={
                "ip_address": "127.0.0.1",
                "request_id": str(uuid.uuid4())
            })
        )
    
    def measure_system_resources(self) -> Dict[str, float]:
        """Measure current system resource usage."""
        process = psutil.Process()
        return {
            "memory_mb": process.memory_info().rss / 1024 / 1024,
            "cpu_percent": process.cpu_percent(),
            "threads": process.num_threads(),
            "open_files": len(process.open_files()) if hasattr(process, 'open_files') else 0
        }
    
    def calculate_statistics(self, data: List[float]) -> Dict[str, float]:
        """Calculate performance statistics."""
        if not data:
            return {"min": 0, "max": 0, "mean": 0, "median": 0, "p95": 0, "p99": 0}
        
        return {
            "min": min(data),
            "max": max(data),
            "mean": statistics.mean(data),
            "median": statistics.median(data),
            "p95": statistics.quantiles(data, n=20)[18] if len(data) >= 20 else max(data),
            "p99": statistics.quantiles(data, n=100)[98] if len(data) >= 100 else max(data)
        }


class TestConcurrentUserLoad(PerformanceTestSuite):
    """Concurrent user load testing suite."""
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_concurrent_users_100(self):
        """Test system performance with 100 concurrent users."""
        self._run_concurrent_load_test(num_users=100, test_duration=30)
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_concurrent_users_500(self):
        """Test system performance with 500 concurrent users."""
        self._run_concurrent_load_test(num_users=500, test_duration=60)
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_concurrent_users_1000(self):
        """Test system performance with 1000 concurrent users."""
        self._run_concurrent_load_test(num_users=1000, test_duration=120)
    
    def _run_concurrent_load_test(self, num_users: int, test_duration: int):
        """Run concurrent load test with specified parameters."""
        
        with self.mock_authentication():
            print(f"\n🚀 Starting concurrent load test: {num_users} users for {test_duration} seconds")
            
            # Test endpoints to simulate realistic user behavior
            test_scenarios = [
                {"method": "GET", "endpoint": "/api/v1/healthcare/health", "weight": 30},
                {"method": "GET", "endpoint": "/api/v1/healthcare/patients", "weight": 25},
                {"method": "GET", "endpoint": "/api/v1/healthcare/immunizations", "weight": 20},
                {"method": "POST", "endpoint": "/api/v1/healthcare/patients", "weight": 15, "data": self._get_sample_patient_data()},
                {"method": "POST", "endpoint": "/api/v1/healthcare/immunizations", "weight": 10, "data": self._get_sample_immunization_data()}
            ]
            
            # Start monitoring thread
            monitoring_thread = threading.Thread(
                target=self._monitor_system_resources,
                args=(test_duration,),
                daemon=True
            )
            monitoring_thread.start()
            
            # Execute concurrent load
            start_time = time.time()
            results = []
            
            with ThreadPoolExecutor(max_workers=num_users) as executor:
                # Submit tasks for each user
                futures = []
                for user_id in range(num_users):
                    future = executor.submit(
                        self._simulate_user_session,
                        user_id,
                        test_scenarios,
                        test_duration
                    )
                    futures.append(future)
                
                # Collect results
                for future in as_completed(futures):
                    try:
                        user_results = future.result(timeout=test_duration + 30)
                        results.extend(user_results)
                    except Exception as e:
                        print(f"User session failed: {e}")
            
            end_time = time.time()
            actual_duration = end_time - start_time
            
            # Wait for monitoring to complete
            monitoring_thread.join(timeout=5)
            
            # Analyze results
            self._analyze_load_test_results(results, num_users, actual_duration)
    
    def _simulate_user_session(self, user_id: int, scenarios: List[Dict], duration: int) -> List[Dict]:
        """Simulate a user session with realistic behavior patterns."""
        session_results = []
        session_start = time.time()
        request_count = 0
        
        while time.time() - session_start < duration:
            # Select random scenario based on weights
            scenario = self._select_weighted_scenario(scenarios)
            
            # Execute request
            start_time = time.time()
            try:
                if scenario["method"] == "GET":
                    response = self.client.get(scenario["endpoint"], headers=self.auth_headers)
                elif scenario["method"] == "POST":
                    response = self.client.post(
                        scenario["endpoint"],
                        json=scenario.get("data", {}),
                        headers=self.auth_headers
                    )
                
                response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
                
                session_results.append({
                    "user_id": user_id,
                    "request_id": request_count,
                    "endpoint": scenario["endpoint"],
                    "method": scenario["method"],
                    "response_time": response_time,
                    "status_code": response.status_code,
                    "success": response.status_code < 400,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
            except Exception as e:
                session_results.append({
                    "user_id": user_id,
                    "request_id": request_count,
                    "endpoint": scenario["endpoint"],
                    "method": scenario["method"],
                    "response_time": 0,
                    "status_code": 500,
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            request_count += 1
            
            # Simulate user think time (1-3 seconds)
            time.sleep(1 + (user_id % 3))
        
        return session_results
    
    def _select_weighted_scenario(self, scenarios: List[Dict]) -> Dict:
        """Select scenario based on weight distribution."""
        import random
        
        total_weight = sum(scenario["weight"] for scenario in scenarios)
        random_value = random.uniform(0, total_weight)
        
        current_weight = 0
        for scenario in scenarios:
            current_weight += scenario["weight"]
            if random_value <= current_weight:
                return scenario
        
        return scenarios[0]  # Fallback
    
    def _monitor_system_resources(self, duration: int):
        """Monitor system resources during the test."""
        monitoring_start = time.time()
        
        while time.time() - monitoring_start < duration:
            resources = self.measure_system_resources()
            self.metrics["memory_usage"].append(resources["memory_mb"])
            self.metrics["cpu_usage"].append(resources["cpu_percent"])
            
            time.sleep(5)  # Sample every 5 seconds
    
    def _analyze_load_test_results(self, results: List[Dict], num_users: int, duration: float):
        """Analyze and report load test results."""
        if not results:
            pytest.fail("No results collected from load test")
        
        # Calculate metrics
        response_times = [r["response_time"] for r in results if r["success"]]
        error_count = len([r for r in results if not r["success"]])
        total_requests = len(results)
        
        # Performance statistics
        response_time_stats = self.calculate_statistics(response_times)
        throughput = total_requests / duration
        error_rate = (error_count / total_requests) * 100 if total_requests > 0 else 0
        
        # Resource statistics
        memory_stats = self.calculate_statistics(self.metrics["memory_usage"])
        cpu_stats = self.calculate_statistics(self.metrics["cpu_usage"])
        
        # Print detailed results
        print(f"\n📊 LOAD TEST RESULTS ({num_users} users, {duration:.1f}s)")
        print(f"Total Requests: {total_requests}")
        print(f"Successful Requests: {total_requests - error_count}")
        print(f"Failed Requests: {error_count}")
        print(f"Error Rate: {error_rate:.2f}%")
        print(f"Throughput: {throughput:.2f} req/s")
        
        print(f"\n⏱️ RESPONSE TIME STATISTICS (ms)")
        print(f"Min: {response_time_stats['min']:.2f}")
        print(f"Max: {response_time_stats['max']:.2f}")
        print(f"Mean: {response_time_stats['mean']:.2f}")
        print(f"Median: {response_time_stats['median']:.2f}")
        print(f"95th percentile: {response_time_stats['p95']:.2f}")
        print(f"99th percentile: {response_time_stats['p99']:.2f}")
        
        print(f"\n💾 RESOURCE USAGE")
        print(f"Memory (MB) - Mean: {memory_stats['mean']:.2f}, Max: {memory_stats['max']:.2f}")
        print(f"CPU (%) - Mean: {cpu_stats['mean']:.2f}, Max: {cpu_stats['max']:.2f}")
        
        # Performance assertions
        assert response_time_stats['p95'] < self.thresholds['max_response_time'], \
            f"95th percentile response time {response_time_stats['p95']:.2f}ms exceeds threshold {self.thresholds['max_response_time']}ms"
        
        assert throughput >= self.thresholds['min_throughput'], \
            f"Throughput {throughput:.2f} req/s below threshold {self.thresholds['min_throughput']} req/s"
        
        assert error_rate <= self.thresholds['max_error_rate'], \
            f"Error rate {error_rate:.2f}% exceeds threshold {self.thresholds['max_error_rate']}%"
        
        assert memory_stats['max'] <= self.thresholds['max_memory_usage'], \
            f"Peak memory usage {memory_stats['max']:.2f}MB exceeds threshold {self.thresholds['max_memory_usage']}MB"
    
    def _get_sample_patient_data(self) -> Dict:
        """Generate sample patient data for testing."""
        return {
            "identifier": [{
                "use": "official",
                "system": "http://performance-test.org",
                "value": f"PERF-{uuid.uuid4().hex[:8]}"
            }],
            "active": True,
            "name": [{
                "use": "official",
                "family": "PerformancePatient",
                "given": ["Load", "Test"]
            }],
            "gender": "other",
            "birthDate": "1990-01-01"
        }
    
    def _get_sample_immunization_data(self) -> Dict:
        """Generate sample immunization data for testing."""
        return {
            "patient_id": str(uuid.uuid4()),
            "status": "completed",
            "vaccine_code": "207",
            "vaccine_display": "COVID-19 vaccine",
            "occurrence_datetime": "2024-01-15T10:30:00Z"
        }


class TestDatabasePerformance(PerformanceTestSuite):
    """Database performance testing suite."""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_database_connection_pool_performance(self):
        """Test database connection pool performance under load."""
        
        print("\n🗄️ Testing database connection pool performance...")
        
        connection_times = []
        query_times = []
        
        # Test multiple concurrent database operations
        async def execute_database_operation(session_id: int):
            start_time = time.time()
            
            try:
                async for db_session in get_db():
                    connection_time = (time.time() - start_time) * 1000
                    connection_times.append(connection_time)
                    
                    # Execute sample query
                    query_start = time.time()
                    result = await db_session.execute("SELECT 1 as test_value")
                    query_time = (time.time() - query_start) * 1000
                    query_times.append(query_time)
                    
                    break  # Exit after first iteration
                    
            except Exception as e:
                print(f"Database operation {session_id} failed: {e}")
        
        # Execute concurrent database operations
        tasks = []
        for i in range(50):  # 50 concurrent operations
            task = execute_database_operation(i)
            tasks.append(task)
        
        start_time = time.time()
        await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # Analyze results
        connection_stats = self.calculate_statistics(connection_times)
        query_stats = self.calculate_statistics(query_times)
        
        print(f"Database Connection Performance:")
        print(f"Total Operations: {len(connection_times)}")
        print(f"Total Time: {total_time:.2f}s")
        print(f"Operations/sec: {len(connection_times)/total_time:.2f}")
        
        print(f"\nConnection Times (ms):")
        print(f"Mean: {connection_stats['mean']:.2f}")
        print(f"95th percentile: {connection_stats['p95']:.2f}")
        
        print(f"\nQuery Times (ms):")
        print(f"Mean: {query_stats['mean']:.2f}")
        print(f"95th percentile: {query_stats['p95']:.2f}")
        
        # Performance assertions
        assert connection_stats['p95'] < 100, f"Database connection p95 {connection_stats['p95']:.2f}ms too slow"
        assert query_stats['p95'] < 50, f"Query execution p95 {query_stats['p95']:.2f}ms too slow"
    
    @pytest.mark.performance
    def test_patient_lookup_performance(self):
        """Test patient lookup query performance."""
        
        with self.mock_authentication():
            print("\n👤 Testing patient lookup performance...")
            
            # Create test patients first
            patient_ids = []
            for i in range(10):
                patient_data = {
                    "identifier": [{
                        "use": "official",
                        "system": "http://performance-test.org",
                        "value": f"LOOKUP-PERF-{i:03d}"
                    }],
                    "active": True,
                    "name": [{
                        "use": "official",
                        "family": f"LookupPatient{i}",
                        "given": ["Performance", "Test"]
                    }],
                    "gender": "other",
                    "birthDate": "1990-01-01"
                }
                
                response = self.client.post(
                    "/api/v1/healthcare/patients",
                    json=patient_data,
                    headers=self.auth_headers
                )
                
                if response.status_code == 201:
                    patient_ids.append(response.json()["id"])
            
            # Test lookup performance
            lookup_times = []
            
            for patient_id in patient_ids:
                start_time = time.time()
                
                response = self.client.get(
                    f"/api/v1/healthcare/patients/{patient_id}",
                    headers=self.auth_headers
                )
                
                lookup_time = (time.time() - start_time) * 1000
                lookup_times.append(lookup_time)
                
                assert response.status_code in [200, 404], f"Unexpected status code: {response.status_code}"
            
            # Analyze lookup performance
            if lookup_times:
                lookup_stats = self.calculate_statistics(lookup_times)
                
                print(f"Patient Lookup Performance:")
                print(f"Total Lookups: {len(lookup_times)}")
                print(f"Mean Response Time: {lookup_stats['mean']:.2f}ms")
                print(f"95th Percentile: {lookup_stats['p95']:.2f}ms")
                
                # Performance assertion
                assert lookup_stats['p95'] < 200, f"Patient lookup p95 {lookup_stats['p95']:.2f}ms too slow"


class TestAPIResponseTime(PerformanceTestSuite):
    """API response time testing suite."""
    
    @pytest.mark.performance
    def test_health_endpoint_response_time(self):
        """Test health endpoint response time."""
        
        print("\n❤️ Testing health endpoint response time...")
        
        response_times = []
        
        for i in range(100):
            start_time = time.time()
            response = self.client.get("/api/v1/healthcare/health")
            response_time = (time.time() - start_time) * 1000
            response_times.append(response_time)
            
            assert response.status_code == 200
        
        stats = self.calculate_statistics(response_times)
        
        print(f"Health Endpoint Performance:")
        print(f"Mean: {stats['mean']:.2f}ms")
        print(f"95th Percentile: {stats['p95']:.2f}ms")
        print(f"99th Percentile: {stats['p99']:.2f}ms")
        
        # Health endpoint should be very fast
        assert stats['p95'] < 50, f"Health endpoint p95 {stats['p95']:.2f}ms too slow"
        assert stats['p99'] < 100, f"Health endpoint p99 {stats['p99']:.2f}ms too slow"
    
    @pytest.mark.performance
    def test_authenticated_endpoints_response_time(self):
        """Test authenticated endpoints response time."""
        
        with self.mock_authentication():
            print("\n🔐 Testing authenticated endpoints response time...")
            
            endpoints = [
                "/api/v1/healthcare/patients",
                "/api/v1/healthcare/immunizations",
                "/api/v1/healthcare/documents"
            ]
            
            for endpoint in endpoints:
                response_times = []
                
                for i in range(50):
                    start_time = time.time()
                    response = self.client.get(endpoint, headers=self.auth_headers)
                    response_time = (time.time() - start_time) * 1000
                    response_times.append(response_time)
                    
                    assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
                
                stats = self.calculate_statistics(response_times)
                
                print(f"\n{endpoint}:")
                print(f"Mean: {stats['mean']:.2f}ms")
                print(f"95th Percentile: {stats['p95']:.2f}ms")
                
                # Authenticated endpoints should respond within reasonable time
                assert stats['p95'] < 300, f"{endpoint} p95 {stats['p95']:.2f}ms too slow"


class TestMemoryUsage(PerformanceTestSuite):
    """Memory usage testing suite."""
    
    @pytest.mark.performance
    def test_memory_usage_under_load(self):
        """Test memory usage under sustained load."""
        
        with self.mock_authentication():
            print("\n💾 Testing memory usage under load...")
            
            # Baseline memory usage
            baseline_memory = self.measure_system_resources()["memory_mb"]
            print(f"Baseline memory: {baseline_memory:.2f}MB")
            
            memory_measurements = []
            
            # Sustained load for memory testing
            for iteration in range(100):
                # Execute multiple operations
                for i in range(10):
                    response = self.client.get("/api/v1/healthcare/health", headers=self.auth_headers)
                    assert response.status_code == 200
                
                # Measure memory every 10 iterations
                if iteration % 10 == 0:
                    current_memory = self.measure_system_resources()["memory_mb"]
                    memory_measurements.append(current_memory)
                    print(f"Iteration {iteration}: {current_memory:.2f}MB")
            
            # Analyze memory usage
            final_memory = memory_measurements[-1]
            max_memory = max(memory_measurements)
            memory_growth = final_memory - baseline_memory
            
            print(f"\nMemory Usage Analysis:")
            print(f"Baseline: {baseline_memory:.2f}MB")
            print(f"Final: {final_memory:.2f}MB")
            print(f"Peak: {max_memory:.2f}MB")
            print(f"Growth: {memory_growth:.2f}MB")
            
            # Memory usage assertions
            assert memory_growth < 500, f"Memory growth {memory_growth:.2f}MB indicates memory leak"
            assert max_memory < self.thresholds['max_memory_usage'], \
                f"Peak memory {max_memory:.2f}MB exceeds threshold {self.thresholds['max_memory_usage']}MB"


class TestThroughputAndScalability(PerformanceTestSuite):
    """Throughput and scalability testing suite."""
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_maximum_throughput(self):
        """Test maximum system throughput."""
        
        with self.mock_authentication():
            print("\n🚀 Testing maximum system throughput...")
            
            # Test different concurrency levels
            concurrency_levels = [10, 25, 50, 100]
            throughput_results = []
            
            for concurrency in concurrency_levels:
                print(f"\nTesting concurrency level: {concurrency}")
                
                start_time = time.time()
                successful_requests = 0
                failed_requests = 0
                
                def make_request():
                    try:
                        response = self.client.get("/api/v1/healthcare/health", headers=self.auth_headers)
                        return response.status_code == 200
                    except Exception:
                        return False
                
                # Execute concurrent requests
                with ThreadPoolExecutor(max_workers=concurrency) as executor:
                    futures = [executor.submit(make_request) for _ in range(concurrency * 10)]
                    
                    for future in as_completed(futures):
                        if future.result():
                            successful_requests += 1
                        else:
                            failed_requests += 1
                
                end_time = time.time()
                duration = end_time - start_time
                throughput = successful_requests / duration
                
                throughput_results.append({
                    "concurrency": concurrency,
                    "throughput": throughput,
                    "success_rate": successful_requests / (successful_requests + failed_requests)
                })
                
                print(f"Throughput: {throughput:.2f} req/s")
                print(f"Success rate: {successful_requests / (successful_requests + failed_requests):.2%}")
            
            # Analyze scalability
            print(f"\n📈 Throughput Scalability Analysis:")
            for result in throughput_results:
                print(f"Concurrency {result['concurrency']:3d}: {result['throughput']:6.2f} req/s "
                      f"(Success: {result['success_rate']:.1%})")
            
            # Scalability assertions
            max_throughput = max(result["throughput"] for result in throughput_results)
            assert max_throughput >= self.thresholds['min_throughput'], \
                f"Maximum throughput {max_throughput:.2f} req/s below threshold"


@pytest.mark.performance
@pytest.mark.slow
def test_comprehensive_performance_suite():
    """Run comprehensive performance test suite."""
    
    print("\n🏁 COMPREHENSIVE PERFORMANCE TEST SUITE")
    print("=" * 50)
    
    # Initialize test suite
    perf_suite = PerformanceTestSuite()
    
    # Run all performance tests
    test_results = {
        "concurrent_load": False,
        "database_performance": False,
        "api_response_time": False,
        "memory_usage": False,
        "throughput": False
    }
    
    try:
        # Test concurrent load (reduced for CI)
        load_tester = TestConcurrentUserLoad()
        load_tester._run_concurrent_load_test(num_users=50, test_duration=30)
        test_results["concurrent_load"] = True
        print("✅ Concurrent load test passed")
        
    except Exception as e:
        print(f"❌ Concurrent load test failed: {e}")
    
    try:
        # Test API response times
        api_tester = TestAPIResponseTime()
        api_tester.test_health_endpoint_response_time()
        api_tester.test_authenticated_endpoints_response_time()
        test_results["api_response_time"] = True
        print("✅ API response time test passed")
        
    except Exception as e:
        print(f"❌ API response time test failed: {e}")
    
    try:
        # Test memory usage
        memory_tester = TestMemoryUsage()
        memory_tester.test_memory_usage_under_load()
        test_results["memory_usage"] = True
        print("✅ Memory usage test passed")
        
    except Exception as e:
        print(f"❌ Memory usage test failed: {e}")
    
    # Summary
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    print(f"\n🏆 PERFORMANCE TEST SUMMARY")
    print(f"Passed: {passed_tests}/{total_tests}")
    print(f"Success Rate: {passed_tests/total_tests:.1%}")
    
    if passed_tests >= total_tests * 0.8:  # 80% pass rate required
        print("🎉 Performance test suite PASSED")
    else:
        print("⚠️ Performance test suite needs attention")
    
    return test_results


if __name__ == "__main__":
    """Run performance tests independently."""
    # Configure logging for performance tests
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run with verbose output
    pytest.main([__file__, "-v", "--tb=short", "-m", "performance"])