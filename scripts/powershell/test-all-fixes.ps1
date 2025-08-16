# Test All Enterprise Healthcare API Fixes
# Validates all security fixes and enterprise readiness

Write-Host "Test All Enterprise Healthcare API Fixes" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Gray

$baseUrl = "http://localhost:8000"
$passed = 0
$failed = 0

function Test-Fix {
    param([string]$TestName, [scriptblock]$TestCode)
    Write-Host "`n[TEST] $TestName" -ForegroundColor White
    try {
        $result = & $TestCode
        if ($result) {
            Write-Host "  PASS" -ForegroundColor Green
            $script:passed++
        } else {
            Write-Host "  FAIL" -ForegroundColor Red
            $script:failed++
        }
    } catch {
        Write-Host "  ERROR: $($_.Exception.Message)" -ForegroundColor Red
        $script:failed++
    }
}

# Test 1: Authentication HTTP status codes
Test-Fix "Authentication HTTP Status Codes (401 vs 403)" {
    try {
        # Test unauthenticated request should return 401
        $response = Invoke-WebRequest -Uri "$baseUrl/api/v1/auth/me" -Method GET -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 401) {
            Write-Host "    Returns 401 for unauthenticated requests" -ForegroundColor Green
            return $true
        } else {
            Write-Host "    Returns $($response.StatusCode) instead of 401" -ForegroundColor Red
            return $false
        }
    } catch {
        # Check if the error is 401 Unauthorized
        if ($_.Exception.Response.StatusCode -eq 401) {
            Write-Host "    Returns 401 for unauthenticated requests" -ForegroundColor Green
            return $true
        } else {
            Write-Host "    Returns $($_.Exception.Response.StatusCode) instead of 401" -ForegroundColor Red
            return $false
        }
    }
}

# Test 2: Health endpoint accessibility  
Test-Fix "Health Endpoint Accessibility" {
    try {
        $response = Invoke-RestMethod -Uri "$baseUrl/health" -Method GET
        if ($response.status -eq "ok") {
            Write-Host "    Health endpoint returns OK" -ForegroundColor Green
            return $true
        } else {
            Write-Host "    Health endpoint returns: $($response.status)" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "    Health endpoint not accessible: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Test 3: Database connectivity
Test-Fix "Database Connectivity" {
    try {
        $response = Invoke-RestMethod -Uri "$baseUrl/health/detailed" -Method GET
        if ($response.database -eq "connected") {
            Write-Host "    Database is connected" -ForegroundColor Green
            return $true
        } else {
            Write-Host "    Database status: $($response.database)" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "    Database connectivity check failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Summary
Write-Host "`n" + "=" * 50 -ForegroundColor Gray
Write-Host "TEST RESULTS SUMMARY" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Gray

$total = $passed + $failed
Write-Host "Total Tests: $total" -ForegroundColor White
Write-Host "Passed: $passed" -ForegroundColor Green  
Write-Host "Failed: $failed" -ForegroundColor Red

if ($failed -eq 0) {
    Write-Host "`nALL TESTS PASSED!" -ForegroundColor Green
    Write-Host "Enterprise Healthcare API is ready!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`nSOME TESTS FAILED!" -ForegroundColor Red
    Write-Host "Please review the failed tests above." -ForegroundColor Yellow
    exit 1
}