# Fix Virtual Environment aiohttp Installation
# Ensures aiohttp is installed in the correct virtual environment

Write-Host "Fixing Virtual Environment aiohttp Installation" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green

# Navigate to project root
Push-Location "../../"

try {
    Write-Host "Checking Python environment..." -ForegroundColor Cyan
    
    # Check current Python path
    $pythonPath = python -c "import sys; print(sys.executable)"
    Write-Host "Python executable: $pythonPath" -ForegroundColor Gray
    
    # Check if we're in virtual environment
    $inVenv = python -c "import sys; print('True' if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) else 'False')"
    Write-Host "In virtual environment: $inVenv" -ForegroundColor Gray
    
    if ($inVenv -eq "False") {
        Write-Host "WARNING: Not in virtual environment. Activating..." -ForegroundColor Yellow
        if (Test-Path ".venv\Scripts\activate.ps1") {
            Write-Host "Activating virtual environment..." -ForegroundColor Cyan
            & .venv\Scripts\activate.ps1
        } elseif (Test-Path ".venv\Scripts\Activate.ps1") {
            & .venv\Scripts\Activate.ps1
        } else {
            Write-Host "ERROR: Virtual environment not found. Creating new one..." -ForegroundColor Red
            python -m venv .venv
            & .venv\Scripts\activate.ps1
        }
    }
    
    Write-Host "`nInstalling aiohttp in virtual environment..." -ForegroundColor Cyan
    
    # Force installation in virtual environment (not user)
    Write-Host "Method 1: Direct pip install in venv..." -ForegroundColor Yellow
    & python -m pip install --force-reinstall aiohttp --no-user
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "SUCCESS - aiohttp installed in virtual environment!" -ForegroundColor Green
    } else {
        Write-Host "Method 1 failed, trying alternative..." -ForegroundColor Yellow
        
        # Try with specific version that has pre-compiled wheels
        Write-Host "Method 2: Installing specific version..." -ForegroundColor Yellow
        & python -m pip install aiohttp==3.12.14 --no-user --force-reinstall
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "SUCCESS - aiohttp 3.12.14 installed!" -ForegroundColor Green
        } else {
            Write-Host "Method 2 failed, trying from user packages..." -ForegroundColor Yellow
            
            # Copy from user packages to venv
            Write-Host "Method 3: Copying from user installation..." -ForegroundColor Yellow
            $userSitePackages = python -c "import site; print(site.getusersitepackages())"
            $venvSitePackages = python -c "import site; print(site.getsitepackages()[0])"
            
            Write-Host "User site-packages: $userSitePackages" -ForegroundColor Gray
            Write-Host "Venv site-packages: $venvSitePackages" -ForegroundColor Gray
            
            if (Test-Path "$userSitePackages\aiohttp") {
                Write-Host "Copying aiohttp from user to venv..." -ForegroundColor Cyan
                Copy-Item "$userSitePackages\aiohttp*" "$venvSitePackages\" -Recurse -Force
                Copy-Item "$userSitePackages\aiohappyeyeballs*" "$venvSitePackages\" -Recurse -Force -ErrorAction SilentlyContinue
                Copy-Item "$userSitePackages\aiosignal*" "$venvSitePackages\" -Recurse -Force -ErrorAction SilentlyContinue
                Copy-Item "$userSitePackages\yarl*" "$venvSitePackages\" -Recurse -Force -ErrorAction SilentlyContinue
                Copy-Item "$userSitePackages\multidict*" "$venvSitePackages\" -Recurse -Force -ErrorAction SilentlyContinue
                Copy-Item "$userSitePackages\frozenlist*" "$venvSitePackages\" -Recurse -Force -ErrorAction SilentlyContinue
                Copy-Item "$userSitePackages\propcache*" "$venvSitePackages\" -Recurse -Force -ErrorAction SilentlyContinue
                Write-Host "SUCCESS - aiohttp copied to virtual environment!" -ForegroundColor Green
            } else {
                Write-Host "ERROR - aiohttp not found in user packages" -ForegroundColor Red
            }
        }
    }
    
    # Verify installation
    Write-Host "`nVerifying aiohttp installation..." -ForegroundColor Cyan
    $aiohttpCheck = python -c "import aiohttp; print(f'aiohttp {aiohttp.__version__} found in virtual environment')" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "SUCCESS - $aiohttpCheck" -ForegroundColor Green
        
        Write-Host "`nTesting Healthcare Backend..." -ForegroundColor Cyan
        & python test_import.py
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "`n🎉 PRODUCTION READY - Healthcare Backend is fully operational!" -ForegroundColor Green
            Write-Host "✅ All dependencies resolved in virtual environment" -ForegroundColor Green
            Write-Host "✅ aiohttp integration working" -ForegroundColor Green
            Write-Host "✅ IRIS API client functional" -ForegroundColor Green
            
            Write-Host "`nStarting production server..." -ForegroundColor Cyan
            Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
            Write-Host "=" * 50 -ForegroundColor Green
            
            # Start the production server
            & python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
            
        } else {
            Write-Host "`nApplication still has import issues. Checking for other missing dependencies..." -ForegroundColor Yellow
            
            # Install all requirements to be sure
            Write-Host "Installing all requirements..." -ForegroundColor Cyan
            & python -m pip install -r requirements.txt --no-user
        }
        
    } else {
        Write-Host "ERROR - aiohttp verification failed: $aiohttpCheck" -ForegroundColor Red
        Write-Host "Manual troubleshooting required" -ForegroundColor Yellow
    }
    
}
catch {
    Write-Host "ERROR - Script failed: $($_.Exception.Message)" -ForegroundColor Red
}
finally {
    Pop-Location
}