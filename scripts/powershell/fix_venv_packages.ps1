# Fix Virtual Environment Packages
# Install all required packages directly into the virtual environment

Write-Host "🔧 Installing packages into virtual environment..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# Use the venv Python directly
$venvPython = ".\.venv\Scripts\python.exe"

# Check if venv Python exists
if (Test-Path $venvPython) {
    Write-Host "✅ Found virtual environment Python at: $venvPython" -ForegroundColor Green
    
    # Upgrade pip first
    Write-Host "📦 Upgrading pip..." -ForegroundColor Yellow
    & $venvPython -m pip install --upgrade pip
    
    # Install all required packages
    Write-Host "📦 Installing required packages..." -ForegroundColor Yellow
    $packages = @(
        "pillow",
        "brotli", 
        "psutil",
        "PyJWT",
        "torch",
        "pymilvus",
        "marshmallow",
        "pyarrow"
    )
    
    foreach ($package in $packages) {
        Write-Host "Installing $package..." -ForegroundColor Cyan
        & $venvPython -m pip install $package
    }
    
    Write-Host "🎉 Package installation complete!" -ForegroundColor Green
    Write-Host "📊 Checking installed packages..." -ForegroundColor Yellow
    & $venvPython -m pip list | Select-String -Pattern "pillow|brotli|psutil|PyJWT|torch|pymilvus|marshmallow|pyarrow"
    
    Write-Host "✅ Ready to run tests with:" -ForegroundColor Green
    Write-Host "   .\run_tests_fixed.ps1" -ForegroundColor White
    
} else {
    Write-Host "❌ Virtual environment Python not found at: $venvPython" -ForegroundColor Red
    Write-Host "💡 Try running from the project root directory" -ForegroundColor Yellow
}