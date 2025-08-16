#!/usr/bin/env python3

import asyncio
import json
import sys

sys.path.insert(0, '/mnt/c/Users/aurik/Code_Projects/2_scraper')

async def test_simple_immunization():
    try:
        from httpx import AsyncClient, ASGITransport
        from app.main import app
        from app.core.database_unified import get_db
        from app.tests.helpers.auth_helpers import AuthTestHelper

        async for db_session in get_db():
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                auth_helper = AuthTestHelper(db_session, client)
                
                import uuid
                test_id = str(uuid.uuid4())[:8]
                
                admin_user = await auth_helper.create_user(
                    username=f"imm_admin_{test_id}",
                    role="system_admin",
                    email=f"imm.admin.{test_id}@example.com",
                    password="TestPassword123!"
                )
                
                admin_headers = await auth_helper.get_headers(
                    f"imm_admin_{test_id}", "TestPassword123!"
                )

                # First create a simple patient
                patient_bundle = {
                    "resourceType": "Bundle",
                    "id": "patient-only-bundle",
                    "type": "transaction",
                    "entry": [{
                        "fullUrl": "urn:uuid:patient-001",
                        "resource": {
                            "resourceType": "Patient",
                            "id": "patient-simple-001",
                            "active": True,
                            "name": [{"use": "official", "family": "SimpleTest", "given": ["Patient"]}],
                            "gender": "unknown",
                            "birthDate": "1990-01-01"
                        },
                        "request": {"method": "POST", "url": "Patient"}
                    }]
                }
                
                from app.modules.healthcare_records.schemas import FHIRBundleRequest
                patient_request = FHIRBundleRequest(bundle_type="transaction", bundle_data=patient_bundle)
                
                patient_response = await client.post(
                    "/api/v1/healthcare/fhir/bundle",
                    json=patient_request.model_dump(),
                    headers=admin_headers
                )
                
                print(f"Patient Bundle Status: {patient_response.status_code}")
                if patient_response.status_code == 200:
                    print("Patient creation successful!")
                    
                    # Now try just immunization without reference
                    imm_bundle = {
                        "resourceType": "Bundle", 
                        "id": "imm-only-bundle",
                        "type": "transaction",
                        "entry": [{
                            "fullUrl": "urn:uuid:imm-001",
                            "resource": {
                                "resourceType": "Immunization",
                                "id": "imm-simple-001",
                                "status": "completed",
                                "vaccineCode": {
                                    "coding": [{
                                        "system": "http://hl7.org/fhir/sid/cvx",
                                        "code": "140",
                                        "display": "Influenza, seasonal, injectable"
                                    }]
                                },
                                "occurrenceDateTime": "2023-10-15",  # Simple date without timezone
                                "primarySource": True
                            },
                            "request": {"method": "POST", "url": "Immunization"}
                        }]
                    }
                    
                    imm_request = FHIRBundleRequest(bundle_type="transaction", bundle_data=imm_bundle)
                    
                    imm_response = await client.post(
                        "/api/v1/healthcare/fhir/bundle",
                        json=imm_request.model_dump(),
                        headers=admin_headers
                    )
                    
                    print(f"Immunization Bundle Status: {imm_response.status_code}")
                    if imm_response.status_code != 200:
                        print(f"Immunization Error: {imm_response.text}")
                
                await auth_helper.cleanup()
            
            break
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simple_immunization())