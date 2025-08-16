# Apply database schema fix for missing patient fields
# This script adds gender and active columns to the patients table

Write-Host "🔧 Applying database schema fix for Patient fields..." -ForegroundColor Cyan

# Check if Docker container is running
$containerStatus = docker ps --filter "name=iris_postgres" --format "{{.Status}}"
if (-not $containerStatus) {
    Write-Host "❌ PostgreSQL container 'iris_postgres' is not running!" -ForegroundColor Red
    Write-Host "Please start Docker services first: docker-compose up -d" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ PostgreSQL container is running" -ForegroundColor Green

# Apply the SQL changes
try {
    Write-Host "📝 Applying SQL schema changes..." -ForegroundColor Yellow
    
    # Execute the SQL file using docker exec
    docker exec iris_postgres psql -U postgres -d iris_db -f /tmp/add_patient_fields.sql
    
    # Copy SQL file to container first, then execute
    docker cp add_patient_fields.sql iris_postgres:/tmp/add_patient_fields.sql
    
    # Execute the SQL
    $result = docker exec iris_postgres psql -U postgres -d iris_db -f /tmp/add_patient_fields.sql
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Database schema updated successfully!" -ForegroundColor Green
        Write-Host "🔄 Restarting FastAPI container to reflect changes..." -ForegroundColor Yellow
        
        # Restart the app container
        docker restart iris_app
        
        Write-Host "✅ FastAPI container restarted" -ForegroundColor Green
        Write-Host "📊 You can now run the API tests again - Patient Creation should work!" -ForegroundColor Cyan
    }
    else {
        Write-Host "❌ Failed to apply database changes" -ForegroundColor Red
        Write-Host "SQL output: $result" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "❌ Error applying database changes: $_" -ForegroundColor Red
}

Write-Host "`n🚀 Schema fix complete! Ready for testing." -ForegroundColor Green