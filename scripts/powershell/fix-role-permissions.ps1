# Fix Role-Based Access Control Issues
Write-Host "Fixing Role-Based Access Control" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Gray

Write-Host "Security Violations Found:" -ForegroundColor Yellow
Write-Host "1. PATIENT can access audit logs (should be admin/auditor only)" -ForegroundColor Red
Write-Host "2. LAB_TECH can access clinical workflows (should be restricted)" -ForegroundColor Red
Write-Host ""

# Step 1: Check current role requirements
Write-Host "Step 1: Checking current role requirements..." -ForegroundColor White

$check_roles = @"
import sys
sys.path.insert(0, '.')
import asyncio
from pathlib import Path

async def check_role_decorators():
    # Check audit logger router
    audit_router_path = Path('app/modules/audit_logger/router.py')
    if audit_router_path.exists():
        with open(audit_router_path, 'r') as f:
            content = f.read()
            
        print('=== AUDIT ROUTER ANALYSIS ===')
        if 'require_role' in content:
            print('✅ Role decorators found in audit router')
            # Extract role requirements
            import re
            roles = re.findall(r'require_role\([\"\'](.*?)[\"\']', content)
            print(f'Required roles: {roles}')
        else:
            print('❌ No role decorators found in audit router')
            
        if '/logs' in content:
            print('✅ Logs endpoint found')
            # Check if it has role protection
            logs_section = content[content.find('/logs'):content.find('/logs') + 500]
            if 'require_role' in logs_section:
                print('✅ Logs endpoint has role protection')
            else:
                print('❌ Logs endpoint missing role protection')
    
    # Check clinical workflows router
    clinical_router_path = Path('app/modules/clinical_workflows/router.py')
    if clinical_router_path.exists():
        with open(clinical_router_path, 'r') as f:
            content = f.read()
            
        print('\\n=== CLINICAL WORKFLOWS ROUTER ANALYSIS ===')
        if 'require_role' in content:
            print('✅ Role decorators found in clinical workflows router')
            # Extract role requirements
            import re
            roles = re.findall(r'require_role\([\"\'](.*?)[\"\']', content)
            print(f'Required roles: {roles}')
        else:
            print('❌ No role decorators found in clinical workflows router')
            
        if '/workflows' in content:
            print('✅ Workflows endpoint found')

asyncio.run(check_role_decorators())
"@

docker-compose exec app python -c $check_roles

# Step 2: Fix audit logs role protection
Write-Host "`nStep 2: Adding role protection to audit logs..." -ForegroundColor White

$fix_audit_roles = @'
# Read the audit router file
$auditRouterPath = "/mnt/c/Users/aurik/Code_Projects/2_scraper/app/modules/audit_logger/router.py"
if (Test-Path $auditRouterPath) {
    $content = Get-Content $auditRouterPath -Raw
    
    # Add require_role import if not present
    if ($content -notmatch "require_role") {
        $content = $content -replace "from app\.core\.security import", "from app.core.security import verify_token, require_role"
    }
    
    # Find the logs endpoint and add role protection
    if ($content -match "@router\.get\(`"/logs`"") {
        # Add role decorator before the endpoint
        $content = $content -replace "(@router\.get\(`"/logs`".*?)", "@require_role(`"admin`")`n$1"
        Write-Host "✅ Added admin role requirement to audit logs endpoint" -ForegroundColor Green
    }
    
    # Save the file
    Set-Content $auditRouterPath -Value $content
} else {
    Write-Host "❌ Audit router file not found" -ForegroundColor Red
}
'@

Invoke-Expression $fix_audit_roles

# Step 3: Fix clinical workflows role protection  
Write-Host "`nStep 3: Adding role protection to clinical workflows..." -ForegroundColor White

$fix_clinical_roles = @'
# Read the clinical workflows router file
$clinicalRouterPath = "/mnt/c/Users/aurik/Code_Projects/2_scraper/app/modules/clinical_workflows/router.py"
if (Test-Path $clinicalRouterPath) {
    $content = Get-Content $clinicalRouterPath -Raw
    
    # Add require_role import if not present
    if ($content -notmatch "require_role") {
        $content = $content -replace "from app\.core\.security import", "from app.core.security import verify_token, require_role"
    }
    
    # Find the workflows endpoint and add role protection
    if ($content -match "@router\.get\(`"/workflows`"") {
        # Add role decorator before the endpoint - restrict to admin and doctor roles
        $content = $content -replace "(@router\.get\(`"/workflows`".*?)", "@require_role(`"admin`", `"doctor`")`n$1"
        Write-Host "✅ Added admin/doctor role requirement to clinical workflows endpoint" -ForegroundColor Green
    }
    
    # Save the file
    Set-Content $clinicalRouterPath -Value $content
} else {
    Write-Host "❌ Clinical workflows router file not found" -ForegroundColor Red
}
'@

Invoke-Expression $fix_clinical_roles

# Step 4: Create a role requirements verification script
Write-Host "`nStep 4: Creating role verification test..." -ForegroundColor White

$role_test = @"
import sys
sys.path.insert(0, '.')
import asyncio
import aiohttp
import json

async def test_role_permissions():
    base_url = 'http://localhost:8000'
    
    # Test credentials
    test_users = [
        ('admin', 'Admin123!', 'admin'),
        ('patient', 'Patient123!', 'user'),
        ('doctor', 'Doctor123!', 'user'),
        ('lab_tech', 'LabTech123!', 'user')
    ]
    
    print('=== ROLE PERMISSION TEST ===')
    
    for username, password, role in test_users:
        print(f'\\nTesting user: {username} (role: {role})')
        
        # Get authentication token
        async with aiohttp.ClientSession() as session:
            login_data = {'username': username, 'password': password}
            
            try:
                async with session.post(f'{base_url}/api/v1/auth/login', json=login_data) as resp:
                    if resp.status == 200:
                        auth_data = await resp.json()
                        token = auth_data['access_token']
                        headers = {'Authorization': f'Bearer {token}'}
                        
                        # Test audit logs access
                        async with session.get(f'{base_url}/api/v1/audit-logs/logs', headers=headers) as audit_resp:
                            if audit_resp.status == 200:
                                print(f'  Audit logs: ✅ ALLOWED (status: {audit_resp.status})')
                            elif audit_resp.status in [401, 403]:
                                print(f'  Audit logs: ❌ DENIED (status: {audit_resp.status})')
                            else:
                                print(f'  Audit logs: ⚠️  ERROR (status: {audit_resp.status})')
                        
                        # Test clinical workflows access
                        async with session.get(f'{base_url}/api/v1/clinical-workflows/workflows', headers=headers) as clinical_resp:
                            if clinical_resp.status == 200:
                                print(f'  Clinical workflows: ✅ ALLOWED (status: {clinical_resp.status})')
                            elif clinical_resp.status in [401, 403]:
                                print(f'  Clinical workflows: ❌ DENIED (status: {clinical_resp.status})')
                            else:
                                print(f'  Clinical workflows: ⚠️  ERROR (status: {clinical_resp.status})')
                                
                    else:
                        print(f'  Authentication failed: {resp.status}')
                        
            except Exception as e:
                print(f'  Error testing {username}: {e}')

asyncio.run(test_role_permissions())
"@

# Step 5: Restart application and test
Write-Host "`nStep 5: Restarting application to apply role fixes..." -ForegroundColor White

Write-Host "Restarting Docker containers..." -ForegroundColor Yellow
docker-compose restart app

Write-Host "Waiting for application to start..." -ForegroundColor Yellow
Start-Sleep 15

# Step 6: Run role permission test
Write-Host "`nStep 6: Testing role permissions after fixes..." -ForegroundColor White

docker-compose exec app python -c $role_test

Write-Host "`nRole permission fixes complete!" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Gray

Write-Host "`nExpected results:" -ForegroundColor White
Write-Host "✅ ADMIN should access both audit logs and clinical workflows" -ForegroundColor Green
Write-Host "❌ PATIENT should be denied access to audit logs" -ForegroundColor Green
Write-Host "✅ DOCTOR should access clinical workflows" -ForegroundColor Green
Write-Host "❌ LAB_TECH should be denied access to clinical workflows" -ForegroundColor Green

Write-Host "`nNext step: Run full validation tests to see improvements!" -ForegroundColor Yellow