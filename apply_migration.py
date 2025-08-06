#!/usr/bin/env python3
"""
Apply database migration script for AuditLog schema updates
"""
import asyncio
import asyncpg
import os

async def apply_migration():
    """Apply the database migration script"""
    database_url = "postgresql://postgres:password@localhost:5432/iris_db"
    
    try:
        # Read the migration script
        with open("update_audit_log_schema.sql", "r") as f:
            migration_sql = f.read()
        
        # Connect to database and apply migration
        conn = await asyncpg.connect(database_url)
        
        # Split the SQL into individual statements
        statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip() and not stmt.strip().startswith('--')]
        
        for statement in statements:
            if statement.upper() == 'COMMIT':
                continue
            print(f"Executing: {statement[:50]}...")
            await conn.execute(statement)
        
        await conn.close()
        print("✅ Database migration applied successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(apply_migration())
    exit(0 if success else 1)