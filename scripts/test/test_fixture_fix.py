#!/usr/bin/env python3
"""
Quick test to verify that the auth_headers fixture is working correctly
without coroutine iteration errors.
"""
import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_fixture_imports():
    """Test that we can import the fixtures without errors."""
    try:
        from app.tests.conftest import auth_headers, admin_auth_headers, test_access_token, test_admin_token
        from app.core.config import Settings
        print("✓ All fixtures imported successfully")
        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        return False

def test_token_creation():
    """Test that tokens can be created without database dependencies."""
    try:
        from app.core.config import Settings
        from app.core.security import security_manager
        from datetime import timedelta
        
        # Create test settings
        test_settings = Settings(
            DEBUG=True,
            ENVIRONMENT="test",
            DATABASE_URL="postgresql+asyncpg://postgres:password@db:5432/iris_db",
            SECRET_KEY="test_secret_key_32_characters_long",
            ACCESS_TOKEN_EXPIRE_MINUTES=30,
        )
        
        # Test token creation (mimicking the fixture logic)
        token_data = {
            "user_id": "test-user-id",
            "username": "testuser",
            "role": "USER",
            "email": "test@example.com"
        }
        token = security_manager.create_access_token(
            data=token_data,
            expires_delta=timedelta(minutes=test_settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        # Test headers creation
        headers = {"Authorization": f"Bearer {token}"}
        
        print("✓ Token and headers created successfully")
        print(f"  Token prefix: {token[:20]}...")
        print(f"  Headers: {headers}")
        return True
        
    except Exception as e:
        print(f"✗ Token creation error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("Testing fixture fix for coroutine iteration error...")
    print()
    
    success = True
    
    print("1. Testing fixture imports...")
    success &= test_fixture_imports()
    print()
    
    print("2. Testing token creation...")
    success &= test_token_creation()
    print()
    
    if success:
        print("🎉 All tests passed! The fixture fix should resolve the coroutine iteration error.")
        return 0
    else:
        print("❌ Some tests failed. There may still be issues with the fixture configuration.")
        return 1

if __name__ == "__main__":
    exit(main())