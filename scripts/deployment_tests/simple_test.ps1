# Simple Infrastructure Test - Compatible with Russian PowerShell
# Tests basic connectivity without complex syntax

Write-Host "Simple Infrastructure Test" -ForegroundColor Green
Write-Host "==========================" -ForegroundColor Green

$results = @()

# Test Database Connection
Write-Host "`nTesting Database..." -ForegroundColor Yellow
try {
    $dbHost = "localhost"
    $dbPort = 5432
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $tcpClient.ReceiveTimeout = 5000
    $tcpClient.SendTimeout = 5000
    $tcpClient.Connect($dbHost, $dbPort)
    $tcpClient.Close()
    Write-Host "Database: PASS" -ForegroundColor Green
    $results += "Database Connection: PASS"
}
catch {
    Write-Host "Database: FAIL - $($_.Exception.Message)" -ForegroundColor Red
    $results += "Database Connection: FAIL"
}

# Test Redis Connection  
Write-Host "`nTesting Redis..." -ForegroundColor Yellow
try {
    $redisHost = "localhost"
    $redisPort = 6379
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $tcpClient.ReceiveTimeout = 5000
    $tcpClient.SendTimeout = 5000
    $tcpClient.Connect($redisHost, $redisPort)
    $tcpClient.Close()
    Write-Host "Redis: PASS" -ForegroundColor Green
    $results += "Redis Connection: PASS"
}
catch {
    Write-Host "Redis: FAIL - $($_.Exception.Message)" -ForegroundColor Red
    $results += "Redis Connection: FAIL"
}

# Test Application Health
Write-Host "`nTesting Application Health..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 10 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "Application Health: PASS" -ForegroundColor Green
        $results += "Application Health: PASS"
    } else {
        Write-Host "Application Health: FAIL - HTTP $($response.StatusCode)" -ForegroundColor Red
        $results += "Application Health: FAIL"
    }
}
catch {
    Write-Host "Application Health: FAIL - $($_.Exception.Message)" -ForegroundColor Red
    $results += "Application Health: FAIL"
}

# Test Healthcare API
Write-Host "`nTesting Healthcare API..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/healthcare-records/health" -TimeoutSec 10 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "Healthcare API: PASS" -ForegroundColor Green
        $results += "Healthcare API: PASS"
    } else {
        Write-Host "Healthcare API: FAIL - HTTP $($response.StatusCode)" -ForegroundColor Red
        $results += "Healthcare API: FAIL"
    }
}
catch {
    Write-Host "Healthcare API: FAIL - $($_.Exception.Message)" -ForegroundColor Red
    $results += "Healthcare API: FAIL"
}

# Show Summary
Write-Host "`nTest Summary:" -ForegroundColor Cyan
Write-Host "=============" -ForegroundColor Cyan
foreach ($result in $results) {
    if ($result -match "PASS") {
        Write-Host $result -ForegroundColor Green
    } else {
        Write-Host $result -ForegroundColor Red
    }
}

$passCount = ($results | Where-Object { $_ -match "PASS" }).Count
$totalCount = $results.Count

Write-Host "`nResults: $passCount/$totalCount tests passed" -ForegroundColor $(if ($passCount -eq $totalCount) { "Green" } else { "Yellow" })

if ($passCount -eq $totalCount) {
    Write-Host "All basic infrastructure tests passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "Some tests failed. Check service status." -ForegroundColor Yellow
    exit 1
}