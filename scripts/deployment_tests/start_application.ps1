# Start FastAPI Application - PowerShell Script
# Starts the Healthcare Records Backend application

Write-Host "Starting Healthcare Records Backend Application" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green

# Check if we're in the right directory
$currentPath = Get-Location
Write-Host "Current directory: $currentPath" -ForegroundColor Gray

# Look for the main application file
$appPaths = @(
    "../../app/main.py",
    "../../../app/main.py", 
    "app/main.py",
    "./app/main.py"
)

$appPath = $null
foreach ($path in $appPaths) {
    if (Test-Path $path) {
        $appPath = $path
        Write-Host "Found application at: $appPath" -ForegroundColor Green
        break
    }
}

if (!$appPath) {
    Write-Host "Could not find app/main.py" -ForegroundColor Red
    Write-Host "Please navigate to the project root directory" -ForegroundColor Yellow
    exit 1
}

# Check if Python is available
Write-Host "`nChecking Python availability..." -ForegroundColor Cyan
try {
    $pythonVersion = & python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Python is available: $pythonVersion" -ForegroundColor Green
    } else {
        # Try python3
        $pythonVersion = & python3 --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Python3 is available: $pythonVersion" -ForegroundColor Green
            $python = "python3"
        } else {
            Write-Host "Python is not available. Please install Python." -ForegroundColor Red
            exit 1
        }
    }
}
catch {
    Write-Host "Python check failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Set Python command
if (!$python) { $python = "python" }

# Check if required packages are installed
Write-Host "`nChecking required packages..." -ForegroundColor Cyan
$requiredPackages = @("fastapi", "uvicorn", "sqlalchemy", "psycopg2")
$missingPackages = @()

foreach ($package in $requiredPackages) {
    try {
        $result = & $python -c "import $package" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  $package - Available" -ForegroundColor Green
        } else {
            Write-Host "  $package - Missing" -ForegroundColor Red
            $missingPackages += $package
        }
    }
    catch {
        Write-Host "  $package - Missing" -ForegroundColor Red
        $missingPackages += $package
    }
}

if ($missingPackages.Count -gt 0) {
    Write-Host "`nMissing packages detected. Installing..." -ForegroundColor Yellow
    
    # Try to install missing packages
    try {
        Write-Host "Installing packages: $($missingPackages -join ', ')" -ForegroundColor Cyan
        foreach ($package in $missingPackages) {
            Write-Host "Installing $package..." -ForegroundColor Yellow
            & $python -m pip install $package 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  $package installed successfully" -ForegroundColor Green
            } else {
                Write-Host "  Failed to install $package" -ForegroundColor Red
            }
        }
    }
    catch {
        Write-Host "Package installation failed: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "Please install packages manually: pip install fastapi uvicorn sqlalchemy psycopg2-binary" -ForegroundColor Yellow
    }
}

# Check if we need to run database migrations
Write-Host "`nChecking database migrations..." -ForegroundColor Cyan
$alembicPath = "alembic"
if (Test-Path "../../alembic") {
    $alembicPath = "../../alembic"
} elseif (Test-Path "../alembic") {
    $alembicPath = "../alembic"
}

if (Test-Path "$alembicPath/alembic.ini") {
    Write-Host "Alembic found. Running database migrations..." -ForegroundColor Yellow
    
    try {
        # Change to the correct directory for alembic
        $originalLocation = Get-Location
        $alembicDir = Split-Path $alembicPath -Parent
        if ($alembicDir) {
            Set-Location $alembicDir
        }
        
        # Run migrations
        $migrationResult = & alembic upgrade head 2>&1
        
        # Return to original location
        Set-Location $originalLocation
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Database migrations completed successfully" -ForegroundColor Green
        } else {
            Write-Host "Database migration warning (this may be normal if no migrations are needed)" -ForegroundColor Yellow
            Write-Host "Migration output: $migrationResult" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "Migration check failed: $($_.Exception.Message)" -ForegroundColor Yellow
        Write-Host "Continuing with application startup..." -ForegroundColor Gray
    }
} else {
    Write-Host "No Alembic configuration found - skipping migrations" -ForegroundColor Yellow
}

# Set up environment variables
Write-Host "`nSetting up environment..." -ForegroundColor Cyan

# Load .env file if it exists
$envFiles = @("../../.env", "../.env", ".env")
foreach ($envFile in $envFiles) {
    if (Test-Path $envFile) {
        Write-Host "Loading environment from: $envFile" -ForegroundColor Green
        
        try {
            $envContent = Get-Content $envFile
            foreach ($line in $envContent) {
                if ($line -match '^([^#][^=]*?)=(.*)$') {
                    $name = $matches[1].Trim()
                    $value = $matches[2].Trim()
                    [Environment]::SetEnvironmentVariable($name, $value, "Process")
                    Write-Host "  Set $name" -ForegroundColor Gray
                }
            }
        }
        catch {
            Write-Host "Error loading .env file: $($_.Exception.Message)" -ForegroundColor Yellow
        }
        break
    }
}

# Start the FastAPI application
Write-Host "`nStarting FastAPI application..." -ForegroundColor Green
Write-Host "Application will start on: http://localhost:8000" -ForegroundColor Cyan
Write-Host "Health endpoint: http://localhost:8000/health" -ForegroundColor Cyan
Write-Host "API documentation: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "`nPress Ctrl+C to stop the application" -ForegroundColor Yellow
Write-Host "=" * 50 -ForegroundColor Gray

try {
    # Change to the app directory
    $appDir = Split-Path $appPath -Parent
    if ($appDir) {
        Push-Location $appDir
    }
    
    # Start the application
    if ($appPath -match "main\.py$") {
        # Direct Python execution
        & $python main.py
    } else {
        # Uvicorn execution  
        & $python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    }
}
catch {
    Write-Host "`nApplication startup failed: $($_.Exception.Message)" -ForegroundColor Red
}
finally {
    # Return to original location
    if ($appDir) {
        Pop-Location
    }
    
    Write-Host "`nApplication stopped." -ForegroundColor Yellow
    Write-Host "To test infrastructure again, run: .\working_test.ps1" -ForegroundColor Cyan
}