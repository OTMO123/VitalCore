# Fix Database Schema Mismatch - Windows Compatible Version
Write-Host "Fixing Database Schema Mismatch" -ForegroundColor Cyan
Write-Host "===============================" -ForegroundColor Gray

# Step 1: Check application status first
Write-Host "Step 1: Checking application status..." -ForegroundColor White

try {
    $healthResponse = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 10
    Write-Host "✅ Application is running and healthy" -ForegroundColor Green
} catch {
    Write-Host "❌ Application not responding, starting it..." -ForegroundColor Red
    docker-compose up -d
    Start-Sleep 20
}

# Step 2: Fix the database schema mismatch using Docker exec
Write-Host "`nStep 2: Fixing audit logs schema mismatch..." -ForegroundColor White

$fixSchemaScript = @"
import sys
sys.path.insert(0, '.')
import os
import re

def fix_schema_files():
    files_to_fix = [
        'app/core/database_advanced.py',
        'app/modules/audit_logger/service.py', 
        'app/modules/audit_logger/enhanced_audit_service.py'
    ]
    
    fixed_count = 0
    
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            print(f'Fixing {file_path}...')
            
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Count current 'result' references
            result_count = len(re.findall(r'\.result\b', content))
            print(f'  Found {result_count} .result references')
            
            # Replace .result with .outcome
            new_content = re.sub(r'\.result\b', '.outcome', content)
            
            # Also fix any AuditLog.result references
            new_content = re.sub(r'AuditLog\.result', 'AuditLog.outcome', new_content)
            
            # Fix model definition if it exists
            new_content = re.sub(
                r'result: Mapped\[str\] = mapped_column\(String\(50\), nullable=False\)',
                'outcome: Mapped[str] = mapped_column(String(50), nullable=False)',
                new_content
            )
            
            if new_content != content:
                with open(file_path, 'w') as f:
                    f.write(new_content)
                
                outcome_count = len(re.findall(r'\.outcome\b', new_content))
                print(f'  ✅ Fixed! Now has {outcome_count} .outcome references')
                fixed_count += 1
            else:
                print(f'  ✅ No changes needed')
        else:
            print(f'  ❌ File not found: {file_path}')
    
    print(f'\nFixed {fixed_count} files')
    return fixed_count > 0

# Run the fix
success = fix_schema_files()
print('SUCCESS' if success else 'NO_CHANGES')
"@

Write-Host "Running schema fix inside Docker container..." -ForegroundColor Yellow
$result = docker-compose exec app python -c $fixSchemaScript

if ($result -like "*SUCCESS*") {
    Write-Host "✅ Schema files updated successfully" -ForegroundColor Green
    
    Write-Host "`nRestarting application..." -ForegroundColor Yellow
    docker-compose restart app
    Start-Sleep 15
} else {
    Write-Host "ℹ️ No schema changes were needed" -ForegroundColor Yellow
}

# Step 3: Test the fix
Write-Host "`nStep 3: Testing endpoints after schema fix..." -ForegroundColor White

try {
    # Get authentication token
    $loginData = @{ username = "admin"; password = "Admin123!" } | ConvertTo-Json
    $authResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -ContentType "application/json" -Body $loginData
    
    if ($authResponse.access_token) {
        Write-Host "✅ Authentication working" -ForegroundColor Green
        
        $headers = @{
            "Authorization" = "Bearer $($authResponse.access_token)"
            "Content-Type" = "application/json"
        }
        
        # Test audit logs endpoint
        Write-Host "`nTesting audit logs endpoint..." -ForegroundColor Yellow
        try {
            $auditResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/audit-logs/logs" -Method GET -Headers $headers
            Write-Host "✅ SUCCESS: Audit logs endpoint working!" -ForegroundColor Green
        } catch {
            Write-Host "❌ Audit logs failed: $($_.Exception.Message)" -ForegroundColor Red
            if ($_.Exception.Response) {
                Write-Host "Status: $($_.Exception.Response.StatusCode)" -ForegroundColor Yellow
            }
        }
        
        # Test healthcare patients endpoint
        Write-Host "`nTesting healthcare patients endpoint..." -ForegroundColor Yellow
        try {
            $patientsResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients" -Method GET -Headers $headers
            Write-Host "✅ SUCCESS: Healthcare patients endpoint working!" -ForegroundColor Green
        } catch {
            Write-Host "❌ Healthcare patients failed: $($_.Exception.Message)" -ForegroundColor Red
            if ($_.Exception.Response) {
                Write-Host "Status: $($_.Exception.Response.StatusCode)" -ForegroundColor Yellow
                if ($_.Exception.Response.StatusCode -ne 500) {
                    Write-Host "✅ Progress: No longer a 500 error!" -ForegroundColor Green
                }
            }
        }
    } else {
        Write-Host "❌ Authentication failed - no token received" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Authentication request failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`nSchema fix complete!" -ForegroundColor Cyan
Write-Host "===================" -ForegroundColor Gray

Write-Host "`nNext steps:" -ForegroundColor White
Write-Host "1. Run .\simple-test.ps1 to verify basic functionality" -ForegroundColor Yellow
Write-Host "2. Run .\validate_core_security_fixes.ps1 for security validation" -ForegroundColor Yellow
Write-Host "3. Run .\validate-role-based-security.ps1 for role testing" -ForegroundColor Yellow