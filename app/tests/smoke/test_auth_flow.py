"""
Smoke Tests: Authentication Flow

Tests the complete authentication lifecycle:
- User login with credentials
- JWT token generation and validation
- Role-based access control
- Token expiration
- Logout flow
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from jose import jwt, JWTError
import time

from app.core.config import get_settings
from app.core.database_unified import User
from app.core.security import create_access_token


pytestmark = pytest.mark.smoke


class TestAuthenticationFlow:
    """Test complete authentication lifecycle"""
    
    @pytest.mark.asyncio
    async def test_user_login_success(self, async_test_client, test_user):
        """
        Test successful login returns valid JWT token.
        This is the entry point for all authenticated operations.
        """
        # Prepare login data
        login_data = {
            "username": test_user.username,
            "password": "testpassword"  # From fixture
        }
        
        # Attempt login
        response = await async_test_client.post(
            "/api/v1/auth/login",
            json=login_data  # Send as JSON, not form data
        )
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        # Verify response structure
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 50  # JWT tokens are long
        
        # Decode and verify token claims using the security manager
        from app.core.security import security_manager
        token_payload = security_manager.verify_token(data["access_token"])
        
        # Verify required claims
        assert token_payload["sub"] == str(test_user.id)
        assert token_payload["user_id"] == str(test_user.id)
        assert token_payload["username"] == test_user.username
        assert token_payload["role"] == test_user.role
        
        # Verify standard JWT claims
        assert "exp" in token_payload  # Expiration
        assert "iat" in token_payload  # Issued at
        assert "jti" in token_payload  # JWT ID
        
        print(f"✓ User login successful for role: {test_user.role}")
        
        return data["access_token"]  # Return for use in other tests
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, async_test_client, test_user):
        """
        Test login fails with invalid credentials.
        Security: Must not leak information about valid usernames.
        """
        # Test wrong password
        response = await async_test_client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.username,
                "password": "wrongpassword"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "Incorrect username or password" in data["detail"]
        
        # Test non-existent user
        response = await async_test_client.post(
            "/api/v1/auth/login",
            data={
                "username": "nonexistent_user",
                "password": "anypassword"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 401
        data = response.json()
        # Same error message - don't reveal if username exists
        assert "Incorrect username or password" in data["detail"]
        
        print("✓ Invalid credentials properly rejected")
    
    @pytest.mark.asyncio
    async def test_token_validation_on_protected_endpoint(self, async_test_client, test_user):
        """
        Test that valid tokens grant access to protected endpoints.
        This verifies the auth middleware is working.
        """
        # First, login to get token
        login_response = await async_test_client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.username,
                "password": "testpassword"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        token = login_response.json()["access_token"]
        
        # Try accessing protected endpoint with token
        response = await async_test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        
        user_data = response.json()
        assert user_data["id"] == str(test_user.id)
        assert user_data["username"] == test_user.username
        assert user_data["email"] == test_user.email
        assert user_data["role"] == test_user.role
        assert user_data["is_active"] is True
        
        print("✓ Token validation successful on protected endpoint")
    
    @pytest.mark.asyncio
    async def test_access_without_token_fails(self, async_test_client):
        """
        Test that protected endpoints reject requests without tokens.
        This is critical for security.
        """
        # Try accessing protected endpoint without token
        response = await async_test_client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
        assert "Authorization header missing" in response.json()["detail"]
        
        # Try with invalid authorization header
        response = await async_test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "InvalidToken"}
        )
        
        assert response.status_code == 401
        
        print("✓ Unauthenticated access properly blocked")
    
    @pytest.mark.asyncio
    async def test_role_based_access_control(self, async_test_client, test_user, test_admin_user):
        """
        Test RBAC: Different roles have different access levels.
        Critical for PHI protection and compliance.
        """
        results = {}
        
        # Test regular user
        login_response = await async_test_client.post(
            "/api/v1/auth/login",
            data={"username": test_user.username, "password": "testpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        user_token = login_response.json()["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}
        
        # Test admin user
        login_response = await async_test_client.post(
            "/api/v1/auth/login", 
            data={"username": test_admin_user.username, "password": "adminpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        admin_token = login_response.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Test admin-only endpoint
        user_admin_response = await async_test_client.get(
            "/api/v1/auth/users",
            headers=user_headers
        )
        admin_admin_response = await async_test_client.get(
            "/api/v1/auth/users",
            headers=admin_headers
        )
        
        # Verify access control
        assert user_admin_response.status_code == 403  # Regular user forbidden
        assert admin_admin_response.status_code == 200  # Admin allowed
        
        print("✓ Role-based access control verified")
    
    @pytest.mark.asyncio
    async def test_token_expiration(self, async_test_client):
        """
        Test that tokens expire after configured time.
        Important for security - tokens should not be valid forever.
        """
        settings = get_settings()
        
        # Create a token with very short expiration for testing
        token_data = {
            "sub": "12345",
            "user_id": "12345",
            "username": "test_user",
            "role": "user",
            "email": "test@example.com"
        }
        
        # Create token that expires in 1 second using security manager
        from app.core.security import security_manager
        short_token = security_manager.create_access_token(
            data=token_data,
            expires_delta=timedelta(seconds=1)
        )
        
        # Wait for expiration
        await asyncio.sleep(2)
        
        # Token should now be expired
        response = await async_test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {short_token}"}
        )
        
        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]
        
        print("✓ Token expiration working correctly")
    
    @pytest.mark.asyncio
    async def test_token_validation_security(self, async_test_client):
        """
        Test token validation against common attacks.
        Ensures tokens can't be forged or tampered with.
        """
        settings = get_settings()
        
        # Test 1: Modified token (tampered payload)
        from app.core.security import security_manager
        valid_token = security_manager.create_access_token(
            data={
                "sub": "12345",
                "user_id": "12345", 
                "username": "test_user",
                "role": "user",
                "email": "test@example.com"
            }
        )
        
        # Tamper with token (change last character)
        tampered_token = valid_token[:-1] + ("a" if valid_token[-1] != "a" else "b")
        
        response = await async_test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {tampered_token}"}
        )
        
        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]
        
        # Test 2: Token signed with wrong key (using RS256 format but wrong key)
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        
        # Generate a different RSA key pair
        wrong_private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        wrong_private_pem = wrong_private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode()
        
        wrong_key_token = jwt.encode(
            {
                "sub": "99999",
                "user_id": "99999",
                "username": "hacker",
                "role": "ADMIN",  # Trying to escalate privileges
                "exp": datetime.utcnow() + timedelta(hours=1),
                "iss": "iris-api-system",
                "aud": "iris-api-clients"
            },
            wrong_private_pem,
            algorithm="RS256"
        )
        
        response = await async_test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {wrong_key_token}"}
        )
        
        assert response.status_code == 401
        
        # Test 3: Malformed token
        response = await async_test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer not.a.valid.jwt"}
        )
        
        assert response.status_code == 401
        
        print("✓ Token security validation passed")
    
    @pytest.mark.asyncio
    async def test_concurrent_sessions(self, async_test_client, test_user):
        """
        Test that multiple tokens can be valid simultaneously.
        Users might be logged in from multiple devices.
        """
        settings = get_settings()
        tokens = []
        
        # Create 3 login sessions
        for i in range(3):
            response = await async_test_client.post(
                "/api/v1/auth/login",
                data={
                    "username": test_user.username,
                    "password": "testpassword"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            tokens.append(response.json()["access_token"])
            await asyncio.sleep(0.1)  # Small delay to ensure different iat
        
        # Verify all tokens are valid
        for i, token in enumerate(tokens):
            response = await async_test_client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200, f"Token {i} should be valid"
            
            # Decode token to check unique jti using security manager
            from app.core.security import security_manager
            payload = security_manager.verify_token(token)
            assert "jti" in payload  # JWT ID should be unique
        
        # Verify JTIs are unique using security manager
        from app.core.security import security_manager
        jtis = [
            security_manager.verify_token(token)["jti"]
            for token in tokens
        ]
        assert len(set(jtis)) == 3, "Each token should have unique JTI"
        
        print("✓ Multiple concurrent sessions supported")


class TestAuthenticationEdgeCases:
    """Test edge cases and security scenarios"""
    
    @pytest.mark.asyncio
    async def test_sql_injection_in_login(self, async_test_client):
        """
        Test that login is safe from SQL injection.
        Critical security test.
        """
        injection_attempts = [
            "admin' OR '1'='1",
            "admin'; DROP TABLE users;--",
            "' OR 1=1--",
            "admin'/*",
        ]
        
        for attempt in injection_attempts:
            response = await async_test_client.post(
                "/api/v1/auth/login",
                data={
                    "username": attempt,
                    "password": "password"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            assert response.status_code == 401
            assert "Incorrect username or password" in response.json()["detail"]
        
        print("✓ SQL injection attempts properly blocked")
    
    @pytest.mark.asyncio
    async def test_rate_limiting_on_login(self, async_test_client):
        """
        Test that login endpoint has rate limiting.
        Prevents brute force attacks.
        """
        # Make multiple rapid login attempts
        responses = []
        for i in range(10):
            response = await async_test_client.post(
                "/api/v1/auth/login",
                data={
                    "username": f"attacker_{i}",
                    "password": "wrong"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            responses.append(response.status_code)
        
        # Check if rate limiting kicked in
        # Should see 429 (Too Many Requests) after several attempts
        if 429 in responses:
            print("✓ Rate limiting active on login endpoint")
        else:
            print("⚠️  No rate limiting detected - consider adding for production")


if __name__ == "__main__":
    """
    Run authentication smoke tests directly:
    python app/tests/smoke/test_auth_flow.py
    """
    print("🔐 Running authentication flow tests...")
    pytest.main([__file__, "-v", "--tb=short"])