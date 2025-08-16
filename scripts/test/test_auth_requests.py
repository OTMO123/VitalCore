#!/usr/bin/env python3
"""
Test authentication using requests library
"""

import requests
import json

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get("http://localhost:8003/health")
        print(f"Health Check: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        else:
            print(f"Error Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_login(username, password):
    """Test login with username/password"""
    try:
        # Test with form data
        response = requests.post(
            "http://localhost:8003/api/v1/auth/login",
            data={
                "username": username,
                "password": password
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )
        
        print(f"Login Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print("SUCCESS: Authentication worked!")
            print(f"Token Type: {data.get('token_type', 'N/A')}")
            if 'access_token' in data:
                token = data['access_token']
                print(f"Token Length: {len(token)}")
                return token
            return True
        else:
            print("FAILED: Authentication failed")
            return None
            
    except Exception as e:
        print(f"Login request failed: {e}")
        return None

def test_authenticated_request(token):
    """Test an authenticated request"""
    if not token:
        print("No token available for authenticated request")
        return False
        
    try:
        response = requests.get(
            "http://localhost:8003/api/v1/auth/me",
            headers={
                "Authorization": f"Bearer {token}"
            }
        )
        
        print(f"Auth Test Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"Authenticated request failed: {e}")
        return False

def main():
    print("=" * 60)
    print("AUTHENTICATION TEST")
    print("=" * 60)
    
    # Test health first
    print("\n1. Testing Health Endpoint...")
    if not test_health():
        print("Server is not responding. Exiting.")
        return
    
    # Test login with admin
    print("\n2. Testing Login with admin...")
    token = test_login("admin", "admin123")
    
    if not token:
        print("\n3. Testing Login with testadmin...")
        token = test_login("testadmin", "test123")
    
    # Test authenticated request
    if token and isinstance(token, str):
        print("\n4. Testing Authenticated Request...")
        test_authenticated_request(token)
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()