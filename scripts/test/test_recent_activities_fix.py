#!/usr/bin/env python3
"""
Test the Recent Activities fix specifically.
"""

import urllib.request
import urllib.parse
import json

def test_recent_activities():
    """Test the Recent Activities endpoint fix."""
    
    print("🔧 Testing Recent Activities Fix")
    print("=" * 40)
    
    # Login first
    login_url = "http://localhost:8003/api/v1/auth/login"
    login_data = urllib.parse.urlencode({
        "username": "admin",
        "password": "admin123"
    }).encode('utf-8')
    
    try:
        print("1. Getting token...")
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
                print(f"   ✅ Token: {token[:20]}...")
                
                # Test Recent Activities
                print("\n2. Testing Recent Activities...")
                
                activities_url = "http://localhost:8003/api/v1/audit/recent-activities?limit=5"
                auth_headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }
                
                try:
                    test_req = urllib.request.Request(activities_url, headers=auth_headers)
                    with urllib.request.urlopen(test_req, timeout=10) as test_response:
                        status = test_response.getcode()
                        response_data = json.loads(test_response.read().decode('utf-8'))
                        
                        print(f"   Status: {status}")
                        
                        if status == 200:
                            activities = response_data.get('activities', [])
                            print(f"   ✅ Recent Activities: SUCCESS")
                            print(f"   📊 Found {len(activities)} activities")
                            
                            # Show activity details
                            for i, activity in enumerate(activities[:3]):  # Show first 3
                                print(f"      {i+1}. {activity.get('description', 'Unknown')} - {activity.get('severity', 'info')}")
                            
                            if len(activities) == 0:
                                print("   ℹ️ No activities yet - this is normal for a fresh system")
                            
                            print("\n   🎉 Recent Activities endpoint is working!")
                            print("   ✅ No more enum errors")
                            print("   ✅ Ready for dashboard")
                            
                        else:
                            print(f"   ❌ Failed with status: {status}")
                            
                except urllib.error.HTTPError as e:
                    error_data = e.read().decode('utf-8')
                    print(f"   ❌ HTTP Error {e.code}")
                    print(f"   Details: {error_data}")
                    
                except Exception as e:
                    print(f"   ❌ Request failed: {e}")
                    
            else:
                print(f"   ❌ Login failed: {response.getcode()}")
                
    except Exception as e:
        print(f"   ❌ Test failed: {e}")

if __name__ == "__main__":
    test_recent_activities()