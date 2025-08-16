# Simple test for Update Patient endpoint
Write-Host "Testing Update Patient endpoint..." -ForegroundColor Cyan

try {
    # Get auth token
    $loginBody = @{username="admin"; password="admin123"} | ConvertTo-Json
    $authResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Body $loginBody -ContentType "application/json"
    $token = $authResponse.access_token
    Write-Host "Auth token obtained" -ForegroundColor Green
    
    # Test 1: Try debug endpoint first to verify it exists
    $headers = @{"Authorization" = "Bearer $token"}
    Write-Host "Testing debug endpoint..." -ForegroundColor Yellow
    
    try {
        $debugResult = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/debug-timestamp" -Method GET -Headers $headers
        Write-Host "Debug endpoint works: $($debugResult.message)" -ForegroundColor Green
    } catch {
        Write-Host "Debug endpoint failed: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Test 2: Create a fresh patient first
    Write-Host "Creating test patient..." -ForegroundColor Yellow
    $patientBody = @{
        resourceType = "Patient"
        active = $true
        name = @(@{use="official"; family="TestUpdate"; given=@("Simple")})
        gender = "unknown"
        birthDate = "1990-01-01"
    } | ConvertTo-Json -Depth 3
    
    $createResult = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients" -Method POST -Body $patientBody -Headers $headers -ContentType "application/json"
    $patientId = $createResult.id
    Write-Host "Created patient with ID: $patientId" -ForegroundColor Green
    
    # Test 3: Try simple update with minimal data
    Write-Host "Testing simple update..." -ForegroundColor Yellow
    $updateBody = @{gender="female"} | ConvertTo-Json
    
    $updateResult = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients/$patientId" -Method PUT -Body $updateBody -Headers $headers -ContentType "application/json"
    Write-Host "Update successful!" -ForegroundColor Green
    
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Status Code: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
    
    # Try to get detailed error response
    try {
        $errorStream = $_.Exception.Response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($errorStream)
        $errorContent = $reader.ReadToEnd()
        Write-Host "Detailed Error Response:" -ForegroundColor Yellow
        Write-Host $errorContent -ForegroundColor Red
    } catch {
        Write-Host "Could not read detailed error response" -ForegroundColor Yellow
    }
}