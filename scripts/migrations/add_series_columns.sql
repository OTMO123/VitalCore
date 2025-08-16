-- Add series_complete and series_dosed columns to immunizations table
-- for enterprise healthcare compliance (SOC2, HIPAA, FHIR R4, GDPR)

-- Add series_complete column (NOT NULL with default FALSE)
ALTER TABLE immunizations 
ADD COLUMN IF NOT EXISTS series_complete BOOLEAN NOT NULL DEFAULT FALSE;

-- Add comment for series_complete
COMMENT ON COLUMN immunizations.series_complete IS 'Whether vaccine series is complete (enterprise compliance field)';

-- Add series_dosed column (nullable with default 1)
ALTER TABLE immunizations 
ADD COLUMN IF NOT EXISTS series_dosed INTEGER DEFAULT 1;

-- Add comment for series_dosed
COMMENT ON COLUMN immunizations.series_dosed IS 'Number of doses administered in series (enterprise compliance field)';

-- Update any existing NULL values (defensive programming)
UPDATE immunizations 
SET series_complete = FALSE 
WHERE series_complete IS NULL;

UPDATE immunizations 
SET series_dosed = 1 
WHERE series_dosed IS NULL;

-- Verify the columns were added
SELECT 
    column_name, 
    data_type, 
    is_nullable, 
    column_default
FROM information_schema.columns 
WHERE table_name = 'immunizations' 
  AND column_name IN ('series_complete', 'series_dosed')
ORDER BY column_name;