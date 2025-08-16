# Install Missing Dependencies - Production Fix
# Installs required packages for Healthcare Backend

Write-Host "Installing Healthcare Backend Dependencies" -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green

# Navigate to project root
Push-Location "../../"

try {
    Write-Host "Checking Python environment..." -ForegroundColor Cyan
    
    # Check if virtual environment is active
    $pythonPath = python -c "import sys; print(sys.executable)" 2>&1
    Write-Host "Python path: $pythonPath" -ForegroundColor Gray
    
    # Check if we're in a virtual environment
    $inVenv = python -c "import sys; print('True' if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) else 'False')" 2>&1
    Write-Host "Virtual environment active: $inVenv" -ForegroundColor Gray
    
    if ($inVenv -eq "False") {
        Write-Host "WARNING: Not in virtual environment. Activate with: .venv\Scripts\activate" -ForegroundColor Yellow
    }
    
    Write-Host "`nInstalling critical dependencies..." -ForegroundColor Cyan
    
    # Install most critical packages first
    $criticalPackages = @(
        "aiohttp==3.9.1",
        "fastapi==0.104.1", 
        "uvicorn[standard]==0.24.0",
        "pydantic==2.5.0",
        "sqlalchemy==2.0.23",
        "psycopg2-binary==2.9.9",
        "redis==5.0.1"
    )
    
    foreach ($package in $criticalPackages) {
        Write-Host "Installing $package..." -ForegroundColor Yellow
        try {
            & pip install $package
            if ($LASTEXITCODE -eq 0) {
                Write-Host "SUCCESS - $package installed" -ForegroundColor Green
            } else {
                Write-Host "ERROR - Failed to install $package" -ForegroundColor Red
            }
        }
        catch {
            Write-Host "ERROR - Exception installing $package - $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    Write-Host "`nInstalling all dependencies from requirements.txt..." -ForegroundColor Cyan
    
    # Install all requirements
    try {
        & pip install -r requirements.txt
        if ($LASTEXITCODE -eq 0) {
            Write-Host "SUCCESS - All requirements installed" -ForegroundColor Green
        } else {
            Write-Host "WARNING - Some packages may have failed" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "ERROR - Failed to install requirements.txt - $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Write-Host "`nVerifying key packages..." -ForegroundColor Cyan
    
    # Verify critical packages
    $packages = @("aiohttp", "fastapi", "uvicorn", "pydantic", "sqlalchemy", "psycopg2", "redis")
    $allInstalled = $true
    
    foreach ($pkg in $packages) {
        try {
            $version = python -c "import $pkg; print($pkg.__version__)" 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "SUCCESS - $pkg $version" -ForegroundColor Green
            } else {
                Write-Host "ERROR - $pkg not found" -ForegroundColor Red
                $allInstalled = $false
            }
        }
        catch {
            Write-Host "ERROR - $pkg check failed" -ForegroundColor Red
            $allInstalled = $false
        }
    }
    
    if ($allInstalled) {
        Write-Host "`nSUCCESS - All critical dependencies installed!" -ForegroundColor Green
        Write-Host "Next steps:" -ForegroundColor Cyan
        Write-Host "  1. Test import: python test_import.py" -ForegroundColor White
        Write-Host "  2. Start server: .\start_production_fixed.ps1" -ForegroundColor White
    } else {
        Write-Host "`nWARNING - Some dependencies missing. Check errors above." -ForegroundColor Yellow
    }
    
}
catch {
    Write-Host "ERROR - Dependency installation failed: $($_.Exception.Message)" -ForegroundColor Red
}
finally {
    Pop-Location
}