#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database_unified import get_db
from app.modules.auth.service import auth_service
from app.modules.auth.schemas import UserLogin

async def test_api_direct():
    """Test the same path as the API uses"""
    
    # Get database session the same way API does
    async for db in get_db():
        try:
            print("🔍 Testing API path directly...")
            
            # Simulate OAuth2PasswordRequestForm data
            form_data = type('OAuth2Form', (), {
                'username': 'admin',
                'password': 'admin123'
            })()
            
            print(f"📝 Form data: username={form_data.username}, password=***")
            
            # Convert to UserLogin (same as router does)
            login_data = UserLogin(username=form_data.username, password=form_data.password)
            print(f"📝 Login data: username={login_data.username}")
            
            # Mock client info
            client_info = {"ip_address": "127.0.0.1", "user_agent": "test"}
            
            # Try authentication (same as router does)
            print("\n🔐 Attempting authentication...")
            user = await auth_service.authenticate_user(login_data, db, client_info)
            
            if not user:
                print("❌ Authentication failed - user is None")
                return
                
            print(f"✅ Authentication successful!")
            print(f"   User ID: {user.id}")
            print(f"   Username: {user.username}")
            print(f"   Role: {user.role}")
            print(f"   Role type: {type(user.role)}")
            
            # Try to create tokens (same as router does)
            print(f"\n🎫 Creating tokens...")
            token_data = await auth_service.create_access_token(user)
            print(f"✅ Tokens created successfully!")
            print(f"   Has access_token: {'access_token' in token_data}")
            print(f"   Has refresh_token: {'refresh_token' in token_data}")
            
            # Show what would be returned to client
            print(f"\n📤 API Response would be:")
            print(f"   access_token: {token_data.get('access_token', 'MISSING')[:50]}...")
            print(f"   refresh_token: {token_data.get('refresh_token', 'MISSING')[:50]}...")
            print(f"   token_type: {token_data.get('token_type', 'MISSING')}")
            print(f"   expires_in: {token_data.get('expires_in', 'MISSING')}")
            
        except Exception as e:
            print(f"💥 Error: {e}")
            import traceback
            traceback.print_exc()
        
        # Break after first iteration
        break

if __name__ == "__main__":
    asyncio.run(test_api_direct())