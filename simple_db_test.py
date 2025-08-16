#!/usr/bin/env python3
"""Simple database connection test without Unicode."""

import asyncio
import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine

async def test_db():
    configs = [
        ("Main DB 5432", "postgresql+asyncpg://postgres:password@localhost:5432/iris_db"),
        ("Test DB 5433", "postgresql+asyncpg://test_user:test_password@localhost:5433/test_iris_db"),
    ]
    
    print("Testing database connections...")
    
    for name, url in configs:
        print(f"\nTesting {name}:")
        try:
            engine = create_async_engine(url)
            async with engine.begin() as conn:
                result = await conn.execute("SELECT 1")
                print(f"  SUCCESS - {name} is working")
                await engine.dispose()
                return name, url
        except Exception as e:
            print(f"  FAILED - {name}: {e}")
            try:
                await engine.dispose()
            except:
                pass
    
    print("\nNo database connections available.")
    return None, None

if __name__ == "__main__":
    working_name, working_url = asyncio.run(test_db())
    if working_url:
        print(f"\nUSE THIS CONFIG: {working_url}")
    else:
        print("\nNeed to start PostgreSQL database")