#!/usr/bin/env python3
"""
Test the specific health endpoint that the frontend is calling.
"""

import urllib.request
import json

def test_health_endpoint():
    """Test the health endpoint that frontend calls."""
    
    print("🏥 Testing Health Endpoint")
    print("=" * 30)
    
    try:
        print("1. Testing /health endpoint...")
        req = urllib.request.Request("http://localhost:8003/health")
        
        with urllib.request.urlopen(req, timeout=10) as response:
            status = response.getcode()
            data = response.read().decode('utf-8')
            
            print(f"   Status: {status}")
            
            if status == 200:
                try:
                    json_data = json.loads(data)
                    print(f"   ✅ Health endpoint working!")
                    print(f"   Response: {json_data}")
                except:
                    print(f"   ✅ Health endpoint working (non-JSON)!")
                    print(f"   Response: {data[:100]}...")
            else:
                print(f"   ❌ Health endpoint failed: {status}")
                print(f"   Response: {data[:200]}...")
                
    except urllib.error.HTTPError as e:
        error_data = e.read().decode('utf-8')
        print(f"   ❌ HTTP Error {e.code}")
        print(f"   Details: {error_data[:200]}...")
        
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
    
    # Also test /api/health (the proxied path)
    try:
        print("\n2. Testing direct backend health...")
        req2 = urllib.request.Request("http://localhost:8003/api/v1/health")
        
        with urllib.request.urlopen(req2, timeout=10) as response:
            status = response.getcode()
            print(f"   /api/v1/health Status: {status}")
            
    except Exception as e:
        print(f"   /api/v1/health failed: {e}")

if __name__ == "__main__":
    test_health_endpoint()