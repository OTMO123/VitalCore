# Working Infrastructure Test - Russian PowerShell Compatible
# No colons in strings, no Host parameter conflicts, proper syntax

Write-Host "Working Infrastructure Test" -ForegroundColor Green
Write-Host "============================" -ForegroundColor Green

$results = @()
$passed = 0
$failed = 0

Write-Host "`nChecking required services..." -ForegroundColor Cyan
Write-Host "Note: Services need to be running for tests to pass" -ForegroundColor Gray

# Test Database Connection
Write-Host "`nTesting Database..." -ForegroundColor Yellow
try {
    $dbHostname = "localhost"
    $dbPortNum = 5432
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $tcpClient.ReceiveTimeout = 5000
    $tcpClient.SendTimeout = 5000
    $tcpClient.Connect($dbHostname, $dbPortNum)
    $tcpClient.Close()
    Write-Host "Database Connection - PASS" -ForegroundColor Green
    $results += "Database Connection - PASS"
    $passed++
}
catch {
    Write-Host "Database Connection - FAIL" -ForegroundColor Red
    Write-Host "  Error - $($_.Exception.Message)" -ForegroundColor Red
    $results += "Database Connection - FAIL"
    $failed++
}

# Test Redis Connection  
Write-Host "`nTesting Redis..." -ForegroundColor Yellow
try {
    $redisHostname = "localhost"
    $redisPortNum = 6379
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $tcpClient.ReceiveTimeout = 5000
    $tcpClient.SendTimeout = 5000
    $tcpClient.Connect($redisHostname, $redisPortNum)
    $tcpClient.Close()
    Write-Host "Redis Connection - PASS" -ForegroundColor Green
    $results += "Redis Connection - PASS"
    $passed++
}
catch {
    Write-Host "Redis Connection - FAIL" -ForegroundColor Red
    Write-Host "  Error - $($_.Exception.Message)" -ForegroundColor Red
    $results += "Redis Connection - FAIL"
    $failed++
}

# Test Application Health
Write-Host "`nTesting Application Health..." -ForegroundColor Yellow
try {
    $healthUrl = "http://localhost:8000/health"
    $response = Invoke-WebRequest -Uri $healthUrl -TimeoutSec 10 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "Application Health - PASS" -ForegroundColor Green
        $results += "Application Health - PASS"
        $passed++
    } else {
        Write-Host "Application Health - FAIL (HTTP $($response.StatusCode))" -ForegroundColor Red
        $results += "Application Health - FAIL"
        $failed++
    }
}
catch {
    Write-Host "Application Health - FAIL" -ForegroundColor Red
    Write-Host "  Error - $($_.Exception.Message)" -ForegroundColor Red
    $results += "Application Health - FAIL"
    $failed++
}

# Test Healthcare API
Write-Host "`nTesting Healthcare API..." -ForegroundColor Yellow
try {
    $apiUrl = "http://localhost:8000/api/v1/healthcare-records/health"
    $response = Invoke-WebRequest -Uri $apiUrl -TimeoutSec 10 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "Healthcare API - PASS" -ForegroundColor Green
        $results += "Healthcare API - PASS"
        $passed++
    } else {
        Write-Host "Healthcare API - FAIL (HTTP $($response.StatusCode))" -ForegroundColor Red
        $results += "Healthcare API - FAIL"
        $failed++
    }
}
catch {
    Write-Host "Healthcare API - FAIL" -ForegroundColor Red
    Write-Host "  Error - $($_.Exception.Message)" -ForegroundColor Red
    $results += "Healthcare API - FAIL"
    $failed++
}

# Test Docker
Write-Host "`nTesting Docker..." -ForegroundColor Yellow
try {
    $dockerResult = & docker --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Docker Service - PASS" -ForegroundColor Green
        $results += "Docker Service - PASS"
        $passed++
    } else {
        Write-Host "Docker Service - FAIL" -ForegroundColor Red
        $results += "Docker Service - FAIL"
        $failed++
    }
}
catch {
    Write-Host "Docker Service - FAIL" -ForegroundColor Red
    Write-Host "  Error - $($_.Exception.Message)" -ForegroundColor Red
    $results += "Docker Service - FAIL"
    $failed++
}

# Test Environment Variables
Write-Host "`nTesting Environment Configuration..." -ForegroundColor Yellow
$envIssues = 0

$dbUrl = [Environment]::GetEnvironmentVariable("DATABASE_URL")
if ([string]::IsNullOrEmpty($dbUrl)) {
    Write-Host "  DATABASE_URL - Missing" -ForegroundColor Red
    $envIssues++
} else {
    Write-Host "  DATABASE_URL - Set" -ForegroundColor Green
}

$jwtSecret = [Environment]::GetEnvironmentVariable("JWT_SECRET_KEY")
if ([string]::IsNullOrEmpty($jwtSecret)) {
    Write-Host "  JWT_SECRET_KEY - Missing" -ForegroundColor Red
    $envIssues++
} else {
    Write-Host "  JWT_SECRET_KEY - Set" -ForegroundColor Green
}

$phiKey = [Environment]::GetEnvironmentVariable("PHI_ENCRYPTION_KEY")
if ([string]::IsNullOrEmpty($phiKey)) {
    Write-Host "  PHI_ENCRYPTION_KEY - Missing" -ForegroundColor Red
    $envIssues++
} else {
    Write-Host "  PHI_ENCRYPTION_KEY - Set" -ForegroundColor Green
}

if ($envIssues -eq 0) {
    Write-Host "Environment Configuration - PASS" -ForegroundColor Green
    $results += "Environment Configuration - PASS"
    $passed++
} else {
    Write-Host "Environment Configuration - FAIL ($envIssues missing)" -ForegroundColor Red
    $results += "Environment Configuration - FAIL"
    $failed++
}

# Show Summary
Write-Host "`nTest Results Summary" -ForegroundColor Cyan  
Write-Host "====================" -ForegroundColor Cyan

foreach ($result in $results) {
    if ($result -match "PASS") {
        Write-Host "  $result" -ForegroundColor Green
    } else {
        Write-Host "  $result" -ForegroundColor Red
    }
}

$total = $passed + $failed
$successRate = if ($total -gt 0) { [math]::Round(($passed / $total) * 100, 1) } else { 0 }

Write-Host "`nOverall Results" -ForegroundColor Cyan
Write-Host "  Passed - $passed" -ForegroundColor Green
Write-Host "  Failed - $failed" -ForegroundColor $(if ($failed -eq 0) { "Green" } else { "Red" })
Write-Host "  Success Rate - $successRate%" -ForegroundColor $(if ($failed -eq 0) { "Green" } elseif ($failed -le 2) { "Yellow" } else { "Red" })

# Final Status
Write-Host "`nFinal Assessment" -ForegroundColor Cyan
if ($failed -eq 0) {
    Write-Host "SUCCESS - All critical components are working!" -ForegroundColor Green
    Write-Host "System appears ready for deployment." -ForegroundColor Green
    
    Write-Host "`nNext Steps:" -ForegroundColor Cyan
    Write-Host "  1. Run full deployment validation tests" -ForegroundColor White
    Write-Host "  2. Check security and compliance settings" -ForegroundColor White
    Write-Host "  3. Verify monitoring and alerting" -ForegroundColor White
    
    exit 0
} elseif ($failed -le 2) {
    Write-Host "WARNING - Some components have issues but core system is functional." -ForegroundColor Yellow
    Write-Host "Review failed tests and fix if needed." -ForegroundColor Yellow
    
    Write-Host "`nCommon Solutions:" -ForegroundColor Cyan
    Write-Host "  - Start services with: docker-compose up -d" -ForegroundColor White
    Write-Host "  - Start application with: python app/main.py" -ForegroundColor White
    Write-Host "  - Check .env file for missing variables" -ForegroundColor White
    
    exit 1
} else {
    Write-Host "FAILED - Multiple critical issues detected!" -ForegroundColor Red
    Write-Host "System is not ready for deployment." -ForegroundColor Red
    
    Write-Host "`nRequired Actions:" -ForegroundColor Cyan
    Write-Host "  1. Start required services (Database, Redis, Application)" -ForegroundColor White
    Write-Host "  2. Configure environment variables" -ForegroundColor White
    Write-Host "  3. Verify Docker installation" -ForegroundColor White
    Write-Host "  4. Re-run this test after fixes" -ForegroundColor White
    
    exit 2
}

Write-Host "`nFor detailed testing, run the full deployment validation suite." -ForegroundColor Gray