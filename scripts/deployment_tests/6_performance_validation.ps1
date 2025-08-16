# Performance Validation Script
# Tests: Load testing, response times, throughput, resource usage, scalability
# Based on: PRODUCTION_DEPLOYMENT_CHECKLIST.md - Performance Validation

Write-Host "⚡ Performance Validation Test" -ForegroundColor Green
Write-Host "=============================" -ForegroundColor Green

$testResults = @()
$allPassed = $true
$performanceIssues = @()

function Test-APIResponseTimes {
    Write-Host "`n⏱️ Testing API Response Times..." -ForegroundColor Yellow
    
    # Define endpoints to test
    $endpoints = @(
        @{Name = "Health Check"; URL = "http://localhost:8000/health"; MaxResponseTime = 100},
        @{Name = "Healthcare Health"; URL = "http://localhost:8000/api/v1/healthcare-records/health"; MaxResponseTime = 200},
        @{Name = "API Docs"; URL = "http://localhost:8000/docs"; MaxResponseTime = 1000}
    )
    
    foreach ($endpoint in $endpoints) {
        Write-Host "  Testing $($endpoint.Name)..." -ForegroundColor Cyan
        
        $responseTimes = @()
        $successCount = 0
        $totalRequests = 10
        
        for ($i = 1; $i -le $totalRequests; $i++) {
            try {
                $startTime = Get-Date
                $response = Invoke-WebRequest -Uri $endpoint.URL -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
                $endTime = Get-Date
                
                $responseTime = ($endTime - $startTime).TotalMilliseconds
                $responseTimes += $responseTime
                
                if ($response.StatusCode -eq 200) {
                    $successCount++
                }
                
                # Show progress for longer tests
                if ($i % 5 -eq 0) {
                    Write-Host "    Progress: $i/$totalRequests requests completed..." -ForegroundColor Gray
                }
            }
            catch {
                Write-Host "    ❌ Request $i failed: $($_.Exception.Message)" -ForegroundColor Red
            }
        }
        
        if ($responseTimes.Count -gt 0) {
            $avgResponseTime = ($responseTimes | Measure-Object -Average).Average
            $minResponseTime = ($responseTimes | Measure-Object -Minimum).Minimum
            $maxResponseTime = ($responseTimes | Measure-Object -Maximum).Maximum
            $p95ResponseTime = if ($responseTimes.Count -ge 5) { 
                ($responseTimes | Sort-Object)[[math]::Floor($responseTimes.Count * 0.95)] 
            } else { 
                $maxResponseTime 
            }
            
            $successRate = ($successCount / $totalRequests) * 100
            
            Write-Host "    📊 Results for $($endpoint.Name):" -ForegroundColor Cyan
            Write-Host "      Average: $([math]::Round($avgResponseTime, 2))ms" -ForegroundColor White
            Write-Host "      Min: $([math]::Round($minResponseTime, 2))ms" -ForegroundColor White
            Write-Host "      Max: $([math]::Round($maxResponseTime, 2))ms" -ForegroundColor White
            Write-Host "      95th percentile: $([math]::Round($p95ResponseTime, 2))ms" -ForegroundColor White
            Write-Host "      Success rate: $([math]::Round($successRate, 1))%" -ForegroundColor White
            
            # Evaluate performance
            if ($avgResponseTime -le $endpoint.MaxResponseTime -and $successRate -ge 95) {
                Write-Host "    ✅ Performance meets requirements" -ForegroundColor Green
                $testResults += @{
                    Test = "API_RESPONSE_$($endpoint.Name.Replace(' ', '_').ToUpper())"
                    Status = "✅ PASS"
                    Description = "API response time: $($endpoint.Name)"
                    Details = "Avg: $([math]::Round($avgResponseTime, 2))ms, Success: $([math]::Round($successRate, 1))%"
                    Category = "Performance"
                    Severity = "INFO"
                    ResponseTime = $avgResponseTime
                    SuccessRate = $successRate
                }
            } elseif ($avgResponseTime -le ($endpoint.MaxResponseTime * 1.5) -and $successRate -ge 90) {
                Write-Host "    ⚠️ Performance acceptable but could be better" -ForegroundColor Yellow
                $script:performanceIssues += "$($endpoint.Name) response time is higher than optimal"
                $testResults += @{
                    Test = "API_RESPONSE_$($endpoint.Name.Replace(' ', '_').ToUpper())"
                    Status = "⚠️ SLOW"
                    Description = "API response time: $($endpoint.Name)"
                    Details = "Avg: $([math]::Round($avgResponseTime, 2))ms (target: $($endpoint.MaxResponseTime)ms)"
                    Category = "Performance"
                    Severity = "MEDIUM"
                    ResponseTime = $avgResponseTime
                    SuccessRate = $successRate
                }
            } else {
                Write-Host "    ❌ Performance does not meet requirements" -ForegroundColor Red
                $script:allPassed = $false
                $script:performanceIssues += "$($endpoint.Name) performance is unacceptable"
                $testResults += @{
                    Test = "API_RESPONSE_$($endpoint.Name.Replace(' ', '_').ToUpper())"
                    Status = "❌ FAIL"
                    Description = "API response time: $($endpoint.Name)"
                    Details = "Avg: $([math]::Round($avgResponseTime, 2))ms, Success: $([math]::Round($successRate, 1))%"
                    Category = "Performance"
                    Severity = "HIGH"
                    ResponseTime = $avgResponseTime
                    SuccessRate = $successRate
                }
            }
        } else {
            Write-Host "    ❌ No successful responses received" -ForegroundColor Red
            $script:allPassed = $false
            $script:performanceIssues += "$($endpoint.Name) is not responding"
            $testResults += @{
                Test = "API_RESPONSE_$($endpoint.Name.Replace(' ', '_').ToUpper())"
                Status = "❌ FAIL"
                Description = "API response time: $($endpoint.Name)"
                Details = "No successful responses"
                Category = "Performance"
                Severity = "CRITICAL"
                ResponseTime = 0
                SuccessRate = 0
            }
        }
    }
}

function Test-ConcurrentLoad {
    Write-Host "`n🚀 Testing Concurrent Load..." -ForegroundColor Yellow
    
    $testConfigs = @(
        @{Name = "Light Load"; Users = 5; Requests = 3; MaxFailureRate = 5},
        @{Name = "Medium Load"; Users = 10; Requests = 5; MaxFailureRate = 10},
        @{Name = "Heavy Load"; Users = 20; Requests = 3; MaxFailureRate = 15}
    )
    
    foreach ($config in $testConfigs) {
        Write-Host "  Running $($config.Name) test ($($config.Users) users, $($config.Requests) requests each)..." -ForegroundColor Cyan
        
        $allResults = @()
        $startTime = Get-Date
        
        # Create runspace pool for concurrent execution
        $runspacePool = [runspacefactory]::CreateRunspacePool(1, $config.Users)
        $runspacePool.Open()
        
        $jobs = @()
        
        # Create jobs for each user
        for ($user = 1; $user -le $config.Users; $user++) {
            $powerShell = [powershell]::Create()
            $powerShell.RunspacePool = $runspacePool
            
            $scriptBlock = {
                param($userId, $requests, $baseUrl)
                
                $userResults = @()
                for ($req = 1; $req -le $requests; $req++) {
                    try {
                        $requestStart = Get-Date
                        $response = Invoke-WebRequest -Uri "$baseUrl/health" -TimeoutSec 10 -UseBasicParsing
                        $requestEnd = Get-Date
                        
                        $userResults += @{
                            UserId = $userId
                            RequestId = $req
                            ResponseTime = ($requestEnd - $requestStart).TotalMilliseconds
                            StatusCode = $response.StatusCode
                            Success = ($response.StatusCode -eq 200)
                        }
                    }
                    catch {
                        $userResults += @{
                            UserId = $userId
                            RequestId = $req
                            ResponseTime = 0
                            StatusCode = 0
                            Success = $false
                            Error = $_.Exception.Message
                        }
                    }
                }
                return $userResults
            }
            
            $null = $powerShell.AddScript($scriptBlock).AddParameter("userId", $user).AddParameter("requests", $config.Requests).AddParameter("baseUrl", "http://localhost:8000")
            
            $jobs += @{
                PowerShell = $powerShell
                Handle = $powerShell.BeginInvoke()
            }
        }
        
        # Wait for all jobs to complete
        Write-Host "    Waiting for concurrent requests to complete..." -ForegroundColor Gray
        
        foreach ($job in $jobs) {
            try {
                $results = $job.PowerShell.EndInvoke($job.Handle)
                $allResults += $results
                $job.PowerShell.Dispose()
            }
            catch {
                Write-Host "    ⚠️ Job completion error: $($_.Exception.Message)" -ForegroundColor Yellow
            }
        }
        
        $runspacePool.Close()
        $runspacePool.Dispose()
        
        $endTime = Get-Date
        $totalDuration = ($endTime - $startTime).TotalSeconds
        
        # Analyze results
        if ($allResults.Count -gt 0) {
            $successfulRequests = $allResults | Where-Object { $_.Success -eq $true }
            $failedRequests = $allResults | Where-Object { $_.Success -eq $false }
            
            $totalRequests = $allResults.Count
            $successCount = $successfulRequests.Count
            $failureRate = (($totalRequests - $successCount) / $totalRequests) * 100
            $throughput = $successCount / $totalDuration
            
            if ($successfulRequests.Count -gt 0) {
                $avgResponseTime = ($successfulRequests.ResponseTime | Measure-Object -Average).Average
                $minResponseTime = ($successfulRequests.ResponseTime | Measure-Object -Minimum).Minimum
                $maxResponseTime = ($successfulRequests.ResponseTime | Measure-Object -Maximum).Maximum
            } else {
                $avgResponseTime = 0
                $minResponseTime = 0
                $maxResponseTime = 0
            }
            
            Write-Host "    📊 $($config.Name) Results:" -ForegroundColor Cyan
            Write-Host "      Total requests: $totalRequests" -ForegroundColor White
            Write-Host "      Successful requests: $successCount" -ForegroundColor White
            Write-Host "      Failure rate: $([math]::Round($failureRate, 2))%" -ForegroundColor White
            Write-Host "      Throughput: $([math]::Round($throughput, 2)) req/s" -ForegroundColor White
            Write-Host "      Average response time: $([math]::Round($avgResponseTime, 2))ms" -ForegroundColor White
            Write-Host "      Total duration: $([math]::Round($totalDuration, 2))s" -ForegroundColor White
            
            # Evaluate performance
            if ($failureRate -le $config.MaxFailureRate -and $avgResponseTime -le 500) {
                Write-Host "    ✅ $($config.Name) performance acceptable" -ForegroundColor Green
                $testResults += @{
                    Test = "CONCURRENT_LOAD_$($config.Name.Replace(' ', '_').ToUpper())"
                    Status = "✅ PASS"
                    Description = "Concurrent load test: $($config.Name)"
                    Details = "Failure rate: $([math]::Round($failureRate, 2))%, Throughput: $([math]::Round($throughput, 2)) req/s"
                    Category = "Concurrency"
                    Severity = "INFO"
                    FailureRate = $failureRate
                    Throughput = $throughput
                }
            } elseif ($failureRate -le ($config.MaxFailureRate * 1.5) -and $avgResponseTime -le 1000) {
                Write-Host "    ⚠️ $($config.Name) performance needs improvement" -ForegroundColor Yellow
                $script:performanceIssues += "$($config.Name) has higher than optimal failure rate or response time"
                $testResults += @{
                    Test = "CONCURRENT_LOAD_$($config.Name.Replace(' ', '_').ToUpper())"
                    Status = "⚠️ SLOW"
                    Description = "Concurrent load test: $($config.Name)"
                    Details = "Failure rate: $([math]::Round($failureRate, 2))%, Avg response: $([math]::Round($avgResponseTime, 2))ms"
                    Category = "Concurrency"
                    Severity = "MEDIUM"
                    FailureRate = $failureRate
                    Throughput = $throughput
                }
            } else {
                Write-Host "    ❌ $($config.Name) performance unacceptable" -ForegroundColor Red
                $script:allPassed = $false
                $script:performanceIssues += "$($config.Name) failed performance requirements"
                $testResults += @{
                    Test = "CONCURRENT_LOAD_$($config.Name.Replace(' ', '_').ToUpper())"
                    Status = "❌ FAIL"
                    Description = "Concurrent load test: $($config.Name)"
                    Details = "Failure rate: $([math]::Round($failureRate, 2))%, Avg response: $([math]::Round($avgResponseTime, 2))ms"
                    Category = "Concurrency"
                    Severity = "HIGH"
                    FailureRate = $failureRate
                    Throughput = $throughput
                }
            }
        } else {
            Write-Host "    ❌ No results received from $($config.Name)" -ForegroundColor Red
            $script:allPassed = $false
            $script:performanceIssues += "$($config.Name) test failed completely"
            $testResults += @{
                Test = "CONCURRENT_LOAD_$($config.Name.Replace(' ', '_').ToUpper())"
                Status = "❌ FAIL"
                Description = "Concurrent load test: $($config.Name)"
                Details = "No successful requests"
                Category = "Concurrency"
                Severity = "CRITICAL"
                FailureRate = 100
                Throughput = 0
            }
        }
    }
}

function Test-SustainedLoad {
    Write-Host "`n⏳ Testing Sustained Load..." -ForegroundColor Yellow
    
    $testDuration = 30  # seconds
    $requestsPerSecond = 5
    $maxErrorRate = 10  # percent
    
    Write-Host "  Running sustained load test ($testDuration seconds at $requestsPerSecond req/s)..." -ForegroundColor Cyan
    
    $allResults = @()
    $startTime = Get-Date
    $requestId = 0
    
    while ((Get-Date) - $startTime).TotalSeconds -lt $testDuration) {
        $batchStart = Get-Date
        
        # Send requests for this second
        for ($i = 0; $i -lt $requestsPerSecond; $i++) {
            $requestId++
            
            try {
                $reqStart = Get-Date
                $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -UseBasicParsing
                $reqEnd = Get-Date
                
                $allResults += @{
                    RequestId = $requestId
                    Timestamp = $reqStart
                    ResponseTime = ($reqEnd - $reqStart).TotalMilliseconds
                    StatusCode = $response.StatusCode
                    Success = ($response.StatusCode -eq 200)
                }
            }
            catch {
                $allResults += @{
                    RequestId = $requestId
                    Timestamp = (Get-Date)
                    ResponseTime = 0
                    StatusCode = 0
                    Success = $false
                    Error = $_.Exception.Message
                }
            }
        }
        
        # Wait for the remainder of the second
        $batchDuration = ((Get-Date) - $batchStart).TotalMilliseconds
        if ($batchDuration -lt 1000) {
            Start-Sleep -Milliseconds (1000 - $batchDuration)
        }
        
        # Show progress every 10 seconds
        $elapsed = [math]::Floor(((Get-Date) - $startTime).TotalSeconds)
        if ($elapsed % 10 -eq 0 -and $elapsed -gt 0) {
            Write-Host "    Progress: $elapsed/$testDuration seconds, $($allResults.Count) requests sent..." -ForegroundColor Gray
        }
    }
    
    $totalDuration = ((Get-Date) - $startTime).TotalSeconds
    
    # Analyze sustained load results
    if ($allResults.Count -gt 0) {
        $successfulRequests = $allResults | Where-Object { $_.Success -eq $true }
        $failedRequests = $allResults | Where-Object { $_.Success -eq $false }
        
        $totalRequests = $allResults.Count
        $successCount = $successfulRequests.Count
        $errorRate = (($totalRequests - $successCount) / $totalRequests) * 100
        $actualThroughput = $successCount / $totalDuration
        $targetThroughput = $requestsPerSecond
        
        if ($successfulRequests.Count -gt 0) {
            $avgResponseTime = ($successfulRequests.ResponseTime | Measure-Object -Average).Average
            $minResponseTime = ($successfulRequests.ResponseTime | Measure-Object -Minimum).Minimum
            $maxResponseTime = ($successfulRequests.ResponseTime | Measure-Object -Maximum).Maximum
        } else {
            $avgResponseTime = 0
            $minResponseTime = 0
            $maxResponseTime = 0
        }
        
        Write-Host "    📊 Sustained Load Results:" -ForegroundColor Cyan
        Write-Host "      Total requests: $totalRequests" -ForegroundColor White
        Write-Host "      Successful requests: $successCount" -ForegroundColor White
        Write-Host "      Error rate: $([math]::Round($errorRate, 2))%" -ForegroundColor White
        Write-Host "      Target throughput: $targetThroughput req/s" -ForegroundColor White
        Write-Host "      Actual throughput: $([math]::Round($actualThroughput, 2)) req/s" -ForegroundColor White
        Write-Host "      Average response time: $([math]::Round($avgResponseTime, 2))ms" -ForegroundColor White
        Write-Host "      Max response time: $([math]::Round($maxResponseTime, 2))ms" -ForegroundColor White
        Write-Host "      Test duration: $([math]::Round($totalDuration, 2))s" -ForegroundColor White
        
        # Performance evaluation
        $throughputRatio = $actualThroughput / $targetThroughput
        
        if ($errorRate -le $maxErrorRate -and $throughputRatio -ge 0.9 -and $avgResponseTime -le 300) {
            Write-Host "    ✅ Sustained load performance excellent" -ForegroundColor Green
            $testResults += @{
                Test = "SUSTAINED_LOAD"
                Status = "✅ EXCELLENT"
                Description = "Sustained load test"
                Details = "Error rate: $([math]::Round($errorRate, 2))%, Actual throughput: $([math]::Round($actualThroughput, 2)) req/s"
                Category = "Endurance"
                Severity = "INFO"
                ErrorRate = $errorRate
                ActualThroughput = $actualThroughput
                TargetThroughput = $targetThroughput
            }
        } elseif ($errorRate -le ($maxErrorRate * 1.5) -and $throughputRatio -ge 0.7 -and $avgResponseTime -le 500) {
            Write-Host "    ⚠️ Sustained load performance acceptable" -ForegroundColor Yellow
            $script:performanceIssues += "Sustained load performance could be improved"
            $testResults += @{
                Test = "SUSTAINED_LOAD"
                Status = "⚠️ ACCEPTABLE"
                Description = "Sustained load test"
                Details = "Error rate: $([math]::Round($errorRate, 2))%, Throughput ratio: $([math]::Round($throughputRatio, 2))"
                Category = "Endurance"
                Severity = "MEDIUM"
                ErrorRate = $errorRate
                ActualThroughput = $actualThroughput
                TargetThroughput = $targetThroughput
            }
        } else {
            Write-Host "    ❌ Sustained load performance unacceptable" -ForegroundColor Red
            $script:allPassed = $false
            $script:performanceIssues += "Sustained load performance fails requirements"
            $testResults += @{
                Test = "SUSTAINED_LOAD"
                Status = "❌ POOR"
                Description = "Sustained load test"
                Details = "Error rate: $([math]::Round($errorRate, 2))%, Avg response: $([math]::Round($avgResponseTime, 2))ms"
                Category = "Endurance"
                Severity = "HIGH"
                ErrorRate = $errorRate
                ActualThroughput = $actualThroughput
                TargetThroughput = $targetThroughput
            }
        }
        
        # Check for performance degradation over time
        if ($successfulRequests.Count -ge 10) {
            $firstHalf = $successfulRequests | Select-Object -First ([math]::Floor($successfulRequests.Count / 2))
            $secondHalf = $successfulRequests | Select-Object -Last ([math]::Floor($successfulRequests.Count / 2))
            
            $firstHalfAvg = ($firstHalf.ResponseTime | Measure-Object -Average).Average
            $secondHalfAvg = ($secondHalf.ResponseTime | Measure-Object -Average).Average
            
            $degradationPercent = (($secondHalfAvg - $firstHalfAvg) / $firstHalfAvg) * 100
            
            if ($degradationPercent -le 20) {
                Write-Host "    ✅ No significant performance degradation detected" -ForegroundColor Green
                $testResults += @{
                    Test = "PERFORMANCE_STABILITY"
                    Status = "✅ STABLE"
                    Description = "Performance stability over time"
                    Details = "Degradation: $([math]::Round($degradationPercent, 2))%"
                    Category = "Stability"
                    Severity = "INFO"
                }
            } else {
                Write-Host "    ⚠️ Performance degradation detected: $([math]::Round($degradationPercent, 2))%" -ForegroundColor Yellow
                $script:performanceIssues += "Performance degrades over time under sustained load"
                $testResults += @{
                    Test = "PERFORMANCE_STABILITY"
                    Status = "⚠️ DEGRADING"
                    Description = "Performance stability over time"
                    Details = "Degradation: $([math]::Round($degradationPercent, 2))%"
                    Category = "Stability"
                    Severity = "MEDIUM"
                }
            }
        }
    } else {
        Write-Host "    ❌ No results from sustained load test" -ForegroundColor Red
        $script:allPassed = $false
        $script:performanceIssues += "Sustained load test failed completely"
        $testResults += @{
            Test = "SUSTAINED_LOAD"
            Status = "❌ FAIL"
            Description = "Sustained load test"
            Details = "No successful requests"
            Category = "Endurance"
            Severity = "CRITICAL"
        }
    }
}

function Test-ResourceUsage {
    Write-Host "`n💻 Testing Resource Usage..." -ForegroundColor Yellow
    
    Write-Host "  Monitoring system resources during load..." -ForegroundColor Cyan
    
    # Get baseline resource usage
    try {
        $initialMemory = (Get-Process | Measure-Object WorkingSet -Sum).Sum / 1MB
        Write-Host "    📊 Initial memory usage: $([math]::Round($initialMemory, 2)) MB" -ForegroundColor White
        
        # Monitor resources during a brief load test
        $resourceSamples = @()
        $monitoringDuration = 20  # seconds
        $startTime = Get-Date
        
        # Start a light load in background
        $loadJob = Start-Job -ScriptBlock {
            for ($i = 1; $i -le 50; $i++) {
                try {
                    Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -UseBasicParsing | Out-Null
                    Start-Sleep -Milliseconds 100
                }
                catch {
                    # Ignore errors in background load
                }
            }
        }
        
        # Sample resources every 2 seconds
        while ((Get-Date) - $startTime).TotalSeconds -lt $monitoringDuration) {
            try {
                $sample = @{
                    Timestamp = Get-Date
                    TotalMemoryMB = (Get-Process | Measure-Object WorkingSet -Sum).Sum / 1MB
                    ProcessCount = (Get-Process).Count
                }
                
                # Try to get CPU usage (may not be available in all environments)
                try {
                    $cpuCounter = Get-Counter "\Processor(_Total)\% Processor Time" -ErrorAction SilentlyContinue
                    if ($cpuCounter) {
                        $sample.CPUPercent = $cpuCounter.CounterSamples[0].CookedValue
                    }
                }
                catch {
                    # CPU monitoring not available
                }
                
                $resourceSamples += $sample
                Start-Sleep -Seconds 2
            }
            catch {
                Write-Host "    ⚠️ Resource sampling error: $($_.Exception.Message)" -ForegroundColor Yellow
            }
        }
        
        # Wait for load job to complete
        $loadJob | Wait-Job -Timeout 30 | Out-Null
        $loadJob | Remove-Job -Force
        
        # Analyze resource usage
        if ($resourceSamples.Count -ge 3) {
            $finalMemory = ($resourceSamples | Select-Object -Last 1).TotalMemoryMB
            $maxMemory = ($resourceSamples.TotalMemoryMB | Measure-Object -Maximum).Maximum
            $avgMemory = ($resourceSamples.TotalMemoryMB | Measure-Object -Average).Average
            $memoryIncrease = $maxMemory - $initialMemory
            
            Write-Host "    📊 Resource Usage Analysis:" -ForegroundColor Cyan
            Write-Host "      Initial memory: $([math]::Round($initialMemory, 2)) MB" -ForegroundColor White
            Write-Host "      Peak memory: $([math]::Round($maxMemory, 2)) MB" -ForegroundColor White
            Write-Host "      Average memory: $([math]::Round($avgMemory, 2)) MB" -ForegroundColor White
            Write-Host "      Memory increase: $([math]::Round($memoryIncrease, 2)) MB" -ForegroundColor White
            
            # CPU usage if available
            $cpuSamples = $resourceSamples | Where-Object { $_.CPUPercent -ne $null }
            if ($cpuSamples.Count -gt 0) {
                $avgCPU = ($cpuSamples.CPUPercent | Measure-Object -Average).Average
                $maxCPU = ($cpuSamples.CPUPercent | Measure-Object -Maximum).Maximum
                Write-Host "      Average CPU: $([math]::Round($avgCPU, 2))%" -ForegroundColor White
                Write-Host "      Peak CPU: $([math]::Round($maxCPU, 2))%" -ForegroundColor White
            }
            
            # Evaluate resource usage
            if ($memoryIncrease -le 100 -and ($cpuSamples.Count -eq 0 -or $avgCPU -le 50)) {
                Write-Host "    ✅ Resource usage is efficient" -ForegroundColor Green
                $testResults += @{
                    Test = "RESOURCE_USAGE"
                    Status = "✅ EFFICIENT"
                    Description = "System resource usage"
                    Details = "Memory increase: $([math]::Round($memoryIncrease, 2)) MB"
                    Category = "Resources"
                    Severity = "INFO"
                    MemoryIncrease = $memoryIncrease
                }
            } elseif ($memoryIncrease -le 200 -and ($cpuSamples.Count -eq 0 -or $avgCPU -le 80)) {
                Write-Host "    ⚠️ Resource usage is acceptable" -ForegroundColor Yellow
                $script:performanceIssues += "Resource usage could be more efficient"
                $testResults += @{
                    Test = "RESOURCE_USAGE"
                    Status = "⚠️ ACCEPTABLE"
                    Description = "System resource usage"
                    Details = "Memory increase: $([math]::Round($memoryIncrease, 2)) MB"
                    Category = "Resources"
                    Severity = "MEDIUM"
                    MemoryIncrease = $memoryIncrease
                }
            } else {
                Write-Host "    ❌ Resource usage is concerning" -ForegroundColor Red
                $script:performanceIssues += "High resource usage may impact performance"
                $testResults += @{
                    Test = "RESOURCE_USAGE"
                    Status = "❌ HIGH"
                    Description = "System resource usage"
                    Details = "Memory increase: $([math]::Round($memoryIncrease, 2)) MB"
                    Category = "Resources"
                    Severity = "HIGH"
                    MemoryIncrease = $memoryIncrease
                }
            }
            
            # Check for memory leaks
            $firstThird = $resourceSamples | Select-Object -First ([math]::Floor($resourceSamples.Count / 3))
            $lastThird = $resourceSamples | Select-Object -Last ([math]::Floor($resourceSamples.Count / 3))
            
            if ($firstThird.Count -gt 0 -and $lastThird.Count -gt 0) {
                $firstAvg = ($firstThird.TotalMemoryMB | Measure-Object -Average).Average
                $lastAvg = ($lastThird.TotalMemoryMB | Measure-Object -Average).Average
                $memoryTrend = $lastAvg - $firstAvg
                
                if ($memoryTrend -le 20) {
                    Write-Host "    ✅ No significant memory leak detected" -ForegroundColor Green
                    $testResults += @{
                        Test = "MEMORY_LEAK_CHECK"
                        Status = "✅ CLEAN"
                        Description = "Memory leak detection"
                        Details = "Memory trend: +$([math]::Round($memoryTrend, 2)) MB"
                        Category = "Stability"
                        Severity = "INFO"
                    }
                } else {
                    Write-Host "    ⚠️ Potential memory leak detected: +$([math]::Round($memoryTrend, 2)) MB" -ForegroundColor Yellow
                    $script:performanceIssues += "Potential memory leak detected"
                    $testResults += @{
                        Test = "MEMORY_LEAK_CHECK"
                        Status = "⚠️ LEAK"
                        Description = "Memory leak detection"
                        Details = "Memory trend: +$([math]::Round($memoryTrend, 2)) MB"
                        Category = "Stability"
                        Severity = "MEDIUM"
                    }
                }
            }
        } else {
            Write-Host "    ⚠️ Insufficient resource samples collected" -ForegroundColor Yellow
            $testResults += @{
                Test = "RESOURCE_USAGE"
                Status = "⚠️ INCOMPLETE"
                Description = "System resource usage"
                Details = "Insufficient monitoring data"
                Category = "Resources"
                Severity = "LOW"
            }
        }
    }
    catch {
        Write-Host "    ❌ Resource monitoring failed: $($_.Exception.Message)" -ForegroundColor Red
        $script:performanceIssues += "Cannot monitor system resources"
        $testResults += @{
            Test = "RESOURCE_USAGE"
            Status = "❌ FAIL"
            Description = "System resource usage"
            Details = $_.Exception.Message
            Category = "Resources"
            Severity = "MEDIUM"
        }
    }
}

function Test-DatabasePerformance {
    Write-Host "`n🗃️ Testing Database Performance..." -ForegroundColor Yellow
    
    # Test database connection response time
    $dbHost = [Environment]::GetEnvironmentVariable("DB_HOST") ?? "localhost"
    $dbPort = [Environment]::GetEnvironmentVariable("DB_PORT") ?? "5432"
    
    Write-Host "  Testing database connection performance..." -ForegroundColor Cyan
    
    $connectionTimes = @()
    for ($i = 1; $i -le 10; $i++) {
        try {
            $startTime = Get-Date
            $tcpClient = New-Object System.Net.Sockets.TcpClient
            $tcpClient.ReceiveTimeout = 5000
            $tcpClient.SendTimeout = 5000
            $tcpClient.Connect($dbHost, [int]$dbPort)
            $tcpClient.Close()
            $endTime = Get-Date
            
            $connectionTime = ($endTime - $startTime).TotalMilliseconds
            $connectionTimes += $connectionTime
        }
        catch {
            Write-Host "    ⚠️ Connection attempt $i failed" -ForegroundColor Yellow
        }
    }
    
    if ($connectionTimes.Count -gt 0) {
        $avgConnectionTime = ($connectionTimes | Measure-Object -Average).Average
        $maxConnectionTime = ($connectionTimes | Measure-Object -Maximum).Maximum
        
        Write-Host "    📊 Database Connection Performance:" -ForegroundColor Cyan
        Write-Host "      Average connection time: $([math]::Round($avgConnectionTime, 2))ms" -ForegroundColor White
        Write-Host "      Max connection time: $([math]::Round($maxConnectionTime, 2))ms" -ForegroundColor White
        Write-Host "      Successful connections: $($connectionTimes.Count)/10" -ForegroundColor White
        
        if ($avgConnectionTime -le 10 -and $connectionTimes.Count -ge 9) {
            Write-Host "    ✅ Database connection performance excellent" -ForegroundColor Green
            $testResults += @{
                Test = "DATABASE_CONNECTION_PERF"
                Status = "✅ EXCELLENT"
                Description = "Database connection performance"
                Details = "Avg: $([math]::Round($avgConnectionTime, 2))ms, Success: $($connectionTimes.Count)/10"
                Category = "Database"
                Severity = "INFO"
                AvgConnectionTime = $avgConnectionTime
            }
        } elseif ($avgConnectionTime -le 50 -and $connectionTimes.Count -ge 8) {
            Write-Host "    ⚠️ Database connection performance acceptable" -ForegroundColor Yellow
            $testResults += @{
                Test = "DATABASE_CONNECTION_PERF"
                Status = "⚠️ ACCEPTABLE"
                Description = "Database connection performance"
                Details = "Avg: $([math]::Round($avgConnectionTime, 2))ms, Success: $($connectionTimes.Count)/10"
                Category = "Database"
                Severity = "MEDIUM"
                AvgConnectionTime = $avgConnectionTime
            }
        } else {
            Write-Host "    ❌ Database connection performance poor" -ForegroundColor Red
            $script:allPassed = $false
            $script:performanceIssues += "Database connection performance is poor"
            $testResults += @{
                Test = "DATABASE_CONNECTION_PERF"
                Status = "❌ POOR"
                Description = "Database connection performance"
                Details = "Avg: $([math]::Round($avgConnectionTime, 2))ms, Success: $($connectionTimes.Count)/10"
                Category = "Database"
                Severity = "HIGH"
                AvgConnectionTime = $avgConnectionTime
            }
        }
    } else {
        Write-Host "    ❌ Cannot establish database connections" -ForegroundColor Red
        $script:allPassed = $false
        $script:performanceIssues += "Database is not accessible"
        $testResults += @{
            Test = "DATABASE_CONNECTION_PERF"
            Status = "❌ FAIL"
            Description = "Database connection performance"
            Details = "No successful connections"
            Category = "Database"
            Severity = "CRITICAL"
        }
    }
    
    # Test query performance if psql is available
    $psqlCmd = Get-Command psql -ErrorAction SilentlyContinue
    if ($psqlCmd) {
        Write-Host "  Testing database query performance..." -ForegroundColor Cyan
        
        $dbName = [Environment]::GetEnvironmentVariable("DB_NAME") ?? "healthcare_db"
        $dbUser = [Environment]::GetEnvironmentVariable("DB_USER") ?? "healthcare_user"
        $dbPassword = [Environment]::GetEnvironmentVariable("DB_PASSWORD")
        
        try {
            if (![string]::IsNullOrEmpty($dbPassword)) {
                $env:PGPASSWORD = $dbPassword
            }
            
            # Test simple queries
            $queryTests = @(
                @{Name = "Version Query"; Query = "SELECT version();"; MaxTime = 100},
                @{Name = "Current Time"; Query = "SELECT now();"; MaxTime = 50},
                @{Name = "Database Size"; Query = "SELECT pg_database_size(current_database());"; MaxTime = 200}
            )
            
            foreach ($queryTest in $queryTests) {
                $queryTimes = @()
                
                for ($i = 1; $i -le 5; $i++) {
                    try {
                        $startTime = Get-Date
                        $result = psql -h $dbHost -p $dbPort -U $dbUser -d $dbName -t -c $queryTest.Query 2>&1
                        $endTime = Get-Date
                        
                        if ($LASTEXITCODE -eq 0) {
                            $queryTime = ($endTime - $startTime).TotalMilliseconds
                            $queryTimes += $queryTime
                        }
                    }
                    catch {
                        # Query failed
                    }
                }
                
                if ($queryTimes.Count -gt 0) {
                    $avgQueryTime = ($queryTimes | Measure-Object -Average).Average
                    
                    if ($avgQueryTime -le $queryTest.MaxTime) {
                        Write-Host "    ✅ $($queryTest.Name): $([math]::Round($avgQueryTime, 2))ms" -ForegroundColor Green
                        $testResults += @{
                            Test = "DB_QUERY_$($queryTest.Name.Replace(' ', '_').ToUpper())"
                            Status = "✅ FAST"
                            Description = "Database query: $($queryTest.Name)"
                            Details = "Avg: $([math]::Round($avgQueryTime, 2))ms"
                            Category = "Database"
                            Severity = "INFO"
                        }
                    } else {
                        Write-Host "    ⚠️ $($queryTest.Name): $([math]::Round($avgQueryTime, 2))ms (slow)" -ForegroundColor Yellow
                        $testResults += @{
                            Test = "DB_QUERY_$($queryTest.Name.Replace(' ', '_').ToUpper())"
                            Status = "⚠️ SLOW"
                            Description = "Database query: $($queryTest.Name)"
                            Details = "Avg: $([math]::Round($avgQueryTime, 2))ms (target: $($queryTest.MaxTime)ms)"
                            Category = "Database"
                            Severity = "MEDIUM"
                        }
                    }
                } else {
                    Write-Host "    ❌ $($queryTest.Name): Failed" -ForegroundColor Red
                    $testResults += @{
                        Test = "DB_QUERY_$($queryTest.Name.Replace(' ', '_').ToUpper())"
                        Status = "❌ FAIL"
                        Description = "Database query: $($queryTest.Name)"
                        Details = "Query execution failed"
                        Category = "Database"
                        Severity = "HIGH"
                    }
                }
            }
            
            Remove-Item env:PGPASSWORD -ErrorAction SilentlyContinue
        }
        catch {
            Write-Host "    ❌ Database query testing failed: $($_.Exception.Message)" -ForegroundColor Red
            $script:performanceIssues += "Database query testing failed"
            Remove-Item env:PGPASSWORD -ErrorAction SilentlyContinue
        }
    } else {
        Write-Host "    ⚪ psql not available - skipping query performance tests" -ForegroundColor White
        $testResults += @{
            Test = "DATABASE_QUERY_PERF"
            Status = "⚪ SKIP"
            Description = "Database query performance"
            Details = "psql not available"
            Category = "Database"
            Severity = "LOW"
        }
    }
}

# Run all performance validation tests
Write-Host "`n🚀 Starting Performance Validation Tests..." -ForegroundColor Cyan

Test-APIResponseTimes
Test-ConcurrentLoad
Test-SustainedLoad
Test-ResourceUsage
Test-DatabasePerformance

# Generate results summary
Write-Host "`n📊 PERFORMANCE VALIDATION RESULTS" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green

$passedTests = ($testResults | Where-Object { $_.Status -match "✅" }).Count
$failedTests = ($testResults | Where-Object { $_.Status -match "❌" }).Count
$warningTests = ($testResults | Where-Object { $_.Status -match "⚠️" }).Count
$skippedTests = ($testResults | Where-Object { $_.Status -match "⚪" }).Count
$totalTests = $testResults.Count

Write-Host "`nPerformance Test Summary:" -ForegroundColor Cyan
Write-Host "  Total Tests: $totalTests"
Write-Host "  Passed: $passedTests" -ForegroundColor Green
Write-Host "  Failed: $failedTests" -ForegroundColor Red
Write-Host "  Warnings: $warningTests" -ForegroundColor Yellow
Write-Host "  Skipped: $skippedTests" -ForegroundColor Gray

# Group results by severity
$criticalIssues = ($testResults | Where-Object { $_.Severity -eq "CRITICAL" -and $_.Status -match "❌" }).Count
$highIssues = ($testResults | Where-Object { $_.Severity -eq "HIGH" -and $_.Status -match "❌" }).Count
$mediumIssues = ($testResults | Where-Object { $_.Severity -eq "MEDIUM" -and $_.Status -match "❌|⚠️" }).Count

Write-Host "`nIssues by Severity:" -ForegroundColor Cyan
Write-Host "  Critical: $criticalIssues" -ForegroundColor $(if ($criticalIssues -eq 0) { "Green" } else { "Red" })
Write-Host "  High: $highIssues" -ForegroundColor $(if ($highIssues -eq 0) { "Green" } else { "Red" })
Write-Host "  Medium: $mediumIssues" -ForegroundColor $(if ($mediumIssues -eq 0) { "Green" } else { "Yellow" })

# Show performance issues
if ($performanceIssues.Count -gt 0) {
    Write-Host "`n⚡ Performance Issues to Address:" -ForegroundColor Yellow
    for ($i = 0; $i -lt $performanceIssues.Count; $i++) {
        Write-Host "  $($i + 1). $($performanceIssues[$i])" -ForegroundColor Red
    }
}

# Show detailed results by category
Write-Host "`nDetailed Results by Category:" -ForegroundColor Cyan
$categories = @("Performance", "Concurrency", "Endurance", "Resources", "Database", "Stability")

foreach ($category in $categories) {
    $categoryTests = $testResults | Where-Object { $_.Category -eq $category }
    if ($categoryTests.Count -gt 0) {
        Write-Host "  $category Tests:" -ForegroundColor Yellow
        foreach ($test in $categoryTests) {
            Write-Host "    $($test.Status) $($test.Description)"
            if ($test.Details -and $test.Details -ne "") {
                Write-Host "      Details: $($test.Details)" -ForegroundColor Gray
            }
        }
    }
}

# Performance benchmarks summary
Write-Host "`n📈 Performance Benchmarks:" -ForegroundColor Cyan
$apiResponseTests = $testResults | Where-Object { $_.Test -match "API_RESPONSE" -and $_.ResponseTime }
if ($apiResponseTests.Count -gt 0) {
    $avgApiResponse = ($apiResponseTests.ResponseTime | Measure-Object -Average).Average
    Write-Host "  Average API Response Time: $([math]::Round($avgApiResponse, 2))ms" -ForegroundColor White
}

$concurrencyTests = $testResults | Where-Object { $_.Test -match "CONCURRENT_LOAD" -and $_.Throughput }
if ($concurrencyTests.Count -gt 0) {
    $maxThroughput = ($concurrencyTests.Throughput | Measure-Object -Maximum).Maximum
    Write-Host "  Peak Throughput: $([math]::Round($maxThroughput, 2)) req/s" -ForegroundColor White
}

$sustainedTest = $testResults | Where-Object { $_.Test -eq "SUSTAINED_LOAD" -and $_.ActualThroughput }
if ($sustainedTest) {
    Write-Host "  Sustained Throughput: $([math]::Round($sustainedTest.ActualThroughput, 2)) req/s" -ForegroundColor White
}

# Save results to file
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$resultFile = "performance_validation_$timestamp.json"

try {
    $resultsData = @{
        timestamp = $timestamp
        summary = @{
            total_tests = $totalTests
            passed = $passedTests
            failed = $failedTests
            warnings = $warningTests
            skipped = $skippedTests
            critical_issues = $criticalIssues
            high_issues = $highIssues
            medium_issues = $mediumIssues
        }
        tests = $testResults
        performance_issues = $performanceIssues
        benchmarks = @{
            avg_api_response_time = if ($apiResponseTests.Count -gt 0) { ($apiResponseTests.ResponseTime | Measure-Object -Average).Average } else { 0 }
            peak_throughput = if ($concurrencyTests.Count -gt 0) { ($concurrencyTests.Throughput | Measure-Object -Maximum).Maximum } else { 0 }
            sustained_throughput = if ($sustainedTest) { $sustainedTest.ActualThroughput } else { 0 }
        }
        production_ready = ($criticalIssues -eq 0 -and $highIssues -eq 0)
    }
    
    $resultsData | ConvertTo-Json -Depth 5 | Out-File -FilePath $resultFile -Encoding UTF8
    Write-Host "`n📁 Results saved to: $resultFile" -ForegroundColor Cyan
}
catch {
    Write-Host "`n⚠️ Could not save results to file: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Final assessment
Write-Host "`n🎯 FINAL PERFORMANCE ASSESSMENT" -ForegroundColor Green
if ($allPassed -and $criticalIssues -eq 0 -and $highIssues -eq 0) {
    Write-Host "✅ PERFORMANCE VALIDATION PASSED" -ForegroundColor Green
    Write-Host "System performance meets production requirements!" -ForegroundColor Green
    exit 0
} elseif ($criticalIssues -eq 0 -and $highIssues -eq 0) {
    Write-Host "⚠️ PERFORMANCE VALIDATION PASSED WITH RECOMMENDATIONS" -ForegroundColor Yellow
    Write-Host "System performance is acceptable but could be optimized." -ForegroundColor Yellow
    exit 0
} else {
    Write-Host "❌ PERFORMANCE VALIDATION FAILED" -ForegroundColor Red
    Write-Host "Performance issues must be addressed before production deployment!" -ForegroundColor Red
    exit 1
}