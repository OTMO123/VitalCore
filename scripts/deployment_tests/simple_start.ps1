# Simple FastAPI Startup - Most reliable method
# Uses uvicorn directly from project root

Write-Host "Simple FastAPI Startup" -ForegroundColor Green
Write-Host "======================" -ForegroundColor Green

# Go to project root
Write-Host "Navigating to project root..." -ForegroundColor Cyan
Push-Location "../../"

try {
    # Show current location
    $location = Get-Location
    Write-Host "Current directory: $location" -ForegroundColor Gray
    
    # Check if main app file exists
    if (!(Test-Path "app/main.py")) {
        Write-Host "ERROR: app/main.py not found in current directory" -ForegroundColor Red
        Write-Host "Contents of current directory:" -ForegroundColor Yellow
        Get-ChildItem | Select-Object Name | Format-Table -AutoSize
        exit 1
    }
    
    Write-Host "Found app/main.py - starting server..." -ForegroundColor Green
    
    # Load environment variables if .env exists
    if (Test-Path ".env") {
        Write-Host "Loading .env file..." -ForegroundColor Cyan
        $envLines = Get-Content ".env" | Where-Object { $_ -match "=" -and !$_.StartsWith("#") }
        Write-Host "Loaded $($envLines.Count) environment variables" -ForegroundColor Green
    }
    
    Write-Host "`nStarting FastAPI server..." -ForegroundColor Green
    Write-Host "Server will be available at: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "Press Ctrl+C to stop the server`n" -ForegroundColor Yellow
    
    # Start with uvicorn - most reliable method
    & python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    
}
catch {
    Write-Host "Error starting server: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "`nTrying alternative method..." -ForegroundColor Yellow
    
    # Fallback: try direct execution
    try {
        & python app/main.py
    }
    catch {
        Write-Host "Alternative method also failed: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "`nDebugging information:" -ForegroundColor Cyan
        Write-Host "Python version:" -ForegroundColor Gray
        & python --version
        Write-Host "`nPython path:" -ForegroundColor Gray
        & python -c "import sys; print('\n'.join(sys.path))"
        Write-Host "`nInstalled packages:" -ForegroundColor Gray
        & python -m pip list | findstr -i "fastapi uvicorn"
    }
}
finally {
    Pop-Location
    Write-Host "`nServer stopped. Run .\working_test.ps1 to test services." -ForegroundColor Cyan
}