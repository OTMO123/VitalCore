# Enterprise Healthcare API Server - Windows PowerShell Startup Script

param(
    [switch]$Production,
    [switch]$Check,
    [switch]$Help
)

# Show help information
if ($Help) {
    Write-Host "Enterprise Healthcare API Server - Windows Startup Script"
    Write-Host "Usage: .\start_server.ps1 [OPTIONS]"
    Write-Host "Options: -Production, -Check, -Help"
    exit 0
}

# Script banner
Write-Host "Enterprise Healthcare API Server" -ForegroundColor Cyan
Write-Host "SOC2 Type II + HIPAA + FHIR R4 Compliant" -ForegroundColor Green

# Set environment variables
$env:PYTHONPATH = $PSScriptRoot
$env:PYTHONDONTWRITEBYTECODE = "1"

# System check function
function Test-SystemReady {
    Write-Host "Performing system checks..." -ForegroundColor Yellow
    
    try {
        python -c "import fastapi, uvicorn" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Core dependencies installed" -ForegroundColor Green
            return $true
        } else {
            Write-Host "Missing dependencies - run: pip install -r requirements.txt" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "Python check failed: $_" -ForegroundColor Red
        return $false
    }
}

# Main execution
try {
    if ($Check) {
        if (Test-SystemReady) {
            Write-Host "System ready!" -ForegroundColor Green
            exit 0
        } else {
            exit 1
        }
    }
    
    if (-not (Test-SystemReady)) {
        Write-Host "System checks failed" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "Starting server..." -ForegroundColor Green
    python run.py $(if ($Production) { "--production" })
}
catch {
    Write-Host "Startup failed: $_" -ForegroundColor Red
    exit 1
}