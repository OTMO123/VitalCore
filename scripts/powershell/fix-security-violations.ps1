# Fix Critical Security Violations
Write-Host "Fixing Critical Security Violations" -ForegroundColor Red
Write-Host "===================================" -ForegroundColor Gray

Write-Host "CRITICAL ISSUES FOUND:" -ForegroundColor Red
Write-Host "1. PATIENT can access audit logs (SECURITY VIOLATION)" -ForegroundColor Red
Write-Host "2. LAB_TECH can access clinical workflows (SECURITY VIOLATION)" -ForegroundColor Red
Write-Host "3. Healthcare patients 500 error (missing functionality)" -ForegroundColor Red
Write-Host ""

# Step 1: Check current role decorators
Write-Host "Step 1: Checking role decorators..." -ForegroundColor White

Write-Host "Checking audit logger router..." -ForegroundColor Yellow
docker-compose exec app python -c "import os; print('✅ audit router exists' if os.path.exists('app/modules/audit_logger/router.py') else '❌ not found')"

Write-Host "Checking clinical workflows router..." -ForegroundColor Yellow  
docker-compose exec app python -c "import os; print('✅ clinical router exists' if os.path.exists('app/modules/clinical_workflows/router.py') else '❌ not found')"

# Step 2: Check what's in the audit router
Write-Host "`nStep 2: Analyzing audit router role protection..." -ForegroundColor White

$checkAuditRouter = @"
import os
if os.path.exists('app/modules/audit_logger/router.py'):
    with open('app/modules/audit_logger/router.py', 'r') as f:
        content = f.read()
    
    print('=== AUDIT ROUTER ANALYSIS ===')
    
    # Check for logs endpoint
    if '/logs' in content:
        print('✅ Found /logs endpoint')
        
        # Check for role requirements
        if 'require_role' in content:
            print('✅ Has require_role decorators')
            
            # Count role decorators
            role_count = content.count('@require_role')
            print(f'✅ Found {role_count} role decorators')
            
            # Check specific roles mentioned
            if 'admin' in content:
                print('✅ Mentions admin role')
            if 'auditor' in content:
                print('✅ Mentions auditor role')
                
        else:
            print('❌ NO role decorators found')
    else:
        print('❌ No /logs endpoint found')
else:
    print('❌ Audit router file not found')
"@

docker-compose exec app python -c $checkAuditRouter

# Step 3: Check clinical workflows router
Write-Host "`nStep 3: Analyzing clinical workflows router..." -ForegroundColor White

$checkClinicalRouter = @"
import os
if os.path.exists('app/modules/clinical_workflows/router.py'):
    with open('app/modules/clinical_workflows/router.py', 'r') as f:
        content = f.read()
    
    print('=== CLINICAL WORKFLOWS ROUTER ANALYSIS ===')
    
    if '/workflows' in content:
        print('✅ Found /workflows endpoint')
        
        if 'require_role' in content:
            print('✅ Has require_role decorators')
            role_count = content.count('@require_role')
            print(f'✅ Found {role_count} role decorators')
        else:
            print('❌ NO role decorators found - THIS IS THE SECURITY ISSUE')
    else:
        print('❌ No /workflows endpoint found')
else:
    print('❌ Clinical workflows router file not found')
"@

docker-compose exec app python -c $checkClinicalRouter

# Step 4: Check healthcare service issue
Write-Host "`nStep 4: Checking healthcare service tables..." -ForegroundColor White

$checkTables = @"
import asyncio
from app.core.database_unified import get_db
from sqlalchemy import text

async def check_tables():
    try:
        db_gen = get_db()
        db = await db_gen.__anext__()
        
        # Check for patients table
        result = await db.execute(text('SELECT table_name FROM information_schema.tables WHERE table_name = \'patients\''))
        patients_exists = result.fetchone()
        
        if patients_exists:
            print('✅ Patients table exists')
        else:
            print('❌ Patients table missing - this causes 500 errors')
            
        # Check for healthcare tables
        result = await db.execute(text('SELECT table_name FROM information_schema.tables WHERE table_name LIKE \'%health%\' OR table_name LIKE \'%patient%\''))
        health_tables = result.fetchall()
        
        print(f'Healthcare-related tables: {[t[0] for t in health_tables]}')
        
    except Exception as e:
        print(f'❌ Database check failed: {e}')

asyncio.run(check_tables())
"@

docker-compose exec app python -c $checkTables

# Step 5: Test direct role-based access
Write-Host "`nStep 5: Testing role-based access directly..." -ForegroundColor White

Write-Host "Testing patient access to audit logs..." -ForegroundColor Yellow
try {
    $patientLogin = @{ username = "patient"; password = "Patient123!" } | ConvertTo-Json
    $patientAuth = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -ContentType "application/json" -Body $patientLogin
    
    if ($patientAuth.access_token) {
        $patientHeaders = @{ "Authorization" = "Bearer $($patientAuth.access_token)" }
        
        try {
            $auditTest = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/audit-logs/logs" -Method GET -Headers $patientHeaders
            Write-Host "❌ CRITICAL: Patient CAN access audit logs - SECURITY VIOLATION" -ForegroundColor Red
            Write-Host "Response received - this should NOT happen" -ForegroundColor Red
        } catch {
            if ($_.Exception.Response.StatusCode -eq 403) {
                Write-Host "✅ GOOD: Patient properly denied access (403)" -ForegroundColor Green
            } elseif ($_.Exception.Response.StatusCode -eq 401) {
                Write-Host "⚠️  Patient denied access (401) - check if this is expected" -ForegroundColor Yellow
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
            Write-Host "Response received - this should be restricted" -ForegroundColor Red
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

Write-Host "`nSecurity analysis complete!" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Gray

Write-Host "`nFINDINGS:" -ForegroundColor White
Write-Host "🔍 The role decorators may exist but are not being enforced properly" -ForegroundColor Yellow
Write-Host "🔍 Healthcare patients endpoint is missing required database tables" -ForegroundColor Yellow
Write-Host "🔍 Role-based access control needs verification and enforcement" -ForegroundColor Yellow

Write-Host "`nNEXT ACTIONS NEEDED:" -ForegroundColor White
Write-Host "1. Verify role decorator implementation in router files" -ForegroundColor Red
Write-Host "2. Check if @require_role decorators are actually being applied" -ForegroundColor Red
Write-Host "3. Create missing healthcare database tables" -ForegroundColor Red
Write-Host "4. Test role enforcement is working correctly" -ForegroundColor Red