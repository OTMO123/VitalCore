# Simple Test Script for Healthcare API
# Tests basic functionality after startup

Write-Host "Simple Healthcare API Test" -ForegroundColor Cyan
Write-Host "==========================" -ForegroundColor Gray

$baseUrl = "http://localhost:8000"
$testsPassed = 0
$testsFailed = 0

function Test-Endpoint {
    param([string]$Name, [string]$Url, [string]$ExpectedStatus = "200")
    
    Write-Host "`nTesting: $Name" -ForegroundColor White
    try {
        if ($ExpectedStatus -eq "401") {
            # Test for 401 Unauthorized
            try {
                Invoke-RestMethod -Uri $Url -TimeoutSec 10
                Write-Host "  FAIL: Should have returned 401" -ForegroundColor Red
                $script:testsFailed++
            } catch {
                if ($_.Exception.Response.StatusCode -eq 401) {
                    Write-Host "  PASS: Returns 401 as expected" -ForegroundColor Green
                    $script:testsPassed++
                } else {
                    Write-Host "  FAIL: Returned $($_.Exception.Response.StatusCode) instead of 401" -ForegroundColor Red
                    $script:testsFailed++
                }
            }
        } else {
            # Test for successful response
            $response = Invoke-RestMethod -Uri $Url -TimeoutSec 10
            Write-Host "  PASS: Endpoint responding" -ForegroundColor Green
            $script:testsPassed++
        }
    } catch {
        Write-Host "  FAIL: $($_.Exception.Message)" -ForegroundColor Red
        $script:testsFailed++
    }
}

# Test 1: Health endpoint
Test-Endpoint "Health Check" "$baseUrl/health"

# Test 2: API documentation
Test-Endpoint "API Documentation" "$baseUrl/docs"

# Test 3: Authentication required endpoint (should return 401)
Test-Endpoint "Auth Required Endpoint" "$baseUrl/api/v1/auth/me" "401"

# Test 4: Database health
Write-Host "`nTesting: Database Connection" -ForegroundColor White
try {
    $healthResponse = Invoke-RestMethod -Uri "$baseUrl/health/detailed" -TimeoutSec 10
    if ($healthResponse.database -eq "connected") {
        Write-Host "  PASS: Database connected" -ForegroundColor Green
        $testsPassed++
    } else {
        Write-Host "  FAIL: Database not connected" -ForegroundColor Red
        $testsFailed++
    }
} catch {
    Write-Host "  FAIL: Database health check failed" -ForegroundColor Red
    $testsFailed++
}

# Test 5: Authentication flow
Write-Host "`nTesting: Authentication Flow" -ForegroundColor White
try {
    $loginData = '{"username": "admin", "password": "Admin123!"}'
    $authResponse = Invoke-RestMethod -Uri "$baseUrl/api/v1/auth/login" -Method POST -Body $loginData -ContentType "application/json" -TimeoutSec 10
    
    if ($authResponse.access_token) {
        Write-Host "  PASS: Authentication successful" -ForegroundColor Green
        $testsPassed++
        
        # Test authenticated endpoint
        $headers = @{ "Authorization" = "Bearer $($authResponse.access_token)" }
        $userResponse = Invoke-RestMethod -Uri "$baseUrl/api/v1/auth/me" -Headers $headers -TimeoutSec 10
        
        if ($userResponse.username -eq "admin") {
            Write-Host "  PASS: Authenticated endpoint access" -ForegroundColor Green
            $testsPassed++
        } else {
            Write-Host "  FAIL: Authenticated endpoint failed" -ForegroundColor Red
            $testsFailed++
        }
    } else {
        Write-Host "  FAIL: No access token received" -ForegroundColor Red
        $testsFailed++
    }
} catch {
    Write-Host "  FAIL: Authentication failed - $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

# Summary
Write-Host "`n" + "=" * 30 -ForegroundColor Gray
Write-Host "TEST SUMMARY" -ForegroundColor Cyan
Write-Host "=" * 30 -ForegroundColor Gray

$totalTests = $testsPassed + $testsFailed
Write-Host "Total Tests: $totalTests" -ForegroundColor White
Write-Host "Passed: $testsPassed" -ForegroundColor Green
Write-Host "Failed: $testsFailed" -ForegroundColor Red

if ($testsFailed -eq 0) {
    Write-Host "`nALL TESTS PASSED!" -ForegroundColor Green
    Write-Host "Healthcare API is working correctly!" -ForegroundColor Green
    Write-Host ""
    Write-Host "You can now run your advanced tests:" -ForegroundColor Yellow
    Write-Host "  .\validate-role-based-security.ps1" -ForegroundColor White
    Write-Host "  .\validate_core_security_fixes.ps1" -ForegroundColor White
} else {
    Write-Host "`nSome tests failed. Check the API status:" -ForegroundColor Red
    Write-Host "  docker-compose ps" -ForegroundColor White
    Write-Host "  docker-compose logs app" -ForegroundColor White
}