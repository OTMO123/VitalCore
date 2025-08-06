#!/usr/bin/env python3

import requests
import json

def test_auth_endpoints():
    """Test different auth endpoints to see which ones work"""
    
    base_url = "http://localhost:8000/api/v1/auth"
    
    tests = [
        {
            "name": "GET /me (should get 401 but show endpoint works)",
            "method": "GET",
            "url": f"{base_url}/me",
            "headers": {"Authorization": "Bearer fake_token"}
        },
        {
            "name": "GET /users (should get 401/403 but show endpoint works)", 
            "method": "GET",
            "url": f"{base_url}/users"
        },
        {
            "name": "POST /login (our problematic endpoint)",
            "method": "POST", 
            "url": f"{base_url}/login",
            "headers": {"Content-Type": "application/x-www-form-urlencoded"},
            "data": "username=admin&password=admin123"
        }
    ]
    
    for test in tests:
        print(f"\n{'='*60}")
        print(f"Testing: {test['name']}")
        print(f"URL: {test['url']}")
        
        try:
            kwargs = {
                "method": test["method"],
                "url": test["url"]
            }
            
            if "headers" in test:
                kwargs["headers"] = test["headers"]
            if "data" in test:
                kwargs["data"] = test["data"]
                
            response = requests.request(**kwargs)
            
            print(f"Status: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            
            try:
                json_response = response.json()
                print(f"Response: {json.dumps(json_response, indent=2)}")
            except:
                print(f"Response (non-JSON): {response.text}")
                
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    test_auth_endpoints()