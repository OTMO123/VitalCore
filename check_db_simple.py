#!/usr/bin/env python3
"""
Simple Database Tables Check (Windows-compatible)
"""
import asyncpg
import asyncio

async def check_tables():
    try:
        conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/iris_db")
        print("Connected to PostgreSQL successfully!")
        
        # Get all table names
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        
        print(f"\nExisting tables ({len(tables)} total):")
        existing_tables = [t['table_name'] for t in tables]
        for table in existing_tables:
            print(f"  {table}")
        
        # Check clinical workflows tables
        clinical_tables = [
            'clinical_workflows', 
            'clinical_workflow_steps', 
            'clinical_encounters', 
            'clinical_workflow_audit'
        ]
        
        print(f"\nClinical Workflows Tables:")
        missing_clinical = []
        for table in clinical_tables:
            if table in existing_tables:
                print(f"  [EXISTS] {table}")
            else:
                print(f"  [MISSING] {table}")
                missing_clinical.append(table)
        
        # Check referenced tables
        referenced_tables = ['users', 'organizations', 'patients', 'providers', 'roles']
        
        print(f"\nReferenced Tables:")
        missing_ref = []
        for table in referenced_tables:
            if table in existing_tables:
                print(f"  [EXISTS] {table}")
            else:
                print(f"  [MISSING] {table}")
                missing_ref.append(table)
        
        await conn.close()
        
        print(f"\nSummary:")
        print(f"Total tables: {len(existing_tables)}")
        print(f"Missing clinical: {missing_clinical}")
        print(f"Missing referenced: {missing_ref}")
        
        return existing_tables, missing_clinical, missing_ref
        
    except Exception as e:
        print(f"ERROR: {e}")
        return None, None, None

if __name__ == "__main__":
    result = asyncio.run(check_tables())