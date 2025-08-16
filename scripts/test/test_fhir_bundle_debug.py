#!/usr/bin/env python3
"""
Debug FHIR Bundle Processing - Direct API Test
"""
import asyncio
import json
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from httpx import AsyncClient, ASGITransport

async def test_fhir_bundle():
    """Test FHIR bundle processing directly."""
    
    from app.main import app
    from app.tests.helpers.auth_helpers import create_test_user, get_auth_headers
    from app.core.database_unified import get_db
    
    # Set up test environment
    transport = ASGITransport(app=app)
    
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Get database session
        async for db_session in get_db():
            try:
                # 1. Create test user
                import uuid
                test_id = str(uuid.uuid4())[:8]
                username = f"fhir_debug_user_{test_id}"
                email = f"fhir.debug.{test_id}@example.com"
                print(f"1. Creating test user: {username}...")
                user = await create_test_user(
                    db_session=db_session,
                    username=username,
                    role="system_admin",
                    email=email,
                    password="DebugPassword123!"
                )
                print(f"   User created: {user.id} - {user.username}")
                
                # 2. Get authentication headers
                print("2. Getting authentication...")
                try:
                    auth_headers = await get_auth_headers(
                        client, username, "DebugPassword123!"
                    )
                    print("   Authentication successful!")
                except Exception as auth_error:
                    print(f"   Authentication failed: {auth_error}")
                    return
                
                # 3. Create FHIR bundle request - exactly matching the working test
                print("3. Creating FHIR bundle...")
                bundle_data = {
                    "resourceType": "Bundle",
                    "id": str(uuid.uuid4()),  # Use valid UUID format
                    "type": "transaction",
                    "entry": [
                        {
                            "fullUrl": f"urn:uuid:{str(uuid.uuid4())}",
                            "resource": {
                                "resourceType": "Patient",
                                "id": str(uuid.uuid4()),  # Use valid UUID format
                                "active": True,
                                "name": [{
                                    "use": "official",
                                    "family": "DebugTest",
                                    "given": ["Bundle"]
                                }],
                                "gender": "unknown",
                                "birthDate": "1990-01-01"
                            },
                            "request": {
                                "method": "POST",
                                "url": "Patient"
                            }
                        }
                    ]
                }
                
                from app.modules.healthcare_records.schemas import FHIRBundleRequest
                bundle_request = FHIRBundleRequest(
                    bundle_type="transaction",
                    bundle_data=bundle_data
                )
                
                # 4. Send FHIR bundle request
                print("4. Sending FHIR bundle request...")
                response = await client.post(
                    "/api/v1/healthcare/fhir/bundle",
                    json=bundle_request.model_dump(),
                    headers=auth_headers
                )
                
                print(f"   Response status: {response.status_code}")
                print(f"   Response headers: {dict(response.headers)}")
                
                if response.status_code >= 400:
                    print(f"   ERROR Response body: {response.text}")
                else:
                    response_data = response.json()
                    print(f"   SUCCESS Response: {json.dumps(response_data, indent=2)}")
                
            finally:
                await db_session.close()

if __name__ == "__main__":
    asyncio.run(test_fhir_bundle())