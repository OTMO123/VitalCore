# Security Check - Simple Direct Testing
Write-Host "Security Violation Analysis" -ForegroundColor Red
Write-Host "===========================" -ForegroundColor Gray

# Step 1: Test security violations directly
Write-Host "Step 1: Testing current security violations..." -ForegroundColor White

Write-Host "`nTesting patient access to audit logs..." -ForegroundColor Yellow
try {
    $patientLogin = @{ username = "patient"; password = "Patient123!" } | ConvertTo-Json
    $patientAuth = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -ContentType "application/json" -Body $patientLogin
    
    if ($patientAuth.access_token) {
        $patientHeaders = @{ "Authorization" = "Bearer $($patientAuth.access_token)" }
        
        try {
            $auditTest = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/audit-logs/logs" -Method GET -Headers $patientHeaders
            Write-Host "❌ SECURITY VIOLATION: Patient CAN access audit logs" -ForegroundColor Red
            Write-Host "This is a critical security issue that must be fixed" -ForegroundColor Red
        } catch {
            Write-Host "✅ Good: Patient access denied - Status: $($_.Exception.Response.StatusCode)" -ForegroundColor Green
        }
    }
} catch {
    Write-Host "Patient authentication failed" -ForegroundColor Yellow
}

Write-Host "`nTesting lab_tech access to clinical workflows..." -ForegroundColor Yellow
try {
    $labLogin = @{ username = "lab_tech"; password = "LabTech123!" } | ConvertTo-Json
    $labAuth = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -ContentType "application/json" -Body $labLogin
    
    if ($labAuth.access_token) {
        $labHeaders = @{ "Authorization" = "Bearer $($labAuth.access_token)" }
        
        try {
            $workflowTest = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/clinical-workflows/workflows" -Method GET -Headers $labHeaders
            Write-Host "❌ SECURITY VIOLATION: Lab tech CAN access clinical workflows" -ForegroundColor Red
            Write-Host "This should be restricted to doctors and admins only" -ForegroundColor Red
        } catch {
            Write-Host "✅ Good: Lab tech access denied - Status: $($_.Exception.Response.StatusCode)" -ForegroundColor Green
        }
    }
} catch {
    Write-Host "Lab tech authentication failed" -ForegroundColor Yellow
}

# Step 2: Test healthcare endpoints
Write-Host "`nStep 2: Testing healthcare endpoints..." -ForegroundColor White

try {
    $adminLogin = @{ username = "admin"; password = "Admin123!" } | ConvertTo-Json
    $adminAuth = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -ContentType "application/json" -Body $adminLogin
    
    if ($adminAuth.access_token) {
        $adminHeaders = @{ "Authorization" = "Bearer $($adminAuth.access_token)" }
        
        Write-Host "Testing healthcare patients endpoint..." -ForegroundColor Yellow
        try {
            $patientsTest = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients" -Method GET -Headers $adminHeaders
            Write-Host "✅ Healthcare patients endpoint working" -ForegroundColor Green
        } catch {
            Write-Host "❌ Healthcare patients failed - Status: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
            if ($_.Exception.Response.StatusCode -eq 500) {
                Write-Host "500 error suggests missing database tables or service issues" -ForegroundColor Yellow
            }
        }
    }
} catch {
    Write-Host "Admin authentication failed" -ForegroundColor Red
}

# Step 3: Check file existence
Write-Host "`nStep 3: Checking critical files..." -ForegroundColor White

Write-Host "Checking if router files exist..." -ForegroundColor Yellow
docker-compose exec app test -f app/modules/audit_logger/router.py && Write-Host "✅ Audit router exists" -ForegroundColor Green || Write-Host "❌ Audit router missing" -ForegroundColor Red

docker-compose exec app test -f app/modules/clinical_workflows/router.py && Write-Host "✅ Clinical workflows router exists" -ForegroundColor Green || Write-Host "❌ Clinical workflows router missing" -ForegroundColor Red

# Step 4: Look for role decorators
Write-Host "`nStep 4: Checking for role decorators..." -ForegroundColor White

Write-Host "Searching for require_role in audit router..." -ForegroundColor Yellow
$auditRoleCheck = docker-compose exec app grep -c "require_role" app/modules/audit_logger/router.py 2>$null
if ($auditRoleCheck -gt 0) {
    Write-Host "✅ Found $auditRoleCheck require_role decorators in audit router" -ForegroundColor Green
} else {
    Write-Host "❌ No require_role decorators found in audit router" -ForegroundColor Red
}

Write-Host "Searching for require_role in clinical workflows router..." -ForegroundColor Yellow
$clinicalRoleCheck = docker-compose exec app grep -c "require_role" app/modules/clinical_workflows/router.py 2>$null
if ($clinicalRoleCheck -gt 0) {
    Write-Host "✅ Found $clinicalRoleCheck require_role decorators in clinical workflows router" -ForegroundColor Green
} else {
    Write-Host "❌ No require_role decorators found in clinical workflows router" -ForegroundColor Red
}

Write-Host "`nSecurity analysis complete!" -ForegroundColor Cyan
Write-Host "============================" -ForegroundColor Gray

Write-Host "`nSUMMARY:" -ForegroundColor White
Write-Host "Run the validation tests to see current status:" -ForegroundColor Yellow
Write-Host "  .\validate_core_security_fixes.ps1" -ForegroundColor Green
Write-Host "  .\validate-role-based-security.ps1" -ForegroundColor Green