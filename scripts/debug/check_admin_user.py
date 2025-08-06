#!/usr/bin/env python3
"""
Check if admin user exists and test authentication.
"""

import asyncio
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.abspath('.'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.modules.auth.service import auth_service
from app.modules.auth.schemas import UserLogin

async def check_admin_user():
    """Check if admin user exists and test authentication."""
    
    print("SECURITY TEST - Checking admin user")
    print("=" * 50)
    
    settings = get_settings()
    
    # Create database connection
    print(f"Connecting to database: {settings.DATABASE_URL}")
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as session:
            print("Database connection established")
            
            # Check if admin user exists
            print("\n1. Checking if admin user exists...")
            user_by_username = await auth_service.get_user_by_username("admin", session)
            user_by_email = await auth_service.get_user_by_email("admin", session)
            
            print(f"User found by username 'admin': {bool(user_by_username)}")
            print(f"User found by email 'admin': {bool(user_by_email)}")
            
            if user_by_username:
                user = user_by_username
                print(f"\nUser details:")
                print(f"  ID: {user.id}")
                print(f"  Username: {user.username}")
                print(f"  Email: {user.email}")
                print(f"  Role: {user.role}")
                print(f"  Active: {user.is_active}")
                print(f"  Email verified: {user.email_verified}")
                print(f"  Failed attempts: {user.failed_login_attempts}")
                print(f"  Locked until: {user.locked_until}")
                print(f"  Last login: {user.last_login_at}")
                
                # Test password verification
                print(f"\n2. Testing password verification...")
                from app.core.security import security_manager
                
                # Test the actual password
                password_correct = security_manager.verify_password("admin123", user.password_hash)
                print(f"Password 'admin123' is correct: {password_correct}")
                
                # Test authentication through service
                print(f"\n3. Testing full authentication...")
                login_data = UserLogin(username="admin", password="admin123")
                client_info = {
                    "ip_address": "127.0.0.1",
                    "user_agent": "TestScript/1.0",
                    "referer": None,
                    "request_id": "test-001"
                }
                
                auth_user = await auth_service.authenticate_user(login_data, session, client_info)
                
                if auth_user:
                    print("SUCCESS: Authentication passed!")
                    
                    # Test token creation
                    print(f"\n4. Testing token creation...")
                    token_data = await auth_service.create_access_token(auth_user)
                    print(f"Token creation successful: {bool(token_data.get('access_token'))}")
                    print(f"Access token length: {len(token_data.get('access_token', ''))}")
                    print(f"Refresh token length: {len(token_data.get('refresh_token', ''))}")
                    
                else:
                    print("FAILED: Authentication failed!")
                    
            else:
                print("\nNo admin user found!")
                
                # Let's check what users exist
                print("\nChecking existing users...")
                from sqlalchemy import select, text
                from app.core.database_unified import User
                
                # Get all users
                result = await session.execute(select(User).limit(10))
                users = result.scalars().all()
                
                print(f"Total users found: {len(users)}")
                for user in users:
                    print(f"  - {user.username} ({user.email}) - Role: {user.role} - Active: {user.is_active}")
    
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await engine.dispose()
        print("Database connection closed")

if __name__ == "__main__":
    asyncio.run(check_admin_user())