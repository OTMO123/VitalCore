-- Enterprise Healthcare Database Initialization
-- SOC2 Type II + HIPAA + FHIR R4 + GDPR Compliance Extensions
-- This script ensures required PostgreSQL extensions are available

-- Enable required enterprise security extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "citext";

-- Create enterprise schemas if they don't exist
CREATE SCHEMA IF NOT EXISTS audit;
CREATE SCHEMA IF NOT EXISTS healthcare; 
CREATE SCHEMA IF NOT EXISTS security;

-- Grant usage permissions
GRANT USAGE ON SCHEMA audit TO postgres;
GRANT USAGE ON SCHEMA healthcare TO postgres;
GRANT USAGE ON SCHEMA security TO postgres;

-- Log database initialization for compliance
DO $$
BEGIN
    RAISE NOTICE 'IRIS Healthcare Enterprise Database Extensions Initialized';
    RAISE NOTICE 'SOC2 Type II + HIPAA + FHIR R4 + GDPR Compliance Extensions Ready';
    RAISE NOTICE 'Available Extensions: uuid-ossp, pgcrypto, citext';
END
$$;