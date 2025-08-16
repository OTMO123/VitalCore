# Start FastAPI Application - Fixed Python Path
# Properly handles Python module imports

Write-Host "Starting Healthcare Records Backend Application (Fixed)" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Green

# Navigate to the project root directory
$projectRoot = "../../"
if (!(Test-Path "$projectRoot/app/main.py")) {
    Write-Host "Cannot find app/main.py. Please run this script from the scripts/deployment_tests directory." -ForegroundColor Red
    exit 1
}

Write-Host "Changing to project root directory..." -ForegroundColor Cyan
Push-Location $projectRoot

try {
    # Check Python availability
    Write-Host "`nChecking Python..." -ForegroundColor Cyan
    $pythonVersion = & python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Python not found. Please install Python." -ForegroundColor Red
        exit 1
    }
    Write-Host "Python version: $pythonVersion" -ForegroundColor Green

    # Load environment variables from .env file
    Write-Host "`nLoading environment variables..." -ForegroundColor Cyan
    if (Test-Path ".env") {
        $envContent = Get-Content ".env"
        foreach ($line in $envContent) {
            if ($line -match '^([^#][^=]*?)=(.*)$') {
                $name = $matches[1].Trim()
                $value = $matches[2].Trim()
                [Environment]::SetEnvironmentVariable($name, $value, "Process")
            }
        }
        Write-Host "Environment variables loaded from .env" -ForegroundColor Green
    } else {
        Write-Host "No .env file found - using system environment" -ForegroundColor Yellow
    }

    # Add current directory to Python path
    Write-Host "`nSetting up Python path..." -ForegroundColor Cyan
    $currentDir = (Get-Location).Path
    $env:PYTHONPATH = "$currentDir;$env:PYTHONPATH"
    Write-Host "PYTHONPATH set to include: $currentDir" -ForegroundColor Green

    # Check if we can import the app module
    Write-Host "`nTesting app module import..." -ForegroundColor Cyan
    $importTest = & python -c "import app.main; print('Import successful')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "App module import successful" -ForegroundColor Green
    } else {
        Write-Host "App module import failed: $importTest" -ForegroundColor Red
        Write-Host "Trying alternative import method..." -ForegroundColor Yellow
        
        # Try with -m flag
        $importTest2 = & python -m app.main --help 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Module import works with -m flag" -ForegroundColor Green
        } else {
            Write-Host "Module import still failing. Trying direct execution..." -ForegroundColor Yellow
        }
    }

    # Try multiple startup methods
    Write-Host "`nStarting FastAPI application..." -ForegroundColor Green
    Write-Host "Application will be available at:" -ForegroundColor Cyan
    Write-Host "  - Main: http://localhost:8000" -ForegroundColor White
    Write-Host "  - Health: http://localhost:8000/health" -ForegroundColor White
    Write-Host "  - Docs: http://localhost:8000/docs" -ForegroundColor White
    Write-Host "  - Healthcare API: http://localhost:8000/api/v1/healthcare-records/health" -ForegroundColor White
    Write-Host "`nPress Ctrl+C to stop the server" -ForegroundColor Yellow
    Write-Host "=" * 60 -ForegroundColor Gray
    
    # Method 1: Try uvicorn with module path
    Write-Host "`nAttempt 1: Starting with uvicorn (recommended)..." -ForegroundColor Cyan
    try {
        $uvicornResult = & python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload 2>&1
        Write-Host $uvicornResult
    }
    catch {
        Write-Host "Uvicorn method failed: $($_.Exception.Message)" -ForegroundColor Red
        
        # Method 2: Try direct python execution
        Write-Host "`nAttempt 2: Starting with direct Python execution..." -ForegroundColor Cyan
        try {
            & python app/main.py
        }
        catch {
            Write-Host "Direct execution failed: $($_.Exception.Message)" -ForegroundColor Red
            
            # Method 3: Try with python -m
            Write-Host "`nAttempt 3: Starting with python -m..." -ForegroundColor Cyan
            try {
                & python -m app.main
            }
            catch {
                Write-Host "Module execution failed: $($_.Exception.Message)" -ForegroundColor Red
                
                # Method 4: Try changing to app directory
                Write-Host "`nAttempt 4: Starting from app directory..." -ForegroundColor Cyan
                Push-Location "app"
                try {
                    & python main.py
                }
                catch {
                    Write-Host "App directory execution failed: $($_.Exception.Message)" -ForegroundColor Red
                }
                finally {
                    Pop-Location
                }
            }
        }
    }
}
catch {
    Write-Host "Critical error: $($_.Exception.Message)" -ForegroundColor Red
}
finally {
    # Return to original directory
    Pop-Location
    Write-Host "`nApplication stopped." -ForegroundColor Yellow
    Write-Host "To test services, run: .\working_test.ps1" -ForegroundColor Cyan
}