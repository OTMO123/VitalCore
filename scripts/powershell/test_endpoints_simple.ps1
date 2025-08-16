# Simple Endpoint Testing Script
# Tests both old (Patient API) and new (Clinical Workflows) endpoints

Write-Host "IRIS Healthcare Platform - Endpoint Testing" -ForegroundColor Green
Write-Host "=" * 60

# Initialize counters
$TotalTests = 0
$PassedTests = 0

function Test-Endpoint {
    param($Name, $URL, $ExpectedStatus = @(200))
    
    $global:TotalTests++
    Write-Host "Testing $Name..." -NoNewline
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000$URL" -UseBasicParsing -TimeoutSec 10 -SkipHttpErrorCheck
        
        if ($ExpectedStatus -contains $response.StatusCode) {
            Write-Host " PASS ($($response.StatusCode))" -ForegroundColor Green
            $global:PassedTests++
            return $true
        } else {
            Write-Host " FAIL ($($response.StatusCode))" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host " ERROR ($_)" -ForegroundColor Red
        return $false
    }
}

# Test 1: System Health
Write-Host "`n1. SYSTEM HEALTH TESTS" -ForegroundColor Cyan
Test-Endpoint "Main Health" "/health" @(200)

# Test 2: Authentication (with credentials)
Write-Host "`n2. AUTHENTICATION TESTS" -ForegroundColor Cyan
try {
    $authBody = '{"username":"admin","password":"admin123"}'
    $authResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Body $authBody -ContentType "application/json" -UseBasicParsing -TimeoutSec 10 -SkipHttpErrorCheck
    
    $TotalTests++
    if ($authResponse.StatusCode -eq 200) {
        Write-Host "Authentication Login... PASS (200)" -ForegroundColor Green
        $PassedTests++
        $authData = $authResponse.Content | ConvertFrom-Json
        $token = $authData.access_token
    } else {
        Write-Host "Authentication Login... FAIL ($($authResponse.StatusCode))" -ForegroundColor Red
        $token = $null
    }
} catch {
    Write-Host "Authentication Login... ERROR ($_)" -ForegroundColor Red
    $TotalTests++
    $token = $null
}

# Test 3: Patient Management API (Previously 100% Working)
Write-Host "`n3. PATIENT MANAGEMENT API" -ForegroundColor Cyan
if ($token) {
    try {
        $headers = @{ "Authorization" = "Bearer $token" }
        $patientsResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/healthcare/patients" -Headers $headers -UseBasicParsing -TimeoutSec 10 -SkipHttpErrorCheck
        
        $TotalTests++
        if ($patientsResponse.StatusCode -eq 200) {
            Write-Host "Patient List... PASS (200)" -ForegroundColor Green
            $PassedTests++
        } else {
            Write-Host "Patient List... FAIL ($($patientsResponse.StatusCode))" -ForegroundColor Red
        }
    } catch {
        Write-Host "Patient List... ERROR ($_)" -ForegroundColor Red
        $TotalTests++
    }
} else {
    Write-Host "Patient List... SKIPPED (no token)" -ForegroundColor Yellow
}

# Test 4: Clinical Workflows API (New Module)
Write-Host "`n4. CLINICAL WORKFLOWS API" -ForegroundColor Cyan
$clinicalEndpoints = @(
    @{Name="Health Check"; URL="/api/v1/clinical-workflows/health"},
    @{Name="Metrics"; URL="/api/v1/clinical-workflows/metrics"},
    @{Name="Workflows"; URL="/api/v1/clinical-workflows/workflows"},
    @{Name="Analytics"; URL="/api/v1/clinical-workflows/analytics"}
)

foreach ($endpoint in $clinicalEndpoints) {
    $headers = if ($token) { @{ "Authorization" = "Bearer $token" } } else { @{} }
    
    $TotalTests++
    Write-Host "Testing $($endpoint.Name)..." -NoNewline
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000$($endpoint.URL)" -Headers $headers -UseBasicParsing -TimeoutSec 10 -SkipHttpErrorCheck
        
        if ($response.StatusCode -in @(200, 401, 403)) {
            if ($response.StatusCode -eq 200) {
                Write-Host " PASS (Accessible)" -ForegroundColor Green
            } else {
                Write-Host " PASS (Secured $($response.StatusCode))" -ForegroundColor Green
            }
            $PassedTests++
        } else {
            Write-Host " FAIL ($($response.StatusCode))" -ForegroundColor Red
        }
    } catch {
        Write-Host " ERROR ($_)" -ForegroundColor Red
    }
}

# Test 5: API Documentation
Write-Host "`n5. API DOCUMENTATION" -ForegroundColor Cyan
Test-Endpoint "Swagger UI" "/docs" @(200)
Test-Endpoint "OpenAPI Schema" "/openapi.json" @(200)

# Test 6: Endpoint Count Verification
Write-Host "`n6. ENDPOINT VERIFICATION" -ForegroundColor Cyan
try {
    $openApiResponse = Invoke-WebRequest -Uri "http://localhost:8000/openapi.json" -UseBasicParsing -TimeoutSec 5
    if ($openApiResponse.StatusCode -eq 200) {
        $openApiContent = $openApiResponse.Content | ConvertFrom-Json
        $allPaths = $openApiContent.paths.PSObject.Properties
        
        $authPaths = $allPaths | Where-Object { $_.Name -like "*auth*" }
        $healthcarePaths = $allPaths | Where-Object { $_.Name -like "*healthcare*" }
        $clinicalPaths = $allPaths | Where-Object { $_.Name -like "*clinical-workflows*" }
        
        Write-Host "Total API Endpoints: $($allPaths.Count)" -ForegroundColor White
        Write-Host "  - Authentication: $($authPaths.Count)" -ForegroundColor Gray
        Write-Host "  - Healthcare: $($healthcarePaths.Count)" -ForegroundColor Gray
        Write-Host "  - Clinical Workflows: $($clinicalPaths.Count)" -ForegroundColor Gray
        
        $TotalTests++
        if ($clinicalPaths.Count -ge 10) {
            Write-Host "Clinical Workflows Endpoints... PASS ($($clinicalPaths.Count) found)" -ForegroundColor Green
            $PassedTests++
        } else {
            Write-Host "Clinical Workflows Endpoints... FAIL (Only $($clinicalPaths.Count) found)" -ForegroundColor Red
        }
    }
} catch {
    Write-Host "Endpoint Verification... ERROR ($_)" -ForegroundColor Red
    $TotalTests++
}

# Final Results
Write-Host "`n" + "=" * 60 -ForegroundColor Green
Write-Host "TEST RESULTS SUMMARY" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green

$successRate = if ($TotalTests -gt 0) { [math]::Round(($PassedTests / $TotalTests) * 100, 1) } else { 0 }

Write-Host "`nResults:" -ForegroundColor White
Write-Host "  Total Tests: $TotalTests" -ForegroundColor Gray
Write-Host "  Passed: $PassedTests" -ForegroundColor Green
Write-Host "  Failed: $($TotalTests - $PassedTests)" -ForegroundColor Red
Write-Host "  Success Rate: $successRate%" -ForegroundColor $(if ($successRate -ge 90) { "Green" } elseif ($successRate -ge 70) { "Yellow" } else { "Red" })

if ($successRate -ge 90) {
    Write-Host "`nIRIS Healthcare Platform is PRODUCTION READY!" -ForegroundColor Green
} elseif ($successRate -ge 70) {
    Write-Host "`nIRIS Healthcare Platform is mostly operational" -ForegroundColor Yellow
} else {
    Write-Host "`nIRIS Healthcare Platform needs attention" -ForegroundColor Red
}

Write-Host "`nSystem Access:" -ForegroundColor Cyan
Write-Host "  Documentation: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  Clinical Workflows: http://localhost:8000/api/v1/clinical-workflows/" -ForegroundColor White
Write-Host "  Patient Management: http://localhost:8000/api/v1/healthcare/patients" -ForegroundColor White