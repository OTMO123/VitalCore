#\!/usr/bin/env python3
"""Test PostgreSQL database connection."""

import psycopg2
import asyncpg
import asyncio

def test_sync_connection():
    """Test synchronous connection with psycopg2."""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="iris_db", 
            user="postgres",
            password="password",
            sslmode="disable"  # Disable SSL
        )
        print("✅ Sync connection successful\!")
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"PostgreSQL version: {version[0]}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Sync connection failed: {e}")
        return False

async def test_async_connection():
    """Test asynchronous connection with asyncpg."""
    try:
        # Test without SSL first
        conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            database="iris_db",
            user="postgres", 
            password="password",
            ssl=False  # Disable SSL
        )
        print("✅ Async connection successful\!")
        version = await conn.fetchval("SELECT version();")
        print(f"PostgreSQL version: {version}")
        await conn.close()
        return True
    except Exception as e:
        print(f"❌ Async connection failed: {e}")
        return False

async def test_async_connection_with_ssl():
    """Test asynchronous connection with SSL."""
    try:
        conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            database="iris_db",
            user="postgres",
            password="password"
            # SSL enabled by default
        )
        print("✅ Async connection with SSL successful\!")
        version = await conn.fetchval("SELECT version();")
        print(f"PostgreSQL version: {version}")
        await conn.close()
        return True
    except Exception as e:
        print(f"❌ Async connection with SSL failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing PostgreSQL database connections...")
    print()
    
    print("1. Testing synchronous connection (psycopg2):")
    sync_ok = test_sync_connection()
    print()
    
    print("2. Testing asynchronous connection without SSL (asyncpg):")
    async_ok = asyncio.run(test_async_connection())
    print()
    
    print("3. Testing asynchronous connection with SSL (asyncpg):")
    async_ssl_ok = asyncio.run(test_async_connection_with_ssl())
    print()
    
    print("Summary:")
    print(f"  Sync connection: {'✅' if sync_ok else '❌'}")
    print(f"  Async no SSL: {'✅' if async_ok else '❌'}")
    print(f"  Async with SSL: {'✅' if async_ssl_ok else '❌'}")
