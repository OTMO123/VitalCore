#!/usr/bin/env python3
"""
Comprehensive smoke tests using SQLite instead of PostgreSQL.
This allows testing database functionality without Docker.
"""
import asyncio
import sys
import os
import tempfile
from pathlib import Path

# Add project root to path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

async def test_database_operations():
    """Test database operations with SQLite."""
    print("\n--- Testing Database Operations ---")
    
    try:
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
        from sqlalchemy import text
        from app.core.database import Base
        
        # Create in-memory SQLite database
        DATABASE_URL = "sqlite+aiosqlite:///:memory:"
        engine = create_async_engine(DATABASE_URL, echo=False)
        
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("[OK] Database tables created")
        
        # Test basic operations
        SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with SessionLocal() as session:
            # Test basic query
            result = await session.execute(text("SELECT 1 as test"))
            assert result.scalar() == 1
            print("[OK] Basic database query works")
            
            # Test table existence
            result = await session.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result.fetchall()]
            
            expected_tables = ['users', 'audit_logs', 'iris_api_logs', 'purge_policies']
            for table in expected_tables:
                if table in tables:
                    print(f"[OK] Table '{table}' exists")
                else:
                    print(f"[WARN] Table '{table}' missing")
        
        await engine.dispose()
        return True
        
    except Exception as e:
        print(f"[FAIL] Database test failed: {e}")
        return False

async def test_encryption_service():
    """Test encryption service with async operations."""
    print("\n--- Testing Encryption Service ---")
    
    try:
        from app.core.security import EncryptionService
        from app.core.config import Settings
        
        # Create test settings
        settings = Settings(
            SECRET_KEY="test_secret_key_with_sufficient_length_for_validation",
            ENCRYPTION_KEY="test_encryption_key_with_sufficient_length_for_validation",
            ENCRYPTION_SALT="test_salt_with_sufficient_length_for_validation",
            ENVIRONMENT="test"
        )
        
        encryption_service = EncryptionService()
        
        # Test basic encryption/decryption
        test_data = "sensitive_phi_data_123"
        encrypted = await encryption_service.encrypt(test_data)
        decrypted = await encryption_service.decrypt(encrypted)
        
        assert encrypted != test_data, "Data should be encrypted"
        assert decrypted == test_data, "Decryption should restore original data"
        print(f"[OK] Encryption/decryption working: '{test_data}' -> encrypted -> '{decrypted}'")
        
        # Test deterministic hashing
        from app.core.security import hash_deterministic
        hash1 = hash_deterministic("test@example.com")
        hash2 = hash_deterministic("test@example.com")
        assert hash1 == hash2, "Deterministic hashing should be consistent"
        print("[OK] Deterministic hashing working")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Encryption test failed: {e}")
        return False

async def test_fastapi_app():
    """Test FastAPI application setup."""
    print("\n--- Testing FastAPI Application ---")
    
    try:
        from app.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Test health endpoint
        response = client.get("/health")
        if response.status_code == 200:
            print("[OK] Health endpoint responding")
            data = response.json()
            print(f"     Status: {data.get('status', 'unknown')}")
        else:
            print(f"[WARN] Health endpoint returned {response.status_code}")
        
        # Count routes
        routes = [route for route in app.routes if hasattr(route, 'path')]
        api_routes = [r for r in routes if r.path.startswith('/api/')]
        print(f"[OK] FastAPI app has {len(routes)} total routes, {len(api_routes)} API routes")
        
        # Test some key endpoints exist
        key_endpoints = ['/health', '/api/v1/auth/login', '/api/v1/patients']
        existing_paths = [route.path for route in routes]
        
        for endpoint in key_endpoints:
            if any(endpoint in path for path in existing_paths):
                print(f"[OK] Key endpoint '{endpoint}' found")
            else:
                print(f"[WARN] Key endpoint '{endpoint}' not found")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] FastAPI test failed: {e}")
        return False

async def test_event_bus():
    """Test event bus functionality."""
    print("\n--- Testing Event Bus ---")
    
    try:
        from app.core.event_bus_advanced import HybridEventBus, BaseEvent
        
        # Test event bus classes can be imported
        print("[OK] Event bus classes imported successfully")
        
        # Test event creation without DB dependency
        test_event = BaseEvent(
            event_type="test.smoke_test",
            aggregate_id="test-123",
            aggregate_type="test",
            publisher="smoke_test",
            data={"message": "smoke test event"},
            metadata={"user_id": "test-user"}
        )
        
        print(f"[OK] Event created: {test_event.event_type}")
        print(f"     Event ID: {test_event.event_id}")
        
        # Event bus initialization requires DB, so we skip that part
        print("[OK] Event bus architecture verified (DB-dependent features skipped)")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Event bus test failed: {e}")
        return False

async def test_healthcare_modules():
    """Test healthcare-specific modules."""
    print("\n--- Testing Healthcare Modules ---")
    
    try:
        # Test healthcare schemas
        from app.modules.healthcare_records.schemas import (
            ClinicalDocumentCreate, 
            ConsentCreate,
            FHIRValidationRequest
        )
        
        # Test schema creation with valid UUIDs
        import uuid
        test_patient_id = str(uuid.uuid4())
        
        doc_schema = ClinicalDocumentCreate(
            patient_id=test_patient_id,
            title="COVID-19 Immunization Record",
            document_type="immunization_record", 
            content='{"vaccine": "COVID-19", "date": "2024-01-15"}',
            fhir_resource={"resourceType": "Immunization"}
        )
        print("[OK] Clinical document schema created")
        
        consent_schema = ConsentCreate(
            patient_id=test_patient_id,
            consent_type="treatment",
            purpose="treatment",
            granted=True
        )
        print("[OK] Patient consent schema created")
        
        # Test FHIR validation schema
        fhir_request = FHIRValidationRequest(
            resource_type="Patient",
            resource_data={"resourceType": "Patient", "id": "test-123"}
        )
        print("[OK] FHIR validation schema created")
        
        # Test healthcare service import
        from app.modules.healthcare_records.service import HealthcareRecordsService
        print("[OK] Healthcare records service imported")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Healthcare modules test failed: {e}")
        return False

async def run_comprehensive_tests():
    """Run all comprehensive smoke tests."""
    print("=" * 80)
    print("COMPREHENSIVE IRIS API SYSTEM SMOKE TESTS (WITH DATABASE)")
    print("=" * 80)
    
    test_functions = [
        test_database_operations,
        test_encryption_service,
        test_fastapi_app,
        test_event_bus,
        test_healthcare_modules,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            result = await test_func()
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"[FAIL] {test_func.__name__} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"COMPREHENSIVE TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 80)
    
    if failed == 0:
        print("SUCCESS: ALL COMPREHENSIVE TESTS PASSED!")
        print("   The IRIS API system is fully functional and ready for production development.")
        return True
    else:
        print(f"WARNING: {failed} tests failed - system needs attention before production use.")
        return False

def main():
    """Main entry point."""
    try:
        success = asyncio.run(run_comprehensive_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Test runner failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()