#!/usr/bin/env python3
"""
Test API endpoints to understand what's working
"""

import requests
import json

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health: {response.status_code} - {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_login():
    """Test login"""
    try:
        response = requests.post(
            f"{API_BASE}/auth/login",
            data={"username": "admin", "password": "admin123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        print(f"Login: {response.status_code}")
        if response.status_code == 200:
            token = response.json()["access_token"]
            print(f"Got token: {token[:20]}...")
            return {"Authorization": f"Bearer {token}"}
        else:
            print(f"Login failed: {response.text}")
            return None
    except Exception as e:
        print(f"Login error: {e}")
        return None

def test_patients_get(auth_headers=None):
    """Test get patients endpoint"""
    try:
        headers = {}
        if auth_headers:
            headers.update(auth_headers)
        
        response = requests.get(f"{API_BASE}/healthcare/patients", headers=headers)
        print(f"Get patients: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Patients data: {json.dumps(data, indent=2)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Get patients error: {e}")

def test_simple_patient_create(auth_headers=None):
    """Test create patient with minimal data"""
    try:
        headers = {"Content-Type": "application/json"}
        if auth_headers:
            headers.update(auth_headers)
        
        # Minimal patient data
        patient = {
            "identifier": [
                {
                    "use": "official",
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                "code": "MR"
                            }
                        ]
                    },
                    "system": "http://test.hospital.org",
                    "value": "TEST001"
                }
            ],
            "name": [
                {
                    "use": "official",
                    "family": "TestPatient",
                    "given": ["John"]
                }
            ],
            "active": True,
            "birthDate": "1990-01-01",
            "gender": "male",
            "organization_id": "550e8400-e29b-41d4-a716-446655440000"
        }
        
        response = requests.post(f"{API_BASE}/healthcare/patients", json=patient, headers=headers)
        print(f"Create patient: {response.status_code}")
        if response.status_code in [200, 201]:
            print(f"Patient created: {response.json()}")
        else:
            print(f"Create error: {response.text}")
    except Exception as e:
        print(f"Create patient error: {e}")

def main():
    print("🔍 Testing API endpoints...")
    print("=" * 40)
    
    # Test health
    print("\n1. Health check:")
    if not test_health():
        print("❌ Backend not available")
        return
    
    # Test login
    print("\n2. Login test:")
    auth_headers = test_login()
    
    # Test get patients
    print("\n3. Get patients:")
    test_patients_get(auth_headers)
    
    # Test create simple patient
    print("\n4. Create simple patient:")
    test_simple_patient_create(auth_headers)
    
    # Test get patients again
    print("\n5. Get patients after creation:")
    test_patients_get(auth_headers)

if __name__ == "__main__":
    main()