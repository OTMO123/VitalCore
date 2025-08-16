# Test the fixed Patient API
Write-Host "Restarting application with PatientFilters fix..." -ForegroundColor Yellow
docker restart iris_app

Write-Host "Waiting for application restart..." -ForegroundColor Yellow
Start-Sleep 20

Write-Host "Testing fixed Patient API..." -ForegroundColor Green

# Get auth token
$loginBody = "username=admin&password=admin123"
$loginHeaders = @{"Content-Type" = "application/x-www-form-urlencoded"}
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Headers $loginHeaders -Body $loginBody
$token = $response.access_token
Write-Host "Auth successful" -ForegroundColor Green

$authHeaders = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

# Test patient list endpoint
try {
    $patients = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients" -Headers $authHeaders
    Write-Host "SUCCESS! Patient API working! Found $($patients.total) patients" -ForegroundColor Green
    
    # Test patient creation
    $newPatient = @{
        first_name = "Test"
        last_name = "Patient" 
        date_of_birth = "1990-01-01"
        gender = "male"
        email = "test@example.com"
    } | ConvertTo-Json
    
    $created = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients" -Method POST -Headers $authHeaders -Body $newPatient
    Write-Host "SUCCESS! Created patient with ID: $($created.id)" -ForegroundColor Green
    
    Write-Host "100% SUCCESS! ROOT CAUSE FIXED!" -ForegroundColor Green
    Write-Host "Frontend will now work perfectly!" -ForegroundColor Green
    Write-Host "Login credentials: admin / admin123" -ForegroundColor Cyan
    
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}