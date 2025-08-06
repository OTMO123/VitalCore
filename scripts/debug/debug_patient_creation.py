#!/usr/bin/env python3
"""
Debug patient creation endpoint directly.
"""

import asyncio
import json
from datetime import date
from fastapi.testclient import TestClient
from app.main import app

# Test data in correct FHIR format
test_patient_data = {
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
            "system": "http://hospital.example.org/patients", 
            "value": "MRN-001"
        }
    ],
    "name": [
        {
            "use": "official",
            "family": "Doe",
            "given": ["John"]
        }
    ],
    "telecom": [
        {
            "system": "phone",
            "value": "(555) 123-4567",
            "use": "home"
        },
        {
            "system": "email", 
            "value": "john.doe@example.com",
            "use": "home"
        }
    ],
    "gender": "male",
    "birthDate": "1990-01-15",
    "address": [
        {
            "use": "home",
            "line": ["123 Main St"],
            "city": "Anytown",
            "state": "CA", 
            "postalCode": "12345",
            "country": "US"
        }
    ],
    "active": True,
    "organization_id": "c4c4fec4-c63a-49d1-a5c7-07495c4740b0",
    "consent_status": "pending",
    "consent_types": ["treatment"]
}

def test_patient_creation():
    """Test patient creation with detailed error reporting."""
    print("🧪 TESTING PATIENT CREATION DIRECTLY")
    print("=" * 50)
    
    # Create test client
    client = TestClient(app)
    
    # Login first
    print("1. Logging in...")
    login_response = client.post(
        "/api/v1/auth/login",
        data="username=admin&password=admin123",
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(f"Response: {login_response.text}")
        return
    
    token = login_response.json()["access_token"]
    print("✅ Login successful")
    
    # Test patient creation
    print("\n2. Creating patient...")
    print(f"Data: {json.dumps(test_patient_data, indent=2)}")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = client.post(
            "/api/v1/healthcare/patients",
            json=test_patient_data,
            headers=headers
        )
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 201:
            print("✅ Patient created successfully!")
            patient = response.json()
            print(f"Patient ID: {patient.get('id')}")
        else:
            print(f"❌ Patient creation failed!")
            
    except Exception as e:
        print(f"❌ Exception during request: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_patient_creation()