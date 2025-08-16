-- ============================================
-- IRIS API INTEGRATION + SOC2 AUDIT SYSTEM
-- PostgreSQL 15+ Schema with Advanced Features
-- ============================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "btree_gist";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "pg_partman";

-- Create custom types
CREATE TYPE api_status AS ENUM ('active', 'inactive', 'maintenance', 'deprecated');
CREATE TYPE request_status AS ENUM ('pending', 'in_progress', 'completed', 'failed', 'timeout', 'circuit_broken');
CREATE TYPE audit_event_type AS ENUM ('access', 'modify', 'delete', 'authenticate', 'authorize', 'api_call', 'purge', 'export', 'configuration_change');
CREATE TYPE data_classification AS ENUM ('public', 'internal', 'confidential', 'restricted', 'phi', 'pii');
CREATE TYPE purge_status AS ENUM ('scheduled', 'in_progress', 'completed', 'failed', 'overridden', 'suspended');
CREATE TYPE retention_reason AS ENUM ('legal_hold', 'active_investigation', 'compliance_audit', 'user_request', 'system_dependency');

-- ============================================
-- CORE SYSTEM TABLES
-- ============================================

-- System configuration with audit capability
CREATE TABLE system_configuration (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key VARCHAR(255) NOT NULL UNIQUE,
    value JSONB NOT NULL,
    encrypted BOOLEAN DEFAULT FALSE,
    data_classification data_classification DEFAULT 'internal',
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

-- Temporal history for configuration changes (SOC2 requirement)
CREATE TABLE system_configuration_history (
    history_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id UUID NOT NULL,
    key VARCHAR(255) NOT NULL,
    value JSONB NOT NULL,
    encrypted BOOLEAN,
    data_classification data_classification,
    description TEXT,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ NOT NULL,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    changed_by UUID NOT NULL,
    change_reason TEXT,
    version INTEGER NOT NULL
);

-- ============================================
-- USER & ACCESS MANAGEMENT
-- ============================================

-- Users table with enhanced security fields
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    email_verified BOOLEAN DEFAULT FALSE,
    username VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    mfa_secret VARCHAR(255),
    mfa_enabled BOOLEAN DEFAULT FALSE,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMPTZ,
    last_login_at TIMESTAMPTZ,
    last_login_ip INET,
    password_changed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    must_change_password BOOLEAN DEFAULT FALSE,
    api_key_hash VARCHAR(255) UNIQUE,
    api_key_last_used TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    is_system_user BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deactivated_at TIMESTAMPTZ,
    CONSTRAINT check_lock_validity CHECK (locked_until IS NULL OR locked_until > CURRENT_TIMESTAMP)
);

-- Roles with hierarchical support
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    parent_role_id UUID REFERENCES roles(id),
    is_system_role BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Permissions granular control
CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    resource VARCHAR(255) NOT NULL,
    action VARCHAR(100) NOT NULL,
    description TEXT,
    is_system_permission BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_resource_action UNIQUE (resource, action)
);

-- Role-Permission mapping
CREATE TABLE role_permissions (
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    granted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    granted_by UUID NOT NULL REFERENCES users(id),
    PRIMARY KEY (role_id, permission_id)
);

-- User-Role assignments with temporal validity
CREATE TABLE user_roles (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    valid_from TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    valid_to TIMESTAMPTZ,
    assigned_by UUID NOT NULL REFERENCES users(id),
    assignment_reason TEXT,
    PRIMARY KEY (user_id, role_id, valid_from),
    CONSTRAINT check_role_validity CHECK (valid_to IS NULL OR valid_to > valid_from)
);

-- ============================================
-- API INTEGRATION TABLES
-- ============================================

-- API Endpoints configuration
CREATE TABLE api_endpoints (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    base_url VARCHAR(500) NOT NULL,
    api_version VARCHAR(50),
    status api_status NOT NULL DEFAULT 'active',
    auth_type VARCHAR(50) NOT NULL CHECK (auth_type IN ('oauth2', 'hmac', 'jwt', 'api_key', 'basic')),
    rate_limit_requests INTEGER,
    rate_limit_window_seconds INTEGER,
    timeout_seconds INTEGER DEFAULT 30,
    retry_attempts INTEGER DEFAULT 3,
    retry_delay_seconds INTEGER DEFAULT 1,
    circuit_breaker_threshold INTEGER DEFAULT 5,
    circuit_breaker_timeout_seconds INTEGER DEFAULT 60,
    ssl_verify BOOLEAN DEFAULT TRUE,
    health_check_endpoint VARCHAR(500),
    health_check_interval_seconds INTEGER DEFAULT 300,
    last_health_check_at TIMESTAMPTZ,
    last_health_check_status BOOLEAN,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- API Credentials vault (encrypted storage)
CREATE TABLE api_credentials (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    api_endpoint_id UUID NOT NULL REFERENCES api_endpoints(id) ON DELETE CASCADE,
    credential_name VARCHAR(255) NOT NULL,
    encrypted_value TEXT NOT NULL, -- Always encrypted
    expires_at TIMESTAMPTZ,
    last_rotated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    rotation_reminder_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by UUID NOT NULL REFERENCES users(id),
    CONSTRAINT unique_endpoint_credential UNIQUE (api_endpoint_id, credential_name)
);

-- API Request tracking with comprehensive audit
CREATE TABLE api_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    api_endpoint_id UUID NOT NULL REFERENCES api_endpoints(id),
    correlation_id UUID NOT NULL, -- For request tracing
    user_id UUID REFERENCES users(id),
    method VARCHAR(20) NOT NULL,
    endpoint_path VARCHAR(500) NOT NULL,
    request_headers JSONB,
    request_body JSONB,
    request_hash VARCHAR(64), -- For deduplication
    response_status_code INTEGER,
    response_headers JSONB,
    response_body JSONB,
    status request_status NOT NULL DEFAULT 'pending',
    attempt_count INTEGER DEFAULT 1,
    total_duration_ms INTEGER,
    error_message TEXT,
    error_stack_trace TEXT,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,
    CONSTRAINT check_completion CHECK (
        (status IN ('completed', 'failed', 'timeout') AND completed_at IS NOT NULL) OR
        (status IN ('pending', 'in_progress') AND completed_at IS NULL)
    )
) PARTITION BY RANGE (created_at);

-- Create partitions for API requests (monthly)
CREATE TABLE api_requests_2025_01 PARTITION OF api_requests
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
CREATE TABLE api_requests_2025_02 PARTITION OF api_requests
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');
-- Continue creating partitions as needed...

-- API Response cache for performance
CREATE TABLE api_response_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cache_key VARCHAR(500) NOT NULL UNIQUE,
    api_endpoint_id UUID NOT NULL REFERENCES api_endpoints(id),
    response_data JSONB NOT NULL,
    ttl_seconds INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ NOT NULL GENERATED ALWAYS AS (created_at + (ttl_seconds || ' seconds')::INTERVAL) STORED,
    hit_count INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMPTZ
);

-- ============================================
-- AUDIT LOGGING TABLES (SOC2 COMPLIANT)
-- ============================================

-- Immutable audit log table (partitioned for performance)
CREATE TABLE audit_logs (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    event_type audit_event_type NOT NULL,
    user_id UUID REFERENCES users(id),
    session_id UUID,
    correlation_id UUID,
    resource_type VARCHAR(100),
    resource_id UUID,
    action VARCHAR(100) NOT NULL,
    result VARCHAR(50) NOT NULL CHECK (result IN ('success', 'failure', 'error', 'denied')),
    ip_address INET,
    user_agent TEXT,
    request_method VARCHAR(20),
    request_path VARCHAR(500),
    request_body_hash VARCHAR(64), -- Hash of request for integrity
    response_status_code INTEGER,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    compliance_tags TEXT[], -- SOC2, HIPAA, etc.
    data_classification data_classification,
    -- Integrity fields
    previous_log_hash VARCHAR(64),
    log_hash VARCHAR(64) NOT NULL, -- Hash of this record
    PRIMARY KEY (id, timestamp)
) PARTITION BY RANGE (timestamp);

-- No updates allowed on audit logs (SOC2 requirement)
CREATE RULE audit_logs_no_update AS ON UPDATE TO audit_logs DO INSTEAD NOTHING;
CREATE RULE audit_logs_no_delete AS ON DELETE TO audit_logs DO INSTEAD NOTHING;

-- Create monthly partitions for audit logs
CREATE TABLE audit_logs_2025_01 PARTITION OF audit_logs
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
CREATE TABLE audit_logs_2025_02 PARTITION OF audit_logs
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

-- Access logs for SOC2 user activity tracking
CREATE TABLE access_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    access_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resource_type VARCHAR(100) NOT NULL,
    resource_id UUID,
    access_type VARCHAR(50) NOT NULL CHECK (access_type IN ('view', 'download', 'export', 'share')),
    access_granted BOOLEAN NOT NULL,
    denial_reason TEXT,
    ip_address INET,
    geographic_location JSONB, -- For SOC2 location tracking
    device_fingerprint VARCHAR(255),
    session_id UUID,
    risk_score DECIMAL(3,2), -- 0.00 to 1.00
    metadata JSONB DEFAULT '{}'
);

-- ============================================
-- DATA RETENTION & PURGE MANAGEMENT
-- ============================================

-- Retention policies configuration
CREATE TABLE retention_policies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    table_name VARCHAR(255) NOT NULL,
    retention_days INTEGER NOT NULL CHECK (retention_days > 0),
    purge_strategy VARCHAR(50) NOT NULL CHECK (purge_strategy IN ('hard_delete', 'soft_delete', 'archive')),
    archive_table_name VARCHAR(255),
    filter_condition TEXT, -- SQL condition for selective purging
    is_active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 100,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Retention overrides for specific records
CREATE TABLE retention_overrides (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name VARCHAR(255) NOT NULL,
    record_id UUID NOT NULL,
    override_reason retention_reason NOT NULL,
    override_until TIMESTAMPTZ,
    requested_by UUID NOT NULL REFERENCES users(id),
    approved_by UUID REFERENCES users(id),
    approval_timestamp TIMESTAMPTZ,
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_table_record UNIQUE (table_name, record_id)
);

-- Purge execution history
CREATE TABLE purge_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    retention_policy_id UUID NOT NULL REFERENCES retention_policies(id),
    execution_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status purge_status NOT NULL DEFAULT 'scheduled',
    records_identified INTEGER,
    records_purged INTEGER,
    records_failed INTEGER,
    records_overridden INTEGER,
    execution_duration_ms INTEGER,
    error_message TEXT,
    error_details JSONB,
    dry_run BOOLEAN DEFAULT FALSE,
    executed_by UUID REFERENCES users(id),
    completion_timestamp TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'
);

-- ============================================
-- ENCRYPTION & KEY MANAGEMENT
-- ============================================

-- Encryption keys management
CREATE TABLE encryption_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key_name VARCHAR(255) NOT NULL UNIQUE,
    key_version INTEGER NOT NULL DEFAULT 1,
    algorithm VARCHAR(50) NOT NULL DEFAULT 'AES-256-GCM',
    encrypted_key TEXT NOT NULL, -- Key encrypted with master key
    key_purpose VARCHAR(100) NOT NULL CHECK (key_purpose IN ('data', 'api', 'audit', 'backup')),
    is_active BOOLEAN DEFAULT TRUE,
    valid_from TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    valid_to TIMESTAMPTZ,
    last_rotated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    rotation_schedule_days INTEGER DEFAULT 90,
    created_by UUID NOT NULL REFERENCES users(id),
    metadata JSONB DEFAULT '{}',
    CONSTRAINT unique_active_key UNIQUE (key_name, key_version)
);

-- Track encrypted fields for compliance
CREATE TABLE encrypted_fields_registry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name VARCHAR(255) NOT NULL,
    column_name VARCHAR(255) NOT NULL,
    encryption_key_id UUID NOT NULL REFERENCES encryption_keys(id),
    data_classification data_classification NOT NULL,
    is_searchable BOOLEAN DEFAULT FALSE, -- If using deterministic encryption
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_table_column UNIQUE (table_name, column_name)
);

-- ============================================
-- EVENT SOURCING SUPPORT
-- ============================================

-- Event store for event-driven architecture
CREATE TABLE event_store (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    aggregate_id UUID NOT NULL,
    aggregate_type VARCHAR(255) NOT NULL,
    event_type VARCHAR(255) NOT NULL,
    event_version INTEGER NOT NULL,
    event_data JSONB NOT NULL,
    metadata JSONB DEFAULT '{}',
    user_id UUID REFERENCES users(id),
    correlation_id UUID,
    causation_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_aggregate_version UNIQUE (aggregate_id, event_version)
);

-- Event projections status
CREATE TABLE event_projections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    projection_name VARCHAR(255) NOT NULL UNIQUE,
    last_processed_event_id UUID,
    last_processed_timestamp TIMESTAMPTZ,
    projection_version INTEGER NOT NULL DEFAULT 1,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    error_count INTEGER DEFAULT 0,
    last_error_message TEXT,
    last_error_timestamp TIMESTAMPTZ,
    checkpoint_data JSONB DEFAULT '{}',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- HEALTHCARE SPECIFIC (IRIS/FHIR)
-- ============================================

-- Patient data with PHI classification
CREATE TABLE patients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id VARCHAR(255) UNIQUE, -- IRIS patient ID
    mrn VARCHAR(100), -- Medical Record Number (encrypted)
    first_name_encrypted TEXT NOT NULL,
    last_name_encrypted TEXT NOT NULL,
    date_of_birth_encrypted TEXT NOT NULL,
    ssn_encrypted TEXT,
    data_classification data_classification DEFAULT 'phi',
    consent_status JSONB DEFAULT '{}',
    iris_sync_status VARCHAR(50),
    iris_last_sync_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    soft_deleted_at TIMESTAMPTZ
);

-- Immunization records
CREATE TABLE immunizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id),
    vaccine_code VARCHAR(50) NOT NULL,
    vaccine_name VARCHAR(255),
    administration_date DATE NOT NULL,
    lot_number VARCHAR(100),
    manufacturer VARCHAR(255),
    dose_number INTEGER,
    series_complete BOOLEAN DEFAULT FALSE,
    administered_by VARCHAR(255),
    administration_site VARCHAR(100),
    route VARCHAR(50),
    iris_record_id VARCHAR(255),
    data_source VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    soft_deleted_at TIMESTAMPTZ
);

-- ============================================
-- PERFORMANCE & MONITORING
-- ============================================

-- System metrics for monitoring
CREATE TABLE system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(255) NOT NULL,
    metric_value DECIMAL(20,4) NOT NULL,
    metric_unit VARCHAR(50),
    metric_type VARCHAR(50) NOT NULL CHECK (metric_type IN ('counter', 'gauge', 'histogram', 'summary')),
    tags JSONB DEFAULT '{}',
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (recorded_at);

-- Create daily partitions for metrics
CREATE TABLE system_metrics_2025_01_01 PARTITION OF system_metrics
    FOR VALUES FROM ('2025-01-01') TO ('2025-01-02');

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

-- User and access indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_api_key_hash ON users(api_key_hash) WHERE api_key_hash IS NOT NULL;
CREATE INDEX idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX idx_user_roles_temporal ON user_roles(user_id, valid_from, valid_to);

-- API request indexes
CREATE INDEX idx_api_requests_endpoint_created ON api_requests(api_endpoint_id, created_at DESC);
CREATE INDEX idx_api_requests_correlation ON api_requests(correlation_id);
CREATE INDEX idx_api_requests_user_created ON api_requests(user_id, created_at DESC) WHERE user_id IS NOT NULL;
CREATE INDEX idx_api_requests_status ON api_requests(status) WHERE status != 'completed';

-- Audit log indexes (critical for SOC2 queries)
CREATE INDEX idx_audit_logs_user_timestamp ON audit_logs(user_id, timestamp DESC);
CREATE INDEX idx_audit_logs_event_type ON audit_logs(event_type, timestamp DESC);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id, timestamp DESC);
CREATE INDEX idx_audit_logs_compliance ON audit_logs USING GIN(compliance_tags);
CREATE INDEX idx_audit_logs_correlation ON audit_logs(correlation_id) WHERE correlation_id IS NOT NULL;

-- Access log indexes
CREATE INDEX idx_access_logs_user_timestamp ON access_logs(user_id, access_timestamp DESC);
CREATE INDEX idx_access_logs_resource ON access_logs(resource_type, resource_id);
CREATE INDEX idx_access_logs_denied ON access_logs(access_timestamp DESC) WHERE access_granted = FALSE;

-- Retention and purge indexes
CREATE INDEX idx_retention_overrides_active ON retention_overrides(table_name, record_id) WHERE is_active = TRUE;
CREATE INDEX idx_purge_executions_policy ON purge_executions(retention_policy_id, execution_timestamp DESC);

-- Event store indexes
CREATE INDEX idx_event_store_aggregate ON event_store(aggregate_id, event_version);
CREATE INDEX idx_event_store_correlation ON event_store(correlation_id) WHERE correlation_id IS NOT NULL;
CREATE INDEX idx_event_store_created ON event_store(created_at);

-- Healthcare indexes
CREATE INDEX idx_patients_external_id ON patients(external_id) WHERE external_id IS NOT NULL;
CREATE INDEX idx_immunizations_patient ON immunizations(patient_id, administration_date DESC);
CREATE INDEX idx_immunizations_iris ON immunizations(iris_record_id) WHERE iris_record_id IS NOT NULL;

-- Full text search indexes
CREATE INDEX idx_audit_logs_metadata ON audit_logs USING GIN(metadata);
CREATE INDEX idx_api_requests_error_search ON api_requests USING GIN(to_tsvector('english', error_message));

-- ============================================
-- CONSTRAINTS & TRIGGERS
-- ============================================

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

CREATE TRIGGER audit_log_hash_trigger
BEFORE INSERT ON audit_logs
FOR EACH ROW
EXECUTE FUNCTION calculate_log_hash();

-- Function to update modified_at timestamp
CREATE OR REPLACE FUNCTION update_modified_at() RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply update trigger to relevant tables
CREATE TRIGGER update_system_configuration_modtime
BEFORE UPDATE ON system_configuration
FOR EACH ROW
EXECUTE FUNCTION update_modified_at();

CREATE TRIGGER update_users_modtime
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION update_modified_at();

-- Function to archive configuration changes
CREATE OR REPLACE FUNCTION archive_configuration_change() RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO system_configuration_history (
        id, key, value, encrypted, data_classification,
        description, valid_from, valid_to, changed_by,
        change_reason, version
    ) VALUES (
        OLD.id, OLD.key, OLD.value, OLD.encrypted, OLD.data_classification,
        OLD.description, OLD.valid_from, CURRENT_TIMESTAMP, NEW.modified_by,
        'Automatic archive on update', OLD.version
    );
    
    NEW.version := OLD.version + 1;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER archive_config_on_update
BEFORE UPDATE ON system_configuration
FOR EACH ROW
WHEN (OLD.* IS DISTINCT FROM NEW.*)
EXECUTE FUNCTION archive_configuration_change();

-- Function to validate retention override dates
CREATE OR REPLACE FUNCTION validate_retention_override() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.override_until IS NOT NULL AND NEW.override_until <= CURRENT_TIMESTAMP THEN
        RAISE EXCEPTION 'Override until date must be in the future';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER validate_retention_override_trigger
BEFORE INSERT OR UPDATE ON retention_overrides
FOR EACH ROW
EXECUTE FUNCTION validate_retention_override();

-- ============================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================

-- Enable RLS on sensitive tables
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE immunizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_credentials ENABLE ROW LEVEL SECURITY;

-- Example RLS policy for patients (customize based on requirements)
CREATE POLICY patients_access_policy ON patients
    FOR ALL
    TO application_role
    USING (
        EXISTS (
            SELECT 1 FROM user_roles ur
            JOIN roles r ON ur.role_id = r.id
            JOIN role_permissions rp ON r.id = rp.role_id
            JOIN permissions p ON rp.permission_id = p.id
            WHERE ur.user_id = current_setting('app.current_user_id')::UUID
            AND p.resource = 'patients'
            AND p.action IN ('read', 'write')
            AND (ur.valid_to IS NULL OR ur.valid_to > CURRENT_TIMESTAMP)
        )
    );

-- ============================================
-- MAINTENANCE PROCEDURES
-- ============================================

-- Procedure to rotate partition tables
CREATE OR REPLACE PROCEDURE create_monthly_partitions(
    table_name TEXT,
    months_ahead INTEGER DEFAULT 3
) AS $$
DECLARE
    start_date DATE;
    end_date DATE;
    partition_name TEXT;
    i INTEGER;
BEGIN
    FOR i IN 0..months_ahead LOOP
        start_date := DATE_TRUNC('month', CURRENT_DATE + (i || ' months')::INTERVAL);
        end_date := start_date + INTERVAL '1 month';
        partition_name := table_name || '_' || TO_CHAR(start_date, 'YYYY_MM');
        
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS %I PARTITION OF %I FOR VALUES FROM (%L) TO (%L)',
            partition_name, table_name, start_date, end_date
        );
    END LOOP;
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

-- ============================================
-- INITIAL DATA & PERMISSIONS
-- ============================================

-- Create system user
INSERT INTO users (id, email, username, password_hash, is_system_user, is_active)
VALUES (
    '00000000-0000-0000-0000-000000000000',
    'system@internal',
    'system',
    'NO_LOGIN',
    TRUE,
    TRUE
);

-- Create default roles
INSERT INTO roles (name, description, is_system_role) VALUES
    ('super_admin', 'Full system access', TRUE),
    ('admin', 'Administrative access', TRUE),
    ('operator', 'Operational access', TRUE),
    ('auditor', 'Read-only audit access', TRUE),
    ('api_user', 'API access only', TRUE);

-- Create base permissions
INSERT INTO permissions (resource, action, description, is_system_permission) VALUES
    ('system', 'manage', 'Full system management', TRUE),
    ('users', 'create', 'Create users', TRUE),
    ('users', 'read', 'View users', TRUE),
    ('users', 'update', 'Update users', TRUE),
    ('users', 'delete', 'Delete users', TRUE),
    ('audit_logs', 'read', 'View audit logs', TRUE),
    ('api_endpoints', 'manage', 'Manage API endpoints', TRUE),
    ('retention_policies', 'manage', 'Manage retention policies', TRUE),
    ('patients', 'read', 'View patient data', TRUE),
    ('patients', 'write', 'Modify patient data', TRUE);

-- Grant permissions to super_admin role
INSERT INTO role_permissions (role_id, permission_id, granted_by)
SELECT r.id, p.id, '00000000-0000-0000-0000-000000000000'
FROM roles r, permissions p
WHERE r.name = 'super_admin';

-- ============================================
-- PERFORMANCE VIEWS
-- ============================================

-- View for active user sessions
CREATE VIEW active_user_sessions AS
SELECT 
    u.id,
    u.email,
    u.last_login_at,
    u.last_login_ip,
    COUNT(DISTINCT al.session_id) as active_sessions,
    MAX(al.timestamp) as last_activity
FROM users u
LEFT JOIN audit_logs al ON u.id = al.user_id 
    AND al.timestamp > CURRENT_TIMESTAMP - INTERVAL '30 minutes'
WHERE u.is_active = TRUE
GROUP BY u.id, u.email, u.last_login_at, u.last_login_ip;

-- View for API endpoint health
CREATE VIEW api_endpoint_health AS
SELECT 
    ae.id,
    ae.name,
    ae.status,
    ae.last_health_check_status,
    COUNT(ar.id) FILTER (WHERE ar.created_at > CURRENT_TIMESTAMP - INTERVAL '1 hour') as requests_last_hour,
    AVG(ar.total_duration_ms) FILTER (WHERE ar.created_at > CURRENT_TIMESTAMP - INTERVAL '1 hour') as avg_duration_ms,
    COUNT(ar.id) FILTER (WHERE ar.status = 'failed' AND ar.created_at > CURRENT_TIMESTAMP - INTERVAL '1 hour') as failures_last_hour
FROM api_endpoints ae
LEFT JOIN api_requests ar ON ae.id = ar.api_endpoint_id
GROUP BY ae.id, ae.name, ae.status, ae.last_health_check_status;

-- View for retention policy status
CREATE VIEW retention_policy_status AS
SELECT 
    rp.id,
    rp.name,
    rp.table_name,
    rp.retention_days,
    pe.execution_timestamp as last_execution,
    pe.status as last_status,
    pe.records_purged as last_records_purged,
    COUNT(ro.id) as active_overrides
FROM retention_policies rp
LEFT JOIN LATERAL (
    SELECT * FROM purge_executions 
    WHERE retention_policy_id = rp.id 
    ORDER BY execution_timestamp DESC 
    LIMIT 1
) pe ON TRUE
LEFT JOIN retention_overrides ro ON ro.table_name = rp.table_name AND ro.is_active = TRUE
WHERE rp.is_active = TRUE
GROUP BY rp.id, rp.name, rp.table_name, rp.retention_days, 
         pe.execution_timestamp, pe.status, pe.records_purged;

-- ============================================
-- MAINTENANCE COMMENTS
-- ============================================

COMMENT ON SCHEMA public IS 'IRIS API Integration + SOC2 Audit System - Production Schema';
COMMENT ON TABLE audit_logs IS 'Immutable audit trail for SOC2 compliance - NO UPDATES OR DELETES ALLOWED';
COMMENT ON TABLE api_credentials IS 'Encrypted storage for API credentials - all values must be encrypted before storage';
COMMENT ON TABLE patients IS 'PHI data storage - all PII fields must be encrypted';
COMMENT ON COLUMN audit_logs.log_hash IS 'SHA-256 hash for log integrity verification - forms blockchain-like structure';
COMMENT ON COLUMN retention_overrides.override_reason IS 'Legal/compliance reason for retention override - must be documented';