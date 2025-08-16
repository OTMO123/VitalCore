# Simple 5 Whys Success Test
Write-Host "=== 5 WHYS UUID FIX VERIFICATION ===" -ForegroundColor Cyan

$baseUrl = "http://localhost:8000"
$successCount = 0

try {
    # Login
    $loginBody = "username=admin&password=admin123"
    $loginResponse = Invoke-RestMethod -Uri "$baseUrl/api/v1/auth/login" -Method POST -Headers @{'Content-Type'='application/x-www-form-urlencoded'} -Body $loginBody
    $token = $loginResponse.access_token
    Write-Host "Auth Success: Token obtained" -ForegroundColor Green
    
    # Test patient creation
    $patientData = @{
        identifier = @(@{value = "TEST-SUCCESS-$(Get-Random)"})
        name = @(@{family = "TestSuccess"; given = @("UUID", "Fixed")})
    } | ConvertTo-Json -Depth 3
    
    $headers = @{
        'Authorization' = "Bearer $token"
        'Content-Type' = 'application/json'
    }
    
    $response = Invoke-RestMethod -Uri "$baseUrl/api/v1/healthcare/patients" -Method POST -Headers $headers -Body $patientData
    
    if ($response.id) {
        Write-Host "SUCCESS: Patient created with ID: $($response.id)" -ForegroundColor Green
        Write-Host "Name: $($response.name[0].given[0]) $($response.name[0].family)" -ForegroundColor White
        $successCount = 1
    }
}
catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Message -like "*UUID*") {
        Write-Host "UUID ERROR DETECTED - 5 Whys fix did not work!" -ForegroundColor Red
    }
}

if ($successCount -eq 1) {
    Write-Host ""
    Write-Host "RESULT: 5 WHYS FRAMEWORK SUCCESS!" -ForegroundColor Green
    Write-Host "UUID problem is FIXED!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "RESULT: 5 Whys fix needs more work" -ForegroundColor Red
}