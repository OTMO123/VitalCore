#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import get_db
from app.modules.auth.service import auth_service
from app.modules.auth.schemas import UserLogin

async def debug_login():
    """Debug the login process step by step"""
    
    # Get database session
    async for db in get_db():
        try:
            print("🔍 Starting login debug...")
            
            login_data = UserLogin(username="admin", password="admin123")
            print(f"📝 Login data: username={login_data.username}, password=***")
            
            # Step 1: Try to find user by username
            print("\n1️⃣ Looking for user by username...")
            user = await auth_service.get_user_by_username(login_data.username, db)
            
            if user:
                print(f"✅ User found: {user.username} (ID: {user.id})")
                print(f"   Role: {user.role}")
                print(f"   Active: {user.is_active}")
                print(f"   Password hash: {user.password_hash[:50]}...")
            else:
                print("❌ User not found by username")
                
                # Try by email
                print("\n2️⃣ Looking for user by email...")
                user = await auth_service.get_user_by_email(login_data.username, db)
                if user:
                    print(f"✅ User found by email: {user.username}")
                else:
                    print("❌ User not found by email either")
                    return
            
            # Step 2: Check if account is locked
            print(f"\n3️⃣ Checking account lock status...")
            if user.locked_until:
                print(f"🔒 Account locked until: {user.locked_until}")
            else:
                print("🔓 Account not locked")
            
            # Step 3: Verify password
            print(f"\n4️⃣ Verifying password...")
            try:
                is_valid = auth_service.security.verify_password(login_data.password, user.password_hash)
                print(f"🔑 Password valid: {is_valid}")
            except Exception as e:
                print(f"❌ Password verification error: {e}")
                return
            
            # Step 4: Check if user is active
            print(f"\n5️⃣ Checking if user is active...")
            print(f"👤 User active: {user.is_active}")
            
            # Step 5: Try full authentication
            print(f"\n6️⃣ Attempting full authentication...")
            client_info = {"ip_address": "127.0.0.1", "user_agent": "test"}
            
            authenticated_user = await auth_service.authenticate_user(login_data, db, client_info)
            
            if authenticated_user:
                print(f"✅ Authentication successful!")
                print(f"   User ID: {authenticated_user.id}")
                print(f"   Username: {authenticated_user.username}")
                print(f"   Role: {authenticated_user.role}")
                
                # Step 6: Try to create tokens
                print(f"\n7️⃣ Creating access tokens...")
                token_data = await auth_service.create_access_token(authenticated_user)
                print(f"✅ Tokens created successfully!")
                print(f"   Has access_token: {'access_token' in token_data}")
                print(f"   Has refresh_token: {'refresh_token' in token_data}")
                
                if 'access_token' in token_data:
                    print(f"   Access token: {token_data['access_token'][:50]}...")
                if 'refresh_token' in token_data:
                    print(f"   Refresh token: {token_data['refresh_token'][:50]}...")
                    
            else:
                print(f"❌ Authentication failed")
            
        except Exception as e:
            print(f"💥 Unexpected error: {e}")
            import traceback
            traceback.print_exc()
        
        # Break after first iteration since get_db yields one session
        break

if __name__ == "__main__":
    asyncio.run(debug_login())