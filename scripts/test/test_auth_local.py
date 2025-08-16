#!/usr/bin/env python3
"""
Direct local test of authentication without running server.
Tests the auth service directly for security debugging.
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

async def test_auth_service_directly():
    """Test auth service directly with comprehensive logging."""
    
    print("🔧 SECURITY TEST - DIRECT AUTH SERVICE TEST")
    print("=" * 60)
    
    settings = get_settings()
    
    # Create database connection
    print(f"📊 Connecting to database: {settings.DATABASE_URL}")
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as session:
            print("✅ Database connection established")
            
            # Create test login data
            login_data = UserLogin(username="admin", password="admin123")
            
            # Mock client info
            client_info = {
                "ip_address": "127.0.0.1",
                "user_agent": "SecurityTest/1.0",
                "referer": None,
                "request_id": "test-request-001"
            }
            
            print(f"🔑 Testing authentication for: {login_data.username}")
            print(f"🌐 Client info: {client_info}")
            
            # Test authentication
            user = await auth_service.authenticate_user(login_data, session, client_info)
            
            if user:
                print(f"✅ Authentication successful!")
                print(f"   User ID: {user.id}")
                print(f"   Username: {user.username}")
                print(f"   Role: {user.role}")
                print(f"   Active: {user.is_active}")
                print(f"   Email verified: {user.email_verified}")
                
                # Test token creation
                print(f"🎟️ Testing token creation...")
                token_data = await auth_service.create_access_token(user)
                
                print(f"✅ Token creation successful!")
                print(f"   Has access token: {bool(token_data.get('access_token'))}")
                print(f"   Has refresh token: {bool(token_data.get('refresh_token'))}")
                print(f"   Token type: {token_data.get('token_type')}")
                print(f"   Expires in: {token_data.get('expires_in')} seconds")
                
                if token_data.get('access_token'):
                    print(f"   Access token preview: {token_data['access_token'][:50]}...")
                if token_data.get('refresh_token'):
                    print(f"   Refresh token preview: {token_data['refresh_token'][:50]}...")
                
            else:
                print(f"❌ Authentication failed for user: {login_data.username}")
                
                # Check if user exists at all
                user_by_username = await auth_service.get_user_by_username(login_data.username, session)
                user_by_email = await auth_service.get_user_by_email(login_data.username, session)
                
                print(f"🔍 User lookup results:")
                print(f"   By username: {bool(user_by_username)}")
                print(f"   By email: {bool(user_by_email)}")
                
                if user_by_username:
                    print(f"   Found user: {user_by_username.username} (ID: {user_by_username.id})")
                    print(f"   User active: {user_by_username.is_active}")
                    print(f"   Failed attempts: {user_by_username.failed_login_attempts}")
                    print(f"   Locked until: {user_by_username.locked_until}")
    
    except Exception as e:
        print(f"💥 CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await engine.dispose()
        print("🔌 Database connection closed")

if __name__ == "__main__":
    asyncio.run(test_auth_service_directly())