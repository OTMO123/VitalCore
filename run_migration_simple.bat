@echo off
echo Enterprise Healthcare Database Migration - Simple Version
echo Adding series_complete and series_dosed columns
echo.

REM Direct Docker commands to run the migration
echo Step 1: Starting PostgreSQL if not running...
docker-compose up -d postgres

echo.
echo Step 2: Waiting for database to be ready...
timeout /t 5 >nul

echo.
echo Step 3: Running migration SQL directly...
docker exec postgres psql -U healthcare_admin -d healthcare_db -c "ALTER TABLE immunizations ADD COLUMN IF NOT EXISTS series_complete BOOLEAN NOT NULL DEFAULT FALSE;"
docker exec postgres psql -U healthcare_admin -d healthcare_db -c "ALTER TABLE immunizations ADD COLUMN IF NOT EXISTS series_dosed INTEGER DEFAULT 1;"

echo.
echo Step 4: Verifying columns were added...
docker exec postgres psql -U healthcare_admin -d healthcare_db -c "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'immunizations' AND column_name IN ('series_complete', 'series_dosed');"

echo.
echo MIGRATION COMPLETE!
echo The enterprise healthcare deployment should now work.
echo.
pause