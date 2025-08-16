#!/usr/bin/env python3
"""
Check enum values in database
"""

import asyncio
import asyncpg

async def check_enums():
    # Connect to database
    conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/iris_db")
    
    try:
        print("Checking enum types...")
        
        # Get all enum types
        enums = await conn.fetch("""
            SELECT t.typname, e.enumlabel
            FROM pg_type t 
            JOIN pg_enum e ON t.oid = e.enumtypid
            ORDER BY t.typname, e.enumsortorder
        """)
        
        current_enum = None
        for enum in enums:
            if enum['typname'] != current_enum:
                current_enum = enum['typname']
                print(f"\nEnum: {current_enum}")
            print(f"  - {enum['enumlabel']}")
            
        # Check users table role values
        print("\nActual role values in users table:")
        roles = await conn.fetch("SELECT DISTINCT role FROM users")
        for role in roles:
            print(f"  - '{role['role']}'")
            
    except Exception as e:
        print(f"Error checking enums: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_enums())