# Check PostgreSQL Connection and Application Status
# This script checks if PostgreSQL is accessible and the application is working

Write-Host "=== POSTGRESQL CONNECTION AND APPLICATION STATUS CHECK ===" -ForegroundColor Cyan

# Step 1: Check if containers are running
Write-Host "`n1. Checking Docker containers..." -ForegroundColor Green
try {
    $containers = docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    Write-Host $containers
    Write-Host "Docker containers are running" -ForegroundColor Green
} catch {
    Write-Host "Docker command failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Step 2: Check if PostgreSQL port is accessible
Write-Host "`n2. Checking PostgreSQL port accessibility..." -ForegroundColor Green
try {
    $pgConnection = Test-NetConnection -ComputerName localhost -Port 5432 -WarningAction SilentlyContinue
    if ($pgConnection.TcpTestSucceeded) {
        Write-Host "PostgreSQL port 5432 is accessible" -ForegroundColor Green
    } else {
        Write-Host "PostgreSQL port 5432 is not accessible" -ForegroundColor Red
    }
} catch {
    Write-Host "Port test failed: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Step 3: Check if application is running
Write-Host "`n3. Checking application status..." -ForegroundColor Green
try {
    $healthResponse = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get -TimeoutSec 5
    if ($healthResponse.status -eq "healthy") {
        Write-Host "Application is healthy: $($healthResponse.service)" -ForegroundColor Green
    } else {
        Write-Host "Application status: $($healthResponse.status)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Application health check failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Step 4: Check PostgreSQL connection through application
Write-Host "`n4. Testing database connection through application..." -ForegroundColor Green
try {
    # Try to get authentication first (this tests database connectivity)
    $loginResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method Post -ContentType "application/json" -Body '{"username":"admin","password":"admin123"}' -TimeoutSec 10
    if ($loginResponse.access_token) {
        Write-Host "Database connection through application is working" -ForegroundColor Green
        $token = $loginResponse.access_token
        
        # Test a database query
        $headers = @{"Authorization" = "Bearer $token"}
        $patientsResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients" -Method Get -Headers $headers -TimeoutSec 10
        Write-Host "Database queries are working - found $($patientsResponse.patients.Count) patients" -ForegroundColor Green
    } else {
        Write-Host "Authentication failed - database may not be accessible" -ForegroundColor Red
    }
} catch {
    Write-Host "Database test through application failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Step 5: Check logs for any obvious errors
Write-Host "`n5. Checking application logs..." -ForegroundColor Green
try {
    $logs = docker logs iris_app --tail 20 2>&1
    if ($logs -match "error|Error|ERROR|exception|Exception|EXCEPTION") {
        Write-Host "Found potential errors in logs:" -ForegroundColor Yellow
        $logs | Select-String -Pattern "error|Error|ERROR|exception|Exception|EXCEPTION" | ForEach-Object {
            Write-Host "  $($_.Line)" -ForegroundColor Red
        }
    } else {
        Write-Host "No obvious errors found in recent logs" -ForegroundColor Green
    }
} catch {
    Write-Host "Could not check application logs: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host "`n=== DIAGNOSTIC SUMMARY ===" -ForegroundColor Cyan
Write-Host "If all checks above are green, the system is ready for testing" -ForegroundColor White
Write-Host "If any checks are red, investigate those specific issues" -ForegroundColor White

Write-Host "`nNext step: Run the comprehensive debug script:" -ForegroundColor Yellow
Write-Host ".\debug_get_patient_comprehensive.ps1" -ForegroundColor White