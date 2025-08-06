-- IRIS Healthcare Platform Database Initialization
-- Create database and initial setup

-- Create the database user if it doesn't exist
DO
$body$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_user 
      WHERE usename = 'iris_user') THEN
      
      CREATE USER iris_user WITH PASSWORD 'iris_secure_password';
   END IF;
END
$body$;

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE iris_db TO iris_user;

-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Set timezone
SET timezone = 'UTC';

-- Log completion
SELECT 'Database initialization completed' as status;