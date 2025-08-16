#!/usr/bin/env python3

import requests
import json
import sys
import importlib

# Clear any cached modules
modules_to_clear = [
    'app.modules.auth.service',
    'app.modules.auth.router', 
    'app.core.database',
    'app.core.database_unified'
]

for module in modules_to_clear:
    if module in sys.modules:
        del sys.modules[module]

def test_login_fresh():
    """Test login with fresh imports"""
    url = "http://localhost:8000/api/v1/auth/login"
    
    # Test data
    data = {
        "username": "admin",
        "password": "admin123"
    }
    
    # Test with correct Content-Type header
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    try:
        print("Testing fresh login API...")
        print(f"URL: {url}")
        print(f"Data: {data}")
        print(f"Headers: {headers}")
        
        response = requests.post(url, data=data, headers=headers)
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        try:
            response_json = response.json()
            print(f"\nResponse JSON:")
            print(json.dumps(response_json, indent=2))
            
            if response.status_code == 200:
                if "access_token" in response_json:
                    print(f"\n✅ Access token present: {response_json['access_token'][:50]}...")
                else:
                    print(f"\n❌ No access_token in response")
                    
                if "refresh_token" in response_json:
                    print(f"✅ Refresh token present: {response_json['refresh_token'][:50]}...")
                else:
                    print(f"❌ No refresh_token in response")
            else:
                print(f"\n❌ Login failed with status {response.status_code}")
                
        except json.JSONDecodeError:
            print(f"\nNon-JSON response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_login_fresh()