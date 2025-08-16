#!/usr/bin/env python3
"""
Simple database test to verify advanced schema works.
"""
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

async def test_simple_user_creation():
    """Test creating a simple user with the advanced schema."""
    # Set database URL for test
    database_url = "postgresql+asyncpg://test_user:test_password@localhost:5433/test_iris_db"
    
    # Create engine
    engine = create_async_engine(database_url, echo=True)
    
    # Create session factory
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    
    try:
        # Import the advanced database models
        from app.core.database_advanced import User
        from app.core.security import get_password_hash
        
        print("Creating simple user...")
        
        async with session_factory() as session:
            # Create a simple user with minimal required fields
            user = User(
                email="test@example.com",
                username="testuser",
                password_hash=get_password_hash("testpassword")
            )
            
            session.add(user)
            await session.commit()
            await session.refresh(user)
            
            print(f"User created successfully: {user.id}")
            print(f"User email: {user.email}")
            print(f"User username: {user.username}")
            print(f"User is_active: {user.is_active}")
        
        print("SUCCESS: User creation test passed!")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_simple_user_creation())