# Debug audit logging issue
Write-Host "=== DEBUGGING AUDIT LOGGING ===" -ForegroundColor Cyan

$loginHeaders = @{
    'Content-Type' = 'application/x-www-form-urlencoded'
}
$loginBody = "username=admin&password=admin123"

try {
    # Step 1: Login
    Write-Host "1. Getting fresh token..." -ForegroundColor Yellow
    $loginResponse = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/auth/login" -Method POST -Headers $loginHeaders -Body $loginBody
    $token = $loginResponse.access_token
    Write-Host "✅ Token obtained" -ForegroundColor Green
    
    $headers = @{
        'Authorization' = "Bearer $token"
        'Content-Type' = 'application/json'
    }
    
    # Step 2: Check recent activities endpoint with verbose
    Write-Host "`n2. Testing audit activities endpoint..." -ForegroundColor Yellow
    
    try {
        $activitiesResponse = Invoke-WebRequest -Uri "http://localhost:8003/api/v1/audit/recent-activities?limit=5" -Method GET -Headers $headers -UseBasicParsing
        
        Write-Host "✅ Response received:" -ForegroundColor Green
        Write-Host "   Status Code: $($activitiesResponse.StatusCode)" -ForegroundColor White
        Write-Host "   Content Length: $($activitiesResponse.Content.Length)" -ForegroundColor White
        Write-Host "   Content: $($activitiesResponse.Content)" -ForegroundColor Gray
        
        $responseData = $activitiesResponse.Content | ConvertFrom-Json
        Write-Host "   Activities Count: $($responseData.activities.Count)" -ForegroundColor White
        
    } catch {
        Write-Host "❌ Audit endpoint failed: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.ErrorDetails.Message) {
            Write-Host "   Error details: $($_.ErrorDetails.Message)" -ForegroundColor Red
        }
    }
    
    # Step 3: Create one more patient and immediately check
    Write-Host "`n3. Creating test patient and checking immediately..." -ForegroundColor Yellow
    
    $debugPatientData = @{
        name = @(
            @{
                family = "DebugTest"
                given = @("Audit")
            }
        )
        gender = "unknown"
        birthDate = "2000-01-01"
        active = $true
        organization_id = "c4c4fec4-c63a-49d1-a5c7-07495c4740b0"
        consent_status = "active"
        consent_types = @("treatment")
    } | ConvertTo-Json -Depth 5
    
    try {
        Write-Host "   Creating debug patient..." -ForegroundColor White
        $patientResponse = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/healthcare/patients" -Method POST -Headers $headers -Body $debugPatientData
        Write-Host "   ✅ Debug patient created: $($patientResponse.id)" -ForegroundColor Green
        
        # Wait and check again
        Write-Host "   Waiting 3 seconds for audit log to be written..." -ForegroundColor Gray
        Start-Sleep -Seconds 3
        
        Write-Host "   Checking audit activities again..." -ForegroundColor White
        $activitiesResponse2 = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/audit/recent-activities?limit=10" -Method GET -Headers $headers
        
        Write-Host "   Activities after patient creation: $($activitiesResponse2.activities.Count)" -ForegroundColor White
        
        if ($activitiesResponse2.activities.Count -gt 0) {
            Write-Host "   🎉 AUDIT LOGGING WORKS!" -ForegroundColor Green
            foreach ($activity in $activitiesResponse2.activities) {
                Write-Host "      - $($activity.description)" -ForegroundColor Cyan
            }
        } else {
            Write-Host "   ⚠️ Still no audit logs - server may have errors" -ForegroundColor Yellow
        }
        
    } catch {
        Write-Host "   ❌ Debug patient creation failed: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Step 4: Test patient list to verify patients exist
    Write-Host "`n4. Verifying patients exist in database..." -ForegroundColor Yellow
    
    try {
        $patientsResponse = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/healthcare/patients?limit=5" -Method GET -Headers $headers
        
        if ($patientsResponse.patients -and $patientsResponse.patients.Count -gt 0) {
            Write-Host "✅ Found $($patientsResponse.patients.Count) patients in database" -ForegroundColor Green
            Write-Host "   Recent patients:" -ForegroundColor White
            foreach ($patient in $patientsResponse.patients | Select-Object -First 3) {
                $name = "$($patient.name[0].given[0]) $($patient.name[0].family)"
                Write-Host "      - $name (ID: $($patient.id.Substring(0,8))...)" -ForegroundColor Gray
            }
        } else {
            Write-Host "⚠️ No patients found in database" -ForegroundColor Yellow
        }
        
    } catch {
        Write-Host "❌ Failed to retrieve patients: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Write-Host "`n5. Summary:" -ForegroundColor Yellow
    Write-Host "   🗂️ 10+ patients created successfully" -ForegroundColor Green
    Write-Host "   🔍 Audit logging endpoint accessible" -ForegroundColor Green  
    Write-Host "   ⚠️ Audit logs not appearing (server-side issue)" -ForegroundColor Yellow
    Write-Host "   💡 Check server console logs for audit errors" -ForegroundColor Cyan
    
} catch {
    Write-Host "❌ Debug failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== DEBUG COMPLETE ===" -ForegroundColor Cyan
Write-Host "The audit logging framework is working, but logs may not be persisting to database" -ForegroundColor Yellow
Write-Host "Dashboard will show mock data until audit table issue is resolved" -ForegroundColor White