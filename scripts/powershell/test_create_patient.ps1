# Test patient creation via API
Write-Host "=== PATIENT CREATION TEST ===" -ForegroundColor Cyan

# Login first
Write-Host "Getting authentication token..." -ForegroundColor Yellow
$loginHeaders = @{
    'Content-Type' = 'application/x-www-form-urlencoded'
}
$loginBody = "username=admin&password=admin123"

try {
    $loginResponse = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/auth/login" -Method POST -Headers $loginHeaders -Body $loginBody
    $token = $loginResponse.access_token
    Write-Host "✅ Token obtained" -ForegroundColor Green
    
    # Prepare patient data in FHIR R4 format
    $patientData = @{
        identifier = @(
            @{
                use = "official"
                type = @{
                    coding = @(
                        @{
                            system = "http://terminology.hl7.org/CodeSystem/v2-0203"
                            code = "MR"
                        }
                    )
                }
                system = "http://hospital.example.org/patients"
                value = "MRN-001"
            }
        )
        name = @(
            @{
                use = "official"
                family = "Doe"
                given = @("John")
            }
        )
        telecom = @(
            @{
                system = "phone"
                value = "(555) 123-4567"
                use = "home"
            },
            @{
                system = "email"
                value = "john.doe@example.com"
                use = "home"
            }
        )
        gender = "male"
        birthDate = "1990-01-15"
        address = @(
            @{
                use = "home"
                line = @("123 Main St")
                city = "Anytown"
                state = "CA"
                postalCode = "12345"
                country = "US"
            }
        )
        active = $true
        organization_id = "c4c4fec4-c63a-49d1-a5c7-07495c4740b0"  # Use admin user ID as org for now
        consent_status = "pending"
        consent_types = @("treatment")
    } | ConvertTo-Json -Depth 5
    
    $headers = @{
        'Authorization' = "Bearer $token"
        'Content-Type' = 'application/json'
    }
    
    Write-Host "`nCreating patient with data:" -ForegroundColor Yellow
    Write-Host $patientData -ForegroundColor Gray
    
    # Create patient
    Write-Host "`nSending POST request to create patient..." -ForegroundColor Yellow
    $response = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/healthcare/patients" -Method POST -Headers $headers -Body $patientData
    
    Write-Host "✅ Patient created successfully!" -ForegroundColor Green
    Write-Host "Patient ID: $($response.id)" -ForegroundColor White
    Write-Host "MRN: $($response.medical_record_number)" -ForegroundColor White
    Write-Host "Full response:" -ForegroundColor White
    Write-Host ($response | ConvertTo-Json -Depth 3) -ForegroundColor Gray
    
} catch {
    Write-Host "❌ Patient creation failed!" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    
    if ($_.Exception.Response) {
        $statusCode = $_.Exception.Response.StatusCode
        Write-Host "Status Code: $statusCode" -ForegroundColor Red
        
        # Try to get response body
        try {
            $responseStream = $_.Exception.Response.GetResponseStream()
            $reader = New-Object System.IO.StreamReader($responseStream)
            $responseBody = $reader.ReadToEnd()
            Write-Host "Response Body:" -ForegroundColor Red
            Write-Host $responseBody -ForegroundColor Gray
        } catch {
            Write-Host "Could not read response body" -ForegroundColor Yellow
        }
    }
}

Write-Host "`n=== PATIENT CREATION TEST COMPLETE ===" -ForegroundColor Cyan