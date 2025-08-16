#!/usr/bin/env python3
"""
Test the actual API authentication endpoint to see detailed errors
"""
import requests
import json

def test_api_auth():
    print("=== API AUTHENTICATION DEBUG ===")
    
    url = "http://localhost:8000/api/v1/auth/login"
    payload = {
        "username": "admin",
        "password": "admin123"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print(f"Testing: POST {url}")
        print(f"Payload: {json.dumps(payload)}")
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("SUCCESS: Authentication worked!")
        elif response.status_code == 401:
            print("FAIL: Authentication rejected (credentials invalid)")
        elif response.status_code == 422:
            print("FAIL: Validation error (malformed request)")
        else:
            print(f"UNEXPECTED: Status {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"Request Error: {e}")
    except Exception as e:
        print(f"Unexpected Error: {e}")

if __name__ == "__main__":
    test_api_auth()