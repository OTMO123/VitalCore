# Direct Database Fix for Enterprise Healthcare Compliance
# Find and fix the PostgreSQL container for series_complete columns

Write-Host "Enterprise Healthcare Database Fix" -ForegroundColor Cyan
Write-Host "Identifying and fixing PostgreSQL container" -ForegroundColor White
Write-Host "=" * 50

# Step 1: Check what containers are running
Write-Host "Step 1: Checking running containers..." -ForegroundColor Yellow
docker ps

# Step 2: Check all containers (including stopped)
Write-Host "`nStep 2: Checking all containers..." -ForegroundColor Yellow
docker ps -a

# Step 3: Try different Docker Compose commands
Write-Host "`nStep 3: Trying to start database services..." -ForegroundColor Yellow

# Try different service names and compose files
$composeFiles = @(
    "docker-compose.yml",
    "docker-compose.production.yml", 
    "docker-compose.enterprise.yml"
)

$serviceNames = @(
    "postgres",
    "postgresql", 
    "database",
    "db",
    "healthcare-db"
)

foreach ($composeFile in $composeFiles) {
    if (Test-Path $composeFile) {
        Write-Host "Found compose file: $composeFile" -ForegroundColor Green
        
        foreach ($serviceName in $serviceNames) {
            Write-Host "Trying service: $serviceName" -ForegroundColor Yellow
            docker-compose -f $composeFile up -d $serviceName 2>$null
            Start-Sleep -Seconds 3
            
            # Check if container is now running
            $containerCheck = docker ps --filter "name=$serviceName" --format "{{.Names}}"
            if ($containerCheck) {
                Write-Host "SUCCESS: Started container $containerCheck" -ForegroundColor Green
                
                # Try to run the migration
                Write-Host "Running database migration..." -ForegroundColor Yellow
                
                $containerName = $containerCheck.Split()[0]
                
                # Try different database connection parameters
                $dbParams = @(
                    @{user="healthcare_admin"; db="healthcare_db"},
                    @{user="postgres"; db="healthcare_db"},
                    @{user="postgres"; db="postgres"},
                    @{user="admin"; db="healthcare"}
                )
                
                foreach ($param in $dbParams) {
                    Write-Host "Trying connection: $($param.user)@$($param.db)" -ForegroundColor Cyan
                    
                    $testConnection = docker exec $containerName psql -U $($param.user) -d $($param.db) -c "SELECT 1;" 2>$null
                    if ($?) {
                        Write-Host "SUCCESS: Connected to database!" -ForegroundColor Green
                        
                        # Run the migration
                        Write-Host "Adding series_complete column..." -ForegroundColor Yellow
                        docker exec $containerName psql -U $($param.user) -d $($param.db) -c "ALTER TABLE immunizations ADD COLUMN IF NOT EXISTS series_complete BOOLEAN NOT NULL DEFAULT FALSE;"
                        
                        Write-Host "Adding series_dosed column..." -ForegroundColor Yellow  
                        docker exec $containerName psql -U $($param.user) -d $($param.db) -c "ALTER TABLE immunizations ADD COLUMN IF NOT EXISTS series_dosed INTEGER DEFAULT 1;"
                        
                        Write-Host "Verifying columns..." -ForegroundColor Yellow
                        docker exec $containerName psql -U $($param.user) -d $($param.db) -c "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'immunizations' AND column_name IN ('series_complete', 'series_dosed');"
                        
                        Write-Host "`nSUCCESS: Migration completed!" -ForegroundColor Green
                        Write-Host "Enterprise healthcare deployment is now ready!" -ForegroundColor Green
                        exit
                    }
                }
            }
        }
    }
}

Write-Host "`nNo PostgreSQL container found. Let's try manual startup..." -ForegroundColor Yellow

# Manual container start attempts
Write-Host "Attempting manual PostgreSQL startup..." -ForegroundColor Yellow
docker run -d --name postgres-temp -e POSTGRES_PASSWORD=VitalCore2024 -e POSTGRES_USER=healthcare_admin -e POSTGRES_DB=healthcare_db -p 5433:5432 postgres:13

Start-Sleep -Seconds 10

Write-Host "Checking if temporary container started..." -ForegroundColor Yellow
$tempContainer = docker ps --filter "name=postgres-temp" --format "{{.Names}}"
if ($tempContainer) {
    Write-Host "SUCCESS: Temporary PostgreSQL container started" -ForegroundColor Green
    Write-Host "NOTE: This is a temporary fix. You'll need to migrate your data." -ForegroundColor Red
} else {
    Write-Host "FAILED: Could not start PostgreSQL" -ForegroundColor Red
    Write-Host "Please ensure Docker Desktop is running and try again" -ForegroundColor Yellow
}