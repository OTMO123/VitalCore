#!/usr/bin/env python3
"""
Quick test to verify login endpoint works with JSON
"""
import os
import asyncio
import httpx

# Set environment for testing
os.environ.update({
    "DEBUG": "true",
    "ENVIRONMENT": "test", 
    "DATABASE_URL": "sqlite:///./test_db.sqlite",
    "SECRET_KEY": "test-secret-key",
    "ENCRYPTION_KEY": "test-encryption-key-32-chars-long!",
    "ENCRYPTION_SALT": "test-salt",
    "ALGORITHM": "HS256",
    "ACCESS_TOKEN_EXPIRE_MINUTES": "30"
})

async def test_login_format():
    """Test login endpoint format"""
    from fastapi.testclient import TestClient
    from app.main import app
    
    print("🧪 Testing login endpoint format...")
    
    client = TestClient(app)
    
    # Test 1: Form data (should fail with validation error)
    print("1. Testing form data (expected to fail)...")
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "test", "password": "test"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    print(f"   Form data response: {response.status_code}")
    if response.status_code == 422:
        print("   ✅ Form data correctly rejected")
    
    # Test 2: JSON data (should work or fail with auth error, not validation)
    print("2. Testing JSON data...")
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "test", "password": "test"}
    )
    print(f"   JSON response: {response.status_code}")
    if response.status_code in [401, 404]:  # Auth error, not validation error
        print("   ✅ JSON data correctly parsed (auth failed as expected)")
    elif response.status_code == 422:
        print("   ❌ Still getting validation error")
        print(f"   Response: {response.text}")
    else:
        print(f"   Response: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_login_format())