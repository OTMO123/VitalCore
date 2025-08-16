# Role-Based Security Validation Script
# Tests healthcare role access controls and HIPAA compliance
# Usage: .\validate-role-based-security.ps1

param(
    [string]$BaseUrl = "http://localhost:8000",
    [string]$TestRole = "all"  # all, patient, doctor, lab
)

Write-Host "Role-Based Security Validation" -ForegroundColor Cyan
Write-Host "=" * 40 -ForegroundColor Gray

if ($TestRole -ne "all") {
    Write-Host "Testing specific role: $TestRole" -ForegroundColor Yellow
} else {
    Write-Host "Testing all healthcare roles" -ForegroundColor Yellow
}

Write-Host ""

# Test results tracking
$RoleTestResults = @{
    "total_tests" = 0
    "passed_tests" = 0
    "failed_tests" = 0
    "role_compliance" = @{}
    "security_violations" = @()
}

function Test-RoleAccess {
    param(
        [string]$RoleName,
        [string]$Username,
        [string]$Password,
        [string]$TestDescription,
        [string]$Endpoint,
        [string]$Method = "GET",
        [bool]$ShouldSucceed = $true
    )
    
    $RoleTestResults.total_tests++
    
    Write-Host "[ROLE TEST] $RoleName - $TestDescription" -ForegroundColor White
    
    try {
        # Get authentication token
        $loginData = @{
            username = $Username
            password = $Password
        } | ConvertTo-Json
        
        try {
            $authResponse = Invoke-RestMethod -Uri "$BaseUrl/api/v1/auth/login" -Method POST -ContentType "application/json" -Body $loginData
            $token = $authResponse.access_token
        } catch {
            Write-Host "  ❌ Authentication failed for $Username" -ForegroundColor Red
            $RoleTestResults.failed_tests++
            return $false
        }
        
        if (-not $token) {
            Write-Host "  ❌ No token received for $Username" -ForegroundColor Red
            $RoleTestResults.failed_tests++
            return $false
        }
        
        # Test endpoint access
        $headers = @{
            "Authorization" = "Bearer $token"
            "Content-Type" = "application/json"
        }
        
        try {
            $response = Invoke-RestMethod -Uri "$BaseUrl$Endpoint" -Method $Method -Headers $headers
            
            if ($ShouldSucceed) {
                Write-Host "  ✅ Access granted as expected" -ForegroundColor Green
                $RoleTestResults.passed_tests++
                return $true
            } else {
                Write-Host "  ❌ Access granted when it should be denied (SECURITY VIOLATION)" -ForegroundColor Red
                $RoleTestResults.failed_tests++
                $RoleTestResults.security_violations += @{
                    "role" = $RoleName
                    "test" = $TestDescription
                    "violation" = "Unauthorized access granted"
                    "endpoint" = $Endpoint
                }
                return $false
            }
        } catch {
            $statusCode = $null
            if ($_.Exception.Response) {
                $statusCode = $_.Exception.Response.StatusCode.value__
            }
            
            if (-not $ShouldSucceed -and $statusCode -in @(403, 404, 401)) {
                Write-Host "  ✅ Access properly denied (Status: $statusCode)" -ForegroundColor Green
                $RoleTestResults.passed_tests++
                return $true
            } elseif ($ShouldSucceed) {
                Write-Host "  ❌ Access denied when it should succeed (Status: $statusCode)" -ForegroundColor Red
                $RoleTestResults.failed_tests++
                return $false
            } else {
                Write-Host "  ⚠️  Unexpected error: $($_.Exception.Message)" -ForegroundColor Yellow
                $RoleTestResults.failed_tests++
                return $false
            }
        }
    } catch {
        Write-Host "  ❌ Test execution failed: $($_.Exception.Message)" -ForegroundColor Red
        $RoleTestResults.failed_tests++
        return $false
    }
}

# Test Admin Role (Baseline)
if ($TestRole -eq "all" -or $TestRole -eq "admin") {
    Write-Host "Testing Admin Role Access Controls" -ForegroundColor Magenta
    Write-Host "-" * 35 -ForegroundColor Gray
    
    # Admin should have access to most endpoints
    Test-RoleAccess "ADMIN" "admin" "Admin123!" "Health Check Access" "/health" "GET" $true
    Test-RoleAccess "ADMIN" "admin" "Admin123!" "Patient List Access" "/api/v1/healthcare/patients" "GET" $true
    Test-RoleAccess "ADMIN" "admin" "Admin123!" "Audit Logs Access" "/api/v1/audit-logs/logs" "GET" $true
    Test-RoleAccess "ADMIN" "admin" "Admin123!" "User Management Access" "/api/v1/auth/users" "GET" $true
    
    Write-Host ""
}

# Test Patient Role (if user exists)
if ($TestRole -eq "all" -or $TestRole -eq "patient") {
    Write-Host "Testing Patient Role Access Controls" -ForegroundColor Green
    Write-Host "-" * 35 -ForegroundColor Gray
    
    # Patient should have limited access
    Test-RoleAccess "PATIENT" "patient" "Patient123!" "Own Health Record" "/api/v1/healthcare/patients/self" "GET" $true
    Test-RoleAccess "PATIENT" "patient" "Patient123!" "User Management Denied" "/api/v1/auth/users" "GET" $false
    Test-RoleAccess "PATIENT" "patient" "Patient123!" "Audit Logs Denied" "/api/v1/audit-logs/logs" "GET" $false
    Test-RoleAccess "PATIENT" "patient" "Patient123!" "Admin Functions Denied" "/api/v1/system/config" "GET" $false
    
    Write-Host ""
}

# Test Doctor Role (if user exists)
if ($TestRole -eq "all" -or $TestRole -eq "doctor") {
    Write-Host "Testing Doctor Role Access Controls" -ForegroundColor Blue
    Write-Host "-" * 35 -ForegroundColor Gray
    
    # Doctor should have clinical access but not admin
    Test-RoleAccess "DOCTOR" "doctor" "Doctor123!" "Patient Records Access" "/api/v1/healthcare/patients" "GET" $true
    Test-RoleAccess "DOCTOR" "doctor" "Doctor123!" "Clinical Workflows" "/api/v1/clinical-workflows/workflows" "GET" $true
    Test-RoleAccess "DOCTOR" "doctor" "Doctor123!" "User Management Denied" "/api/v1/auth/users" "GET" $false
    Test-RoleAccess "DOCTOR" "doctor" "Doctor123!" "System Config Denied" "/api/v1/system/config" "GET" $false
    
    Write-Host ""
}

# Test Lab Technician Role (if user exists)
if ($TestRole -eq "all" -or $TestRole -eq "lab") {
    Write-Host "Testing Lab Technician Role Access Controls" -ForegroundColor Yellow
    Write-Host "-" * 40 -ForegroundColor Gray
    
    # Lab tech should have limited access
    Test-RoleAccess "LAB_TECH" "lab_tech" "LabTech123!" "Lab Results Upload" "/api/v1/laboratory/results" "GET" $true
    Test-RoleAccess "LAB_TECH" "lab_tech" "LabTech123!" "Patient Full Records Denied" "/api/v1/healthcare/patients" "GET" $false
    Test-RoleAccess "LAB_TECH" "lab_tech" "LabTech123!" "User Management Denied" "/api/v1/auth/users" "GET" $false
    Test-RoleAccess "LAB_TECH" "lab_tech" "LabTech123!" "Clinical Workflows Denied" "/api/v1/clinical-workflows/workflows" "GET" $false
    
    Write-Host ""
}

# Test Cross-Role Security
if ($TestRole -eq "all") {
    Write-Host "Testing Cross-Role Security Boundaries" -ForegroundColor Red
    Write-Host "-" * 35 -ForegroundColor Gray
    
    # Test that no role can access debug endpoints (should be removed)
    $roles = @(
        @("admin", "Admin123!"),
        @("doctor", "Doctor123!"),
        @("patient", "Patient123!"),
        @("lab_tech", "LabTech123!")
    )
    
    foreach ($role in $roles) {
        $username = $role[0]
        $password = $role[1]
        Test-RoleAccess $username.ToUpper() $username $password "Debug Endpoints Removed" "/api/v1/healthcare/step-by-step-debug/test" "GET" $false
    }
    
    Write-Host ""
}

# Calculate compliance metrics
$ComplianceScore = 0
if ($RoleTestResults.total_tests -gt 0) {
    $ComplianceScore = [math]::Round(($RoleTestResults.passed_tests / $RoleTestResults.total_tests) * 100, 1)
}

# Generate summary report
Write-Host "Role-Based Security Summary" -ForegroundColor Cyan
Write-Host "=" * 30 -ForegroundColor Gray
Write-Host "Total Tests: $($RoleTestResults.total_tests)" -ForegroundColor White
Write-Host "Passed: $($RoleTestResults.passed_tests)" -ForegroundColor Green  
Write-Host "Failed: $($RoleTestResults.failed_tests)" -ForegroundColor Red
Write-Host "Compliance Score: $ComplianceScore%" -ForegroundColor Yellow

if ($RoleTestResults.security_violations.Count -gt 0) {
    Write-Host ""
    Write-Host "SECURITY VIOLATIONS DETECTED:" -ForegroundColor Red
    Write-Host "-" * 30 -ForegroundColor Gray
    
    foreach ($violation in $RoleTestResults.security_violations) {
        Write-Host "[$($violation.role)] $($violation.test)" -ForegroundColor Red
        Write-Host "  Violation: $($violation.violation)" -ForegroundColor Red
        Write-Host "  Endpoint: $($violation.endpoint)" -ForegroundColor Yellow
        Write-Host ""
    }
}

# Final status
Write-Host "FINAL STATUS:" -ForegroundColor White
if ($ComplianceScore -ge 95 -and $RoleTestResults.security_violations.Count -eq 0) {
    Write-Host "✅ ROLE-BASED SECURITY VALIDATED" -ForegroundColor Green
    Write-Host "✅ HIPAA MINIMUM NECESSARY RULE ENFORCED" -ForegroundColor Green
    Write-Host "✅ NO SECURITY VIOLATIONS DETECTED" -ForegroundColor Green
} elseif ($ComplianceScore -ge 80) {
    Write-Host "⚠️  PARTIAL COMPLIANCE - REVIEW REQUIRED" -ForegroundColor Yellow
    Write-Host "⚠️  SOME SECURITY TESTS FAILED" -ForegroundColor Yellow
} else {
    Write-Host "❌ SECURITY VIOLATIONS DETECTED" -ForegroundColor Red
    Write-Host "❌ IMMEDIATE REMEDIATION REQUIRED" -ForegroundColor Red
}

Write-Host ""
Write-Host "Role-Based Security Validation Complete" -ForegroundColor Cyan

return $RoleTestResults