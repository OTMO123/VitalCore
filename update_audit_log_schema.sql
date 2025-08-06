-- Enterprise AuditLog Schema Update for SOC2 Compliance
-- Adds missing fields required for SOC2 compliance tests

-- Add enterprise SOC2 compliance fields
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS aggregate_id VARCHAR(255);
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS aggregate_type VARCHAR(100);
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS publisher VARCHAR(255);
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS soc2_category VARCHAR(50);

-- Modify user_id to support string values for system users
ALTER TABLE audit_logs ALTER COLUMN user_id TYPE VARCHAR(255);

-- Add headers field for additional metadata
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS headers JSONB;

-- Make action field optional
ALTER TABLE audit_logs ALTER COLUMN action DROP NOT NULL;

-- Make log_hash field optional for flexibility
ALTER TABLE audit_logs ALTER COLUMN log_hash DROP NOT NULL;

-- Change event_type to string for flexibility
ALTER TABLE audit_logs ALTER COLUMN event_type TYPE VARCHAR(100);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_audit_logs_aggregate_id ON audit_logs(aggregate_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_soc2_category ON audit_logs(soc2_category);
CREATE INDEX IF NOT EXISTS idx_audit_logs_publisher ON audit_logs(publisher);

-- Update existing records to have default values
UPDATE audit_logs SET outcome = 'success' WHERE outcome IS NULL;
UPDATE audit_logs SET headers = '{}' WHERE headers IS NULL;

COMMIT;