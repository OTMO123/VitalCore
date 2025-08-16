#!/usr/bin/env python3
"""
Test working endpoints for frontend integration planning
"""

import requests
import json

def test_working_endpoints():
    # Authenticate
    response = requests.post(
        "http://localhost:8003/api/v1/auth/login",
        data={"username": "admin", "password": "admin123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("TESTING WORKING ENDPOINTS FOR FRONTEND INTEGRATION")
    print("=" * 60)
    
    # Test endpoints that should work based on main.py
    endpoints = [
        # Dashboard endpoints
        ("GET", "/api/v1/dashboard/stats", "Dashboard stats for main page"),
        
        # Healthcare/Patient endpoints
        ("GET", "/api/v1/healthcare/patients", "Patient list"),
        ("POST", "/api/v1/healthcare/patients", "Create patient", {
            "mrn": "TEST123",
            "first_name": "Test",
            "last_name": "Patient",
            "date_of_birth": "1990-01-01",
            "gender": "M"
        }),
        
        # IRIS API endpoints
        ("GET", "/api/v1/iris/status", "IRIS integration status"),
        
        # Audit endpoints
        ("GET", "/api/v1/audit/logs", "Audit logs"),
        
        # Analytics endpoints
        ("GET", "/api/v1/analytics/dashboard", "Analytics dashboard"),
        
        # Risk stratification
        ("GET", "/api/v1/patients/risk/stratification", "Risk stratification"),
        
        # Purge scheduler
        ("GET", "/api/v1/purge/status", "Purge scheduler status"),
    ]
    
    working_endpoints = []
    for method, endpoint, description, *data in endpoints:
        try:
            payload = data[0] if data else None
            
            if method == "GET":
                response = requests.get(f"http://localhost:8003{endpoint}", headers=headers)
            elif method == "POST":
                response = requests.post(f"http://localhost:8003{endpoint}", headers=headers, json=payload)
            
            status = "OK" if response.status_code < 400 else "ERROR"
            print(f"{status} {method} {endpoint}")
            print(f"    {description}")
            print(f"    Status: {response.status_code}")
            
            if response.status_code < 400:
                working_endpoints.append((method, endpoint, description))
                try:
                    data = response.json()
                    if isinstance(data, dict) and len(data) < 10:
                        print(f"    Response: {data}")
                    elif isinstance(data, dict):
                        print(f"    Response keys: {list(data.keys())}")
                    elif isinstance(data, list):
                        print(f"    Items: {len(data)}")
                except:
                    print(f"    Response length: {len(response.text)}")
            else:
                print(f"    Error: {response.text}")
            print()
            
        except Exception as e:
            print(f"ERROR {method} {endpoint} - {str(e)}\n")
    
    print("=" * 60)
    print("FRONTEND INTEGRATION PLAN")
    print("=" * 60)
    
    if working_endpoints:
        print("WORKING ENDPOINTS TO USE:")
        for method, endpoint, description in working_endpoints:
            print(f"  {method} {endpoint} - {description}")
        
        print(f"\nNext steps:")
        print("1. Update React components to use these working endpoints")
        print("2. Add document management router if needed")
        print("3. Test frontend integration with working endpoints")
    else:
        print("No working endpoints found - need to investigate routing")
    
    # Test document management module exists
    print("\n" + "=" * 60)
    print("DOCUMENT MANAGEMENT MODULE CHECK")
    print("=" * 60)
    
    # Check if document management endpoints exist in any form
    doc_endpoints = [
        "/api/v1/document-management",
        "/api/v1/documents", 
        "/api/v1/healthcare/documents",
        "/api/v1/iris/documents"
    ]
    
    for endpoint in doc_endpoints:
        try:
            response = requests.get(f"http://localhost:8003{endpoint}", headers=headers)
            if response.status_code != 404:
                print(f"FOUND: {endpoint} -> {response.status_code}")
            else:
                print(f"Missing: {endpoint}")
        except:
            print(f"Error testing: {endpoint}")

if __name__ == "__main__":
    test_working_endpoints()