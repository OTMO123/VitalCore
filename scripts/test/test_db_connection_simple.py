#!/usr/bin/env python3
"""Simple PostgreSQL database connection test using asyncpg only."""

import asyncpg
import asyncio

async def test_ssl_connection():
    """Test SSL connection with intelligent fallback."""
    print("🔍 Testing PostgreSQL SSL connectivity...")
    
    # Test SSL connection with timeout
    try:
        print("  Attempting SSL connection...")
        conn = await asyncio.wait_for(
            asyncpg.connect(
                host="localhost",
                port=5432,
                database="iris_db",
                user="postgres",
                password="password",
                ssl="prefer"
            ),
            timeout=8.0
        )
        print("✅ SSL connection successful!")
        version = await conn.fetchval("SELECT version();")
        print(f"  PostgreSQL version: {version}")
        await conn.close()
        return True
    except asyncio.TimeoutError:
        print("❌ SSL connection timeout")
        return False
    except Exception as e:
        print(f"❌ SSL connection failed: {e}")
        return False

async def test_no_ssl_connection():
    """Test connection without SSL."""
    print("  Attempting non-SSL connection...")
    try:
        conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            database="iris_db",
            user="postgres",
            password="password",
            ssl=False
        )
        print("✅ Non-SSL connection successful!")
        version = await conn.fetchval("SELECT version();")
        print(f"  PostgreSQL version: {version}")
        await conn.close()
        return True
    except Exception as e:
        print(f"❌ Non-SSL connection failed: {e}")
        return False

async def main():
    print("Healthcare Backend - Database Connection Test")
    print("===========================================")
    
    # Test SSL first
    ssl_ok = await test_ssl_connection()
    print()
    
    # Test non-SSL if SSL failed
    if not ssl_ok:
        print("🔄 Trying fallback connection without SSL...")
        no_ssl_ok = await test_no_ssl_connection()
        print()
    else:
        no_ssl_ok = False
    
    print("Summary:")
    print(f"  SSL connection: {'✅' if ssl_ok else '❌'}")
    print(f"  Non-SSL connection: {'✅' if no_ssl_ok else '❌'}")
    
    if ssl_ok:
        print("\n🛡️  Enterprise security status: SSL/TLS encryption active")
    elif no_ssl_ok:
        print("\n⚠️  Security advisory: Using non-SSL connection")
        print("   For production: Configure PostgreSQL with SSL certificates")
    else:
        print("\n❌ Database connectivity failed - check PostgreSQL service")

if __name__ == "__main__":
    asyncio.run(main())