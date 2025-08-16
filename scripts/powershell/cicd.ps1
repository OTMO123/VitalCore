# =====================================================
# IRIS Healthcare API - CI/CD Pipeline Launcher
# Simple, compatible PowerShell launcher for CI/CD operations
# =====================================================

param(
    [Parameter(Position=0, Mandatory=$false)]
    [string]$Action = "help",
    [switch]$Verbose
)

# Configuration
$ProjectRoot = $PSScriptRoot
$ServerUrl = "http://localhost:8004"
$VenvPython = Join-Path $ProjectRoot "venv\Scripts\python.exe"

function Write-ColoredOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Test-Prerequisites {
    Write-ColoredOutput "Checking CI/CD prerequisites..." "Cyan"
    
    $allGood = $true
    
    # Check Python virtual environment
    if (Test-Path $VenvPython) {
        Write-ColoredOutput "  ✓ Python Virtual Environment: OK" "Green"
    } else {
        Write-ColoredOutput "  ✗ Python Virtual Environment: MISSING" "Red"
        $allGood = $false
    }
    
    # Check pytest
    try {
        $null = & $VenvPython -m pytest --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-ColoredOutput "  ✓ Pytest Framework: OK" "Green"
        } else {
            Write-ColoredOutput "  ✗ Pytest Framework: MISSING" "Red"
            $allGood = $false
        }
    } catch {
        Write-ColoredOutput "  ✗ Pytest Framework: ERROR" "Red"
        $allGood = $false
    }
    
    # Check database
    try {
        $connection = Test-NetConnection -ComputerName "localhost" -Port 5432 -WarningAction SilentlyContinue
        if ($connection.TcpTestSucceeded) {
            Write-ColoredOutput "  ✓ PostgreSQL Database: ACCESSIBLE" "Green"
        } else {
            Write-ColoredOutput "  ⚠ PostgreSQL Database: NOT ACCESSIBLE" "Yellow"
        }
    } catch {
        Write-ColoredOutput "  ⚠ PostgreSQL Database: ERROR" "Yellow"
    }
    
    return $allGood
}

function Get-SystemStatus {
    Write-ColoredOutput "Checking system status..." "Cyan"
    
    # Check server health
    try {
        $response = Invoke-RestMethod -Uri "$ServerUrl/health" -TimeoutSec 5
        Write-ColoredOutput "  ✓ API Server: HEALTHY ($($response.status))" "Green"
    } catch {
        Write-ColoredOutput "  ✗ API Server: UNAVAILABLE" "Red"
    }
    
    # Check API documentation
    try {
        $response = Invoke-WebRequest -Uri "$ServerUrl/docs" -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-ColoredOutput "  ✓ API Documentation: ACCESSIBLE" "Green"
        }
    } catch {
        Write-ColoredOutput "  ✗ API Documentation: UNAVAILABLE" "Red"
    }
}

function Invoke-InfrastructureTests {
    Write-ColoredOutput "Running infrastructure tests..." "Cyan"
    
    Set-Location $ProjectRoot
    $env:PYTHONPATH = $ProjectRoot
    
    try {
        $output = & $VenvPython -m pytest "app\tests\infrastructure\test_system_health.py" -v --tb=short 2>&1
        
        $passedCount = ($output | Select-String "PASSED").Count
        $failedCount = ($output | Select-String "FAILED").Count
        $skippedCount = ($output | Select-String "SKIPPED").Count
        $totalCount = $passedCount + $failedCount + $skippedCount
        
        Write-ColoredOutput "Infrastructure Test Results:" "White"
        Write-ColoredOutput "  Total: $totalCount" "White"
        Write-ColoredOutput "  Passed: $passedCount" "Green"
        Write-ColoredOutput "  Failed: $failedCount" $(if ($failedCount -gt 0) { "Red" } else { "White" })
        Write-ColoredOutput "  Skipped: $skippedCount" "Yellow"
        
        if ($totalCount -gt 0) {
            $passRate = [math]::Round(($passedCount / $totalCount) * 100, 1)
            Write-ColoredOutput "  Pass Rate: $passRate%" $(if ($passRate -ge 75) { "Green" } else { "Yellow" })
        }
        
        if ($Verbose) {
            Write-ColoredOutput "Detailed Output:" "Gray"
            $output | ForEach-Object { Write-ColoredOutput "  $_" "Gray" }
        }
        
        return $LASTEXITCODE
    } catch {
        Write-ColoredOutput "Infrastructure tests failed: $($_.Exception.Message)" "Red"
        return 1
    }
}

function Invoke-SmokeTests {
    Write-ColoredOutput "Running smoke tests..." "Cyan"
    
    Set-Location $ProjectRoot
    $env:PYTHONPATH = $ProjectRoot
    
    try {
        $output = & $VenvPython -m pytest "app\tests\smoke\test_authentication_basic.py" -v --tb=short 2>&1
        
        $passedCount = ($output | Select-String "PASSED").Count
        $failedCount = ($output | Select-String "FAILED").Count
        $skippedCount = ($output | Select-String "SKIPPED").Count
        $totalCount = $passedCount + $failedCount + $skippedCount
        
        Write-ColoredOutput "Smoke Test Results:" "White"
        Write-ColoredOutput "  Total: $totalCount" "White"
        Write-ColoredOutput "  Passed: $passedCount" "Green"
        Write-ColoredOutput "  Failed: $failedCount" $(if ($failedCount -gt 0) { "Red" } else { "White" })
        Write-ColoredOutput "  Skipped: $skippedCount" "Yellow"
        
        if ($totalCount -gt 0) {
            $passRate = [math]::Round(($passedCount / $totalCount) * 100, 1)
            Write-ColoredOutput "  Pass Rate: $passRate%" $(if ($passRate -ge 80) { "Green" } else { "Yellow" })
        }
        
        if ($Verbose) {
            Write-ColoredOutput "Detailed Output:" "Gray"
            $output | ForEach-Object { Write-ColoredOutput "  $_" "Gray" }
        }
        
        return $LASTEXITCODE
    } catch {
        Write-ColoredOutput "Smoke tests failed: $($_.Exception.Message)" "Red"
        return 1
    }
}

function Invoke-SecurityScan {
    Write-ColoredOutput "Running security scan..." "Cyan"
    
    Set-Location $ProjectRoot
    
    try {
        # Try to run bandit
        $output = & $VenvPython -m bandit -r app\ -ll 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColoredOutput "  ✓ Bandit Security Scan: CLEAN" "Green"
        } else {
            Write-ColoredOutput "  ⚠ Bandit Security Scan: ISSUES DETECTED" "Yellow"
        }
        
        if ($Verbose) {
            Write-ColoredOutput "Security Scan Output:" "Gray"
            $output | ForEach-Object { Write-ColoredOutput "  $_" "Gray" }
        }
        
        return $LASTEXITCODE
    } catch {
        Write-ColoredOutput "Security scan failed: $($_.Exception.Message)" "Red"
        return 1
    }
}

function Show-Help {
    Write-ColoredOutput "IRIS Healthcare API - CI/CD Pipeline Launcher" "Cyan"
    Write-ColoredOutput "=============================================" "Cyan"
    Write-ColoredOutput ""
    Write-ColoredOutput "USAGE:" "White"
    Write-ColoredOutput "  .\cicd.ps1 <command> [-Verbose]" "Gray"
    Write-ColoredOutput ""
    Write-ColoredOutput "COMMANDS:" "White"
    Write-ColoredOutput "  status      - Check system and pipeline status" "Gray"
    Write-ColoredOutput "  test        - Run complete test pipeline" "Gray"
    Write-ColoredOutput "  infra       - Run infrastructure tests only" "Gray"
    Write-ColoredOutput "  smoke       - Run smoke tests only" "Gray"
    Write-ColoredOutput "  security    - Run security scan only" "Gray"
    Write-ColoredOutput "  prereq      - Check prerequisites" "Gray"
    Write-ColoredOutput "  help        - Show this help message" "Gray"
    Write-ColoredOutput ""
    Write-ColoredOutput "OPTIONS:" "White"
    Write-ColoredOutput "  -Verbose    - Show detailed output" "Gray"
    Write-ColoredOutput ""
    Write-ColoredOutput "EXAMPLES:" "White"
    Write-ColoredOutput "  .\cicd.ps1 status" "Gray"
    Write-ColoredOutput "  .\cicd.ps1 test -Verbose" "Gray"
    Write-ColoredOutput "  .\cicd.ps1 infra" "Gray"
    Write-ColoredOutput ""
    Write-ColoredOutput "For detailed documentation: reports\cicd\README.md" "Yellow"
}

# Main execution
Write-ColoredOutput "🚀 IRIS Healthcare API - CI/CD Pipeline" "Cyan"
Write-ColoredOutput "Action: $Action" "Gray"
Write-ColoredOutput ""

switch ($Action.ToLower()) {
    "status" {
        Get-SystemStatus
    }
    
    "prereq" {
        Test-Prerequisites
    }
    
    "test" {
        Write-ColoredOutput "Running complete CI/CD pipeline..." "Cyan"
        $prereqOk = Test-Prerequisites
        if (-not $prereqOk) {
            Write-ColoredOutput "Prerequisites check failed - some tests may not work properly" "Yellow"
        }
        
        $infraResult = Invoke-InfrastructureTests
        Write-ColoredOutput ""
        $smokeResult = Invoke-SmokeTests
        Write-ColoredOutput ""
        $securityResult = Invoke-SecurityScan
        
        Write-ColoredOutput ""
        Write-ColoredOutput "=====================================" "Cyan"
        Write-ColoredOutput "CI/CD Pipeline Results Summary" "Cyan"
        Write-ColoredOutput "=====================================" "Cyan"
        Write-ColoredOutput "Infrastructure Tests: $(if ($infraResult -eq 0) { 'PASSED' } else { 'ISSUES' })" $(if ($infraResult -eq 0) { "Green" } else { "Yellow" })
        Write-ColoredOutput "Smoke Tests: $(if ($smokeResult -eq 0) { 'PASSED' } else { 'ISSUES' })" $(if ($smokeResult -eq 0) { "Green" } else { "Yellow" })
        Write-ColoredOutput "Security Scan: $(if ($securityResult -eq 0) { 'CLEAN' } else { 'ISSUES' })" $(if ($securityResult -eq 0) { "Green" } else { "Yellow" })
        
        $overallSuccess = ($infraResult -eq 0) -and ($smokeResult -eq 0) -and ($securityResult -eq 0)
        Write-ColoredOutput "Overall: $(if ($overallSuccess) { 'SUCCESS' } else { 'ATTENTION NEEDED' })" $(if ($overallSuccess) { "Green" } else { "Yellow" })
        
        exit $(if ($overallSuccess) { 0 } else { 1 })
    }
    
    "infra" {
        $result = Invoke-InfrastructureTests
        exit $result
    }
    
    "smoke" {
        $result = Invoke-SmokeTests
        exit $result
    }
    
    "security" {
        $result = Invoke-SecurityScan
        exit $result
    }
    
    "help" {
        Show-Help
    }
    
    default {
        Write-ColoredOutput "Unknown command: $Action" "Red"
        Write-ColoredOutput "Use 'help' to see available commands" "Yellow"
        exit 1
    }
}