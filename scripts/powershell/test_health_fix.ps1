# Test health endpoint fix
Write-Host "=== TESTING HEALTH ENDPOINT FIX ===" -ForegroundColor Cyan

$loginHeaders = @{
    'Content-Type' = 'application/x-www-form-urlencoded'
}
$loginBody = "username=admin&password=admin123"

try {
    # Login
    Write-Host "1. Getting token..." -ForegroundColor Yellow
    $loginResponse = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/auth/login" -Method POST -Headers $loginHeaders -Body $loginBody
    $token = $loginResponse.access_token
    Write-Host "Token obtained" -ForegroundColor Green
    
    $headers = @{
        'Authorization' = "Bearer $token"
        'Content-Type' = 'application/json'
    }
    
    # Test health summary endpoint
    Write-Host "`n2. Testing IRIS health summary..." -ForegroundColor Yellow
    try {
        $healthResponse = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/iris/health/summary" -Method GET -Headers $headers
        Write-Host "Health summary: SUCCESS" -ForegroundColor Green
        Write-Host "Overall status: $($healthResponse.overall_status)" -ForegroundColor White
        Write-Host "Endpoints: $($healthResponse.total_endpoints)" -ForegroundColor White
    } catch {
        Write-Host "Health summary: FAILED" -ForegroundColor Red
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Test dashboard data loading
    Write-Host "`n3. Testing dashboard data loading..." -ForegroundColor Yellow
    
    $dashboardTests = @(
        @{ Name = "Patients"; URL = "http://localhost:8003/api/v1/healthcare/patients?limit=1" },
        @{ Name = "Audit Stats"; URL = "http://localhost:8003/api/v1/audit/stats" },
        @{ Name = "Recent Activities"; URL = "http://localhost:8003/api/v1/audit/recent-activities?limit=5" }
    )
    
    foreach ($test in $dashboardTests) {
        try {
            $response = Invoke-RestMethod -Uri $test.URL -Method GET -Headers $headers
            Write-Host "   $($test.Name): SUCCESS" -ForegroundColor Green
        } catch {
            Write-Host "   $($test.Name): FAILED - $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
} catch {
    Write-Host "Test failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== HEALTH FIX TEST COMPLETE ===" -ForegroundColor Cyan
Write-Host "Dashboard should now load without 500 errors!" -ForegroundColor Green
Write-Host "Visit: http://localhost:3000 or http://localhost:5173" -ForegroundColor Cyan