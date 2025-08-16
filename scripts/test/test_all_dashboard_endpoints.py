#!/usr/bin/env python3
"""
Test ALL dashboard endpoints to find any remaining 500 errors.
"""

import urllib.request
import urllib.parse
import json

def test_all_endpoints():
    """Test every dashboard endpoint to identify 500 errors."""
    
    print("🔍 Testing ALL Dashboard Endpoints")
    print("=" * 50)
    
    # Login first
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
            if response.getcode() != 200:
                print(f"   ❌ Login failed: {response.getcode()}")
                return
                
            login_response = json.loads(response.read().decode('utf-8'))
            token = login_response["access_token"]
            print(f"   ✅ Token obtained")
            
            # Test ALL possible dashboard endpoints
            auth_headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            endpoints = [
                # Core dashboard endpoints
                ("Recent Activities", "http://localhost:8003/api/v1/audit/recent-activities?limit=5"),
                ("Audit Stats", "http://localhost:8003/api/v1/audit/stats"),
                ("Health Summary", "http://localhost:8003/api/v1/iris/health/summary"),
                ("IRIS Status", "http://localhost:8003/api/v1/iris/status"),
                ("Patients List", "http://localhost:8003/api/v1/healthcare/patients?limit=3"),
                
                # User management
                ("Current User", "http://localhost:8003/api/v1/auth/me"),
                ("Users List", "http://localhost:8003/api/v1/auth/users?limit=5"),
                
                # Health checks
                ("App Health", "http://localhost:8003/health"),
                ("IRIS Health", "http://localhost:8003/api/v1/iris/health"),
            ]
            
            print(f"\n2. Testing {len(endpoints)} endpoints...")
            
            success_count = 0
            errors_found = []
            
            for name, url in endpoints:
                try:
                    test_req = urllib.request.Request(url, headers=auth_headers)
                    with urllib.request.urlopen(test_req, timeout=10) as test_response:
                        status = test_response.getcode()
                        response_data = test_response.read().decode('utf-8')
                        
                        if status == 200:
                            print(f"   ✅ {name}: SUCCESS (200)")
                            success_count += 1
                        else:
                            print(f"   ⚠️ {name}: HTTP {status}")
                            errors_found.append(f"{name}: {status}")
                            
                except urllib.error.HTTPError as e:
                    error_data = e.read().decode('utf-8') if hasattr(e, 'read') else str(e)
                    print(f"   ❌ {name}: HTTP {e.code}")
                    errors_found.append(f"{name}: {e.code} - {error_data[:100]}")
                    
                except Exception as e:
                    print(f"   ❌ {name}: ERROR - {str(e)[:50]}")
                    errors_found.append(f"{name}: {str(e)[:50]}")
            
            print(f"\n3. Results Summary:")
            print(f"   ✅ Working endpoints: {success_count}/{len(endpoints)}")
            print(f"   ❌ Failed endpoints: {len(errors_found)}")
            
            if errors_found:
                print(f"\n4. Errors Found:")
                for error in errors_found:
                    print(f"   → {error}")
                    
                print(f"\n   🔧 These are the endpoints causing 500 errors!")
            else:
                print(f"\n   🎉 NO 500 ERRORS FOUND!")
                print(f"   All backend endpoints are working perfectly!")
                
            if success_count >= len(endpoints) - 2:
                print(f"\n   ✅ Dashboard should work great!")
                print(f"   Start frontend: cd frontend && npm run dev")
                
    except Exception as e:
        print(f"   ❌ Test failed: {e}")

if __name__ == "__main__":
    test_all_endpoints()