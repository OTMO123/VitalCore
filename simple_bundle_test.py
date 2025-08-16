#!/usr/bin/env python3

import asyncio
import json
import sys

sys.path.insert(0, '/mnt/c/Users/aurik/Code_Projects/2_scraper')

async def test_bundle():
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
                    username=f"test_admin_{test_id}",
                    role="system_admin",
                    email=f"test.admin.{test_id}@example.com",
                    password="TestPassword123!"
                )
                
                admin_headers = await auth_helper.get_headers(
                    f"test_admin_{test_id}", "TestPassword123!"
                )

                bundle = {
                    "resourceType": "Bundle",
                    "id": "test-bundle-001",
                    "type": "transaction",
                    "entry": [{
                        "fullUrl": "urn:uuid:patient-test-001",
                        "resource": {
                            "resourceType": "Patient",
                            "id": "patient-test-001",
                            "active": True,
                            "name": [{"use": "official", "family": "Test", "given": ["Patient"]}],
                            "gender": "unknown",
                            "birthDate": "1990-01-01"
                        },
                        "request": {"method": "POST", "url": "Patient"}
                    }]
                }
                
                from app.modules.healthcare_records.schemas import FHIRBundleRequest
                bundle_request = FHIRBundleRequest(bundle_type="transaction", bundle_data=bundle)
                
                response = await client.post(
                    "/api/v1/healthcare/fhir/bundle",
                    json=bundle_request.model_dump(),
                    headers=admin_headers
                )
                
                print(f"Status: {response.status_code}")
                if response.status_code != 200:
                    print(f"Response: {response.text}")
                else:
                    print("Success!")
                
                await auth_helper.cleanup()
            
            break
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_bundle())