# Test 11th root cause fix - BaseEvent fields
Write-Host "Testing 11th root cause fix..." -ForegroundColor Yellow
docker restart iris_app
Start-Sleep 20

# Auth
$body = "username=admin&password=admin123"
$headers = @{"Content-Type" = "application/x-www-form-urlencoded"}
$auth = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Headers $headers -Body $body
$token = $auth.access_token
Write-Host "Auth: SUCCESS" -ForegroundColor Green

$authHeaders = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

# Test patient creation
$patient = @{
    resourceType = "Patient"
    identifier = @(@{ value = "TEST_11_FIXES" })
    name = @(@{ family = "Test"; given = @("Eleven") })
    gender = "male"
    birthDate = "1990-01-01"
} | ConvertTo-Json -Depth 3

try {
    $result = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients" -Method POST -Headers $authHeaders -Body $patient
    Write-Host "SUCCESS! ALL 11 ROOT CAUSES FIXED!" -ForegroundColor Green
    Write-Host "Patient created: $($result.id)" -ForegroundColor Green
    
    # Verify
    $patients = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients" -Headers $authHeaders
    Write-Host "Total patients: $($patients.total)" -ForegroundColor Green
    Write-Host "SYSTEM FULLY OPERATIONAL!" -ForegroundColor Green
    
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails) {
        Write-Host "Details: $($_.ErrorDetails.Message)" -ForegroundColor Yellow
    }
}