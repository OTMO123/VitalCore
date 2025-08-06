#!/usr/bin/env python3
"""
Check Database Constraints and Enums
"""
import asyncpg
import asyncio

async def check_constraints():
    try:
        conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/iris_db")
        
        # Check constraints on clinical_workflows
        constraints = await conn.fetch("""
            SELECT constraint_name, check_clause
            FROM information_schema.check_constraints
            WHERE constraint_name LIKE '%workflow%';
        """)
        
        print("Workflow constraints:")
        for constraint in constraints:
            print(f"  {constraint['constraint_name']}: {constraint['check_clause']}")
        
        # Check enum types
        enums = await conn.fetch("""
            SELECT typname, enumlabel
            FROM pg_type t
            JOIN pg_enum e ON t.oid = e.enumtypid
            WHERE typname LIKE '%workflow%' OR typname LIKE '%clinical%'
            ORDER BY typname, enumsortorder;
        """)
        
        current_enum = None
        print("\nEnum types:")
        for enum in enums:
            if enum['typname'] != current_enum:
                current_enum = enum['typname']
                print(f"  {current_enum}:")
            print(f"    - {enum['enumlabel']}")
        
        await conn.close()
        
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(check_constraints())