# Install Missing ML Dependencies for Production
# Installs numpy and other ML packages required for healthcare backend

Write-Host "Installing ML Dependencies for Healthcare Backend" -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Green

try {
    Write-Host "Installing numpy..." -ForegroundColor Cyan
    & python -m pip install numpy --no-user
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "SUCCESS - numpy installed" -ForegroundColor Green
    } else {
        Write-Host "ERROR - Failed to install numpy" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "`nInstalling other ML dependencies..." -ForegroundColor Cyan
    $mlPackages = @("pandas", "scikit-learn", "transformers", "torch")
    
    foreach ($package in $mlPackages) {
        Write-Host "Installing $package..." -ForegroundColor Yellow
        & python -m pip install $package --no-user
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "SUCCESS - $package installed" -ForegroundColor Green
        } else {
            Write-Host "WARNING - Failed to install $package (optional)" -ForegroundColor Yellow
        }
    }
    
    Write-Host "`nVerifying numpy installation..." -ForegroundColor Cyan
    $version = python -c "import numpy; print(f'numpy {numpy.__version__} installed successfully')" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "SUCCESS - $version" -ForegroundColor Green
        
        Write-Host "`nStarting Healthcare Backend..." -ForegroundColor Cyan
        Write-Host "=" * 50 -ForegroundColor Green
        
        # Start the production server
        & python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
        
    } else {
        Write-Host "ERROR - numpy verification failed" -ForegroundColor Red
    }
    
}
catch {
    Write-Host "ERROR - Installation failed: $($_.Exception.Message)" -ForegroundColor Red
}