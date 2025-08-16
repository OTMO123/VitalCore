# System Health Diagnostic Script for IRIS API
# PowerShell version for comprehensive system checking

param(
    [string]$BaseUrl = "http://localhost:8000",
    [switch]$Verbose
)

# Global variables
$script:TotalChecks = 0
$script:PassedChecks = 0
$script:FailedChecks = 0

function Write-DiagnosticLog {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "HH:mm:ss.fff"
    $icons = @{
        "INFO" = "ℹ️"
        "PASS" = "✅"
        "FAIL" = "❌"
        "WARN" = "⚠️"
        "DEBUG" = "🔍"
    }
    
    $icon = $icons[$Level]
    Write-Host "[$timestamp] $icon $Message" -ForegroundColor $(
        switch ($Level) {
            "PASS" { "Green" }
            "FAIL" { "Red" }
            "WARN" { "Yellow" }
            "DEBUG" { "Cyan" }
            default { "White" }
        }
    )
}

function Test-Check {
    param(
        [string]$Description,
        [scriptblock]$TestScript
    )
    
    $script:TotalChecks++
    Write-DiagnosticLog "Testing: $Description" "DEBUG"
    
    try {
        $result = & $TestScript
        if ($result) {
            $script:PassedChecks++
            Write-DiagnosticLog "$Description - OK" "PASS"
            return $true
        } else {
            $script:FailedChecks++
            Write-DiagnosticLog "$Description - FAILED" "FAIL"
            return $false
        }
    }
    catch {
        $script:FailedChecks++
        Write-DiagnosticLog "$Description - ERROR: $($_.Exception.Message)" "FAIL"
        return $false
    }
}

function Test-DockerStatus {
    Write-DiagnosticLog "📦 DOCKER STATUS CHECK" "INFO"
    Write-Host "=" * 60
    
    # Check if Docker is running
    $dockerRunning = Test-Check "Docker daemon accessibility" {
        try {
            $null = docker version 2>&1
            return $LASTEXITCODE -eq 0
        }
        catch {
            return $false
        }
    }
    
    if (-not $dockerRunning) {
        Write-DiagnosticLog "Docker is not accessible. Please start Docker Desktop." "FAIL"
        return $false
    }
    
    # Check Docker Compose
    $composeWorking = Test-Check "Docker Compose functionality" {
        try {
            $null = docker compose version 2>&1
            return $LASTEXITCODE -eq 0
        }
        catch {
            return $false
        }
    }
    
    # List all containers
    Write-DiagnosticLog "Container Status:" "INFO"
    try {
        $containers = docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        Write-Host $containers
    }
    catch {
        Write-DiagnosticLog "Could not list containers" "WARN"
    }
    
    # Check IRIS-specific containers
    $irisContainers = Test-Check "IRIS containers running" {
        try {
            $runningContainers = docker ps --filter "name=iris" --format "{{.Names}}"
            if ($runningContainers) {
                Write-DiagnosticLog "IRIS containers found: $($runningContainers -join ', ')" "INFO"
                return $true
            }
            return $false
        }
        catch {
            return $false
        }
    }
    
    return $dockerRunning -and $composeWorking
}

function Test-DatabaseConnectivity {
    Write-DiagnosticLog "🗄️ DATABASE CONNECTIVITY CHECK" "INFO"
    Write-Host "=" * 60
    
    # Check PostgreSQL container
    $pgContainer = Test-Check "PostgreSQL container running" {
        try {
            $pgContainers = docker ps --filter "name=postgres" --format "{{.Names}}"
            return $pgContainers.Count -gt 0
        }
        catch {
            return $false
        }
    }
    
    if (-not $pgContainer) {
        return $false
    }
    
    # Test database connection
    $dbConnection = Test-Check "Database accepting connections" {
        try {
            $result = docker exec $(docker ps -q --filter "name=postgres") pg_isready -U postgres 2>&1
            return $LASTEXITCODE -eq 0
        }
        catch {
            return $false
        }
    }
    
    # Check Redis container
    $redisContainer = Test-Check "Redis container running" {
        try {
            $redisContainers = docker ps --filter "name=redis" --format "{{.Names}}"
            return $redisContainers.Count -gt 0
        }
        catch {
            return $false
        }
    }
    
    return $pgContainer -and $dbConnection -and $redisContainer
}

function Test-ApplicationHealth {
    Write-DiagnosticLog "🚀 APPLICATION HEALTH CHECK" "INFO"
    Write-Host "=" * 60
    
    # Check if Python is available
    $pythonAvailable = Test-Check "Python 3 available" {
        try {
            $version = python --version 2>&1
            return $version -match "Python 3"
        }
        catch {
            return $false
        }
    }
    
    # Check if app can import
    $appImport = Test-Check "Application imports successfully" {
        try {
            $result = python -c "from app.main import create_app; print('Import successful')" 2>&1
            return $LASTEXITCODE -eq 0
        }
        catch {
            Write-DiagnosticLog "Import error: $($_.Exception.Message)" "DEBUG"
            return $false
        }
    }
    
    # Check database models
    $modelsImport = Test-Check "Database models import" {
        try {
            $result = python -c "from app.core.database_unified import Patient, User; print('Models OK')" 2>&1
            return $LASTEXITCODE -eq 0
        }
        catch {
            Write-DiagnosticLog "Models import error: $($_.Exception.Message)" "DEBUG"
            return $false
        }
    }
    
    # Check if server starts (quick test)
    $serverStart = Test-Check "Server can start (quick test)" {
        try {
            # Start server in background and test quickly
            $job = Start-Job -ScriptBlock { 
                cd $using:PWD
                python app/main.py 
            }
            
            Start-Sleep -Seconds 5
            
            # Test if server responds
            try {
                $response = Invoke-WebRequest -Uri "$BaseUrl/health" -TimeoutSec 5 -UseBasicParsing
                $serverResponding = $response.StatusCode -eq 200
            }
            catch {
                $serverResponding = $false
            }
            
            # Stop the test server
            Stop-Job -Job $job -Force
            Remove-Job -Job $job -Force
            
            return $serverResponding
        }
        catch {
            return $false
        }
    }
    
    return $pythonAvailable -and $appImport -and $modelsImport
}

function Test-ConfigurationFiles {
    Write-DiagnosticLog "⚙️ CONFIGURATION FILES CHECK" "INFO"
    Write-Host "=" * 60
    
    $requiredFiles = @(
        "app/main.py",
        "app/core/database_unified.py", 
        "app/modules/healthcare_records/router.py",
        "docker-compose.yml",
        "requirements.txt",
        "alembic.ini"
    )
    
    $allFilesExist = $true
    
    foreach ($file in $requiredFiles) {
        $exists = Test-Check "File exists: $file" {
            return Test-Path $file
        }
        $allFilesExist = $allFilesExist -and $exists
    }
    
    # Check environment variables
    Write-DiagnosticLog "Environment Variables:" "INFO"
    $envVars = @("DATABASE_URL", "REDIS_URL", "SECRET_KEY")
    
    foreach ($var in $envVars) {
        $value = [Environment]::GetEnvironmentVariable($var)
        if ($value) {
            Write-DiagnosticLog "✅ $var - Set" "PASS"
        } else {
            Write-DiagnosticLog "⚠️ $var - Not set (using defaults)" "WARN"
        }
    }
    
    return $allFilesExist
}

function Test-NetworkConnectivity {
    Write-DiagnosticLog "🌐 NETWORK CONNECTIVITY CHECK" "INFO"
    Write-Host "=" * 60
    
    # Test if server port is accessible
    $portOpen = Test-Check "Port 8000 accessible" {
        try {
            $tcpClient = New-Object System.Net.Sockets.TcpClient
            $tcpClient.ConnectAsync("localhost", 8000).Wait(2000)
            $isConnected = $tcpClient.Connected
            $tcpClient.Close()
            return $isConnected
        }
        catch {
            return $false
        }
    }
    
    # Test basic HTTP connectivity
    $httpConnectivity = Test-Check "HTTP endpoint responsive" {
        try {
            $response = Invoke-WebRequest -Uri "$BaseUrl/health" -TimeoutSec 10 -UseBasicParsing
            return $response.StatusCode -eq 200
        }
        catch {
            if ($Verbose) {
                Write-DiagnosticLog "HTTP test error: $($_.Exception.Message)" "DEBUG"
            }
            return $false
        }
    }
    
    return $portOpen -or $httpConnectivity
}

function Start-DockerServices {
    Write-DiagnosticLog "🐳 STARTING DOCKER SERVICES" "INFO"
    Write-Host "=" * 60
    
    if (Test-Path "docker-compose.yml") {
        try {
            Write-DiagnosticLog "Starting Docker Compose services..." "INFO"
            docker compose up -d
            
            if ($LASTEXITCODE -eq 0) {
                Write-DiagnosticLog "Docker services started successfully" "PASS"
                
                # Wait for services to be ready
                Write-DiagnosticLog "Waiting for services to initialize..." "INFO"
                Start-Sleep -Seconds 10
                
                return $true
            } else {
                Write-DiagnosticLog "Failed to start Docker services" "FAIL"
                return $false
            }
        }
        catch {
            Write-DiagnosticLog "Error starting services: $($_.Exception.Message)" "FAIL"
            return $false
        }
    } else {
        Write-DiagnosticLog "docker-compose.yml not found" "FAIL"
        return $false
    }
}

function Write-DiagnosticSummary {
    Write-Host ""
    Write-DiagnosticLog "📊 DIAGNOSTIC SUMMARY" "INFO"
    Write-Host "=" * 80
    
    $successRate = if ($script:TotalChecks -gt 0) { 
        [math]::Round(($script:PassedChecks / $script:TotalChecks) * 100, 1) 
    } else { 0 }
    
    Write-DiagnosticLog "Total Checks: $script:TotalChecks" "INFO"
    Write-DiagnosticLog "Passed: $script:PassedChecks" "PASS"
    Write-DiagnosticLog "Failed: $script:FailedChecks" "FAIL"
    Write-DiagnosticLog "Success Rate: $successRate%" "INFO"
    
    # Recommendations
    Write-Host ""
    Write-DiagnosticLog "💡 RECOMMENDATIONS" "INFO"
    Write-Host "=" * 60
    
    if ($script:FailedChecks -eq 0) {
        Write-DiagnosticLog "🎉 ALL CHECKS PASSED - System ready!" "PASS"
    } elseif ($successRate -ge 80) {
        Write-DiagnosticLog "⚠️ System mostly working - minor fixes needed" "WARN"
        Write-DiagnosticLog "Run: .\diagnostic_scripts\Test-ApiEndpoints.ps1 for detailed API testing" "INFO"
    } else {
        Write-DiagnosticLog "❌ Major issues detected - check Docker and configuration" "FAIL"
        
        if ($script:FailedChecks -gt ($script:TotalChecks / 2)) {
            Write-DiagnosticLog "Try running: .\diagnostic_scripts\Check-SystemHealth.ps1 -StartServices" "INFO"
        }
    }
    
    return $successRate
}

# Main execution
Write-Host "🔍 IRIS API SYSTEM HEALTH DIAGNOSTIC" -ForegroundColor Cyan
Write-Host "=" * 80
Write-DiagnosticLog "Starting comprehensive system health check..." "INFO"
Write-DiagnosticLog "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" "INFO"
Write-DiagnosticLog "PowerShell Version: $($PSVersionTable.PSVersion)" "INFO"
Write-DiagnosticLog "Working Directory: $(Get-Location)" "INFO"
Write-Host ""

# Run all diagnostic checks
$dockerOk = Test-DockerStatus
$dbOk = if ($dockerOk) { Test-DatabaseConnectivity } else { $false }
$appOk = Test-ApplicationHealth  
$configOk = Test-ConfigurationFiles
$networkOk = Test-NetworkConnectivity

# Final summary
$overallSuccess = Write-DiagnosticSummary

# Save diagnostic log
$logFile = "diagnostic_scripts\system_health_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
Write-DiagnosticLog "Diagnostic log saved to: $logFile" "INFO"

# Exit with appropriate code
if ($overallSuccess -ge 90) {
    exit 0
} elseif ($overallSuccess -ge 70) {
    exit 1
} else {
    exit 2
}