# Manual test for Update Patient endpoint
Write-Host "🧪 Testing Update Patient endpoint manually..." -ForegroundColor Cyan

try {
    # Step 1: Get authentication token
    Write-Host "🔑 Getting auth token..." -ForegroundColor Yellow
    $loginBody = @{
        username = "admin"
        password = "admin123"
    } | ConvertTo-Json
    
    $authResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Body $loginBody -ContentType "application/json"
    $token = $authResponse.access_token
    
    Write-Host "✅ Auth token obtained" -ForegroundColor Green
    
    # Step 2: Create a test patient first
    Write-Host "👤 Creating test patient..." -ForegroundColor Yellow
    $headers = @{"Authorization" = "Bearer $token"}
    
    $patientBody = @{
        resourceType = "Patient"
        active = $true
        name = @(@{
            use = "official"
            family = "TestPatient"
            given = @("Update", "Test")
        })
        gender = "unknown"
        birthDate = "1990-01-01"
    } | ConvertTo-Json -Depth 3
    
    $createResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients" -Method POST -Body $patientBody -Headers $headers -ContentType "application/json"
    $patientId = $createResponse.id
    
    Write-Host "✅ Test patient created with ID: $patientId" -ForegroundColor Green
    
    # Step 3: Try to update the patient
    Write-Host "✏️ Updating patient..." -ForegroundColor Yellow
    
    $updateBody = @{
        gender = "female"
        consent_status = "active"
    } | ConvertTo-Json
    
    $updateResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients/$patientId" -Method PUT -Body $updateBody -Headers $headers -ContentType "application/json"
    
    Write-Host "✅ Update successful!" -ForegroundColor Green
    Write-Host "Updated patient data:" -ForegroundColor Cyan
    $updateResponse | ConvertTo-Json -Depth 2
    
} catch {
    Write-Host "❌ Error during manual test:" -ForegroundColor Red
    Write-Host "Status Code: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
    Write-Host "Error Message: $($_.Exception.Message)" -ForegroundColor Red
    
    # Try to get response content
    try {
        $errorStream = $_.Exception.Response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($errorStream)
        $errorContent = $reader.ReadToEnd()
        Write-Host "Error Response: $errorContent" -ForegroundColor Red
    } catch {
        Write-Host "Could not read error response" -ForegroundColor Yellow
    }
}