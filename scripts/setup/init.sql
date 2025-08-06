-- ============================================
-- IRIS API INTEGRATION + SOC2 AUDIT SYSTEM
-- PostgreSQL 15+ Schema with Advanced Features
-- ============================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "btree_gist";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create custom types (will be created by Alembic migrations)
-- Note: Custom types moved to migrations for better version control

-- Create system user for automated operations
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'system_user') THEN
      CREATE ROLE system_user NOLOGIN;
   END IF;
END
$$;

-- System configuration with audit capability (simplified for init)
-- Note: Full table with custom types will be created by Alembic migrations
CREATE TABLE IF NOT EXISTS system_configuration (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key VARCHAR(255) NOT NULL UNIQUE,
    value JSONB NOT NULL,
    encrypted BOOLEAN DEFAULT FALSE,
    data_classification TEXT DEFAULT 'internal',
    description TEXT,
    valid_from TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    valid_to TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by UUID NOT NULL,
    modified_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_by UUID NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    CONSTRAINT check_valid_dates CHECK (valid_to IS NULL OR valid_to > valid_from)
);

-- Insert essential system configuration
INSERT INTO system_configuration (key, value, description, created_by, modified_by) VALUES
    ('system.name', '"IRIS API Integration System"', 'System name', uuid_generate_v4(), uuid_generate_v4()),
    ('system.version', '"1.0.0"', 'System version', uuid_generate_v4(), uuid_generate_v4()),
    ('audit.enabled', 'true', 'Enable audit logging', uuid_generate_v4(), uuid_generate_v4()),
    ('purge.enabled', 'true', 'Enable data purging', uuid_generate_v4(), uuid_generate_v4())
ON CONFLICT (key) DO NOTHING;

-- Function to calculate log hash for integrity
CREATE OR REPLACE FUNCTION calculate_log_hash() RETURNS TRIGGER AS $$
DECLARE
    previous_hash VARCHAR(64);
    content_to_hash TEXT;
BEGIN
    -- Get the previous log hash
    SELECT log_hash INTO previous_hash
    FROM audit_logs
    WHERE timestamp < NEW.timestamp
    ORDER BY timestamp DESC
    LIMIT 1;
    
    -- If no previous hash, use a known starting value
    IF previous_hash IS NULL THEN
        previous_hash := 'GENESIS_BLOCK_HASH';
    END IF;
    
    -- Concatenate fields for hashing
    content_to_hash := COALESCE(previous_hash, '') || 
                      NEW.id::TEXT || 
                      NEW.timestamp::TEXT || 
                      NEW.event_type::TEXT || 
                      COALESCE(NEW.user_id::TEXT, '') || 
                      NEW.action || 
                      NEW.result;
    
    -- Calculate hash
    NEW.previous_log_hash := previous_hash;
    NEW.log_hash := encode(digest(content_to_hash, 'sha256'), 'hex');
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to update modified_at timestamp
CREATE OR REPLACE FUNCTION update_modified_at() RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Procedure to verify audit log integrity
CREATE OR REPLACE FUNCTION verify_audit_log_integrity(
    start_time TIMESTAMPTZ DEFAULT CURRENT_DATE - INTERVAL '1 day',
    end_time TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
) RETURNS TABLE (
    log_id UUID,
    is_valid BOOLEAN,
    error_message TEXT
) AS $$
DECLARE
    log_record RECORD;
    calculated_hash VARCHAR(64);
    content_to_hash TEXT;
BEGIN
    FOR log_record IN 
        SELECT * FROM audit_logs 
        WHERE timestamp BETWEEN start_time AND end_time 
        ORDER BY timestamp
    LOOP
        -- Calculate expected hash
        content_to_hash := COALESCE(log_record.previous_log_hash, '') || 
                          log_record.id::TEXT || 
                          log_record.timestamp::TEXT || 
                          log_record.event_type::TEXT || 
                          COALESCE(log_record.user_id::TEXT, '') || 
                          log_record.action || 
                          log_record.result;
        
        calculated_hash := encode(digest(content_to_hash, 'sha256'), 'hex');
        
        IF calculated_hash != log_record.log_hash THEN
            RETURN QUERY SELECT 
                log_record.id, 
                FALSE, 
                'Hash mismatch: expected ' || calculated_hash || ' but found ' || log_record.log_hash;
        ELSE
            RETURN QUERY SELECT log_record.id, TRUE, NULL::TEXT;
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Views for monitoring and reporting
-- Note: audit_log_summary view will be created by migrations after audit_logs table exists

COMMENT ON SCHEMA public IS 'IRIS API Integration + SOC2 Audit System - Production Schema';