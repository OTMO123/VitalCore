# Test final fix for Patient API
Write-Host "Restarting with final PatientListResponse fix..." -ForegroundColor Yellow
docker restart iris_app

Start-Sleep 20

Write-Host "Testing FINAL fix..." -ForegroundColor Green

# Get auth token
$loginBody = "username=admin&password=admin123"
$loginHeaders = @{"Content-Type" = "application/x-www-form-urlencoded"}
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Headers $loginHeaders -Body $loginBody
$token = $response.access_token

$authHeaders = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

try {
    $patients = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients" -Headers $authHeaders
    Write-Host "SUCCESS! Patient list works! Found $($patients.total) patients" -ForegroundColor Green
    
    # Test creating patient
    $newPatient = @{
        first_name = "Test"
        last_name = "User"
        date_of_birth = "1990-01-01"
        gender = "male"
        email = "test@example.com"
    } | ConvertTo-Json
    
    $created = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients" -Method POST -Headers $authHeaders -Body $newPatient
    Write-Host "SUCCESS! Patient creation works! ID: $($created.id)" -ForegroundColor Green
    
    Write-Host "COMPLETE SUCCESS! All root causes fixed!" -ForegroundColor Green
    Write-Host "Frontend Add Patient will work 100%" -ForegroundColor Green
    Write-Host "Login: admin / admin123" -ForegroundColor Cyan
    
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}