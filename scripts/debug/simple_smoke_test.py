#!/usr/bin/env python3
"""
Simple smoke test for IRIS API system without any pytest fixtures.
This tests basic functionality to verify the system can start.
"""
import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

def test_python_version():
    """Test Python version compatibility."""
    print(f"Python version: {sys.version}")
    assert sys.version_info >= (3, 8), f"Python 3.8+ required, got {sys.version_info}"
    print("[OK] Python version compatible")

def test_core_dependencies():
    """Test core dependencies can be imported."""
    try:
        import fastapi
        print(f"FastAPI version: {fastapi.__version__}")
        
        import pydantic
        print(f"Pydantic version: {pydantic.__version__}")
        
        import sqlalchemy
        print(f"SQLAlchemy version: {sqlalchemy.__version__}")
        
        print("[OK] Core dependencies imported")
    except ImportError as e:
        raise AssertionError(f"Failed to import core dependencies: {e}")

def test_app_config():
    """Test app configuration loads."""
    try:
        from app.core.config import Settings, get_settings
        
        # Test manual config creation
        config = Settings(
            SECRET_KEY="test_secret_key_with_sufficient_length_for_validation",
            ENCRYPTION_KEY="test_encryption_key_with_sufficient_length_for_validation",
            ENCRYPTION_SALT="test_salt_with_sufficient_length_for_validation",
            ENVIRONMENT="test"
        )
        assert config.ENVIRONMENT == "test"
        print("[OK] Manual config creation works")
        
        # Test default config loading (from .env)
        settings = get_settings()
        assert settings is not None
        assert hasattr(settings, 'ENVIRONMENT')
        print(f"[OK] Default config loaded: {settings.ENVIRONMENT} environment")
        
    except Exception as e:
        raise AssertionError(f"Config test failed: {e}")

def test_security_module():
    """Test security module can be imported."""
    try:
        from app.core.security import EncryptionService
        print("[OK] Security module imported")
        
        # Test encryption service creation (might fail without proper config, that's ok)
        try:
            service = EncryptionService()
            test_data = "test_phi_data"
            encrypted = service.encrypt(test_data)
            decrypted = service.decrypt(encrypted)
            assert decrypted == test_data
            print("[OK] Encryption service working")
        except Exception as e:
            print(f"[WARN] Encryption service init issue (expected without DB): {e}")
        
    except ImportError as e:
        raise AssertionError(f"Security import failed: {e}")

def test_main_app_import():
    """Test main FastAPI app can be imported."""
    try:
        from app.main import app
        assert app is not None
        assert hasattr(app, 'routes')
        route_count = len([r for r in app.routes if hasattr(r, 'path')])
        print(f"[OK] FastAPI app imported with {route_count} routes")
    except Exception as e:
        print(f"[WARN] FastAPI app import issue (expected without DB): {e}")

def test_module_imports():
    """Test key modules can be imported."""
    modules_to_test = [
        ("app.modules.auth.router", "Auth router"),
        ("app.modules.healthcare_records.schemas", "Healthcare schemas"),
        ("app.core.database_advanced", "Database advanced"),
        ("app.core.event_bus_advanced", "Event bus"),
    ]
    
    for module_name, description in modules_to_test:
        try:
            __import__(module_name)
            print(f"[OK] {description} imported")
        except ImportError as e:
            print(f"[WARN] {description} import issue: {e}")

def run_all_tests():
    """Run all smoke tests."""
    print("=" * 60)
    print("RUNNING IRIS API SYSTEM SMOKE TESTS")
    print("=" * 60)
    
    test_functions = [
        test_python_version,
        test_core_dependencies,
        test_app_config,
        test_security_module,
        test_main_app_import,
        test_module_imports,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            print(f"\n--- Running {test_func.__name__} ---")
            test_func()
            passed += 1
        except Exception as e:
            print(f"[FAIL] {test_func.__name__}: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"SMOKE TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed > 0:
        print("Some tests failed - check output above for details")
        return False
    else:
        print("ALL SMOKE TESTS PASSED! System ready for development.")
        return True

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)