# Rebuild Docker with Clinical Workflows
# PowerShell script to rebuild Docker containers with latest changes

Write-Host "🚀 Rebuilding Docker with Clinical Workflows Integration" -ForegroundColor Green
Write-Host "=" * 60

# Stop existing containers
Write-Host "📥 Stopping existing containers..." -ForegroundColor Yellow
docker-compose down

# Remove old images to force rebuild
Write-Host "🗑️ Removing old images..." -ForegroundColor Yellow
docker-compose down --rmi all

# Build new containers with latest code
Write-Host "🔨 Building new containers with clinical workflows..." -ForegroundColor Yellow
docker-compose build --no-cache

# Start the services
Write-Host "🚀 Starting services..." -ForegroundColor Yellow
docker-compose up -d

# Wait for services to be ready
Write-Host "⏳ Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Check container status
Write-Host "📊 Container Status:" -ForegroundColor Green
docker-compose ps

# Check if database is ready
Write-Host "🔍 Checking database connectivity..." -ForegroundColor Yellow
$dbReady = $false
$attempts = 0
$maxAttempts = 10

while (-not $dbReady -and $attempts -lt $maxAttempts) {
    try {
        $result = docker-compose exec -T db pg_isready -U postgres
        if ($LASTEXITCODE -eq 0) {
            $dbReady = $true
            Write-Host "✅ Database is ready!" -ForegroundColor Green
        } else {
            Write-Host "⏳ Database not ready yet... (attempt $($attempts + 1)/$maxAttempts)" -ForegroundColor Yellow
            Start-Sleep -Seconds 5
        }
    } catch {
        Write-Host "⏳ Waiting for database... (attempt $($attempts + 1)/$maxAttempts)" -ForegroundColor Yellow
        Start-Sleep -Seconds 5
    }
    $attempts++
}

if (-not $dbReady) {
    Write-Host "❌ Database failed to start after $maxAttempts attempts" -ForegroundColor Red
    exit 1
}

# Test application health
Write-Host "🏥 Testing application health..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Application is healthy!" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Application returned status: $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️ Application not yet responding (this is normal during startup)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎉 Docker rebuild complete!" -ForegroundColor Green
Write-Host "📚 API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "🏥 Clinical Workflows: http://localhost:8000/api/v1/clinical-workflows/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Run test suite: .\scripts\run_full_test_suite.ps1" -ForegroundColor Gray
Write-Host "  2. Test endpoints: .\scripts\test_clinical_workflows.ps1" -ForegroundColor Gray