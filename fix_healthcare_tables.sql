
-- Healthcare Tables Fix for 500 Errors
-- This ensures all required tables exist

-- Patients table (if missing)
CREATE TABLE IF NOT EXISTS patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fhir_id VARCHAR(255) UNIQUE,
    identifier VARCHAR(255),
    active BOOLEAN DEFAULT true,
    name_family VARCHAR(255),
    name_given VARCHAR(255),
    gender VARCHAR(10),
    birth_date DATE,
    phone VARCHAR(50),
    email VARCHAR(255),
    address_line VARCHAR(255),
    address_city VARCHAR(100),
    address_state VARCHAR(50),
    address_postal_code VARCHAR(20),
    address_country VARCHAR(50),
    marital_status VARCHAR(50),
    communication_language VARCHAR(10),
    general_practitioner VARCHAR(255),
    managing_organization VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    encrypted_data JSONB,
    metadata JSONB
);

-- Immunizations table (if missing)
CREATE TABLE IF NOT EXISTS immunizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fhir_id VARCHAR(255) UNIQUE,
    patient_id UUID REFERENCES patients(id),
    status VARCHAR(20) DEFAULT 'completed',
    vaccine_code VARCHAR(50),
    vaccine_display VARCHAR(255),
    vaccine_system VARCHAR(255),
    occurrence_datetime TIMESTAMP WITH TIME ZONE,
    recorded_date TIMESTAMP WITH TIME ZONE,
    location VARCHAR(255),
    primary_source BOOLEAN DEFAULT true,
    lot_number VARCHAR(100),
    expiration_date DATE,
    manufacturer VARCHAR(255),
    route_code VARCHAR(50),
    route_display VARCHAR(255),
    site_code VARCHAR(50),
    site_display VARCHAR(255),
    dose_quantity_value DECIMAL(10,2),
    dose_quantity_unit VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    encrypted_data JSONB,
    metadata JSONB
);

-- Clinical documents table (if missing)
CREATE TABLE IF NOT EXISTS clinical_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id),
    document_type VARCHAR(100),
    title VARCHAR(255),
    status VARCHAR(20) DEFAULT 'current',
    date_created TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    author VARCHAR(255),
    content TEXT,
    fhir_resource JSONB,
    classification VARCHAR(100),
    security_label VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    encrypted_data JSONB,
    metadata JSONB
);

-- Consent records table (if missing)
CREATE TABLE IF NOT EXISTS consent_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id),
    status VARCHAR(20) DEFAULT 'active',
    scope VARCHAR(100),
    category VARCHAR(100),
    date_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    source_reference VARCHAR(255),
    policy_rule VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_patients_fhir_id ON patients(fhir_id);
CREATE INDEX IF NOT EXISTS idx_patients_identifier ON patients(identifier);
CREATE INDEX IF NOT EXISTS idx_immunizations_patient_id ON immunizations(patient_id);
CREATE INDEX IF NOT EXISTS idx_immunizations_vaccine_code ON immunizations(vaccine_code);
CREATE INDEX IF NOT EXISTS idx_clinical_documents_patient_id ON clinical_documents(patient_id);

-- Ensure audit logs table exists with proper structure
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id VARCHAR(255) UNIQUE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR(255),
    event_type VARCHAR(100),
    operation VARCHAR(100),
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    outcome VARCHAR(20),
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(255),
    session_id VARCHAR(255),
    additional_data JSONB,
    sequence_number BIGSERIAL,
    integrity_hash VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type ON audit_logs(event_type);
