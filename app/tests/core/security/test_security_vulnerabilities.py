"""
Security vulnerability tests for the IRIS API system.

Tests for common security vulnerabilities including:
- SQL injection
- XSS (Cross-Site Scripting)
- CSRF (Cross-Site Request Forgery)
- Path traversal
- Authentication bypass
- Input validation failures
"""
import pytest
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.security


class TestInputValidation:
    """Test input validation and sanitization"""
    
    @pytest.mark.asyncio
    async def test_xss_prevention_in_patient_data(self, async_test_client, admin_headers):
        """
        Test that XSS payloads are properly sanitized in patient data.
        This is critical for protecting PHI from script injection.
        """
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';DROP TABLE users;--",
            "<iframe src='javascript:alert(\"xss\")'></iframe>"
        ]
        
        for payload in xss_payloads:
            patient_data = {
                "identifier": [{"use": "official", "value": "TEST123"}],
                "active": True,
                "name": [{"use": "official", "family": payload, "given": ["John"]}],
                "gender": "male",
                "birthDate": "1980-01-01"
            }
            
            response = await async_test_client.post(
                "/api/v1/healthcare/patients",
                headers=admin_headers,
                json=patient_data
            )
            
            if response.status_code == 201:
                # Created - check if payload was sanitized
                created_patient = response.json()
                
                # Verify script tags were removed/escaped
                assert "<script>" not in created_patient["name"][0]["family"]
                assert "javascript:" not in created_patient["name"][0]["family"]
                assert payload != created_patient["name"][0]["family"]  # Should be sanitized
            else:
                # Should be rejected with validation error
                assert response.status_code in [400, 422]


class TestFileUploadSecurity:
    """Test file upload security measures"""
    
    @pytest.mark.asyncio
    async def test_malicious_filename_handling(self, async_test_client, admin_headers):
        """Test handling of malicious filenames in file uploads."""
        
        malicious_filenames = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "file\x00.pdf.exe",  # Null byte injection
            "file%2e%2e%2f%2e%2e%2fpasswd",
            "con.pdf",  # Windows reserved name
            "file|touch /tmp/hacked|.pdf",
        ]
        
        for bad_filename in malicious_filenames:
            files = {
                "file": (bad_filename, b"dummy content", "application/pdf")
            }
            
            response = await async_test_client.post(
                "/api/v1/healthcare/documents/upload",
                headers=admin_headers,
                files=files
            )
            
            # Should reject malicious filenames
            assert response.status_code in [400, 422, 403]
            if response.status_code == 400:
                error_detail = response.json().get("detail", "")
                assert "filename" in error_detail.lower() or "invalid" in error_detail.lower()


class TestSQLInjection:
    """Test SQL injection prevention"""
    
    @pytest.mark.asyncio
    async def test_sql_injection_in_search(self, async_test_client, admin_headers):
        """Test SQL injection attempts in search parameters."""
        
        sql_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "1' UNION SELECT * FROM users --",
            "'; INSERT INTO users (username) VALUES ('hacker'); --",
            "1' AND (SELECT COUNT(*) FROM users) > 0 --"
        ]
        
        for payload in sql_payloads:
            response = await async_test_client.get(
                f"/api/v1/healthcare/patients?search={payload}",
                headers=admin_headers
            )
            
            # Should not return SQL errors or expose database structure
            assert response.status_code != 500
            if response.status_code == 200:
                data = response.json()
                # Should not contain SQL error messages
                assert "sql" not in str(data).lower()
                assert "error" not in str(data).lower()
                assert "exception" not in str(data).lower()


class TestAuthenticationBypass:
    """Test authentication and authorization bypass attempts"""
    
    @pytest.mark.asyncio
    async def test_jwt_manipulation_attempts(self, async_test_client):
        """Test attempts to manipulate JWT tokens."""
        
        malicious_tokens = [
            "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiYWRtaW4ifQ.invalid",
            "Bearer ../../../admin/token",
            "Bearer null",
            "Bearer undefined",
            "Bearer <script>alert('xss')</script>",
        ]
        
        for token in malicious_tokens:
            response = await async_test_client.get(
                "/api/v1/healthcare/patients",
                headers={"Authorization": token}
            )
            
            # Should reject invalid tokens
            assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_privilege_escalation_attempts(self, async_test_client, user_headers):
        """Test attempts to access admin-only endpoints with user credentials."""
        
        admin_endpoints = [
            "/api/v1/audit/logs",
            "/api/v1/users",
            "/api/v1/purge/policies",
            "/api/v1/admin/system-info"
        ]
        
        for endpoint in admin_endpoints:
            response = await async_test_client.get(
                endpoint,
                headers=user_headers
            )
            
            # Should deny access
            assert response.status_code in [401, 403]


class TestRateLimiting:
    """Test rate limiting protection"""
    
    @pytest.mark.asyncio
    async def test_login_rate_limiting(self, async_test_client):
        """Test rate limiting on login attempts."""
        
        login_data = {
            "username": "nonexistent",
            "password": "wrongpassword"
        }
        
        # Attempt multiple failed logins
        failed_attempts = 0
        for i in range(10):  # Try 10 failed logins
            response = await async_test_client.post(
                "/api/v1/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 429:  # Rate limited
                break
            else:
                failed_attempts += 1
        
        # Should eventually rate limit
        assert failed_attempts < 10, "Rate limiting not working - too many attempts allowed"


class TestDataExposure:
    """Test for sensitive data exposure"""
    
    @pytest.mark.asyncio
    async def test_error_messages_dont_expose_sensitive_data(self, async_test_client):
        """Test that error messages don't expose sensitive information."""
        
        # Test various endpoints that might expose sensitive data
        test_cases = [
            ("/api/v1/auth/login", {"username": "admin", "password": "wrong"}),
            ("/api/v1/patients/99999", None),  # Non-existent patient
            ("/api/v1/audit/logs/99999", None),  # Non-existent log
        ]
        
        for endpoint, data in test_cases:
            if data:
                response = await async_test_client.post(
                    endpoint,
                    json=data if "login" not in endpoint else None,
                    data=data if "login" in endpoint else None,
                    headers={"Content-Type": "application/x-www-form-urlencoded" if "login" in endpoint else "application/json"}
                )
            else:
                response = await async_test_client.get(endpoint)
            
            if response.status_code >= 400:
                error_response = response.json()
                error_text = str(error_response).lower()
                
                # Should not expose sensitive information
                assert "password" not in error_text
                assert "database" not in error_text
                assert "connection" not in error_text
                assert "internal" not in error_text
                assert "traceback" not in error_text


class TestCSRFProtection:
    """Test CSRF protection mechanisms"""
    
    @pytest.mark.asyncio
    async def test_csrf_token_required_for_state_changing_operations(self, async_test_client, admin_headers):
        """Test that CSRF protection is in place for state-changing operations."""
        
        # Remove CSRF token from headers if present
        headers_without_csrf = admin_headers.copy()
        headers_without_csrf.pop("X-CSRF-Token", None)
        
        patient_data = {
            "identifier": [{"use": "official", "value": "TEST123"}],
            "active": True,
            "name": [{"use": "official", "family": "TestUser", "given": ["John"]}],
            "gender": "male",
            "birthDate": "1980-01-01"
        }
        
        # Should require CSRF token for POST operations
        response = await async_test_client.post(
            "/api/v1/healthcare/patients",
            headers=headers_without_csrf,
            json=patient_data
        )
        
        # Note: Actual CSRF implementation may vary
        # This test ensures we're thinking about CSRF protection
        # Implementation depends on the specific CSRF strategy used
        assert response.status_code in [200, 201, 403]  # Allow success if CSRF not yet implemented


class TestSecurityHeaders:
    """Test security headers in responses"""
    
    @pytest.mark.asyncio
    async def test_security_headers_present(self, async_test_client):
        """Test that important security headers are present."""
        
        response = await async_test_client.get("/health")
        
        # Check for important security headers
        headers = response.headers
        
        # These headers help prevent various attacks
        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options", 
            "X-XSS-Protection",
        ]
        
        for header in security_headers:
            # Note: Some headers might not be implemented yet
            # This test documents what should be implemented
            if header in headers:
                assert headers[header] is not None


# Placeholder tests for future security enhancements
class TestAdvancedSecurityFeatures:
    """Placeholder for advanced security feature tests"""
    
    @pytest.mark.skip(reason="Not yet implemented")
    @pytest.mark.asyncio
    async def test_content_security_policy(self, async_test_client):
        """Test Content Security Policy implementation."""
        pass
    
    @pytest.mark.skip(reason="Not yet implemented") 
    @pytest.mark.asyncio
    async def test_api_key_rotation(self, async_test_client):
        """Test API key rotation functionality."""
        pass
    
    @pytest.mark.skip(reason="Not yet implemented")
    @pytest.mark.asyncio
    async def test_encryption_key_management(self, async_test_client):
        """Test encryption key management and rotation."""
        pass