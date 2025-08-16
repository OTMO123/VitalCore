#!/usr/bin/env pwsh

<#
.SYNOPSIS
    Enterprise Healthcare Infrastructure Test Runner
    
.DESCRIPTION
    Comprehensive test runner for IRIS API healthcare platform infrastructure.
    Handles Docker services, database setup, and validates enterprise readiness.
    
.PARAMETER TestOnly
    Skip infrastructure startup and run tests only
    
.PARAMETER WithDocker
    Start Docker services before testing
    
.PARAMETER Cleanup
    Stop and clean up Docker services after testing
    
.EXAMPLE
    .\run_infrastructure_tests.ps1 -WithDocker
    
.EXAMPLE  
    .\run_infrastructure_tests.ps1 -TestOnly
#>

param(
    [switch]$TestOnly,
    [switch]$WithDocker,
    [switch]$Cleanup
)

$ErrorActionPreference = "Continue"
$SuccessColor = "Green"
$WarningColor = "Yellow" 
$ErrorColor = "Red"
$InfoColor = "Cyan"

function Write-Status {
    param([string]$Message, [string]$Color = "White")
    Write-Host "🏥 " -ForegroundColor $InfoColor -NoNewline
    Write-Host $Message -ForegroundColor $Color
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ " -ForegroundColor $SuccessColor -NoNewline
    Write-Host $Message -ForegroundColor $SuccessColor
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  " -ForegroundColor $WarningColor -NoNewline
    Write-Host $Message -ForegroundColor $WarningColor
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "❌ " -ForegroundColor $ErrorColor -NoNewline
    Write-Host $Message -ForegroundColor $ErrorColor
}

Write-Status "IRIS Healthcare Infrastructure Test Runner" $InfoColor
Write-Status "==========================================" $InfoColor

# Check if Docker is available
$dockerAvailable = $false
try {
    docker --version | Out-Null
    $dockerAvailable = $true
    Write-Success "Docker is available"
} catch {
    Write-Warning "Docker not available - will test without container infrastructure"
}

# Check if virtual environment is activated
if (-not $env:VIRTUAL_ENV -and -not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Warning "Virtual environment not activated. Attempting to activate..."
    if (Test-Path ".venv\Scripts\Activate.ps1") {
        & .\.venv\Scripts\Activate.ps1
        Write-Success "Virtual environment activated"
    } else {
        Write-Error-Custom "Virtual environment not found. Run: python -m venv .venv"
        exit 1
    }
}

# Start Docker services if requested
if ($WithDocker -and $dockerAvailable) {
    Write-Status "Starting Docker infrastructure..." $InfoColor
    
    # Start test infrastructure 
    Write-Status "Starting test database and services..."
    docker-compose -f docker-compose.test.yml up -d test-postgres test-redis
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Test infrastructure started"
        
        # Wait for services to be healthy
        Write-Status "Waiting for services to be ready..."
        $maxWait = 60
        $waited = 0
        
        do {
            Start-Sleep -Seconds 2
            $waited += 2
            
            $postgresHealthy = docker inspect iris-test-postgres --format='{{.State.Health.Status}}' 2>$null
            $redisHealthy = docker inspect iris-test-redis --format='{{.State.Health.Status}}' 2>$null
            
            if ($postgresHealthy -eq "healthy" -and $redisHealthy -eq "healthy") {
                Write-Success "All services are healthy"
                break
            }
            
            if ($waited -ge $maxWait) {
                Write-Warning "Services taking longer than expected to start"
                break
            }
            
            Write-Host "." -NoNewline
        } while ($waited -lt $maxWait)
        
        Write-Host ""
        
    } else {
        Write-Warning "Failed to start Docker services - continuing with local tests"
    }
}

if (-not $TestOnly -and -not $WithDocker) {
    Write-Status "Checking local infrastructure availability..." $InfoColor
    
    # Check if local PostgreSQL is running
    try {
        $pgResult = Test-NetConnection -ComputerName localhost -Port 5432 -WarningAction SilentlyContinue
        if ($pgResult.TcpTestSucceeded) {
            Write-Success "PostgreSQL available on localhost:5432"
        } else {
            Write-Warning "PostgreSQL not available on localhost:5432"
        }
    } catch {
        Write-Warning "Could not check PostgreSQL connectivity"
    }
    
    # Check if test PostgreSQL is running
    try {
        $pgTestResult = Test-NetConnection -ComputerName localhost -Port 5433 -WarningAction SilentlyContinue
        if ($pgTestResult.TcpTestSucceeded) {
            Write-Success "Test PostgreSQL available on localhost:5433"
        }
    } catch {
        # Test DB not running is fine
    }
}

# Set environment variables for testing
$env:PYTEST_RUNNING = "true"
$env:TEST_ENV = "infrastructure"

Write-Status "Running enterprise infrastructure tests..." $InfoColor

# Run the infrastructure tests
$testCommand = ".venv\Scripts\python.exe -m pytest app/tests/infrastructure/ -v --tb=short --maxfail=5"

Write-Status "Executing: $testCommand" $InfoColor
Invoke-Expression $testCommand

$testExitCode = $LASTEXITCODE

# Display results
if ($testExitCode -eq 0) {
    Write-Success "🎉 All infrastructure tests passed!"
    Write-Success "Healthcare platform infrastructure is enterprise-ready"
} else {
    Write-Warning "Some infrastructure tests failed or were skipped"
    Write-Status "This may be expected if infrastructure is not fully started" $WarningColor
    
    if ($WithDocker -and $dockerAvailable) {
        Write-Status "To debug issues:" $InfoColor
        Write-Host "  • Check container logs: docker-compose -f docker-compose.test.yml logs"
        Write-Host "  • Check container status: docker-compose -f docker-compose.test.yml ps"
        Write-Host "  • Connect to test DB: docker exec -it iris-test-postgres psql -U test_user -d test_iris_db"
    } else {
        Write-Status "To enable full infrastructure testing:" $InfoColor
        Write-Host "  • Install Docker Desktop"
        Write-Host "  • Run: .\run_infrastructure_tests.ps1 -WithDocker"
        Write-Host "  • Or start local PostgreSQL on port 5432"
    }
}

# Cleanup if requested
if ($Cleanup -and $dockerAvailable) {
    Write-Status "Cleaning up Docker services..." $InfoColor
    docker-compose -f docker-compose.test.yml down
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Docker services cleaned up"
    } else {
        Write-Warning "Failed to clean up some Docker services"
    }
}

Write-Status "Infrastructure testing completed" $InfoColor
exit $testExitCode