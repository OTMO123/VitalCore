#!/usr/bin/env python3
"""
Quick test to verify backend is responding after restart.
"""

import urllib.request
import json

def test_backend():
    print("🔍 Testing Backend Connection")
    print("=" * 40)
    
    # Test basic health endpoint
    try:
        print("1. Testing basic health endpoint...")
        req = urllib.request.Request("http://localhost:8003/health")
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.getcode() == 200:
                print("   ✅ Backend is responding")
                data = json.loads(response.read().decode('utf-8'))
                print(f"   Status: {data.get('status', 'unknown')}")
            else:
                print(f"   ❌ Backend returned: {response.getcode()}")
                
    except Exception as e:
        print(f"   ❌ Backend connection failed: {e}")
        return False
    
    # Test login endpoint
    try:
        print("\n2. Testing login endpoint...")
        login_data = "username=admin&password=admin123".encode('utf-8')
        req = urllib.request.Request(
            "http://localhost:8003/api/v1/auth/login",
            data=login_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.getcode() == 200:
                print("   ✅ Login endpoint working")
                return True
            else:
                print(f"   ❌ Login failed: {response.getcode()}")
                return False
                
    except Exception as e:
        print(f"   ❌ Login test failed: {e}")
        return False

if __name__ == "__main__":
    if test_backend():
        print("\n🎉 Backend is working!")
        print("Frontend infinite loading might be a React issue.")
        print("\nTry:")
        print("1. Stop frontend (Ctrl+C)")
        print("2. Clear cache: rm -rf node_modules/.vite")
        print("3. Restart: npm run dev")
    else:
        print("\n❌ Backend has issues - need to fix backend first")