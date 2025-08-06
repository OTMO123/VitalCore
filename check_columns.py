8#!/usr/bin/env python3
"""
Check Clinical Workflows Table Columns
"""
import asyncpg
import asyncio

async def check_columns():
    try:
        conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/iris_db")
        
        # Check clinical_workflows columns
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'clinical_workflows' 
            ORDER BY ordinal_position;
        """)
        
        print("clinical_workflows table columns:")
        print("-" * 40)
        for col in columns:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
            print(f"  {col['column_name']}: {col['data_type']} {nullable}{default}")
            
        await conn.close()
        
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(check_columns())