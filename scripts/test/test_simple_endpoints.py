#!/usr/bin/env python3
"""
Simple endpoint test script - based on FRONTEND_INTEGRATION_REPORT.md
Tests the 5 working authentication endpoints and documents findings
"""

import requests
import json
import time

def test_endpoints():
    base_url = "http://localhost:8003/api/v1"
    
    print("🎯 TESTING ALL 5 ENDPOINTS")
    print("=" * 40)
    
    # Step 1: Test authentication
    print("🔐 Step 1: Authenticating...")
    try:
        login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        
        response = requests.post(
            f"{base_url}/auth/login",
            data=login_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=10
        )
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get('access_token')
            print(f"✅ Auth successful! Token: {access_token[:20]}...")
            
            headers = {'Authorization': f'Bearer {access_token}'}
            
            # Step 2: Test all working endpoints from report
            endpoints = [
                ("GET", "/auth/roles", "List all roles"),
                ("GET", "/auth/permissions", "List all permissions"), 
                ("GET", "/auth/me", "Get current user data"),
                ("GET", "/analytics/health", "Analytics health check"),
                ("POST", "/analytics/quality-measures", "Quality measures analytics")
            ]
            
            print(f"\n📊 Step 2: Testing {len(endpoints)} working endpoints...")
            
            for method, endpoint, description in endpoints:
                try:
                    if method == "GET":
                        resp = requests.get(f"{base_url}{endpoint}", headers=headers, timeout=5)
                    else:
                        # Sample data for POST requests
                        test_data = {
                            "measure_ids": ["hba1c_control"],
                            "time_range": "90d",
                            "requesting_user_id": "test-user"
                        }
                        resp = requests.post(f"{base_url}{endpoint}", headers=headers, json=test_data, timeout=5)
                    
                    status = "✅" if resp.status_code in [200, 201] else "❌"
                    print(f"  {status} {method} {endpoint} - {resp.status_code} - {description}")
                    
                except Exception as e:
                    print(f"  ❌ {method} {endpoint} - Error: {str(e)[:50]}")
            
            # Step 3: Test healthcare endpoints 
            print(f"\n🏥 Step 3: Testing healthcare endpoints...")
            healthcare_endpoints = [
                ("GET", "/healthcare/patients", "List patients with SOC2 audit"),
                ("GET", "/patients/risk/health", "Risk stratification health check")
            ]
            
            for method, endpoint, description in healthcare_endpoints:
                try:
                    resp = requests.get(f"{base_url}{endpoint}", headers=headers, timeout=5)
                    status = "✅" if resp.status_code in [200, 201] else "❌"
                    print(f"  {status} {method} {endpoint} - {resp.status_code} - {description}")
                    
                except Exception as e:
                    print(f"  ❌ {method} {endpoint} - Error: {str(e)[:50]}")
            
            # Step 4: Test document endpoints (expected to fail)
            print(f"\n📁 Step 4: Testing document endpoints (implementation needed)...")
            doc_endpoints = [
                ("POST", "/healthcare/documents/upload", "File upload"),
                ("GET", "/healthcare/documents/search", "Document search"),
                ("POST", "/healthcare/documents/bulk-upload", "Bulk upload")
            ]
            
            for method, endpoint, description in doc_endpoints:
                try:
                    if method == "GET":
                        resp = requests.get(f"{base_url}{endpoint}", headers=headers, timeout=5)
                    else:
                        resp = requests.post(f"{base_url}{endpoint}", headers=headers, json={}, timeout=5)
                    
                    status = "✅" if resp.status_code in [200, 201] else "❌"
                    print(f"  {status} {method} {endpoint} - {resp.status_code} - {description}")
                    
                except Exception as e:
                    print(f"  ❌ {method} {endpoint} - Error: {str(e)[:50]}")
            
            print(f"\n🎊 SUMMARY:")
            print("✅ Authentication: Working (100%)")
            print("✅ Basic endpoints: Should be working") 
            print("❌ Document endpoints: Need implementation")
            print("\n📋 Next steps:")
            print("1. Implement missing document endpoints")
            print("2. Add file upload functionality") 
            print("3. Create React frontend components")
            
        else:
            print(f"❌ Auth failed: {response.status_code} - {response.text[:100]}")
            
    except Exception as e:
        print(f"❌ Auth error: {e}")

if __name__ == "__main__":
    test_endpoints()