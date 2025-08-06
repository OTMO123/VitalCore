#!/usr/bin/env python3

import asyncio
import asyncpg

async def check_table_structure():
    """Check the actual structure of the users table"""
    try:
        # Connect to database
        conn = await asyncpg.connect(
            host="localhost",
            port=5433,
            user="test_user", 
            password="test_password",
            database="test_iris_db"
        )
        
        print("Connected to database successfully!")
        
        # Get table structure
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable, column_default 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            ORDER BY ordinal_position
        """)
        
        print(f"\nUsers table structure:")
        print("=" * 50)
        for col in columns:
            print(f"Column: {col['column_name']}")
            print(f"  Type: {col['data_type']}")
            print(f"  Nullable: {col['is_nullable']}")
            print(f"  Default: {col['column_default']}")
            print()
            
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_table_structure())