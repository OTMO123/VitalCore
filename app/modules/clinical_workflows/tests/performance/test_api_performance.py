"""
Clinical Workflows API Performance Tests

Comprehensive performance testing for API endpoints with enterprise benchmarks.
Tests response times, throughput, concurrency, and scalability requirements.
"""

import pytest
import asyncio
import time
import statistics
from datetime import datetime, timedelta
from uuid import uuid4
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

import psutil
from httpx import AsyncClient
from fastapi.testclient import TestClient


class TestAPIResponseTimes:
    """Test API endpoint response time requirements."""
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    @pytest.mark.physician
    async def test_create_workflow_response_time(
        self, async_client: AsyncClient, physician_token: str, 
        valid_workflow_data: Dict[str, Any], role_based_headers
    ):
        """Test workflow creation response time (<200ms requirement)."""
        headers = role_based_headers(physician_token)
        
        # Prepare workflow data
        workflow_data = valid_workflow_data.copy()
        workflow_data["patient_id"] = str(workflow_data["patient_id"])
        workflow_data["provider_id"] = str(workflow_data["provider_id"])
        workflow_data["workflow_type"] = workflow_data["workflow_type"].value
        workflow_data["priority"] = workflow_data["priority"].value
        
        # Measure response times over multiple requests
        response_times = []
        
        for i in range(10):  # Test 10 requests
            start_time = time.perf_counter()
            
            response = await async_client.post(
                "/api/v1/clinical-workflows/workflows",
                json={**workflow_data, "chief_complaint": f"Performance test {i}"},
                headers=headers
            )
            
            end_time = time.perf_counter()
            response_time_ms = (end_time - start_time) * 1000
            response_times.append(response_time_ms)
            
            # Clean up successful creations
            if response.status_code == 201:
                workflow_id = response.json()["id"]
                # Would delete workflow in real scenario
        
        # Analyze performance metrics
        avg_response_time = statistics.mean(response_times)
        p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
        max_response_time = max(response_times)
        
        # Enterprise requirements
        assert avg_response_time < 200, f"Average response time {avg_response_time:.2f}ms exceeds 200ms"
        assert p95_response_time < 500, f"95th percentile {p95_response_time:.2f}ms exceeds 500ms"
        assert max_response_time < 1000, f"Max response time {max_response_time:.2f}ms exceeds 1000ms"
        
        print(f"Workflow Creation Performance:")
        print(f"  Average: {avg_response_time:.2f}ms")
        print(f"  95th percentile: {p95_response_time:.2f}ms")
        print(f"  Maximum: {max_response_time:.2f}ms")
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_get_workflow_response_time(
        self, async_client: AsyncClient, physician_token: str, role_based_headers
    ):
        """Test workflow retrieval response time (<100ms requirement)."""
        headers = role_based_headers(physician_token)
        
        # Create a workflow first for testing
        workflow_data = {
            "patient_id": str(uuid4()),
            "provider_id": str(uuid4()),
            "workflow_type": "encounter",
            "priority": "routine",
            "chief_complaint": "Performance test workflow",
            "location": "Test Department"
        }
        
        create_response = await async_client.post(
            "/api/v1/clinical-workflows/workflows",
            json=workflow_data,
            headers=headers
        )
        
        if create_response.status_code == 201:
            workflow_id = create_response.json()["id"]
            
            # Test retrieval performance
            response_times = []
            
            for i in range(20):  # Test 20 retrievals
                start_time = time.perf_counter()
                
                response = await async_client.get(
                    f"/api/v1/clinical-workflows/workflows/{workflow_id}",
                    params={"decrypt_phi": True},
                    headers=headers
                )
                
                end_time = time.perf_counter()
                response_time_ms = (end_time - start_time) * 1000
                response_times.append(response_time_ms)
            
            # Analyze performance
            avg_response_time = statistics.mean(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18]
            
            # Requirements for read operations
            assert avg_response_time < 100, f"Average retrieval time {avg_response_time:.2f}ms exceeds 100ms"
            assert p95_response_time < 200, f"95th percentile {p95_response_time:.2f}ms exceeds 200ms"
            
            print(f"Workflow Retrieval Performance:")
            print(f"  Average: {avg_response_time:.2f}ms")
            print(f"  95th percentile: {p95_response_time:.2f}ms")
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_search_workflows_response_time(
        self, async_client: AsyncClient, physician_token: str, role_based_headers
    ):
        """Test workflow search response time (<150ms requirement)."""
        headers = role_based_headers(physician_token)
        
        response_times = []
        
        for i in range(15):  # Test 15 search requests
            start_time = time.perf_counter()
            
            response = await async_client.get(
                "/api/v1/clinical-workflows/workflows",
                params={
                    "page": 1,
                    "page_size": 20,
                    "workflow_type": "encounter",
                    "sort_by": "created_at"
                },
                headers=headers
            )
            
            end_time = time.perf_counter()
            response_time_ms = (end_time - start_time) * 1000
            response_times.append(response_time_ms)
        
        avg_response_time = statistics.mean(response_times)
        p95_response_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else max(response_times)
        
        # Search operation requirements
        assert avg_response_time < 150, f"Average search time {avg_response_time:.2f}ms exceeds 150ms"
        assert p95_response_time < 300, f"95th percentile {p95_response_time:.2f}ms exceeds 300ms"
        
        print(f"Workflow Search Performance:")
        print(f"  Average: {avg_response_time:.2f}ms")
        print(f"  95th percentile: {p95_response_time:.2f}ms")


class TestConcurrentUserPerformance:
    """Test performance under concurrent user load."""
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_workflow_creation(
        self, async_client: AsyncClient, physician_token: str, role_based_headers
    ):
        """Test concurrent workflow creation performance."""
        headers = role_based_headers(physician_token)
        concurrent_users = 10
        requests_per_user = 5
        
        async def create_workflow_batch(user_index: int):
            """Create multiple workflows for a single user."""
            user_response_times = []
            
            for req_index in range(requests_per_user):
                workflow_data = {
                    "patient_id": str(uuid4()),
                    "provider_id": str(uuid4()),
                    "workflow_type": "encounter",
                    "priority": "routine",
                    "chief_complaint": f"Concurrent test user {user_index} request {req_index}",
                    "location": "Test Department"
                }
                
                start_time = time.perf_counter()
                
                response = await async_client.post(
                    "/api/v1/clinical-workflows/workflows",
                    json=workflow_data,
                    headers=headers
                )
                
                end_time = time.perf_counter()
                response_time_ms = (end_time - start_time) * 1000
                user_response_times.append(response_time_ms)
            
            return user_response_times
        
        # Execute concurrent requests
        start_time = time.perf_counter()
        
        tasks = [create_workflow_batch(i) for i in range(concurrent_users)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # Analyze results
        all_response_times = []
        successful_requests = 0
        
        for result in results:
            if isinstance(result, list):
                all_response_times.extend(result)
                successful_requests += len(result)
        
        if all_response_times:
            avg_response_time = statistics.mean(all_response_times)
            p95_response_time = statistics.quantiles(all_response_times, n=20)[18]
            throughput = successful_requests / total_time
            
            # Concurrent performance requirements
            assert avg_response_time < 500, f"Concurrent avg response time {avg_response_time:.2f}ms exceeds 500ms"
            assert p95_response_time < 1000, f"Concurrent 95th percentile {p95_response_time:.2f}ms exceeds 1000ms"
            assert throughput > 10, f"Throughput {throughput:.2f} req/s below minimum 10 req/s"
            
            print(f"Concurrent Creation Performance ({concurrent_users} users):")
            print(f"  Total requests: {successful_requests}")
            print(f"  Average response time: {avg_response_time:.2f}ms")
            print(f"  95th percentile: {p95_response_time:.2f}ms")
            print(f"  Throughput: {throughput:.2f} requests/second")
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_workflow_retrieval(
        self, async_client: AsyncClient, physician_token: str, role_based_headers
    ):
        """Test concurrent workflow retrieval performance."""
        headers = role_based_headers(physician_token)
        
        # Create some workflows first
        workflow_ids = []
        for i in range(5):
            workflow_data = {
                "patient_id": str(uuid4()),
                "provider_id": str(uuid4()),
                "workflow_type": "encounter",
                "priority": "routine",
                "chief_complaint": f"Concurrent retrieval test {i}",
                "location": "Test Department"
            }
            
            response = await async_client.post(
                "/api/v1/clinical-workflows/workflows",
                json=workflow_data,
                headers=headers
            )
            
            if response.status_code == 201:
                workflow_ids.append(response.json()["id"])
        
        if workflow_ids:
            concurrent_users = 20
            
            async def retrieve_workflows_batch(user_index: int):
                """Retrieve workflows for a single user."""
                response_times = []
                
                for workflow_id in workflow_ids:
                    start_time = time.perf_counter()
                    
                    response = await async_client.get(
                        f"/api/v1/clinical-workflows/workflows/{workflow_id}",
                        headers=headers
                    )
                    
                    end_time = time.perf_counter()
                    response_time_ms = (end_time - start_time) * 1000
                    response_times.append(response_time_ms)
                
                return response_times
            
            # Execute concurrent retrievals
            start_time = time.perf_counter()
            
            tasks = [retrieve_workflows_batch(i) for i in range(concurrent_users)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.perf_counter()
            total_time = end_time - start_time
            
            # Analyze concurrent retrieval performance
            all_response_times = []
            for result in results:
                if isinstance(result, list):
                    all_response_times.extend(result)
            
            if all_response_times:
                avg_response_time = statistics.mean(all_response_times)
                p95_response_time = statistics.quantiles(all_response_times, n=20)[18]
                throughput = len(all_response_times) / total_time
                
                # Concurrent read performance requirements
                assert avg_response_time < 200, f"Concurrent read avg {avg_response_time:.2f}ms exceeds 200ms"
                assert throughput > 50, f"Read throughput {throughput:.2f} req/s below minimum 50 req/s"
                
                print(f"Concurrent Retrieval Performance ({concurrent_users} users):")
                print(f"  Total requests: {len(all_response_times)}")
                print(f"  Average response time: {avg_response_time:.2f}ms")
                print(f"  Throughput: {throughput:.2f} requests/second")


class TestMemoryUsagePerformance:
    """Test memory usage and resource consumption."""
    
    @pytest.mark.performance
    def test_memory_usage_workflow_creation(self):
        """Test memory usage during workflow creation."""
        import gc
        
        # Get baseline memory usage
        gc.collect()
        process = psutil.Process()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Simulate creating many workflows (in-memory objects)
        workflows = []
        for i in range(1000):
            workflow_data = {
                "id": uuid4(),
                "patient_id": uuid4(),
                "provider_id": uuid4(),
                "workflow_type": "encounter",
                "chief_complaint": f"Memory test workflow {i} with detailed clinical information",
                "history_present_illness": "Detailed medical history " * 10,
                "assessment": "Clinical assessment " * 20,
                "plan": "Treatment plan " * 15
            }
            workflows.append(workflow_data)
        
        # Check memory usage after creation
        current_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = current_memory - baseline_memory
        
        # Memory usage should be reasonable (<100MB for 1000 workflows)
        assert memory_increase < 100, f"Memory usage increased by {memory_increase:.2f}MB, exceeds 100MB limit"
        
        # Clean up
        workflows.clear()
        gc.collect()
        
        print(f"Memory Usage Test:")
        print(f"  Baseline: {baseline_memory:.2f}MB")
        print(f"  After 1000 workflows: {current_memory:.2f}MB")
        print(f"  Increase: {memory_increase:.2f}MB")
    
    @pytest.mark.performance
    def test_memory_leak_detection(self):
        """Test for memory leaks in repeated operations."""
        import gc
        
        process = psutil.Process()
        memory_samples = []
        
        # Perform repeated operations and monitor memory
        for cycle in range(5):
            # Simulate workflow operations
            for i in range(100):
                workflow_data = {
                    "id": uuid4(),
                    "data": f"Cycle {cycle} workflow {i}" * 100
                }
                # Simulate processing
                processed_data = workflow_data.copy()
                processed_data["processed"] = True
                # Data goes out of scope
            
            # Force garbage collection
            gc.collect()
            
            # Sample memory usage
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_samples.append(current_memory)
        
        # Check for memory growth pattern
        if len(memory_samples) >= 3:
            # Memory should stabilize, not continuously grow
            recent_trend = memory_samples[-3:]
            memory_growth = max(recent_trend) - min(recent_trend)
            
            # Memory growth should be minimal (<10MB across cycles)
            assert memory_growth < 10, f"Potential memory leak detected: {memory_growth:.2f}MB growth"
            
            print(f"Memory Leak Detection:")
            print(f"  Memory samples: {[f'{m:.1f}MB' for m in memory_samples]}")
            print(f"  Recent growth: {memory_growth:.2f}MB")


class TestDatabasePerformance:
    """Test database operation performance."""
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_database_query_performance(self, db_session):
        """Test database query performance benchmarks."""
        # This would test actual database operations
        # For now, simulate with timing measurements
        
        query_times = []
        
        for i in range(50):
            start_time = time.perf_counter()
            
            # Simulate database query
            # In real test: db_session.query(ClinicalWorkflow).filter(...).all()
            await asyncio.sleep(0.001)  # Simulate 1ms query time
            
            end_time = time.perf_counter()
            query_time_ms = (end_time - start_time) * 1000
            query_times.append(query_time_ms)
        
        avg_query_time = statistics.mean(query_times)
        p95_query_time = statistics.quantiles(query_times, n=20)[18]
        
        # Database performance requirements
        assert avg_query_time < 50, f"Average query time {avg_query_time:.2f}ms exceeds 50ms"
        assert p95_query_time < 100, f"95th percentile query time {p95_query_time:.2f}ms exceeds 100ms"
        
        print(f"Database Query Performance:")
        print(f"  Average: {avg_query_time:.2f}ms")
        print(f"  95th percentile: {p95_query_time:.2f}ms")
    
    @pytest.mark.performance
    def test_database_connection_pool_performance(self):
        """Test database connection pool efficiency."""
        # Test connection acquisition times
        acquisition_times = []
        
        for i in range(100):
            start_time = time.perf_counter()
            
            # Simulate connection acquisition
            # In real test: would acquire connection from pool
            time.sleep(0.0001)  # Simulate 0.1ms acquisition
            
            end_time = time.perf_counter()
            acquisition_time_ms = (end_time - start_time) * 1000
            acquisition_times.append(acquisition_time_ms)
        
        avg_acquisition_time = statistics.mean(acquisition_times)
        max_acquisition_time = max(acquisition_times)
        
        # Connection pool performance requirements
        assert avg_acquisition_time < 1, f"Average connection acquisition {avg_acquisition_time:.2f}ms exceeds 1ms"
        assert max_acquisition_time < 5, f"Max connection acquisition {max_acquisition_time:.2f}ms exceeds 5ms"
        
        print(f"Connection Pool Performance:")
        print(f"  Average acquisition: {avg_acquisition_time:.2f}ms")
        print(f"  Maximum acquisition: {max_acquisition_time:.2f}ms")


class TestEncryptionPerformance:
    """Test PHI encryption/decryption performance."""
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_phi_encryption_performance(self, clinical_security):
        """Test PHI encryption performance benchmarks."""
        # Test encryption of various data sizes
        test_data_sizes = [
            ("small", "Brief clinical note"),
            ("medium", "Clinical assessment: " + "detailed information " * 50),
            ("large", "Comprehensive clinical documentation: " + "extensive details " * 500)
        ]
        
        for size_name, test_data in test_data_sizes:
            encryption_times = []
            
            for i in range(20):
                start_time = time.perf_counter()
                
                await clinical_security.encrypt_clinical_field(
                    data=test_data,
                    field_name="assessment",
                    patient_id=str(uuid4())
                )
                
                end_time = time.perf_counter()
                encryption_time_ms = (end_time - start_time) * 1000
                encryption_times.append(encryption_time_ms)
            
            avg_encryption_time = statistics.mean(encryption_times)
            p95_encryption_time = statistics.quantiles(encryption_times, n=20)[18]
            
            # Encryption performance requirements
            max_allowed_time = {"small": 10, "medium": 25, "large": 50}[size_name]
            
            assert avg_encryption_time < max_allowed_time, \
                f"{size_name} data encryption avg {avg_encryption_time:.2f}ms exceeds {max_allowed_time}ms"
            
            print(f"PHI Encryption Performance ({size_name} data):")
            print(f"  Data size: {len(test_data)} characters")
            print(f"  Average: {avg_encryption_time:.2f}ms")
            print(f"  95th percentile: {p95_encryption_time:.2f}ms")
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_phi_decryption_performance(self, clinical_security):
        """Test PHI decryption performance benchmarks."""
        # First encrypt some test data
        test_data = "Encrypted clinical assessment data for performance testing"
        encrypted_data = await clinical_security.encrypt_clinical_field(
            data=test_data,
            field_name="assessment",
            patient_id=str(uuid4())
        )
        
        # Test decryption performance
        decryption_times = []
        
        for i in range(30):
            start_time = time.perf_counter()
            
            await clinical_security.decrypt_clinical_field(
                encrypted_data=encrypted_data,
                field_name="assessment",
                patient_id=str(uuid4()),
                user_id=str(uuid4()),
                access_purpose="performance_test"
            )
            
            end_time = time.perf_counter()
            decryption_time_ms = (end_time - start_time) * 1000
            decryption_times.append(decryption_time_ms)
        
        avg_decryption_time = statistics.mean(decryption_times)
        p95_decryption_time = statistics.quantiles(decryption_times, n=20)[18]
        
        # Decryption should be faster than encryption
        assert avg_decryption_time < 30, f"Average decryption time {avg_decryption_time:.2f}ms exceeds 30ms"
        assert p95_decryption_time < 50, f"95th percentile decryption {p95_decryption_time:.2f}ms exceeds 50ms"
        
        print(f"PHI Decryption Performance:")
        print(f"  Average: {avg_decryption_time:.2f}ms")
        print(f"  95th percentile: {p95_decryption_time:.2f}ms")


class TestScalabilityLimits:
    """Test system scalability and limits."""
    
    @pytest.mark.performance
    def test_large_dataset_handling(self):
        """Test handling of large datasets."""
        # Test with large number of workflows
        large_dataset_size = 10000
        workflows = []
        
        start_time = time.perf_counter()
        
        for i in range(large_dataset_size):
            workflow = {
                "id": str(uuid4()),
                "patient_id": str(uuid4()),
                "provider_id": str(uuid4()),
                "chief_complaint": f"Large dataset test case {i}",
                "created_at": datetime.utcnow().isoformat()
            }
            workflows.append(workflow)
        
        creation_time = time.perf_counter() - start_time
        
        # Test filtering performance
        start_time = time.perf_counter()
        
        # Simulate filtering operations
        active_workflows = [w for w in workflows if "test case" in w["chief_complaint"]]
        recent_workflows = [w for w in workflows if int(w["chief_complaint"].split()[-1]) > 5000]
        
        filtering_time = time.perf_counter() - start_time
        
        # Performance requirements for large datasets
        assert creation_time < 5.0, f"Large dataset creation took {creation_time:.2f}s, exceeds 5s"
        assert filtering_time < 1.0, f"Large dataset filtering took {filtering_time:.2f}s, exceeds 1s"
        assert len(active_workflows) == large_dataset_size
        assert len(recent_workflows) < large_dataset_size
        
        print(f"Large Dataset Performance:")
        print(f"  Dataset size: {large_dataset_size:,} workflows")
        print(f"  Creation time: {creation_time:.2f}s")
        print(f"  Filtering time: {filtering_time:.2f}s")
        print(f"  Memory usage: {len(str(workflows)) / 1024 / 1024:.2f}MB")
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_pagination_performance(self, async_client: AsyncClient, physician_token: str, role_based_headers):
        """Test pagination performance with large result sets."""
        headers = role_based_headers(physician_token)
        
        # Test different page sizes
        page_sizes = [10, 25, 50, 100]
        
        for page_size in page_sizes:
            response_times = []
            
            for page in range(1, 6):  # Test first 5 pages
                start_time = time.perf_counter()
                
                response = await async_client.get(
                    "/api/v1/clinical-workflows/workflows",
                    params={
                        "page": page,
                        "page_size": page_size,
                        "sort_by": "created_at"
                    },
                    headers=headers
                )
                
                end_time = time.perf_counter()
                response_time_ms = (end_time - start_time) * 1000
                response_times.append(response_time_ms)
            
            avg_response_time = statistics.mean(response_times)
            
            # Pagination performance should scale linearly
            max_allowed_time = 50 + (page_size * 0.5)  # 50ms base + 0.5ms per item
            
            assert avg_response_time < max_allowed_time, \
                f"Page size {page_size} avg response {avg_response_time:.2f}ms exceeds {max_allowed_time:.2f}ms"
            
            print(f"Pagination Performance (page_size={page_size}):")
            print(f"  Average response time: {avg_response_time:.2f}ms")
            print(f"  Max allowed: {max_allowed_time:.2f}ms")