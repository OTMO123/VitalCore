#!/usr/bin/env python3
"""
Test existing endpoints to see what's available for frontend integration
"""

import requests
import json

def test_all_endpoints():
    # Authenticate first
    response = requests.post(
        "http://localhost:8003/api/v1/auth/login",
        data={"username": "admin", "password": "admin123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code != 200:
        print("Authentication failed")
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test common endpoint patterns
    endpoints = [
        # Health and status
        ("GET", "/health"),
        ("GET", "/api/v1/health"),
        
        # Auth endpoints
        ("GET", "/api/v1/auth/me"),
        
        # Patient endpoints
        ("GET", "/api/v1/patients"),
        ("GET", "/api/v1/healthcare-records/patients"),
        
        # Document management
        ("GET", "/api/v1/document-management"),
        ("GET", "/api/v1/document_management"),
        ("GET", "/api/v1/documents"),
        
        # Dashboard endpoints
        ("GET", "/api/v1/dashboard"),
        ("GET", "/api/v1/dashboard/metrics"),
        ("GET", "/api/v1/dashboard/stats"),
        
        # Analytics
        ("GET", "/api/v1/analytics"),
        ("GET", "/api/v1/analytics/dashboard"),
        
        # Audit logs
        ("GET", "/api/v1/audit"),
        ("GET", "/api/v1/audit-logger"),
        ("GET", "/api/v1/audit_logger"),
        
        # IRIS API
        ("GET", "/api/v1/iris"),
        ("GET", "/api/v1/iris-api"),
        ("GET", "/api/v1/iris_api"),
        
        # Risk stratification
        ("GET", "/api/v1/risk"),
        ("GET", "/api/v1/risk-stratification"),
        
        # Purge scheduler
        ("GET", "/api/v1/purge"),
        ("GET", "/api/v1/purge-scheduler"),
    ]
    
    print("TESTING EXISTING ENDPOINTS")
    print("=" * 50)
    
    working_endpoints = []
    
    for method, endpoint in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"http://localhost:8003{endpoint}", headers=headers)
            elif method == "POST":
                response = requests.post(f"http://localhost:8003{endpoint}", headers=headers, json={})
            
            status = "OK" if response.status_code < 400 else "ERROR"
            print(f"{status} {method} {endpoint} -> {response.status_code}")
            
            if response.status_code < 400:
                working_endpoints.append((method, endpoint, response.status_code))
                
                # Try to show response keys if JSON
                try:
                    data = response.json()
                    if isinstance(data, dict):
                        print(f"      Response keys: {list(data.keys())}")
                    elif isinstance(data, list):
                        print(f"      Items count: {len(data)}")
                except:
                    pass
            
        except Exception as e:
            print(f"ERROR {method} {endpoint} -> {str(e)}")
    
    print("\n" + "=" * 50)
    print("WORKING ENDPOINTS SUMMARY:")
    print("=" * 50)
    
    for method, endpoint, status in working_endpoints:
        print(f"{method} {endpoint} ({status})")
    
    print(f"\nTotal working endpoints: {len(working_endpoints)}")

if __name__ == "__main__":
    test_all_endpoints()