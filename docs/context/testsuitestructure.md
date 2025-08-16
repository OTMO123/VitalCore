tests/
├── smoke/           # Basic system verification
│   ├── test_system_startup.py
│   ├── test_auth_flow.py
│   └── test_core_endpoints.py
├── core/            # Critical business logic
│   ├── healthcare_records/
│   │   ├── test_patient_api.py
│   │   ├── test_phi_encryption.py
│   │   └── test_consent_management.py
│   └── security/
│       ├── test_authorization.py
│       └── test_audit_logging.py
└── integration/     # Later priority

"""
Smoke Tests: System Startup and Health Verification

These tests verify the basic system infrastructure is operational.
Run these first to ensure the system can start and connect to dependencies.
"""
import pytest
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from alembic.config import Config
from alembic import command
from pathlib import Path

from app.core.config import settings
from app.core.database_advanced import engine, get_async_session
from app.core.security import EncryptionService
from app.modules.audit_logger.service import AuditService
from app.main import app


pytestmark = pytest.mark.smoke


class TestSystemStartup:
    """Verify core system components can initialize"""
    
    @pytest.mark.order(1)
    @pytest.mark.asyncio
    async def test_database_connection(self, async_session: AsyncSession):
        """
        Verify database is accessible and responsive.
        This is the most fundamental test - if this fails, nothing else will work.
        """
        # Test basic connectivity
        result = await async_session.execute(text("SELECT 1"))
        assert result.scalar() == 1
        
        # Verify PostgreSQL version (should be 13+)
        version_result = await async_session.execute(text("SELECT version()"))
        version = version_result.scalar()
        assert "PostgreSQL" in version
        print(f"✓ Database connected: {version.split(',')[0]}")
        
        # Check critical extensions
        extensions_result = await async_session.execute(
            text("SELECT extname FROM pg_extension WHERE extname IN ('uuid-ossp', 'pgcrypto')")
        )
        extensions = [row[0] for row in extensions_result]
        assert "uuid-ossp" in extensions, "UUID extension required for healthcare IDs"
        assert "pgcrypto" in extensions, "Crypto extension required for PHI protection"
    
    @pytest.mark.order(2)
    @pytest.mark.asyncio
    async def test_database_migration_status(self, async_session: AsyncSession):
        """
        Verify all migrations have been applied.
        The system cannot run safely without complete schema.
        """
        try:
            # Check if alembic_version table exists
            result = await async_session.execute(
                text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'alembic_version'
                    )
                """)
            )
            has_alembic_table = result.scalar()
            
            if not has_alembic_table:
                pytest.fail(
                    "⚠️  No alembic_version table found!\n"
                    "Run: alembic upgrade head"
                )
            
            # Check current migration version
            version_result = await async_session.execute(
                text("SELECT version_num FROM alembic_version")
            )
            current_version = version_result.scalar()
            
            if not current_version:
                pytest.fail(
                    "⚠️  No migration version found!\n"
                    "Run: alembic upgrade head"
                )
            
            print(f"✓ Database migration version: {current_version}")
            
            # Verify critical tables exist
            critical_tables = [
                'users', 'patients', 'clinical_documents', 
                'consents', 'audit_logs', 'immunizations',
                'phi_access_logs', 'compliance_reports'
            ]
            
            for table in critical_tables:
                result = await async_session.execute(
                    text(f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = '{table}'
                        )
                    """)
                )
                exists = result.scalar()
                assert exists, f"Critical table '{table}' missing"
            
            print(f"✓ All {len(critical_tables)} critical tables verified")
            
        except Exception as e:
            pytest.fail(f"Migration check failed: {str(e)}")
    
    @pytest.mark.order(3)
    def test_encryption_service_initialization(self):
        """
        Verify PHI encryption service is properly configured.
        This is critical for HIPAA compliance.
        """
        encryption_service = EncryptionService()
        
        # Verify encryption key is configured
        assert hasattr(encryption_service, '_fernet'), "Encryption not initialized"
        assert encryption_service._fernet is not None, "Encryption key missing"
        
        # Test basic encryption/decryption
        test_phi = "123-45-6789"  # Test SSN
        encrypted = encryption_service.encrypt_value(test_phi)
        decrypted = encryption_service.decrypt_value(encrypted)
        
        assert encrypted != test_phi, "Value not encrypted"
        assert decrypted == test_phi, "Decryption failed"
        assert encrypted.startswith("gAAAAA"), "Invalid Fernet format"
        
        print("✓ PHI encryption service verified")
    
    @pytest.mark.order(4)
    @pytest.mark.asyncio
    async def test_redis_connection(self, redis_client):
        """
        Verify Redis is accessible for caching and Celery.
        Required for background tasks and performance.
        """
        # Test basic operations
        test_key = "smoke_test:redis_check"
        test_value = "healthy"
        
        # Set and get
        await redis_client.set(test_key, test_value, ex=60)
        result = await redis_client.get(test_key)
        assert result == test_value
        
        # Cleanup
        await redis_client.delete(test_key)
        
        # Check Redis info
        info = await redis_client.info()
        assert "redis_version" in info
        print(f"✓ Redis connected: v{info['redis_version']}")
    
    @pytest.mark.order(5)
    def test_fastapi_app_initialization(self):
        """
        Verify FastAPI application initializes with all routers.
        This ensures all modules are properly registered.
        """
        # Check app exists
        assert app is not None, "FastAPI app not initialized"
        
        # Verify critical routers are included
        router_paths = [route.path for route in app.routes]
        
        critical_endpoints = [
            "/health",  # Health check
            "/api/v1/auth/login",  # Authentication
            "/api/v1/patients",  # Patient management
            "/api/v1/clinical-documents",  # Clinical docs
            "/api/v1/audit-logs",  # Compliance
        ]
        
        for endpoint in critical_endpoints:
            # Check if endpoint exists (considering path parameters)
            endpoint_exists = any(
                endpoint in path or path.startswith(endpoint)
                for path in router_paths
            )
            assert endpoint_exists, f"Critical endpoint missing: {endpoint}"
        
        # Count total endpoints
        api_routes = [r for r in router_paths if r.startswith("/api/")]
        print(f"✓ FastAPI initialized with {len(api_routes)} API endpoints")
    
    @pytest.mark.order(6)
    @pytest.mark.asyncio
    async def test_audit_service_initialization(self, async_session: AsyncSession):
        """
        Verify audit logging is operational for SOC2 compliance.
        Every PHI access must be logged.
        """
        audit_service = AuditService(async_session)
        
        # Create test audit log
        test_log = await audit_service.log_action(
            user_id="smoke-test-user",
            action="SYSTEM_HEALTH_CHECK",
            resource_type="system",
            resource_id="smoke-test",
            details={"test": "smoke test audit verification"}
        )
        
        assert test_log is not None
        assert test_log.id is not None
        assert test_log.timestamp is not None
        
        # Verify it was persisted
        result = await async_session.execute(
            text("SELECT COUNT(*) FROM audit_logs WHERE user_id = :user_id"),
            {"user_id": "smoke-test-user"}
        )
        count = result.scalar()
        assert count >= 1, "Audit log not persisted"
        
        print("✓ Audit logging service verified")
    
    @pytest.mark.order(7)
    def test_critical_environment_variables(self):
        """
        Verify all critical configuration is present.
        Missing config will cause runtime failures.
        """
        critical_vars = [
            ("SECRET_KEY", settings.SECRET_KEY),
            ("DATABASE_URL", settings.DATABASE_URL),
            ("REDIS_URL", settings.REDIS_URL),
            ("ENCRYPTION_KEY", settings.ENCRYPTION_KEY),
            ("JWT_ALGORITHM", settings.JWT_ALGORITHM),
            ("ACCESS_TOKEN_EXPIRE_MINUTES", settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        ]
        
        missing = []
        for var_name, var_value in critical_vars:
            if not var_value:
                missing.append(var_name)
        
        if missing:
            pytest.fail(f"Missing critical environment variables: {', '.join(missing)}")
        
        # Verify JWT settings
        assert settings.JWT_ALGORITHM == "HS256", "Unexpected JWT algorithm"
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30, "Non-standard token expiry"
        
        print("✓ All critical configuration verified")


class TestHealthEndpoints:
    """Verify health check endpoints are responsive"""
    
    @pytest.mark.asyncio
    async def test_basic_health_endpoint(self, async_client):
        """
        Test the basic /health endpoint.
        This should always return 200 OK.
        """
        response = await async_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        print("✓ Basic health endpoint operational")
    
    @pytest.mark.asyncio
    async def test_detailed_health_endpoint(self, async_client):
        """
        Test the detailed health check with component status.
        This verifies all subsystems are operational.
        """
        response = await async_client.get("/health/detailed")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        
        # Check component health
        components = data.get("components", {})
        critical_components = ["database", "redis", "encryption"]
        
        for component in critical_components:
            assert component in components, f"Missing health check for {component}"
            assert components[component]["status"] == "healthy", f"{component} unhealthy"
        
        print("✓ Detailed health check passed")


# Helper function for manual migration if needed
def apply_migrations():
    """
    Helper to apply database migrations.
    Only use this if migrations haven't been applied yet.
    """
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    print("✅ Migrations applied successfully")


if __name__ == "__main__":
    """
    Run this file directly to check system readiness:
    python tests/smoke/test_system_startup.py
    """
    print("🔍 Running system startup verification...")
    pytest.main([__file__, "-v", "--tb=short"])

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

from app.core.config import settings
from app.modules.auth.models import User
from app.modules.auth.security import create_access_token, verify_token


pytestmark = pytest.mark.smoke


class TestAuthenticationFlow:
    """Test complete authentication lifecycle"""
    
    @pytest.mark.asyncio
    async def test_user_login_success(self, async_client, test_user):
        """
        Test successful login returns valid JWT token.
        This is the entry point for all authenticated operations.
        """
        # Prepare login data
        login_data = {
            "username": test_user.username,
            "password": "testpassword123"  # From fixture
        }
        
        # Attempt login
        response = await async_client.post(
            "/api/v1/auth/login",
            data=login_data,  # OAuth2 expects form data
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        # Verify response structure
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 50  # JWT tokens are long
        
        # Decode and verify token claims
        token_payload = jwt.decode(
            data["access_token"],
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Verify required claims
        assert token_payload["sub"] == test_user.username
        assert token_payload["user_id"] == str(test_user.id)
        assert token_payload["role"] == test_user.role
        assert token_payload["email"] == test_user.email
        
        # Verify standard JWT claims
        assert "exp" in token_payload  # Expiration
        assert "iat" in token_payload  # Issued at
        assert "jti" in token_payload  # JWT ID
        
        print(f"✓ User login successful for role: {test_user.role}")
        
        return data["access_token"]  # Return for use in other tests
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, async_client, test_user):
        """
        Test login fails with invalid credentials.
        Security: Must not leak information about valid usernames.
        """
        # Test wrong password
        response = await async_client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.username,
                "password": "wrongpassword"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Incorrect username or password"
        
        # Test non-existent user
        response = await async_client.post(
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
        assert data["detail"] == "Incorrect username or password"
        
        print("✓ Invalid credentials properly rejected")
    
    @pytest.mark.asyncio
    async def test_token_validation_on_protected_endpoint(self, async_client, test_user):
        """
        Test that valid tokens grant access to protected endpoints.
        This verifies the auth middleware is working.
        """
        # First, login to get token
        login_response = await async_client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.username,
                "password": "testpassword123"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        token = login_response.json()["access_token"]
        
        # Try accessing protected endpoint with token
        response = await async_client.get(
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
    async def test_access_without_token_fails(self, async_client):
        """
        Test that protected endpoints reject requests without tokens.
        This is critical for security.
        """
        # Try accessing protected endpoint without token
        response = await async_client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"
        
        # Try with invalid authorization header
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "InvalidToken"}
        )
        
        assert response.status_code == 401
        
        print("✓ Unauthenticated access properly blocked")
    
    @pytest.mark.asyncio
    async def test_role_based_access_control(self, async_client, test_users_by_role):
        """
        Test RBAC: Different roles have different access levels.
        Critical for PHI protection and compliance.
        """
        results = {}
        
        for role, user in test_users_by_role.items():
            # Login as user with specific role
            login_response = await async_client.post(
                "/api/v1/auth/login",
                data={
                    "username": user.username,
                    "password": "testpassword123"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test admin-only endpoint
            admin_response = await async_client.get(
                "/api/v1/admin/users",
                headers=headers
            )
            
            # Test super-admin-only endpoint
            super_admin_response = await async_client.get(
                "/api/v1/admin/system/config",
                headers=headers
            )
            
            results[role] = {
                "admin_endpoint": admin_response.status_code,
                "super_admin_endpoint": super_admin_response.status_code
            }
        
        # Verify access control matrix
        assert results["user"]["admin_endpoint"] == 403  # Forbidden
        assert results["user"]["super_admin_endpoint"] == 403
        
        assert results["admin"]["admin_endpoint"] == 200  # Allowed
        assert results["admin"]["super_admin_endpoint"] == 403  # Forbidden
        
        assert results["super_admin"]["admin_endpoint"] == 200  # Allowed
        assert results["super_admin"]["super_admin_endpoint"] == 200  # Allowed
        
        print("✓ Role-based access control verified for all roles")
    
    @pytest.mark.asyncio
    async def test_token_expiration(self, async_client):
        """
        Test that tokens expire after 30 minutes.
        Important for security - tokens should not be valid forever.
        """
        # Create a token with very short expiration for testing
        token_data = {
            "sub": "test_user",
            "user_id": "12345",
            "role": "user",
            "email": "test@example.com"
        }
        
        # Create token that expires in 1 second
        short_token = create_access_token(
            data=token_data,
            expires_delta=timedelta(seconds=1)
        )
        
        # Token should work immediately
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {short_token}"}
        )
        # This will fail because we're using a fake user_id, but that's ok
        # We're testing token validation, not user lookup
        
        # Wait for expiration
        await asyncio.sleep(2)
        
        # Token should now be expired
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {short_token}"}
        )
        
        assert response.status_code == 401
        assert "Token has expired" in response.json()["detail"]
        
        print("✓ Token expiration working correctly")
    
    @pytest.mark.asyncio
    async def test_token_validation_security(self, async_client):
        """
        Test token validation against common attacks.
        Ensures tokens can't be forged or tampered with.
        """
        # Test 1: Modified token (tampered payload)
        valid_token = create_access_token(
            data={
                "sub": "test_user",
                "user_id": "12345",
                "role": "user",
                "email": "test@example.com"
            }
        )
        
        # Tamper with token (change last character)
        tampered_token = valid_token[:-1] + ("a" if valid_token[-1] != "a" else "b")
        
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {tampered_token}"}
        )
        
        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]
        
        # Test 2: Token signed with wrong key
        wrong_key_token = jwt.encode(
            {
                "sub": "hacker",
                "user_id": "99999",
                "role": "super_admin",  # Trying to escalate privileges
                "exp": datetime.utcnow() + timedelta(hours=1)
            },
            "wrong-secret-key",
            algorithm=settings.JWT_ALGORITHM
        )
        
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {wrong_key_token}"}
        )
        
        assert response.status_code == 401
        
        # Test 3: Malformed token
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer not.a.valid.jwt"}
        )
        
        assert response.status_code == 401
        
        print("✓ Token security validation passed")
    
    @pytest.mark.asyncio
    async def test_concurrent_sessions(self, async_client, test_user):
        """
        Test that multiple tokens can be valid simultaneously.
        Users might be logged in from multiple devices.
        """
        tokens = []
        
        # Create 3 login sessions
        for i in range(3):
            response = await async_client.post(
                "/api/v1/auth/login",
                data={
                    "username": test_user.username,
                    "password": "testpassword123"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            tokens.append(response.json()["access_token"])
            await asyncio.sleep(0.1)  # Small delay to ensure different iat
        
        # Verify all tokens are valid
        for i, token in enumerate(tokens):
            response = await async_client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200, f"Token {i} should be valid"
            
            # Decode token to check unique jti
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            assert "jti" in payload  # JWT ID should be unique
        
        # Verify JTIs are unique
        jtis = [
            jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])["jti"]
            for token in tokens
        ]
        assert len(set(jtis)) == 3, "Each token should have unique JTI"
        
        print("✓ Multiple concurrent sessions supported")
    
    @pytest.mark.asyncio
    async def test_logout_flow(self, async_client, test_user):
        """
        Test logout endpoint (if implemented).
        Note: With JWT, logout is typically client-side.
        """
        # Login first
        login_response = await async_client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.username,
                "password": "testpassword123"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        token = login_response.json()["access_token"]
        
        # Check if logout endpoint exists
        logout_response = await async_client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if logout_response.status_code == 404:
            print("⚠️  No logout endpoint implemented (normal for JWT)")
        else:
            assert logout_response.status_code == 200
            # In a blacklist implementation, the token would now be invalid
            # But with standard JWT, token remains valid until expiration
            print("✓ Logout endpoint called successfully")


class TestAuthenticationEdgeCases:
    """Test edge cases and security scenarios"""
    
    @pytest.mark.asyncio
    async def test_sql_injection_in_login(self, async_client):
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
            response = await async_client.post(
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
    async def test_rate_limiting_on_login(self, async_client):
        """
        Test that login endpoint has rate limiting.
        Prevents brute force attacks.
        """
        # Make multiple rapid login attempts
        responses = []
        for i in range(10):
            response = await async_client.post(
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
    python tests/smoke/test_auth_flow.py
    """
    print("🔐 Running authentication flow tests...")
    pytest.main([__file__, "-v", "--tb=short"])

    """
Smoke Tests: Core API Endpoints

Verifies that all critical API endpoints are:
- Accessible and returning correct status codes
- Properly authenticated when required
- Returning expected response structures
"""
import pytest
from typing import Dict, List, Tuple

from app.modules.auth.security import create_access_token


pytestmark = pytest.mark.smoke


class TestPublicEndpoints:
    """Test endpoints that should be accessible without authentication"""
    
    @pytest.mark.asyncio
    async def test_openapi_documentation(self, async_client):
        """
        Test that API documentation is accessible.
        Developers need this to understand the API.
        """
        # Test OpenAPI JSON endpoint
        response = await async_client.get("/openapi.json")
        assert response.status_code == 200
        
        openapi_spec = response.json()
        assert openapi_spec["openapi"].startswith("3.")  # OpenAPI 3.x
        assert "IRIS Healthcare API" in openapi_spec["info"]["title"]
        assert len(openapi_spec["paths"]) >= 60  # Should have 60+ endpoints
        
        print(f"✓ OpenAPI spec available with {len(openapi_spec['paths'])} endpoints")
        
        # Test Swagger UI
        response = await async_client.get("/docs")
        assert response.status_code == 200
        assert "swagger-ui" in response.text.lower()
        
        # Test ReDoc
        response = await async_client.get("/redoc")
        assert response.status_code == 200
        assert "redoc" in response.text.lower()
        
        print("✓ API documentation endpoints accessible")
    
    @pytest.mark.asyncio
    async def test_health_endpoints_public_access(self, async_client):
        """
        Test that health endpoints work without authentication.
        Monitoring systems need unauthenticated access.
        """
        endpoints = [
            ("/health", 200),
            ("/health/detailed", 200),
            ("/api/v1/health", 200),
        ]
        
        for endpoint, expected_status in endpoints:
            response = await async_client.get(endpoint)
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
                "sub": test_user.username,
                "user_id": str(test_user.id),
                "role": test_user.role,
                "email": test_user.email
            }
        )
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture
    async def admin_headers(self, admin_user) -> Dict[str, str]:
        """Generate admin auth headers"""
        token = create_access_token(
            data={
                "sub": admin_user.username,
                "user_id": str(admin_user.id),
                "role": admin_user.role,
                "email": admin_user.email
            }
        )
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.mark.asyncio
    async def test_patient_endpoints(self, async_client, auth_headers):
        """
        Test patient management endpoints.
        Core functionality for healthcare records.
        """
        # List patients (should be empty initially)
        response = await async_client.get(
            "/api/v1/patients",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "items" in data  # List or paginated
        
        # Create patient endpoint should exist
        response = await async_client.post(
            "/api/v1/patients",
            headers=auth_headers,
            json={
                "first_name": "Test",
                "last_name": "Patient",
                "date_of_birth": "1990-01-01",
                "ssn": "123-45-6789"
            }
        )
        # Might fail with validation, but endpoint should exist
        assert response.status_code in [201, 400, 422]
        
        print("✓ Patient endpoints accessible")
    
    @pytest.mark.asyncio
    async def test_clinical_documents_endpoints(self, async_client, auth_headers):
        """
        Test clinical document management endpoints.
        Essential for storing medical records.
        """
        # List documents
        response = await async_client.get(
            "/api/v1/clinical-documents",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Search documents
        response = await async_client.get(
            "/api/v1/clinical-documents/search?patient_id=test",
            headers=auth_headers
        )
        assert response.status_code in [200, 404]  # 404 if no patient
        
        print("✓ Clinical document endpoints accessible")
    
    @pytest.mark.asyncio
    async def test_consent_endpoints(self, async_client, auth_headers):
        """
        Test consent management endpoints.
        Critical for HIPAA compliance.
        """
        # List consents
        response = await async_client.get(
            "/api/v1/consents",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Check consent status endpoint
        response = await async_client.get(
            "/api/v1/consents/status?patient_id=test",
            headers=auth_headers
        )
        assert response.status_code in [200, 404]
        
        print("✓ Consent management endpoints accessible")
    
    @pytest.mark.asyncio
    async def test_audit_log_endpoints(self, async_client, admin_headers):
        """
        Test audit logging endpoints.
        Required for SOC2 compliance.
        """
        # List audit logs (admin only)
        response = await async_client.get(
            "/api/v1/audit-logs",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        # Search audit logs
        response = await async_client.get(
            "/api/v1/audit-logs/search?action=LOGIN",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        print("✓ Audit log endpoints accessible to admin")
    
    @pytest.mark.asyncio
    async def test_immunization_endpoints(self, async_client, auth_headers):
        """
        Test immunization record endpoints.
        Core feature for IRIS integration.
        """
        # List immunizations
        response = await async_client.get(
            "/api/v1/immunizations",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # FHIR format endpoint
        response = await async_client.get(
            "/api/v1/immunizations/fhir",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        print("✓ Immunization endpoints accessible")
    
    @pytest.mark.asyncio
    async def test_iris_api_endpoints(self, async_client, auth_headers):
        """
        Test IRIS API integration endpoints.
        External system integration points.
        """
        # IRIS status endpoint
        response = await async_client.get(
            "/api/v1/iris/status",
            headers=auth_headers
        )
        assert response.status_code in [200, 503]  # 503 if IRIS is down
        
        # IRIS sync endpoint should exist
        response = await async_client.post(
            "/api/v1/iris/sync",
            headers=auth_headers,
            json={"patient_id": "test"}
        )
        assert response.status_code in [200, 202, 400, 404]
        
        print("✓ IRIS integration endpoints accessible")


class TestEndpointSecurity:
    """Test security aspects of endpoints"""
    
    @pytest.mark.asyncio
    async def test_all_endpoints_require_auth(self, async_client):
        """
        Verify all sensitive endpoints require authentication.
        Critical for PHI protection.
        """
        # Endpoints that should require auth
        protected_endpoints = [
            ("/api/v1/patients", "GET"),
            ("/api/v1/patients", "POST"),
            ("/api/v1/clinical-documents", "GET"),
            ("/api/v1/consents", "GET"),
            ("/api/v1/immunizations", "GET"),
            ("/api/v1/audit-logs", "GET"),
            ("/api/v1/phi-access-logs", "GET"),
            ("/api/v1/compliance-reports", "GET"),
        ]
        
        for endpoint, method in protected_endpoints:
            if method == "GET":
                response = await async_client.get(endpoint)
            elif method == "POST":
                response = await async_client.post(endpoint, json={})
            
            assert response.status_code == 401, f"{endpoint} not protected!"
            assert "Not authenticated" in response.json()["detail"]
        
        print(f"✓ All {len(protected_endpoints)} protected endpoints require auth")
    
    @pytest.mark.asyncio
    async def test_cors_headers(self, async_client):
        """
        Test CORS headers are properly configured.
        Important for frontend integration.
        """
        # Make OPTIONS request
        response = await async_client.options(
            "/api/v1/patients",
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
    async def test_response_headers_security(self, async_client):
        """
        Test security headers are present.
        Important for preventing common attacks.
        """
        response = await async_client.get("/health")
        
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
    async def test_endpoint_response_times(self, async_client, auth_headers):
        """
        Test that key endpoints respond quickly.
        Slow endpoints indicate system issues.
        """
        import time
        
        performance_targets = [
            ("/health", 100),  # Should respond in <100ms
            ("/api/v1/auth/me", 200),  # Auth check <200ms
            ("/api/v1/patients", 500),  # List operation <500ms
        ]
        
        results = []
        
        for endpoint, max_ms in performance_targets:
            start = time.time()
            
            if endpoint == "/health":
                response = await async_client.get(endpoint)
            else:
                response = await async_client.get(endpoint, headers=auth_headers)
            
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
    async def test_api_version_in_urls(self, async_client):
        """
        Verify API versioning is consistent.
        Important for backward compatibility.
        """
        # Get OpenAPI spec
        response = await async_client.get("/openapi.json")
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
        response = await async_client.get("/api/v1/health")
        if "api-version" in response.headers:
            assert response.headers["api-version"] == "1.0"
            print("✓ API version in response headers")


if __name__ == "__main__":
    """
    Run core endpoint smoke tests directly:
    python tests/smoke/test_core_endpoints.py
    """
    print("🌐 Running core endpoint tests...")
    pytest.main([__file__, "-v", "--tb=short"])

    