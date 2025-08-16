# Check app status and logs
Write-Host "Checking application status..." -ForegroundColor Yellow

# Check if app is running
Write-Host "Docker container status:" -ForegroundColor Cyan
docker ps --filter "name=iris_app"

# Check recent logs
Write-Host "`nRecent application logs:" -ForegroundColor Cyan  
docker logs iris_app --tail 15

# Test health endpoint
Write-Host "`nTesting health endpoint:" -ForegroundColor Cyan
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health"
    Write-Host "Health check: $($health.status)" -ForegroundColor Green
} catch {
    Write-Host "Health check failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test openapi docs
Write-Host "`nTesting OpenAPI docs:" -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/docs" -UseBasicParsing
    Write-Host "OpenAPI docs: HTTP $($response.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "OpenAPI docs failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`nApp status check completed" -ForegroundColor Green