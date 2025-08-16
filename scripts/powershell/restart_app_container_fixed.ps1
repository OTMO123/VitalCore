#!/usr/bin/env pwsh

Write-Host "Restarting FastAPI application container..." -ForegroundColor Cyan

# Restart the application container to pick up code changes
docker restart iris_app

Write-Host "Waiting for container to be healthy..." -ForegroundColor Yellow

# Wait for the container to be healthy
$maxWait = 60
$waited = 0

do {
    Start-Sleep -Seconds 2
    $waited += 2
    
    $status = docker inspect iris_app --format='{{.State.Health.Status}}' 2>$null
    
    if ($status -eq "healthy") {
        Write-Host "Container is healthy!" -ForegroundColor Green
        break
    }
    
    if ($waited -ge $maxWait) {
        Write-Host "Container taking longer than expected to be healthy" -ForegroundColor Yellow
        break
    }
    
    Write-Host "." -NoNewline
    
} while ($waited -lt $maxWait)

Write-Host ""

# Test the health endpoint
Write-Host "Testing health endpoint..." -ForegroundColor Cyan

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 10 -UseBasicParsing
    $healthData = $response.Content | ConvertFrom-Json
    
    Write-Host "Health endpoint responding: $($healthData.status)" -ForegroundColor Green
    Write-Host "Database: $($healthData.database.status)" -ForegroundColor White
    Write-Host "Extensions: $($healthData.database.extensions -join ', ')" -ForegroundColor White
    
} catch {
    Write-Host "Health endpoint not accessible: $_" -ForegroundColor Red
}

Write-Host "Enterprise healthcare infrastructure status updated!" -ForegroundColor Cyan