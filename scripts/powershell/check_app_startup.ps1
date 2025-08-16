# Check app startup status
Write-Host "Checking application startup status..." -ForegroundColor Yellow

# Check container status
Write-Host "Container status:" -ForegroundColor Cyan
docker ps --filter "name=iris_app"

# Check if app is healthy
Write-Host "`nContainer health:" -ForegroundColor Cyan
docker inspect iris_app --format='{{.State.Health.Status}}'

# Check recent logs for errors
Write-Host "`nRecent startup logs:" -ForegroundColor Cyan
docker logs iris_app --tail 20

# Wait a bit and test health endpoint
Write-Host "`nWaiting 10 seconds and testing health..." -ForegroundColor Yellow
Start-Sleep 10

try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 5
    Write-Host "Health check: SUCCESS - $($health.status)" -ForegroundColor Green
} catch {
    Write-Host "Health check failed: $($_.Exception.Message)" -ForegroundColor Red
    
    # Show more logs if health fails
    Write-Host "`nAdditional startup logs:" -ForegroundColor Red
    docker logs iris_app --tail 30
}