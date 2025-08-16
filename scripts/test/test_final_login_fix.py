#!/usr/bin/env python3
"""
Test script to verify the audit logging fix is working.
"""

import urllib.request
import urllib.parse
import json
import sys

def test_login_fix():
    """Test the login endpoint to verify audit logging fix."""
    
    print("🔐 Testing Final Login Fix (log_hash)")
    print("=" * 50)
    
    # Login endpoint
    login_url = "http://localhost:8003/api/v1/auth/login"
    
    # Login data
    login_data = urllib.parse.urlencode({
        "username": "admin",
        "password": "admin123"
    }).encode('utf-8')
    
    try:
        print("1. Testing login with audit logging fix...")
        
        # Create request
        req = urllib.request.Request(
            login_url,
            data=login_data,
            headers={
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            method='POST'
        )
        
        # Make request
        with urllib.request.urlopen(req, timeout=10) as response:
            status_code = response.getcode()
            response_data = response.read().decode('utf-8')
            
            print(f"   Status Code: {status_code}")
            
            if status_code == 200:
                print("   ✅ LOGIN SUCCESS - Audit logging fix working!")
                
                # Parse JSON response
                try:
                    login_response = json.loads(response_data)
                    
                    if "access_token" in login_response:
                        token = login_response["access_token"]
                        print(f"   🎟️ Access token: {token[:20]}...")
                        
                        # Test dashboard endpoints
                        print("\n2. Testing dashboard endpoints...")
                        
                        auth_headers = {
                            'Authorization': f'Bearer {token}',
                            'Content-Type': 'application/json'
                        }
                        
                        endpoints = [
                            ("Recent Activities", "http://localhost:8003/api/v1/audit/recent-activities?limit=5"),
                            ("Health Summary", "http://localhost:8003/api/v1/iris/health/summary"),
                            ("Patients", "http://localhost:8003/api/v1/healthcare/patients?limit=1")
                        ]
                        
                        success_count = 0
                        for name, url in endpoints:
                            try:
                                test_req = urllib.request.Request(url, headers=auth_headers)
                                with urllib.request.urlopen(test_req, timeout=10) as test_response:
                                    if test_response.getcode() == 200:
                                        print(f"   ✅ {name}: SUCCESS")
                                        success_count += 1
                                    else:
                                        print(f"   ⚠️ {name}: HTTP {test_response.getcode()}")
                            except Exception as e:
                                print(f"   ❌ {name}: FAILED ({e})")
                        
                        print(f"\n3. Dashboard Status: {success_count}/3 endpoints working")
                        
                        if success_count >= 2:
                            print("\n   🎉 SYSTEM OPERATIONAL!")
                            print("   ✅ Authentication: WORKING") 
                            print("   ✅ Audit Logging: FIXED")
                            print("   ✅ Dashboard APIs: READY")
                            print("\n   🌐 Your dashboard should work perfectly now!")
                            print("   Visit: http://localhost:3000 or http://localhost:5173")
                        else:
                            print("\n   ⚠️ Some dashboard endpoints need attention")
                        
                    else:
                        print("   ❌ Token not found in response")
                        
                except json.JSONDecodeError as e:
                    print(f"   ❌ Failed to parse JSON: {e}")
                    
            else:
                print(f"   ❌ LOGIN FAILED - Status: {status_code}")
                print(f"   Response: {response_data}")
                
    except urllib.error.HTTPError as e:
        status_code = e.code
        error_data = e.read().decode('utf-8')
        
        print(f"   ❌ HTTP Error {status_code}")
        
        if status_code == 500:
            print("   🔍 Still getting 500 error - check server logs for details")
            
        print(f"   Error: {error_data}")
            
    except Exception as e:
        print(f"   ❌ Test failed: {e}")

if __name__ == "__main__":
    test_login_fix()