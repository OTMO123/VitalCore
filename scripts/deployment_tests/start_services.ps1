# Start Services Script - Russian PowerShell Compatible
# Starts all required services for deployment testing

Write-Host "Starting Healthcare Backend Services" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green

$startTime = Get-Date
$servicesStarted = @()
$servicesFailed = @()

function Start-ServiceWithStatus {
    param([string]$ServiceName, [scriptblock]$StartCommand)
    
    Write-Host "`nStarting $ServiceName..." -ForegroundColor Yellow
    
    try {
        $result = & $StartCommand
        if ($LASTEXITCODE -eq 0 -or $result) {
            Write-Host "  $ServiceName - Started Successfully" -ForegroundColor Green
            $script:servicesStarted += $ServiceName
        } else {
            Write-Host "  $ServiceName - Failed to Start" -ForegroundColor Red
            $script:servicesFailed += $ServiceName
        }
    }
    catch {
        Write-Host "  $ServiceName - Error: $($_.Exception.Message)" -ForegroundColor Red
        $script:servicesFailed += $ServiceName
    }
}

# Check if Docker is available
Write-Host "`nChecking Docker availability..." -ForegroundColor Cyan
try {
    $dockerVersion = & docker --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Docker is available: $dockerVersion" -ForegroundColor Green
    } else {
        Write-Host "Docker is not available - cannot start containerized services" -ForegroundColor Red
        Write-Host "Please install Docker Desktop and try again" -ForegroundColor Yellow
        exit 1
    }
}
catch {
    Write-Host "Docker is not available - $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Start Docker services
Write-Host "`nStarting containerized services..." -ForegroundColor Cyan

Start-ServiceWithStatus "PostgreSQL Database" {
    # Check if docker-compose.yml exists
    if (Test-Path "docker-compose.yml") {
        & docker-compose up -d postgres 2>$null
        return ($LASTEXITCODE -eq 0)
    } elseif (Test-Path "../../docker-compose.yml") {
        Push-Location "../.."
        & docker-compose up -d postgres 2>$null
        $result = ($LASTEXITCODE -eq 0)
        Pop-Location
        return $result
    } else {
        Write-Host "    docker-compose.yml not found - trying generic postgres container" -ForegroundColor Yellow
        & docker run -d --name healthcare-postgres -e POSTGRES_DB=healthcare_db -e POSTGRES_USER=healthcare_user -e POSTGRES_PASSWORD=healthcare_pass -p 5432:5432 postgres:13 2>$null
        return ($LASTEXITCODE -eq 0)
    }
}

Start-ServiceWithStatus "Redis Cache" {
    if (Test-Path "docker-compose.yml") {
        & docker-compose up -d redis 2>$null
        return ($LASTEXITCODE -eq 0)
    } elseif (Test-Path "../../docker-compose.yml") {
        Push-Location "../.."
        & docker-compose up -d redis 2>$null
        $result = ($LASTEXITCODE -eq 0)
        Pop-Location
        return $result
    } else {
        Write-Host "    docker-compose.yml not found - trying generic redis container" -ForegroundColor Yellow
        & docker run -d --name healthcare-redis -p 6379:6379 redis:6-alpine 2>$null
        return ($LASTEXITCODE -eq 0)
    }
}

Start-ServiceWithStatus "MinIO Storage" {
    if (Test-Path "docker-compose.yml") {
        & docker-compose up -d minio 2>$null
        return ($LASTEXITCODE -eq 0)
    } elseif (Test-Path "../../docker-compose.yml") {
        Push-Location "../.."
        & docker-compose up -d minio 2>$null
        $result = ($LASTEXITCODE -eq 0)
        Pop-Location
        return $result
    } else {
        Write-Host "    MinIO not configured - skipping" -ForegroundColor Yellow
        return $true
    }
}

# Wait for services to be ready
Write-Host "`nWaiting for services to initialize..." -ForegroundColor Cyan
Start-Sleep -Seconds 10

# Test service connectivity
Write-Host "`nTesting service connectivity..." -ForegroundColor Cyan

function Test-ServiceReady {
    param([string]$ServiceName, [string]$TestHost, [int]$TestPort)
    
    try {
        $tcpClient = New-Object System.Net.Sockets.TcpClient
        $tcpClient.ReceiveTimeout = 3000
        $tcpClient.SendTimeout = 3000
        $tcpClient.Connect($TestHost, $TestPort)
        $tcpClient.Close()
        Write-Host "  $ServiceName - Ready" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "  $ServiceName - Not Ready" -ForegroundColor Red
        return $false
    }
}

$dbReady = Test-ServiceReady "PostgreSQL" "localhost" 5432
$redisReady = Test-ServiceReady "Redis" "localhost" 6379

# Show Docker container status
Write-Host "`nDocker container status:" -ForegroundColor Cyan
try {
    & docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | Where-Object { $_ -match "postgres|redis|minio|healthcare" }
}
catch {
    Write-Host "Could not retrieve Docker status" -ForegroundColor Yellow
}

# Set up basic environment variables if missing
Write-Host "`nChecking environment variables..." -ForegroundColor Cyan

$envVars = @{
    "DATABASE_URL" = "postgresql://healthcare_user:healthcare_pass@localhost:5432/healthcare_db"
    "DB_HOST" = "localhost"
    "DB_PORT" = "5432"
    "DB_NAME" = "healthcare_db"
    "DB_USER" = "healthcare_user"
    "DB_PASSWORD" = "healthcare_pass"
    "REDIS_URL" = "redis://localhost:6379"
    "REDIS_HOST" = "localhost"
    "REDIS_PORT" = "6379"
    "JWT_SECRET_KEY" = "your-jwt-secret-key-change-this-in-production-min-32-chars"
    "PHI_ENCRYPTION_KEY" = "your-phi-encryption-key-change-this-in-production-32-chars"
    "SECRET_KEY" = "your-app-secret-key-change-this-in-production"
    "ENVIRONMENT" = "development"
    "DEBUG" = "true"
    "HIPAA_ENABLED" = "true"
    "AUDIT_LOG_ENABLED" = "true"
    "PHI_AUDIT_ENABLED" = "true"
}

$envSet = 0
$envMissing = 0

foreach ($envVar in $envVars.Keys) {
    $currentValue = [Environment]::GetEnvironmentVariable($envVar)
    if ([string]::IsNullOrEmpty($currentValue)) {
        Write-Host "  Setting $envVar" -ForegroundColor Yellow
        [Environment]::SetEnvironmentVariable($envVar, $envVars[$envVar], "Process")
        $envMissing++
    } else {
        Write-Host "  $envVar - Already Set" -ForegroundColor Green
        $envSet++
    }
}

# Create .env file if it doesn't exist
$envFilePath = "../../.env"
if (!(Test-Path $envFilePath)) {
    Write-Host "`nCreating .env file..." -ForegroundColor Cyan
    
    $envContent = @"
# Healthcare Backend Environment Configuration
# Generated by start_services.ps1 on $(Get-Date)

# Database Configuration
DATABASE_URL=postgresql://healthcare_user:healthcare_pass@localhost:5432/healthcare_db
DB_HOST=localhost
DB_PORT=5432
DB_NAME=healthcare_db
DB_USER=healthcare_user
DB_PASSWORD=healthcare_pass

# Redis Configuration
REDIS_URL=redis://localhost:6379
REDIS_HOST=localhost
REDIS_PORT=6379

# Security Configuration (CHANGE THESE IN PRODUCTION!)
JWT_SECRET_KEY=your-jwt-secret-key-change-this-in-production-min-32-chars
PHI_ENCRYPTION_KEY=your-phi-encryption-key-change-this-in-production-32-chars
SECRET_KEY=your-app-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application Configuration
ENVIRONMENT=development
DEBUG=true
API_TITLE=Healthcare Records API
API_VERSION=v1.0.0

# HIPAA Compliance
HIPAA_ENABLED=true
AUDIT_LOG_ENABLED=true
PHI_AUDIT_ENABLED=true
AUDIT_LOG_RETENTION_DAYS=2555
CONSENT_VALIDATION_ENABLED=true
DATA_ENCRYPTION_AT_REST=true

# Security Headers
HTTPS_ONLY=false
SECURITY_HEADERS_ENABLED=true
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
RATE_LIMIT_ENABLED=true

# Monitoring
LOG_LEVEL=INFO
"@
    
    try {
        $envContent | Out-File -FilePath $envFilePath -Encoding UTF8
        Write-Host ".env file created at $envFilePath" -ForegroundColor Green
    }
    catch {
        Write-Host "Could not create .env file: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Summary
$endTime = Get-Date
$duration = [math]::Round(($endTime - $startTime).TotalSeconds, 1)

Write-Host "`nService Startup Summary" -ForegroundColor Green
Write-Host "======================" -ForegroundColor Green
Write-Host "Duration: $duration seconds" -ForegroundColor Gray

if ($servicesStarted.Count -gt 0) {
    Write-Host "`nServices Started Successfully:" -ForegroundColor Green
    foreach ($service in $servicesStarted) {
        Write-Host "  - $service" -ForegroundColor Green
    }
}

if ($servicesFailed.Count -gt 0) {
    Write-Host "`nServices That Failed:" -ForegroundColor Red
    foreach ($service in $servicesFailed) {
        Write-Host "  - $service" -ForegroundColor Red
    }
}

Write-Host "`nEnvironment Variables:" -ForegroundColor Cyan
Write-Host "  Set: $envSet" -ForegroundColor Green
Write-Host "  Missing/Created: $envMissing" -ForegroundColor Yellow

Write-Host "`nNext Steps:" -ForegroundColor Cyan
Write-Host "  1. Start the application: python app/main.py" -ForegroundColor White
Write-Host "  2. Run tests: .\working_test.ps1" -ForegroundColor White
Write-Host "  3. Check service status: docker ps" -ForegroundColor White

if ($dbReady -and $redisReady) {
    Write-Host "`nAll core services are ready! You can now start the application." -ForegroundColor Green
    exit 0
} else {
    Write-Host "`nSome services are not ready. Check Docker container logs." -ForegroundColor Yellow
    Write-Host "Use: docker logs container_name" -ForegroundColor Gray
    exit 1
}