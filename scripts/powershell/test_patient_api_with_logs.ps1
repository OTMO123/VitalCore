# Test Patient API and watch logs
Write-Host "Testing Patient API with live log monitoring..." -ForegroundColor Yellow

# Clear recent logs and test
Write-Host "Starting fresh log monitoring..." -ForegroundColor Cyan

# Get auth token
Write-Host "Step 1: Getting auth token..." -ForegroundColor Yellow
try {
    $loginBody = "username=admin&password=admin123"
    $loginHeaders = @{"Content-Type" = "application/x-www-form-urlencoded"}
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Headers $loginHeaders -Body $loginBody
    $token = $response.access_token
    Write-Host "Auth successful" -ForegroundColor Green
} catch {
    Write-Host "Auth failed: $($_.Exception.Message)" -ForegroundColor Red
    exit
}

$authHeaders = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

# Test patient endpoint and capture exact error
Write-Host "Step 2: Testing patient endpoint..." -ForegroundColor Yellow
try {
    $patients = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients" -Headers $authHeaders
    Write-Host "SUCCESS! Patient API works! Response: $($patients | ConvertTo-Json -Depth 2)" -ForegroundColor Green
} catch {
    Write-Host "Patient API failed: $($_.Exception.Message)" -ForegroundColor Red
    
    # Get detailed error
    if ($_.Exception.Response) {
        Write-Host "Status Code: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
        Write-Host "Status Description: $($_.Exception.Response.StatusDescription)" -ForegroundColor Red
    }
    
    # Show recent logs that might explain the error
    Write-Host "Recent application logs:" -ForegroundColor Yellow
    docker logs iris_app --tail 10
}

Write-Host "Test completed" -ForegroundColor Green