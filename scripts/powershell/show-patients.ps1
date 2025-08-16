# Show All Patients
# Usage: .\show-patients.ps1

Write-Host "Patient List:" -ForegroundColor Cyan

$response = & .\quick-test.ps1 "/api/v1/healthcare/patients"

# If we got patients, show them nicely
if ($response -and $response.patients) {
    Write-Host "`nFound $($response.total) patients:" -ForegroundColor Green
    
    foreach ($patient in $response.patients) {
        Write-Host "`n--- Patient ---" -ForegroundColor Yellow
        Write-Host "ID: $($patient.id)" -ForegroundColor White
        Write-Host "Name: $($patient.name[0].given[0]) $($patient.name[0].family)" -ForegroundColor White
        Write-Host "Gender: $($patient.gender)" -ForegroundColor White
        Write-Host "Birth Date: $($patient.birthDate)" -ForegroundColor White
        Write-Host "Created: $($patient.created_at)" -ForegroundColor Gray
    }
} else {
    Write-Host "No patients found or error occurred" -ForegroundColor Red
}