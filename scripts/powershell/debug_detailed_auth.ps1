# Debug Detailed Authentication - Show Server Logs
Write-Host "=== DETAILED AUTH DEBUG ===" -ForegroundColor Yellow

# Clean up
$jobs = Get-Job | Where-Object { $_.State -eq "Running" }
if ($jobs) { $jobs | Stop-Job; $jobs | Remove-Job }

$processesOnPort = Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue
if ($processesOnPort) {
    foreach ($connection in $processesOnPort) {
        try { Stop-Process -Id $connection.OwningProcess -Force -ErrorAction SilentlyContinue } catch { }
    }
    Start-Sleep -Seconds 2
}

$env:PYTHONPATH = $PWD

Write-Host "Starting server with detailed logging..." -ForegroundColor Cyan
$job = Start-Job -ScriptBlock {
    param($WorkingDir)
    Set-Location $WorkingDir
    $env:PYTHONPATH = $WorkingDir
    $env:DATABASE_URL = "postgresql://postgres:password@localhost:5432/iris_db"
    $env:LOG_LEVEL = "DEBUG"
    
    python -c "
import sys
sys.path.insert(0, '.')
from app.main import app
import uvicorn
uvicorn.run(app, host='127.0.0.1', port=8001, log_level='info')
"
} -ArgumentList $PWD

Write-Host "Waiting for server..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# First test health endpoint
Write-Host "Testing health endpoint..." -ForegroundColor Cyan
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8001/health" -Method GET -TimeoutSec 5
    Write-Host "Health: $($health.status)" -ForegroundColor Green
} catch {
    Write-Host "Health check failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Now test authentication with detailed logging
Write-Host ""
Write-Host "Testing authentication..." -ForegroundColor Cyan
Write-Host "URL: http://localhost:8001/api/v1/auth/login" -ForegroundColor Gray
Write-Host "Payload: {username: 'admin', password: 'admin123'}" -ForegroundColor Gray

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8001/api/v1/auth/login" -Method POST -Body (@{username="admin";password="admin123"} | ConvertTo-Json) -ContentType "application/json" -TimeoutSec 10
    
    Write-Host ""
    Write-Host "SUCCESS!" -ForegroundColor Green
    Write-Host "User: $($response.user.username)" -ForegroundColor White
    
} catch {
    Write-Host ""
    Write-Host "FAILED with 401 - Let's see server logs:" -ForegroundColor Red
    Write-Host ""
    Write-Host "--- SERVER LOGS (Last 20 lines) ---" -ForegroundColor Yellow
    Receive-Job $job | Select-Object -Last 20
    
    Write-Host ""
    Write-Host "--- ANALYSIS ---" -ForegroundColor Magenta
    Write-Host "The server logs above should show us exactly where authentication fails" -ForegroundColor Cyan
    Write-Host "Look for:" -ForegroundColor Cyan
    Write-Host "1. AUTH_SERVICE - Starting user lookup by username" -ForegroundColor Gray
    Write-Host "2. AUTH_SERVICE - User found by username" -ForegroundColor Gray
    Write-Host "3. SECURITY_MANAGER - Password verification completed" -ForegroundColor Gray
    Write-Host "4. Any error messages in between" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Complete server output:" -ForegroundColor Yellow
Write-Host "--- FULL SERVER LOG ---" -ForegroundColor Cyan
Receive-Job $job

Write-Host ""
Write-Host "To stop: Stop-Job $($job.Id); Remove-Job $($job.Id)" -ForegroundColor Gray
Write-Host "=== DEBUG COMPLETE ===" -ForegroundColor Yellow