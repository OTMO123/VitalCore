#!/usr/bin/env python3
"""
Create test users for authentication testing.
"""
import asyncio
import sys
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Suppress SQLAlchemy logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

from app.core.database import get_db, User
from app.core.security import get_password_hash
from app.modules.auth.schemas import UserCreate
from app.modules.auth.service import AuthService

async def create_test_users():
    """Create test users if they don't exist."""
    print("Creating test users for authentication...")
    auth_service = AuthService()
    
    # Define test users
    test_users = [
        {
            "username": "testuser",
            "email": "test@example.com", 
            "password": "testpassword",
            "role": "user"
        },
        {
            "username": "testpassword123",  # Some tests might expect this
            "email": "test123@example.com",
            "password": "testpassword123", 
            "role": "user"
        },
        {
            "username": "admin",
            "email": "admin@example.com",
            "password": "testpassword123",
            "role": "admin"
        },
        {
            "username": "super_admin",
            "email": "superadmin@example.com", 
            "password": "testpassword123",
            "role": "super_admin"
        }
    ]
    
    async for session in get_db():
        try:
            created_count = 0
            for user_data in test_users:
                # Check if user exists
                result = await session.execute(
                    select(User).where(User.username == user_data["username"])
                )
                existing_user = result.scalar_one_or_none()
                
                if not existing_user:
                    # Create user directly (bypass auth service validation)
                    hashed_password = get_password_hash(user_data["password"])
                    user = User(
                        username=user_data["username"],
                        email=user_data["email"], 
                        hashed_password=hashed_password,
                        role=user_data["role"],
                        is_active=True,
                        is_verified=True
                    )
                    session.add(user)
                    created_count += 1
                    print(f"[+] Created user: {user_data['username']} ({user_data['role']})")
                else:
                    print(f"- User already exists: {user_data['username']}")
            
            if created_count > 0:
                await session.commit()
                print(f"\n[SUCCESS] Successfully created {created_count} test users")
            else:
                print("\n[SUCCESS] All test users already exist")
                
        except Exception as e:
            print(f"[ERROR] Error creating test users: {e}")
            await session.rollback()
            return False
        finally:
            break  # Exit the async generator
            
    return True

if __name__ == "__main__":
    success = asyncio.run(create_test_users())
    sys.exit(0 if success else 1)