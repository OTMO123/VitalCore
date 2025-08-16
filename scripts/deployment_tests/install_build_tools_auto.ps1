# Automated Visual C++ Build Tools Installation - Production Ready
# Downloads and installs Microsoft Visual C++ Build Tools automatically

Write-Host "Automated Visual C++ Build Tools Installation" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")

if (-not $isAdmin) {
    Write-Host "ERROR: This script requires Administrator privileges" -ForegroundColor Red
    Write-Host "Right-click PowerShell and 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

Write-Host "Administrator privileges confirmed" -ForegroundColor Green

try {
    Write-Host "`nDownloading Visual Studio Build Tools..." -ForegroundColor Cyan
    
    # Download Visual Studio Build Tools installer
    $buildToolsUrl = "https://aka.ms/vs/17/release/vs_buildtools.exe"
    $installerPath = "$env:TEMP\vs_buildtools.exe"
    
    Write-Host "Downloading from: $buildToolsUrl" -ForegroundColor Gray
    Invoke-WebRequest -Uri $buildToolsUrl -OutFile $installerPath
    
    if (Test-Path $installerPath) {
        Write-Host "SUCCESS - Installer downloaded" -ForegroundColor Green
        
        Write-Host "`nInstalling C++ Build Tools..." -ForegroundColor Cyan
        Write-Host "This may take 5-10 minutes..." -ForegroundColor Yellow
        
        # Install with minimal C++ workload
        $installArgs = @(
            "--quiet",
            "--wait",
            "--add", "Microsoft.VisualStudio.Workload.VCTools",
            "--add", "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
            "--add", "Microsoft.VisualStudio.Component.Windows10SDK.20348"
        )
        
        $process = Start-Process -FilePath $installerPath -ArgumentList $installArgs -Wait -PassThru
        
        if ($process.ExitCode -eq 0) {
            Write-Host "SUCCESS - Visual C++ Build Tools installed!" -ForegroundColor Green
            
            Write-Host "`nInstalling aiohttp..." -ForegroundColor Cyan
            & pip install aiohttp==3.9.1
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "SUCCESS - aiohttp installed successfully!" -ForegroundColor Green
                
                # Test the installation
                $version = python -c "import aiohttp; print(f'aiohttp {aiohttp.__version__} ready for production')" 2>&1
                Write-Host "SUCCESS - $version" -ForegroundColor Green
                
                Write-Host "`nTesting Healthcare Backend..." -ForegroundColor Cyan
                & python test_import.py
                
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "`n🎉 PRODUCTION READY - Healthcare Backend is ready!" -ForegroundColor Green
                    Write-Host "Start server with: .\start_production_fixed.ps1" -ForegroundColor Cyan
                } else {
                    Write-Host "Application needs additional fixes" -ForegroundColor Yellow
                }
            } else {
                Write-Host "ERROR - aiohttp installation still failed" -ForegroundColor Red
            }
        } else {
            Write-Host "ERROR - Build Tools installation failed with exit code: $($process.ExitCode)" -ForegroundColor Red
        }
        
        # Cleanup
        Remove-Item $installerPath -Force -ErrorAction SilentlyContinue
        
    } else {
        Write-Host "ERROR - Failed to download installer" -ForegroundColor Red
    }
    
}
catch {
    Write-Host "ERROR - Installation failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "`nManual installation required:" -ForegroundColor Yellow
    Write-Host "  1. Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/" -ForegroundColor White
    Write-Host "  2. Install 'C++ build tools' workload" -ForegroundColor White
    Write-Host "  3. Restart PowerShell" -ForegroundColor White
    Write-Host "  4. Run: pip install aiohttp==3.9.1" -ForegroundColor White
}