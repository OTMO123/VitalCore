# Fix Infrastructure Tests - Set Required Environment Variables
# This script sets up the environment for infrastructure tests to pass

Write-Host "🔧 Setting up environment variables for infrastructure tests..." -ForegroundColor Cyan

# Get current directory
$currentDir = Get-Location
Write-Host "Current directory: $currentDir" -ForegroundColor Green

# Set PYTHONPATH environment variable for current session
$env:PYTHONPATH = $currentDir
Write-Host "PYTHONPATH set to: $env:PYTHONPATH" -ForegroundColor Green

# Set PYTHONPATH permanently for the user
[Environment]::SetEnvironmentVariable("PYTHONPATH", $currentDir, "User")
Write-Host "PYTHONPATH set permanently for user" -ForegroundColor Green

# Verify the environment variable is set
Write-Host "Verifying environment setup..." -ForegroundColor Yellow
Write-Host "PYTHONPATH: $env:PYTHONPATH" -ForegroundColor White

# Run the infrastructure tests
Write-Host "🧪 Running infrastructure tests..." -ForegroundColor Cyan
python -m pytest app/tests/infrastructure/test_system_health.py -v

Write-Host "✅ Infrastructure test setup complete!" -ForegroundColor Green