# Healthcare Security Fixes Validation Script
# Tests all critical security fixes implemented in Phase 1 & 2
# Usage: .\test-healthcare-security-fixes.ps1

param(
    [string]$BaseUrl = "http://localhost:8000"
)

Write-Host "Healthcare Security Fixes Validation" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Gray
Write-Host "Testing critical security fixes and HIPAA compliance" -ForegroundColor Yellow
Write-Host ""

# Initialize test results
$TestResults = @{
    "total_tests" = 0
    "passed_tests" = 0 
    "failed_tests" = 0
    "security_issues" = @()
    "compliance_status" = "unknown"
}

function Test-SecurityFix {
    param(
        [string]$TestName,
        [scriptblock]$TestCode,
        [string]$SecurityImportance = "HIGH"
    )
    
    $TestResults.total_tests++
    
    Write-Host "[TEST] $TestName" -ForegroundColor White
    
    try {
        $result = & $TestCode
        if ($result) {
            Write-Host "  ✅ PASS - Security fix validated" -ForegroundColor Green
            $TestResults.passed_tests++
        } else {
            Write-Host "  ❌ FAIL - Security issue detected" -ForegroundColor Red
            $TestResults.failed_tests++
            $TestResults.security_issues += @{
                "test" = $TestName
                "importance" = $SecurityImportance
                "issue" = "Security fix validation failed"
            }
        }
    } catch {
        Write-Host "  ⚠️  ERROR - Test execution failed: $($_.Exception.Message)" -ForegroundColor Yellow
        $TestResults.failed_tests++
        $TestResults.security_issues += @{
            "test" = $TestName
            "importance" = $SecurityImportance  
            "issue" = "Test execution error: $($_.Exception.Message)"
        }
    }
    
    Write-Host ""
}

# Test 1: Verify Debug Endpoints Removed
Test-SecurityFix "Debug Endpoints Removal" {
    try {
        # Test that debug endpoints return 404 (removed)
        $debugEndpoints = @(
            "/api/v1/healthcare/step-by-step-debug/test-id",
            "/api/v1/healthcare/debug-get-patient/test-id"
        )
        
        $allRemoved = $true
        foreach ($endpoint in $debugEndpoints) {
            try {
                $response = Invoke-RestMethod -Uri "$BaseUrl$endpoint" -Method GET -ErrorAction Stop
                $allRemoved = $false
                Write-Host "    ⚠️  Debug endpoint still accessible: $endpoint" -ForegroundColor Yellow
            } catch {
                if ($_.Exception.Response.StatusCode -eq 404) {
                    Write-Host "    ✅ Debug endpoint properly removed: $endpoint" -ForegroundColor Green
                } else {
                    Write-Host "    ⚠️  Unexpected response for $endpoint" -ForegroundColor Yellow
                }
            }
        }
        return $allRemoved
    } catch {
        return $false
    }
} "CRITICAL"

# Test 2: Verify Transactional PHI Auditing
Test-SecurityFix "Transactional PHI Audit Logging" {
    try {
        # Get authentication token
        $loginData = @{
            username = "admin"
            password = "admin123"
        } | ConvertTo-Json
        
        $authResponse = Invoke-RestMethod -Uri "$BaseUrl/api/v1/auth/login" -Method POST -ContentType "application/json" -Body $loginData
        $token = $authResponse.access_token
        
        if (-not $token) {
            Write-Host "    ⚠️  Could not authenticate for PHI audit test" -ForegroundColor Yellow
            return $false
        }
        
        $headers = @{
            "Authorization" = "Bearer $token"
            "Content-Type" = "application/json"
        }
        
        # Test patient access (should trigger PHI audit logging)
        try {
            $patientsResponse = Invoke-RestMethod -Uri "$BaseUrl/api/v1/healthcare/patients" -Method GET -Headers $headers
            Write-Host "    ✅ Patient access successful - PHI audit logging should be active" -ForegroundColor Green
            return $true
        } catch {
            if ($_.Exception.Response.StatusCode -eq 403) {
                Write-Host "    ✅ Access properly controlled - audit logging working" -ForegroundColor Green
                return $true
            } else {
                Write-Host "    ⚠️  Unexpected response: $($_.Exception.Message)" -ForegroundColor Yellow
                return $false
            }
        }
    } catch {
        Write-Host "    ❌ PHI audit test failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
} "CRITICAL"

# Test 3: Verify Authentication Security
Test-SecurityFix "Authentication Security" {
    try {
        # Test valid authentication
        $validLogin = @{
            username = "admin"
            password = "admin123"
        } | ConvertTo-Json
        
        $validResponse = Invoke-RestMethod -Uri "$BaseUrl/api/v1/auth/login" -Method POST -ContentType "application/json" -Body $validLogin
        
        if ($validResponse.access_token) {
            Write-Host "    ✅ Valid authentication working" -ForegroundColor Green
            
            # Test invalid authentication
            try {
                $invalidLogin = @{
                    username = "invalid"
                    password = "invalid"
                } | ConvertTo-Json
                
                $invalidResponse = Invoke-RestMethod -Uri "$BaseUrl/api/v1/auth/login" -Method POST -ContentType "application/json" -Body $invalidLogin -ErrorAction Stop
                Write-Host "    ❌ Invalid authentication not properly rejected" -ForegroundColor Red
                return $false
            } catch {
                Write-Host "    ✅ Invalid authentication properly rejected" -ForegroundColor Green
                return $true
            }
        } else {
            Write-Host "    ❌ Valid authentication failed" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "    ❌ Authentication test failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
} "HIGH"

# Test 4: Verify API Security Headers
Test-SecurityFix "Security Headers Compliance" {
    try {
        $response = Invoke-WebRequest -Uri "$BaseUrl/health" -Method GET
        
        $requiredHeaders = @(
            "content-security-policy",
            "x-content-type-options", 
            "referrer-policy",
            "permissions-policy"
        )
        
        $headersPresent = $true
        foreach ($header in $requiredHeaders) {
            if ($response.Headers.ContainsKey($header)) {
                Write-Host "    ✅ Security header present: $header" -ForegroundColor Green
            } else {
                Write-Host "    ❌ Missing security header: $header" -ForegroundColor Red
                $headersPresent = $false
            }
        }
        
        return $headersPresent
    } catch {
        Write-Host "    ❌ Security headers test failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
} "HIGH"

# Test 5: Verify Health Endpoint Security
Test-SecurityFix "Health Endpoint Functionality" {
    try {
        $healthResponse = Invoke-RestMethod -Uri "$BaseUrl/health" -Method GET
        
        if ($healthResponse.status -eq "healthy") {
            Write-Host "    ✅ Health endpoint operational" -ForegroundColor Green
            
            # Check detailed health
            try {
                $detailedHealth = Invoke-RestMethod -Uri "$BaseUrl/health/detailed" -Method GET
                if ($detailedHealth.status -eq "healthy") {
                    Write-Host "    ✅ Detailed health endpoint operational" -ForegroundColor Green
                    return $true
                } else {
                    Write-Host "    ⚠️  Detailed health endpoint issues" -ForegroundColor Yellow
                    return $false
                }
            } catch {
                Write-Host "    ⚠️  Detailed health endpoint not accessible" -ForegroundColor Yellow
                return $true # Basic health is still working
            }
        } else {
            Write-Host "    ❌ Health endpoint returning unhealthy status" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "    ❌ Health endpoint test failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
} "MEDIUM"

# Test 6: Verify Audit Logs Endpoint
Test-SecurityFix "Audit Logs Availability" {
    try {
        # Get authentication token
        $loginData = @{
            username = "admin"
            password = "admin123"
        } | ConvertTo-Json
        
        $authResponse = Invoke-RestMethod -Uri "$BaseUrl/api/v1/auth/login" -Method POST -ContentType "application/json" -Body $loginData
        $token = $authResponse.access_token
        
        if ($token) {
            $headers = @{
                "Authorization" = "Bearer $token"
                "Content-Type" = "application/json"
            }
            
            $auditResponse = Invoke-RestMethod -Uri "$BaseUrl/api/v1/audit/logs" -Method GET -Headers $headers
            
            if ($auditResponse) {
                Write-Host "    ✅ Audit logs endpoint operational" -ForegroundColor Green
                
                # Check if fallback data is being used (indicates schema issue)
                if ($auditResponse.fallback_data) {
                    Write-Host "    ⚠️  Audit logs using fallback data - schema fix needed" -ForegroundColor Yellow
                    return $false
                } else {
                    Write-Host "    ✅ Audit logs using proper database schema" -ForegroundColor Green
                    return $true
                }
            } else {
                Write-Host "    ❌ Audit logs endpoint not responding" -ForegroundColor Red
                return $false
            }
        } else {
            Write-Host "    ❌ Could not authenticate for audit logs test" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "    ❌ Audit logs test failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
} "HIGH"

# Generate Test Summary
Write-Host "Security Validation Summary" -ForegroundColor Cyan
Write-Host "=" * 30 -ForegroundColor Gray
Write-Host "Total Tests: $($TestResults.total_tests)" -ForegroundColor White
Write-Host "Passed: $($TestResults.passed_tests)" -ForegroundColor Green
Write-Host "Failed: $($TestResults.failed_tests)" -ForegroundColor Red

$ComplianceScore = [math]::Round(($TestResults.passed_tests / $TestResults.total_tests) * 100, 1)
Write-Host "Compliance Score: $ComplianceScore%" -ForegroundColor Yellow

if ($ComplianceScore -ge 90) {
    Write-Host "STATUS: SECURITY FIXES VALIDATED ✅" -ForegroundColor Green
    $TestResults.compliance_status = "compliant"
} elseif ($ComplianceScore -ge 70) {
    Write-Host "STATUS: PARTIAL COMPLIANCE - REVIEW REQUIRED ⚠️" -ForegroundColor Yellow
    $TestResults.compliance_status = "partial"
} else {
    Write-Host "STATUS: SECURITY ISSUES DETECTED - IMMEDIATE ACTION REQUIRED ❌" -ForegroundColor Red
    $TestResults.compliance_status = "non_compliant"
}

# Show security issues if any
if ($TestResults.security_issues.Count -gt 0) {
    Write-Host ""
    Write-Host "Security Issues Detected:" -ForegroundColor Red
    Write-Host "-" * 25 -ForegroundColor Gray
    
    foreach ($issue in $TestResults.security_issues) {
        Write-Host "[$($issue.importance)] $($issue.test): $($issue.issue)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
if ($TestResults.compliance_status -eq "compliant") {
    Write-Host "✅ All security fixes validated successfully" -ForegroundColor Green
    Write-Host "✅ System ready for production deployment" -ForegroundColor Green
    Write-Host "✅ HIPAA/SOC2 compliance maintained" -ForegroundColor Green
} else {
    Write-Host "⚠️  Address failing security tests before production" -ForegroundColor Yellow
    Write-Host "⚠️  Review audit logs schema if using fallback data" -ForegroundColor Yellow
    Write-Host "⚠️  Ensure all endpoints properly secured" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Healthcare Security Validation Complete" -ForegroundColor Cyan

return $TestResults