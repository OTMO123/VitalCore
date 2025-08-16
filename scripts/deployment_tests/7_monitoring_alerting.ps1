# Monitoring & Alerting Validation Script
# Tests: Grafana dashboards, Prometheus metrics, Alertmanager rules, health monitoring
# Based on: PRODUCTION_DEPLOYMENT_CHECKLIST.md - Monitoring & Alerting

Write-Host "📊 Monitoring & Alerting Validation Test" -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green

$testResults = @()
$allPassed = $true
$monitoringIssues = @()

function Test-PrometheusService {
    Write-Host "`n🔍 Testing Prometheus Service..." -ForegroundColor Yellow
    
    $prometheusUrl = "http://localhost:9090"
    
    try {
        # Test Prometheus web interface
        $response = Invoke-WebRequest -Uri "$prometheusUrl/api/v1/query?query=up" -TimeoutSec 10 -UseBasicParsing
        
        if ($response.StatusCode -eq 200) {
            Write-Host "  ✅ Prometheus API is accessible" -ForegroundColor Green
            $testResults += @{
                Test = "PROMETHEUS_API"
                Status = "✅ ACCESSIBLE"
                Description = "Prometheus API accessibility"
                Details = "HTTP 200 response received"
                Category = "Monitoring"
                Severity = "INFO"
            }
            
            # Parse response to check for targets
            $data = $response.Content | ConvertFrom-Json
            $upTargets = $data.data.result.Count
            
            Write-Host "  ✅ Found $upTargets active targets" -ForegroundColor Green
            $testResults += @{
                Test = "PROMETHEUS_TARGETS"
                Status = "✅ ACTIVE"
                Description = "Prometheus monitoring targets"
                Details = "$upTargets targets found"
                Category = "Monitoring"
                Severity = "INFO"
            }
        }
    }
    catch {
        Write-Host "  ❌ Prometheus service not accessible: $($_.Exception.Message)" -ForegroundColor Red
        $script:allPassed = $false
        $script:monitoringIssues += "Prometheus service is not running or accessible"
        $testResults += @{
            Test = "PROMETHEUS_SERVICE"
            Status = "❌ FAIL"
            Description = "Prometheus service accessibility"
            Details = $_.Exception.Message
            Category = "Monitoring"
            Severity = "CRITICAL"
        }
    }
    
    # Test Prometheus configuration file
    $prometheusConfig = "monitoring/prometheus/prometheus.yml"
    if (Test-Path $prometheusConfig) {
        Write-Host "  ✅ Prometheus configuration file exists" -ForegroundColor Green
        $testResults += @{
            Test = "PROMETHEUS_CONFIG"
            Status = "✅ EXISTS"
            Description = "Prometheus configuration file"
            Details = "Configuration file found at $prometheusConfig"
            Category = "Monitoring"
            Severity = "INFO"
        }
        
        # Validate configuration content
        try {
            $configContent = Get-Content $prometheusConfig -Raw
            if ($configContent -match "healthcare-api" -and $configContent -match "scrape_configs") {
                Write-Host "  ✅ Prometheus configuration appears valid" -ForegroundColor Green
                $testResults += @{
                    Test = "PROMETHEUS_CONFIG_VALID"
                    Status = "✅ VALID"
                    Description = "Prometheus configuration validation"
                    Details = "Healthcare API scraping configured"
                    Category = "Monitoring"
                    Severity = "INFO"
                }
            } else {
                Write-Host "  ⚠️ Prometheus configuration may be incomplete" -ForegroundColor Yellow
                $script:monitoringIssues += "Prometheus configuration missing healthcare-api scraping"
                $testResults += @{
                    Test = "PROMETHEUS_CONFIG_VALID"
                    Status = "⚠️ INCOMPLETE"
                    Description = "Prometheus configuration validation"
                    Details = "Configuration may be missing healthcare scraping"
                    Category = "Monitoring"
                    Severity = "MEDIUM"
                }
            }
        }
        catch {
            Write-Host "  ❌ Failed to validate Prometheus configuration" -ForegroundColor Red
            $script:monitoringIssues += "Cannot read Prometheus configuration file"
        }
    } else {
        Write-Host "  ❌ Prometheus configuration file not found" -ForegroundColor Red
        $script:allPassed = $false
        $script:monitoringIssues += "Prometheus configuration file missing"
        $testResults += @{
            Test = "PROMETHEUS_CONFIG"
            Status = "❌ MISSING"
            Description = "Prometheus configuration file"
            Details = "Configuration file not found"
            Category = "Monitoring"
            Severity = "HIGH"
        }
    }
    
    # Test alert rules
    $alertRules = "monitoring/prometheus/alert_rules.yml"
    if (Test-Path $alertRules) {
        Write-Host "  ✅ Prometheus alert rules file exists" -ForegroundColor Green
        $testResults += @{
            Test = "PROMETHEUS_ALERT_RULES"
            Status = "✅ EXISTS"
            Description = "Prometheus alert rules file"
            Details = "Alert rules found at $alertRules"
            Category = "Monitoring"
            Severity = "INFO"
        }
    } else {
        Write-Host "  ⚠️ Prometheus alert rules file not found" -ForegroundColor Yellow
        $script:monitoringIssues += "Prometheus alert rules file missing"
        $testResults += @{
            Test = "PROMETHEUS_ALERT_RULES"
            Status = "⚠️ MISSING"
            Description = "Prometheus alert rules file"
            Details = "Alert rules file not found"
            Category = "Monitoring"
            Severity = "MEDIUM"
        }
    }
}

function Test-GrafanaService {
    Write-Host "`n📈 Testing Grafana Service..." -ForegroundColor Yellow
    
    $grafanaUrl = "http://localhost:3001"
    
    try {
        # Test Grafana login page
        $response = Invoke-WebRequest -Uri "$grafanaUrl/login" -TimeoutSec 10 -UseBasicParsing
        
        if ($response.StatusCode -eq 200) {
            Write-Host "  ✅ Grafana web interface is accessible" -ForegroundColor Green
            $testResults += @{
                Test = "GRAFANA_WEB_INTERFACE"
                Status = "✅ ACCESSIBLE"
                Description = "Grafana web interface accessibility"
                Details = "Login page accessible"
                Category = "Monitoring"
                Severity = "INFO"
            }
        }
        
        # Test Grafana API (health check)
        try {
            $healthResponse = Invoke-WebRequest -Uri "$grafanaUrl/api/health" -TimeoutSec 10 -UseBasicParsing
            if ($healthResponse.StatusCode -eq 200) {
                Write-Host "  ✅ Grafana API health check passed" -ForegroundColor Green
                $testResults += @{
                    Test = "GRAFANA_API_HEALTH"
                    Status = "✅ HEALTHY"
                    Description = "Grafana API health check"
                    Details = "API health endpoint responding"
                    Category = "Monitoring"
                    Severity = "INFO"
                }
            }
        }
        catch {
            Write-Host "  ⚠️ Grafana API health check failed" -ForegroundColor Yellow
            $testResults += @{
                Test = "GRAFANA_API_HEALTH"
                Status = "⚠️ LIMITED"
                Description = "Grafana API health check"
                Details = "Health endpoint not accessible"
                Category = "Monitoring"
                Severity = "LOW"
            }
        }
        
    }
    catch {
        Write-Host "  ❌ Grafana service not accessible: $($_.Exception.Message)" -ForegroundColor Red
        $script:allPassed = $false
        $script:monitoringIssues += "Grafana service is not running or accessible"
        $testResults += @{
            Test = "GRAFANA_SERVICE"
            Status = "❌ FAIL"
            Description = "Grafana service accessibility"
            Details = $_.Exception.Message
            Category = "Monitoring"
            Severity = "CRITICAL"
        }
    }
    
    # Test Grafana configuration files
    $grafanaConfigs = @(
        @{Path = "monitoring/grafana/grafana.ini"; Desc = "Grafana main configuration"},
        @{Path = "monitoring/grafana/provisioning/datasources/prometheus.yml"; Desc = "Prometheus datasource"},
        @{Path = "monitoring/grafana/provisioning/dashboards/dashboard.yml"; Desc = "Dashboard provisioning"}
    )
    
    foreach ($config in $grafanaConfigs) {
        if (Test-Path $config.Path) {
            Write-Host "  ✅ $($config.Desc) file exists" -ForegroundColor Green
            $testResults += @{
                Test = "GRAFANA_CONFIG_$($config.Path.Split('/')[-1].Replace('.','_').ToUpper())"
                Status = "✅ EXISTS"
                Description = $config.Desc
                Details = "Configuration file found"
                Category = "Monitoring"
                Severity = "INFO"
            }
        } else {
            Write-Host "  ⚠️ $($config.Desc) file not found" -ForegroundColor Yellow
            $script:monitoringIssues += "$($config.Desc) configuration missing"
            $testResults += @{
                Test = "GRAFANA_CONFIG_$($config.Path.Split('/')[-1].Replace('.','_').ToUpper())"
                Status = "⚠️ MISSING"
                Description = $config.Desc
                Details = "Configuration file not found"
                Category = "Monitoring"
                Severity = "MEDIUM"
            }
        }
    }
    
    # Check for dashboard files
    $dashboardDir = "monitoring/grafana/dashboards"
    if (Test-Path $dashboardDir) {
        $dashboardFiles = Get-ChildItem -Path $dashboardDir -Filter "*.json" | Measure-Object
        if ($dashboardFiles.Count -gt 0) {
            Write-Host "  ✅ Found $($dashboardFiles.Count) dashboard files" -ForegroundColor Green
            $testResults += @{
                Test = "GRAFANA_DASHBOARDS"
                Status = "✅ FOUND"
                Description = "Grafana dashboard files"
                Details = "$($dashboardFiles.Count) dashboard files found"
                Category = "Monitoring"
                Severity = "INFO"
            }
        } else {
            Write-Host "  ⚠️ No dashboard files found" -ForegroundColor Yellow
            $script:monitoringIssues += "No Grafana dashboard files found"
            $testResults += @{
                Test = "GRAFANA_DASHBOARDS"
                Status = "⚠️ EMPTY"
                Description = "Grafana dashboard files"
                Details = "No dashboard files found"
                Category = "Monitoring"
                Severity = "MEDIUM"
            }
        }
    }
}

function Test-AlertmanagerService {
    Write-Host "`n🚨 Testing Alertmanager Service..." -ForegroundColor Yellow
    
    $alertmanagerUrl = "http://localhost:9093"
    
    try {
        # Test Alertmanager API
        $response = Invoke-WebRequest -Uri "$alertmanagerUrl/api/v1/status" -TimeoutSec 10 -UseBasicParsing
        
        if ($response.StatusCode -eq 200) {
            Write-Host "  ✅ Alertmanager API is accessible" -ForegroundColor Green
            $testResults += @{
                Test = "ALERTMANAGER_API"
                Status = "✅ ACCESSIBLE"
                Description = "Alertmanager API accessibility"
                Details = "Status endpoint responding"
                Category = "Alerting"
                Severity = "INFO"
            }
            
            # Test alerts endpoint
            try {
                $alertsResponse = Invoke-WebRequest -Uri "$alertmanagerUrl/api/v1/alerts" -TimeoutSec 10 -UseBasicParsing
                if ($alertsResponse.StatusCode -eq 200) {
                    $alertsData = $alertsResponse.Content | ConvertFrom-Json
                    $activeAlerts = $alertsData.data.Count
                    
                    Write-Host "  ✅ Alertmanager alerts endpoint accessible ($activeAlerts active alerts)" -ForegroundColor Green
                    $testResults += @{
                        Test = "ALERTMANAGER_ALERTS"
                        Status = "✅ ACCESSIBLE"
                        Description = "Alertmanager alerts endpoint"
                        Details = "$activeAlerts active alerts"
                        Category = "Alerting"
                        Severity = "INFO"
                    }
                }
            }
            catch {
                Write-Host "  ⚠️ Alertmanager alerts endpoint not accessible" -ForegroundColor Yellow
            }
        }
    }
    catch {
        Write-Host "  ❌ Alertmanager service not accessible: $($_.Exception.Message)" -ForegroundColor Red
        $script:allPassed = $false
        $script:monitoringIssues += "Alertmanager service is not running or accessible"
        $testResults += @{
            Test = "ALERTMANAGER_SERVICE"
            Status = "❌ FAIL"
            Description = "Alertmanager service accessibility"
            Details = $_.Exception.Message
            Category = "Alerting"
            Severity = "HIGH"
        }
    }
    
    # Test Alertmanager configuration
    $alertmanagerConfig = "monitoring/alertmanager/alertmanager.yml"
    if (Test-Path $alertmanagerConfig) {
        Write-Host "  ✅ Alertmanager configuration file exists" -ForegroundColor Green
        $testResults += @{
            Test = "ALERTMANAGER_CONFIG"
            Status = "✅ EXISTS"
            Description = "Alertmanager configuration file"
            Details = "Configuration file found"
            Category = "Alerting"
            Severity = "INFO"
        }
    } else {
        Write-Host "  ⚠️ Alertmanager configuration file not found" -ForegroundColor Yellow
        $script:monitoringIssues += "Alertmanager configuration file missing"
        $testResults += @{
            Test = "ALERTMANAGER_CONFIG"
            Status = "⚠️ MISSING"
            Description = "Alertmanager configuration file"
            Details = "Configuration file not found"
            Category = "Alerting"
            Severity = "MEDIUM"
        }
    }
}

function Test-ApplicationMetrics {
    Write-Host "`n📊 Testing Application Metrics..." -ForegroundColor Yellow
    
    $metricsUrl = "http://localhost:8000/metrics"
    
    try {
        # Test application metrics endpoint
        $response = Invoke-WebRequest -Uri $metricsUrl -TimeoutSec 10 -UseBasicParsing
        
        if ($response.StatusCode -eq 200) {
            Write-Host "  ✅ Application metrics endpoint accessible" -ForegroundColor Green
            
            # Check for specific healthcare metrics
            $metricsContent = $response.Content
            $healthcareMetrics = @(
                "healthcare_api_requests_total",
                "healthcare_phi_access_total",
                "healthcare_immunization_records_total",
                "healthcare_audit_events_total",
                "healthcare_database_connections",
                "healthcare_response_time_seconds"
            )
            
            $foundMetrics = 0
            foreach ($metric in $healthcareMetrics) {
                if ($metricsContent -match $metric) {
                    $foundMetrics++
                    Write-Host "    ✅ Found metric: $metric" -ForegroundColor Green
                } else {
                    Write-Host "    ⚠️ Missing metric: $metric" -ForegroundColor Yellow
                }
            }
            
            $metricsPercentage = [math]::Round(($foundMetrics / $healthcareMetrics.Count) * 100, 1)
            
            $testResults += @{
                Test = "APPLICATION_METRICS"
                Status = if ($foundMetrics -eq $healthcareMetrics.Count) { "✅ COMPLETE" } 
                         elseif ($foundMetrics -gt 0) { "⚠️ PARTIAL" } 
                         else { "❌ MISSING" }
                Description = "Application healthcare metrics"
                Details = "$foundMetrics/$($healthcareMetrics.Count) metrics found ($metricsPercentage%)"
                Category = "Metrics"
                Severity = if ($foundMetrics -gt ($healthcareMetrics.Count / 2)) { "INFO" } else { "MEDIUM" }
            }
            
            if ($foundMetrics -lt $healthcareMetrics.Count) {
                $script:monitoringIssues += "Some healthcare metrics are missing from /metrics endpoint"
            }
        }
    }
    catch {
        Write-Host "  ❌ Application metrics endpoint not accessible: $($_.Exception.Message)" -ForegroundColor Red
        $script:allPassed = $false
        $script:monitoringIssues += "Application metrics endpoint is not accessible"
        $testResults += @{
            Test = "APPLICATION_METRICS"
            Status = "❌ FAIL"
            Description = "Application metrics endpoint"
            Details = $_.Exception.Message
            Category = "Metrics"
            Severity = "HIGH"
        }
    }
}

function Test-HealthEndpoints {
    Write-Host "`n❤️ Testing Health Monitoring Endpoints..." -ForegroundColor Yellow
    
    $healthEndpoints = @(
        @{Url = "http://localhost:8000/health"; Name = "Main Health Check"},
        @{Url = "http://localhost:8000/api/v1/healthcare-records/health"; Name = "Healthcare Records Health"},
        @{Url = "http://localhost:8000/readiness"; Name = "Readiness Probe"},
        @{Url = "http://localhost:8000/liveness"; Name = "Liveness Probe"}
    )
    
    foreach ($endpoint in $healthEndpoints) {
        try {
            $response = Invoke-WebRequest -Uri $endpoint.Url -TimeoutSec 10 -UseBasicParsing
            
            if ($response.StatusCode -eq 200) {
                Write-Host "  ✅ $($endpoint.Name) is healthy" -ForegroundColor Green
                
                # Try to parse JSON response for more details
                try {
                    $healthData = $response.Content | ConvertFrom-Json
                    $status = $healthData.status ?? "unknown"
                    
                    $testResults += @{
                        Test = "HEALTH_$($endpoint.Name.Replace(' ', '_').ToUpper())"
                        Status = "✅ HEALTHY"
                        Description = $endpoint.Name
                        Details = "Status: $status"
                        Category = "Health"
                        Severity = "INFO"
                    }
                }
                catch {
                    $testResults += @{
                        Test = "HEALTH_$($endpoint.Name.Replace(' ', '_').ToUpper())"
                        Status = "✅ RESPONDING"
                        Description = $endpoint.Name
                        Details = "HTTP 200 but non-JSON response"
                        Category = "Health"
                        Severity = "INFO"
                    }
                }
            } else {
                Write-Host "  ⚠️ $($endpoint.Name) returned HTTP $($response.StatusCode)" -ForegroundColor Yellow
                $testResults += @{
                    Test = "HEALTH_$($endpoint.Name.Replace(' ', '_').ToUpper())"
                    Status = "⚠️ DEGRADED"
                    Description = $endpoint.Name
                    Details = "HTTP $($response.StatusCode)"
                    Category = "Health"
                    Severity = "MEDIUM"
                }
            }
        }
        catch {
            Write-Host "  ❌ $($endpoint.Name) is not accessible: $($_.Exception.Message)" -ForegroundColor Red
            $script:allPassed = $false
            $script:monitoringIssues += "$($endpoint.Name) health endpoint is not accessible"
            $testResults += @{
                Test = "HEALTH_$($endpoint.Name.Replace(' ', '_').ToUpper())"
                Status = "❌ FAIL"
                Description = $endpoint.Name
                Details = $_.Exception.Message
                Category = "Health"
                Severity = "HIGH"
            }
        }
    }
}

function Test-LoggingServices {
    Write-Host "`n📝 Testing Logging Services..." -ForegroundColor Yellow
    
    # Test Loki service (if available)
    try {
        $lokiResponse = Invoke-WebRequest -Uri "http://localhost:3100/ready" -TimeoutSec 5 -UseBasicParsing
        if ($lokiResponse.StatusCode -eq 200) {
            Write-Host "  ✅ Loki logging service is accessible" -ForegroundColor Green
            $testResults += @{
                Test = "LOKI_SERVICE"
                Status = "✅ ACCESSIBLE"
                Description = "Loki logging service"
                Details = "Ready endpoint responding"
                Category = "Logging"
                Severity = "INFO"
            }
        }
    }
    catch {
        Write-Host "  ⚠️ Loki logging service not accessible (optional)" -ForegroundColor Yellow
        $testResults += @{
            Test = "LOKI_SERVICE"
            Status = "⚠️ UNAVAILABLE"
            Description = "Loki logging service"
            Details = "Service not accessible"
            Category = "Logging"
            Severity = "LOW"
        }
    }
    
    # Test log directories and files
    $logDirs = @("logs", "logs/audit", "logs/security", "logs/performance")
    foreach ($logDir in $logDirs) {
        if (Test-Path $logDir) {
            Write-Host "  ✅ Log directory exists: $logDir" -ForegroundColor Green
            
            # Check if there are recent log files
            try {
                $recentLogs = Get-ChildItem -Path $logDir -Filter "*.log" | Where-Object { $_.LastWriteTime -gt (Get-Date).AddHours(-24) }
                if ($recentLogs.Count -gt 0) {
                    Write-Host "    ✅ Found $($recentLogs.Count) recent log files" -ForegroundColor Green
                    $testResults += @{
                        Test = "LOG_DIR_$($logDir.Replace('/', '_').ToUpper())"
                        Status = "✅ ACTIVE"
                        Description = "Log directory: $logDir"
                        Details = "$($recentLogs.Count) recent log files"
                        Category = "Logging"
                        Severity = "INFO"
                    }
                } else {
                    Write-Host "    ⚠️ No recent log files in $logDir" -ForegroundColor Yellow
                    $testResults += @{
                        Test = "LOG_DIR_$($logDir.Replace('/', '_').ToUpper())"
                        Status = "⚠️ INACTIVE"
                        Description = "Log directory: $logDir"
                        Details = "No recent log files"
                        Category = "Logging"
                        Severity = "LOW"
                    }
                }
            }
            catch {
                $testResults += @{
                    Test = "LOG_DIR_$($logDir.Replace('/', '_').ToUpper())"
                    Status = "✅ EXISTS"
                    Description = "Log directory: $logDir"
                    Details = "Directory exists"
                    Category = "Logging"
                    Severity = "INFO"
                }
            }
        } else {
            Write-Host "  ⚠️ Log directory missing: $logDir" -ForegroundColor Yellow
            $script:monitoringIssues += "Log directory missing: $logDir"
        }
    }
}

# Run all monitoring and alerting tests
Write-Host "`n🚀 Starting Monitoring & Alerting Tests...`n" -ForegroundColor Cyan

Test-PrometheusService
Test-GrafanaService
Test-AlertmanagerService
Test-ApplicationMetrics
Test-HealthEndpoints
Test-LoggingServices

# Generate results summary
Write-Host "`n📊 MONITORING & ALERTING RESULTS" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green

$passedTests = ($testResults | Where-Object { $_.Status -match "✅" }).Count
$failedTests = ($testResults | Where-Object { $_.Status -match "❌" }).Count
$warningTests = ($testResults | Where-Object { $_.Status -match "⚠️" }).Count
$totalTests = $testResults.Count

Write-Host "`nMonitoring Test Summary:" -ForegroundColor Cyan
Write-Host "  Total Tests: $totalTests"
Write-Host "  Passed: $passedTests" -ForegroundColor Green
Write-Host "  Failed: $failedTests" -ForegroundColor Red
Write-Host "  Warnings: $warningTests" -ForegroundColor Yellow

# Group results by category
$categories = @("Monitoring", "Alerting", "Metrics", "Health", "Logging")
foreach ($category in $categories) {
    $categoryTests = $testResults | Where-Object { $_.Category -eq $category }
    if ($categoryTests.Count -gt 0) {
        Write-Host "`n$category Tests:" -ForegroundColor Yellow
        foreach ($test in $categoryTests) {
            Write-Host "  $($test.Status) $($test.Description)"
            if ($test.Details) {
                Write-Host "    Details: $($test.Details)" -ForegroundColor Gray
            }
        }
    }
}

# Show monitoring issues
if ($monitoringIssues.Count -gt 0) {
    Write-Host "`n🔧 Monitoring Issues to Fix:" -ForegroundColor Yellow
    for ($i = 0; $i -lt $monitoringIssues.Count; $i++) {
        Write-Host "  $($i + 1). $($monitoringIssues[$i])" -ForegroundColor Red
    }
}

# Save results to file
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$resultFile = "monitoring_alerting_$timestamp.json"

try {
    $resultsData = @{
        timestamp = $timestamp
        summary = @{
            total_tests = $totalTests
            passed = $passedTests
            failed = $failedTests
            warnings = $warningTests
        }
        tests = $testResults
        monitoring_issues = $monitoringIssues
        service_status = @{
            prometheus = ($testResults | Where-Object { $_.Test -eq "PROMETHEUS_API" -and $_.Status -match "✅" }) -ne $null
            grafana = ($testResults | Where-Object { $_.Test -eq "GRAFANA_WEB_INTERFACE" -and $_.Status -match "✅" }) -ne $null
            alertmanager = ($testResults | Where-Object { $_.Test -eq "ALERTMANAGER_API" -and $_.Status -match "✅" }) -ne $null
            app_metrics = ($testResults | Where-Object { $_.Test -eq "APPLICATION_METRICS" -and $_.Status -match "✅" }) -ne $null
        }
    }
    
    $resultsData | ConvertTo-Json -Depth 5 | Out-File -FilePath $resultFile -Encoding UTF8
    Write-Host "`n📁 Results saved to: $resultFile" -ForegroundColor Cyan
}
catch {
    Write-Host "`n⚠️ Could not save results to file: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Final assessment
Write-Host "`n🎯 FINAL MONITORING ASSESSMENT" -ForegroundColor Green
$criticalFailures = ($testResults | Where-Object { $_.Severity -eq "CRITICAL" -and $_.Status -match "❌" }).Count
$highFailures = ($testResults | Where-Object { $_.Severity -eq "HIGH" -and $_.Status -match "❌" }).Count

if ($allPassed -and $criticalFailures -eq 0 -and $highFailures -eq 0) {
    Write-Host "✅ MONITORING & ALERTING VALIDATION PASSED" -ForegroundColor Green
    Write-Host "All monitoring services are operational and ready for production!" -ForegroundColor Green
    exit 0
} elseif ($criticalFailures -eq 0 -and $highFailures -eq 0) {
    Write-Host "⚠️ MONITORING & ALERTING VALIDATION PASSED WITH WARNINGS" -ForegroundColor Yellow
    Write-Host "Core monitoring is working but some optional features need attention." -ForegroundColor Yellow
    exit 0
} else {
    Write-Host "❌ MONITORING & ALERTING VALIDATION FAILED" -ForegroundColor Red
    Write-Host "Critical monitoring issues must be fixed before production deployment!" -ForegroundColor Red
    exit 1
}