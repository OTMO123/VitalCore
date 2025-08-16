# Simple test for 7th root cause fix
Write-Host "Testing 7th root cause fix..." -ForegroundColor Yellow
docker restart iris_app
Start-Sleep 20

# Auth
$body = "username=admin" + "&" + "password=admin123"
$headers = @{"Content-Type" = "application/x-www-form-urlencoded"}
$auth = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Headers $headers -Body $body
$token = $auth.access_token

$authHeaders = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

# Test patient creation
$patient = @{
    resourceType = "Patient"
    identifier = @(@{ value = "TEST_ENUM_FIX" })
    name = @(@{ family = "Test"; given = @("Enum") })
    gender = "male"
    birthDate = "1990-01-01"
} | ConvertTo-Json -Depth 3

try {
    $result = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients" -Method POST -Headers $authHeaders -Body $patient
    Write-Host "SUCCESS! Patient created: $($result.id)" -ForegroundColor Green
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    docker logs iris_app --tail 5
}