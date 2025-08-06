"""Initialize audit_logs table if it doesn't exist."""

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

async def ensure_audit_table_exists(db: AsyncSession) -> bool:
    """
    Ensure audit_logs table exists, create if not.
    Returns True if table exists or was created successfully.
    """
    try:
        # Check if table exists
        check_query = text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'audit_logs'
            );
        """)
        
        table_exists = await db.execute(check_query)
        exists = table_exists.scalar()
        
        if exists:
            logger.info("✅ audit_logs table already exists")
            return True
        
        logger.info("🔨 Creating audit_logs table...")
        
        # Create table
        create_table_query = text("""
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
        """)
        
        await db.execute(create_table_query)
        
        # Create indexes
        indexes = [
            "CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);",
            "CREATE INDEX idx_audit_logs_event_type ON audit_logs(event_type);", 
            "CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);"
        ]
        
        for index_sql in indexes:
            await db.execute(text(index_sql))
        
        # Insert initial record
        init_query = text("""
            INSERT INTO audit_logs (event_type, action, result, config_metadata) 
            VALUES ('system_startup', 'audit_table_created', 'success', '{"auto_created": true, "compliance": "SOC2_Type_II"}');
        """)
        
        await db.execute(init_query)
        await db.commit()
        
        # Verify table was created
        verify_query = text("SELECT COUNT(*) FROM audit_logs;")
        count_result = await db.execute(verify_query)
        record_count = count_result.scalar()
        
        logger.info(f"✅ audit_logs table created successfully with {record_count} records")
        return True
        
    except Exception as e:
        logger.error("❌ Failed to create audit_logs table", error=str(e))
        return False