# Debug 400 error - simple version
Write-Host "Getting detailed 400 error..." -ForegroundColor Yellow

# Auth
$body = "username=admin&password=admin123"
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
    identifier = @(@{ value = "DEBUG_400" })
    name = @(@{ family = "Debug"; given = @("Test") })
    gender = "male"
    birthDate = "1990-01-01"
} | ConvertTo-Json -Depth 3

Write-Host "Sending request..." -ForegroundColor Yellow

try {
    $result = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients" -Method POST -Headers $authHeaders -Body $patient
    Write-Host "Success: $($result.id)" -ForegroundColor Green
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails) {
        Write-Host "Details: $($_.ErrorDetails.Message)" -ForegroundColor Yellow
    }
}