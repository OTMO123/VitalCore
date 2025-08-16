# Fix Database Schema Mismatch - Working Version
Write-Host "Fixing Database Schema Mismatch" -ForegroundColor Cyan
Write-Host "===============================" -ForegroundColor Gray

# Step 1: Check application status
Write-Host "Step 1: Checking application status..." -ForegroundColor White

try {
    $healthResponse = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 10
    Write-Host "✅ Application is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Application not responding, starting..." -ForegroundColor Red
    docker-compose up -d
    Start-Sleep 20
}

# Step 2: Fix schema using a proper Python script
Write-Host "`nStep 2: Fixing schema mismatch..." -ForegroundColor White

Write-Host "Creating schema fix script..." -ForegroundColor Yellow

# Create the Python script as a separate step
$pythonCode = @'
import os
import re

files_to_fix = [
    "app/core/database_advanced.py",
    "app/modules/audit_logger/service.py", 
    "app/modules/audit_logger/enhanced_audit_service.py"
]

fixed_count = 0

for file_path in files_to_fix:
    if os.path.exists(file_path):
        print(f"Processing {file_path}...")
        
        with open(file_path, "r") as f:
            content = f.read()
        
        # Replace .result with .outcome
        new_content = re.sub(r"\.result\b", ".outcome", content)
        
        if new_content != content:
            with open(file_path, "w") as f:
                f.write(new_content)
            print(f"  ✅ Fixed {file_path}")
            fixed_count += 1
        else:
            print(f"  ✅ {file_path} already correct")
    else:
        print(f"  ❌ {file_path} not found")

print(f"\nFixed {fixed_count} files")
'@

# Write the Python script to a temporary file and execute it
$pythonCode | Out-File -FilePath "temp_fix_schema.py" -Encoding UTF8

Write-Host "Running schema fix in Docker container..." -ForegroundColor Yellow
docker-compose exec app python temp_fix_schema.py

# Clean up temp file
Remove-Item "temp_fix_schema.py" -ErrorAction SilentlyContinue

# Step 3: Restart application
Write-Host "`nStep 3: Restarting application..." -ForegroundColor White
docker-compose restart app
Write-Host "Waiting for application to start..." -ForegroundColor Yellow
Start-Sleep 20

# Step 4: Test endpoints
Write-Host "`nStep 4: Testing endpoints..." -ForegroundColor White

try {
    # Test health first
    $healthResponse = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 10
    Write-Host "✅ Application health check passed" -ForegroundColor Green
    
    # Authentication
    $loginData = @{ username = "admin"; password = "Admin123!" } | ConvertTo-Json
    $authResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -ContentType "application/json" -Body $loginData -TimeoutSec 10
    
    if ($authResponse.access_token) {
        Write-Host "✅ Authentication working" -ForegroundColor Green
        
        $headers = @{
            "Authorization" = "Bearer $($authResponse.access_token)"
            "Content-Type" = "application/json"
        }
        
        # Test audit logs
        Write-Host "`nTesting audit logs..." -ForegroundColor Yellow
        try {
            $auditResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/audit-logs/logs" -Method GET -Headers $headers -TimeoutSec 10
            Write-Host "✅ SUCCESS: Audit logs working!" -ForegroundColor Green
        } catch {
            Write-Host "❌ Audit logs failed: $($_.Exception.Message)" -ForegroundColor Red
            if ($_.Exception.Response) {
                Write-Host "Status: $($_.Exception.Response.StatusCode)" -ForegroundColor Yellow
            }
        }
        
        # Test healthcare patients
        Write-Host "`nTesting healthcare patients..." -ForegroundColor Yellow
        try {
            $patientsResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients" -Method GET -Headers $headers -TimeoutSec 10
            Write-Host "✅ SUCCESS: Healthcare patients working!" -ForegroundColor Green
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
    Write-Host "❌ Request failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`nSchema fix complete!" -ForegroundColor Cyan
Write-Host "===================" -ForegroundColor Gray

Write-Host "`nNext steps:" -ForegroundColor White
Write-Host "Run validation tests:" -ForegroundColor Yellow
Write-Host "  .\simple-test.ps1" -ForegroundColor Green
Write-Host "  .\validate_core_security_fixes.ps1" -ForegroundColor Green
Write-Host "  .\validate-role-based-security.ps1" -ForegroundColor Green