"""
Smoke Tests: Core API Endpoints

Verifies that all critical API endpoints are:
- Accessible and returning correct status codes
- Properly authenticated when required
- Returning expected response structures
"""
import pytest
from typing import Dict, List, Tuple

from app.core.security import create_access_token


pytestmark = pytest.mark.smoke


class TestPublicEndpoints:
    """Test endpoints that should be accessible without authentication"""
    
    @pytest.mark.asyncio
    async def test_openapi_documentation(self, async_test_client):
        """
        Test that API documentation is accessible.
        Developers need this to understand the API.
        """
        # Test OpenAPI JSON endpoint
        response = await async_test_client.get("/openapi.json")
        assert response.status_code == 200
        
        openapi_spec = response.json()
        assert openapi_spec["openapi"].startswith("3.")  # OpenAPI 3.x
        assert "IRIS" in openapi_spec["info"]["title"]
        assert len(openapi_spec["paths"]) >= 20  # Should have 20+ endpoints
        
        print(f"✓ OpenAPI spec available with {len(openapi_spec['paths'])} endpoints")
        
        # Test Swagger UI
        response = await async_test_client.get("/docs")
        assert response.status_code == 200
        assert "swagger-ui" in response.text.lower()
        
        # Test ReDoc
        response = await async_test_client.get("/redoc")
        assert response.status_code == 200
        assert "redoc" in response.text.lower()
        
        print("✓ API documentation endpoints accessible")
    
    @pytest.mark.asyncio
    async def test_health_endpoints_public_access(self, async_test_client):
        """
        Test that health endpoints work without authentication.
        Monitoring systems need unauthenticated access.
        """
        endpoints = [
            ("/health", 200),
            ("/health/detailed", 200),
        ]
        
        for endpoint, expected_status in endpoints:
            response = await async_test_client.get(endpoint)
            assert response.status_code == expected_status, f"{endpoint} failed"
            
            if response.status_code == 200:
                data = response.json()
                assert "status" in data
                assert data["status"] in ["healthy", "degraded", "unhealthy"]
        
        print("✓ All health endpoints accessible without auth")


class TestProtectedEndpoints:
    """Test endpoints that require authentication"""
    
    @pytest.fixture
    async def auth_headers(self, test_user) -> Dict[str, str]:
        """Generate auth headers for requests"""
        token = create_access_token(
            data={
                "sub": str(test_user.id),
                "user_id": str(test_user.id),
                "username": test_user.username,
                "role": test_user.role,
                "email": test_user.email
            }
        )
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture
    async def admin_headers(self, test_admin_user) -> Dict[str, str]:
        """Generate admin auth headers"""
        token = create_access_token(
            data={
                "sub": str(test_admin_user.id),
                "user_id": str(test_admin_user.id),
                "username": test_admin_user.username,
                "role": test_admin_user.role,
                "email": test_admin_user.email
            }
        )
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.mark.asyncio
    async def test_auth_endpoints(self, async_test_client, auth_headers):
        """
        Test authentication-related endpoints.
        Core functionality for user management.
        """
        # Test current user info
        response = await async_test_client.get(
            "/api/v1/auth/me",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "username" in data
        assert "role" in data
        
        print("✓ Auth endpoints accessible")
    
    @pytest.mark.asyncio
    async def test_audit_log_endpoints(self, async_test_client, admin_headers):
        """
        Test audit logging endpoints.
        Required for SOC2 compliance.
        """
        # List audit logs (admin only)
        response = await async_test_client.get(
            "/api/v1/audit-logs",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        # Search audit logs
        response = await async_test_client.get(
            "/api/v1/audit-logs/search?action=LOGIN",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        print("✓ Audit log endpoints accessible to admin")
    
    @pytest.mark.asyncio
    async def test_iris_api_endpoints(self, async_test_client, auth_headers):
        """
        Test IRIS API integration endpoints.
        External system integration points.
        """
        # IRIS status endpoint
        response = await async_test_client.get(
            "/api/v1/iris/status",
            headers=auth_headers
        )
        assert response.status_code in [200, 503]  # 503 if IRIS is down
        
        # IRIS sync endpoint should exist
        response = await async_test_client.post(
            "/api/v1/iris/sync",
            headers=auth_headers,
            json={"patient_id": "test"}
        )
        assert response.status_code in [200, 202, 400, 404]
        
        print("✓ IRIS integration endpoints accessible")


class TestEndpointSecurity:
    """Test security aspects of endpoints"""
    
    @pytest.mark.asyncio
    async def test_all_endpoints_require_auth(self, async_test_client):
        """
        Verify all sensitive endpoints require authentication.
        Critical for PHI protection.
        """
        # Endpoints that should require auth
        protected_endpoints = [
            ("/api/v1/auth/me", "GET"),
            ("/api/v1/auth/users", "GET"),
            ("/api/v1/audit-logs", "GET"),
            ("/api/v1/iris/status", "GET"),
            ("/api/v1/iris/sync", "POST"),
        ]
        
        for endpoint, method in protected_endpoints:
            if method == "GET":
                response = await async_test_client.get(endpoint)
            elif method == "POST":
                response = await async_test_client.post(endpoint, json={})
            
            assert response.status_code == 401, f"{endpoint} not protected!"
            assert "Not authenticated" in response.json()["detail"]
        
        print(f"✓ All {len(protected_endpoints)} protected endpoints require auth")
    
    @pytest.mark.asyncio
    async def test_cors_headers(self, async_test_client):
        """
        Test CORS headers are properly configured.
        Important for frontend integration.
        """
        # Make OPTIONS request
        response = await async_test_client.options(
            "/api/v1/auth/me",
            headers={"Origin": "http://localhost:3000"}
        )
        
        # Check CORS headers
        if "access-control-allow-origin" in response.headers:
            allowed_origin = response.headers["access-control-allow-origin"]
            assert allowed_origin in ["*", "http://localhost:3000"]
            print(f"✓ CORS configured: {allowed_origin}")
        else:
            print("⚠️  CORS not configured - needed for frontend")
    
    @pytest.mark.asyncio
    async def test_response_headers_security(self, async_test_client):
        """
        Test security headers are present.
        Important for preventing common attacks.
        """
        response = await async_test_client.get("/health")
        
        # Check security headers
        security_headers = {
            "x-content-type-options": "nosniff",
            "x-frame-options": ["DENY", "SAMEORIGIN"],
            "x-xss-protection": "1; mode=block",
            "strict-transport-security": "max-age=31536000",
        }
        
        present_headers = []
        missing_headers = []
        
        for header, valid_values in security_headers.items():
            if header in response.headers:
                value = response.headers[header]
                if isinstance(valid_values, list):
                    assert value in valid_values
                else:
                    assert value == valid_values
                present_headers.append(header)
            else:
                missing_headers.append(header)
        
        if missing_headers:
            print(f"⚠️  Missing security headers: {', '.join(missing_headers)}")
        else:
            print("✓ All security headers present")


class TestEndpointPerformance:
    """Basic performance smoke tests"""
    
    @pytest.mark.asyncio
    async def test_endpoint_response_times(self, async_test_client, auth_headers):
        """
        Test that key endpoints respond quickly.
        Slow endpoints indicate system issues.
        """
        import time
        
        performance_targets = [
            ("/health", 100),  # Should respond in <100ms
            ("/api/v1/auth/me", 200),  # Auth check <200ms
        ]
        
        results = []
        
        for endpoint, max_ms in performance_targets:
            start = time.time()
            
            if endpoint == "/health":
                response = await async_test_client.get(endpoint)
            else:
                response = await async_test_client.get(endpoint, headers=auth_headers)
            
            elapsed_ms = (time.time() - start) * 1000
            
            results.append({
                "endpoint": endpoint,
                "status": response.status_code,
                "time_ms": elapsed_ms,
                "target_ms": max_ms,
                "passed": elapsed_ms < max_ms
            })
        
        # Report results
        for result in results:
            status = "✓" if result["passed"] else "⚠️"
            print(f"{status} {result['endpoint']}: {result['time_ms']:.0f}ms (target: {result['target_ms']}ms)")
        
        # At least 80% should meet targets
        passed = sum(1 for r in results if r["passed"])
        assert passed >= len(results) * 0.8, "Too many slow endpoints"


class TestAPIVersioning:
    """Test API versioning is properly implemented"""
    
    @pytest.mark.asyncio
    async def test_api_version_in_urls(self, async_test_client):
        """
        Verify API versioning is consistent.
        Important for backward compatibility.
        """
        # Get OpenAPI spec
        response = await async_test_client.get("/openapi.json")
        openapi_spec = response.json()
        
        # Check all paths use v1
        api_paths = [
            path for path in openapi_spec["paths"] 
            if path.startswith("/api/")
        ]
        
        v1_paths = [
            path for path in api_paths 
            if path.startswith("/api/v1/")
        ]
        
        assert len(v1_paths) == len(api_paths), "All API paths should use v1"
        print(f"✓ All {len(api_paths)} API endpoints use v1 versioning")
        
        # Test version in response headers
        response = await async_test_client.get("/health")
        if "api-version" in response.headers:
            assert response.headers["api-version"] == "1.0"
            print("✓ API version in response headers")


if __name__ == "__main__":
    """
    Run core endpoint smoke tests directly:
    python app/tests/smoke/test_core_endpoints.py
    """
    print("🌐 Running core endpoint tests...")
    pytest.main([__file__, "-v", "--tb=short"])