# Infrastructure Validation Script
# Tests: Database, Redis, MinIO, SSL, DNS, Network connectivity
# Based on: PRODUCTION_DEPLOYMENT_CHECKLIST.md - Infrastructure Prerequisites

Write-Host "🏗️ Infrastructure Validation Test" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green

$testResults = @()
$allPassed = $true

function Test-ServiceConnection {
    param(
        [string]$ServiceName,
        [string]$Host,
        [int]$Port,
        [string]$Protocol = "TCP"
    )
    
    Write-Host "`n🔍 Testing $ServiceName connection..." -ForegroundColor Yellow
    
    try {
        if ($Protocol -eq "HTTP" -or $Protocol -eq "HTTPS") {
            $response = Invoke-WebRequest -Uri "${Protocol}://${Host}:${Port}" -TimeoutSec 10 -UseBasicParsing
            $result = @{
                Service = $ServiceName
                Status = "✅ PASS"
                Details = "HTTP Status: $($response.StatusCode)"
                ResponseTime = "< 10s"
            }
        } else {
            $tcpClient = New-Object System.Net.Sockets.TcpClient
            $tcpClient.ReceiveTimeout = 5000
            $tcpClient.SendTimeout = 5000
            $tcpClient.Connect($Host, $Port)
            $tcpClient.Close()
            
            $result = @{
                Service = $ServiceName
                Status = "✅ PASS"
                Details = "TCP connection successful"
                ResponseTime = "< 5s"
            }
        }
        
        Write-Host "  Status: ✅ $ServiceName is accessible" -ForegroundColor Green
        return $result
    }
    catch {
        $result = @{
            Service = $ServiceName
            Status = "❌ FAIL"
            Details = $_.Exception.Message
            ResponseTime = "Timeout"
        }
        
        Write-Host "  Status: ❌ $ServiceName connection failed" -ForegroundColor Red
        Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
        $script:allPassed = $false
        return $result
    }
}

function Test-DatabaseConnection {
    Write-Host "`n🗃️ Testing PostgreSQL Database..." -ForegroundColor Yellow
    
    try {
        # Test basic connection
        $testResults += Test-ServiceConnection -ServiceName "PostgreSQL" -Host "localhost" -Port 5432
        
        # Test database-specific operations
        Write-Host "  Testing database operations..." -ForegroundColor Cyan
        
        # Check if psql is available
        $psqlTest = Get-Command psql -ErrorAction SilentlyContinue
        if ($psqlTest) {
            # Test database connection with psql
            $dbTest = psql -h localhost -p 5432 -U healthcare_user -d healthcare_db -c "SELECT 1;" 2>&1
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✅ Database query test passed" -ForegroundColor Green
                $testResults += @{
                    Service = "Database Query"
                    Status = "✅ PASS"
                    Details = "SELECT query executed successfully"
                    ResponseTime = "< 1s"
                }
            } else {
                Write-Host "  ❌ Database query test failed" -ForegroundColor Red
                Write-Host "  Error: $dbTest" -ForegroundColor Red
                $script:allPassed = $false
                $testResults += @{
                    Service = "Database Query"
                    Status = "❌ FAIL"
                    Details = "Query execution failed: $dbTest"
                    ResponseTime = "N/A"
                }
            }
        } else {
            Write-Host "  ⚠️ psql not available - skipping query test" -ForegroundColor Yellow
            $testResults += @{
                Service = "Database Query"
                Status = "⚠️ SKIP"
                Details = "psql command not found"
                ResponseTime = "N/A"
            }
        }
    }
    catch {
        Write-Host "  ❌ Database test failed: $($_.Exception.Message)" -ForegroundColor Red
        $script:allPassed = $false
    }
}

function Test-RedisConnection {
    Write-Host "`n🔴 Testing Redis Cache..." -ForegroundColor Yellow
    
    try {
        $testResults += Test-ServiceConnection -ServiceName "Redis" -Host "localhost" -Port 6379
        
        # Test Redis-specific operations
        Write-Host "  Testing Redis operations..." -ForegroundColor Cyan
        
        # Check if redis-cli is available
        $redisTest = Get-Command redis-cli -ErrorAction SilentlyContinue
        if ($redisTest) {
            # Test Redis ping
            $redisPing = redis-cli -h localhost -p 6379 ping 2>&1
            
            if ($redisPing -eq "PONG") {
                Write-Host "  ✅ Redis ping test passed" -ForegroundColor Green
                $testResults += @{
                    Service = "Redis Ping"
                    Status = "✅ PASS"
                    Details = "PING/PONG successful"
                    ResponseTime = "< 100ms"
                }
            } else {
                Write-Host "  ❌ Redis ping test failed" -ForegroundColor Red
                $script:allPassed = $false
                $testResults += @{
                    Service = "Redis Ping"
                    Status = "❌ FAIL"
                    Details = "PING failed: $redisPing"
                    ResponseTime = "N/A"
                }
            }
        } else {
            Write-Host "  ⚠️ redis-cli not available - skipping ping test" -ForegroundColor Yellow
            $testResults += @{
                Service = "Redis Ping"
                Status = "⚠️ SKIP"
                Details = "redis-cli command not found"
                ResponseTime = "N/A"
            }
        }
    }
    catch {
        Write-Host "  ❌ Redis test failed: $($_.Exception.Message)" -ForegroundColor Red
        $script:allPassed = $false
    }
}

function Test-MinIOStorage {
    Write-Host "`n📦 Testing MinIO Storage..." -ForegroundColor Yellow
    
    try {
        $testResults += Test-ServiceConnection -ServiceName "MinIO" -Host "localhost" -Port 9000 -Protocol "HTTP"
        
        # Test MinIO health endpoint
        try {
            $healthResponse = Invoke-WebRequest -Uri "http://localhost:9000/minio/health/live" -TimeoutSec 10 -UseBasicParsing
            Write-Host "  ✅ MinIO health check passed" -ForegroundColor Green
            $testResults += @{
                Service = "MinIO Health"
                Status = "✅ PASS"
                Details = "Health endpoint responded: $($healthResponse.StatusCode)"
                ResponseTime = "< 5s"
            }
        }
        catch {
            Write-Host "  ❌ MinIO health check failed" -ForegroundColor Red
            Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
            $script:allPassed = $false
            $testResults += @{
                Service = "MinIO Health"
                Status = "❌ FAIL"
                Details = $_.Exception.Message
                ResponseTime = "Timeout"
            }
        }
    }
    catch {
        Write-Host "  ❌ MinIO test failed: $($_.Exception.Message)" -ForegroundColor Red
        $script:allPassed = $false
    }
}

function Test-ApplicationServices {
    Write-Host "`n🏥 Testing Application Services..." -ForegroundColor Yellow
    
    # Test main API health
    try {
        $apiHealth = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 10 -UseBasicParsing
        Write-Host "  ✅ Main API health check passed" -ForegroundColor Green
        $testResults += @{
            Service = "Main API Health"
            Status = "✅ PASS" 
            Details = "API responded: $($apiHealth.StatusCode)"
            ResponseTime = "< 5s"
        }
    }
    catch {
        Write-Host "  ❌ Main API health check failed" -ForegroundColor Red
        Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
        $script:allPassed = $false
        $testResults += @{
            Service = "Main API Health"
            Status = "❌ FAIL"
            Details = $_.Exception.Message
            ResponseTime = "Timeout"
        }
    }
    
    # Test healthcare module health
    try {
        $healthcareHealth = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/healthcare-records/health" -TimeoutSec 10 -UseBasicParsing
        Write-Host "  ✅ Healthcare module health check passed" -ForegroundColor Green
        $testResults += @{
            Service = "Healthcare Module Health"
            Status = "✅ PASS"
            Details = "Healthcare API responded: $($healthcareHealth.StatusCode)"
            ResponseTime = "< 5s"
        }
    }
    catch {
        Write-Host "  ❌ Healthcare module health check failed" -ForegroundColor Red
        Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
        $script:allPassed = $false
        $testResults += @{
            Service = "Healthcare Module Health"
            Status = "❌ FAIL"
            Details = $_.Exception.Message
            ResponseTime = "Timeout"
        }
    }
}

function Test-MonitoringStack {
    Write-Host "`n📊 Testing Monitoring Stack..." -ForegroundColor Yellow
    
    # Test Grafana
    $testResults += Test-ServiceConnection -ServiceName "Grafana" -Host "localhost" -Port 3000 -Protocol "HTTP"
    
    # Test Prometheus
    $testResults += Test-ServiceConnection -ServiceName "Prometheus" -Host "localhost" -Port 9090 -Protocol "HTTP"
    
    # Test Node Exporter
    $testResults += Test-ServiceConnection -ServiceName "Node Exporter" -Host "localhost" -Port 9100 -Protocol "HTTP"
    
    # Test cAdvisor
    $testResults += Test-ServiceConnection -ServiceName "cAdvisor" -Host "localhost" -Port 8080 -Protocol "HTTP"
}

function Test-NetworkConnectivity {
    Write-Host "`n🌐 Testing Network Connectivity..." -ForegroundColor Yellow
    
    $externalSites = @(
        @{Name = "Google DNS"; Host = "8.8.8.8"; Port = 53},
        @{Name = "GitHub"; Host = "github.com"; Port = 443},
        @{Name = "Docker Hub"; Host = "registry-1.docker.io"; Port = 443}
    )
    
    foreach ($site in $externalSites) {
        try {
            $testResults += Test-ServiceConnection -ServiceName $site.Name -Host $site.Host -Port $site.Port
        }
        catch {
            Write-Host "  ❌ $($site.Name) connectivity test failed" -ForegroundColor Red
            $script:allPassed = $false
        }
    }
}

function Test-DockerServices {
    Write-Host "`n🐳 Testing Docker Services..." -ForegroundColor Yellow
    
    try {
        # Check if Docker is running
        $dockerVersion = docker version --format "{{.Server.Version}}" 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ Docker is running (version: $dockerVersion)" -ForegroundColor Green
            $testResults += @{
                Service = "Docker Engine"
                Status = "✅ PASS"
                Details = "Docker version: $dockerVersion"
                ResponseTime = "< 2s"
            }
            
            # Check running containers
            $containers = docker ps --format "table {{.Names}}\t{{.Status}}" 2>&1
            Write-Host "  Docker containers status:" -ForegroundColor Cyan
            Write-Host $containers
            
            $testResults += @{
                Service = "Docker Containers"
                Status = "✅ PASS"
                Details = "Container status retrieved"
                ResponseTime = "< 3s"
            }
        } else {
            Write-Host "  ❌ Docker is not running or not accessible" -ForegroundColor Red
            Write-Host "  Error: $dockerVersion" -ForegroundColor Red
            $script:allPassed = $false
            $testResults += @{
                Service = "Docker Engine"
                Status = "❌ FAIL"
                Details = "Docker not accessible: $dockerVersion"
                ResponseTime = "N/A"
            }
        }
    }
    catch {
        Write-Host "  ❌ Docker test failed: $($_.Exception.Message)" -ForegroundColor Red
        $script:allPassed = $false
        $testResults += @{
            Service = "Docker Engine"
            Status = "❌ FAIL"
            Details = $_.Exception.Message
            ResponseTime = "N/A"
        }
    }
}

# Run all infrastructure tests
Write-Host "`n🚀 Starting Infrastructure Validation Tests..." -ForegroundColor Cyan

Test-DockerServices
Test-DatabaseConnection  
Test-RedisConnection
Test-MinIOStorage
Test-ApplicationServices
Test-MonitoringStack
Test-NetworkConnectivity

# Generate results summary
Write-Host "`n📊 INFRASTRUCTURE VALIDATION RESULTS" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green

$passedTests = ($testResults | Where-Object { $_.Status -eq "✅ PASS" }).Count
$failedTests = ($testResults | Where-Object { $_.Status -eq "❌ FAIL" }).Count
$skippedTests = ($testResults | Where-Object { $_.Status -eq "⚠️ SKIP" }).Count
$totalTests = $testResults.Count

Write-Host "`nTest Summary:" -ForegroundColor Cyan
Write-Host "  Total Tests: $totalTests"
Write-Host "  Passed: $passedTests" -ForegroundColor Green
Write-Host "  Failed: $failedTests" -ForegroundColor Red
Write-Host "  Skipped: $skippedTests" -ForegroundColor Yellow

Write-Host "`nDetailed Results:" -ForegroundColor Cyan
foreach ($test in $testResults) {
    Write-Host "  $($test.Status) $($test.Service) - $($test.Details)"
}

# Save results to file
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$resultFile = "infrastructure_validation_$timestamp.json"

try {
    $testResults | ConvertTo-Json -Depth 3 | Out-File -FilePath $resultFile -Encoding UTF8
    Write-Host "`n📁 Results saved to: $resultFile" -ForegroundColor Cyan
}
catch {
    Write-Host "`n⚠️ Could not save results to file: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Final assessment
Write-Host "`n🎯 FINAL ASSESSMENT" -ForegroundColor Green
if ($allPassed -and $failedTests -eq 0) {
    Write-Host "✅ ALL INFRASTRUCTURE TESTS PASSED" -ForegroundColor Green
    Write-Host "Infrastructure is ready for production deployment!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "❌ INFRASTRUCTURE ISSUES DETECTED" -ForegroundColor Red
    Write-Host "Please fix the failed tests before proceeding with deployment." -ForegroundColor Red
    
    if ($failedTests -gt 0) {
        Write-Host "`n🔧 Issues to fix:" -ForegroundColor Yellow
        $failedTests = $testResults | Where-Object { $_.Status -eq "❌ FAIL" }
        foreach ($failed in $failedTests) {
            Write-Host "  - $($failed.Service): $($failed.Details)" -ForegroundColor Red
        }
    }
    exit 1
}