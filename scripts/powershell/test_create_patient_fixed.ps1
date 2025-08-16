# Create patient with FIXED encryption
Write-Host "=== CREATING PATIENT WITH FIXED ENCRYPTION ===" -ForegroundColor Cyan

$loginHeaders = @{
    'Content-Type' = 'application/x-www-form-urlencoded'
}
$loginBody = "username=admin&password=admin123"

try {
    $loginResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Headers $loginHeaders -Body $loginBody
    $token = $loginResponse.access_token
    Write-Host "✅ Token obtained" -ForegroundColor Green
    
    # Patient with fixed encryption
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
                value = "MRN-FIXED-001"
            }
        )
        name = @(
            @{
                use = "official"
                family = "Johnson"
                given = @("Alice")
            }
        )
        telecom = @(
            @{
                system = "phone"
                value = "(555) 111-2222"
                use = "mobile"
            },
            @{
                system = "email"
                value = "alice.johnson@example.com"
                use = "work"
            }
        )
        gender = "female"
        birthDate = "1992-07-10"
        address = @(
            @{
                use = "home"
                line = @("789 Pine St")
                city = "Austin"
                state = "TX"
                postalCode = "73301"
                country = "US"
            }
        )
        active = $true
        organization_id = "c4c4fec4-c63a-49d1-a5c7-07495c4740b0"
        consent_status = "active"
        consent_types = @("treatment")
    } | ConvertTo-Json -Depth 5
    
    $headers = @{
        'Authorization' = "Bearer $token"
        'Content-Type' = 'application/json'
    }
    
    Write-Host "`nCreating Alice Johnson with FIXED encryption..." -ForegroundColor Yellow
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients" -Method POST -Headers $headers -Body $patientData
    
    Write-Host "✅ Alice Johnson created with proper encryption!" -ForegroundColor Green
    Write-Host "Patient ID: $($response.id)" -ForegroundColor White
    Write-Host "Name: $($response.name[0].given[0]) $($response.name[0].family)" -ForegroundColor White
    
} catch {
    Write-Host "❌ Failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== FIXED ENCRYPTION TEST COMPLETE ===" -ForegroundColor Cyan