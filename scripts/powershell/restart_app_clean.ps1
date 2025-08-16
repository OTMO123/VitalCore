# Clean restart of FastAPI application
Write-Host "Restarting FastAPI Application (Clean)" -ForegroundColor Green
Write-Host "======================================"

# Kill any existing Python processes
Write-Host "`nStopping existing Python processes..." -ForegroundColor Yellow
try {
    Get-Process python* | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    Write-Host "Python processes stopped" -ForegroundColor Green
} catch {
    Write-Host "No Python processes to stop" -ForegroundColor Yellow
}

# Clear any cached files
Write-Host "`nClearing Python cache..." -ForegroundColor Yellow
if (Test-Path "__pycache__") {
    Remove-Item -Recurse -Force "__pycache__"
}
Get-ChildItem -Recurse -Name "__pycache__" | ForEach-Object { 
    Remove-Item -Recurse -Force $_
}

# Start fresh application
Write-Host "`nStarting fresh FastAPI application..." -ForegroundColor Yellow
Start-Process -FilePath "python.exe" -ArgumentList "run_app_windows.py" -PassThru

Write-Host "`nWaiting for application startup..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Test the application
Write-Host "`nTesting application health..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/docs" -Method GET -TimeoutSec 10
    Write-Host "[SUCCESS] Application is responding" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Application not responding: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`nApplication restart complete!" -ForegroundColor Green