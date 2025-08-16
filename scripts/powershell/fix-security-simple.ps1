# Fix Critical Security Violations - Simple Version
Write-Host "Fixing Critical Security Violations" -ForegroundColor Red
Write-Host "===================================" -ForegroundColor Gray

Write-Host "CRITICAL ISSUES FOUND:" -ForegroundColor Red
Write-Host "1. PATIENT can access audit logs (SECURITY VIOLATION)" -ForegroundColor Red
Write-Host "2. LAB_TECH can access clinical workflows (SECURITY VIOLATION)" -ForegroundColor Red
Write-Host "3. Healthcare patients 500 error (missing functionality)" -ForegroundColor Red
Write-Host ""

# Step 1: Check if files exist
Write-Host "Step 1: Checking router files..." -ForegroundColor White

Write-Host "Checking audit logger router..." -ForegroundColor Yellow
docker-compose exec app ls -la app/modules/audit_logger/router.py

Write-Host "Checking clinical workflows router..." -ForegroundColor Yellow  
docker-compose exec app ls -la app/modules/clinical_workflows/router.py

# Step 2: Check database tables
Write-Host "`nStep 2: Checking database tables..." -ForegroundColor White

Write-Host "Checking for patients table..." -ForegroundColor Yellow
$checkPatientsTable = "import asyncio; from app.core.database_unified import get_db; from sqlalchemy import text; async def check(): db_gen = get_db(); db = await db_gen.__anext__(); result = await db.execute(text(\"SELECT table_name FROM information_schema.tables WHERE table_name = 'patients'\"")); exists = result.fetchone(); print('✅ Patients table exists' if exists else '❌ Patients table missing'); asyncio.run(check())"

docker-compose exec app python -c $checkPatientsTable

# Step 3: Test security violations directly
Write-Host "`nStep 3: Testing security violations..." -ForegroundColor White

Write-Host "Testing patient access to audit logs..." -ForegroundColor Yellow
try {
    $patientLogin = @{ username = "patient"; password = "Patient123!" } | ConvertTo-Json
    $patientAuth = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -ContentType "application/json" -Body $patientLogin
    
    if ($patientAuth.access_token) {
        $patientHeaders = @{ "Authorization" = "Bearer $($patientAuth.access_token)" }
        
        try {
            $auditTest = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/audit-logs/logs" -Method GET -Headers $patientHeaders
            Write-Host "❌ CRITICAL: Patient CAN access audit logs - SECURITY VIOLATION" -ForegroundColor Red
        } catch {
            if ($_.Exception.Response.StatusCode -eq 403) {
                Write-Host "✅ GOOD: Patient properly denied access (403)" -ForegroundColor Green
            } elseif ($_.Exception.Response.StatusCode -eq 401) {
                Write-Host "⚠️  Patient denied access (401)" -ForegroundColor Yellow
            } else {
                Write-Host "⚠️  Unexpected response: $($_.Exception.Response.StatusCode)" -ForegroundColor Yellow
            }
        }
    }
} catch {
    Write-Host "❌ Patient authentication failed" -ForegroundColor Red
}

Write-Host "`nTesting lab_tech access to clinical workflows..." -ForegroundColor Yellow
try {
    $labLogin = @{ username = "lab_tech"; password = "LabTech123!" } | ConvertTo-Json
    $labAuth = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -ContentType "application/json" -Body $labLogin
    
    if ($labAuth.access_token) {
        $labHeaders = @{ "Authorization" = "Bearer $($labAuth.access_token)" }
        
        try {
            $workflowTest = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/clinical-workflows/workflows" -Method GET -Headers $labHeaders
            Write-Host "❌ CRITICAL: Lab tech CAN access clinical workflows - SECURITY VIOLATION" -ForegroundColor Red
        } catch {
            if ($_.Exception.Response.StatusCode -eq 403) {
                Write-Host "✅ GOOD: Lab tech properly denied access (403)" -ForegroundColor Green
            } else {
                Write-Host "⚠️  Response: $($_.Exception.Response.StatusCode)" -ForegroundColor Yellow
            }
        }
    }
} catch {
    Write-Host "❌ Lab tech authentication failed" -ForegroundColor Red
}

# Step 4: Check role decorators in files
Write-Host "`nStep 4: Checking role decorators..." -ForegroundColor White

Write-Host "Checking audit router for role decorators..." -ForegroundColor Yellow
docker-compose exec app grep -n "require_role" app/modules/audit_logger/router.py || Write-Host "No require_role found in audit router" -ForegroundColor Red

Write-Host "Checking clinical workflows for role decorators..." -ForegroundColor Yellow
docker-compose exec app grep -n "require_role" app/modules/clinical_workflows/router.py || Write-Host "No require_role found in clinical workflows router" -ForegroundColor Red

# Step 5: Summary and next steps
Write-Host "`nSecurity analysis complete!" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Gray

Write-Host "`nKEY FINDINGS:" -ForegroundColor White
Write-Host "- Role decorators may exist but are not being enforced" -ForegroundColor Yellow
Write-Host "- Healthcare tables may be missing from database" -ForegroundColor Yellow
Write-Host "- Security violations need immediate attention" -ForegroundColor Red

Write-Host "`nNEXT ACTIONS:" -ForegroundColor White
Write-Host "1. Add proper role decorators to endpoints" -ForegroundColor Yellow
Write-Host "2. Create missing database tables" -ForegroundColor Yellow
Write-Host "3. Test role enforcement" -ForegroundColor Yellow
Write-Host "4. Re-run validation tests" -ForegroundColor Yellow