# Quick Deployment Test - Russian PowerShell Compatible
# Fast validation of critical components

param(
    [switch]$Verbose
)

Write-Host "Quick Deployment Validation" -ForegroundColor Green
Write-Host "===========================" -ForegroundColor Green

$tests = @()
$passed = 0
$failed = 0

function Test-Component {
    param([string]$Name, [scriptblock]$TestScript)
    
    Write-Host "`nTesting $Name..." -ForegroundColor Yellow
    
    try {
        $result = & $TestScript
        if ($result) {
            Write-Host "  ${Name}: PASS" -ForegroundColor Green
            $script:passed++
            $script:tests += "${Name}: PASS"
            return $true
        } else {
            Write-Host "  ${Name}: FAIL" -ForegroundColor Red
            $script:failed++
            $script:tests += "${Name}: FAIL"
            return $false
        }
    }
    catch {
        Write-Host "  ${Name}: FAIL - $($_.Exception.Message)" -ForegroundColor Red
        if ($Verbose) {
            Write-Host "    Error details: $($_.Exception.Message)" -ForegroundColor Gray
        }
        $script:failed++
        $script:tests += "${Name}: FAIL - $($_.Exception.Message)"
        return $false
    }
}

# Test Database
Test-Component "Database Connection" {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $tcpClient.ReceiveTimeout = 3000
    $tcpClient.SendTimeout = 3000
    $tcpClient.Connect("localhost", 5432)
    $tcpClient.Close()
    return $true
}

# Test Redis
Test-Component "Redis Connection" {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $tcpClient.ReceiveTimeout = 3000
    $tcpClient.SendTimeout = 3000
    $tcpClient.Connect("localhost", 6379)
    $tcpClient.Close()
    return $true
}

# Test Application
Test-Component "Application Health" {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -UseBasicParsing
    return ($response.StatusCode -eq 200)
}

# Test Healthcare API
Test-Component "Healthcare API" {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/healthcare/health" -TimeoutSec 5 -UseBasicParsing
    return ($response.StatusCode -eq 200)
}

# Test Docker
Test-Component "Docker Service" {
    $dockerVersion = & docker --version 2>$null
    return ($LASTEXITCODE -eq 0)
}

# Check Environment Variables
Test-Component "Environment Configuration" {
    $dbUrl = [Environment]::GetEnvironmentVariable("DATABASE_URL")
    $jwtSecret = [Environment]::GetEnvironmentVariable("JWT_SECRET_KEY")
    $phiKey = [Environment]::GetEnvironmentVariable("PHI_ENCRYPTION_KEY")
    
    return (![string]::IsNullOrEmpty($dbUrl) -and ![string]::IsNullOrEmpty($jwtSecret) -and ![string]::IsNullOrEmpty($phiKey))
}

# Show Results
Write-Host "`nTest Results Summary:" -ForegroundColor Cyan
Write-Host "=====================" -ForegroundColor Cyan

foreach ($test in $tests) {
    if ($test -match "PASS") {
        Write-Host "  $test" -ForegroundColor Green
    } else {
        Write-Host "  $test" -ForegroundColor Red
    }
}

Write-Host "`nOverall Results:" -ForegroundColor Cyan
Write-Host "  Passed: $passed" -ForegroundColor Green
Write-Host "  Failed: $failed" -ForegroundColor $(if ($failed -eq 0) { "Green" } else { "Red" })
Write-Host "  Success Rate: $([math]::Round(($passed / ($passed + $failed)) * 100, 1))%" -ForegroundColor $(if ($failed -eq 0) { "Green" } elseif ($failed -le 2) { "Yellow" } else { "Red" })

# Final Status
if ($failed -eq 0) {
    Write-Host "`nSUCCESS: All critical components are working!" -ForegroundColor Green
    Write-Host "System appears ready for deployment." -ForegroundColor Green
    exit 0
} elseif ($failed -le 2) {
    Write-Host "`nWARNING: Some components have issues but core system is functional." -ForegroundColor Yellow
    Write-Host "Review failed tests and fix if needed." -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "`nFAILED: Multiple critical issues detected!" -ForegroundColor Red
    Write-Host "System is not ready for deployment. Fix issues before proceeding." -ForegroundColor Red
    exit 2
}

Write-Host "`nFor detailed testing, run: .\1_infrastructure_validation_fixed.ps1" -ForegroundColor Cyan