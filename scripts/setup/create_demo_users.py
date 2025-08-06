#!/usr/bin/env python3
"""
Create demo users for login testing.
"""
import asyncio
import sys
import logging
from sqlalchemy import text

# Suppress SQLAlchemy logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

from app.core.database import get_db
from app.core.security import get_password_hash

async def create_demo_users():
    """Create demo users if they don't exist."""
    print("Creating demo users for login testing...")
    
    demo_users = [
        {"username": "viewer", "password": "viewer123", "role": "USER"},
        {"username": "operator", "password": "operator123", "role": "OPERATOR"}, 
        {"username": "admin", "password": "admin123", "role": "ADMIN"}
    ]
    
    async for session in get_db():
        try:
            created_count = 0
            for user_info in demo_users:
                username = user_info["username"]
                password = user_info["password"] 
                role = user_info["role"]
                email = f"{username}@example.com"
                hashed_password = get_password_hash(password)
                
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
                            "role": role,
                            "is_active": True,
                            "email_verified": True,
                            "mfa_enabled": False,
                            "failed_login_attempts": 0,
                            "must_change_password": False,
                            "is_system_user": False
                        }
                    )
                    created_count += 1
                    print(f"[SUCCESS] Created user: {username} ({role})")
                else:
                    print(f"[INFO] User already exists: {username}")
                    
            if created_count > 0:
                await session.commit()
                print(f"\n[SUCCESS] Successfully created {created_count} demo users")
            else:
                print(f"\n[INFO] All demo users already exist")
                
        except Exception as e:
            print(f"[ERROR] Error creating users: {e}")
            await session.rollback()
            return False
        finally:
            break
            
    return True

if __name__ == "__main__":
    success = asyncio.run(create_demo_users())
    sys.exit(0 if success else 1)