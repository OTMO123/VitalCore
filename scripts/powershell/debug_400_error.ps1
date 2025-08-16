# Debug 400 error - Get detailed error message
Write-Host "🔍 WHY 1: Getting detailed 400 error message..." -ForegroundColor Yellow

# Auth
$body = "username=admin" + "&" + "password=admin123"
$headers = @{"Content-Type" = "application/x-www-form-urlencoded"}
$auth = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Headers $headers -Body $body
$token = $auth.access_token
Write-Host "Auth: SUCCESS" -ForegroundColor Green

$authHeaders = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

# Test patient creation with detailed error capture
$patient = @{
    resourceType = "Patient"
    identifier = @(@{ value = "DEBUG_400_ERROR" })
    name = @(@{ family = "Debug"; given = @("Error") })
    gender = "male"
    birthDate = "1990-01-01"
} | ConvertTo-Json -Depth 3

Write-Host "🎯 Sending request to get detailed 400 error..." -ForegroundColor Yellow
Write-Host "Request Body:" -ForegroundColor Cyan
Write-Host $patient -ForegroundColor White

try {
    $result = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients" -Method POST -Headers $authHeaders -Body $patient
    Write-Host "Unexpected success: $($result.id)" -ForegroundColor Green
} catch {
    Write-Host "Error Status: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
    if ($_.ErrorDetails) {
        Write-Host "Detailed Error Response:" -ForegroundColor Red
        Write-Host $_.ErrorDetails.Message -ForegroundColor Yellow
    }
    if ($_.Exception.Response) {
        Write-Host "Response Headers:" -ForegroundColor Red
        $_.Exception.Response.Headers | ForEach-Object { Write-Host "$($_.Key): $($_.Value)" -ForegroundColor Gray }
    }
}