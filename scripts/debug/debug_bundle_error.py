#!/usr/bin/env python3

import asyncio
import json
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, '/mnt/c/Users/aurik/Code_Projects/2_scraper')

async def debug_bundle_error():
    """Debug the FHIR bundle processing error by calling the endpoint directly."""
    
    try:
        # Import after path setup
        import httpx
        from httpx import AsyncClient, ASGITransport
        from sqlalchemy.ext.asyncio import AsyncSession
        from app.main import app
        from app.core.database_unified import get_db
        from app.tests.helpers.auth_helpers import AuthTestHelper
        
        print("Starting FHIR bundle debug...")
        
        # Create async database session
        async for db_session in get_db():
            print("Database session created")
            
            # Set up test environment
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                auth_helper = AuthTestHelper(db_session, client)
                
                # Create test user
                import uuid
                test_id = str(uuid.uuid4())[:8]
                
                print(f"Creating test user with ID: {test_id}")
                
                try:
                    admin_user = await auth_helper.create_user(
                        username=f"debug_admin_{test_id}",
                        role="system_admin", 
                        email=f"debug.admin.{test_id}@example.com",
                        password="DebugPassword123!"
                    )
                    print(f"Test user created: {admin_user.id}")
                    
                    # Get auth headers
                    admin_headers = await auth_helper.get_headers(
                        f"debug_admin_{test_id}", "DebugPassword123!"
                    )
                    print("Authentication headers obtained")
                    
                    # Create simple transaction bundle (same as test)
                    transaction_bundle = {
                        "resourceType": "Bundle",
                        "id": "debug-transaction-bundle-001",
                        "type": "transaction",
                        "entry": [
                            {
                                "fullUrl": "urn:uuid:patient-debug-001",
                                "resource": {
                                    "resourceType": "Patient",
                                    "id": "patient-debug-001",
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
                    
                    # Create bundle request
                    from app.modules.healthcare_records.schemas import FHIRBundleRequest
                    bundle_request = FHIRBundleRequest(
                        bundle_type="transaction",
                        bundle_data=transaction_bundle
                    )
                    
                    print("Bundle request created, sending to API...")
                    print(f"Bundle data keys: {list(bundle_request.bundle_data.keys())}")
                    print(f"Entry count: {len(bundle_request.bundle_data.get('entry', []))}")
                    
                    # Make the request
                    response = await client.post(
                        "/api/v1/healthcare/fhir/bundle",
                        json=bundle_request.model_dump(),
                        headers=admin_headers
                    )
                    
                    print(f"\nResponse Status: {response.status_code}")
                    print(f"Response Headers: {dict(response.headers)}")
                    
                    try:
                        response_data = response.json()
                        print(f"Response Data: {json.dumps(response_data, indent=2)}")
                    except Exception as json_error:
                        print(f"Response Text (not JSON): {response.text}")
                        print(f"JSON parse error: {json_error}")
                    
                    # Cleanup
                    await auth_helper.cleanup()
                    
                except Exception as user_error:
                    print(f"User creation/auth error: {user_error}")
                    import traceback
                    print(f"Traceback: {traceback.format_exc()}")
                    
            break  # Exit the async generator loop
            
    except Exception as e:
        print(f"Debug error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    print("FHIR Bundle Error Debug Script")
    print("=" * 50)
    asyncio.run(debug_bundle_error())