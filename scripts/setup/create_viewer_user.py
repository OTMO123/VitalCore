#!/usr/bin/env python3
"""
Create viewer user for login testing.
"""
import asyncio
import sys
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

# Suppress SQLAlchemy logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

from app.core.database import get_db
from app.core.security import get_password_hash

async def create_viewer_user():
    """Create viewer user if it doesn't exist."""
    print("Creating viewer user for login testing...")
    
    username = "viewer"
    password = "viewer123"
    email = "viewer@example.com"
    hashed_password = get_password_hash(password)
    
    async for session in get_db():
        try:
            # Check if user exists
            result = await session.execute(
                text("SELECT id FROM users WHERE username = :username"),
                {"username": username}
            )
            existing_user = result.fetchone()
            
            if not existing_user:
                # Insert user directly with raw SQL using correct column names
                await session.execute(
                    text("""
                        INSERT INTO users (id, username, email, password_hash, role, is_active, email_verified, 
                                         mfa_enabled, failed_login_attempts, must_change_password, 
                                         password_changed_at, is_system_user, created_at, updated_at) 
                        VALUES (gen_random_uuid(), :username, :email, :password_hash, :role, :is_active, :email_verified,
                               :mfa_enabled, :failed_login_attempts, :must_change_password,
                               NOW(), :is_system_user, NOW(), NOW())
                    """),
                    {
                        "username": username,
                        "email": email,
                        "password_hash": hashed_password,
                        "role": "USER",
                        "is_active": True,
                        "email_verified": True,
                        "mfa_enabled": False,
                        "failed_login_attempts": 0,
                        "must_change_password": False,
                        "is_system_user": False
                    }
                )
                await session.commit()
                print(f"[SUCCESS] Created user: {username}")
            else:
                print(f"[INFO] User already exists: {username}")
                
        except Exception as e:
            print(f"[ERROR] Error creating user: {e}")
            await session.rollback()
            return False
        finally:
            break
            
    return True

if __name__ == "__main__":
    success = asyncio.run(create_viewer_user())
    sys.exit(0 if success else 1)