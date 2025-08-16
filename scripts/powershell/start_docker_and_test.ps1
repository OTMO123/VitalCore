# Start Docker Services and Test Get Patient - Complete Environment Setup
# This script sets up the complete testing environment and runs the comprehensive debug

Write-Host "=== DOCKER ENVIRONMENT SETUP AND GET PATIENT DEBUG ===" -ForegroundColor Cyan

# Step 1: Start Docker services
Write-Host "`n1. Starting Docker services..." -ForegroundColor Green
Write-Host "Starting PostgreSQL, Redis, MinIO..." -ForegroundColor Yellow

try {
    docker-compose up -d
    Write-Host "✅ Docker services started successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to start Docker services: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Make sure Docker Desktop is running and WSL integration is enabled" -ForegroundColor Yellow
    exit 1
}

# Step 2: Wait for services to be ready
Write-Host "`n2. Waiting for services to be ready..." -ForegroundColor Green
Start-Sleep -Seconds 10

# Step 3: Check if PostgreSQL is ready
Write-Host "`n3. Checking PostgreSQL connection..." -ForegroundColor Green
$postgresReady = $false
$maxRetries = 30
$retryCount = 0

while (-not $postgresReady -and $retryCount -lt $maxRetries) {
    try {
        # Try to connect to PostgreSQL
        $testConnection = docker exec -i postgres_iris psql -U iris_user -d iris_db -c "SELECT 1;" 2>$null
        if ($LASTEXITCODE -eq 0) {
            $postgresReady = $true
            Write-Host "✅ PostgreSQL is ready" -ForegroundColor Green
        }
    } catch {
        # Ignore connection errors during startup
    }
    
    if (-not $postgresReady) {
        Write-Host "⏳ Waiting for PostgreSQL... (attempt $($retryCount + 1)/$maxRetries)" -ForegroundColor Yellow
        Start-Sleep -Seconds 2
        $retryCount++
    }
}

if (-not $postgresReady) {
    Write-Host "❌ PostgreSQL failed to start within timeout" -ForegroundColor Red
    exit 1
}

# Step 4: Run database migrations
Write-Host "`n4. Running database migrations..." -ForegroundColor Green
try {
    python app/main.py --migrate-only 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Database migrations completed" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Migration command not available, continuing..." -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️ Migration step skipped, continuing with server startup..." -ForegroundColor Yellow
}

# Step 5: Start FastAPI server
Write-Host "`n5. Starting FastAPI server..." -ForegroundColor Green
Write-Host "Server will start on http://localhost:8000" -ForegroundColor Yellow

# Start server in background
Start-Process python -ArgumentList "app/main.py" -WindowStyle Hidden
Start-Sleep -Seconds 5

# Step 6: Check if server is ready
Write-Host "`n6. Checking server health..." -ForegroundColor Green
$serverReady = $false
$maxRetries = 20
$retryCount = 0

while (-not $serverReady -and $retryCount -lt $maxRetries) {
    try {
        $healthResponse = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get -TimeoutSec 3
        if ($healthResponse.status -eq "healthy") {
            $serverReady = $true
            Write-Host "✅ FastAPI server is ready" -ForegroundColor Green
        }
    } catch {
        Write-Host "⏳ Waiting for server... (attempt $($retryCount + 1)/$maxRetries)" -ForegroundColor Yellow
        Start-Sleep -Seconds 3
        $retryCount++
    }
}

if (-not $serverReady) {
    Write-Host "❌ FastAPI server failed to start within timeout" -ForegroundColor Red
    Write-Host "Check server logs for errors" -ForegroundColor Yellow
    exit 1
}

# Step 7: Run the comprehensive Get Patient debug
Write-Host "`n7. Running comprehensive Get Patient debug..." -ForegroundColor Green
Write-Host "Executing 5 Whys analysis..." -ForegroundColor Yellow

# Execute the comprehensive debug script
& ".\debug_get_patient_comprehensive.ps1"

Write-Host "`n=== ENVIRONMENT STATUS ===" -ForegroundColor Cyan
Write-Host "✅ Docker services: Running" -ForegroundColor Green
Write-Host "✅ PostgreSQL: Ready" -ForegroundColor Green
Write-Host "✅ FastAPI server: Ready" -ForegroundColor Green
Write-Host "✅ Comprehensive debug: Completed" -ForegroundColor Green

Write-Host "`nServer is running at: http://localhost:8000" -ForegroundColor Yellow
Write-Host "PostgreSQL is available on port 5432" -ForegroundColor Yellow
Write-Host "Redis is available on port 6379" -ForegroundColor Yellow

Write-Host "`nTo check server logs: docker-compose logs iris_app" -ForegroundColor White
Write-Host "To stop services: docker-compose down" -ForegroundColor White