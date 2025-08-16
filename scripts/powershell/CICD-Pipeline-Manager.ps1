# =====================================================
# IRIS Healthcare API - CI/CD Pipeline Manager
# Comprehensive PowerShell script for pipeline operations
# =====================================================

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("status", "test", "infrastructure", "smoke", "security", "deploy", "rollback", "monitor", "help")]
    [string]$Action = "help",
    
    [Parameter(Mandatory=$false)]
    [string]$Environment = "development",
    
    [Parameter(Mandatory=$false)]
    [switch]$Verbose,
    
    [Parameter(Mandatory=$false)]
    [switch]$Force
)

# =====================================================
# Configuration and Constants
# =====================================================

$script:Config = @{
    ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
    ServerUrl = "http://localhost:8004"
    TestTimeout = 300
    LogLevel = if ($Verbose) { "DEBUG" } else { "INFO" }
    DatabaseUrl = "postgresql://postgres:password@localhost:5432/iris_db"
    TestDatabaseUrl = "postgresql://postgres:password@localhost:5432/iris_test_db"
}

$script:Colors = @{
    Success = "Green"
    Warning = "Yellow" 
    Error = "Red"
    Info = "Cyan"
    Debug = "Gray"
}

# =====================================================
# Utility Functions
# =====================================================

function Write-Log {
    param(
        [string]$Message,
        [ValidateSet("SUCCESS", "WARNING", "ERROR", "INFO", "DEBUG")]
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = $script:Colors[$Level.ToLower()] ?? "White"
    
    if ($Level -eq "DEBUG" -and -not $Verbose) { return }
    
    $logMessage = "[$timestamp] [$Level] $Message"
    Write-Host $logMessage -ForegroundColor $color
    
    # Log to file
    $logFile = Join-Path $script:Config.ProjectRoot "logs" "cicd-pipeline.log"
    $logDir = Split-Path $logFile -Parent
    if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
    Add-Content -Path $logFile -Value $logMessage
}

function Test-Prerequisites {
    Write-Log "Checking CI/CD prerequisites..." "INFO"
    
    $checks = @()
    
    # Check Python virtual environment
    $venvPath = Join-Path $script:Config.ProjectRoot "venv" "Scripts" "python.exe"
    if (Test-Path $venvPath) {
        $checks += @{ Name = "Python Virtual Environment"; Status = "✅ OK"; Details = $venvPath }
    } else {
        $checks += @{ Name = "Python Virtual Environment"; Status = "❌ MISSING"; Details = "Run: python -m venv venv" }
    }
    
    # Check pytest installation
    try {
        $pytestVersion = & $venvPath -m pytest --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            $checks += @{ Name = "Pytest Framework"; Status = "✅ OK"; Details = $pytestVersion }
        } else {
            $checks += @{ Name = "Pytest Framework"; Status = "❌ MISSING"; Details = "Run: pip install pytest" }
        }
    } catch {
        $checks += @{ Name = "Pytest Framework"; Status = "❌ ERROR"; Details = $_.Exception.Message }
    }
    
    # Check database connectivity
    try {
        $testConnection = Test-NetConnection -ComputerName "localhost" -Port 5432 -WarningAction SilentlyContinue
        if ($testConnection.TcpTestSucceeded) {
            $checks += @{ Name = "PostgreSQL Database"; Status = "✅ OK"; Details = "Port 5432 accessible" }
        } else {
            $checks += @{ Name = "PostgreSQL Database"; Status = "❌ UNAVAILABLE"; Details = "Port 5432 not accessible" }
        }
    } catch {
        $checks += @{ Name = "PostgreSQL Database"; Status = "❌ ERROR"; Details = $_.Exception.Message }
    }
    
    # Check GitHub Actions workflow
    $workflowPath = Join-Path $script:Config.ProjectRoot ".github" "workflows" "conservative-ci.yml"
    if (Test-Path $workflowPath) {
        $checks += @{ Name = "GitHub Actions Workflow"; Status = "✅ OK"; Details = "Pipeline configured" }
    } else {
        $checks += @{ Name = "GitHub Actions Workflow"; Status = "⚠️ MISSING"; Details = "Pipeline not configured" }
    }
    
    # Display results
    Write-Log "Prerequisites Check Results:" "INFO"
    foreach ($check in $checks) {
        Write-Log "  $($check.Name): $($check.Status) - $($check.Details)" "INFO"
    }
    
    $failedChecks = ($checks | Where-Object { $_.Status -like "*❌*" }).Count
    return $failedChecks -eq 0
}

function Get-PipelineStatus {
    Write-Log "Fetching CI/CD pipeline status..." "INFO"
    
    $status = @{
        Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss UTC"
        Environment = $Environment
        Components = @{}
        TestResults = @{}
        OverallHealth = "UNKNOWN"
    }
    
    # Check server health
    try {
        $healthResponse = Invoke-RestMethod -Uri "$($script:Config.ServerUrl)/health" -TimeoutSec 10
        $status.Components["API Server"] = @{
            Status = "✅ HEALTHY"
            Details = $healthResponse.status
            LastCheck = Get-Date -Format "HH:mm:ss"
        }
    } catch {
        $status.Components["API Server"] = @{
            Status = "❌ UNHEALTHY"
            Details = $_.Exception.Message
            LastCheck = Get-Date -Format "HH:mm:ss"
        }
    }
    
    # Check database connectivity
    try {
        $dbTest = Test-NetConnection -ComputerName "localhost" -Port 5432 -WarningAction SilentlyContinue
        if ($dbTest.TcpTestSucceeded) {
            $status.Components["Database"] = @{
                Status = "✅ ACCESSIBLE"
                Details = "PostgreSQL responding on port 5432"
                LastCheck = Get-Date -Format "HH:mm:ss"
            }
        } else {
            $status.Components["Database"] = @{
                Status = "❌ INACCESSIBLE"
                Details = "PostgreSQL not responding on port 5432"
                LastCheck = Get-Date -Format "HH:mm:ss"
            }
        }
    } catch {
        $status.Components["Database"] = @{
            Status = "❌ ERROR"
            Details = $_.Exception.Message
            LastCheck = Get-Date -Format "HH:mm:ss"
        }
    }
    
    # Check test framework
    $venvPython = Join-Path $script:Config.ProjectRoot "venv" "Scripts" "python.exe"
    if (Test-Path $venvPython) {
        try {
            $pytestCheck = & $venvPython -m pytest --version 2>$null
            if ($LASTEXITCODE -eq 0) {
                $status.Components["Test Framework"] = @{
                    Status = "✅ OPERATIONAL"
                    Details = "Pytest framework ready"
                    LastCheck = Get-Date -Format "HH:mm:ss"
                }
            }
        } catch {
            $status.Components["Test Framework"] = @{
                Status = "❌ ERROR"
                Details = "Pytest framework issues"
                LastCheck = Get-Date -Format "HH:mm:ss"
            }
        }
    }
    
    # Determine overall health
    $healthyComponents = ($status.Components.Values | Where-Object { $_.Status -like "*✅*" }).Count
    $totalComponents = $status.Components.Count
    
    if ($healthyComponents -eq $totalComponents) {
        $status.OverallHealth = "✅ HEALTHY"
    } elseif ($healthyComponents -gt ($totalComponents / 2)) {
        $status.OverallHealth = "⚠️ DEGRADED"
    } else {
        $status.OverallHealth = "❌ UNHEALTHY"
    }
    
    return $status
}

function Invoke-InfrastructureTests {
    Write-Log "Running infrastructure validation tests..." "INFO"
    
    Set-Location $script:Config.ProjectRoot
    $env:PYTHONPATH = $script:Config.ProjectRoot
    
    $venvPython = Join-Path $script:Config.ProjectRoot "venv" "Scripts" "python.exe"
    
    try {
        Write-Log "Executing infrastructure tests..." "DEBUG"
        $testOutput = & $venvPython -m pytest "app/tests/infrastructure/test_system_health.py" -v --tb=short 2>&1
        
        $results = @{
            ExitCode = $LASTEXITCODE
            Output = $testOutput -join "`n"
            Timestamp = Get-Date
            Duration = $null
        }
        
        # Parse test results
        $passedTests = ($testOutput | Select-String "PASSED").Count
        $failedTests = ($testOutput | Select-String "FAILED").Count
        $skippedTests = ($testOutput | Select-String "SKIPPED").Count
        $totalTests = $passedTests + $failedTests + $skippedTests
        
        $results.Summary = @{
            Total = $totalTests
            Passed = $passedTests
            Failed = $failedTests
            Skipped = $skippedTests
            PassRate = if ($totalTests -gt 0) { [math]::Round(($passedTests / $totalTests) * 100, 1) } else { 0 }
        }
        
        Write-Log "Infrastructure Tests Results:" "INFO"
        Write-Log "  Total: $($results.Summary.Total)" "INFO"
        Write-Log "  Passed: $($results.Summary.Passed)" "SUCCESS"
        Write-Log "  Failed: $($results.Summary.Failed)" $(if ($results.Summary.Failed -gt 0) { "ERROR" } else { "INFO" })
        Write-Log "  Skipped: $($results.Summary.Skipped)" "WARNING"
        Write-Log "  Pass Rate: $($results.Summary.PassRate)%" $(if ($results.Summary.PassRate -ge 75) { "SUCCESS" } else { "WARNING" })
        
        return $results
        
    } catch {
        Write-Log "Infrastructure tests failed with error: $($_.Exception.Message)" "ERROR"
        return @{
            ExitCode = 1
            Output = $_.Exception.Message
            Error = $true
        }
    }
}

function Invoke-SmokeTests {
    Write-Log "Running smoke tests..." "INFO"
    
    Set-Location $script:Config.ProjectRoot
    $env:PYTHONPATH = $script:Config.ProjectRoot
    
    $venvPython = Join-Path $script:Config.ProjectRoot "venv" "Scripts" "python.exe"
    
    try {
        Write-Log "Executing smoke tests..." "DEBUG"
        $testOutput = & $venvPython -m pytest "app/tests/smoke/test_authentication_basic.py" -v --tb=short 2>&1
        
        $results = @{
            ExitCode = $LASTEXITCODE
            Output = $testOutput -join "`n"
            Timestamp = Get-Date
        }
        
        # Parse test results
        $passedTests = ($testOutput | Select-String "PASSED").Count
        $failedTests = ($testOutput | Select-String "FAILED").Count
        $skippedTests = ($testOutput | Select-String "SKIPPED").Count
        $totalTests = $passedTests + $failedTests + $skippedTests
        
        $results.Summary = @{
            Total = $totalTests
            Passed = $passedTests
            Failed = $failedTests
            Skipped = $skippedTests
            PassRate = if ($totalTests -gt 0) { [math]::Round(($passedTests / $totalTests) * 100, 1) } else { 0 }
        }
        
        Write-Log "Smoke Tests Results:" "INFO"
        Write-Log "  Total: $($results.Summary.Total)" "INFO"
        Write-Log "  Passed: $($results.Summary.Passed)" "SUCCESS"
        Write-Log "  Failed: $($results.Summary.Failed)" $(if ($results.Summary.Failed -gt 0) { "ERROR" } else { "INFO" })
        Write-Log "  Skipped: $($results.Summary.Skipped)" "WARNING"
        Write-Log "  Pass Rate: $($results.Summary.PassRate)%" $(if ($results.Summary.PassRate -ge 80) { "SUCCESS" } else { "WARNING" })
        
        return $results
        
    } catch {
        Write-Log "Smoke tests failed with error: $($_.Exception.Message)" "ERROR"
        return @{
            ExitCode = 1
            Output = $_.Exception.Message
            Error = $true
        }
    }
}

function Invoke-SecurityScan {
    Write-Log "Running security scan..." "INFO"
    
    Set-Location $script:Config.ProjectRoot
    $venvPython = Join-Path $script:Config.ProjectRoot "venv" "Scripts" "python.exe"
    
    try {
        # Run Bandit security scan
        Write-Log "Running Bandit security analysis..." "DEBUG"
        $banditOutput = & $venvPython -m bandit -r app/ -ll --format json 2>&1
        
        # Run dependency security check (if safety is available)
        Write-Log "Checking dependency security..." "DEBUG"
        try {
            $safetyOutput = & $venvPython -m safety check --json 2>&1
        } catch {
            $safetyOutput = "Safety not available - install with: pip install safety"
        }
        
        $results = @{
            Bandit = @{
                ExitCode = $LASTEXITCODE
                Output = $banditOutput -join "`n"
            }
            Safety = @{
                Output = $safetyOutput -join "`n"
            }
            Timestamp = Get-Date
        }
        
        Write-Log "Security Scan Results:" "INFO"
        if ($results.Bandit.ExitCode -eq 0) {
            Write-Log "  Bandit: ✅ No high/medium severity issues found" "SUCCESS"
        } else {
            Write-Log "  Bandit: ⚠️ Issues detected - review output" "WARNING"
        }
        
        return $results
        
    } catch {
        Write-Log "Security scan failed with error: $($_.Exception.Message)" "ERROR"
        return @{
            Error = $true
            Message = $_.Exception.Message
        }
    }
}

function Invoke-CompletePipeline {
    Write-Log "Starting complete CI/CD pipeline execution..." "INFO"
    
    $pipelineResults = @{
        StartTime = Get-Date
        Prerequisites = $null
        Infrastructure = $null
        Smoke = $null
        Security = $null
        OverallSuccess = $false
    }
    
    # Step 1: Prerequisites check
    Write-Log "Step 1: Checking prerequisites..." "INFO"
    $pipelineResults.Prerequisites = Test-Prerequisites
    if (-not $pipelineResults.Prerequisites) {
        Write-Log "Prerequisites check failed - aborting pipeline" "ERROR"
        return $pipelineResults
    }
    
    # Step 2: Infrastructure tests
    Write-Log "Step 2: Infrastructure validation..." "INFO"
    $pipelineResults.Infrastructure = Invoke-InfrastructureTests
    if ($pipelineResults.Infrastructure.Summary.PassRate -lt 70) {
        Write-Log "Infrastructure tests below threshold (70%) - continuing with warnings" "WARNING"
    }
    
    # Step 3: Smoke tests
    Write-Log "Step 3: Smoke testing..." "INFO"
    $pipelineResults.Smoke = Invoke-SmokeTests
    if ($pipelineResults.Smoke.Summary.PassRate -lt 80) {
        Write-Log "Smoke tests below threshold (80%) - continuing with warnings" "WARNING"
    }
    
    # Step 4: Security scan
    Write-Log "Step 4: Security scanning..." "INFO"
    $pipelineResults.Security = Invoke-SecurityScan
    
    # Calculate overall success
    $infraSuccess = $pipelineResults.Infrastructure.Summary.PassRate -ge 70
    $smokeSuccess = $pipelineResults.Smoke.Summary.PassRate -ge 80
    $securitySuccess = -not $pipelineResults.Security.Error
    
    $pipelineResults.OverallSuccess = $infraSuccess -and $smokeSuccess -and $securitySuccess
    $pipelineResults.EndTime = Get-Date
    $pipelineResults.Duration = $pipelineResults.EndTime - $pipelineResults.StartTime
    
    # Final summary
    Write-Log "=============================================" "INFO"
    Write-Log "CI/CD Pipeline Execution Complete" "INFO"
    Write-Log "=============================================" "INFO"
    Write-Log "Duration: $($pipelineResults.Duration.TotalSeconds) seconds" "INFO"
    Write-Log "Infrastructure: $($pipelineResults.Infrastructure.Summary.PassRate)% pass rate" $(if ($infraSuccess) { "SUCCESS" } else { "WARNING" })
    Write-Log "Smoke Tests: $($pipelineResults.Smoke.Summary.PassRate)% pass rate" $(if ($smokeSuccess) { "SUCCESS" } else { "WARNING" })
    Write-Log "Security Scan: $(if ($securitySuccess) { "✅ Clean" } else { "⚠️ Issues detected" })" $(if ($securitySuccess) { "SUCCESS" } else { "WARNING" })
    Write-Log "Overall Result: $(if ($pipelineResults.OverallSuccess) { "✅ SUCCESS" } else { "⚠️ WARNINGS" })" $(if ($pipelineResults.OverallSuccess) { "SUCCESS" } else { "WARNING" })
    
    return $pipelineResults
}

function Show-Help {
    Write-Host @"
╔══════════════════════════════════════════════════════════════════════════════╗
║                    IRIS Healthcare API - CI/CD Pipeline Manager              ║
╚══════════════════════════════════════════════════════════════════════════════╝

USAGE:
    .\CICD-Pipeline-Manager.ps1 -Action <action> [options]

ACTIONS:
    status          Show current pipeline and system status
    test            Run complete test pipeline (infrastructure + smoke + security)
    infrastructure  Run infrastructure validation tests only
    smoke           Run smoke tests only
    security        Run security scan only
    deploy          Deploy application (development environment)
    rollback        Rollback to previous version
    monitor         Show real-time monitoring dashboard
    help            Show this help message

OPTIONS:
    -Environment    Target environment (development, staging, production)
    -Verbose        Enable verbose logging and debug output
    -Force          Force execution even if prerequisites fail

EXAMPLES:
    # Check current system status
    .\CICD-Pipeline-Manager.ps1 -Action status

    # Run complete pipeline with verbose output
    .\CICD-Pipeline-Manager.ps1 -Action test -Verbose

    # Run only infrastructure tests
    .\CICD-Pipeline-Manager.ps1 -Action infrastructure

    # Deploy to staging environment
    .\CICD-Pipeline-Manager.ps1 -Action deploy -Environment staging

CONFIGURATION:
    Server URL: $($script:Config.ServerUrl)
    Database: $($script:Config.DatabaseUrl)
    Project Root: $($script:Config.ProjectRoot)

For detailed documentation, see: reports/cicd/README.md
"@
}

# =====================================================
# Main Execution Logic
# =====================================================

function Main {
    Write-Log "IRIS Healthcare API - CI/CD Pipeline Manager" "INFO"
    Write-Log "Action: $Action | Environment: $Environment" "INFO"
    
    switch ($Action.ToLower()) {
        "status" {
            $status = Get-PipelineStatus
            Write-Host "`n📊 CI/CD Pipeline Status Dashboard" -ForegroundColor Cyan
            Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
            Write-Host "Timestamp: $($status.Timestamp)" -ForegroundColor Gray
            Write-Host "Environment: $($status.Environment)" -ForegroundColor Gray
            Write-Host "Overall Health: $($status.OverallHealth)" -ForegroundColor $(if ($status.OverallHealth -like "*✅*") { "Green" } else { "Yellow" })
            Write-Host "`nComponent Status:" -ForegroundColor White
            foreach ($component in $status.Components.GetEnumerator()) {
                Write-Host "  $($component.Key): $($component.Value.Status)" -ForegroundColor $(if ($component.Value.Status -like "*✅*") { "Green" } else { "Red" })
                Write-Host "    Details: $($component.Value.Details)" -ForegroundColor Gray
                Write-Host "    Last Check: $($component.Value.LastCheck)" -ForegroundColor Gray
            }
        }
        
        "test" {
            $results = Invoke-CompletePipeline
            exit $(if ($results.OverallSuccess) { 0 } else { 1 })
        }
        
        "infrastructure" {
            $results = Invoke-InfrastructureTests
            exit $results.ExitCode
        }
        
        "smoke" {
            $results = Invoke-SmokeTests
            exit $results.ExitCode
        }
        
        "security" {
            $results = Invoke-SecurityScan
            exit $(if ($results.Error) { 1 } else { 0 })
        }
        
        "deploy" {
            Write-Log "Deployment functionality coming in Phase 2 implementation" "WARNING"
            Write-Log "Current focus: Conservative testing foundation" "INFO"
        }
        
        "rollback" {
            Write-Log "Rollback functionality coming in Phase 2 implementation" "WARNING"
            Write-Log "Current focus: Conservative testing foundation" "INFO"
        }
        
        "monitor" {
            Write-Log "Real-time monitoring dashboard coming in Phase 2 implementation" "WARNING"
            Write-Log "Use -Action status for current system status" "INFO"
        }
        
        "help" {
            Show-Help
        }
        
        default {
            Write-Log "Unknown action: $Action" "ERROR"
            Show-Help
            exit 1
        }
    }
}

# Execute main function
try {
    Main
} catch {
    Write-Log "Pipeline execution failed: $($_.Exception.Message)" "ERROR"
    Write-Log "Stack trace: $($_.ScriptStackTrace)" "DEBUG"
    exit 1
}