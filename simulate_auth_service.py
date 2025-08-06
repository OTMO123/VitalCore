#!/usr/bin/env python3
"""
Simulate exactly what the authentication service does
"""
import asyncio
from app.core.database_unified import get_db
from app.modules.auth.service import AuthService
from app.modules.auth.schemas import UserLogin

async def simulate_auth_service():
    print("=== SIMULATING AUTH SERVICE FLOW ===")
    
    try:
        # Create auth service instance
        auth_service = AuthService()
        print("OK: AuthService created")
        
        # Create login data
        login_data = UserLogin(username="admin", password="admin123")
        print(f"OK: Login data: {login_data.username}")
        
        # Get database session
        async for db in get_db():
            print("OK: Database session obtained")
            
            # Call authenticate method directly
            client_info = {
                "ip_address": "127.0.0.1",
                "user_agent": "test-client",
                "request_id": "test-123"
            }
            
            print("Calling auth_service.authenticate()...")
            
            user = await auth_service.authenticate_user(login_data, db, client_info)
            
            if user:
                print(f"SUCCESS: Authentication returned user {user.username}")
                print(f"  User ID: {user.id}")
                print(f"  User Role: {user.role}")
            else:
                print("FAIL: Authentication returned None")
                print("  This matches the 401 response we're seeing")
            
            break  # Only use first db session
    
    except Exception as e:
        print(f"ERROR in auth service: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(simulate_auth_service())