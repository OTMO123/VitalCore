# Fix Database Schema Mismatch - Simple Version
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

# Step 2: Fix schema using Docker exec with simple Python script
Write-Host "`nStep 2: Fixing schema mismatch..." -ForegroundColor White

Write-Host "Running schema fix in Docker container..." -ForegroundColor Yellow

# Create a simple Python script to fix the schema
$pythonScript = 'import os, re; files = ["app/core/database_advanced.py", "app/modules/audit_logger/service.py", "app/modules/audit_logger/enhanced_audit_service.py"]; [print(f"Fixing {f}...") or open(f, "w").write(re.sub(r"\.result\b", ".outcome", open(f).read())) for f in files if os.path.exists(f)]; print("Schema fix complete")'

docker-compose exec app python -c $pythonScript

# Step 3: Restart application
Write-Host "`nStep 3: Restarting application..." -ForegroundColor White
docker-compose restart app
Start-Sleep 15

# Step 4: Test endpoints
Write-Host "`nStep 4: Testing endpoints..." -ForegroundColor White

try {
    # Authentication
    $loginData = @{ username = "admin"; password = "Admin123!" } | ConvertTo-Json
    $authResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -ContentType "application/json" -Body $loginData
    
    if ($authResponse.access_token) {
        Write-Host "✅ Authentication working" -ForegroundColor Green
        
        $headers = @{
            "Authorization" = "Bearer $($authResponse.access_token)"
            "Content-Type" = "application/json"
        }
        
        # Test audit logs
        Write-Host "Testing audit logs..." -ForegroundColor Yellow
        try {
            $auditResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/audit-logs/logs" -Method GET -Headers $headers
            Write-Host "✅ Audit logs working!" -ForegroundColor Green
        } catch {
            Write-Host "❌ Audit logs failed: $($_.Exception.Message)" -ForegroundColor Red
        }
        
        # Test healthcare patients
        Write-Host "Testing healthcare patients..." -ForegroundColor Yellow
        try {
            $patientsResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients" -Method GET -Headers $headers
            Write-Host "✅ Healthcare patients working!" -ForegroundColor Green
        } catch {
            Write-Host "❌ Healthcare patients failed: $($_.Exception.Message)" -ForegroundColor Red
        }
        
    } else {
        Write-Host "❌ Authentication failed" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Authentication request failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`nSchema fix complete!" -ForegroundColor Cyan
Write-Host "Next: Run validation tests to see improvements" -ForegroundColor White