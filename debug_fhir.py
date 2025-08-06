#!/usr/bin/env python3

import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.modules.healthcare_records.schemas import FHIRValidationRequest

async def debug_fhir_validation():
    patient_resource = {
        "resourceType": "Patient",
        "id": "patient-001",
        "active": True,
        "identifier": [{
            "use": "official",
            "type": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                    "code": "MR"
                }]
            },
            "system": "http://hospital.example.org",
            "value": "MRN123456"
        }],
        "name": [{
            "use": "official",
            "family": "TestPatient",
            "given": ["John", "William"]
        }],
        "gender": "male",
        "birthDate": "1990-01-01"
    }
    
    validation_request = FHIRValidationRequest(resource=patient_resource)
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Login
        login_response = await client.post("/api/v1/auth/login", 
                                         json={"username": "admin", "password": "admin123"})
        if login_response.status_code != 200:
            print(f"Login failed: {login_response.status_code} - {login_response.text}")
            return
            
        token_data = login_response.json()
        headers = {"Authorization": f"Bearer {token_data['access_token']}", "Content-Type": "application/json"}
        
        response = await client.post(
            "/api/v1/healthcare/fhir/validate",
            json=validation_request.model_dump(),
            headers=headers
        )
        
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Valid: {result.get('valid')}")
        print(f"Resource Type: {result.get('resource_type')}")
        print(f"Issues: {result.get('issues', [])}")
        for i, issue in enumerate(result.get('issues', [])):
            print(f"  Issue {i+1}: {issue}")
        print(f"Full Response: {result}")

if __name__ == "__main__":
    asyncio.run(debug_fhir_validation())