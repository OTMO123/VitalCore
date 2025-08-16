#!/usr/bin/env pwsh

Write-Host "🔍 Testing server connectivity..." -ForegroundColor Cyan

# Test if server is responding
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 10 -UseBasicParsing
    Write-Host "✅ Server is responding: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "Response: $($response.Content)" -ForegroundColor White
} catch {
    Write-Host "❌ Server not accessible: $_" -ForegroundColor Red
}

# Test database connectivity directly
Write-Host "`n🗄️ Testing database connectivity..." -ForegroundColor Cyan

try {
    $env:PGPASSWORD = "password"
    $result = psql -h localhost -p 5432 -U postgres -d iris_db -c "SELECT 1;"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Database is accessible" -ForegroundColor Green
    } else {
        Write-Host "❌ Database connection failed" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ psql not available or database not accessible" -ForegroundColor Red
}

# Check Docker containers
Write-Host "`n🐳 Docker container status:" -ForegroundColor Cyan
docker ps --filter "name=iris_"