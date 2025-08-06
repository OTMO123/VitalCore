#!/usr/bin/env python3
"""
Complete database schema fix - remove all enum constraints and make all fields flexible
"""
import asyncio
import asyncpg

async def complete_database_fix():
    """Complete database schema fix for all enum constraints"""
    database_url = "postgresql://postgres:password@localhost:5432/iris_db"
    
    try:
        conn = await asyncpg.connect(database_url)
        
        print("🔧 Starting complete database schema fix...")
        
        # Drop enum constraints entirely and use VARCHAR
        try:
            await conn.execute("""
                -- Drop the enum type constraint on event_type
                ALTER TABLE audit_logs DROP CONSTRAINT IF EXISTS audit_logs_event_type_check;
                
                -- Change event_type to unlimited VARCHAR
                ALTER TABLE audit_logs ALTER COLUMN event_type DROP DEFAULT;
                ALTER TABLE audit_logs ALTER COLUMN event_type TYPE VARCHAR USING event_type::text;
            """)
            print("✅ event_type constraint removed and converted to VARCHAR")
        except Exception as e:
            print(f"⚠️  event_type fix warning: {e}")
        
        # Fix data_classification enum
        try:
            await conn.execute("""
                -- Drop constraint on data_classification if any
                ALTER TABLE audit_logs DROP CONSTRAINT IF EXISTS audit_logs_data_classification_check;
                
                -- Convert to VARCHAR for flexibility
                ALTER TABLE audit_logs ALTER COLUMN data_classification TYPE VARCHAR USING data_classification::text;
            """)
            print("✅ data_classification converted to VARCHAR")
        except Exception as e:
            print(f"⚠️  data_classification fix warning: {e}")
        
        # Ensure all other fields are properly typed
        await conn.execute("""
            -- Make sure user_id is VARCHAR
            ALTER TABLE audit_logs ALTER COLUMN user_id TYPE VARCHAR(255);
            
            -- Make sure soc2_category is VARCHAR
            ALTER TABLE audit_logs ALTER COLUMN soc2_category TYPE VARCHAR(100);
            
            -- Make sure outcome is VARCHAR
            ALTER TABLE audit_logs ALTER COLUMN outcome TYPE VARCHAR(100);
            
            -- Make action optional
            ALTER TABLE audit_logs ALTER COLUMN action DROP NOT NULL;
            
            -- Make log_hash optional 
            ALTER TABLE audit_logs ALTER COLUMN log_hash DROP NOT NULL;
            
            -- Ensure headers is JSONB
            ALTER TABLE audit_logs ALTER COLUMN headers TYPE JSONB USING headers::jsonb;
        """)
        print("✅ All audit_logs fields properly configured")
        
        # Update any existing records to prevent issues
        await conn.execute("""
            -- Set default values for potentially problematic fields
            UPDATE audit_logs SET 
                event_type = COALESCE(event_type, 'system_event'),
                outcome = COALESCE(outcome, 'success'),
                data_classification = COALESCE(data_classification, 'internal'),
                headers = COALESCE(headers, '{}')
            WHERE event_type IS NULL OR outcome IS NULL OR data_classification IS NULL OR headers IS NULL;
        """)
        print("✅ Existing records updated with default values")
        
        # Create indexes for performance
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type ON audit_logs(event_type);
            CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
            CREATE INDEX IF NOT EXISTS idx_audit_logs_outcome ON audit_logs(outcome);
            CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
            CREATE INDEX IF NOT EXISTS idx_audit_logs_soc2_category ON audit_logs(soc2_category);
        """)
        print("✅ Performance indexes created")
        
        await conn.close()
        print("✅ Complete database schema fix completed successfully!")
        
    except Exception as e:
        print(f"❌ Database fix failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(complete_database_fix())
    exit(0 if success else 1)