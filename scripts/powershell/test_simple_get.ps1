# Test if basic patient list endpoint works
Write-Host "=== SIMPLE PATIENT LIST TEST ===" -ForegroundColor Cyan

# Login
$loginHeaders = @{
    'Content-Type' = 'application/x-www-form-urlencoded'
}
$loginBody = "username=admin&password=admin123"

try {
    $loginResponse = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/auth/login" -Method POST -Headers $loginHeaders -Body $loginBody
    $token = $loginResponse.access_token
    Write-Host "✅ Token obtained" -ForegroundColor Green
    
    $headers = @{
        'Authorization' = "Bearer $token"
        'Content-Type' = 'application/json'
    }
    
    # Test GET patients (this was working)
    Write-Host "`nTesting GET /api/v1/healthcare/patients..." -ForegroundColor Yellow
    $response = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/healthcare/patients" -Method GET -Headers $headers
    Write-Host "✅ GET patients works" -ForegroundColor Green
    Write-Host "Response: $($response | ConvertTo-Json)" -ForegroundColor Gray
    
} catch {
    Write-Host "❌ Failed: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        Write-Host "Status: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
    }
}

Write-Host "`n=== SIMPLE TEST COMPLETE ===" -ForegroundColor Cyan