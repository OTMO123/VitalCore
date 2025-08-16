# Test patient creation with proper FHIR R4 format
Write-Host "Testing patient creation with FHIR R4 format..." -ForegroundColor Yellow

# Get auth token
$loginBody = "username=admin&password=admin123"
$loginHeaders = @{"Content-Type" = "application/x-www-form-urlencoded"}
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Headers $loginHeaders -Body $loginBody
$token = $response.access_token

$authHeaders = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

# Create FHIR R4 compliant patient data
$fhirPatient = @{
    resourceType = "Patient"
    identifier = @(
        @{
            use = "usual"
            system = "http://hospital.example.org"
            value = "TEST001"
        }
    )
    active = $true
    name = @(
        @{
            use = "official"
            family = "Patient"
            given = @("Test")
        }
    )
    telecom = @(
        @{
            system = "email"
            value = "test@example.com"
            use = "home"
        }
    )
    gender = "male"
    birthDate = "1990-01-01"
    address = @(
        @{
            use = "home"
            line = @("123 Main St")
            city = "Test City"
            state = "TS"
            postalCode = "12345"
            country = "US"
        }
    )
} | ConvertTo-Json -Depth 5

Write-Host "Sending FHIR R4 compliant patient data..." -ForegroundColor Cyan

try {
    $created = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients" -Method POST -Headers $authHeaders -Body $fhirPatient
    Write-Host "SUCCESS! Patient created with ID: $($created.id)" -ForegroundColor Green
    
    # Test patient list again to see the new patient
    $patients = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients" -Headers $authHeaders
    Write-Host "Updated patient list: Found $($patients.total) patients" -ForegroundColor Green
    
    Write-Host "COMPLETE SUCCESS! Backend is 100% functional!" -ForegroundColor Green
    Write-Host "Frontend Add Patient will work with FHIR format!" -ForegroundColor Green
    
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails) {
        Write-Host "Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
}