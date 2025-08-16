#!/usr/bin/env python3
"""
Test to find exact problem by comparing local vs HTTP.
"""

import asyncio
import sys
import os
import urllib.request
import urllib.parse

# Add project root to Python path
sys.path.insert(0, os.path.abspath('.'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
from app.modules.auth.service import auth_service
from app.modules.auth.schemas import UserLogin

async def test_local_auth():
    """Test auth locally."""
    print("1. TESTING LOCAL AUTH")
    print("-" * 30)
    
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as session:
            login_data = UserLogin(username="admin", password="admin123")
            client_info = {
                "ip_address": "127.0.0.1",
                "user_agent": "TestScript/1.0",
                "referer": None,
                "request_id": "test-001"
            }
            
            # Test authentication
            user = await auth_service.authenticate_user(login_data, session, client_info)
            print(f"Local auth result: {bool(user)}")
            
            if user:
                print(f"  User: {user.username} (ID: {user.id})")
                print(f"  Role: {user.role} (value: {user.role.value})")
                
                # Test token creation
                try:
                    token_data = await auth_service.create_access_token(user)
                    print(f"  Token creation: SUCCESS")
                    print(f"  Access token: {bool(token_data.get('access_token'))}")
                    print(f"  Refresh token: {bool(token_data.get('refresh_token'))}")
                except Exception as e:
                    print(f"  Token creation: FAILED - {e}")
            else:
                print("  Local auth FAILED")
    
    except Exception as e:
        print(f"Local test error: {e}")
    finally:
        await engine.dispose()

def test_http_auth():
    """Test auth via HTTP."""
    print("\n2. TESTING HTTP AUTH")
    print("-" * 30)
    
    try:
        data = urllib.parse.urlencode({'username': 'admin', 'password': 'admin123'}).encode()
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'TestScript/1.0'
        }
        
        req = urllib.request.Request(
            "http://localhost:8000/api/v1/auth/login",
            data=data,
            headers=headers,
            method='POST'
        )
        
        print(f"HTTP request to: {req.full_url}")
        print(f"HTTP headers: {headers}")
        print(f"HTTP data: {data.decode()}")
        
        with urllib.request.urlopen(req) as response:
            login_data = response.read().decode()
            print(f"HTTP auth result: SUCCESS")
            print(f"  Status: {response.status}")
            print(f"  Response: {login_data}")
            
    except urllib.error.HTTPError as e:
        error_data = e.read().decode()
        print(f"HTTP auth result: FAILED")
        print(f"  Status: {e.status}")
        print(f"  Error: {error_data}")
        print(f"  Headers: {dict(e.headers)}")
    except Exception as e:
        print(f"HTTP test error: {e}")

def test_different_users():
    """Test if other users work."""
    print("\n3. TESTING OTHER USERS")
    print("-" * 30)
    
    test_users = [
        ("operator", "operator123"),
        ("viewer", "viewer123"),
        ("admin@example.com", "admin123"),  # Try email
        ("ADMIN", "admin123"),  # Try uppercase
    ]
    
    for username, password in test_users:
        try:
            data = urllib.parse.urlencode({'username': username, 'password': password}).encode()
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            
            req = urllib.request.Request(
                "http://localhost:8000/api/v1/auth/login",
                data=data,
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req) as response:
                print(f"  {username}: SUCCESS ({response.status})")
                
        except urllib.error.HTTPError as e:
            print(f"  {username}: FAILED ({e.status})")
        except Exception as e:
            print(f"  {username}: ERROR - {e}")

async def main():
    await test_local_auth()
    test_http_auth()
    test_different_users()

if __name__ == "__main__":
    asyncio.run(main())