#!/usr/bin/env python3
"""
Check Database Tables Script
Check what tables exist in the current database and identify missing ones.
"""
import asyncpg
import asyncio
from datetime import datetime

async def check_database_tables():
    """Check what tables exist in the database."""
    try:
        # Connect to Docker PostgreSQL
        conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/iris_db")
        print("Connected to Docker PostgreSQL successfully!")
        
        # Get all table names
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        
        print(f"\nExisting tables in database ({len(tables)} total):")
        print("=" * 50)
        existing_tables = []
        for table in tables:
            table_name = table['table_name']
            existing_tables.append(table_name)
            print(f"  ✓ {table_name}")
        
        # Check for clinical workflows specific tables
        clinical_tables = [
            'clinical_workflows', 
            'clinical_workflow_steps', 
            'clinical_encounters', 
            'clinical_workflow_audit'
        ]
        
        print(f"\nClinical Workflows Tables Status:")
        print("=" * 50)
        missing_clinical = []
        for table in clinical_tables:
            if table in existing_tables:
                print(f"  ✓ {table} - EXISTS")
            else:
                print(f"  ✗ {table} - MISSING")
                missing_clinical.append(table)
        
        # Check for referenced tables that clinical workflows depends on
        referenced_tables = [
            'users',
            'organizations', 
            'patients',
            'providers',
            'user_roles',
            'roles',
            'permissions'
        ]
        
        print(f"\nReferenced Tables Status:")
        print("=" * 50)
        missing_referenced = []
        for table in referenced_tables:
            if table in existing_tables:
                print(f"  ✓ {table} - EXISTS")
            else:
                print(f"  ✗ {table} - MISSING")
                missing_referenced.append(table)
        
        # Check column details for existing clinical workflow tables
        for table in clinical_tables:
            if table in existing_tables:
                columns = await conn.fetch(f"""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = '{table}' 
                    ORDER BY ordinal_position;
                """)
                
                print(f"\nTable '{table}' columns ({len(columns)} total):")
                print("-" * 40)
                for col in columns:
                    nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                    default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                    print(f"  {col['column_name']}: {col['data_type']} {nullable}{default}")
        
        await conn.close()
        
        print(f"\nSummary:")
        print("=" * 50)
        print(f"Total existing tables: {len(existing_tables)}")
        print(f"Missing clinical workflow tables: {len(missing_clinical)}")
        print(f"Missing referenced tables: {len(missing_referenced)}")
        
        if missing_clinical:
            print(f"\nNeed to create clinical tables: {', '.join(missing_clinical)}")
        
        if missing_referenced:
            print(f"\nNeed to create referenced tables: {', '.join(missing_referenced)}")
            
        return {
            'existing': existing_tables,
            'missing_clinical': missing_clinical,
            'missing_referenced': missing_referenced
        }
        
    except Exception as e:
        print(f"ERROR Database check failed: {e}")
        return None

if __name__ == "__main__":
    result = asyncio.run(check_database_tables())