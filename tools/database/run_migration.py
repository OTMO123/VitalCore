#!/usr/bin/env python3
"""
Run Database Migration to Fix Audit Enum Mismatch
"""

import asyncpg
import asyncio

async def run_migration():
    """Run the audit enum fix migration directly"""
    
    try:
        # Connect to the database
        conn = await asyncpg.connect("postgresql://test_user:test_password@localhost:5433/test_iris_db")
        
        print("🔧 FIXING AUDIT ENUM MISMATCH")
        print("=" * 40)
        
        # Check current enum values
        print("📋 Checking current audit enum values...")
        current_enums = await conn.fetch("""
            SELECT enumlabel 
            FROM pg_enum 
            WHERE enumtypid = (
                SELECT oid 
                FROM pg_type 
                WHERE typname = 'auditeventtype'
            )
            ORDER BY enumlabel;
        """)
        
        print("Current enum values:")
        for enum_val in current_enums:
            print(f"  - {enum_val['enumlabel']}")
        
        # Start the migration
        print("\n🔄 Starting migration...")
        
        # Step 1: Rename old enum
        print("Step 1: Renaming old enum...")
        await conn.execute("ALTER TYPE auditeventtype RENAME TO auditeventtype_old")
        
        # Step 2: Create new enum with all values
        print("Step 2: Creating new enum with correct values...")
        await conn.execute("""
            CREATE TYPE auditeventtype AS ENUM (
                'user_login', 'user_logout', 'user_login_failed', 
                'user_created', 'user_updated', 'user_deleted',
                'phi_accessed', 'phi_created', 'phi_updated', 'phi_deleted', 'phi_exported',
                'patient_created', 'patient_updated', 'patient_accessed', 'patient_search',
                'document_created', 'document_accessed', 'document_updated', 'document_deleted',
                'consent_granted', 'consent_withdrawn', 'consent_updated',
                'system_access', 'config_changed', 'security_violation', 'data_breach_detected',
                'api_request', 'api_response', 'api_error',
                'iris_sync_started', 'iris_sync_completed', 'iris_sync_failed',
                'access', 'modify', 'delete', 'authenticate', 'authorize', 'api_call', 'purge', 'export', 'configuration_change'
            )
        """)
        
        # Step 3: Update audit_logs table
        print("Step 3: Updating audit_logs table...")
        await conn.execute("""
            ALTER TABLE audit_logs 
            ALTER COLUMN event_type TYPE auditeventtype 
            USING CASE 
                WHEN event_type::text = 'access' THEN 'system_access'::auditeventtype
                WHEN event_type::text = 'modify' THEN 'phi_updated'::auditeventtype  
                WHEN event_type::text = 'delete' THEN 'phi_deleted'::auditeventtype
                WHEN event_type::text = 'authenticate' THEN 'user_login'::auditeventtype
                WHEN event_type::text = 'authorize' THEN 'system_access'::auditeventtype
                WHEN event_type::text = 'api_call' THEN 'api_request'::auditeventtype
                WHEN event_type::text = 'purge' THEN 'phi_deleted'::auditeventtype
                WHEN event_type::text = 'export' THEN 'phi_exported'::auditeventtype
                WHEN event_type::text = 'configuration_change' THEN 'config_changed'::auditeventtype
                ELSE event_type::text::auditeventtype
            END
        """)
        
        # Step 4: Drop old enum
        print("Step 4: Dropping old enum...")
        await conn.execute("DROP TYPE auditeventtype_old")
        
        # Verify the new enum
        print("\n✅ Migration completed! Checking new enum values...")
        new_enums = await conn.fetch("""
            SELECT enumlabel 
            FROM pg_enum 
            WHERE enumtypid = (
                SELECT oid 
                FROM pg_type 
                WHERE typname = 'auditeventtype'
            )
            ORDER BY enumlabel;
        """)
        
        print("New enum values:")
        for enum_val in new_enums:
            print(f"  - {enum_val['enumlabel']}")
        
        await conn.close()
        
        print("\n🎉 MIGRATION SUCCESSFUL!")
        print("The database now supports all audit enum values expected by the code.")
        print("You can now test the endpoints again.")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print("You may need to run this migration manually.")

if __name__ == "__main__":
    asyncio.run(run_migration())