#!/usr/bin/env python3
"""
Check database status and apply necessary migrations
"""
import asyncio
import asyncpg
import sys

async def check_and_migrate():
    """Check database status and apply migrations"""
    database_url = "postgresql://postgres:password@localhost:5432/iris_db"
    
    try:
        conn = await asyncpg.connect(database_url)
        
        # Check if audit_logs table exists
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'audit_logs'
            );
        """)
        
        print(f"audit_logs table exists: {table_exists}")
        
        if table_exists:
            # Check existing columns
            columns = await conn.fetch("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'audit_logs'
                ORDER BY ordinal_position;
            """)
            
            print("Existing columns:")
            for col in columns:
                print(f"  - {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")
            
            # Apply only missing columns
            existing_cols = [col['column_name'] for col in columns]
            
            if 'aggregate_id' not in existing_cols:
                await conn.execute("ALTER TABLE audit_logs ADD COLUMN aggregate_id VARCHAR(255);")
                print("✅ Added aggregate_id column")
            
            if 'aggregate_type' not in existing_cols:
                await conn.execute("ALTER TABLE audit_logs ADD COLUMN aggregate_type VARCHAR(100);")
                print("✅ Added aggregate_type column")
            
            if 'publisher' not in existing_cols:
                await conn.execute("ALTER TABLE audit_logs ADD COLUMN publisher VARCHAR(255);")
                print("✅ Added publisher column")
            
            if 'soc2_category' not in existing_cols:
                await conn.execute("ALTER TABLE audit_logs ADD COLUMN soc2_category VARCHAR(50);")
                print("✅ Added soc2_category column")
            
            if 'headers' not in existing_cols:
                await conn.execute("ALTER TABLE audit_logs ADD COLUMN headers JSONB;")
                print("✅ Added headers column")
            
            # Create indexes
            try:
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_aggregate_id ON audit_logs(aggregate_id);")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_soc2_category ON audit_logs(soc2_category);")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_publisher ON audit_logs(publisher);")
                print("✅ Created indexes")
            except Exception as e:
                print(f"Index creation warning: {e}")
            
        else:
            print("❌ audit_logs table does not exist. Database needs to be initialized first.")
        
        await conn.close()
        print("✅ Database check and migration completed!")
        
    except Exception as e:
        print(f"❌ Database operation failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(check_and_migrate())
    exit(0 if success else 1)