#!/usr/bin/env python3
"""
Test the dashboard fixes for 500 errors.
"""

import urllib.request
import urllib.parse
import json
import sys

def test_dashboard_endpoints():
    """Test the fixed dashboard endpoints."""
    
    print("🔧 Testing Dashboard 500 Error Fixes")
    print("=" * 50)
    
    # First, login to get token
    login_url = "http://localhost:8003/api/v1/auth/login"
    login_data = urllib.parse.urlencode({
        "username": "admin",
        "password": "admin123"
    }).encode('utf-8')
    
    try:
        print("1. Getting authentication token...")
        
        req = urllib.request.Request(
            login_url,
            data=login_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.getcode() == 200:
                login_response = json.loads(response.read().decode('utf-8'))
                token = login_response["access_token"]
                print(f"   ✅ Token obtained: {token[:20]}...")
                
                # Test the problematic endpoints
                auth_headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }
                
                print("\n2. Testing fixed endpoints...")
                
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
                            status = test_response.getcode()
                            if status == 200:
                                response_data = json.loads(test_response.read().decode('utf-8'))
                                print(f"   ✅ {name}: SUCCESS (200)")
                                
                                # Show some data details
                                if name == "Recent Activities":
                                    activities = response_data.get('activities', [])
                                    print(f"      → Found {len(activities)} activities")
                                elif name == "Health Summary":
                                    print(f"      → Status: {response_data.get('overall_status')}")
                                elif name == "Patients":
                                    print(f"      → Total patients: {response_data.get('total', 0)}")
                                
                                success_count += 1
                            else:
                                print(f"   ⚠️ {name}: HTTP {status}")
                                
                    except urllib.error.HTTPError as e:
                        error_data = e.read().decode('utf-8') if hasattr(e, 'read') else str(e)
                        print(f"   ❌ {name}: HTTP {e.code}")
                        print(f"      → Error: {error_data[:100]}...")
                        
                    except Exception as e:
                        print(f"   ❌ {name}: FAILED ({e})")
                
                print(f"\n3. Final Results:")
                print(f"   Working endpoints: {success_count}/3")
                
                if success_count == 3:
                    print("\n   🎉 ALL DASHBOARD ENDPOINTS FIXED!")
                    print("   ✅ No more 500 errors")
                    print("   ✅ Dashboard should load perfectly")
                    print("\n   🌐 Try your dashboard now:")
                    print("   → http://localhost:3000")
                    print("   → http://localhost:5173")
                elif success_count >= 2:
                    print("\n   ✅ Major issues fixed!")
                    print("   Dashboard should work with minor issues")
                else:
                    print("\n   ⚠️ Still some issues to resolve")
                    
            else:
                print(f"   ❌ Login failed: {response.getcode()}")
                
    except Exception as e:
        print(f"   ❌ Test failed: {e}")

if __name__ == "__main__":
    test_dashboard_endpoints()