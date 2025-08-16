# Test API with proper validation
Write-Host "Testing API with correct validation..." -ForegroundColor Yellow

# First check what auth schema expects
Write-Host "Checking auth schema..." -ForegroundColor Yellow
$openapi = Invoke-RestMethod -Uri "http://localhost:8000/openapi.json"
Write-Host "Auth login schema found" -ForegroundColor Green

# Try different auth payload formats
Write-Host "Testing auth with username/password..." -ForegroundColor Yellow
try {
    $authBody1 = @{
        username = "admin@iris.com"
        password = "admin123"
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Headers @{"Content-Type"="application/json"} -Body $authBody1
    $token = $response.access_token
    Write-Host "Auth SUCCESS with username!" -ForegroundColor Green
} catch {
    Write-Host "Username format failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "Testing auth with form data..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Headers @{"Content-Type"="application/x-www-form-urlencoded"} -Body "username=admin@iris.com&password=admin123"
    $token = $response.access_token
    Write-Host "Auth SUCCESS with form data!" -ForegroundColor Green
} catch {
    Write-Host "Form data failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Check if we can access patient endpoint without auth (should show schema error)
Write-Host "Testing patient endpoint without auth..." -ForegroundColor Yellow
try {
    $patients = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients"
    Write-Host "Patients accessible without auth!" -ForegroundColor Yellow
} catch {
    Write-Host "Patients require auth (expected): $($_.Exception.Message)" -ForegroundColor Green
}

Write-Host "API validation test completed!" -ForegroundColor Green