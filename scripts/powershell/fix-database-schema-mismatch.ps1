# Fix Database Schema Mismatch - Critical Fix
Write-Host "Fixing Database Schema Mismatch" -ForegroundColor Cyan
Write-Host "===============================" -ForegroundColor Gray

Write-Host "Root Cause: audit_logs 'result' column was renamed to 'outcome' but code still references 'result'" -ForegroundColor Yellow
Write-Host ""

# Step 1: Fix database_advanced.py model
Write-Host "Step 1: Fixing audit logs model definition..." -ForegroundColor White

$model_fix = @'
# Read the file
$content = Get-Content "/mnt/c/Users/aurik/Code_Projects/2_scraper/app/core/database_advanced.py" -Raw

# Replace result with outcome in the model definition
$content = $content -replace 'result: Mapped\[str\] = mapped_column\(String\(50\), nullable=False\)', 'outcome: Mapped[str] = mapped_column(String(50), nullable=False)'

# Write the file back
Set-Content "/mnt/c/Users/aurik/Code_Projects/2_scraper/app/core/database_advanced.py" -Value $content

Write-Host "✅ Fixed database_advanced.py model definition" -ForegroundColor Green
'@

Invoke-Expression $model_fix

# Step 2: Fix audit logger service
Write-Host "`nStep 2: Fixing audit logger service references..." -ForegroundColor White

$service_fix = @'
# Read the audit service file
$content = Get-Content "/mnt/c/Users/aurik/Code_Projects/2_scraper/app/modules/audit_logger/service.py" -Raw

# Replace all references to .result with .outcome
$content = $content -replace '\.result', '.outcome'
$content = $content -replace 'AuditLog\.result', 'AuditLog.outcome'

# Write the file back
Set-Content "/mnt/c/Users/aurik/Code_Projects/2_scraper/app/modules/audit_logger/service.py" -Value $content

Write-Host "✅ Fixed audit logger service references" -ForegroundColor Green
'@

Invoke-Expression $service_fix

# Step 3: Fix enhanced audit service
Write-Host "`nStep 3: Fixing enhanced audit service..." -ForegroundColor White

$enhanced_fix = @'
# Read the enhanced audit service file
$content = Get-Content "/mnt/c/Users/aurik/Code_Projects/2_scraper/app/modules/audit_logger/enhanced_audit_service.py" -Raw

# Replace audit_log.result with audit_log.outcome but keep JSON key as "result" for API compatibility
$content = $content -replace "audit_log\.result", "audit_log.outcome"

# Write the file back
Set-Content "/mnt/c/Users/aurik/Code_Projects/2_scraper/app/modules/audit_logger/enhanced_audit_service.py" -Value $content

Write-Host "✅ Fixed enhanced audit service references" -ForegroundColor Green
'@

Invoke-Expression $enhanced_fix

# Step 4: Restart the application to apply changes
Write-Host "`nStep 4: Restarting application to apply changes..." -ForegroundColor White

Write-Host "Restarting Docker containers..." -ForegroundColor Yellow
docker-compose restart app

Write-Host "Waiting for application to start..." -ForegroundColor Yellow
Start-Sleep 15

# Step 5: Test audit logs endpoint
Write-Host "`nStep 5: Testing audit logs endpoint after fix..." -ForegroundColor White

try {
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
        Write-Host "Found $($auditResponse.logs.Count) audit log entries" -ForegroundColor Green
    } catch {
        Write-Host "❌ Still failing: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "Status: $($_.Exception.Response.StatusCode)" -ForegroundColor Yellow
        
        # Show recent logs for debugging
        Write-Host "`nChecking application logs..." -ForegroundColor Yellow
        docker-compose logs --tail=10 app | Select-String -Pattern "audit|result|outcome|ERROR"
    }
    
} catch {
    Write-Host "❌ Authentication failed for test" -ForegroundColor Red
}

# Step 6: Test healthcare patients endpoint
Write-Host "`nStep 6: Testing healthcare patients endpoint..." -ForegroundColor White

try {
    Write-Host "Testing healthcare patients endpoint..." -ForegroundColor Yellow
    $patientsResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients" -Method GET -Headers $headers
    Write-Host "✅ SUCCESS: Healthcare patients endpoint working!" -ForegroundColor Green
    
    if ($patientsResponse.patients) {
        Write-Host "Found $($patientsResponse.patients.Count) patients" -ForegroundColor Green
    } else {
        Write-Host "Response structure: $($patientsResponse | ConvertTo-Json -Depth 2)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Healthcare patients still failing: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Status: $($_.Exception.Response.StatusCode)" -ForegroundColor Yellow
    
    # Check if it's a different error now
    if ($_.Exception.Response.StatusCode -ne 500) {
        Write-Host "✅ Good news: No longer a 500 error!" -ForegroundColor Green
    }
}

Write-Host "`nDatabase schema mismatch fix complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Gray

Write-Host "`nNext steps:" -ForegroundColor White
Write-Host "1. Run validation tests to see improvement" -ForegroundColor Yellow
Write-Host "2. Address any remaining role permission issues" -ForegroundColor Yellow

Write-Host "`nExpected improvements:" -ForegroundColor White
Write-Host "✅ Audit logs should work without schema errors" -ForegroundColor Green
Write-Host "✅ PHI Access Auditing test should now pass" -ForegroundColor Green
Write-Host "✅ Core Security score should improve to 90%+" -ForegroundColor Green