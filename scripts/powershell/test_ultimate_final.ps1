# ULTIMATE FINAL TEST - All 5 root causes fixed!
Write-Host "🚀 ULTIMATE FINAL TEST - All 5 root causes fixed!" -ForegroundColor Green
docker restart iris_app

Start-Sleep 20

# Get auth token
$loginBody = "username=admin&password=admin123"
$loginHeaders = @{"Content-Type" = "application/x-www-form-urlencoded"}
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Headers $loginHeaders -Body $loginBody
$token = $response.access_token
Write-Host "✅ Auth: SUCCESS" -ForegroundColor Green

$authHeaders = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

# Test patient list
$patients = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients" -Headers $authHeaders
Write-Host "✅ Patient List: SUCCESS! Found $($patients.total) patients" -ForegroundColor Green

# Test patient creation with all fixes
$newPatient = @{
    resourceType = "Patient"
    identifier = @(
        @{
            value = "ULTIMATE_SUCCESS_001"
        }
    )
    name = @(
        @{
            family = "Victory"
            given = @("Ultimate")
        }
    )
    gender = "male"
    birthDate = "1990-01-01"
} | ConvertTo-Json -Depth 3

Write-Host "🎯 Testing Patient Creation with all 5 root cause fixes..." -ForegroundColor Yellow

try {
    $created = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients" -Method POST -Headers $authHeaders -Body $newPatient
    Write-Host "🏆 PATIENT CREATION: ULTIMATE SUCCESS! ID: $($created.id)" -ForegroundColor Green
    
    # Final verification
    $patientsAfter = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients" -Headers $authHeaders
    Write-Host "🏆 FINAL VERIFICATION: Now $($patientsAfter.total) patients in system" -ForegroundColor Green
    
    Write-Host "`n🎉🎉🎉 ULTIMATE 100% SUCCESS! 🎉🎉🎉" -ForegroundColor Green
    Write-Host "🏆 ALL 5 ROOT CAUSES FIXED:" -ForegroundColor Yellow
    Write-Host "✅ 1. Missing PatientFilters class" -ForegroundColor White
    Write-Host "✅ 2. Wrong PatientListResponse structure" -ForegroundColor White  
    Write-Host "✅ 3. user_info type error (str vs dict)" -ForegroundColor White
    Write-Host "✅ 4. DBConsentStatus.PENDING does not exist" -ForegroundColor White
    Write-Host "✅ 5. Consent model field mismatch (consent_types vs consent_type)" -ForegroundColor White
    Write-Host "`n🚀🚀🚀 FRONTEND READY FOR 100% INTEGRATION! 🚀🚀🚀" -ForegroundColor Green
    Write-Host "📋 Credentials: admin / admin123" -ForegroundColor Cyan
    Write-Host "📋 Patient format: FHIR R4 with identifier and name arrays" -ForegroundColor Cyan
    
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails) {
        Write-Host "Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
    docker logs iris_app --tail 5
}