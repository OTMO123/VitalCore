# Test Patient Creation
# Usage: .\test-create-patient.ps1 [name]

param(
    [string]$PatientName = "Test Patient $(Get-Date -Format 'HHmm')"
)

$patientData = @{
    given_name = $PatientName.Split(' ')[0]
    family_name = $PatientName.Split(' ')[-1] 
    date_of_birth = "1990-01-01"
    gender = "other"
    phone = "555-0123"
    email = "test@example.com"
    address_line1 = "123 Test St"
    city = "Test City"
    state = "TS"
    zip_code = "12345"
} | ConvertTo-Json

Write-Host "🏥 Creating patient: $PatientName" -ForegroundColor Cyan

& .\quick-test.ps1 -Endpoint "/api/v1/healthcare/patients" -Method POST -Body $patientData