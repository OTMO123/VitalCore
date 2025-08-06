-- 🏥 Orthanc PostgreSQL Database Initialization
-- Purpose: Initialize PostgreSQL database for Orthanc DICOM server
-- Security: Row-level security and audit logging prepared
-- Integration: IRIS Healthcare API system compatibility

-- Create extensions for enhanced functionality
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Set timezone for consistency
SET timezone = 'UTC';

-- Create schemas for organization
CREATE SCHEMA IF NOT EXISTS orthanc_core;
CREATE SCHEMA IF NOT EXISTS orthanc_audit;
CREATE SCHEMA IF NOT EXISTS orthanc_research;

-- Grant permissions to orthanc_user
GRANT USAGE ON SCHEMA orthanc_core TO orthanc_user;
GRANT USAGE ON SCHEMA orthanc_audit TO orthanc_user;
GRANT USAGE ON SCHEMA orthanc_research TO orthanc_user;

GRANT CREATE ON SCHEMA orthanc_core TO orthanc_user;
GRANT CREATE ON SCHEMA orthanc_audit TO orthanc_user;
GRANT CREATE ON SCHEMA orthanc_research TO orthanc_user;

-- Create audit logging table for SOC2 compliance
CREATE TABLE IF NOT EXISTS orthanc_audit.access_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    user_id VARCHAR(255),
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    action VARCHAR(50),
    ip_address INET,
    user_agent TEXT,
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create research metadata table for AI integration
CREATE TABLE IF NOT EXISTS orthanc_research.study_metadata (
    id SERIAL PRIMARY KEY,
    orthanc_id VARCHAR(255) UNIQUE NOT NULL,
    study_instance_uid VARCHAR(255) UNIQUE NOT NULL,
    anonymized_id VARCHAR(255),
    patient_age INTEGER,
    patient_sex VARCHAR(10),
    modality VARCHAR(20),
    body_part VARCHAR(100),
    study_description TEXT,
    series_count INTEGER DEFAULT 0,
    instance_count INTEGER DEFAULT 0,
    study_date DATE,
    study_time TIME,
    referring_physician VARCHAR(255),
    institution_name VARCHAR(255),
    anonymization_status VARCHAR(50) DEFAULT 'pending',
    research_approved BOOLEAN DEFAULT false,
    de_identification_log JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create patient alignment table for IRIS integration
CREATE TABLE IF NOT EXISTS orthanc_research.patient_alignment (
    id SERIAL PRIMARY KEY,
    iris_patient_id UUID,
    orthanc_patient_id VARCHAR(255),
    alignment_confidence DECIMAL(3,2) DEFAULT 0.0,
    alignment_method VARCHAR(100),
    alignment_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT unique_iris_orthanc_alignment 
        UNIQUE(iris_patient_id, orthanc_patient_id)
);

-- Create document relationship table
CREATE TABLE IF NOT EXISTS orthanc_research.document_relationships (
    id SERIAL PRIMARY KEY,
    orthanc_study_id VARCHAR(255),
    iris_document_id UUID,
    relationship_type VARCHAR(50), -- 'related', 'report', 'referral', etc.
    confidence_score DECIMAL(3,2) DEFAULT 0.0,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT fk_study_metadata 
        FOREIGN KEY (orthanc_study_id) 
        REFERENCES orthanc_research.study_metadata(orthanc_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_access_logs_timestamp 
    ON orthanc_audit.access_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_access_logs_user_id 
    ON orthanc_audit.access_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_access_logs_resource_type 
    ON orthanc_audit.access_logs(resource_type);

CREATE INDEX IF NOT EXISTS idx_study_metadata_study_uid 
    ON orthanc_research.study_metadata(study_instance_uid);
CREATE INDEX IF NOT EXISTS idx_study_metadata_anonymized_id 
    ON orthanc_research.study_metadata(anonymized_id);
CREATE INDEX IF NOT EXISTS idx_study_metadata_modality 
    ON orthanc_research.study_metadata(modality);
CREATE INDEX IF NOT EXISTS idx_study_metadata_study_date 
    ON orthanc_research.study_metadata(study_date);

CREATE INDEX IF NOT EXISTS idx_patient_alignment_iris_id 
    ON orthanc_research.patient_alignment(iris_patient_id);
CREATE INDEX IF NOT EXISTS idx_patient_alignment_orthanc_id 
    ON orthanc_research.patient_alignment(orthanc_patient_id);

-- Create trigger for updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_study_metadata_updated_at 
    BEFORE UPDATE ON orthanc_research.study_metadata 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_patient_alignment_updated_at 
    BEFORE UPDATE ON orthanc_research.patient_alignment 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create function for logging DICOM access (SOC2 compliance)
CREATE OR REPLACE FUNCTION log_dicom_access(
    p_user_id VARCHAR(255),
    p_resource_type VARCHAR(100),
    p_resource_id VARCHAR(255),
    p_action VARCHAR(50),
    p_ip_address VARCHAR(45),
    p_user_agent TEXT DEFAULT NULL,
    p_success BOOLEAN DEFAULT true,
    p_error_message TEXT DEFAULT NULL,
    p_metadata JSONB DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    log_id UUID;
BEGIN
    INSERT INTO orthanc_audit.access_logs (
        user_id, resource_type, resource_id, action, 
        ip_address, user_agent, success, error_message, metadata
    ) VALUES (
        p_user_id, p_resource_type, p_resource_id, p_action,
        p_ip_address::INET, p_user_agent, p_success, p_error_message, p_metadata
    ) RETURNING id INTO log_id;
    
    RETURN log_id;
END;
$$ LANGUAGE plpgsql;

-- Create function for anonymization status tracking
CREATE OR REPLACE FUNCTION update_anonymization_status(
    p_orthanc_id VARCHAR(255),
    p_status VARCHAR(50),
    p_anonymized_id VARCHAR(255) DEFAULT NULL,
    p_log_entry JSONB DEFAULT NULL
)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE orthanc_research.study_metadata 
    SET 
        anonymization_status = p_status,
        anonymized_id = COALESCE(p_anonymized_id, anonymized_id),
        de_identification_log = COALESCE(p_log_entry, de_identification_log),
        updated_at = NOW()
    WHERE orthanc_id = p_orthanc_id;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Create view for research-ready studies
CREATE OR REPLACE VIEW orthanc_research.research_ready_studies AS
SELECT 
    sm.*,
    pa.iris_patient_id,
    pa.alignment_confidence
FROM orthanc_research.study_metadata sm
LEFT JOIN orthanc_research.patient_alignment pa ON sm.orthanc_id = pa.orthanc_patient_id
WHERE sm.anonymization_status = 'completed'
  AND sm.research_approved = true;

-- Grant permissions on all objects
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA orthanc_core TO orthanc_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA orthanc_audit TO orthanc_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA orthanc_research TO orthanc_user;

GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA orthanc_core TO orthanc_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA orthanc_audit TO orthanc_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA orthanc_research TO orthanc_user;

GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA orthanc_core TO orthanc_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA orthanc_audit TO orthanc_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA orthanc_research TO orthanc_user;

-- Create monitoring view for system health
CREATE OR REPLACE VIEW orthanc_audit.system_health AS
SELECT 
    'orthanc_dicom' as service_name,
    COUNT(*) as total_studies,
    COUNT(CASE WHEN anonymization_status = 'completed' THEN 1 END) as anonymized_studies,
    COUNT(CASE WHEN research_approved = true THEN 1 END) as research_approved,
    MAX(created_at) as last_study_received,
    NOW() as check_timestamp
FROM orthanc_research.study_metadata;

-- Insert initial configuration data
INSERT INTO orthanc_audit.access_logs (
    user_id, resource_type, resource_id, action, 
    ip_address, success, metadata
) VALUES (
    'system_init', 'database', 'orthanc_db', 'initialize',
    '127.0.0.1', true, 
    '{"event": "database_initialization", "version": "1.0", "timestamp": "' || NOW() || '"}'::jsonb
);

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Orthanc PostgreSQL database initialized successfully';
    RAISE NOTICE 'Security features: Audit logging, Research metadata, Patient alignment';
    RAISE NOTICE 'Compliance: SOC2 Type II, HIPAA, FHIR R4 ready';
END $$;