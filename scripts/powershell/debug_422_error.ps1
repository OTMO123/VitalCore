# Debug 422 validation error step by step
Write-Host "=== DEBUGGING 422 VALIDATION ERROR ===" -ForegroundColor Cyan

try {
    # Step 1: Authentication
    Write-Host "STEP 1: Testing authentication..." -ForegroundColor Yellow
    $loginBody = @{username="admin"; password="admin123"} | ConvertTo-Json
    $authResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Body $loginBody -ContentType "application/json"
    $token = $authResponse.access_token
    Write-Host "✅ Authentication successful" -ForegroundColor Green
    
    $headers = @{"Authorization" = "Bearer $token"}
    
    # Step 2: Test if GET patient works (to verify patient exists)
    Write-Host "STEP 2: Testing GET patient with known ID..." -ForegroundColor Yellow
    try {
        $getResult = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients/249b1e26-9d42-4991-a557-f0d6a12d5ab7" -Method GET -Headers $headers
        Write-Host "✅ GET patient works - patient exists" -ForegroundColor Green
        $patientId = "249b1e26-9d42-4991-a557-f0d6a12d5ab7"
    } catch {
        Write-Host "❌ GET patient failed, creating new patient..." -ForegroundColor Red
        
        # Create a new patient
        $patientBody = @{
            resourceType = "Patient"
            active = $true
            name = @(@{use="official"; family="DebugTest"; given=@("Test")})
            gender = "unknown"
            birthDate = "1990-01-01"
        } | ConvertTo-Json -Depth 3
        
        $createResult = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients" -Method POST -Body $patientBody -Headers $headers -ContentType "application/json"
        $patientId = $createResult.id
        Write-Host "✅ Created new patient: $patientId" -ForegroundColor Green
    }
    
    # Step 3: Test PUT with empty body
    Write-Host "STEP 3: Testing PUT with empty body..." -ForegroundColor Yellow
    try {
        $emptyBody = "{}"
        $result = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients/$patientId" -Method PUT -Body $emptyBody -Headers $headers -ContentType "application/json"
        Write-Host "✅ Empty body works" -ForegroundColor Green
    } catch {
        Write-Host "❌ Empty body failed: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
    }
    
    # Step 4: Test PUT with just gender
    Write-Host "STEP 4: Testing PUT with just gender..." -ForegroundColor Yellow
    try {
        $genderBody = @{gender="female"} | ConvertTo-Json
        Write-Host "Sending body: $genderBody" -ForegroundColor Cyan
        $result = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients/$patientId" -Method PUT -Body $genderBody -Headers $headers -ContentType "application/json"
        Write-Host "✅ Gender update works!" -ForegroundColor Green
    } catch {
        Write-Host "❌ Gender update failed: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Step 5: Test PUT with consent_status
    Write-Host "STEP 5: Testing PUT with consent_status..." -ForegroundColor Yellow
    try {
        $consentBody = @{consent_status="active"} | ConvertTo-Json
        Write-Host "Sending body: $consentBody" -ForegroundColor Cyan
        $result = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients/$patientId" -Method PUT -Body $consentBody -Headers $headers -ContentType "application/json"
        Write-Host "✅ Consent update works!" -ForegroundColor Green
    } catch {
        Write-Host "❌ Consent update failed: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Step 6: Test PUT with both gender and consent_status (original failing case)
    Write-Host "STEP 6: Testing PUT with both gender and consent_status..." -ForegroundColor Yellow
    try {
        $bothBody = @{gender="female"; consent_status="active"} | ConvertTo-Json
        Write-Host "Sending body: $bothBody" -ForegroundColor Cyan
        $result = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients/$patientId" -Method PUT -Body $bothBody -Headers $headers -ContentType "application/json"
        Write-Host "✅ Both fields update works!" -ForegroundColor Green
    } catch {
        Write-Host "❌ Both fields update failed: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    }
    
} catch {
    Write-Host "FATAL ERROR: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "=== DEBUG COMPLETE ===" -ForegroundColor Cyan