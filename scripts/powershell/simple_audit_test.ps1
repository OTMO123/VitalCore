# Simple audit logging test
Write-Host "=== TESTING AUDIT LOGGING ===" -ForegroundColor Cyan

$loginHeaders = @{
    'Content-Type' = 'application/x-www-form-urlencoded'
}
$loginBody = "username=admin&password=admin123"

try {
    # Login
    Write-Host "1. Getting token..." -ForegroundColor Yellow
    $loginResponse = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/auth/login" -Method POST -Headers $loginHeaders -Body $loginBody
    $token = $loginResponse.access_token
    Write-Host "Token obtained successfully" -ForegroundColor Green
    
    $headers = @{
        'Authorization' = "Bearer $token"
        'Content-Type' = 'application/json'
    }
    
    # Check current activities
    Write-Host "`n2. Checking current activities..." -ForegroundColor Yellow
    $activitiesResponse = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/audit/recent-activities?limit=10" -Method GET -Headers $headers
    Write-Host "Current activities found: $($activitiesResponse.activities.Count)" -ForegroundColor White
    
    # Create one more patient
    Write-Host "`n3. Creating one more test patient..." -ForegroundColor Yellow
    $patientData = @{
        name = @(
            @{
                family = "FinalTest"
                given = @("Audit")
            }
        )
        gender = "unknown"
        birthDate = "2000-01-01" 
        active = $true
    } | ConvertTo-Json -Depth 5
    
    $patientResponse = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/healthcare/patients" -Method POST -Headers $headers -Body $patientData
    Write-Host "Patient created: $($patientResponse.id)" -ForegroundColor Green
    
    # Check activities again
    Write-Host "`n4. Checking activities after creation..." -ForegroundColor Yellow
    Start-Sleep -Seconds 2
    $activitiesResponse2 = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/audit/recent-activities?limit=10" -Method GET -Headers $headers
    Write-Host "Activities after creation: $($activitiesResponse2.activities.Count)" -ForegroundColor White
    
    if ($activitiesResponse2.activities.Count -gt 0) {
        Write-Host "SUCCESS! Audit logging is working!" -ForegroundColor Green
        foreach ($activity in $activitiesResponse2.activities) {
            Write-Host "  - $($activity.description)" -ForegroundColor Cyan
        }
    } else {
        Write-Host "No audit activities found - check server logs" -ForegroundColor Yellow
    }
    
    # Check patient list
    Write-Host "`n5. Verifying patient list..." -ForegroundColor Yellow
    $patientsResponse = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/healthcare/patients?limit=3" -Method GET -Headers $headers
    Write-Host "Total patients in system: $($patientsResponse.patients.Count)" -ForegroundColor White
    
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== TEST COMPLETE ===" -ForegroundColor Cyan
Write-Host "Visit http://localhost:5173 to check the dashboard!" -ForegroundColor Green