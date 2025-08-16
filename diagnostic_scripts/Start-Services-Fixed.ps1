# Start IRIS Services Script (Fixed for Windows)
# PowerShell script to start all required services and verify they're running

param(
    [switch]$Force,
    [switch]$CleanStart,
    [switch]$Verbose
)

function Write-ServiceLog {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "HH:mm:ss"
    $icons = @{
        "INFO" = "[INFO]"
        "SUCCESS" = "[PASS]"
        "ERROR" = "[FAIL]"
        "WARN" = "[WARN]"
        "DEBUG" = "[DEBUG]"
    }
    
    $icon = $icons[$Level]
    Write-Host "[$timestamp] $icon $Message" -ForegroundColor $(
        switch ($Level) {
            "SUCCESS" { "Green" }
            "ERROR" { "Red" }
            "WARN" { "Yellow" }
            "DEBUG" { "Cyan" }
            default { "White" }
        }
    )
}

function Test-DockerAvailable {
    Write-ServiceLog "Checking Docker availability..." "INFO"
    
    try {
        $dockerVersion = docker version --format '{{.Server.Version}}' 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-ServiceLog "Docker available (version: $dockerVersion)" "SUCCESS"
            return $true
        } else {
            Write-ServiceLog "Docker not responding" "ERROR"
            return $false
        }
    }
    catch {
        Write-ServiceLog "Docker not available: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Stop-ExistingServices {
    if ($CleanStart) {
        Write-ServiceLog "Stopping existing services (clean start requested)..." "INFO"
        
        try {
            docker compose down --remove-orphans
            if ($LASTEXITCODE -eq 0) {
                Write-ServiceLog "Services stopped successfully" "SUCCESS"
            }
        }
        catch {
            Write-ServiceLog "Warning: Could not stop services cleanly" "WARN"
        }
        
        # Wait a moment for cleanup
        Start-Sleep -Seconds 3
    }
}

function Start-DockerServices {
    Write-ServiceLog "Starting Docker services..." "INFO"
    
    if (-not (Test-Path "docker-compose.yml")) {
        Write-ServiceLog "docker-compose.yml not found!" "ERROR"
        return $false
    }
    
    try {
        # Start services in detached mode
        Write-ServiceLog "Running: docker compose up -d" "DEBUG"
        docker compose up -d
        
        if ($LASTEXITCODE -eq 0) {
            Write-ServiceLog "Docker Compose started successfully" "SUCCESS"
            return $true
        } else {
            Write-ServiceLog "Docker Compose failed to start" "ERROR"
            return $false
        }
    }
    catch {
        Write-ServiceLog "Error starting Docker services: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Wait-ForServices {
    Write-ServiceLog "Waiting for services to initialize..." "INFO"
    
    $maxWaitTime = 60  # seconds
    $checkInterval = 5 # seconds
    $elapsed = 0
    
    while ($elapsed -lt $maxWaitTime) {
        Write-ServiceLog "Checking service health... ($elapsed/$maxWaitTime seconds)" "DEBUG"
        
        # Check specific containers
        $requiredContainers = @("postgres", "redis", "minio")
        $healthyContainers = 0
        
        foreach ($container in $requiredContainers) {
            try {
                $containerStatus = docker ps --filter "name=$container" --format "{{.Status}}"
                if ($containerStatus -and $containerStatus -match "Up") {
                    $healthyContainers++
                    if ($Verbose) {
                        Write-ServiceLog "OK: $container is running" "DEBUG"
                    }
                } else {
                    if ($Verbose) {
                        Write-ServiceLog "WAIT: $container not ready yet" "DEBUG"
                    }
                }
            }
            catch {
                if ($Verbose) {
                    Write-ServiceLog "ERROR: Could not check $container status" "DEBUG"
                }
            }
        }
        
        if ($healthyContainers -eq $requiredContainers.Count) {
            Write-ServiceLog "All required containers are running!" "SUCCESS"
            return $true
        }
        
        Start-Sleep -Seconds $checkInterval
        $elapsed += $checkInterval
    }
    
    Write-ServiceLog "Timeout waiting for services to be ready" "WARN"
    return $false
}

function Test-DatabaseConnection {
    Write-ServiceLog "Testing database connection..." "INFO"
    
    try {
        $dbTest = docker exec $(docker ps -q --filter "name=postgres") pg_isready -U postgres
        if ($LASTEXITCODE -eq 0) {
            Write-ServiceLog "Database connection successful" "SUCCESS"
            return $true
        } else {
            Write-ServiceLog "Database not ready yet" "WARN"
            return $false
        }
    }
    catch {
        Write-ServiceLog "Could not test database connection" "WARN"
        return $false
    }
}

function Test-RedisConnection {
    Write-ServiceLog "Testing Redis connection..." "INFO"
    
    try {
        $redisTest = docker exec $(docker ps -q --filter "name=redis") redis-cli ping
        if ($redisTest -eq "PONG") {
            Write-ServiceLog "Redis connection successful" "SUCCESS"
            return $true
        } else {
            Write-ServiceLog "Redis not ready yet" "WARN"
            return $false
        }
    }
    catch {
        Write-ServiceLog "Could not test Redis connection" "WARN"
        return $false
    }
}

function Start-PythonApplication {
    Write-ServiceLog "Starting Python application..." "INFO"
    
    # Check if app can start
    try {
        Write-ServiceLog "Testing application startup..." "DEBUG"
        
        # Start app in background for testing
        $appJob = Start-Job -ScriptBlock {
            cd $using:PWD
            python app/main.py
        }
        
        # Wait a few seconds and test
        Start-Sleep -Seconds 8
        
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 10 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                Write-ServiceLog "Application started successfully!" "SUCCESS"
                Write-ServiceLog "API available at: http://localhost:8000" "INFO"
                
                # Keep the job running
                return $true
            }
        }
        catch {
            Write-ServiceLog "Application not responding yet" "WARN"
        }
        
        # Stop test job
        Stop-Job -Job $appJob -Force
        Remove-Job -Job $appJob -Force
        
        return $false
    }
    catch {
        Write-ServiceLog "Error testing application: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Show-ServiceStatus {
    Write-ServiceLog "SERVICE STATUS SUMMARY" "INFO"
    Write-Host "=" * 60
    
    # Show running containers
    try {
        $containers = docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        Write-Host $containers
    }
    catch {
        Write-ServiceLog "Could not list containers" "WARN"
    }
    
    Write-Host ""
    
    # Test key endpoints
    Write-ServiceLog "ENDPOINT TESTS:" "INFO"
    
    $endpoints = @(
        "http://localhost:8000/health",
        "http://localhost:5432",  # PostgreSQL
        "http://localhost:6379",  # Redis  
        "http://localhost:9000"   # MinIO
    )
    
    foreach ($endpoint in $endpoints) {
        try {
            if ($endpoint -match "localhost:8000") {
                $response = Invoke-WebRequest -Uri $endpoint -TimeoutSec 5 -UseBasicParsing
                if ($response.StatusCode -eq 200) {
                    Write-ServiceLog "OK: $endpoint - API Ready" "SUCCESS"
                } else {
                    Write-ServiceLog "WARN: $endpoint - Status: $($response.StatusCode)" "WARN"
                }
            } else {
                # For other ports, just test if they're listening
                $portNumber = ($endpoint -split ':')[-1]
                $tcpTest = Test-NetConnection -ComputerName localhost -Port $portNumber -WarningAction SilentlyContinue
                if ($tcpTest.TcpTestSucceeded) {
                    Write-ServiceLog "OK: Port $portNumber - Service Running" "SUCCESS"
                } else {
                    Write-ServiceLog "FAIL: Port $portNumber - Not Accessible" "ERROR"
                }
            }
        }
        catch {
            Write-ServiceLog "FAIL: $endpoint - Not Accessible" "ERROR"
        }
    }
}

function Write-StartupSummary {
    param([bool]$Success)
    
    Write-Host ""
    Write-ServiceLog "STARTUP SUMMARY" "INFO"
    Write-Host "=" * 60
    
    if ($Success) {
        Write-ServiceLog "ALL SERVICES STARTED SUCCESSFULLY!" "SUCCESS"
        Write-ServiceLog "" "INFO"
        Write-ServiceLog "Next Steps:" "INFO"
        Write-ServiceLog "  1. Run API tests: .\diagnostic_scripts\Test-ApiEndpoints-Fixed.ps1" "INFO"
        Write-ServiceLog "  2. Open browser: http://localhost:8000/docs" "INFO"
        Write-ServiceLog "  3. Check MinIO: http://localhost:9000" "INFO"
        Write-ServiceLog "" "INFO"
        Write-ServiceLog "System is ready for development and testing!" "SUCCESS"
    } else {
        Write-ServiceLog "SERVICE STARTUP INCOMPLETE" "ERROR"
        Write-ServiceLog "" "INFO"
        Write-ServiceLog "Troubleshooting:" "INFO"
        Write-ServiceLog "  1. Check Docker Desktop is running" "INFO"
        Write-ServiceLog "  2. Run: .\diagnostic_scripts\Check-SystemHealth-Fixed.ps1" "INFO"
        Write-ServiceLog "  3. Check logs: docker compose logs" "INFO"
        Write-ServiceLog "  4. Try clean restart: .\diagnostic_scripts\Start-Services-Fixed.ps1 -CleanStart" "INFO"
    }
}

# Main execution
Write-Host "IRIS API SERVICES STARTUP" -ForegroundColor Cyan
Write-Host "=" * 80
Write-ServiceLog "Starting all required services..." "INFO"
Write-ServiceLog "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" "INFO"

if ($CleanStart) {
    Write-ServiceLog "Clean start requested - will stop existing services first" "INFO"
}

if ($Force) {
    Write-ServiceLog "Force mode enabled - will ignore some errors" "INFO"
}

Write-Host ""

# Execute startup sequence
$dockerOk = Test-DockerAvailable
if (-not $dockerOk) {
    Write-ServiceLog "Docker not available - cannot continue" "ERROR"
    exit 1
}

Stop-ExistingServices

$servicesStarted = Start-DockerServices
if (-not $servicesStarted -and -not $Force) {
    Write-ServiceLog "Failed to start Docker services" "ERROR"
    exit 1
}

$servicesReady = Wait-ForServices
$dbOk = Test-DatabaseConnection
$redisOk = Test-RedisConnection

Write-Host ""
Show-ServiceStatus

# Try to start the Python application
$appOk = Start-PythonApplication

$overallSuccess = $servicesStarted -and $servicesReady -and $dbOk -and $redisOk -and $appOk

Write-StartupSummary -Success $overallSuccess

# Exit with appropriate code
if ($overallSuccess) {
    exit 0
} elseif ($servicesStarted -and $servicesReady) {
    # Infrastructure OK, app might need manual start
    exit 1  
} else {
    # Major issues
    exit 2
}