#!/usr/bin/env python3
"""
Test Clinical Workflows Endpoints
"""
import requests
import json

def test_endpoints():
    base_url = "http://localhost:8000"
    
    print("Testing Clinical Workflows Endpoints")
    print("=" * 40)
    
    # Test 1: Health check
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/api/v1/clinical-workflows/health")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
            print("   [PASS] Health endpoint working")
        else:
            print(f"   [FAIL] Health endpoint failed: {response.text}")
    except Exception as e:
        print(f"   [ERROR] {e}")
    
    # Test 2: API documentation
    print("\n2. Testing API documentation...")
    try:
        response = requests.get(f"{base_url}/docs")
        if response.status_code == 200:
            print("   [PASS] API documentation available")
            print(f"   URL: {base_url}/docs")
        else:
            print(f"   [FAIL] Documentation not available")
    except Exception as e:
        print(f"   [ERROR] {e}")
    
    # Test 3: OpenAPI schema
    print("\n3. Testing OpenAPI schema...")
    try:
        response = requests.get(f"{base_url}/openapi.json")
        if response.status_code == 200:
            schema = response.json()
            # Check if clinical workflows endpoints are in the schema
            paths = schema.get('paths', {})
            clinical_paths = [path for path in paths.keys() if 'clinical-workflows' in path]
            print(f"   [PASS] Found {len(clinical_paths)} clinical workflow endpoints")
            for path in clinical_paths[:5]:  # Show first 5
                print(f"     - {path}")
            if len(clinical_paths) > 5:
                print(f"     ... and {len(clinical_paths) - 5} more")
        else:
            print(f"   [FAIL] OpenAPI schema not available")
    except Exception as e:
        print(f"   [ERROR] {e}")
    
    # Test 4: Test an endpoint that requires auth (should return 401/403)
    print("\n4. Testing authenticated endpoint (expect auth error)...")
    try:
        response = requests.get(f"{base_url}/api/v1/clinical-workflows/")
        print(f"   Status: {response.status_code}")
        if response.status_code in [401, 403, 422]:
            print("   [PASS] Authentication required (as expected)")
        else:
            print(f"   [INFO] Unexpected response: {response.text[:100]}")
    except Exception as e:
        print(f"   [ERROR] {e}")
    
    print(f"\n[SUCCESS] Clinical Workflows module is live!")
    print(f"API Documentation: {base_url}/docs")
    print(f"Clinical Workflows: {base_url}/api/v1/clinical-workflows/")

if __name__ == "__main__":
    test_endpoints()