# Simple PowerShell script to add series columns to immunizations table
# Enterprise Healthcare Compliance Fix

Write-Host "Enterprise Healthcare Database Migration" -ForegroundColor Cyan
Write-Host "Adding series_complete and series_dosed columns" -ForegroundColor White
Write-Host "=" * 50

# Step 1: Start PostgreSQL
Write-Host "Step 1: Starting PostgreSQL container..." -ForegroundColor Yellow
docker-compose up -d postgres
Start-Sleep -Seconds 10

# Step 2: Add series_complete column
Write-Host "Step 2: Adding series_complete column..." -ForegroundColor Yellow
$cmd1 = "ALTER TABLE immunizations ADD COLUMN IF NOT EXISTS series_complete BOOLEAN NOT NULL DEFAULT FALSE;"
docker exec postgres psql -U healthcare_admin -d healthcare_db -c $cmd1

# Step 3: Add series_dosed column  
Write-Host "Step 3: Adding series_dosed column..." -ForegroundColor Yellow
$cmd2 = "ALTER TABLE immunizations ADD COLUMN IF NOT EXISTS series_dosed INTEGER DEFAULT 1;"
docker exec postgres psql -U healthcare_admin -d healthcare_db -c $cmd2

# Step 4: Verify columns
Write-Host "Step 4: Verifying columns were added..." -ForegroundColor Yellow
$verifyCmd = "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'immunizations' AND column_name IN ('series_complete', 'series_dosed');"
docker exec postgres psql -U healthcare_admin -d healthcare_db -c $verifyCmd

Write-Host ""
Write-Host "MIGRATION COMPLETE!" -ForegroundColor Green
Write-Host "Enterprise healthcare deployment is now ready!" -ForegroundColor Green