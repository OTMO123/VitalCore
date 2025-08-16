#!/usr/bin/env python3
"""
Quick test to verify User creation with correct schema.
"""
import asyncio
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(__file__))

async def test_basic_user():
    """Test creating a user with the correct schema."""
    try:
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        from app.core.database_advanced import User
        from app.core.security import get_password_hash
        
        print("Connecting to database...")
        database_url = "postgresql+asyncpg://test_user:test_password@localhost:5433/test_iris_db"
        engine = create_async_engine(database_url, echo=False)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        
        print("Creating user...")
        async with session_factory() as session:
            user = User(
                email="quicktest@example.com",
                username="quicktest",
                password_hash=get_password_hash("password123"),
                email_verified=True,
                role="user",
                is_active=True
            )
            
            session.add(user)
            await session.commit()
            await session.refresh(user)
            
            print(f"SUCCESS: User created!")
            print(f"  ID: {user.id}")
            print(f"  Email: {user.email}")
            print(f"  Username: {user.username}")
            print(f"  Role: {user.role}")
            print(f"  Email verified: {user.email_verified}")
            print(f"  Is active: {user.is_active}")
            
        await engine.dispose()
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_basic_user())
    if success:
        print("\n✓ User creation works! Schema is fixed.")
    else:
        print("\n✗ User creation failed. Schema issue persists.")