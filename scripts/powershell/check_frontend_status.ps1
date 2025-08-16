# Check frontend and backend status
Write-Host "=== CHECKING FRONTEND AND BACKEND STATUS ===" -ForegroundColor Cyan

# Check if backend is running
Write-Host "1. Checking backend server (port 8003)..." -ForegroundColor Yellow
try {
    $backendResponse = Invoke-WebRequest -Uri "http://localhost:8003/health" -Method GET -UseBasicParsing -TimeoutSec 5
    Write-Host "Backend Status: $($backendResponse.StatusCode) - RUNNING" -ForegroundColor Green
    Write-Host "Backend Response: $($backendResponse.Content)" -ForegroundColor Gray
} catch {
    Write-Host "Backend Status: NOT RUNNING" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Check if frontend is running
Write-Host "`n2. Checking frontend server (port 5173)..." -ForegroundColor Yellow
try {
    $frontendResponse = Invoke-WebRequest -Uri "http://localhost:5173" -Method GET -UseBasicParsing -TimeoutSec 5
    Write-Host "Frontend Status: $($frontendResponse.StatusCode) - RUNNING" -ForegroundColor Green
    Write-Host "Frontend Content Length: $($frontendResponse.Content.Length) bytes" -ForegroundColor Gray
} catch {
    Write-Host "Frontend Status: NOT RUNNING" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "`nTo start frontend:" -ForegroundColor Yellow
    Write-Host "cd frontend" -ForegroundColor White
    Write-Host "npm run dev" -ForegroundColor White
}

# Check if we can login
Write-Host "`n3. Testing authentication..." -ForegroundColor Yellow
try {
    $loginHeaders = @{
        'Content-Type' = 'application/x-www-form-urlencoded'
    }
    $loginBody = "username=admin&password=admin123"
    
    $loginResponse = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/auth/login" -Method POST -Headers $loginHeaders -Body $loginBody -TimeoutSec 5
    Write-Host "Authentication: SUCCESS" -ForegroundColor Green
    Write-Host "Token received: $($loginResponse.access_token.Substring(0,20))..." -ForegroundColor Gray
} catch {
    Write-Host "Authentication: FAILED" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Check if API endpoints are accessible
Write-Host "`n4. Testing API endpoints..." -ForegroundColor Yellow
try {
    # Get token first
    $loginHeaders = @{ 'Content-Type' = 'application/x-www-form-urlencoded' }
    $loginBody = "username=admin&password=admin123"
    $loginResponse = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/auth/login" -Method POST -Headers $loginHeaders -Body $loginBody
    $token = $loginResponse.access_token
    
    $headers = @{
        'Authorization' = "Bearer $token"
        'Content-Type' = 'application/json'
    }
    
    # Test patient endpoint
    $patientsResponse = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/healthcare/patients?limit=1" -Method GET -Headers $headers -TimeoutSec 5
    Write-Host "Patients API: SUCCESS" -ForegroundColor Green
    Write-Host "Patients found: $($patientsResponse.patients.Count)" -ForegroundColor Gray
    
    # Test audit endpoint
    $auditResponse = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/audit/recent-activities?limit=1" -Method GET -Headers $headers -TimeoutSec 5
    Write-Host "Audit API: SUCCESS" -ForegroundColor Green
    Write-Host "Activities found: $($auditResponse.activities.Count)" -ForegroundColor Gray
    
} catch {
    Write-Host "API Tests: FAILED" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== STATUS CHECK COMPLETE ===" -ForegroundColor Cyan
Write-Host "`nIf frontend is not running, start it with:" -ForegroundColor Yellow
Write-Host "cd frontend" -ForegroundColor White
Write-Host "npm run dev" -ForegroundColor White
Write-Host "`nThen visit: http://localhost:5173" -ForegroundColor Cyan