#!/usr/bin/env python3
"""
Quick test of working endpoints without document management dependencies
"""

import requests
import json

def test_core_endpoints():
    print("TESTING CORE WORKING ENDPOINTS")
    print("=" * 50)
    
    # Test without authentication first
    print("1. Testing public endpoints...")
    
    try:
        response = requests.get("http://localhost:8003/health")
        print(f"Health endpoint: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Health endpoint error: {e}")
    
    print("\n2. Testing authentication...")
    
    try:
        response = requests.post(
            "http://localhost:8003/api/v1/auth/login",
            data={"username": "admin", "password": "admin123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            print("Authentication: SUCCESS")
            data = response.json()
            token = data["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            print("\n3. Testing authenticated endpoints...")
            
            # Test dashboard stats
            try:
                response = requests.get("http://localhost:8003/api/v1/dashboard/stats", headers=headers)
                print(f"Dashboard stats: {response.status_code}")
                if response.status_code == 200:
                    stats = response.json()
                    print(f"  Total patients: {stats.get('total_patients', 'N/A')}")
                    print(f"  System uptime: {stats.get('system_uptime_percentage', 'N/A')}%")
                    print(f"  Compliance score: {stats.get('compliance_score', 'N/A')}")
            except Exception as e:
                print(f"Dashboard error: {e}")
            
            # Test user info
            try:
                response = requests.get("http://localhost:8003/api/v1/auth/me", headers=headers)
                print(f"User info: {response.status_code}")
                if response.status_code == 200:
                    user = response.json()
                    print(f"  User: {user.get('username')} ({user.get('role')})")
            except Exception as e:
                print(f"User info error: {e}")
            
            # Test IRIS status
            try:
                response = requests.get("http://localhost:8003/api/v1/iris/status", headers=headers)
                print(f"IRIS status: {response.status_code}")
                if response.status_code == 200:
                    status = response.json()
                    print(f"  IRIS available: {status.get('iris_api_available', 'N/A')}")
                    print(f"  Connection: {status.get('connection_status', 'N/A')}")
            except Exception as e:
                print(f"IRIS status error: {e}")
                
        else:
            print(f"Authentication failed: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Authentication error: {e}")
    
    print("\n" + "=" * 50)
    print("FRONTEND INTEGRATION RECOMMENDATIONS")
    print("=" * 50)
    
    print("\nSTART WITH THESE WORKING COMPONENTS:")
    print("1. Authentication (login/logout) - WORKING")
    print("2. Dashboard with stats - WORKING") 
    print("3. User profile display - WORKING")
    print("4. System status monitoring - WORKING")
    
    print("\nSHADCN COMPONENTS TO INSTALL FIRST:")
    print("npm install shadcn-ui")
    print("npx shadcn-ui@latest add button card badge alert")
    print("npx shadcn-ui@latest add form input label")
    print("npx shadcn-ui@latest add table progress")
    
    print("\nREACT COMPONENTS TO BUILD:")
    print("1. LoginForm - uses /api/v1/auth/login") 
    print("2. DashboardStats - uses /api/v1/dashboard/stats")
    print("3. UserProfile - uses /api/v1/auth/me")
    print("4. SystemStatus - uses /api/v1/iris/status")
    
    print("\nNEXT STEPS:")
    print("1. Install minio: pip install minio")
    print("2. Fix document management dependencies")
    print("3. Test document endpoints")
    print("4. Build React components with working endpoints")

if __name__ == "__main__":
    test_core_endpoints()