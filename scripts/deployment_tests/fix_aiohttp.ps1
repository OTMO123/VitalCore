# Quick Fix for Missing aiohttp Package
# Installs aiohttp and other critical packages

Write-Host "Quick Fix - Installing Missing Packages" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

try {
    Write-Host "Installing aiohttp..." -ForegroundColor Cyan
    & pip install aiohttp==3.9.1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "SUCCESS - aiohttp installed" -ForegroundColor Green
    } else {
        Write-Host "ERROR - Failed to install aiohttp" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "`nInstalling other critical HTTP packages..." -ForegroundColor Cyan
    & pip install httpx==0.25.2 requests
    
    Write-Host "`nVerifying aiohttp installation..." -ForegroundColor Cyan
    $version = python -c "import aiohttp; print(f'aiohttp {aiohttp.__version__} installed successfully')" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "SUCCESS - $version" -ForegroundColor Green
        
        Write-Host "`nTesting application import..." -ForegroundColor Cyan
        & python test_import.py
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "`nSUCCESS - Application is ready!" -ForegroundColor Green
            Write-Host "Start server with: .\start_production_fixed.ps1" -ForegroundColor Cyan
        } else {
            Write-Host "`nApplication still has import issues. Run full install:" -ForegroundColor Yellow
            Write-Host "  .\install_dependencies.ps1" -ForegroundColor White
        }
    } else {
        Write-Host "ERROR - aiohttp verification failed" -ForegroundColor Red
    }
    
}
catch {
    Write-Host "ERROR - Quick fix failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "`nTry full dependency installation:" -ForegroundColor Yellow
    Write-Host "  .\install_dependencies.ps1" -ForegroundColor White
}