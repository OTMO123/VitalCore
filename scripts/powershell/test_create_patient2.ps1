# Create second patient for testing
Write-Host "=== CREATING SECOND PATIENT ===" -ForegroundColor Cyan

$loginHeaders = @{
    'Content-Type' = 'application/x-www-form-urlencoded'
}
$loginBody = "username=admin&password=admin123"

try {
    $loginResponse = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/auth/login" -Method POST -Headers $loginHeaders -Body $loginBody
    $token = $loginResponse.access_token
    Write-Host "✅ Token obtained" -ForegroundColor Green
    
    # Second patient data
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
                value = "MRN-002"
            }
        )
        name = @(
            @{
                use = "official"
                family = "Smith"
                given = @("Jane")
            }
        )
        telecom = @(
            @{
                system = "phone"
                value = "(555) 987-6543"
                use = "mobile"
            },
            @{
                system = "email"
                value = "jane.smith@example.com"
                use = "work"
            }
        )
        gender = "female"
        birthDate = "1985-03-22"
        address = @(
            @{
                use = "home"
                line = @("456 Oak Ave")
                city = "Springfield"
                state = "IL"
                postalCode = "62701"
                country = "US"
            }
        )
        active = $true
        organization_id = "c4c4fec4-c63a-49d1-a5c7-07495c4740b0"
        consent_status = "active"
        consent_types = @("treatment", "research")
    } | ConvertTo-Json -Depth 5
    
    $headers = @{
        'Authorization' = "Bearer $token"
        'Content-Type' = 'application/json'
    }
    
    Write-Host "`nCreating Jane Smith..." -ForegroundColor Yellow
    $response = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/healthcare/patients" -Method POST -Headers $headers -Body $patientData
    
    Write-Host "✅ Jane Smith created!" -ForegroundColor Green
    Write-Host "Patient ID: $($response.id)" -ForegroundColor White
    Write-Host "Name: $($response.name[0].given[0]) $($response.name[0].family)" -ForegroundColor White
    
} catch {
    Write-Host "❌ Failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== SECOND PATIENT TEST COMPLETE ===" -ForegroundColor Cyan