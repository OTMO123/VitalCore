# Debug patient API issue
Write-Host "Debugging patient API..." -ForegroundColor Yellow

# Get auth token
$loginBody = "username=admin&password=admin123"
$loginHeaders = @{"Content-Type" = "application/x-www-form-urlencoded"}
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Headers $loginHeaders -Body $loginBody
$token = $response.access_token
Write-Host "Auth token received" -ForegroundColor Green

$authHeaders = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

# Test different endpoints to see what works
Write-Host "Testing dashboard..." -ForegroundColor Yellow
try {
    $dashboard = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/dashboard/stats" -Headers $authHeaders
    Write-Host "Dashboard works!" -ForegroundColor Green
} catch {
    Write-Host "Dashboard failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "Testing patient list..." -ForegroundColor Yellow
try {
    $patients = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients" -Headers $authHeaders
    Write-Host "Patient list works! Found $($patients.total) patients" -ForegroundColor Green
} catch {
    Write-Host "Patient list failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Checking app logs..." -ForegroundColor Yellow
    docker logs iris_app --tail 5
}

Write-Host "Debug completed" -ForegroundColor Green