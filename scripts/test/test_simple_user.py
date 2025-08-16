#!/usr/bin/env python3
"""
Simple test to verify User creation works with the updated schema.
"""
import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_user_creation():
    """Test creating a user with the advanced schema including role field."""
    try:
        from app.core.database_advanced import User, get_engine, async_sessionmaker
        from app.core.security import get_password_hash
        
        print("Getting database engine...")
        engine = get_engine()
        
        if engine is None:
            # Initialize engine manually for testing
            from sqlalchemy.ext.asyncio import create_async_engine
            database_url = "postgresql+asyncpg://test_user:test_password@localhost:5433/test_iris_db"
            engine = create_async_engine(database_url, echo=True)
        
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        
        print("Creating user...")
        async with session_factory() as session:
            # Create a user with minimal required fields - avoid email_verified for now
            user = User(
                email="test@example.com",
                username="testuser", 
                password_hash=get_password_hash("testpassword"),
                role="user"  # This should work now
            )
            
            session.add(user)
            await session.commit()
            await session.refresh(user)
            
            print(f"SUCCESS: User created with ID: {user.id}")
            print(f"User email: {user.email}")
            print(f"User role: {user.role}")
            print(f"User is_active: {user.is_active}")
            
            return user
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(test_user_creation())
    if result:
        print("✅ User creation test passed!")
    else:
        print("❌ User creation test failed!")