# Debug patient creation 422 error
Write-Host "Debugging patient creation 422 error..." -ForegroundColor Yellow

# Get auth token
$loginBody = "username=admin&password=admin123"
$loginHeaders = @{"Content-Type" = "application/x-www-form-urlencoded"}
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Headers $loginHeaders -Body $loginBody
$token = $response.access_token

$authHeaders = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

# Test with detailed error handling
Write-Host "Testing patient creation with error details..." -ForegroundColor Cyan

$newPatient = @{
    first_name = "Test"
    last_name = "Patient"
    date_of_birth = "1990-01-01"
    gender = "male"
    email = "test@example.com"
} | ConvertTo-Json

try {
    $created = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients" -Method POST -Headers $authHeaders -Body $newPatient
    Write-Host "Success: $($created.id)" -ForegroundColor Green
} catch {
    Write-Host "Error details:" -ForegroundColor Red
    Write-Host "Status: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
    
    if ($_.ErrorDetails) {
        Write-Host "Validation Error Details:" -ForegroundColor Yellow
        Write-Host $_.ErrorDetails.Message -ForegroundColor Yellow
    }
    
    # Check app logs for more details
    Write-Host "Recent app logs:" -ForegroundColor Cyan
    docker logs iris_app --tail 8
}