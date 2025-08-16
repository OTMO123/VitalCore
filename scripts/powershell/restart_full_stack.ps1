# Restart full Docker stack
Write-Host "Restarting full Docker stack..." -ForegroundColor Yellow

# Stop all containers
Write-Host "Stopping all containers..." -ForegroundColor Cyan
docker-compose down

# Start database and Redis first
Write-Host "Starting database and Redis..." -ForegroundColor Cyan
docker-compose up -d db redis

# Wait for database to be ready
Write-Host "Waiting for database to be ready..." -ForegroundColor Yellow
Start-Sleep 15

# Check database status
Write-Host "Checking database status..." -ForegroundColor Cyan
docker ps --filter "name=iris_postgres"

# Start the application
Write-Host "Starting application..." -ForegroundColor Cyan
docker-compose up -d app

# Wait for application startup
Write-Host "Waiting for application startup..." -ForegroundColor Yellow
Start-Sleep 20

# Check application status
Write-Host "Checking application status..." -ForegroundColor Cyan
docker ps --filter "name=iris_app"

# Test health endpoint
Write-Host "Testing health endpoint..." -ForegroundColor Green
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 10
    Write-Host "SUCCESS: Health check passed - $($health.status)" -ForegroundColor Green
    
    # Quick test of our fixes
    Write-Host "Testing auth..." -ForegroundColor Yellow
    $loginBody = "username=admin&password=admin123"
    $loginHeaders = @{"Content-Type" = "application/x-www-form-urlencoded"}
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Headers $loginHeaders -Body $loginBody
    $token = $response.access_token
    
    $authHeaders = @{
        "Authorization" = "Bearer $token"
        "Content-Type" = "application/json"
    }
    
    # Test patient list
    $patients = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients" -Headers $authHeaders
    Write-Host "SUCCESS: Patient list works! Found $($patients.total) patients" -ForegroundColor Green
    
    Write-Host "Full stack is ready!" -ForegroundColor Green
    
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Checking application logs..." -ForegroundColor Yellow
    docker logs iris_app --tail 10
}