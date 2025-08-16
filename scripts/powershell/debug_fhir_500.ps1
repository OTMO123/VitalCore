# Debug FHIR patient creation 500 error  
Write-Host "Debugging FHIR patient creation 500 error..." -ForegroundColor Yellow

# Get auth token
$loginBody = "username=admin&password=admin123"
$loginHeaders = @{"Content-Type" = "application/x-www-form-urlencoded"}
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Headers $loginHeaders -Body $loginBody
$token = $response.access_token

$authHeaders = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

# Test simple patient data first
Write-Host "Testing simple patient creation..." -ForegroundColor Cyan

$simplePatient = @{
    resourceType = "Patient"
    identifier = @(
        @{
            value = "TEST001"
        }
    )
    name = @(
        @{
            family = "Test"
            given = @("Patient")
        }
    )
    gender = "male"
    birthDate = "1990-01-01"
} | ConvertTo-Json -Depth 3

try {
    $created = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients" -Method POST -Headers $authHeaders -Body $simplePatient
    Write-Host "Simple patient creation: SUCCESS!" -ForegroundColor Green
} catch {
    Write-Host "Simple patient creation failed: $($_.Exception.Message)" -ForegroundColor Red
    
    # Get detailed error from logs
    Write-Host "Application logs during patient creation:" -ForegroundColor Yellow
    docker logs iris_app --tail 15
}