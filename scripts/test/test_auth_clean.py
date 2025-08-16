#!/usr/bin/env python3
"""
Simple authentication test without unicode
"""

import requests
import json

def test_auth():
    url = "http://localhost:8003"
    
    print("Testing authentication...")
    
    # Test login
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    
    try:
        response = requests.post(f"{url}/api/v1/auth/login", data=login_data)
        print(f"Login Status: {response.status_code}")
        print(f"Login Response: {response.text}")
        
        if response.status_code == 200:
            print("SUCCESS: Authentication worked!")
            token_data = response.json()
            print(f"Token: {token_data.get('access_token', 'N/A')}")
            return True
        else:
            print("FAILED: Authentication failed")
            return False
            
    except Exception as e:
        print(f"ERROR: Connection failed - {e}")
        return False

if __name__ == "__main__":
    test_auth()