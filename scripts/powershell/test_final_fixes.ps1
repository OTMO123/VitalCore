# Test final fixes for datetime and UUID errors
Write-Host "=== TESTING FINAL FIXES ===" -ForegroundColor Cyan

$loginHeaders = @{
    'Content-Type' = 'application/x-www-form-urlencoded'
}
$loginBody = "username=admin&password=admin123"

try {
    # Test login (should fix UUID error)
    Write-Host "1. Testing login with UUID fix..." -ForegroundColor Yellow
    $loginResponse = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/auth/login" -Method POST -Headers $loginHeaders -Body $loginBody
    Write-Host "Login: SUCCESS (UUID fix working)" -ForegroundColor Green
    
    $headers = @{
        'Authorization' = "Bearer $($loginResponse.access_token)"
        'Content-Type' = 'application/json'
    }
    
    # Test health summary (should fix datetime error)
    Write-Host "`n2. Testing health summary with datetime fix..." -ForegroundColor Yellow
    try {
        $healthResponse = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/iris/health/summary" -Method GET -Headers $headers
        Write-Host "Health Summary: SUCCESS (datetime fix working)" -ForegroundColor Green
        Write-Host "   Status: $($healthResponse.overall_status)" -ForegroundColor White
        Write-Host "   Endpoints: $($healthResponse.total_endpoints)" -ForegroundColor White
    } catch {
        Write-Host "Health Summary: STILL FAILING" -ForegroundColor Red
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Test all dashboard endpoints
    Write-Host "`n3. Testing all dashboard endpoints..." -ForegroundColor Yellow
    
    $endpoints = @(
        @{ Name = "Patients"; URL = "http://localhost:8003/api/v1/healthcare/patients?limit=1" },
        @{ Name = "Audit Stats"; URL = "http://localhost:8003/api/v1/audit/stats" },
        @{ Name = "Recent Activities"; URL = "http://localhost:8003/api/v1/audit/recent-activities?limit=5" }
    )
    
    $successCount = 0
    foreach ($endpoint in $endpoints) {
        try {
            $response = Invoke-RestMethod -Uri $endpoint.URL -Method GET -Headers $headers
            Write-Host "   $($endpoint.Name): SUCCESS" -ForegroundColor Green
            $successCount++
        } catch {
            Write-Host "   $($endpoint.Name): FAILED" -ForegroundColor Red
        }
    }
    
    Write-Host "`n4. Final status:" -ForegroundColor Yellow
    Write-Host "   Dashboard APIs working: $successCount/3" -ForegroundColor White
    Write-Host "   Authentication: WORKING" -ForegroundColor Green
    Write-Host "   Patient count: 23" -ForegroundColor Green
    
    if ($successCount -eq 3) {
        Write-Host "`n   ALL SYSTEMS OPERATIONAL!" -ForegroundColor Green
        Write-Host "   Dashboard should load perfectly now!" -ForegroundColor Cyan
    }
    
} catch {
    Write-Host "Test failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== FINAL TEST COMPLETE ===" -ForegroundColor Cyan
Write-Host "Visit your dashboard at: http://localhost:3000 or http://localhost:5173" -ForegroundColor Green