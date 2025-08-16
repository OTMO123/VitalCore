#!/usr/bin/env python3

import requests
import json

def test_login_api():
    """Test the login API directly"""
    url = "http://localhost:8000/api/v1/auth/login"
    
    # Prepare form data
    data = {
        "username": "admin",
        "password": "admin123"
    }
    
    # Send request
    try:
        print("Testing login API...")
        print(f"URL: {url}")
        print(f"Data: {data}")
        
        response = requests.post(
            url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"\nResponse JSON:")
            print(json.dumps(response_data, indent=2))
            
            # Check for tokens
            if "access_token" in response_data:
                print(f"\n✅ Access token present: {response_data['access_token'][:50]}...")
            else:
                print(f"\n❌ No access_token in response")
                
            if "refresh_token" in response_data:
                print(f"✅ Refresh token present: {response_data['refresh_token'][:50]}...")
            else:
                print(f"❌ No refresh_token in response")
                
        else:
            print(f"\nError response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Is it running on port 8000?")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_login_api()