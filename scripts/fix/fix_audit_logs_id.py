#!/usr/bin/env python3
"""
Fix audit_logs table ID column type mismatch
"""

import asyncio
import asyncpg

async def fix_audit_logs_id():
    # Connect to database
    conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/iris_db")
    
    try:
        print("Fixing audit_logs table ID column type...")
        
        # Check current ID column type
        id_column = await conn.fetchrow("""
            SELECT data_type FROM information_schema.columns 
            WHERE table_name = 'audit_logs' AND column_name = 'id'
        """)
        
        print(f"Current ID column type: {id_column['data_type']}")
        
        if id_column['data_type'] == 'integer':
            print("Converting ID column from integer to UUID...")
            
            # Start transaction
            async with conn.transaction():
                # Step 1: Add a new UUID column
                await conn.execute("ALTER TABLE audit_logs ADD COLUMN new_id UUID DEFAULT gen_random_uuid()")
                
                # Step 2: Update the new column with generated UUIDs
                await conn.execute("UPDATE audit_logs SET new_id = gen_random_uuid()")
                
                # Step 3: Drop the old integer ID column
                await conn.execute("ALTER TABLE audit_logs DROP COLUMN id")
                
                # Step 4: Rename new_id to id
                await conn.execute("ALTER TABLE audit_logs RENAME COLUMN new_id TO id")
                
                # Step 5: Make it the primary key
                await conn.execute("ALTER TABLE audit_logs ADD PRIMARY KEY (id)")
                
            print("Successfully converted ID column to UUID!")
        else:
            print("ID column is already UUID type")
        
        # Also fix other UUID columns that might be wrong type
        print("\nChecking other UUID columns...")
        
        uuid_columns = ['user_id', 'session_id', 'correlation_id', 'resource_id']
        
        for col_name in uuid_columns:
            col_info = await conn.fetchrow("""
                SELECT data_type FROM information_schema.columns 
                WHERE table_name = 'audit_logs' AND column_name = %s
            """, col_name)
            
            if col_info and col_info['data_type'] == 'character varying':
                print(f"Converting {col_name} from VARCHAR to UUID...")
                await conn.execute(f"ALTER TABLE audit_logs ALTER COLUMN {col_name} TYPE UUID USING {col_name}::UUID")
        
        print("\nAudit logs ID fix completed!")
        
        # Verify final schema
        final_columns = await conn.fetch("""
            SELECT column_name, data_type FROM information_schema.columns 
            WHERE table_name = 'audit_logs' AND column_name IN ('id', 'user_id', 'session_id', 'correlation_id', 'resource_id')
            ORDER BY column_name
        """)
        
        print("\nFinal UUID columns:")
        for col in final_columns:
            print(f"  {col['column_name']}: {col['data_type']}")
        
    except Exception as e:
        print(f"Error fixing audit_logs ID: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(fix_audit_logs_id())