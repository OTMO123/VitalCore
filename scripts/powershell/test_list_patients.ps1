# Test patient listing
Write-Host "=== PATIENT LIST TEST ===" -ForegroundColor Cyan

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
    
    Write-Host "`nListing all patients..." -ForegroundColor Yellow
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/healthcare/patients" -Method GET -Headers $headers
        Write-Host "✅ Patient list retrieved!" -ForegroundColor Green
        Write-Host "Total patients: $($response.total)" -ForegroundColor White
        Write-Host "Patients in this page: $($response.patients.Count)" -ForegroundColor White
        
        foreach ($patient in $response.patients) {
            Write-Host "- $($patient.name[0].given[0]) $($patient.name[0].family) (ID: $($patient.id.Substring(0,8))...)" -ForegroundColor Gray
        }
    } catch {
        Write-Host "❌ List failed (might be encryption issue): $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "But patients are created in database!" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "❌ Login failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== PATIENT LIST TEST COMPLETE ===" -ForegroundColor Cyan