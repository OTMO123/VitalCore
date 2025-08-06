-- Fix last_login_ip column type from VARCHAR to INET
-- This addresses the specific infrastructure test failure

BEGIN;

-- First, check if the column exists and its current type
DO $$
BEGIN
    -- Only proceed if the column is currently VARCHAR type
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'users' 
        AND column_name = 'last_login_ip' 
        AND data_type = 'character varying'
    ) THEN
        -- Convert the column to INET type
        ALTER TABLE users 
        ALTER COLUMN last_login_ip 
        TYPE INET 
        USING last_login_ip::INET;
        
        RAISE NOTICE 'Successfully converted last_login_ip from VARCHAR to INET';
    ELSE
        RAISE NOTICE 'Column last_login_ip not found or already correct type';
    END IF;
END $$;

COMMIT;