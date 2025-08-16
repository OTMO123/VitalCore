# Fix Database Schema Mismatch - Windows Compatible Version
Write-Host "Fixing Database Schema Mismatch (Windows Compatible)" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Gray

# Step 1: Check application status first
Write-Host "Step 1: Checking application status..." -ForegroundColor White

try {
    $healthResponse = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 10
    Write-Host "✅ Application is running and healthy" -ForegroundColor Green
} catch {
    Write-Host "❌ Application not responding, checking Docker status..." -ForegroundColor Red
    docker-compose ps
    
    Write-Host "`nStarting application..." -ForegroundColor Yellow
    docker-compose up -d
    Start-Sleep 20
    
    try {
        $healthResponse = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 10
        Write-Host "✅ Application started successfully" -ForegroundColor Green
    } catch {
        Write-Host "❌ Application still not responding, checking logs..." -ForegroundColor Red
        docker-compose logs --tail=10 app
        return
    }
}

# Step 2: Fix the database schema mismatch using Docker exec
Write-Host "`nStep 2: Fixing audit logs schema mismatch via Docker..." -ForegroundColor White

$fix_schema_script = @"
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
                
                # Count new 'outcome' references
                outcome_count = len(re.findall(r'\.outcome\b', new_content))
                print(f'  ✅ Fixed! Now has {outcome_count} .outcome references')
                fixed_count += 1
            else:
                print(f'  ✅ No changes needed')
        else:
            print(f'  ❌ File not found: {file_path}')
    
    print(f'\\nFixed {fixed_count} files')
    return fixed_count > 0

# Run the fix
success = fix_schema_files()
print('SUCCESS' if success else 'NO_CHANGES')
"@

Write-Host "Running schema fix inside Docker container..." -ForegroundColor Yellow
$result = docker-compose exec app python -c $fix_schema_script

if ($result -like "*SUCCESS*") {
    Write-Host "✅ Schema files updated successfully" -ForegroundColor Green
    
    # Restart the application
    Write-Host "`nRestarting application to apply changes..." -ForegroundColor Yellow
    docker-compose restart app
    Start-Sleep 15
} else {
    Write-Host "ℹ️ No schema changes were needed" -ForegroundColor Yellow
}

# Step 3: Test the fix
Write-Host "`nStep 3: Testing audit logs endpoint after schema fix..." -ForegroundColor White

try {
    # Get authentication token
    $loginData = @{ username = "admin"; password = "Admin123!" } | ConvertTo-Json
    $authResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -ContentType "application/json" -Body $loginData
    $token = $authResponse.access_token
    
    $headers = @{
        "Authorization" = "Bearer $token"
        "Content-Type" = "application/json"
    }
    
    Write-Host "Testing audit logs endpoint..." -ForegroundColor Yellow
    try {
        $auditResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/audit-logs/logs" -Method GET -Headers $headers
        Write-Host "✅ SUCCESS: Audit logs endpoint working!" -ForegroundColor Green
        
        if ($auditResponse.logs) {
            Write-Host "Found $($auditResponse.logs.Count) audit log entries" -ForegroundColor Green
        } elseif ($auditResponse.data) {
            Write-Host "Found audit log data in response" -ForegroundColor Green
        } else {
            Write-Host "Response: $($auditResponse | ConvertTo-Json -Depth 2)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "❌ Audit logs still failing: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "Status: $($_.Exception.Response.StatusCode)" -ForegroundColor Yellow
        
        if ($_.Exception.Response.StatusCode -eq 403) {
            Write-Host "ℹ️ 403 Forbidden - This might be due to role restrictions (good security)" -ForegroundColor Yellow
        }
    }
    
    # Test healthcare patients endpoint
    Write-Host "`nTesting healthcare patients endpoint..." -ForegroundColor Yellow
    try {
        $patientsResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients" -Method GET -Headers $headers
        Write-Host "✅ SUCCESS: Healthcare patients endpoint working!" -ForegroundColor Green
        
        if ($patientsResponse.patients) {
            Write-Host "Found $($patientsResponse.patients.Count) patients" -ForegroundColor Green
        } else {
            Write-Host "Response structure: $($patientsResponse.Keys -join ', ')" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "❌ Healthcare patients still failing: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "Status: $($_.Exception.Response.StatusCode)" -ForegroundColor Yellow
        
        # Check if it's no longer a 500 error
        if ($_.Exception.Response.StatusCode -ne 500) {
            Write-Host "✅ Progress: No longer a 500 Internal Server Error!" -ForegroundColor Green
        }
    }
    
} catch {
    Write-Host "❌ Authentication failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`nSchema mismatch fix complete!" -ForegroundColor Cyan
Write-Host "==============================" -ForegroundColor Gray

Write-Host "`nNext step: Run validation tests to see improvements" -ForegroundColor White
Write-Host "  .\simple-test.ps1" -ForegroundColor Green
Write-Host "  .\validate_core_security_fixes.ps1" -ForegroundColor Green
Write-Host "  .\validate-role-based-security.ps1" -ForegroundColor Green