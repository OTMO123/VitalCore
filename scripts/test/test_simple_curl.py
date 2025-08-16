#!/usr/bin/env python3
"""
Test using urllib without external dependencies.
"""

import urllib.request
import urllib.parse
import json

def test_endpoints():
    """Test endpoints using built-in urllib."""
    
    print("Testing endpoints with urllib")
    print("=" * 40)
    
    # Test health endpoint
    print("1. Testing health endpoint...")
    try:
        with urllib.request.urlopen("http://localhost:8000/health") as response:
            health_data = response.read().decode()
            print(f"Health: {response.status} - {health_data}")
    except Exception as e:
        print(f"Health error: {e}")
    
    # Test root endpoint
    print("\n2. Testing root endpoint...")
    try:
        with urllib.request.urlopen("http://localhost:8000/") as response:
            root_data = response.read().decode()
            print(f"Root: {response.status} - {root_data}")
    except Exception as e:
        print(f"Root error: {e}")
    
    # Test login endpoint
    print("\n3. Testing login endpoint...")
    try:
        data = urllib.parse.urlencode({'username': 'admin', 'password': 'admin123'}).encode()
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        req = urllib.request.Request(
            "http://localhost:8000/api/v1/auth/login",
            data=data,
            headers=headers,
            method='POST'
        )
        
        with urllib.request.urlopen(req) as response:
            login_data = response.read().decode()
            print(f"Login: {response.status} - {login_data}")
            
    except urllib.error.HTTPError as e:
        error_data = e.read().decode()
        print(f"Login error: {e.status} - {error_data}")
    except Exception as e:
        print(f"Login error: {e}")
    
    # Test with wrong endpoint to see if it's path-specific
    print("\n4. Testing non-existent endpoint...")
    try:
        with urllib.request.urlopen("http://localhost:8000/api/v1/nonexistent") as response:
            data = response.read().decode()
            print(f"Non-existent: {response.status} - {data}")
    except urllib.error.HTTPError as e:
        print(f"Non-existent: {e.status} (expected 404)")
    except Exception as e:
        print(f"Non-existent error: {e}")

if __name__ == "__main__":
    test_endpoints()