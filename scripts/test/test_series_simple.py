#!/usr/bin/env python3
"""
Simple test to validate series_complete field fix.
"""
import asyncio
import json
import httpx

# Test FHIR Bundle with series fields
TEST_BUNDLE = {
    "resourceType": "Bundle",
    "id": "series-test-001",
    "type": "transaction",
    "entry": [
        {
            "fullUrl": "urn:uuid:patient-001",
            "resource": {
                "resourceType": "Patient",
                "id": "patient-001",
                "identifier": [{"value": "TEST-SERIES-001"}],
                "name": [{"family": "Test", "given": ["Series"]}],
                "gender": "male",
                "birthDate": "1990-01-01",
                "active": True
            },
            "request": {"method": "POST", "url": "Patient"}
        },
        {
            "fullUrl": "urn:uuid:immunization-001",
            "resource": {
                "resourceType": "Immunization",
                "status": "completed",
                "vaccineCode": {
                    "coding": [{
                        "system": "http://hl7.org/fhir/sid/cvx",
                        "code": "140",
                        "display": "Influenza, seasonal, injectable"
                    }]
                },
                "patient": {"reference": "urn:uuid:patient-001"},
                "occurrenceDateTime": "2023-10-15T10:00:00+00:00",
                "primarySource": True,
                "series_complete": False,
                "series_dosed": 1
            },
            "request": {"method": "POST", "url": "Immunization"}
        }
    ]
}

async def test_bundle():
    """Test bundle processing."""
    print("Testing FHIR Bundle with series_complete fields...")
    
    try:
        async with httpx.AsyncClient(base_url="http://localhost:8001", timeout=15.0) as client:
            # Try to authenticate
            auth_response = await client.post("/api/v1/auth/login", json={
                "username": "healthcareadmin", 
                "password": "HealthcareAdmin2024!"
            })
            
            if auth_response.status_code != 200:
                print(f"❌ Auth failed: {auth_response.status_code}")
                return
                
            token = auth_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test bundle
            response = await client.post(
                "/api/v1/healthcare/fhir/bundle",
                json=TEST_BUNDLE,
                headers=headers
            )
            
            print(f"Bundle Status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                print("✅ SUCCESS: Series fields fix working!")
            else:
                error_data = response.json()
                error_text = str(error_data)
                
                if "series_complete" in error_text and "not-null" in error_text:
                    print("❌ STILL FAILING: series_complete constraint not resolved")
                    print("Need to add database column manually")
                else:
                    print(f"❌ Other error: {response.status_code}")
                    print(json.dumps(error_data, indent=2))
                    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_bundle())