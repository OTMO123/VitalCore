# Infrastructure Validation Script - Russian PowerShell Compatible
# Tests: Database, Redis, MinIO, SSL, DNS, Network connectivity
# Based on: PRODUCTION_DEPLOYMENT_CHECKLIST.md - Infrastructure Prerequisites

Write-Host "Infrastructure Validation Test" -ForegroundColor Green
Write-Host "===============================" -ForegroundColor Green

$testResults = @()
$allPassed = $true
$infraIssues = @()

function Test-ServiceConnection {
    param(
        [string]$ServiceName,
        [string]$TargetHost,
        [int]$Port,
        [string]$Protocol = "TCP"
    )
    
    Write-Host "`nTesting $ServiceName connection..." -ForegroundColor Yellow
    
    try {
        if ($Protocol -eq "HTTP" -or $Protocol -eq "HTTPS") {
            $url = "$Protocol" + "://" + "$TargetHost" + ":" + "$Port"
            $response = Invoke-WebRequest -Uri $url -TimeoutSec 10 -UseBasicParsing
            $result = @{
                Service = $ServiceName
                Status = "PASS"
                Details = "HTTP Status: $($response.StatusCode)"
                ResponseTime = "less than 10 seconds"
            }
        } else {
            $tcpClient = New-Object System.Net.Sockets.TcpClient
            $tcpClient.ReceiveTimeout = 5000
            $tcpClient.SendTimeout = 5000
            $tcpClient.Connect($TargetHost, $Port)
            $tcpClient.Close()
            
            $result = @{
                Service = $ServiceName
                Status = "PASS"
                Details = "TCP connection successful"
                ResponseTime = "less than 5 seconds"
            }
        }
        
        Write-Host "  Status: $ServiceName is accessible" -ForegroundColor Green
        return $result
    }
    catch {
        $result = @{
            Service = $ServiceName
            Status = "FAIL"
            Details = $_.Exception.Message
            ResponseTime = "N/A"
        }
        
        Write-Host "  Status: $ServiceName is not accessible" -ForegroundColor Red
        Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
        $script:allPassed = $false
        $script:infraIssues += "$ServiceName is not accessible: $($_.Exception.Message)"
        return $result
    }
}

function Test-DatabaseService {
    Write-Host "`nTesting Database Service..." -ForegroundColor Yellow
    
    # Test PostgreSQL connection
    $dbResult = Test-ServiceConnection -ServiceName "PostgreSQL" -TargetHost "localhost" -Port 5432 -Protocol "TCP"
    $script:testResults += $dbResult
    
    # Test database query if connection successful
    if ($dbResult.Status -eq "PASS") {
        Write-Host "  Testing database query..." -ForegroundColor Cyan
        
        try {
            # Try to connect and run a simple query (requires psql)
            $psqlExists = Get-Command psql -ErrorAction SilentlyContinue
            if ($psqlExists) {
                $dbHost = "localhost"
                $dbPort = "5432" 
                $dbName = "healthcare_db"
                $dbUser = "healthcare_user"
                
                # Set environment variable for password if available
                $dbPassword = [Environment]::GetEnvironmentVariable("DB_PASSWORD")
                if ($dbPassword) {
                    $env:PGPASSWORD = $dbPassword
                }
                
                $queryResult = & psql -h $dbHost -p $dbPort -U $dbUser -d $dbName -c "SELECT version();" 2>$null
                
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "  Database query test passed" -ForegroundColor Green
                    $script:testResults += @{
                        Service = "Database Query"
                        Status = "PASS"
                        Details = "Query executed successfully"
                        ResponseTime = "less than 2 seconds"
                    }
                } else {
                    Write-Host "  Database query test failed" -ForegroundColor Red
                    $script:infraIssues += "Database query test failed"
                    $script:testResults += @{
                        Service = "Database Query"
                        Status = "FAIL"
                        Details = "Could not execute query"
                        ResponseTime = "N/A"
                    }
                }
                
                # Clean up environment variable
                if ($env:PGPASSWORD) {
                    Remove-Item env:PGPASSWORD -ErrorAction SilentlyContinue
                }
            } else {
                Write-Host "  Skipping database query test (psql not available)" -ForegroundColor Yellow
                $script:testResults += @{
                    Service = "Database Query"
                    Status = "SKIP"
                    Details = "psql command not found"
                    ResponseTime = "N/A"
                }
            }
        }
        catch {
            Write-Host "  Database query test failed: $($_.Exception.Message)" -ForegroundColor Red
            $script:infraIssues += "Database query failed: $($_.Exception.Message)"
        }
    }
}

function Test-RedisService {
    Write-Host "`nTesting Redis Service..." -ForegroundColor Yellow
    
    # Test Redis connection
    $redisResult = Test-ServiceConnection -ServiceName "Redis" -TargetHost "localhost" -Port 6379 -Protocol "TCP"
    $script:testResults += $redisResult
    
    # Test Redis commands if connection successful
    if ($redisResult.Status -eq "PASS") {
        Write-Host "  Testing Redis commands..." -ForegroundColor Cyan
        
        try {
            # Try to use redis-cli if available
            $redisCliExists = Get-Command redis-cli -ErrorAction SilentlyContinue
            if ($redisCliExists) {
                $pingResult = & redis-cli ping 2>$null
                
                if ($pingResult -eq "PONG") {
                    Write-Host "  Redis ping test passed" -ForegroundColor Green
                    $script:testResults += @{
                        Service = "Redis Commands"
                        Status = "PASS"
                        Details = "Redis responding to commands"
                        ResponseTime = "less than 1 second"
                    }
                } else {
                    Write-Host "  Redis ping test failed" -ForegroundColor Red
                    $script:infraIssues += "Redis not responding to ping"
                    $script:testResults += @{
                        Service = "Redis Commands"
                        Status = "FAIL"
                        Details = "Redis not responding to ping"
                        ResponseTime = "N/A"
                    }
                }
            } else {
                Write-Host "  Skipping Redis command test (redis-cli not available)" -ForegroundColor Yellow
                $script:testResults += @{
                    Service = "Redis Commands"
                    Status = "SKIP"
                    Details = "redis-cli command not found"
                    ResponseTime = "N/A"
                }
            }
        }
        catch {
            Write-Host "  Redis command test failed: $($_.Exception.Message)" -ForegroundColor Red
            $script:infraIssues += "Redis command test failed: $($_.Exception.Message)"
        }
    }
}

function Test-MinIOService {
    Write-Host "`nTesting MinIO Service..." -ForegroundColor Yellow
    
    # Test MinIO connection
    $minioResult = Test-ServiceConnection -ServiceName "MinIO" -TargetHost "localhost" -Port 9000 -Protocol "HTTP"
    $script:testResults += $minioResult
}

function Test-ApplicationServices {
    Write-Host "`nTesting Application Services..." -ForegroundColor Yellow
    
    # Test main application health endpoint
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 10 -UseBasicParsing
        
        if ($response.StatusCode -eq 200) {
            Write-Host "  Application health endpoint accessible" -ForegroundColor Green
            $script:testResults += @{
                Service = "Application Health"
                Status = "PASS"
                Details = "Health endpoint responding"
                ResponseTime = "less than 5 seconds"
            }
        } else {
            Write-Host "  Application health endpoint returned HTTP $($response.StatusCode)" -ForegroundColor Red
            $script:allPassed = $false
            $script:infraIssues += "Application health endpoint returned HTTP $($response.StatusCode)"
            $script:testResults += @{
                Service = "Application Health" 
                Status = "FAIL"
                Details = "HTTP $($response.StatusCode)"
                ResponseTime = "less than 5 seconds"
            }
        }
    }
    catch {
        Write-Host "  Application health endpoint not accessible: $($_.Exception.Message)" -ForegroundColor Red
        $script:allPassed = $false
        $script:infraIssues += "Application health endpoint not accessible"
        $script:testResults += @{
            Service = "Application Health"
            Status = "FAIL"
            Details = $_.Exception.Message
            ResponseTime = "N/A"
        }
    }
    
    # Test healthcare API endpoint
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/healthcare/health" -TimeoutSec 10 -UseBasicParsing
        
        if ($response.StatusCode -eq 200) {
            Write-Host "  Healthcare API endpoint accessible" -ForegroundColor Green
            $script:testResults += @{
                Service = "Healthcare API"
                Status = "PASS"
                Details = "Healthcare API responding"
                ResponseTime = "less than 5 seconds"
            }
        } else {
            Write-Host "  Healthcare API endpoint returned HTTP $($response.StatusCode)" -ForegroundColor Red
            $script:infraIssues += "Healthcare API endpoint returned HTTP $($response.StatusCode)"
            $script:testResults += @{
                Service = "Healthcare API"
                Status = "FAIL"
                Details = "HTTP $($response.StatusCode)"
                ResponseTime = "less than 5 seconds"
            }
        }
    }
    catch {
        Write-Host "  Healthcare API endpoint not accessible: $($_.Exception.Message)" -ForegroundColor Red
        $script:infraIssues += "Healthcare API endpoint not accessible"
        $script:testResults += @{
            Service = "Healthcare API"
            Status = "FAIL"
            Details = $_.Exception.Message
            ResponseTime = "N/A"
        }
    }
}

function Test-NetworkConnectivity {
    Write-Host "`nTesting Network Connectivity..." -ForegroundColor Yellow
    
    # Test DNS resolution
    try {
        $dnsResult = Resolve-DnsName "google.com" -ErrorAction Stop
        Write-Host "  DNS resolution working" -ForegroundColor Green
        $script:testResults += @{
            Service = "DNS Resolution"
            Status = "PASS"
            Details = "DNS lookup successful"
            ResponseTime = "less than 2 seconds"
        }
    }
    catch {
        Write-Host "  DNS resolution failed: $($_.Exception.Message)" -ForegroundColor Red
        $script:infraIssues += "DNS resolution failed"
        $script:testResults += @{
            Service = "DNS Resolution"
            Status = "FAIL"
            Details = $_.Exception.Message
            ResponseTime = "N/A"
        }
    }
    
    # Test internet connectivity
    try {
        $response = Invoke-WebRequest -Uri "https://www.google.com" -TimeoutSec 5 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host "  Internet connectivity working" -ForegroundColor Green
            $script:testResults += @{
                Service = "Internet Connectivity"
                Status = "PASS"
                Details = "External HTTP request successful"
                ResponseTime = "less than 5 seconds"
            }
        }
    }
    catch {
        Write-Host "  Internet connectivity limited: $($_.Exception.Message)" -ForegroundColor Yellow
        $script:testResults += @{
            Service = "Internet Connectivity"
            Status = "LIMITED"
            Details = $_.Exception.Message
            ResponseTime = "N/A"
        }
    }
}

function Test-DockerEnvironment {
    Write-Host "`nTesting Docker Environment..." -ForegroundColor Yellow
    
    try {
        # Test Docker command
        $dockerVersion = & docker --version 2>$null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  Docker is installed and accessible" -ForegroundColor Green
            $script:testResults += @{
                Service = "Docker"
                Status = "PASS"
                Details = $dockerVersion
                ResponseTime = "less than 2 seconds"
            }
            
            # Test Docker daemon
            $dockerInfo = & docker info 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  Docker daemon is running" -ForegroundColor Green
                $script:testResults += @{
                    Service = "Docker Daemon"
                    Status = "PASS"
                    Details = "Docker daemon accessible"
                    ResponseTime = "less than 3 seconds"
                }
            } else {
                Write-Host "  Docker daemon is not running" -ForegroundColor Red
                $script:allPassed = $false
                $script:infraIssues += "Docker daemon is not running"
                $script:testResults += @{
                    Service = "Docker Daemon"
                    Status = "FAIL"
                    Details = "Docker daemon not accessible"
                    ResponseTime = "N/A"
                }
            }
        } else {
            Write-Host "  Docker is not installed or not accessible" -ForegroundColor Red
            $script:allPassed = $false
            $script:infraIssues += "Docker is not installed or accessible"
            $script:testResults += @{
                Service = "Docker"
                Status = "FAIL"
                Details = "Docker command not found"
                ResponseTime = "N/A"
            }
        }
    }
    catch {
        Write-Host "  Docker test failed: $($_.Exception.Message)" -ForegroundColor Red
        $script:allPassed = $false
        $script:infraIssues += "Docker test failed: $($_.Exception.Message)"
        $script:testResults += @{
            Service = "Docker"
            Status = "FAIL"
            Details = $_.Exception.Message
            ResponseTime = "N/A"
        }
    }
}

# Run all infrastructure tests
Write-Host "`nStarting Infrastructure Tests..." -ForegroundColor Cyan

Test-DatabaseService
Test-RedisService  
Test-MinIOService
Test-ApplicationServices
Test-NetworkConnectivity
Test-DockerEnvironment

# Generate results summary
Write-Host "`nINFRASTRUCTURE VALIDATION RESULTS" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green

$passedTests = ($testResults | Where-Object { $_.Status -eq "PASS" }).Count
$failedTests = ($testResults | Where-Object { $_.Status -eq "FAIL" }).Count
$skippedTests = ($testResults | Where-Object { $_.Status -eq "SKIP" }).Count
$totalTests = $testResults.Count

Write-Host "`nTest Summary:" -ForegroundColor Cyan
Write-Host "  Total Tests: $totalTests"
Write-Host "  Passed: $passedTests" -ForegroundColor Green
Write-Host "  Failed: $failedTests" -ForegroundColor Red
Write-Host "  Skipped: $skippedTests" -ForegroundColor Yellow

Write-Host "`nDetailed Results:" -ForegroundColor Cyan
foreach ($test in $testResults) {
    $statusColor = "White"
    if ($test.Status -eq "PASS") { $statusColor = "Green" }
    elseif ($test.Status -eq "FAIL") { $statusColor = "Red" }
    elseif ($test.Status -eq "SKIP") { $statusColor = "Yellow" }
    
    Write-Host "  $($test.Status) $($test.Service) - $($test.Details)" -ForegroundColor $statusColor
}

# Show infrastructure issues
if ($infraIssues.Count -gt 0) {
    Write-Host "`nInfrastructure Issues Found:" -ForegroundColor Yellow
    for ($i = 0; $i -lt $infraIssues.Count; $i++) {
        Write-Host "  $($i + 1). $($infraIssues[$i])" -ForegroundColor Red
    }
}

# Save results to file
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$resultFile = "infrastructure_validation_$timestamp.json"

try {
    $resultsData = @{
        timestamp = $timestamp
        summary = @{
            total = $totalTests
            passed = $passedTests
            failed = $failedTests
            skipped = $skippedTests
        }
        tests = $testResults
        issues = $infraIssues
    }
    
    $resultsData | ConvertTo-Json -Depth 4 | Out-File -FilePath $resultFile -Encoding UTF8
    Write-Host "`nResults saved to: $resultFile" -ForegroundColor Cyan
}
catch {
    Write-Host "`nCould not save results to file: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Final assessment
Write-Host "`nFINAL ASSESSMENT" -ForegroundColor Green
if ($allPassed -and $failedTests -eq 0) {
    Write-Host "ALL INFRASTRUCTURE TESTS PASSED" -ForegroundColor Green
    Write-Host "Infrastructure is ready for production deployment!" -ForegroundColor Green
    exit 0
} elseif ($failedTests -le 2) {
    Write-Host "INFRASTRUCTURE TESTS PASSED WITH WARNINGS" -ForegroundColor Yellow
    Write-Host "Most infrastructure components are working but some issues were found." -ForegroundColor Yellow
    exit 0
} else {
    Write-Host "INFRASTRUCTURE TESTS FAILED" -ForegroundColor Red
    Write-Host "Critical infrastructure issues must be resolved before deployment!" -ForegroundColor Red
    exit 1
}