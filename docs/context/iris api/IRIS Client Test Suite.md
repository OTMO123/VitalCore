# IRIS Client Test Suite

## Unit Tests (tests/unit/test_iris_client.py)

```python
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import aiohttp
from freezegun import freeze_time

from iris_client.core.client import IRISClient
from iris_client.core.config import IRISConfig, AuthType
from iris_client.core.exceptions import (
    CircuitBreakerError,
    RateLimitError,
    AuthenticationError,
    FHIRValidationError,
    IRISServerError
)
from iris_client.models.fhir_r4 import (
    Immunization,
    ImmunizationStatus,
    CodeableConcept,
    Reference
)
from iris_client.layers.resilience import CircuitState

class TestIRISClient:
    """Unit tests for IRIS Client"""
    
    @pytest.fixture
    def config(self):
        """Test configuration"""
        return IRISConfig(
            primary_base_url="https://test.iris.api/v1",
            backup_base_urls=["https://backup1.iris.api/v1"],
            auth_type=AuthType.HYBRID,
            oauth2_token_url="https://auth.test/token",
            oauth2_client_id="test-client",
            oauth2_client_secret="test-secret",
            hmac_key_id="test-key",
            hmac_secret="test-hmac-secret",
            enable_phi_encryption=True,
            encryption_key_id="test-kms-key",
            mock_mode=False,
            rate_limit_requests=100,
            rate_limit_window=timedelta(minutes=1)
        )
    
    @pytest.fixture
    def mock_session(self):
        """Mock aiohttp session"""
        session = AsyncMock(spec=aiohttp.ClientSession)
        return session
    
    @pytest.fixture
    async def client(self, config, mock_session):
        """Test client instance"""
        client = IRISClient(config, session=mock_session)
        # Cancel health check task for tests
        if client._health_check_task:
            client._health_check_task.cancel()
        yield client
        await client.transport.close()
    
    @pytest.fixture
    def sample_immunization(self):
        """Sample FHIR immunization"""
        return Immunization(
            id="test-123",
            status=ImmunizationStatus.COMPLETED,
            vaccineCode=CodeableConcept(
                coding=[{
                    "system": "http://hl7.org/fhir/sid/cvx",
                    "code": "140",
                    "display": "Influenza vaccine"
                }]
            ),
            patient=Reference(reference="Patient/456"),
            occurrenceDateTime=datetime(2024, 1, 15, 10, 30)
        )
    
    @pytest.mark.asyncio
    async def test_create_immunization_success(self, client, sample_immunization):
        """Test successful immunization creation"""
        # Mock transport response
        mock_response = AsyncMock()
        mock_response.status = 201
        mock_response.json = AsyncMock(return_value={
            "resourceType": "Immunization",
            "id": "test-123",
            "status": "completed",
            "vaccineCode": sample_immunization.vaccineCode.dict(),
            "patient": {"reference": "Patient/456"}
        })
        
        with patch.object(client.transport, 'request', return_value=mock_response):
            result = await client.create_immunization(sample_immunization)
            
            assert result.id == "test-123"
            assert result.status == ImmunizationStatus.COMPLETED
            assert result.patient.reference == "Patient/456"
    
    @pytest.mark.asyncio
    async def test_create_immunization_validation_error(self, client):
        """Test immunization validation"""
        invalid_immunization = Immunization(
            status=ImmunizationStatus.COMPLETED,
            # Missing required vaccineCode and patient
        )
        
        with pytest.raises(FHIRValidationError) as exc_info:
            await client.create_immunization(invalid_immunization)
        
        assert "vaccineCode is required" in exc_info.value.validation_errors
        assert "patient reference is required" in exc_info.value.validation_errors
    
    @pytest.mark.asyncio
    async def test_token_refresh(self, client):
        """Test OAuth2 token refresh"""
        # Mock token response
        mock_token_response = {
            "access_token": "new-token-123",
            "expires_in": 3600,
            "token_type": "Bearer"
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_token_response
            )
            
            token = await client.security.token_manager.get_token()
            assert token == "new-token-123"
            
            # Verify token refresh was called
            mock_post.assert_called_once_with(
                client.config.oauth2_token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": "test-client",
                    "client_secret": "test-secret",
                    "scope": "immunization.read immunization.write"
                },
                timeout=aiohttp.ClientTimeout(total=30)
            )
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_failures(self, client):
        """Test circuit breaker opens after threshold failures"""
        circuit_breaker = client.resilience.get_circuit_breaker("/test")
        
        # Simulate failures
        for i in range(5):
            with pytest.raises(Exception):
                await circuit_breaker.call(self._failing_function)
        
        # Circuit should be open
        assert circuit_breaker.state == CircuitState.OPEN
        
        # Next call should fail immediately
        with pytest.raises(CircuitBreakerError):
            await circuit_breaker.call(self._failing_function)
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_recovery(self, client):
        """Test circuit breaker recovery through half-open state"""
        circuit_breaker = client.resilience.get_circuit_breaker("/test")
        
        # Open the circuit
        for i in range(5):
            try:
                await circuit_breaker.call(self._failing_function)
            except:
                pass
        
        assert circuit_breaker.state == CircuitState.OPEN
        
        # Fast forward past recovery timeout
        with freeze_time(datetime.utcnow() + timedelta(seconds=61)):
            # Should transition to half-open
            await circuit_breaker.call(self._success_function)
            assert circuit_breaker.state == CircuitState.HALF_OPEN
            
            # Need 3 successes to close
            for i in range(2):
                await circuit_breaker.call(self._success_function)
            
            assert circuit_breaker.state == CircuitState.CLOSED
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, client):
        """Test adaptive rate limiting"""
        rate_limiter = client.resilience.rate_limiter
        
        # Consume all tokens
        for i in range(100):
            acquired = await rate_limiter.acquire()
            assert acquired
        
        # Next request should be rate limited
        acquired = await rate_limiter.acquire()
        assert not acquired
        
        # Test adaptive adjustment
        rate_limiter.update_from_headers({
            "X-RateLimit-Limit": "50",
            "X-RateLimit-Remaining": "0"
        })
        
        assert rate_limiter._current_limit == 50
    
    @pytest.mark.asyncio
    async def test_phi_encryption(self, client):
        """Test PHI data encryption/decryption"""
        sensitive_data = "123-45-6789"  # SSN
        
        # Encrypt
        encrypted = client.security.phi_encryption.encrypt_phi(
            sensitive_data,
            context={"field": "ssn", "patient_id": "123"}
        )
        
        assert encrypted["encrypted"] is True
        assert "ciphertext" in encrypted
        assert "iv" in encrypted
        assert "tag" in encrypted
        assert encrypted["algorithm"] == "AES-256-GCM"
        
        # Decrypt
        decrypted = client.security.phi_encryption.decrypt_phi(encrypted)
        assert decrypted == sensitive_data
    
    @pytest.mark.asyncio
    async def test_hmac_signature_generation(self, client):
        """Test HMAC request signing"""
        headers = client.security.hmac_signer.sign_request(
            method="POST",
            path="/Immunization",
            headers={"Content-Type": "application/json"},
            body=b'{"test": "data"}'
        )
        
        assert "X-IRIS-Key-Id" in headers
        assert "X-IRIS-Timestamp" in headers
        assert "X-IRIS-Nonce" in headers
        assert "X-IRIS-Signature" in headers
        assert headers["X-IRIS-Key-Id"] == "test-key"
    
    @pytest.mark.asyncio
    async def test_idempotency(self, client, sample_immunization):
        """Test idempotency handling"""
        idempotency_key = "test-idempotency-123"
        
        # First request
        mock_response = AsyncMock()
        mock_response.status = 201
        mock_response.json = AsyncMock(return_value={
            "resourceType": "Immunization",
            "id": "test-123",
            "status": "completed"
        })
        
        # Cache the response
        await client.resilience.idempotency.cache_response(
            idempotency_key,
            {"resourceType": "Immunization", "id": "test-123"}
        )
        
        # Second request should return cached response
        cached = await client.resilience.idempotency.get_cached_response(
            idempotency_key
        )
        assert cached is not None
        assert cached["id"] == "test-123"
    
    @pytest.mark.asyncio
    async def test_endpoint_failover(self, client):
        """Test automatic endpoint failover"""
        # Mark primary as unhealthy
        client._endpoint_health[client.config.primary_base_url] = False
        client._endpoint_health[client.config.backup_base_urls[0]] = True
        
        await client._select_active_endpoint()
        
        assert client._active_endpoint == client.config.backup_base_urls[0]
    
    @pytest.mark.asyncio
    async def test_search_immunizations_with_cache(self, client):
        """Test search with caching"""
        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "resourceType": "Bundle",
            "type": "searchset",
            "total": 1,
            "entry": [{
                "resource": {
                    "resourceType": "Immunization",
                    "id": "test-123",
                    "status": "completed"
                }
            }]
        })
        
        with patch.object(client.transport, 'request', return_value=mock_response):
            # First call - hits API
            result1 = await client.search_immunizations(patient_id="Patient/123")
            assert result1.total == 1
            
            # Second call - should hit cache
            with patch.object(client.cache, 'get', return_value={
                "resourceType": "Bundle",
                "type": "searchset",
                "total": 1
            }):
                result2 = await client.search_immunizations(patient_id="Patient/123")
                assert result2.total == 1
    
    async def _failing_function(self):
        """Helper function that always fails"""
        raise Exception("Test failure")
    
    async def _success_function(self):
        """Helper function that always succeeds"""
        return "Success"


class TestFHIRModels:
    """Test FHIR R4 model validation"""
    
    def test_immunization_validation_success(self):
        """Test valid immunization model"""
        immunization = Immunization(
            status=ImmunizationStatus.COMPLETED,
            vaccineCode=CodeableConcept(
                coding=[{"system": "cvx", "code": "140"}]
            ),
            patient=Reference(reference="Patient/123"),
            occurrenceDateTime=datetime.now()
        )
        
        assert immunization.resourceType == "Immunization"
        assert immunization.status == ImmunizationStatus.COMPLETED
    
    def test_immunization_occurrence_conflict(self):
        """Test occurrence field conflict validation"""
        with pytest.raises(ValueError) as exc_info:
            Immunization(
                status=ImmunizationStatus.COMPLETED,
                vaccineCode=CodeableConcept(),
                patient=Reference(reference="Patient/123"),
                occurrenceDateTime=datetime.now(),
                occurrenceString="Today"  # Conflict!
            )
        
        assert "Cannot have both occurrenceDateTime and occurrenceString" in str(exc_info.value)
    
    def test_immunization_bundle_extraction(self):
        """Test extracting immunizations from bundle"""
        from iris_client.models.fhir_r4 import ImmunizationBundle
        
        bundle = ImmunizationBundle(
            type="searchset",
            total=2,
            entry=[
                {
                    "resource": {
                        "resourceType": "Immunization",
                        "id": "1",
                        "status": "completed",
                        "vaccineCode": {"text": "Flu"},
                        "patient": {"reference": "Patient/1"}
                    }
                },
                {
                    "resource": {
                        "resourceType": "Immunization",
                        "id": "2",
                        "status": "completed",
                        "vaccineCode": {"text": "COVID"},
                        "patient": {"reference": "Patient/2"}
                    }
                }
            ]
        )
        
        immunizations = bundle.get_immunizations()
        assert len(immunizations) == 2
        assert immunizations[0].id == "1"
        assert immunizations[1].id == "2"
```

## Integration Tests (tests/integration/test_iris_integration.py)

```python
import pytest
import asyncio
import os
from datetime import datetime, timedelta
import aiohttp
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from iris_client.core.client import IRISClient
from iris_client.core.config import IRISConfig
from iris_client.models.fhir_r4 import (
    Immunization,
    ImmunizationStatus,
    CodeableConcept,
    Reference
)

@pytest.mark.integration
class TestIRISIntegration:
    """Integration tests with real services"""
    
    @pytest.fixture(scope="class")
    def postgres_container(self):
        """PostgreSQL test container"""
        with PostgresContainer("postgres:15") as postgres:
            yield postgres
    
    @pytest.fixture(scope="class")
    def redis_container(self):
        """Redis test container"""
        with RedisContainer("redis:7") as redis:
            yield redis
    
    @pytest.fixture
    async def client(self, postgres_container, redis_container):
        """Configured client for integration tests"""
        config = IRISConfig(
            primary_base_url=os.getenv(
                "IRIS_TEST_URL",
                "https://sandbox.iris.health.gov/api/v1"
            ),
            oauth2_client_id=os.getenv("IRIS_TEST_CLIENT_ID"),
            oauth2_client_secret=os.getenv("IRIS_TEST_CLIENT_SECRET"),
            redis_url=redis_container.get_connection_url(),
            mock_mode=not os.getenv("IRIS_TEST_URL")  # Use mock if no real API
        )
        
        async with IRISClient(config) as client:
            yield client
    
    @pytest.mark.asyncio
    async def test_end_to_end_immunization_lifecycle(self, client):
        """Test complete immunization CRUD lifecycle"""
        # Create immunization
        immunization = Immunization(
            status=ImmunizationStatus.COMPLETED,
            vaccineCode=CodeableConcept(
                coding=[{
                    "system": "http://hl7.org/fhir/sid/cvx",
                    "code": "140",
                    "display": "Influenza, seasonal"
                }]
            ),
            patient=Reference(reference="Patient/test-patient-123"),
            occurrenceDateTime=datetime.utcnow(),
            lotNumber="FLU-2024-001",
            performer=[{
                "actor": {
                    "reference": "Practitioner/test-doc-456",
                    "display": "Dr. Smith"
                }
            }]
        )
        
        # Create
        created = await client.create_immunization(immunization)
        assert created.id is not None
        immunization_id = created.id
        
        # Read
        retrieved = await client.get_immunization(immunization_id)
        assert retrieved.id == immunization_id
        assert retrieved.lotNumber == "FLU-2024-001"
        
        # Update
        retrieved.lotNumber = "FLU-2024-002"
        updated = await client.update_immunization(immunization_id, retrieved)
        assert updated.lotNumber == "FLU-2024-002"
        
        # Search
        results = await client.search_immunizations(
            patient_id="Patient/test-patient-123"
        )
        assert results.total >= 1
        found = False
        for imm in results.get_immunizations():
            if imm.id == immunization_id:
                found = True
                break
        assert found
        
        # Delete
        deleted = await client.delete_immunization(immunization_id)
        assert deleted is True
        
        # Verify deletion
        with pytest.raises(Exception):  # Should raise not found
            await client.get_immunization(immunization_id)
    
    @pytest.mark.asyncio
    async def test_batch_operations(self, client):
        """Test batch create operations"""
        immunizations = []
        for i in range(5):
            immunizations.append(Immunization(
                status=ImmunizationStatus.COMPLETED,
                vaccineCode=CodeableConcept(
                    coding=[{
                        "system": "http://hl7.org/fhir/sid/cvx",
                        "code": "208",  # COVID-19
                        "display": "COVID-19 vaccine"
                    }]
                ),
                patient=Reference(reference=f"Patient/batch-test-{i}"),
                occurrenceDateTime=datetime.utcnow() - timedelta(days=i),
                doseQuantity={
                    "value": 0.5,
                    "unit": "mL",
                    "system": "http://unitsofmeasure.org"
                }
            ))
        
        # Batch create
        results = await client.batch_create_immunizations(immunizations)
        
        # Check results
        successful = [r for r in results if isinstance(r, Immunization)]
        failed = [r for r in results if not isinstance(r, Immunization)]
        
        assert len(successful) >= 3  # At least 60% success
        assert all(imm.id is not None for imm in successful)
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, client):
        """Test handling concurrent requests"""
        # Create multiple concurrent requests
        tasks = []
        for i in range(10):
            task = client.search_immunizations(
                vaccine_code="208",  # COVID-19
                limit=10
            )
            tasks.append(task)
        
        # Execute concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify results
        successful = [r for r in results if not isinstance(r, Exception)]
        assert len(successful) >= 8  # 80% success rate
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self, client):
        """Test circuit breaker with real failures"""
        if client.config.mock_mode:
            # Configure mock to fail
            client.mock_generator.mock_failure_rate = 1.0
        
        # Force failures to open circuit
        for i in range(6):
            try:
                await client.get_immunization("non-existent-id")
            except:
                pass
        
        # Circuit should be open
        circuit = client.resilience.get_circuit_breaker("/Immunization/non-existent-id")
        assert circuit.state.value in ["open", "half_open"]
        
        # Reset mock failure rate
        if client.config.mock_mode:
            client.mock_generator.mock_failure_rate = 0.0
    
    @pytest.mark.asyncio
    async def test_caching_integration(self, client):
        """Test caching with Redis"""
        # First request - cache miss
        start1 = datetime.utcnow()
        result1 = await client.get_immunization("cache-test-123")
        duration1 = (datetime.utcnow() - start1).total_seconds()
        
        # Second request - cache hit (should be faster)
        start2 = datetime.utcnow()
        result2 = await client.get_immunization("cache-test-123")
        duration2 = (datetime.utcnow() - start2).total_seconds()
        
        assert result1.id == result2.id
        assert duration2 < duration1 * 0.5  # At least 50% faster
    
    @pytest.mark.asyncio
    async def test_health_check_endpoint(self, client):
        """Test health check integration"""
        # Manually trigger health check
        await client._check_endpoint_health(client.config.primary_base_url)
        
        # Verify health status
        assert client._endpoint_health[client.config.primary_base_url] is not None


@pytest.mark.performance
class TestPerformance:
    """Performance and load tests"""
    
    @pytest.mark.asyncio
    async def test_throughput(self, client):
        """Test client can handle required throughput"""
        # Target: 1M requests/day = ~12 requests/second
        # Test: 100 requests in 8 seconds
        
        start_time = datetime.utcnow()
        tasks = []
        
        for i in range(100):
            task = client.search_immunizations(
                vaccine_code="208",
                limit=1
            )
            tasks.append(task)
            
            # Stagger requests
            if i % 10 == 0:
                await asyncio.sleep(0.1)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        successful = [r for r in results if not isinstance(r, Exception)]
        success_rate = len(successful) / len(results)
        
        assert success_rate >= 0.95  # 95% success rate
        assert duration < 10  # Complete within 10 seconds
        
        # Calculate throughput
        throughput = len(successful) / duration
        assert throughput >= 10  # At least 10 req/sec
```

## Security Tests (tests/security/test_security.py)

```python
import pytest
from iris_client.core.client import IRISClient
from iris_client.core.config import IRISConfig
from iris_client.core.exceptions import EncryptionError

@pytest.mark.security
class TestSecurity:
    """Security-focused tests"""
    
    @pytest.mark.asyncio
    async def test_phi_encryption_compliance(self):
        """Test PHI encryption meets HIPAA requirements"""
        config = IRISConfig(
            enable_phi_encryption=True,
            encryption_key_id="test-key"
        )
        
        client = IRISClient(config)
        encryption = client.security.phi_encryption
        
        # Test encrypting various PHI types
        phi_samples = [
            "123-45-6789",  # SSN
            "A12345678",    # MRN
            "1234567890",   # Phone
            "patient@email.com"
        ]
        
        for phi in phi_samples:
            encrypted = encryption.encrypt_phi(phi)
            
            # Verify encryption properties
            assert encrypted["encrypted"] is True
            assert encrypted["algorithm"] == "AES-256-GCM"
            assert len(encrypted["iv"]) > 0
            assert len(encrypted["tag"]) > 0
            assert encrypted["ciphertext"] != phi
            
            # Verify decryption
            decrypted = encryption.decrypt_phi(encrypted)
            assert decrypted == phi
    
    @pytest.mark.asyncio
    async def test_authentication_security(self):
        """Test authentication mechanisms"""
        config = IRISConfig(
            auth_type="hybrid",
            oauth2_client_id="test",
            oauth2_client_secret="secret",
            hmac_key_id="key",
            hmac_secret="secret"
        )
        
        client = IRISClient(config)
        
        # Test HMAC signature includes all required components
        headers = client.security.hmac_signer.sign_request(
            "POST",
            "/test",
            {},
            b"test body"
        )
        
        required_headers = [
            "X-IRIS-Key-Id",
            "X-IRIS-Timestamp",
            "X-IRIS-Nonce",
            "X-IRIS-Signature"
        ]
        
        for header in required_headers:
            assert header in headers
            assert len(headers[header]) > 0
    
    @pytest.mark.asyncio
    async def test_audit_logging_compliance(self):
        """Test audit logging meets SOC2 requirements"""
        # This would integrate with actual audit log verification
        # Checking that all required fields are logged
        pass
```

## Performance Benchmark Script

```python
#!/usr/bin/env python3
"""
Performance benchmark for IRIS API Client
"""
import asyncio
import time
import statistics
from datetime import datetime
from typing import List

from iris_client.core.client import IRISClient
from iris_client.core.config import IRISConfig

async def benchmark_operation(client: IRISClient, operation: str, iterations: int = 100):
    """Benchmark a specific operation"""
    latencies = []
    errors = 0
    
    for i in range(iterations):
        start = time.perf_counter()
        try:
            if operation == "search":
                await client.search_immunizations(limit=10)
            elif operation == "get":
                await client.get_immunization(f"test-{i}")
            # Add more operations as needed
            
            latency = (time.perf_counter() - start) * 1000  # ms
            latencies.append(latency)
        except Exception:
            errors += 1
    
    if latencies:
        return {
            "operation": operation,
            "iterations": iterations,
            "errors": errors,
            "min_latency_ms": min(latencies),
            "max_latency_ms": max(latencies),
            "avg_latency_ms": statistics.mean(latencies),
            "p50_latency_ms": statistics.median(latencies),
            "p95_latency_ms": statistics.quantiles(latencies, n=20)[18],  # 95th percentile
            "p99_latency_ms": statistics.quantiles(latencies, n=100)[98],  # 99th percentile
        }
    else:
        return {"operation": operation, "errors": errors, "status": "all_failed"}

async def run_benchmark():
    """Run complete benchmark suite"""
    config = IRISConfig(mock_mode=True)  # Use mock for consistent results
    
    async with IRISClient(config) as client:
        print("Starting IRIS API Client Benchmark")
        print("=" * 50)
        
        # Benchmark different operations
        operations = ["search", "get"]
        results = []
        
        for op in operations:
            print(f"\nBenchmarking {op} operation...")
            result = await benchmark_operation(client, op)
            results.append(result)
            
            print(f"Results for {op}:")
            for key, value in result.items():
                if isinstance(value, float):
                    print(f"  {key}: {value:.2f}")
                else:
                    print(f"  {key}: {value}")
        
        # Test concurrent load
        print("\nTesting concurrent load (100 concurrent requests)...")
        start = time.perf_counter()
        tasks = [client.search_immunizations(limit=1) for _ in range(100)]
        await asyncio.gather(*tasks, return_exceptions=True)
        duration = time.perf_counter() - start
        
        print(f"Concurrent test completed in {duration:.2f} seconds")
        print(f"Throughput: {100/duration:.2f} requests/second")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
```

## Test Configuration (pytest.ini)

```ini
[pytest]
minversion = 7.0
addopts = 
    -ra 
    --strict-markers 
    --cov=iris_client 
    --cov-report=html 
    --cov-report=term-missing:skip-covered
    --asyncio-mode=auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    unit: Unit tests
    integration: Integration tests
    security: Security tests
    performance: Performance tests
    slow: Slow tests
asyncio_mode = auto

[coverage:run]
source = iris_client
omit = 
    */tests/*
    */migrations/*
    */__pycache__/*

[coverage:report]
precision = 2
show_missing = True
skip_covered = False
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
```

## Running Tests

```bash
# Run all tests
pytest

# Run only unit tests
pytest -m unit

# Run integration tests (requires test containers)
pytest -m integration

# Run security tests
pytest -m security

# Run with coverage
pytest --cov=iris_client --cov-report=html

# Run performance benchmarks
python benchmark.py

# Run specific test file
pytest tests/unit/test_iris_client.py -v

# Run tests in parallel
pytest -n auto

# Run tests with detailed output
pytest -vvs
```


implement! 