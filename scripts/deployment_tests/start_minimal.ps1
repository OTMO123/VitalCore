# Start FastAPI Application - Minimal Configuration
# Uses only essential environment variables to avoid validation errors

Write-Host "Starting Healthcare Backend - Minimal Configuration" -ForegroundColor Green
Write-Host "===================================================" -ForegroundColor Green

# Navigate to project root
Push-Location "../../"

try {
    Write-Host "Setting minimal environment variables..." -ForegroundColor Cyan
    
    # Set only essential environment variables
    $env:DEBUG = "true"
    $env:ENVIRONMENT = "development"
    $env:SECRET_KEY = "your-secret-key-change-in-production"
    $env:ALGORITHM = "HS256"
    $env:ACCESS_TOKEN_EXPIRE_MINUTES = "30"
    $env:DATABASE_URL = "postgresql://healthcare_user:healthcare_pass@localhost:5432/healthcare_db"
    $env:REDIS_URL = "redis://localhost:6379"
    $env:ENCRYPTION_KEY = "your-encryption-key-32-chars-minimum"
    $env:ALLOWED_ORIGINS = "http://localhost:3000,http://localhost:8000"
    $env:RATE_LIMIT_REQUESTS_PER_MINUTE = "100"
    $env:RATE_LIMIT_BURST = "10"
    
    Write-Host "Essential environment variables set" -ForegroundColor Green
    
    Write-Host "`nStarting FastAPI server with minimal config..." -ForegroundColor Green
    Write-Host "Server will be available at: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "Health endpoint: http://localhost:8000/health" -ForegroundColor Cyan
    Write-Host "API docs: http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host "`nPress Ctrl+C to stop the server`n" -ForegroundColor Yellow
    
    # Start the server without reload (more stable)
    & python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
    
}
catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    
    Write-Host "`nTrying direct execution method..." -ForegroundColor Yellow
    try {
        # Set Python path
        $env:PYTHONPATH = (Get-Location).Path
        & python app/main.py
    }
    catch {
        Write-Host "Direct execution also failed: $($_.Exception.Message)" -ForegroundColor Red
        
        Write-Host "`nDebug information:" -ForegroundColor Cyan
        Write-Host "Current directory: $(Get-Location)" -ForegroundColor Gray
        Write-Host "Python version: $(python --version)" -ForegroundColor Gray
        Write-Host "Contents:" -ForegroundColor Gray
        Get-ChildItem -Name | Select-Object -First 10 | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
    }
}
finally {
    Pop-Location
    Write-Host "`nServer stopped. Test with: .\working_test.ps1" -ForegroundColor Cyan
}