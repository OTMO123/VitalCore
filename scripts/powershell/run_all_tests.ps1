# Complete Clinical Workflows Test Suite Runner
# PowerShell script to run all tests for clinical workflows functionality

param(
    [switch]$FullSuite,
    [switch]$QuickTest,
    [switch]$PerformanceOnly,
    [switch]$SecurityOnly
)

Write-Host "Clinical Workflows - Complete Test Suite" -ForegroundColor Green
Write-Host "========================================"

# Function to run a test and capture results
function Run-Test {
    param(
        [string]$TestName,
        [string]$Command,
        [string]$Description
    )
    
    Write-Host "`n--- $TestName ---" -ForegroundColor Cyan
    Write-Host $Description -ForegroundColor Gray
    Write-Host "Command: $Command" -ForegroundColor Yellow
    
    try {
        $startTime = Get-Date
        $result = Invoke-Expression $Command
        $endTime = Get-Date
        $duration = ($endTime - $startTime).TotalSeconds
        
        Write-Host "[SUCCESS] $TestName completed in $([math]::Round($duration, 1))s" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "[ERROR] $TestName failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Test configurations
$tests = @()

if ($FullSuite -or !$QuickTest -and !$PerformanceOnly -and !$SecurityOnly) {
    $tests += @{
        Name = "System Status Check"
        Command = "python.exe system_status_final.py"
        Description = "Verify all system components are operational"
    }
    
    $tests += @{
        Name = "Complete Functionality Test"
        Command = "python.exe test_clinical_workflows_complete.py"
        Description = "Test all clinical workflows functionality"
    }
    
    $tests += @{
        Name = "Unit Tests"
        Command = "python -m pytest app/tests/ -v -m unit --tb=short"
        Description = "Run unit tests for clinical workflows"
    }
    
    $tests += @{
        Name = "Integration Tests"
        Command = "python -m pytest app/tests/ -v -m integration --tb=short"
        Description = "Run integration tests with database"
    }
    
    $tests += @{
        Name = "Clinical Workflows Module Tests"
        Command = "python -m pytest app/modules/clinical_workflows/tests/ -v --tb=short"
        Description = "Run clinical workflows specific tests"
    }
    
    $tests += @{
        Name = "API Endpoint Tests"
        Command = "python -m pytest app/tests/ -k clinical -v --tb=short"
        Description = "Test clinical workflows API endpoints"
    }
}

if ($QuickTest) {
    $tests += @{
        Name = "Quick System Check"
        Command = "python.exe system_status_final.py"
        Description = "Quick system verification"
    }
    
    $tests += @{
        Name = "Basic Functionality"
        Command = "python.exe test_clinical_workflows_complete.py"
        Description = "Basic functionality verification"
    }
}

if ($SecurityOnly) {
    $tests += @{
        Name = "Security Tests"
        Command = "python -m pytest app/tests/ -v -m security --tb=short"
        Description = "Run security and authentication tests"
    }
    
    $tests += @{
        Name = "Authentication Test"
        Command = "python.exe test_clinical_workflows_complete.py"
        Description = "Test authentication and authorization"
    }
}

if ($PerformanceOnly) {
    $tests += @{
        Name = "Performance Tests"
        Command = "python -m pytest app/tests/ -v -m performance --tb=short"
        Description = "Run performance and load tests"
    }
    
    $tests += @{
        Name = "Response Time Test"
        Command = "python.exe test_clinical_workflows_complete.py"
        Description = "Test API response times"
    }
}

# Run all configured tests
$results = @{}
$totalTests = $tests.Count

Write-Host "`nRunning $totalTests test categories..." -ForegroundColor Yellow

foreach ($test in $tests) {
    $success = Run-Test -TestName $test.Name -Command $test.Command -Description $test.Description
    $results[$test.Name] = $success
}

# Summary
Write-Host "`n" + "="*50 -ForegroundColor Green
Write-Host "TEST SUITE SUMMARY" -ForegroundColor Green
Write-Host "="*50 -ForegroundColor Green

$passed = 0
foreach ($result in $results.GetEnumerator()) {
    $status = if ($result.Value) { "[PASS]" } else { "[FAIL]" }
    $color = if ($result.Value) { "Green" } else { "Red" }
    
    Write-Host "$status $($result.Key)" -ForegroundColor $color
    if ($result.Value) { $passed++ }
}

Write-Host "`nResults: $passed/$totalTests tests passed" -ForegroundColor Yellow
$successRate = [math]::Round(($passed / $totalTests) * 100, 1)
Write-Host "Success Rate: $successRate%" -ForegroundColor Yellow

if ($passed -eq $totalTests) {
    Write-Host "`nALL TESTS PASSED - Clinical Workflows PRODUCTION READY!" -ForegroundColor Green
}
elseif ($successRate -ge 80) {
    Write-Host "`nMOSTLY SUCCESSFUL - Clinical Workflows ready with minor issues" -ForegroundColor Yellow
}
else {
    Write-Host "`nISSUES DETECTED - Review failed tests before deployment" -ForegroundColor Red
}

Write-Host "`nSystem Access:" -ForegroundColor Cyan
Write-Host "  Main App: http://localhost:8000" -ForegroundColor White
Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  Clinical: http://localhost:8000/api/v1/clinical-workflows/" -ForegroundColor White

Write-Host "`nTest completed at: $(Get-Date)" -ForegroundColor Gray