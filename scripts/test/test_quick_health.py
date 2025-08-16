#!/usr/bin/env python3
"""
Quick health test without Docker dependencies
Uses SQLite instead of PostgreSQL for rapid testing
"""
import os
import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set environment variables for SQLite testing
os.environ.update({
    "DEBUG": "true",
    "ENVIRONMENT": "test",
    "DATABASE_URL": "sqlite:///./test_db.sqlite",
    "REDIS_URL": "redis://localhost:6379/1",  # Will fallback to fake redis
    "SECRET_KEY": "test-secret-key-for-quick-testing",
    "ENCRYPTION_KEY": "test-encryption-key-32-chars-long!",
    "ALGORITHM": "HS256",
    "ACCESS_TOKEN_EXPIRE_MINUTES": "30"
})

async def test_app_startup():
    """Test if the app can start without Docker"""
    try:
        print("🔍 Testing app startup...")
        
        # Import the app
        from app.main import app
        print("✅ App imported successfully")
        
        # Test FastAPI app creation
        assert app is not None
        print("✅ FastAPI app created")
        
        # Check routes are registered
        routes = [route.path for route in app.routes]
        health_routes = [r for r in routes if "health" in r]
        print(f"✅ Found {len(health_routes)} health routes: {health_routes}")
        
        # Check API routes
        api_routes = [r for r in routes if r.startswith("/api/")]
        print(f"✅ Found {len(api_routes)} API routes")
        
        print("\n🎉 App startup test PASSED!")
        print("Your syntax fixes are working correctly!")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Install dependencies: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_health_endpoint():
    """Test health endpoint with test client"""
    try:
        print("\n🔍 Testing health endpoint...")
        
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        
        # Test basic health
        response = client.get("/health")
        print(f"Health response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health endpoint working: {data}")
        else:
            print(f"⚠️  Health endpoint returned {response.status_code}")
        
        # Test detailed health
        response = client.get("/health/detailed")
        print(f"Detailed health response: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Health test error: {e}")
        return False

async def main():
    """Run quick health tests"""
    print("🚀 Quick Health Test (No Docker Required)")
    print("=" * 50)
    
    # Test 1: App startup
    startup_ok = await test_app_startup()
    
    if startup_ok:
        # Test 2: Health endpoint
        await test_health_endpoint()
    
    print("\n" + "=" * 50)
    print("Test complete. If this passes, your Docker issues are likely")
    print("related to container startup time or resource constraints.")

if __name__ == "__main__":
    asyncio.run(main())