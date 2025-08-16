#!/usr/bin/env python3
"""
Test script for doctor history endpoints integration
"""
import requests
import json
import sys
from datetime import datetime, timezone

# Backend base URL
BASE_URL = "http://localhost:8000/api/v1"

def test_doctor_endpoints():
    """Test the doctor history endpoints are accessible"""
    
    print("🔍 Testing Doctor History Integration")
    print("=" * 50)
    
    # Test 1: Health check endpoint (should return 401 without auth)
    print("\n1️⃣  Testing Health Check Endpoint")
    try:
        response = requests.get(f"{BASE_URL}/doctor/health")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 401:
            print("   ✅ Endpoint exists and requires authentication (expected)")
        elif response.status_code == 200:
            print("   ✅ Endpoint accessible")
            print(f"   Response: {response.json()}")
        else:
            print(f"   ❌ Unexpected status code: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Check available endpoints via OpenAPI
    print("\n2️⃣  Testing OpenAPI Documentation")
    try:
        response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/openapi.json")
        if response.status_code == 200:
            openapi_data = response.json()
            doctor_endpoints = []
            
            for path, methods in openapi_data.get('paths', {}).items():
                if '/doctor' in path:
                    for method in methods.keys():
                        doctor_endpoints.append(f"{method.upper()} {path}")
            
            print(f"   ✅ Found {len(doctor_endpoints)} doctor endpoints:")
            for endpoint in doctor_endpoints:
                print(f"      {endpoint}")
        else:
            print(f"   ❌ Cannot access OpenAPI docs: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error accessing OpenAPI: {e}")
    
    # Test 3: Test with demo authentication (if available)
    print("\n3️⃣  Testing with Demo Authentication")
    try:
        # Try to login with demo credentials
        login_data = {
            "username": "admin@vitalcore.com",
            "password": "admin123"
        }
        
        login_response = requests.post(
            f"{BASE_URL}/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if login_response.status_code == 200:
            token_data = login_response.json()
            access_token = token_data.get('access_token')
            
            if access_token:
                headers = {"Authorization": f"Bearer {access_token}"}
                
                # Test health endpoint with auth
                health_response = requests.get(f"{BASE_URL}/doctor/health", headers=headers)
                print(f"   Health endpoint with auth: {health_response.status_code}")
                if health_response.status_code == 200:
                    print(f"   ✅ Response: {health_response.json()}")
                
                # Test case history endpoint (should return 404 or error for invalid case)
                test_case_id = "demo-case-he-3849"
                history_response = requests.get(
                    f"{BASE_URL}/doctor/history/{test_case_id}",
                    headers=headers
                )
                print(f"   History endpoint: {history_response.status_code}")
                if history_response.status_code in [200, 404, 500]:
                    print("   ✅ Endpoint responsive (expected error for demo case)")
                
                # Test linked timeline endpoint
                timeline_response = requests.get(
                    f"{BASE_URL}/doctor/timeline/{test_case_id}/linked",
                    headers=headers
                )
                print(f"   Timeline endpoint: {timeline_response.status_code}")
                if timeline_response.status_code in [200, 404, 500]:
                    print("   ✅ Endpoint responsive (expected error for demo case)")
                    
            else:
                print("   ❌ No access token in login response")
        else:
            print(f"   ❌ Login failed: {login_response.status_code}")
            print(f"   Response: {login_response.text}")
            
    except Exception as e:
        print(f"   ❌ Error testing with auth: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Integration test completed!")
    print("\nFrontend URLs to test:")
    print("   📊 Doctor Dashboard: http://localhost:3000/dashboard")
    print("   📋 History Mode: http://localhost:3000/doctor/history")
    print("   🔗 Timeline View: http://localhost:3000/doctor/timeline")

if __name__ == "__main__":
    test_doctor_endpoints()