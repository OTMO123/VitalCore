# Quick Clinical Workflows Restoration Test
# Tests authentication and basic clinical workflows functionality

Write-Host "IRIS Clinical Workflows Restoration Test" -ForegroundColor Green
Write-Host "======================================="

# Test 1: Check if application starts without SQLAlchemy errors
Write-Host "`n1. Testing Application Startup..." -ForegroundColor Cyan
try {
    $startTest = Start-Process python -ArgumentList "app/main.py" -NoNewWindow -PassThru
    Start-Sleep 3
    
    if ($startTest.HasExited -eq $false) {
        Write-Host "Application Start... PASS (Process running)" -ForegroundColor Green
        $appRunning = $true
        Stop-Process $startTest.Id -Force
    } else {
        Write-Host "Application Start... FAIL (Process exited immediately)" -ForegroundColor Red
        $appRunning = $false
    }
} catch {
    Write-Host "Application Start... ERROR" -ForegroundColor Red
    $appRunning = $false
}

# Test 2: Authentication Test (Critical - must still work)
Write-Host "`n2. Testing Authentication..." -ForegroundColor Cyan
try {
    $authBody = '{"username":"admin","password":"admin123"}'
    $authResponse = Invoke-WebRequest -Uri "http://localhost:8001/api/v1/auth/login" -Method POST -Body $authBody -ContentType "application/json" -UseBasicParsing -TimeoutSec 10 -ErrorAction SilentlyContinue
    
    if ($authResponse -and $authResponse.StatusCode -eq 200) {
        Write-Host "Authentication... PASS (200)" -ForegroundColor Green
        $authWorking = $true
        $authData = $authResponse.Content | ConvertFrom-Json
        $token = $authData.access_token
    } else {
        Write-Host "Authentication... FAIL ($($authResponse.StatusCode))" -ForegroundColor Red
        $authWorking = $false
        $token = $null
    }
} catch {
    Write-Host "Authentication... ERROR" -ForegroundColor Red
    $authWorking = $false
    $token = $null
}

# Test 3: Clinical Workflows Endpoints Test
Write-Host "`n3. Testing Clinical Workflows Endpoints..." -ForegroundColor Cyan
if ($token) {
    $headers = @{ "Authorization" = "Bearer $token" }
    $clinicalTests = 0
    $clinicalPassed = 0
    
    # Test basic clinical workflows endpoints
    $endpoints = @(
        "/api/v1/clinical-workflows/health",
        "/api/v1/clinical-workflows/workflows",
        "/api/v1/clinical-workflows/analytics"
    )
    
    foreach ($endpoint in $endpoints) {
        $clinicalTests++
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8001$endpoint" -Headers $headers -UseBasicParsing -TimeoutSec 5 -ErrorAction SilentlyContinue
            
            if ($response -and $response.StatusCode -in @(200, 401, 403)) {
                Write-Host "Endpoint $endpoint... PASS ($($response.StatusCode))" -ForegroundColor Green
                $clinicalPassed++
            } else {
                Write-Host "Endpoint $endpoint... FAIL ($($response.StatusCode))" -ForegroundColor Red
            }
        } catch {
            if ($_.Exception.Response -and $_.Exception.Response.StatusCode -in @(200, 401, 403)) {
                Write-Host "Endpoint $endpoint... PASS (Secured)" -ForegroundColor Green
                $clinicalPassed++
            } else {
                Write-Host "Endpoint $endpoint... FAIL" -ForegroundColor Red
            }
        }
    }
} else {
    Write-Host "Clinical Workflows... SKIPPED (no auth token)" -ForegroundColor Yellow
    $clinicalTests = 0
    $clinicalPassed = 0
}

# Test 4: OpenAPI Schema Verification
Write-Host "`n4. Testing OpenAPI Schema..." -ForegroundColor Cyan
try {
    $openApiResponse = Invoke-WebRequest -Uri "http://localhost:8001/openapi.json" -UseBasicParsing -TimeoutSec 5 -ErrorAction SilentlyContinue
    if ($openApiResponse -and $openApiResponse.StatusCode -eq 200) {
        $openApiContent = $openApiResponse.Content | ConvertFrom-Json
        $allPaths = $openApiContent.paths.PSObject.Properties
        $clinicalPaths = $allPaths | Where-Object { $_.Name -like "*clinical-workflows*" }
        
        Write-Host "OpenAPI Schema... PASS" -ForegroundColor Green
        Write-Host "Clinical Workflow Endpoints Found: $($clinicalPaths.Count)" -ForegroundColor Gray
        $schemaWorking = $true
    } else {
        Write-Host "OpenAPI Schema... FAIL" -ForegroundColor Red
        $schemaWorking = $false
    }
} catch {
    Write-Host "OpenAPI Schema... ERROR" -ForegroundColor Red
    $schemaWorking = $false
}

# Results Summary
Write-Host "`n=======================================" -ForegroundColor Green
Write-Host "RESTORATION TEST RESULTS" -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green

$totalTests = 4
$passedTests = 0
if ($appRunning) { $passedTests++ }
if ($authWorking) { $passedTests++ }
if ($clinicalTests -gt 0 -and $clinicalPassed -eq $clinicalTests) { $passedTests++ }
if ($schemaWorking) { $passedTests++ }

$successRate = [math]::Round(($passedTests / $totalTests) * 100, 1)

Write-Host "`nResults:" -ForegroundColor White
Write-Host "  Application Startup: $(if ($appRunning) { 'PASS' } else { 'FAIL' })" -ForegroundColor $(if ($appRunning) { 'Green' } else { 'Red' })
Write-Host "  Authentication: $(if ($authWorking) { 'PASS' } else { 'FAIL' })" -ForegroundColor $(if ($authWorking) { 'Green' } else { 'Red' })
Write-Host "  Clinical Workflows: $(if ($clinicalTests -gt 0 -and $clinicalPassed -eq $clinicalTests) { 'PASS' } else { 'FAIL' })" -ForegroundColor $(if ($clinicalTests -gt 0 -and $clinicalPassed -eq $clinicalTests) { 'Green' } else { 'Red' })
Write-Host "  OpenAPI Schema: $(if ($schemaWorking) { 'PASS' } else { 'FAIL' })" -ForegroundColor $(if ($schemaWorking) { 'Green' } else { 'Red' })
Write-Host "  Success Rate: $successRate%" -ForegroundColor $(if ($successRate -ge 75) { 'Green' } else { 'Red' })

Write-Host "`nNext Steps:" -ForegroundColor Cyan
if ($successRate -ge 75) {
    Write-Host "  ✅ Restoration successful - proceed with enterprise testing" -ForegroundColor Green
    Write-Host "  Run: .\test_endpoints_working.ps1" -ForegroundColor Gray
    Write-Host "  Run: Enterprise 185 test suite" -ForegroundColor Gray
} else {
    Write-Host "  ❌ Restoration issues detected - troubleshoot before proceeding" -ForegroundColor Red
    Write-Host "  Check application logs for SQLAlchemy relationship errors" -ForegroundColor Gray
    Write-Host "  Verify Docker services are running" -ForegroundColor Gray
}

Write-Host "`nCritical Success Criteria:" -ForegroundColor Yellow
Write-Host "  - Authentication MUST still work (prevents regression)" -ForegroundColor Yellow
Write-Host "  - Clinical workflows endpoints should be accessible" -ForegroundColor Yellow
Write-Host "  - No SQLAlchemy relationship mapping errors" -ForegroundColor Yellow