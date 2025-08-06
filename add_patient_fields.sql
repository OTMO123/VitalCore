-- Add missing gender and active fields to patients table
-- Run this SQL script directly on the PostgreSQL database

-- Add gender field (nullable string, 20 characters max)
ALTER TABLE patients ADD COLUMN IF NOT EXISTS gender VARCHAR(20);

-- Add active field (boolean with default true)
ALTER TABLE patients ADD COLUMN IF NOT EXISTS active BOOLEAN DEFAULT true NOT NULL;

-- Update existing patients to have active=true if null
UPDATE patients SET active = true WHERE active IS NULL;

-- Verify the changes
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'patients' 
AND column_name IN ('gender', 'active')
ORDER BY column_name;