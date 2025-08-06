#!/usr/bin/env python3
"""
Debug HTTP request to see exactly what's happening.
"""

import requests
import json

def debug_login_request():
    """Debug the login request step by step."""
    
    print("DEBUG - HTTP Login Request")
    print("=" * 40)
    
    url = "http://localhost:8000/api/v1/auth/login"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'DebugTest/1.0'
    }
    data = "username=admin&password=admin123"
    
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print(f"Data: {data}")
    print()
    
    try:
        print("Making request...")
        response = requests.post(url, headers=headers, data=data)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text}")
        
        if response.status_code == 200:
            try:
                json_response = response.json()
                print("JSON Response:")
                print(json.dumps(json_response, indent=2))
                
                # Check token structure
                if 'access_token' in json_response:
                    print(f"Access token length: {len(json_response['access_token'])}")
                if 'refresh_token' in json_response:
                    print(f"Refresh token length: {len(json_response['refresh_token'])}")
                    
            except json.JSONDecodeError:
                print("Response is not valid JSON")
        else:
            print("Login failed!")
            
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to server")
    except Exception as e:
        print(f"ERROR: {e}")

def test_other_endpoints():
    """Test other endpoints to see if server is working."""
    
    print("\nTesting other endpoints:")
    print("-" * 30)
    
    # Test health endpoint
    try:
        health_response = requests.get("http://localhost:8000/health")
        print(f"Health endpoint: {health_response.status_code} - {health_response.text}")
    except Exception as e:
        print(f"Health endpoint error: {e}")
    
    # Test root endpoint
    try:
        root_response = requests.get("http://localhost:8000/")
        print(f"Root endpoint: {root_response.status_code} - {root_response.text}")
    except Exception as e:
        print(f"Root endpoint error: {e}")
    
    # Test protected endpoint (should get 401/403)
    try:
        me_response = requests.get("http://localhost:8000/api/v1/auth/me")
        print(f"Protected /me endpoint: {me_response.status_code} - {me_response.text}")
    except Exception as e:
        print(f"Protected endpoint error: {e}")

if __name__ == "__main__":
    debug_login_request()
    test_other_endpoints()