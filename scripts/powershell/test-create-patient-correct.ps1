# Test Patient Creation with FHIR R4 Compliant Schema
# Usage: .\test-create-patient-correct.ps1 [firstName] [lastName]

param(
    [string]$FirstName = "John",
    [string]$LastName = "Doe"
)

$timestamp = Get-Date -Format "yyyyMMddHHmmss"
$patientData = @{
    identifier = @(
        @{
            use = "usual"
            type = @{
                coding = @(
                    @{
                        system = "http://terminology.hl7.org/CodeSystem/v2-0203"
                        code = "MR"
                        display = "Medical record number"
                    }
                )
            }
            value = "MRN$timestamp"
        }
    )
    active = $true
    name = @(
        @{
            use = "official"
            given = @($FirstName)
            family = $LastName
        }
    )
    telecom = @(
        @{
            system = "phone"
            value = "555-0123"
            use = "home"
        },
        @{
            system = "email"
            value = "test@example.com"
            use = "home"
        }
    )
    gender = "unknown"
    birthDate = "1990-01-01"
    address = @(
        @{
            use = "home"
            type = "physical"
            line = @("123 Test Street")
            city = "Test City"
            state = "TS"
            postalCode = "12345"
            country = "US"
        }
    )
    consent_status = "active"
    consent_types = @("treatment", "data_access")
} | ConvertTo-Json -Depth 10

Write-Host "🏥 Creating FHIR R4 compliant patient: $FirstName $LastName" -ForegroundColor Cyan

& .\quick-test.ps1 -Endpoint "/api/v1/healthcare/patients" -Method POST -Body $patientData