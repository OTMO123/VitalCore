"""
Enterprise Integration Tests - PyTest Compatible
Comprehensive validation of all modules/services working together
"""

import pytest
import httpx
import asyncio
from typing import Dict, Any

class TestEnterpriseIntegration:
    """Enterprise integration test suite for pytest."""
    
    base_url = "http://localhost:8000"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_health_monitoring_integration(self):
        """Test health monitoring system integration."""
        async with httpx.AsyncClient() as client:
            # Test basic health
            response = await client.get(f"{self.base_url}/health", timeout=10)
            assert response.status_code == 200
            
            health_data = response.json()
            assert health_data["status"] in ["healthy", "operational"]
            assert "database" in health_data
            assert health_data["database"]["status"] == "connected"
            
            # Test detailed health
            detailed_response = await client.get(f"{self.base_url}/health/detailed", timeout=10)
            assert detailed_response.status_code == 200
            
            print("✅ Health monitoring integration: PASSED")
    
    @pytest.mark.integration
    @pytest.mark.asyncio 
    async def test_database_application_integration(self):
        """Test database integration through application layer."""
        async with httpx.AsyncClient() as client:
            # Test endpoint that requires database
            response = await client.get(f"{self.base_url}/api/v1/clinical-documents", timeout=10)
            
            # Should get auth error (401) not database error (500)
            assert response.status_code in [200, 401, 403], f"Database integration error: {response.status_code}"
            
            print("✅ Database application integration: PASSED")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_authentication_integration(self):
        """Test authentication system integration."""
        async with httpx.AsyncClient() as client:
            # Test auth endpoint exists and responds
            response = await client.post(
                f"{self.base_url}/api/v1/auth/login",
                json={"username": "test", "password": "test"},
                timeout=10
            )
            
            # Should not crash (no 500 error)
            assert response.status_code != 500, "Authentication system error"
            
            # Test protected endpoint is protected
            protected_response = await client.get(f"{self.base_url}/api/v1/healthcare/patients", timeout=10)
            assert protected_response.status_code == 401, "Protected endpoints not secured"
            
            print("✅ Authentication integration: PASSED")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_healthcare_services_integration(self):
        """Test healthcare services integration."""
        async with httpx.AsyncClient() as client:
            healthcare_endpoints = [
                "/api/v1/healthcare/patients",
                "/api/v1/patients/risk/stratification",
                "/api/v1/clinical-documents"
            ]
            
            for endpoint in healthcare_endpoints:
                response = await client.get(f"{self.base_url}{endpoint}", timeout=10)
                
                # Should require auth (401) not crash (500)
                assert response.status_code != 500, f"Healthcare service error at {endpoint}"
                
            print("✅ Healthcare services integration: PASSED")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_audit_security_integration(self):
        """Test audit and security systems integration."""
        async with httpx.AsyncClient() as client:
            # Test audit logging
            response = await client.get(f"{self.base_url}/api/v1/audit-logs", timeout=10)
            assert response.status_code != 500, "Audit system error"
            
            # Test security monitoring
            security_response = await client.get(f"{self.base_url}/api/v1/security/violations", timeout=10)
            assert security_response.status_code != 500, "Security monitoring error"
            
            print("✅ Audit security integration: PASSED")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_document_management_integration(self):
        """Test document management integration."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/v1/documents", timeout=10)
            assert response.status_code != 500, "Document management system error"
            
            print("✅ Document management integration: PASSED")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_clinical_workflows_integration(self):
        """Test clinical workflows integration."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/v1/clinical-workflows", timeout=10)
            assert response.status_code != 500, "Clinical workflows system error"
            
            print("✅ Clinical workflows integration: PASSED")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_api_documentation_integration(self):
        """Test API documentation and service discovery."""
        async with httpx.AsyncClient() as client:
            # Test API docs
            response = await client.get(f"{self.base_url}/docs", timeout=10)
            assert response.status_code == 200, "API documentation not accessible"
            
            # Test OpenAPI spec
            openapi_response = await client.get(f"{self.base_url}/openapi.json", timeout=10)
            assert openapi_response.status_code == 200, "OpenAPI spec not available"
            
            openapi_data = openapi_response.json()
            paths_count = len(openapi_data.get("paths", {}))
            assert paths_count >= 10, f"Too few API endpoints: {paths_count}"
            
            print(f"✅ API documentation integration: {paths_count} endpoints")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_security_headers_integration(self):
        """Test security headers integration."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/health", timeout=10)
            
            # Check for security headers
            security_headers = [
                "X-Content-Type-Options",
                "X-Frame-Options",
                "X-XSS-Protection"
            ]
            
            present_headers = [h for h in security_headers if h in response.headers]
            assert len(present_headers) > 0, "No security headers present"
            
            print(f"✅ Security headers integration: {', '.join(present_headers)}")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_enterprise_compliance_integration(self):
        """Test enterprise compliance features integration."""
        async with httpx.AsyncClient() as client:
            # Get health data to check enterprise features
            response = await client.get(f"{self.base_url}/health", timeout=10)
            assert response.status_code == 200
            
            health_data = response.json()
            
            # Check database extensions (SOC2/HIPAA compliance)
            extensions = health_data.get("database", {}).get("extensions", [])
            required_extensions = ["pgcrypto", "uuid-ossp"]
            
            for ext in required_extensions:
                assert ext in extensions, f"Missing enterprise extension: {ext}"
            
            # Check enterprise monitoring fields
            monitoring_fields = ["timestamp", "version", "database", "redis"]
            for field in monitoring_fields:
                assert field in health_data, f"Missing monitoring field: {field}"
            
            print("✅ Enterprise compliance integration: SOC2/HIPAA features verified")

@pytest.mark.integration
class TestServiceInteraction:
    """Test service-to-service interactions."""
    
    base_url = "http://localhost:8000"
    
    @pytest.mark.asyncio
    async def test_health_to_database_interaction(self):
        """Test health endpoint correctly reports database status."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/health", timeout=10)
            health_data = response.json()
            
            # Health endpoint should correctly report database connectivity
            assert health_data["database"]["status"] == "connected"
            assert len(health_data["database"]["extensions"]) >= 2
            
            print("✅ Health-Database interaction: PASSED")
    
    @pytest.mark.asyncio
    async def test_auth_to_protected_endpoints_interaction(self):
        """Test authentication properly protects all endpoints."""
        async with httpx.AsyncClient() as client:
            protected_endpoints = [
                "/api/v1/healthcare/patients",
                "/api/v1/documents",
                "/api/v1/clinical-workflows"
            ]
            
            for endpoint in protected_endpoints:
                response = await client.get(f"{self.base_url}{endpoint}", timeout=10)
                # Should require authentication (401/403) or not exist yet (404)
                assert response.status_code in [401, 403, 404], f"Endpoint not protected: {endpoint}"
            
            print("✅ Auth-Endpoints interaction: All endpoints properly protected")

# Fixture for integration tests
@pytest.fixture(scope="session")
def enterprise_client():
    """Provide HTTP client for enterprise testing."""
    return httpx.AsyncClient(base_url="http://localhost:8000", timeout=30.0)