#!/usr/bin/env python3
"""
Create healthcare role users for role-based security testing.

This script creates the missing healthcare role users that are needed
for the role-based security tests:
- patient (role: patient)
- doctor (role: doctor)  
- lab_tech (role: lab_technician)
"""

import asyncio
import sys
import logging
from sqlalchemy import text
from datetime import datetime

# Suppress SQLAlchemy logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

# We need to add the project root to sys.path to import app modules
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from app.core.database import get_db
from app.core.security import get_password_hash

async def create_healthcare_users():
    """Create healthcare role users if they don't exist."""
    print("Creating healthcare role users for security testing...")
    
    healthcare_users = [
        {
            "username": "patient", 
            "password": "TestPassword123!",
            "role": "patient",
            "email": "patient@test.com",
            "description": "Test patient user for role-based security testing"
        },
        {
            "username": "doctor",
            "password": "TestPassword123!", 
            "role": "doctor",
            "email": "doctor@test.com",
            "description": "Test doctor user for role-based security testing"
        },
        {
            "username": "lab_tech",
            "password": "TestPassword123!",
            "role": "lab_technician", 
            "email": "lab_tech@test.com",
            "description": "Test lab technician user for role-based security testing"
        }
    ]
    
    async for session in get_db():
        try:
            created_count = 0
            for user_info in healthcare_users:
                username = user_info["username"]
                password = user_info["password"]
                role = user_info["role"]
                email = user_info["email"]
                description = user_info["description"]
                hashed_password = get_password_hash(password)
                
                # Check if user exists
                result = await session.execute(
                    text("SELECT id FROM users WHERE username = :username"),
                    {"username": username}
                )
                existing_user = result.fetchone()
                
                if not existing_user:
                    print(f"Creating user: {username} ({role})")
                    
                    # Insert user directly with raw SQL using correct column names
                    await session.execute(
                        text("""
                            INSERT INTO users (id, username, email, password_hash, role, is_active, email_verified,
                                             mfa_enabled, failed_login_attempts, must_change_password,
                                             password_changed_at, is_system_user, created_at, updated_at,
                                             profile_data)
                            VALUES (gen_random_uuid(), :username, :email, :password_hash, :role, :is_active, :email_verified,
                                   :mfa_enabled, :failed_login_attempts, :must_change_password,
                                   NOW(), :is_system_user, NOW(), NOW(), :profile_data)
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
                            "is_system_user": False,
                            "profile_data": f'{{"description": "{description}", "created_for": "role_based_security_testing"}}'
                        }
                    )
                    created_count += 1
                    print(f"[SUCCESS] Created user: {username} ({role})")
                else:
                    print(f"[INFO] User already exists: {username}")
                    
            if created_count > 0:
                await session.commit()
                print(f"\n[SUCCESS] Successfully created {created_count} healthcare users")
                print("\nCreated users:")
                for user_info in healthcare_users:
                    print(f"  - Username: {user_info['username']}")
                    print(f"    Role: {user_info['role']}")
                    print(f"    Email: {user_info['email']}")
                    print(f"    Password: {user_info['password']}")
                    print()
            else:
                print(f"\n[INFO] All healthcare users already exist")
                
        except Exception as e:
            print(f"[ERROR] Error creating healthcare users: {e}")
            await session.rollback()
            return False
        finally:
            break
            
    return True

async def verify_healthcare_users():
    """Verify that healthcare users were created successfully."""
    print("\nVerifying healthcare users...")
    
    async for session in get_db():
        try:
            # Get healthcare users
            result = await session.execute(
                text("SELECT username, email, role, is_active FROM users WHERE role IN ('patient', 'doctor', 'lab_technician')")
            )
            users = result.fetchall()
            
            print(f"Found {len(users)} healthcare users:")
            for user in users:
                print(f"  - {user['username']} ({user['role']}) - Active: {user['is_active']}")
                
            expected_roles = {'patient', 'doctor', 'lab_technician'}
            found_roles = {user['role'] for user in users}
            
            if expected_roles.issubset(found_roles):
                print("\n[SUCCESS] All required healthcare roles are present")
                return True
            else:
                missing = expected_roles - found_roles
                print(f"\n[WARNING] Missing roles: {missing}")
                return False
                
        except Exception as e:
            print(f"[ERROR] Error verifying users: {e}")
            return False
        finally:
            break

if __name__ == "__main__":
    success = asyncio.run(create_healthcare_users())
    if success:
        verify_success = asyncio.run(verify_healthcare_users())
        sys.exit(0 if verify_success else 1)
    else:
        sys.exit(1)