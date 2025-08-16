# IRIS Healthcare API - Pipeline Launcher (PL)
# Simple CI/CD pipeline operations

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

$ProjectRoot = $PSScriptRoot
$VenvPython = Join-Path $ProjectRoot "venv\Scripts\python.exe"

function Write-Status($Message, $Type = "INFO") {
    $colors = @{
        "INFO" = "White"
        "SUCCESS" = "Green" 
        "WARNING" = "Yellow"
        "ERROR" = "Red"
        "HEADER" = "Cyan"
    }
    Write-Host $Message -ForegroundColor $colors[$Type]
}

function Test-Requirements {
    Write-Status "Checking requirements..." "HEADER"
    
    if (Test-Path $VenvPython) {
        Write-Status "  Python environment: OK" "SUCCESS"
    } else {
        Write-Status "  Python environment: MISSING" "ERROR"
        return $false
    }
    
    try {
        & $VenvPython -m pytest --version | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Status "  Pytest framework: OK" "SUCCESS"
        } else {
            Write-Status "  Pytest framework: MISSING" "ERROR"
            return $false
        }
    } catch {
        Write-Status "  Pytest framework: ERROR" "ERROR"
        return $false
    }
    
    return $true
}

function Run-InfrastructureTests {
    Write-Status "Running infrastructure tests..." "HEADER"
    
    Set-Location $ProjectRoot
    $env:PYTHONPATH = $ProjectRoot
    
    & $VenvPython -m pytest "app\tests\infrastructure\test_system_health.py" -v --tb=short
    return $LASTEXITCODE
}

function Run-SmokeTests {
    Write-Status "Running smoke tests..." "HEADER"
    
    Set-Location $ProjectRoot
    $env:PYTHONPATH = $ProjectRoot
    
    & $VenvPython -m pytest "app\tests\smoke\test_authentication_basic.py" -v --tb=short
    return $LASTEXITCODE
}

function Show-Help {
    Write-Status "IRIS Healthcare API - Pipeline Launcher" "HEADER"
    Write-Status "======================================="
    Write-Status ""
    Write-Status "COMMANDS:"
    Write-Status "  status  - Check system status"
    Write-Status "  test    - Run complete pipeline"
    Write-Status "  infra   - Run infrastructure tests"
    Write-Status "  smoke   - Run smoke tests"
    Write-Status "  help    - Show this help"
    Write-Status ""
    Write-Status "USAGE:"
    Write-Status "  .\pl.ps1 test"
    Write-Status "  .\pl.ps1 infra -Verbose"
}

# Main execution
Write-Status "IRIS Healthcare API - CI/CD Pipeline" "HEADER"

switch ($Command.ToLower()) {
    "status" {
        Write-Status "Checking system status..." "HEADER"
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:8004/health" -TimeoutSec 5
            Write-Status "  API Server: HEALTHY" "SUCCESS"
        } catch {
            Write-Status "  API Server: UNAVAILABLE" "WARNING"
        }
    }
    
    "test" {
        if (Test-Requirements) {
            $infraResult = Run-InfrastructureTests
            $smokeResult = Run-SmokeTests
            
            Write-Status "" 
            Write-Status "Pipeline Results:" "HEADER"
            Write-Status "  Infrastructure: $(if ($infraResult -eq 0) { 'PASSED' } else { 'ISSUES' })" $(if ($infraResult -eq 0) { "SUCCESS" } else { "WARNING" })
            Write-Status "  Smoke Tests: $(if ($smokeResult -eq 0) { 'PASSED' } else { 'ISSUES' })" $(if ($smokeResult -eq 0) { "SUCCESS" } else { "WARNING" })
        }
    }
    
    "infra" {
        if (Test-Requirements) {
            $result = Run-InfrastructureTests
            exit $result
        }
    }
    
    "smoke" {
        if (Test-Requirements) {
            $result = Run-SmokeTests
            exit $result
        }
    }
    
    "help" {
        Show-Help
    }
    
    default {
        Write-Status "Unknown command: $Command" "ERROR"
        Show-Help
    }
}