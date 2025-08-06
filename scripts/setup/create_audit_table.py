#!/usr/bin/env python3
"""Create audit_logs table directly."""

import asyncio
import asyncpg

async def create_audit_table():
    try:
        conn = await asyncpg.connect(
            "postgresql://test_user:test_password@localhost:5433/test_iris_db"
        )
        
        print("=== CREATING AUDIT_LOGS TABLE ===")
        
        # Drop table if exists
        await conn.execute("DROP TABLE IF EXISTS audit_logs CASCADE;")
        print("✅ Dropped existing audit_logs table")
        
        # Create audit_logs table
        create_table_sql = """
        CREATE TABLE audit_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
            event_type VARCHAR(100) NOT NULL,
            user_id UUID,
            session_id UUID,
            correlation_id UUID,
            resource_type VARCHAR(100),
            resource_id UUID,
            action VARCHAR(100) NOT NULL,
            result VARCHAR(50) NOT NULL,
            ip_address INET,
            user_agent TEXT,
            request_method VARCHAR(10),
            request_path VARCHAR(500),
            request_body_hash VARCHAR(64),
            response_status_code INTEGER,
            error_message TEXT,
            config_metadata JSONB,
            compliance_tags TEXT[],
            data_classification VARCHAR(20) DEFAULT 'internal',
            previous_log_hash VARCHAR(64)
        );
        """
        
        await conn.execute(create_table_sql)
        print("✅ Created audit_logs table")
        
        # Create indexes
        indexes = [
            "CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);",
            "CREATE INDEX idx_audit_logs_event_type ON audit_logs(event_type);",
            "CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);",
        ]
        
        for index_sql in indexes:
            await conn.execute(index_sql)
        
        print("✅ Created indexes")
        
        # Insert test record
        test_insert = """
        INSERT INTO audit_logs (event_type, action, result, config_metadata) 
        VALUES ('user_login', 'test', 'success', '{"test": true}');
        """
        await conn.execute(test_insert)
        print("✅ Inserted test record")
        
        # Verify
        count = await conn.fetchval("SELECT COUNT(*) FROM audit_logs;")
        print(f"✅ Table created successfully with {count} records")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Failed to create table: {e}")

if __name__ == "__main__":
    asyncio.run(create_audit_table())