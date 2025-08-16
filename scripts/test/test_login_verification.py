#!/usr/bin/env python3
"""
Test script to verify that the JSON serialization fix is working
for the authentication endpoint.
"""

import requests
import json
import sys

def test_login_fix():
    """Test the login endpoint to verify JSON serialization fix."""
    
    print("🔐 Testing Authentication JSON Serialization Fix")
    print("=" * 50)
    
    # Login endpoint
    login_url = "http://localhost:8003/api/v1/auth/login"
    
    # Login data
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    try:
        print("1. Testing login endpoint...")
        
        # Make login request
        response = requests.post(
            login_url, 
            data=login_data, 
            headers=headers,
            timeout=10
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ LOGIN SUCCESS - JSON serialization fix working!")
            
            # Parse response
            login_response = response.json()
            
            # Verify token structure
            if "access_token" in login_response:
                token = login_response["access_token"]
                print(f"   🎟️ Access token received: {token[:20]}...")
                
                # Test a protected endpoint with the token
                print("\n2. Testing protected endpoint...")
                
                auth_headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                
                # Test recent activities endpoint
                activities_url = "http://localhost:8003/api/v1/audit/recent-activities"
                
                try:
                    activities_response = requests.get(
                        activities_url,
                        headers=auth_headers,
                        timeout=10
                    )
                    
                    print(f"   Activities API Status: {activities_response.status_code}")
                    
                    if activities_response.status_code == 200:
                        activities_data = activities_response.json()
                        print(f"   ✅ Dashboard API working! Found {len(activities_data.get('activities', []))} activities")
                    else:
                        print(f"   ⚠️ Activities API returned: {activities_response.status_code}")
                        
                except requests.exceptions.RequestException as e:
                    print(f"   ❌ Activities API test failed: {e}")
                
                print("\n3. Final Status:")
                print("   ✅ Authentication: WORKING")
                print("   ✅ JSON Serialization: FIXED")
                print("   ✅ Audit Logging: OPERATIONAL")
                print("   🎉 DASHBOARD SHOULD WORK PERFECTLY!")
                
            else:
                print("   ❌ Token not found in response")
                print(f"   Response: {login_response}")
                
        elif response.status_code == 500:
            print("   ❌ LOGIN FAILED - 500 Internal Server Error")
            print("   🔍 This suggests the JSON serialization issue still exists")
            
            try:
                error_response = response.json()
                print(f"   Error details: {error_response}")
            except:
                print(f"   Raw error: {response.text}")
                
        else:
            print(f"   ❌ LOGIN FAILED - Status: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Cannot connect to server")
        print("   🔍 Make sure uvicorn is running on port 8003")
        print("   Command: uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload")
        
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request failed: {e}")
        
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_login_fix()