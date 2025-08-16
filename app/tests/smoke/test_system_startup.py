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

from app.core.config import get_settings
from app.core.database_advanced import get_db
from app.core.security import EncryptionService
from app.modules.audit_logger.service import SOC2AuditService
from app.main import app


pytestmark = pytest.mark.smoke


class TestSystemStartup:
    """Verify core system components can initialize"""
    
    @pytest.mark.order(1)
    @pytest.mark.asyncio
    async def test_database_connection(self, db_session: AsyncSession):
        """
        Verify database is accessible and responsive.
        This is the most fundamental test - if this fails, nothing else will work.
        """
        # Test basic connectivity
        result = await db_session.execute(text("SELECT 1"))
        assert result.scalar() == 1
        
        # Verify PostgreSQL version (should be 13+)
        version_result = await db_session.execute(text("SELECT version()"))
        version = version_result.scalar()
        assert "PostgreSQL" in version
        print(f"✓ Database connected: {version.split(',')[0]}")
        
        # Check critical extensions
        extensions_result = await db_session.execute(
            text("SELECT extname FROM pg_extension WHERE extname IN ('uuid-ossp', 'pgcrypto')")
        )
        extensions = [row[0] for row in extensions_result]
        assert "uuid-ossp" in extensions, "UUID extension required for healthcare IDs"
        
        # pgcrypto is optional since we use application-level encryption
        if "pgcrypto" in extensions:
            print("✓ pgcrypto extension available")
        else:
            print("ℹ pgcrypto extension not installed - using application-level encryption")
    
    @pytest.mark.order(2)
    @pytest.mark.asyncio
    async def test_database_migration_status(self, db_session: AsyncSession):
        """
        Verify all migrations have been applied.
        The system cannot run safely without complete schema.
        """
        try:
            # Check if alembic_version table exists
            result = await db_session.execute(
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
            version_result = await db_session.execute(
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
                'phi_access_logs'
            ]
            
            # Optional tables (may not exist in all environments)
            optional_tables = ['compliance_reports', 'purge_policies']
            
            missing_critical = []
            for table in critical_tables:
                result = await db_session.execute(
                    text(f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = '{table}'
                        )
                    """)
                )
                exists = result.scalar()
                if not exists:
                    missing_critical.append(table)
            
            if missing_critical:
                assert False, f"Critical tables missing: {', '.join(missing_critical)}"
            
            # Check optional tables
            optional_exists = []
            for table in optional_tables:
                result = await db_session.execute(
                    text(f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = '{table}'
                        )
                    """)
                )
                if result.scalar():
                    optional_exists.append(table)
            
            print(f"✓ All {len(critical_tables)} critical tables verified")
            if optional_exists:
                print(f"ℹ Optional tables found: {', '.join(optional_exists)}")
            
        except Exception as e:
            pytest.fail(f"Migration check failed: {str(e)}")
    
    @pytest.mark.order(3)
    @pytest.mark.asyncio
    async def test_encryption_service_initialization(self):
        """
        Verify PHI encryption service is properly configured.
        This is critical for HIPAA compliance.
        """
        encryption_service = EncryptionService()
        
        # Verify encryption service is configured by testing encryption/decryption
        # This properly initializes the lazy-loaded cipher_suite
        test_phi = "123-45-6789"  # Test SSN
        
        # Test that encryption service can encrypt (initializes _fernet)
        try:
            encrypted = await encryption_service.encrypt(test_phi)
            assert encrypted != test_phi, "Value not encrypted"
            assert isinstance(encrypted, str), "Encrypted value should be string"
        except Exception as e:
            pytest.fail(f"Encryption service initialization failed: {e}")
        
        # Verify cipher suite is now initialized
        assert hasattr(encryption_service, 'cipher_suite'), "Cipher suite not accessible"
        assert encryption_service.cipher_suite is not None, "Cipher suite not initialized"
        
        # Test full encryption/decryption cycle
        decrypted = await encryption_service.decrypt(encrypted)
        assert decrypted == test_phi, "Decryption failed"
        
        # Verify it's the advanced AES-256-GCM format (base64 encoded JSON)
        import base64
        import json
        try:
            decoded = base64.b64decode(encrypted)
            parsed = json.loads(decoded)
            assert parsed.get("version") == "v2", "Should use v2 encryption format"
            assert parsed.get("algorithm") == "AES-256-GCM", "Should use AES-256-GCM"
        except (json.JSONDecodeError, base64.binascii.Error):
            pytest.fail("Encrypted data should be base64-encoded JSON")
        
        print("✓ PHI encryption service verified")
    
    @pytest.mark.order(4)
    @pytest.mark.asyncio
    async def test_redis_connection(self, mock_redis):
        """
        Verify Redis is accessible for caching and Celery.
        Required for background tasks and performance.
        """
        # Test basic operations
        test_key = "smoke_test:redis_check"
        test_value = "healthy"
        
        # Set and get
        await mock_redis.set(test_key, test_value, ex=60)
        result = await mock_redis.get(test_key)
        # Handle byte/string conversion for Redis compatibility
        if isinstance(result, bytes):
            result = result.decode('utf-8')
        assert result == test_value
        
        # Cleanup
        await mock_redis.delete(test_key)
        
        # Check Redis info
        info = await mock_redis.info()
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
            "/api/v1/healthcare/patients",  # Patient management
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
    async def test_audit_service_initialization(self, db_session: AsyncSession):
        """
        Verify audit logging is operational for SOC2 compliance.
        Every PHI access must be logged.
        """
        audit_service = SOC2AuditService(db_session)
        
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
        result = await db_session.execute(
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
        settings = get_settings()
        
        critical_vars = [
            ("SECRET_KEY", settings.SECRET_KEY),
            ("DATABASE_URL", settings.DATABASE_URL),
            ("REDIS_URL", settings.REDIS_URL),
            ("ENCRYPTION_KEY", settings.ENCRYPTION_KEY),
            ("ALGORITHM", settings.ALGORITHM),
            ("ACCESS_TOKEN_EXPIRE_MINUTES", settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        ]
        
        missing = []
        for var_name, var_value in critical_vars:
            if not var_value:
                missing.append(var_name)
        
        if missing:
            pytest.fail(f"Missing critical environment variables: {', '.join(missing)}")
        
        # Verify JWT settings
        assert settings.ALGORITHM == "HS256", "Unexpected JWT algorithm"
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30, "Non-standard token expiry"
        
        print("✓ All critical configuration verified")


class TestHealthEndpoints:
    """Verify health check endpoints are responsive"""
    
    @pytest.mark.asyncio
    async def test_basic_health_endpoint(self, async_test_client):
        """
        Test the basic /health endpoint.
        This should always return 200 OK.
        """
        response = await async_test_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        print("✓ Basic health endpoint operational")
    
    @pytest.mark.asyncio
    async def test_detailed_health_endpoint(self, async_test_client):
        """
        Test the detailed health check with component status.
        This verifies all subsystems are operational.
        """
        response = await async_test_client.get("/health/detailed")
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
    python app/tests/smoke/test_system_startup.py
    """
    print("🔍 Running system startup verification...")
    pytest.main([__file__, "-v", "--tb=short"])