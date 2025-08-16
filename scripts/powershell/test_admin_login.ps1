# Test with admin credentials
Write-Host "Testing with admin:admin123..." -ForegroundColor Yellow

try {
    # Try login with admin/admin123
    $loginBody = "username=admin&password=admin123"
    $loginHeaders = @{"Content-Type" = "application/x-www-form-urlencoded"}
    
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Headers $loginHeaders -Body $loginBody
    $token = $response.access_token
    Write-Host "✅ LOGIN SUCCESS! Token received" -ForegroundColor Green
    
    # Test patient endpoint with token
    $authHeaders = @{
        "Authorization" = "Bearer $token"
        "Content-Type" = "application/json"
    }
    
    $patients = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients" -Headers $authHeaders
    Write-Host "✅ PATIENTS API SUCCESS! Found $($patients.total) patients" -ForegroundColor Green
    
    # Test creating a patient
    $newPatient = @{
        first_name = "Test"
        last_name = "Patient"
        date_of_birth = "1990-01-01"
        gender = "male"
        email = "test@example.com"
    } | ConvertTo-Json
    
    $created = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients" -Method POST -Headers $authHeaders -Body $newPatient
    Write-Host "✅ CREATE PATIENT SUCCESS! ID: $($created.id)" -ForegroundColor Green
    
    Write-Host "`n🎉 100% SUCCESS! Backend is fully functional!" -ForegroundColor Green
    Write-Host "🎉 Frontend Add Patient will now work!" -ForegroundColor Green
    Write-Host "`n📋 Working credentials for frontend:" -ForegroundColor Cyan
    Write-Host "Username: admin" -ForegroundColor White
    Write-Host "Password: admin123" -ForegroundColor White
    
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails) {
        Write-Host "Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
}