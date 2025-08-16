#!/usr/bin/env python3
"""
Check database schema
"""

import asyncio
import asyncpg

async def check_schema():
    # Connect to database
    conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/iris_db")
    
    try:
        # Get table schema
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            ORDER BY ordinal_position
        """)
        
        print("Users table schema:")
        for col in columns:
            print(f"  {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")
            
    except Exception as e:
        print(f"Error checking schema: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_schema())