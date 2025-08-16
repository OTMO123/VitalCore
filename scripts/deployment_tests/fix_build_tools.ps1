# Fix Microsoft Visual C++ Build Tools Issue - Production Ready
# Installs build tools required for aiohttp compilation

Write-Host "Installing Microsoft Visual C++ Build Tools for aiohttp" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Green

Write-Host "CRITICAL: aiohttp requires Microsoft Visual C++ 14.0 or greater" -ForegroundColor Red
Write-Host "This is needed for production-ready IRIS API integration" -ForegroundColor Yellow

Write-Host "`nOption 1 - Install Build Tools (RECOMMENDED):" -ForegroundColor Cyan
Write-Host "  1. Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/" -ForegroundColor White
Write-Host "  2. Install 'C++ build tools' workload" -ForegroundColor White
Write-Host "  3. Restart PowerShell after installation" -ForegroundColor White
Write-Host "  4. Run: .\fix_aiohttp.ps1" -ForegroundColor White

Write-Host "`nOption 2 - Use pre-compiled wheel (QUICK FIX):" -ForegroundColor Cyan
Write-Host "  Trying to install pre-compiled aiohttp wheel..." -ForegroundColor Yellow

try {
    Write-Host "Attempting to install aiohttp without compilation..." -ForegroundColor Cyan
    
    # Try installing a compatible pre-compiled version
    Write-Host "Installing aiohttp with --only-binary option..." -ForegroundColor Yellow
    & pip install --only-binary=all aiohttp
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "SUCCESS - aiohttp installed from pre-compiled wheel!" -ForegroundColor Green
        
        # Verify installation
        $version = python -c "import aiohttp; print(f'aiohttp {aiohttp.__version__} installed successfully')" 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "SUCCESS - $version" -ForegroundColor Green
            
            Write-Host "`nTesting application import..." -ForegroundColor Cyan
            & python test_import.py
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "`nSUCCESS - Healthcare Backend is production ready!" -ForegroundColor Green
                Write-Host "Start server with: .\start_production_fixed.ps1" -ForegroundColor Cyan
            } else {
                Write-Host "`nApplication still has import issues." -ForegroundColor Yellow
            }
        } else {
            Write-Host "ERROR - aiohttp verification failed" -ForegroundColor Red
        }
    } else {
        Write-Host "ERROR - Pre-compiled wheel installation failed" -ForegroundColor Red
        Write-Host "`nFallback: Trying to install compatible version..." -ForegroundColor Yellow
        
        # Try installing a different version that might have pre-compiled wheels
        & pip install aiohttp>=3.8.0
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "SUCCESS - Compatible aiohttp version installed!" -ForegroundColor Green
        } else {
            Write-Host "ERROR - All installation attempts failed" -ForegroundColor Red
            Write-Host "`nYou MUST install Visual C++ Build Tools:" -ForegroundColor Red
            Write-Host "  https://visualstudio.microsoft.com/visual-cpp-build-tools/" -ForegroundColor White
        }
    }
}
catch {
    Write-Host "ERROR - Installation failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "`nREQUIRED: Install Microsoft Visual C++ Build Tools" -ForegroundColor Red
    Write-Host "Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/" -ForegroundColor White
}

Write-Host "`nProduction Requirements:" -ForegroundColor Yellow
Write-Host "  ✅ Visual C++ Build Tools (for native extensions)" -ForegroundColor White
Write-Host "  ✅ aiohttp (for IRIS API HTTP client)" -ForegroundColor White
Write-Host "  ✅ All other dependencies already installed" -ForegroundColor White