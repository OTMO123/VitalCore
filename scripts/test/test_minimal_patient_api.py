#!/usr/bin/env python3
"""
Test minimal patient creation via API
"""

import requests
import json

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def test_minimal_patient():
    """Test creating a minimal patient via API"""
    print("🧪 Testing minimal patient creation via API...")
    
    # Login first
    try:
        response = requests.post(
            f"{API_BASE}/auth/login",
            data={"username": "admin", "password": "admin123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code}")
            return False
            
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
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
                    "value": "MINIMAL001"
                }
            ],
            "name": [
                {
                    "use": "official",
                    "family": "TestMinimal",
                    "given": ["Patient"]
                }
            ],
            "active": True,
            "gender": "unknown",
            "birthDate": "1990-01-01"
        }
        
        response = requests.post(f"{API_BASE}/healthcare/patients", json=patient, headers=headers)
        print(f"Create patient: {response.status_code}")
        
        if response.status_code in [200, 201]:
            print(f"✅ Patient created: {response.json()}")
            return True
        else:
            print(f"❌ Create error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_minimal_patient()