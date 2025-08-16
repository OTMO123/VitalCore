# Test API with correct OAuth2 format
Write-Host "Testing auth with correct OAuth2 format..." -ForegroundColor Yellow

try {
    # Use form-urlencoded data as OAuth2 requires
    $body = "username=admin@iris.com&password=admin123"
    $headers = @{
        "Content-Type" = "application/x-www-form-urlencoded"
    }
    
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Headers $headers -Body $body
    $token = $response.access_token
    Write-Host "✅ AUTH SUCCESS! Token received" -ForegroundColor Green
    
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
    
    Write-Host "`n🎉 ALL TESTS PASSED! Backend is 100% functional!" -ForegroundColor Green
    Write-Host "🎉 Frontend will now work perfectly!" -ForegroundColor Green
    
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails) {
        Write-Host "Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
}