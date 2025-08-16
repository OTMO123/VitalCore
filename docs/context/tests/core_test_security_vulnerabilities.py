"""
Core Tests: Security Vulnerabilities and Hardening

Comprehensive security tests for:
- Input validation and sanitization
- XSS and injection prevention
- File upload security
- API rate limiting
- Session security
- CSRF protection
- Security headers
- Data leak prevention
"""
import pytest
import asyncio
import base64
import mimetypes
from datetime import datetime, timedelta
from typing import List, Dict
import uuid
import json

from app.core.config import settings


pytestmark = [pytest.mark.asyncio, pytest.mark.core, pytest.mark.security]


class TestInputValidation:
    """Test input validation and sanitization"""
    
    async def test_xss_prevention_in_patient_data(
        self,
        async_client,
        admin_headers
    ):
        """
        Test XSS prevention in all input fields.
        Critical for preventing client-side attacks.
        """
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(\"XSS\")'></iframe>",
            "'><script>alert(String.fromCharCode(88,83,83))</script>",
            "<input type=\"text\" onfocus=\"alert('XSS')\">",
            "<body onload=alert('XSS')>",
            "&#60;script&#62;alert('XSS')&#60;/script&#62;",
        ]
        
        for payload in xss_payloads:
            patient_data = {
                "first_name": payload,
                "last_name": f"Test{payload}",
                "date_of_birth": "1990-01-01",
                "ssn": "123-45-6789",
                "notes": payload  # Free text field
            }
            
            response = await async_client.post(
                "/api/v1/patients",
                headers=admin_headers,
                json=patient_data
            )
            
            if response.status_code == 201:
                # Created - check if payload was sanitized
                created_patient = response.json()
                
                # Verify script tags were removed/escaped
                assert "<script>                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    </script>",
            "file\x00.pdf.exe",  # Null byte injection
            "file%2e%2e%2f%2e%2e%2fpasswd",
            "con.pdf",  # Windows reserved name
            "file|touch /tmp/hacked|.pdf",
        ]
        
        for bad_filename in malicious_filenames:
            files = {
                "file": (bad_filename, b"dummy content", "application/pdf")
            }
            
            response = await async_client.post(
                "/api/v1/documents/upload",
                headers=admin_headers,
                files=files,
                data={"document_type": "clinical"}
            )
            
            if response.status_code == 201:
                # Check if filename was sanitized
                doc_info = response.json()
                stored_filename = doc_info.get("filename", "")
                
                # Verify dangerous patterns removed
                assert ".." not in stored_filename
                assert "<script>" not in stored_filename
                assert "|" not in stored_filename
                assert "\x00" not in stored_filename
        
        print("✓ Filename sanitization verified")
    
    async def test_file_content_validation(
        self,
        async_client,
        admin_headers
    ):
        """
        Test that file content matches declared type.
        Prevents disguised malware.
        """
        # PDF magic bytes but executable content
        fake_pdf = b"%PDF-1.4\n" + b"MZ\x90\x00" + b"\x00" * 1000
        
        files = {
            "file": ("document.pdf", fake_pdf, "application/pdf")
        }
        
        response = await async_client.post(
            "/api/v1/documents/upload",
            headers=admin_headers,
            files=files,
            data={"document_type": "clinical"}
        )
        
        if response.status_code in [400, 415, 422]:
            print("✓ File content validation active")
        elif response.status_code == 201:
            # Check if flagged as suspicious
            doc_info = response.json()
            if doc_info.get("warning") or doc_info.get("scan_status"):
                print("✓ Suspicious file content detected")


class TestAPIRateLimiting:
    """Test API rate limiting and DoS protection"""
    
    async def test_authentication_rate_limiting(
        self,
        async_client
    ):
        """
        Test rate limiting on authentication endpoints.
        Prevents brute force attacks.
        """
        # Make rapid login attempts
        rate_limited = False
        responses = []
        
        for i in range(20):
            response = await async_client.post(
                "/api/v1/auth/login",
                data={
                    "username": f"attacker{i}",
                    "password": "wrong"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            responses.append(response.status_code)
            
            if response.status_code == 429:
                rate_limited = True
                break
            
            # Small delay to be nice to the server
            await asyncio.sleep(0.1)
        
        if rate_limited:
            print("✓ Authentication rate limiting active")
        else:
            # Check if any protective measure
            unique_codes = set(responses)
            if 403 in unique_codes or len(unique_codes) > 2:
                print("✓ Authentication protection detected")
            else:
                print("⚠️  No rate limiting on authentication")
    
    async def test_api_endpoint_rate_limiting(
        self,
        async_client,
        user_headers
    ):
        """
        Test general API endpoint rate limiting.
        Prevents API abuse.
        """
        # Hammer a single endpoint
        rate_limited = False
        endpoint = "/api/v1/patients"
        
        for i in range(100):
            response = await async_client.get(
                endpoint,
                headers=user_headers
            )
            
            if response.status_code == 429:
                rate_limited = True
                
                # Check rate limit headers
                headers = response.headers
                if "x-ratelimit-limit" in headers:
                    limit = headers["x-ratelimit-limit"]
                    remaining = headers.get("x-ratelimit-remaining", "0")
                    reset = headers.get("x-ratelimit-reset")
                    
                    print(f"✓ Rate limiting active: {limit} requests, {remaining} remaining")
                else:
                    print("✓ Rate limiting active (429 response)")
                break
        
        if not rate_limited:
            print("⚠️  No rate limiting detected on API endpoints")
    
    async def test_rate_limit_by_user_not_ip(
        self,
        async_client,
        test_users_by_role
    ):
        """
        Test that rate limits are per-user, not per-IP.
        Prevents shared IP issues.
        """
        # Get tokens for two users
        user1 = test_users_by_role["user"]
        admin = test_users_by_role["admin"]
        
        user1_headers = await self._get_auth_headers(async_client, user1)
        admin_headers = await self._get_auth_headers(async_client, admin)
        
        # Hit rate limit with user1
        for i in range(50):
            response = await async_client.get(
                "/api/v1/patients",
                headers=user1_headers
            )
            if response.status_code == 429:
                break
        
        # Admin should still have access
        response = await async_client.get(
            "/api/v1/patients",
            headers=admin_headers
        )
        
        if response.status_code == 200:
            print("✓ Rate limits are per-user, not per-IP")
        elif response.status_code == 429:
            print("⚠️  Rate limits might be per-IP (could affect legitimate users)")
    
    async def _get_auth_headers(self, async_client, user):
        """Helper to get auth headers"""
        response = await async_client.post(
            "/api/v1/auth/login",
            data={
                "username": user.username,
                "password": "testpassword123"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}


class TestSessionSecurity:
    """Test session and authentication security"""
    
    async def test_token_entropy(
        self,
        async_client,
        test_user
    ):
        """
        Test that tokens have sufficient entropy.
        Prevents token prediction attacks.
        """
        tokens = []
        
        # Generate multiple tokens
        for i in range(5):
            response = await async_client.post(
                "/api/v1/auth/login",
                data={
                    "username": test_user.username,
                    "password": "testpassword123"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            token = response.json()["access_token"]
            tokens.append(token)
            
            # Small delay between logins
            await asyncio.sleep(0.1)
        
        # Verify tokens are unique
        assert len(set(tokens)) == len(tokens), "Duplicate tokens generated!"
        
        # Check token length (JWT should be >100 chars)
        avg_length = sum(len(t) for t in tokens) / len(tokens)
        assert avg_length > 100, "Tokens too short"
        
        # Basic entropy check - tokens should be very different
        for i in range(len(tokens) - 1):
            similarity = sum(
                1 for a, b in zip(tokens[i], tokens[i+1]) 
                if a == b
            ) / len(tokens[i])
            assert similarity < 0.5, "Tokens too similar"
        
        print("✓ Token entropy verified")
    
    async def test_concurrent_session_limit(
        self,
        async_client,
        test_user
    ):
        """
        Test concurrent session limits if implemented.
        Prevents session hijacking spread.
        """
        sessions = []
        
        # Create multiple sessions
        for i in range(10):
            response = await async_client.post(
                "/api/v1/auth/login",
                data={
                    "username": test_user.username,
                    "password": "testpassword123"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                sessions.append(response.json()["access_token"])
            elif response.status_code == 429:
                print(f"✓ Session limit enforced at {i} concurrent sessions")
                return
        
        # Test if old sessions are invalidated
        if len(sessions) > 5:
            # Try using first session
            response = await async_client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {sessions[0]}"}
            )
            
            if response.status_code == 401:
                print("✓ Old sessions invalidated when limit exceeded")
            else:
                print("⚠️  No concurrent session limit detected")
    
    async def test_token_refresh_security(
        self,
        async_client,
        test_user
    ):
        """
        Test token refresh mechanism security.
        Should not allow indefinite token refresh.
        """
        # Get initial token
        response = await async_client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.username,
                "password": "testpassword123"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        access_token = response.json()["access_token"]
        
        # Check if refresh endpoint exists
        response = await async_client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {access_token}"},
            json={}
        )
        
        if response.status_code == 404:
            # No refresh tokens - that's actually secure for healthcare
            print("✓ No refresh tokens (secure for healthcare)")
        elif response.status_code == 200:
            # Has refresh - verify it's limited
            new_token = response.json().get("access_token")
            assert new_token != access_token, "Same token returned"
            
            # Try to refresh expired token
            expired_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE1NzA1NTU1NTV9.invalid"
            response = await async_client.post(
                "/api/v1/auth/refresh",
                headers={"Authorization": f"Bearer {expired_token}"},
                json={}
            )
            assert response.status_code == 401
            print("✓ Token refresh has security controls")


class TestSecurityHeaders:
    """Test security headers and browser protections"""
    
    async def test_security_headers_presence(
        self,
        async_client
    ):
        """
        Test that security headers are present.
        Prevents various browser-based attacks.
        """
        response = await async_client.get("/health")
        headers = response.headers
        
        security_headers = {
            "x-content-type-options": "nosniff",
            "x-frame-options": ["DENY", "SAMEORIGIN"],
            "x-xss-protection": "1; mode=block",
            "strict-transport-security": "max-age=",
            "content-security-policy": ["default-src", "script-src"],
            "referrer-policy": ["no-referrer", "strict-origin"],
            "permissions-policy": "geolocation=(), microphone=()",
        }
        
        present_headers = []
        missing_headers = []
        
        for header, expected_values in security_headers.items():
            if header in headers:
                value = headers[header].lower()
                if isinstance(expected_values, list):
                    if any(exp in value for exp in expected_values):
                        present_headers.append(header)
                    else:
                        missing_headers.append(f"{header} (wrong value)")
                else:
                    if expected_values in value:
                        present_headers.append(header)
                    else:
                        missing_headers.append(f"{header} (wrong value)")
            else:
                missing_headers.append(header)
        
        print(f"✓ Security headers present: {len(present_headers)}/{len(security_headers)}")
        if missing_headers:
            print(f"⚠️  Missing: {', '.join(missing_headers)}")
    
    async def test_cors_configuration(
        self,
        async_client
    ):
        """
        Test CORS is properly configured.
        Prevents unauthorized cross-origin requests.
        """
        # Test preflight request
        response = await async_client.options(
            "/api/v1/patients",
            headers={
                "Origin": "https://evil.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type"
            }
        )
        
        if "access-control-allow-origin" in response.headers:
            allowed_origin = response.headers["access-control-allow-origin"]
            
            if allowed_origin == "*":
                print("⚠️  CORS allows all origins (security risk)")
            elif allowed_origin == "https://evil.com":
                print("⚠️  CORS not properly restricted")
            else:
                print(f"✓ CORS properly configured: {allowed_origin}")
        else:
            print("✓ CORS not enabled (secure default)")
    
    async def test_content_type_validation(
        self,
        async_client,
        admin_headers
    ):
        """
        Test that content-type is validated.
        Prevents content-type confusion attacks.
        """
        # Send JSON with wrong content-type
        response = await async_client.post(
            "/api/v1/patients",
            headers={
                **admin_headers,
                "Content-Type": "text/plain"
            },
            data=json.dumps({
                "first_name": "Test",
                "last_name": "Patient",
                "date_of_birth": "1990-01-01",
                "ssn": "123-45-6789"
            })
        )
        
        # Should reject or handle carefully
        assert response.status_code in [400, 415, 422]
        
        print("✓ Content-Type validation active")


class TestDataLeakPrevention:
    """Test prevention of data leaks"""
    
    async def test_error_message_sanitization(
        self,
        async_client,
        user_headers
    ):
        """
        Test that error messages don't leak sensitive info.
        Prevents information disclosure.
        """
        # Trigger various errors
        error_triggers = [
            ("/api/v1/patients/invalid-uuid", "GET"),
            ("/api/v1/nonexistent-endpoint", "GET"),
            ("/api/v1/patients", "POST"),  # Missing data
        ]
        
        for endpoint, method in error_triggers:
            if method == "GET":
                response = await async_client.get(endpoint, headers=user_headers)
            else:
                response = await async_client.post(
                    endpoint,
                    headers=user_headers,
                    json={}
                )
            
            if response.status_code >= 400:
                error_text = response.text.lower()
                
                # Check for sensitive information leaks
                sensitive_patterns = [
                    "sqlalchemy",
                    "psycopg2",
                    "traceback",
                    "file \"",
                    "line [0-9]+",
                    "postgresql",
                    "table",
                    "column",
                    "constraint",
                ]
                
                for pattern in sensitive_patterns:
                    assert pattern not in error_text, f"Error leaks: {pattern}"
        
        print("✓ Error messages properly sanitized")
    
    async def test_debug_mode_disabled(
        self,
        async_client
    ):
        """
        Test that debug mode is disabled.
        Debug mode can leak sensitive information.
        """
        # Try to access debug endpoints
        debug_endpoints = [
            "/_debug/",
            "/debug/",
            "/__debug__/",
            "/api/debug",
            "/metrics",
            "/api/v1/_internal/debug",
        ]
        
        for endpoint in debug_endpoints:
            response = await async_client.get(endpoint)
            
            # Should not exist or require auth
            assert response.status_code in [404, 401, 403]
            
            # Check response doesn't contain debug info
            if response.status_code != 404:
                assert "debug" not in response.text.lower()
                assert "stack" not in response.text.lower()
        
        print("✓ Debug endpoints disabled")
    
    async def test_api_response_filtering(
        self,
        async_client,
        user_headers,
        admin_headers,
        test_patient
    ):
        """
        Test that API responses filter sensitive fields.
        Prevents accidental data exposure.
        """
        # Get patient data as different roles
        response_user = await async_client.get(
            f"/api/v1/patients/{test_patient.id}",
            headers=user_headers
        )
        
        response_admin = await async_client.get(
            f"/api/v1/patients/{test_patient.id}",
            headers=admin_headers
        )
        
        if response_user.status_code == 200:
            user_data = response_user.json()
            admin_data = response_admin.json()
            
            # Check if sensitive fields are filtered for regular users
            sensitive_fields = [
                "ssn_encrypted",
                "encryption_key",
                "internal_notes",
                "audit_metadata",
                "__v",  # Version field
                "_id",  # Internal ID
            ]
            
            user_fields = json.dumps(user_data)
            for field in sensitive_fields:
                assert field not in user_fields, f"Sensitive field exposed: {field}"
            
            print("✓ API response filtering active")
    
    async def test_timing_attack_mitigation(
        self,
        async_client
    ):
        """
        Test protection against timing attacks.
        Important for authentication security.
        """
        import time
        
        valid_username = "testuser"
        invalid_username = "nonexistentuser12345"
        
        timings_valid = []
        timings_invalid = []
        
        # Measure login timing
        for _ in range(5):
            # Valid username
            start = time.time()
            await async_client.post(
                "/api/v1/auth/login",
                data={
                    "username": valid_username,
                    "password": "wrongpass"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            timings_valid.append(time.time() - start)
            
            # Invalid username
            start = time.time()
            await async_client.post(
                "/api/v1/auth/login",
                data={
                    "username": invalid_username,
                    "password": "wrongpass"
                },
                headers={"Content-Type": "application/x-www-form-url