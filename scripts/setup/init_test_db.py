#!/usr/bin/env python3
"""
Initialize test database with advanced schema.
"""
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine

async def init_test_database():
    """Initialize the test database with advanced schema."""
    # Set database URL for test
    database_url = "postgresql+asyncpg://test_user:test_password@localhost:5433/test_iris_db"
    
    # Create engine
    engine = create_async_engine(database_url, echo=True)
    
    try:
        # Import the advanced database Base and models
        from app.core.database_advanced import Base
        
        print("Creating all tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ Database initialized successfully!")
        
        # Verify tables were created
        async with engine.connect() as conn:
            result = await conn.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
            tables = [row[0] for row in result.fetchall()]
            print(f"Created tables: {tables}")
            
            # Check enums
            result = await conn.execute("SELECT typname FROM pg_type WHERE typtype = 'e'")
            enums = [row[0] for row in result.fetchall()]
            print(f"Created enums: {enums}")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_test_database())