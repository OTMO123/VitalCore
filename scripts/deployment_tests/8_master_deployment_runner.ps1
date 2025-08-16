# Master Deployment Test Runner
# Orchestrates all deployment validation tests and provides comprehensive reporting
# Based on: PRODUCTION_DEPLOYMENT_CHECKLIST.md - Complete Deployment Validation

Write-Host "Master Deployment Test Runner" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green
Write-Host "Healthcare Records Backend - Production Deployment Validation`n" -ForegroundColor Cyan

$startTime = Get-Date
$masterResults = @()
$allTestsPassed = $true
$totalIssues = @()

# Define test scripts in execution order
$deploymentTests = @(
    @{
        Script = "1_infrastructure_validation.ps1"
        Name = "Infrastructure Validation"
        Description = "Database, Redis, MinIO, Docker, networking"
        Critical = $true
        Order = 1
    },
    @{
        Script = "2_application_configuration.ps1"  
        Name = "Application Configuration"
        Description = "Environment variables, security settings, HIPAA compliance"
        Critical = $true
        Order = 2
    },
    @{
        Script = "3_security_compliance.ps1"
        Name = "Security & Compliance"
        Description = "HIPAA, SOC2, encryption, audit logging"
        Critical = $true
        Order = 3
    },
    @{
        Script = "4_database_migration.ps1"
        Name = "Database Migration"
        Description = "Alembic migrations, backup/restore, rollback procedures"
        Critical = $true
        Order = 4
    },
    @{
        Script = "5_application_deployment.ps1"
        Name = "Application Deployment"
        Description = "Docker builds, service deployment, health checks"
        Critical = $true
        Order = 5
    },
    @{
        Script = "6_performance_validation.ps1"
        Name = "Performance Validation"
        Description = "Load testing, response times, resource usage"
        Critical = $false
        Order = 6
    },
    @{
        Script = "7_monitoring_alerting.ps1"
        Name = "Monitoring & Alerting"
        Description = "Grafana dashboards, Prometheus metrics, alert rules"
        Critical = $false
        Order = 7
    }
)

function Write-TestHeader {
    param([string]$TestName, [int]$TestNumber, [int]$TotalTests)
    
    Write-Host "`n" + "="*80 -ForegroundColor DarkCyan
    Write-Host "TEST ${TestNumber}/${TotalTests}: $TestName" -ForegroundColor Yellow
    Write-Host "="*80 -ForegroundColor DarkCyan
}

function Write-TestResult {
    param([string]$TestName, [bool]$Passed, [string]$Details, [int]$Duration)
    
    $status = if ($Passed) { "PASSED" } else { "FAILED" }
    $color = if ($Passed) { "Green" } else { "Red" }
    
    Write-Host "`n$TestName Result: $status" -ForegroundColor $color
    Write-Host "   Duration: $Duration seconds" -ForegroundColor Gray
    if ($Details) {
        Write-Host "   Details: $Details" -ForegroundColor Gray
    }
}

function Execute-DeploymentTest {
    param([hashtable]$TestConfig)
    
    $testStartTime = Get-Date
    $testPath = Join-Path "scripts/deployment_tests" $TestConfig.Script
    
    Write-TestHeader -TestName $TestConfig.Name -TestNumber $TestConfig.Order -TotalTests $deploymentTests.Count
    Write-Host "Description: $($TestConfig.Description)" -ForegroundColor Cyan
    Write-Host "Critical: $($TestConfig.Critical)" -ForegroundColor $(if ($TestConfig.Critical) { "Red" } else { "Yellow" })
    Write-Host "Script: $testPath`n" -ForegroundColor Gray
    
    $testResult = @{
        Name = $TestConfig.Name
        Script = $TestConfig.Script
        Critical = $TestConfig.Critical
        StartTime = $testStartTime
        Passed = $false
        ExitCode = -1
        Duration = 0
        Output = ""
        Issues = @()
    }
    
    try {
        if (Test-Path $testPath) {
            Write-Host "Executing test script..." -ForegroundColor Yellow
            
            # Execute the PowerShell script and capture output
            $process = Start-Process -FilePath "powershell.exe" -ArgumentList "-ExecutionPolicy Bypass", "-File", $testPath -NoNewWindow -Wait -PassThru -RedirectStandardOutput "temp_output.txt" -RedirectStandardError "temp_error.txt"
            
            $testResult.ExitCode = $process.ExitCode
            $testResult.Passed = ($process.ExitCode -eq 0)
            
            # Read output files
            if (Test-Path "temp_output.txt") {
                $testResult.Output = Get-Content "temp_output.txt" -Raw
                Remove-Item "temp_output.txt" -Force -ErrorAction SilentlyContinue
            }
            
            if (Test-Path "temp_error.txt") {
                $errorOutput = Get-Content "temp_error.txt" -Raw
                if (![string]::IsNullOrWhiteSpace($errorOutput)) {
                    $testResult.Output += "`nERRORS:`n$errorOutput"
                }
                Remove-Item "temp_error.txt" -Force -ErrorAction SilentlyContinue
            }
            
            # Parse issues from result files if they exist
            $resultFiles = Get-ChildItem -Path "." -Filter "*$($TestConfig.Name.Replace(' ', '_').ToLower())*.json" -ErrorAction SilentlyContinue
            foreach ($resultFile in $resultFiles) {
                try {
                    $resultData = Get-Content $resultFile -Raw | ConvertFrom-Json
                    if ($resultData.issues -or $resultData.security_issues -or $resultData.monitoring_issues) {
                        $issues = @()
                        if ($resultData.issues) { 
                            $issues += $resultData.issues 
                        }
                        if ($resultData.security_issues) { 
                            $issues += $resultData.security_issues 
                        }
                        if ($resultData.monitoring_issues) { 
                            $issues += $resultData.monitoring_issues 
                        }
                        $testResult.Issues = $issues
                    }
                }
                catch {
                    # Ignore JSON parsing errors
                }
            }
            
        } else {
            Write-Host "Test script not found: $testPath" -ForegroundColor Red
            $testResult.Output = "Test script file not found"
            $testResult.Issues += "Test script file not found: $testPath"
        }
    }
    catch {
        Write-Host "Test execution failed: $($_.Exception.Message)" -ForegroundColor Red
        $testResult.Output = $_.Exception.Message
        $testResult.Issues += "Test execution failed: $($_.Exception.Message)"
    }
    
    $testEndTime = Get-Date
    $testResult.Duration = [math]::Round(($testEndTime - $testStartTime).TotalSeconds, 1)
    $testResult.EndTime = $testEndTime
    
    # Update master tracking
    if (!$testResult.Passed) {
        $script:allTestsPassed = $false
        if ($TestConfig.Critical) {
            Write-Host "CRITICAL TEST FAILED - Deployment cannot proceed!" -ForegroundColor Red
        }
        $script:totalIssues += $testResult.Issues
    }
    
    Write-TestResult -TestName $TestConfig.Name -Passed $testResult.Passed -Details "Exit code: $($testResult.ExitCode)" -Duration $testResult.Duration
    
    return $testResult
}

function Generate-DeploymentReport {
    param([array]$Results)
    
    Write-Host "`n" + "="*80 -ForegroundColor Green
    Write-Host "DEPLOYMENT VALIDATION SUMMARY REPORT" -ForegroundColor Green
    Write-Host "="*80 -ForegroundColor Green
    
    $endTime = Get-Date
    $totalDuration = [math]::Round(($endTime - $startTime).TotalMinutes, 1)
    
    Write-Host "`nExecution Summary:" -ForegroundColor Cyan
    Write-Host "  Start Time: $($startTime.ToString('yyyy-MM-dd HH:mm:ss'))"
    Write-Host "  End Time: $($endTime.ToString('yyyy-MM-dd HH:mm:ss'))"
    Write-Host "  Total Duration: $totalDuration minutes"
    Write-Host "  Tests Executed: $($Results.Count)"
    
    # Count results by type
    $passedTests = ($Results | Where-Object { $_.Passed }).Count
    $failedTests = ($Results | Where-Object { !$_.Passed }).Count
    $criticalTests = ($Results | Where-Object { $_.Critical }).Count
    $criticalPassed = ($Results | Where-Object { $_.Critical -and $_.Passed }).Count
    $criticalFailed = ($Results | Where-Object { $_.Critical -and !$_.Passed }).Count
    
    Write-Host "`nTest Results:" -ForegroundColor Cyan
    Write-Host "  Total Passed: $passedTests" -ForegroundColor Green
    Write-Host "  Total Failed: $failedTests" -ForegroundColor Red
    Write-Host "  Critical Tests: $criticalTests"
    Write-Host "  Critical Passed: $criticalPassed" -ForegroundColor $(if ($criticalPassed -eq $criticalTests) { "Green" } else { "Red" })
    Write-Host "  Critical Failed: $criticalFailed" -ForegroundColor $(if ($criticalFailed -eq 0) { "Green" } else { "Red" })
    
    # Show detailed results
    Write-Host "`nDetailed Test Results:" -ForegroundColor Cyan
    foreach ($result in $Results | Sort-Object { $_.StartTime }) {
        $status = if ($result.Passed) { "✅" } else { "❌" }
        $critical = if ($result.Critical) { "[CRITICAL]" } else { "[OPTIONAL]" }
        $criticalColor = if ($result.Critical) { "Red" } else { "Yellow" }
        
        Write-Host "  $status $($result.Name) " -NoNewline
        Write-Host "$critical" -ForegroundColor $criticalColor -NoNewline
        Write-Host " ($($result.Duration)s)"
        
        if ($result.Issues.Count -gt 0) {
            Write-Host "    Issues found: $($result.Issues.Count)" -ForegroundColor Yellow
            foreach ($issue in $result.Issues | Select-Object -First 3) {
                Write-Host "      - $issue" -ForegroundColor Red
            }
            if ($result.Issues.Count -gt 3) {
                Write-Host "      ... and $($result.Issues.Count - 3) more issues" -ForegroundColor Red
            }
        }
    }
    
    # Show all issues summary
    if ($totalIssues.Count -gt 0) {
        Write-Host "`n🚨 All Issues Found ($($totalIssues.Count) total):" -ForegroundColor Red
        $issueCategories = @{}
        
        foreach ($issue in $totalIssues) {
            $category = "General"
            if ($issue -match "HIPAA|PHI") { $category = "HIPAA Compliance" }
            elseif ($issue -match "SOC2|audit") { $category = "SOC2 Compliance" }
            elseif ($issue -match "database|migration") { $category = "Database" }
            elseif ($issue -match "security|encryption|JWT") { $category = "Security" }
            elseif ($issue -match "Docker|deployment") { $category = "Deployment" }
            elseif ($issue -match "performance|load") { $category = "Performance" }
            elseif ($issue -match "monitoring|alert|metrics") { $category = "Monitoring" }
            
            if (!$issueCategories.ContainsKey($category)) {
                $issueCategories[$category] = @()
            }
            $issueCategories[$category] += $issue
        }
        
        foreach ($category in $issueCategories.Keys | Sort-Object) {
            Write-Host "`n  $category Issues:" -ForegroundColor Yellow
            foreach ($issue in $issueCategories[$category] | Sort-Object -Unique) {
                Write-Host "    - $issue" -ForegroundColor Red
            }
        }
    }
}

function Save-MasterReport {
    param([array]$Results, [string]$OverallStatus)
    
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $reportFile = "deployment_validation_master_$timestamp.json"
    
    try {
        $reportData = @{
            timestamp = $timestamp
            start_time = $startTime.ToString('yyyy-MM-dd HH:mm:ss')
            end_time = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
            total_duration_minutes = [math]::Round(((Get-Date) - $startTime).TotalMinutes, 1)
            overall_status = $OverallStatus
            summary = @{
                total_tests = $Results.Count
                passed_tests = ($Results | Where-Object { $_.Passed }).Count
                failed_tests = ($Results | Where-Object { !$_.Passed }).Count
                critical_tests = ($Results | Where-Object { $_.Critical }).Count
                critical_passed = ($Results | Where-Object { $_.Critical -and $_.Passed }).Count
                critical_failed = ($Results | Where-Object { $_.Critical -and !$_.Passed }).Count
                total_issues = $totalIssues.Count
            }
            test_results = $Results
            all_issues = $totalIssues
            deployment_readiness = @{
                production_ready = ($allTestsPassed -and $totalIssues.Count -eq 0)
                critical_systems_ok = (($Results | Where-Object { $_.Critical -and !$_.Passed }).Count -eq 0)
                issues_blocking_deployment = ($Results | Where-Object { $_.Critical -and !$_.Passed }).Count
                recommendations = @(
                    if ($totalIssues.Count -gt 0) { "Address $($totalIssues.Count) identified issues before production deployment" }
                    if (($Results | Where-Object { $_.Critical -and !$_.Passed }).Count -gt 0) { "Critical system failures must be resolved immediately" }
                    if (($Results | Where-Object { !$_.Critical -and !$_.Passed }).Count -gt 0) { "Optional system improvements recommended" }
                    "Review all test outputs and issue details"
                    "Ensure monitoring and alerting systems are operational"
                    "Verify backup and rollback procedures are tested"
                )
            }
        }
        
        $reportData | ConvertTo-Json -Depth 6 | Out-File -FilePath $reportFile -Encoding UTF8
        Write-Host "`nMaster deployment report saved to: $reportFile" -ForegroundColor Cyan
        
        # Also create a summary text report
        $summaryFile = "deployment_validation_summary_$timestamp.txt"
        $summaryContent = @"
HEALTHCARE RECORDS BACKEND - DEPLOYMENT VALIDATION SUMMARY
=========================================================

Execution Time: $($startTime.ToString('yyyy-MM-dd HH:mm:ss')) - $((Get-Date).ToString('yyyy-MM-dd HH:mm:ss'))
Total Duration: $([math]::Round(((Get-Date) - $startTime).TotalMinutes, 1)) minutes
Overall Status: $OverallStatus

TEST RESULTS SUMMARY:
- Total Tests: $($Results.Count)
- Passed: $(($Results | Where-Object { $_.Passed }).Count)
- Failed: $(($Results | Where-Object { !$_.Passed }).Count)
- Critical Tests: $(($Results | Where-Object { $_.Critical }).Count)
- Critical Passed: $(($Results | Where-Object { $_.Critical -and $_.Passed }).Count)
- Critical Failed: $(($Results | Where-Object { $_.Critical -and !$_.Passed }).Count)

DETAILED RESULTS:
$($Results | ForEach-Object { 
    $status = if ($_.Passed) { "[PASS]" } else { "[FAIL]" }
    $critical = if ($_.Critical) { "[CRITICAL]" } else { "[OPTIONAL]" }
    "$status $critical $($_.Name) ($($_.Duration)s)"
} | Out-String)

DEPLOYMENT READINESS:
- Production Ready: $(if ($allTestsPassed -and $totalIssues.Count -eq 0) { "YES" } else { "NO" })
- Critical Systems OK: $(if (($Results | Where-Object { $_.Critical -and !$_.Passed }).Count -eq 0) { "YES" } else { "NO" })
- Issues Found: $($totalIssues.Count)
- Blocking Issues: $(($Results | Where-Object { $_.Critical -and !$_.Passed }).Count)

$(if ($totalIssues.Count -gt 0) {
"ISSUES TO RESOLVE:
$(($totalIssues | ForEach-Object { "- $_" }) -join "`n")
"
})

RECOMMENDATIONS:
- Review all test outputs for detailed information
- Address critical issues before production deployment  
- Ensure monitoring systems are operational
- Test backup and rollback procedures
- Validate security and compliance requirements
"@
        
        $summaryContent | Out-File -FilePath $summaryFile -Encoding UTF8
        Write-Host "Summary report saved to: $summaryFile" -ForegroundColor Cyan
        
    }
    catch {
        Write-Host "Could not save master report: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# Main execution
Write-Host "Starting comprehensive deployment validation..." -ForegroundColor Cyan
Write-Host "This will execute all $($deploymentTests.Count) deployment validation tests in sequence.`n" -ForegroundColor Gray

# Execute all tests in order
foreach ($test in $deploymentTests | Sort-Object Order) {
    $result = Execute-DeploymentTest -TestConfig $test
    $masterResults += $result
    
    # Stop on critical failures if specified
    if (!$result.Passed -and $test.Critical) {
        Write-Host "`nCRITICAL TEST FAILURE DETECTED!" -ForegroundColor Red
        Write-Host "Test: $($test.Name)" -ForegroundColor Red
        Write-Host "This is a critical system requirement. Continuing with remaining tests for full assessment..." -ForegroundColor Yellow
    }
}

# Generate comprehensive report
Generate-DeploymentReport -Results $masterResults

# Determine overall deployment status
$overallStatus = "UNKNOWN"
$criticalFailures = ($masterResults | Where-Object { $_.Critical -and !$_.Passed }).Count
$totalFailures = ($masterResults | Where-Object { !$_.Passed }).Count

if ($criticalFailures -eq 0 -and $totalFailures -eq 0) {
    $overallStatus = "PRODUCTION_READY"
    Write-Host "`nDEPLOYMENT VALIDATION COMPLETE - PRODUCTION READY!" -ForegroundColor Green
    Write-Host "All tests passed successfully. The system is ready for production deployment." -ForegroundColor Green
} elseif ($criticalFailures -eq 0 -and $totalFailures -gt 0) {
    $overallStatus = "PRODUCTION_READY_WITH_WARNINGS"
    Write-Host "`nDEPLOYMENT VALIDATION COMPLETE - PRODUCTION READY WITH WARNINGS" -ForegroundColor Yellow
    Write-Host "Critical systems are operational but some optional features need attention." -ForegroundColor Yellow
} elseif ($criticalFailures -gt 0) {
    $overallStatus = "NOT_PRODUCTION_READY"
    Write-Host "`nDEPLOYMENT VALIDATION FAILED - NOT PRODUCTION READY" -ForegroundColor Red
    Write-Host "Critical system failures detected. Production deployment is not recommended!" -ForegroundColor Red
    Write-Host "Please resolve all critical issues before proceeding." -ForegroundColor Red
}

# Save master report
Save-MasterReport -Results $masterResults -OverallStatus $overallStatus

Write-Host "`nDeployment validation complete!" -ForegroundColor Cyan
Write-Host "Total execution time: $([math]::Round(((Get-Date) - $startTime).TotalMinutes, 1)) minutes" -ForegroundColor Gray

# Set appropriate exit code
if ($criticalFailures -gt 0) {
    exit 1
} elseif ($totalFailures -gt 0) {
    exit 2  # Warnings but not critical
} else {
    exit 0  # All tests passed
}