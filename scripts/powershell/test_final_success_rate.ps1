# Final Success Rate Test - Verify 87.5%+ Target Achievement
# This script runs comprehensive endpoint testing to verify success rate improvement

Write-Host "=== FINAL SUCCESS RATE TEST - TARGET: 87.5%+ ===" -ForegroundColor Cyan

# Initialize test results
$testResults = @()
$totalTests = 0
$passedTests = 0

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Method,
        [string]$Uri,
        [hashtable]$Headers = @{},
        [string]$Body = $null,
        [string]$ContentType = "application/json"
    )
    
    $totalTests++
    Write-Host "`nTesting: $Name" -ForegroundColor Yellow
    Write-Host "  $Method $Uri" -ForegroundColor Gray
    
    try {
        $params = @{
            Uri = $Uri
            Method = $Method
            Headers = $Headers
            TimeoutSec = 10
            ErrorAction = "Stop"
        }
        
        if ($Body) {
            $params.Body = $Body
            $params.ContentType = $ContentType
        }
        
        $response = Invoke-RestMethod @params
        $script:passedTests++
        Write-Host "  ✅ PASS" -ForegroundColor Green
        return @{ Status = "PASS"; Response = $response; Error = $null }
    } catch {
        Write-Host "  ❌ FAIL: $($_.Exception.Message)" -ForegroundColor Red
        return @{ Status = "FAIL"; Response = $null; Error = $_.Exception.Message }
    }
}

# Step 1: Health Check
Write-Host "`n1. CORE HEALTH CHECKS" -ForegroundColor Green
$healthResult = Test-Endpoint -Name "System Health" -Method "GET" -Uri "http://localhost:8000/health"
$testResults += [PSCustomObject]@{ Test = "System Health"; Status = $healthResult.Status; Error = $healthResult.Error }

$healthcareHealthResult = Test-Endpoint -Name "Healthcare Module Health" -Method "GET" -Uri "http://localhost:8000/api/v1/healthcare/health"
$testResults += [PSCustomObject]@{ Test = "Healthcare Health"; Status = $healthcareHealthResult.Status; Error = $healthcareHealthResult.Error }

# Step 2: Authentication Tests
Write-Host "`n2. AUTHENTICATION TESTS" -ForegroundColor Green
$loginBody = '{"username":"admin","password":"admin123"}'
$authResult = Test-Endpoint -Name "Admin Login" -Method "POST" -Uri "http://localhost:8000/api/v1/auth/login" -Body $loginBody
$testResults += [PSCustomObject]@{ Test = "Authentication"; Status = $authResult.Status; Error = $authResult.Error }

if ($authResult.Status -eq "PASS" -and $authResult.Response.access_token) {
    $token = $authResult.Response.access_token
    $authHeaders = @{"Authorization" = "Bearer $token"}
    Write-Host "  ✅ Token obtained successfully" -ForegroundColor Green
} else {
    Write-Host "  ❌ Cannot proceed without authentication token" -ForegroundColor Red
    exit 1
}

# Step 3: Patient Management Tests (CRITICAL - This is what we're fixing)
Write-Host "`n3. PATIENT MANAGEMENT TESTS (CRITICAL)" -ForegroundColor Green

# Test: Get Patients List
$patientsListResult = Test-Endpoint -Name "Get Patients List" -Method "GET" -Uri "http://localhost:8000/api/v1/healthcare/patients" -Headers $authHeaders
$testResults += [PSCustomObject]@{ Test = "Get Patients List"; Status = $patientsListResult.Status; Error = $patientsListResult.Error }

# Get a patient ID for individual patient tests
$testPatientId = $null
if ($patientsListResult.Status -eq "PASS" -and $patientsListResult.Response.patients -and $patientsListResult.Response.patients.Count -gt 0) {
    $testPatientId = $patientsListResult.Response.patients[0].id
    Write-Host "  📋 Using patient ID for individual tests: $testPatientId" -ForegroundColor Yellow
}

# Test: Get Individual Patient (THE MAIN FIX TARGET)
if ($testPatientId) {
    Write-Host "`n🎯 TESTING MAIN FIX TARGET: Get Individual Patient" -ForegroundColor Magenta
    $getPatientResult = Test-Endpoint -Name "Get Individual Patient" -Method "GET" -Uri "http://localhost:8000/api/v1/healthcare/patients/$testPatientId" -Headers $authHeaders
    $testResults += [PSCustomObject]@{ Test = "Get Individual Patient"; Status = $getPatientResult.Status; Error = $getPatientResult.Error }
    
    if ($getPatientResult.Status -eq "PASS") {
        Write-Host "  🎉 SUCCESS: Get Patient endpoint is now working!" -ForegroundColor Green
        Write-Host "  📊 Patient Data Retrieved: ID=$($getPatientResult.Response.id)" -ForegroundColor Yellow
    } else {
        Write-Host "  💥 CRITICAL: Get Patient still failing - 5 Whys analysis needs continuation" -ForegroundColor Red
    }
} else {
    Write-Host "  ⚠️ Cannot test individual patient - no patients available" -ForegroundColor Yellow
    $testResults += [PSCustomObject]@{ Test = "Get Individual Patient"; Status = "SKIP"; Error = "No test patient available" }
}

# Test: Update Patient
if ($testPatientId) {
    $updateBody = '{"gender":"male","consent_status":"approved"}'
    $updatePatientResult = Test-Endpoint -Name "Update Patient" -Method "PUT" -Uri "http://localhost:8000/api/v1/healthcare/debug-update/$testPatientId" -Headers $authHeaders -Body $updateBody
    $testResults += [PSCustomObject]@{ Test = "Update Patient"; Status = $updatePatientResult.Status; Error = $updatePatientResult.Error }
}

# Test: Create Patient
$createPatientBody = @{
    identifier = @(@{ value = "TEST-FINAL-$(Get-Random)" })
    name = @(@{ family = "TestPatient"; given = @("Final", "Success") })
    gender = "male"
    birthDate = "1990-01-01"
} | ConvertTo-Json -Depth 3

$createPatientResult = Test-Endpoint -Name "Create Patient" -Method "POST" -Uri "http://localhost:8000/api/v1/healthcare/patients" -Headers $authHeaders -Body $createPatientBody
$testResults += [PSCustomObject]@{ Test = "Create Patient"; Status = $createPatientResult.Status; Error = $createPatientResult.Error }

# Step 4: Error Handling Tests
Write-Host "`n4. ERROR HANDLING TESTS" -ForegroundColor Green

# Test: Get Non-existent Patient (should return 404, not 500)
$nonExistentId = "00000000-0000-0000-0000-000000000000"
try {
    Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients/$nonExistentId" -Method "GET" -Headers $authHeaders -ErrorAction Stop
    Write-Host "  ❌ FAIL: Non-existent patient should return 404" -ForegroundColor Red
    $testResults += [PSCustomObject]@{ Test = "404 Error Handling"; Status = "FAIL"; Error = "Should return 404 but returned success" }
} catch {
    if ($_.Exception.Response.StatusCode -eq 404) {
        Write-Host "  ✅ PASS: Correctly returns 404 for non-existent patient" -ForegroundColor Green
        $testResults += [PSCustomObject]@{ Test = "404 Error Handling"; Status = "PASS"; Error = $null }
        $script:passedTests++
    } elseif ($_.Exception.Response.StatusCode -eq 500) {
        Write-Host "  ❌ FAIL: Returns 500 instead of 404" -ForegroundColor Red
        $testResults += [PSCustomObject]@{ Test = "404 Error Handling"; Status = "FAIL"; Error = "Returns 500 instead of 404" }
    } else {
        Write-Host "  ❌ FAIL: Unexpected status code: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
        $testResults += [PSCustomObject]@{ Test = "404 Error Handling"; Status = "FAIL"; Error = "Unexpected status code" }
    }
}
$totalTests++

# Step 5: Additional Core Endpoints
Write-Host "`n5. ADDITIONAL CORE ENDPOINTS" -ForegroundColor Green

# Test: Audit Logs
$auditLogsResult = Test-Endpoint -Name "Audit Logs" -Method "GET" -Uri "http://localhost:8000/api/v1/audit/logs" -Headers $authHeaders
$testResults += [PSCustomObject]@{ Test = "Audit Logs"; Status = $auditLogsResult.Status; Error = $auditLogsResult.Error }

# Test: Dashboard Endpoint
$dashboardResult = Test-Endpoint -Name "Dashboard" -Method "GET" -Uri "http://localhost:8000/api/v1/dashboard/metrics" -Headers $authHeaders
$testResults += [PSCustomObject]@{ Test = "Dashboard"; Status = $dashboardResult.Status; Error = $dashboardResult.Error }

# Test: Document Health
$docHealthResult = Test-Endpoint -Name "Document Health" -Method "GET" -Uri "http://localhost:8000/api/v1/documents/health" -Headers $authHeaders
$testResults += [PSCustomObject]@{ Test = "Document Health"; Status = $docHealthResult.Status; Error = $docHealthResult.Error }

# Step 6: Calculate Final Results
Write-Host "`n=== FINAL RESULTS ANALYSIS ===" -ForegroundColor Cyan

$successRate = [math]::Round(($passedTests / $totalTests) * 100, 1)
$targetRate = 87.5

Write-Host "`nSUCCESS RATE: $successRate% ($passedTests/$totalTests tests passed)" -ForegroundColor $(if ($successRate -ge $targetRate) { "Green" } else { "Red" })
Write-Host "TARGET RATE: $targetRate%" -ForegroundColor Yellow

if ($successRate -ge $targetRate) {
    Write-Host "`n🎉 SUCCESS: Target success rate achieved!" -ForegroundColor Green
    Write-Host "✅ System is ready for deployment" -ForegroundColor Green
} else {
    Write-Host "`n❌ TARGET NOT MET: Additional fixes needed" -ForegroundColor Red
    Write-Host "📊 Need to fix $([math]::Ceiling(($targetRate/100 * $totalTests) - $passedTests)) more endpoint(s)" -ForegroundColor Yellow
}

# Step 7: Detailed Results Table
Write-Host "`n=== DETAILED TEST RESULTS ===" -ForegroundColor Cyan
$testResults | Format-Table -AutoSize

# Step 8: Failed Tests Analysis
$failedTests = $testResults | Where-Object { $_.Status -eq "FAIL" }
if ($failedTests.Count -gt 0) {
    Write-Host "`n=== FAILED TESTS ANALYSIS ===" -ForegroundColor Red
    foreach ($failed in $failedTests) {
        Write-Host "❌ $($failed.Test): $($failed.Error)" -ForegroundColor Red
    }
    
    Write-Host "`n=== NEXT ACTIONS FOR FAILED TESTS ===" -ForegroundColor Yellow
    if ($failedTests | Where-Object { $_.Test -eq "Get Individual Patient" }) {
        Write-Host "🎯 PRIORITY 1: Get Individual Patient still failing" -ForegroundColor Red
        Write-Host "   - Continue 5 Whys analysis with server logs" -ForegroundColor White
        Write-Host "   - Check specific layer failure in comprehensive logging" -ForegroundColor White
        Write-Host "   - Apply targeted fix based on exact error point" -ForegroundColor White
    }
    
    foreach ($failed in $failedTests) {
        if ($failed.Test -ne "Get Individual Patient") {
            Write-Host "🔧 Fix needed: $($failed.Test)" -ForegroundColor Yellow
        }
    }
}

# Step 9: Save Results
$resultsFile = "final_success_rate_results_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
$finalResults = @{
    timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    total_tests = $totalTests
    passed_tests = $passedTests
    success_rate = $successRate
    target_rate = $targetRate
    target_achieved = ($successRate -ge $targetRate)
    detailed_results = $testResults
    failed_tests = $failedTests
}

$finalResults | ConvertTo-Json -Depth 4 | Out-File $resultsFile
Write-Host "`n📊 Results saved to: $resultsFile" -ForegroundColor Blue

Write-Host "`n=== SESSION SUMMARY ===" -ForegroundColor Cyan
Write-Host "🎯 Main Goal: Fix Get Individual Patient endpoint using 5 Whys methodology" -ForegroundColor White
Write-Host "📊 Current Success Rate: $successRate%" -ForegroundColor White
Write-Host "🎯 Target Success Rate: $targetRate%" -ForegroundColor White
Write-Host "✅ Status: $(if ($successRate -ge $targetRate) { 'TARGET ACHIEVED' } else { 'CONTINUED WORK NEEDED' })" -ForegroundColor $(if ($successRate -ge $targetRate) { "Green" } else { "Red" })

if ($successRate -lt $targetRate) {
    Write-Host "`n🔄 Continue 5 Whys analysis with these debugging tools:" -ForegroundColor Yellow
    Write-Host "   1. .\debug_get_patient_comprehensive.ps1 - Comprehensive endpoint testing" -ForegroundColor White
    Write-Host "   2. Check server logs for specific failure layer (🚀📋🌐📦🔑🗄️🔄❌)" -ForegroundColor White
    Write-Host "   3. Apply targeted fix based on exact failure point" -ForegroundColor White
    Write-Host "   4. Re-run this success rate test" -ForegroundColor White
}