#!/usr/bin/env pwsh

<#
.SYNOPSIS
    Enterprise Healthcare Infrastructure Startup Script for Windows
    
.DESCRIPTION
    SOC2 Type II + HIPAA + FHIR R4 + GDPR compliant infrastructure startup
    Starts Docker services and FastAPI server for enterprise healthcare deployment
    
.PARAMETER StartDocker
    Start Docker services (PostgreSQL, Redis, MinIO)
    
.PARAMETER StartServer
    Start the FastAPI healthcare API server
    
.PARAMETER RunTests
    Run infrastructure tests after startup
    
.EXAMPLE
    .\start_enterprise_infrastructure_fixed.ps1 -StartDocker -StartServer
    
.EXAMPLE  
    .\start_enterprise_infrastructure_fixed.ps1 -StartDocker -StartServer -RunTests
#>

param(
    [switch]$StartDocker = $true,
    [switch]$StartServer = $true,
    [switch]$RunTests = $false
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

Write-Status "IRIS Healthcare Enterprise Infrastructure Startup" $InfoColor
Write-Status "=================================================" $InfoColor
Write-Status "SOC2 Type II + HIPAA + FHIR R4 + GDPR Compliant" $InfoColor
Write-Status "=================================================" $InfoColor

# Check if virtual environment is activated
if (-not $env:VIRTUAL_ENV -and -not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Warning "Virtual environment not detected. Attempting to activate..."
    if (Test-Path ".venv\Scripts\Activate.ps1") {
        & .\.venv\Scripts\Activate.ps1
        Write-Success "Virtual environment activated"
    } else {
        Write-Error-Custom "Virtual environment not found. Run: python -m venv .venv"
        exit 1
    }
}

# Check if Docker is available
$dockerAvailable = $false
try {
    docker --version | Out-Null
    $dockerAvailable = $true
    Write-Success "Docker is available"
} catch {
    Write-Warning "Docker not available - will run without containerized infrastructure"
}

if ($StartDocker -and $dockerAvailable) {
    Write-Status "Starting Docker infrastructure..." $InfoColor
    
    # Start core database and cache services
    Write-Status "Starting PostgreSQL database..."
    docker-compose up -d db
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "PostgreSQL started successfully"
    } else {
        Write-Warning "PostgreSQL failed to start - will continue with limited functionality"
    }
    
    Write-Status "Starting Redis cache..."
    docker-compose up -d redis
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Redis started successfully"
    } else {
        Write-Warning "Redis failed to start - will continue with limited functionality"
    }
    
    # Start MinIO for document storage
    Write-Status "Starting MinIO object storage..."
    docker-compose up -d minio
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "MinIO started successfully"
    } else {
        Write-Warning "MinIO failed to start - document storage may be limited"
    }
    
    # Wait for services to be healthy
    Write-Status "Waiting for services to be ready..."
    $maxWait = 60
    $waited = 0
    
    do {
        Start-Sleep -Seconds 2
        $waited += 2
        
        $dbHealthy = docker inspect iris_postgres --format='{{.State.Health.Status}}' 2>$null
        $redisHealthy = docker inspect iris_redis --format='{{.State.Health.Status}}' 2>$null
        
        if ($dbHealthy -eq "healthy" -and $redisHealthy -eq "healthy") {
            Write-Success "All core services are healthy"
            break
        }
        
        # Check if services are at least running (even without health checks)
        $dbRunning = docker ps --filter "name=iris_postgres" --filter "status=running" --quiet
        $redisRunning = docker ps --filter "name=iris_redis" --filter "status=running" --quiet
        
        if ($dbRunning -and $redisRunning) {
            Write-Success "Core services are running"
            break
        }
        
        if ($waited -ge $maxWait) {
            Write-Warning "Services taking longer than expected to start"
            break
        }
        
        Write-Host "." -NoNewline
    } while ($waited -lt $maxWait)
    
    Write-Host ""
    
    # Show service status
    Write-Status "Service Status:" $InfoColor
    docker-compose ps
}

if ($StartServer) {
    Write-Status "Starting Enterprise Healthcare API Server..." $InfoColor
    
    # Set environment variables for enterprise deployment
    $env:ENVIRONMENT = "development"
    $env:DEBUG = "true"
    $env:DATABASE_URL = "postgresql://postgres:password@localhost:5432/iris_db"
    $env:REDIS_URL = "redis://localhost:6379/0"
    
    # Check if database migration is needed
    Write-Status "Checking database migrations..."
    try {
        python -m alembic upgrade head
        Write-Success "Database migrations completed"
    } catch {
        Write-Warning "Database migration skipped - database may not be available"
    }
    
    # Start the FastAPI server
    Write-Status "Starting IRIS Healthcare API..."
    Write-Status "API Documentation: http://localhost:8000/docs" $InfoColor
    Write-Status "Health Check: http://localhost:8000/health" $InfoColor
    Write-Status "Enterprise Status: http://localhost:8000/health/detailed" $InfoColor
    
    try {
        # Start server in background for testing, or foreground for normal use
        if ($RunTests) {
            Write-Status "Starting server in background for testing..."
            $serverJob = Start-Job -ScriptBlock {
                Set-Location $using:PWD
                python run.py
            }
            Write-Success "Server started in background (Job ID: $($serverJob.Id))"
            
            # Wait a moment for server to start
            Start-Sleep -Seconds 5
        } else {
            Write-Status "Starting server in foreground..."
            python run.py
        }
    } catch {
        Write-Error-Custom "Failed to start FastAPI server: $_"
        exit 1
    }
}

if ($RunTests) {
    Write-Status "Running infrastructure tests..." $InfoColor
    
    # Wait for server to be fully ready
    Write-Status "Waiting for server to be ready..."
    $maxWait = 30
    $waited = 0
    $serverReady = $false
    
    do {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                Write-Success "Server is ready"
                $serverReady = $true
                break
            }
        } catch {
            # Server not ready yet
        }
        
        Start-Sleep -Seconds 1
        $waited += 1
        Write-Host "." -NoNewline
        
    } while ($waited -lt $maxWait)
    
    Write-Host ""
    
    if ($serverReady) {
        # Run infrastructure tests
        Write-Status "Running enterprise infrastructure tests..."
        python -m pytest app/tests/infrastructure/ -v --tb=short
        
        $testExitCode = $LASTEXITCODE
        
        if ($testExitCode -eq 0) {
            Write-Success "All infrastructure tests passed!"
            Write-Success "Enterprise healthcare platform is ready for deployment"
        } else {
            Write-Warning "Some infrastructure tests failed"
            Write-Status "Check test output above for details" $WarningColor
        }
    } else {
        Write-Warning "Server not ready for testing"
    }
    
    # Clean up background server job if created
    if ($serverJob) {
        Write-Status "Stopping background server job..."
        Stop-Job -Job $serverJob
        Remove-Job -Job $serverJob
    }
}

Write-Status "Enterprise healthcare infrastructure startup completed" $InfoColor

if (-not $RunTests -and $StartServer) {
    Write-Status "To run infrastructure tests:" $InfoColor
    Write-Host "   .\start_enterprise_infrastructure_fixed.ps1 -RunTests"
    Write-Status "To stop services:" $InfoColor
    Write-Host "   docker-compose down"
}