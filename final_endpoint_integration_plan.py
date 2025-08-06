#!/usr/bin/env python3
"""
Final Document Management Endpoint Integration Plan
Tests all available endpoints and provides React component integration plan
"""

import requests
import json

def test_comprehensive_endpoints():
    print("=" * 70)
    print("IRIS DOCUMENT MANAGEMENT - FINAL INTEGRATION PLAN")
    print("=" * 70)
    
    # Authenticate
    response = requests.post(
        "http://localhost:8003/api/v1/auth/login",
        data={"username": "admin", "password": "admin123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code != 200:
        print("ERROR: Authentication failed")
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("OK Authentication successful")
    print()
    
    # Test all endpoint categories
    endpoints = {
        "Document Management (Core)": [
            ("POST", "/api/v1/documents/upload", "File upload with form data"),
            ("GET", "/api/v1/documents/{document_id}/download", "Download document"),
            ("GET", "/api/v1/documents/{document_id}/versions", "Document version history"),
            ("GET", "/api/v1/documents/health", "Service health check"),
        ],
        
        "Document Processing": [
            ("POST", "/api/v1/documents/classify", "AI document classification"),
            ("POST", "/api/v1/documents/generate-filename", "Smart filename generation"),
        ],
        
        "Dashboard & Analytics": [
            ("GET", "/api/v1/dashboard/stats", "Main dashboard statistics"),
            ("GET", "/api/v1/analytics/dashboard", "Analytics overview"),
        ],
        
        "Patient Management": [
            ("GET", "/api/v1/healthcare/patients", "Patient list"),
            ("POST", "/api/v1/healthcare/patients", "Create patient"),
            ("GET", "/api/v1/healthcare/documents", "Healthcare documents"),
        ],
        
        "System Management": [
            ("GET", "/api/v1/iris/status", "IRIS API integration status"),
            ("GET", "/api/v1/purge/status", "Data purge scheduler status"),
            ("GET", "/api/v1/audit/logs", "System audit logs"),
        ],
        
        "Security & Auth": [
            ("GET", "/api/v1/auth/me", "Current user info"),
            ("POST", "/api/v1/auth/logout", "User logout"),
        ]
    }
    
    working_endpoints = {}
    
    for category, endpoint_list in endpoints.items():
        print(f"{category}:")
        print("-" * 50)
        
        working_endpoints[category] = []
        
        for method, endpoint, description in endpoint_list:
            # Replace placeholders for testing
            test_endpoint = endpoint.replace("{document_id}", "test-doc-id")
            
            try:
                if method == "GET":
                    response = requests.get(f"http://localhost:8003{test_endpoint}", headers=headers)
                elif method == "POST":
                    # Use appropriate test data for different endpoints
                    if "upload" in endpoint:
                        # Skip file upload test for now
                        print(f"SKIP {method} {endpoint} - {description} (file upload)")
                        continue
                    elif "patients" in endpoint:
                        test_data = {
                            "identifier": [{"value": "TEST123", "system": "MRN"}],
                            "name": [{"family": "Doe", "given": ["John"]}],
                            "organization_id": "test-org"
                        }
                        response = requests.post(f"http://localhost:8003{test_endpoint}", headers=headers, json=test_data)
                    else:
                        response = requests.post(f"http://localhost:8003{test_endpoint}", headers=headers, json={})
                
                status = "OK" if response.status_code < 400 else "ERROR"
                print(f"{status} {method} {endpoint} - {description}")
                print(f"     Status: {response.status_code}")
                
                if response.status_code < 400:
                    working_endpoints[category].append((method, endpoint, description, response.status_code))
                    
                    # Show sample response for key endpoints
                    if endpoint in ["/api/v1/dashboard/stats", "/api/v1/auth/me", "/api/v1/documents/health"]:
                        try:
                            data = response.json()
                            if isinstance(data, dict):
                                keys = list(data.keys())[:5]  # First 5 keys
                                print(f"     Response keys: {keys}")
                        except:
                            pass
                else:
                    try:
                        error_data = response.json()
                        print(f"     Error: {error_data.get('detail', 'Unknown error')}")
                    except:
                        print(f"     Error: {response.text[:100]}")
                
            except Exception as e:
                print(f"ERROR {method} {endpoint} - Connection error: {str(e)}")
            
            print()
        
        print()
    
    # Summary and Integration Plan
    print("=" * 70)
    print("REACT FRONTEND INTEGRATION SUMMARY")
    print("=" * 70)
    
    total_working = sum(len(endpoints) for endpoints in working_endpoints.values())
    
    print(f"Total working endpoints: {total_working}")
    print()
    
    print("RECOMMENDED INTEGRATION APPROACH:")
    print()
    
    print("1. IMMEDIATE IMPLEMENTATION (Working Endpoints):")
    for category, endpoint_list in working_endpoints.items():
        if endpoint_list:
            print(f"   {category}:")
            for method, endpoint, description, status in endpoint_list:
                print(f"     - {method} {endpoint}")
    
    print()
    print("2. REACT COMPONENT ARCHITECTURE WITH SHADCN:")
    print()
    
    components = {
        "Dashboard Components": [
            "DashboardStats - Uses /api/v1/dashboard/stats",
            "SystemHealth - Uses /api/v1/iris/status + /api/v1/purge/status",
            "UserProfile - Uses /api/v1/auth/me"
        ],
        
        "Document Management": [
            "DocumentUpload - Uses /api/v1/documents/upload (when working)",
            "DocumentHealth - Uses /api/v1/documents/health",
            "DocumentVersions - Uses /api/v1/documents/{id}/versions"
        ],
        
        "Patient Management": [
            "PatientList - Needs /api/v1/healthcare/patients fix",
            "PatientCreate - Needs schema correction",
            "DocumentHistory - Needs patient-document endpoint"
        ]
    }
    
    for component_type, component_list in components.items():
        print(f"   {component_type}:")
        for component in component_list:
            print(f"     - {component}")
        print()
    
    print("3. NEXT DEVELOPMENT STEPS:")
    print("   a) Fix broken patient endpoints (schema issues)")
    print("   b) Implement missing document search endpoints")  
    print("   c) Add bulk operations endpoints")
    print("   d) Test file upload with proper form data")
    print("   e) Install and configure Shadcn UI components")
    print()
    
    print("4. SHADCN COMPONENTS TO INSTALL:")
    print("   npx shadcn-ui@latest add button card table badge alert")
    print("   npx shadcn-ui@latest add dialog form input progress toast")
    print("   npx shadcn-ui@latest add select dropdown-menu pagination")
    print()
    
    print("5. PRIORITY ORDER:")
    print("   1. Dashboard (working endpoints)")
    print("   2. Document health monitoring (working)")
    print("   3. User authentication UI (working)")
    print("   4. Fix patient endpoints")
    print("   5. Implement file upload UI")
    print("   6. Add search and bulk operations")

if __name__ == "__main__":
    test_comprehensive_endpoints()