# Debug audit endpoint issue
Write-Host "=== DEBUGGING AUDIT ENDPOINT ===" -ForegroundColor Cyan

$loginHeaders = @{
    'Content-Type' = 'application/x-www-form-urlencoded'
}
$loginBody = "username=admin&password=admin123"

try {
    # Get fresh token
    Write-Host "1. Getting fresh token..." -ForegroundColor Yellow
    $loginResponse = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/auth/login" -Method POST -Headers $loginHeaders -Body $loginBody
    $token = $loginResponse.access_token
    Write-Host "✅ Token obtained: $($token.Substring(0,20))..." -ForegroundColor Green
    
    $headers = @{
        'Authorization' = "Bearer $token"
        'Content-Type' = 'application/json'
    }
    
    # Test direct audit endpoint
    Write-Host "`n2. Testing audit endpoint directly..." -ForegroundColor Yellow
    try {
        $auditResponse = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/audit/recent-activities?limit=5" -Method GET -Headers $headers
        Write-Host "✅ Audit endpoint response:" -ForegroundColor Green
        Write-Host ($auditResponse | ConvertTo-Json -Depth 3) -ForegroundColor White
        
        if ($auditResponse.activities.Count -eq 0) {
            Write-Host "⚠️ No activities found - checking database connection..." -ForegroundColor Yellow
            
            # Test audit stats endpoint
            Write-Host "`n3. Testing audit stats endpoint..." -ForegroundColor Yellow
            try {
                $statsResponse = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/audit/stats" -Method GET -Headers $headers
                Write-Host "✅ Stats response:" -ForegroundColor Green
                Write-Host ($statsResponse | ConvertTo-Json -Depth 2) -ForegroundColor White
            } catch {
                Write-Host "❌ Stats endpoint failed: $($_.Exception.Message)" -ForegroundColor Red
            }
        }
        
    } catch {
        Write-Host "❌ Audit endpoint failed: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "Response: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
    
    # Test if we can create activity and see it immediately
    Write-Host "`n4. Creating new patient to generate activity..." -ForegroundColor Yellow
    $patientData = @{
        identifier = @(
            @{
                use = "official"
                type = @{
                    coding = @(
                        @{
                            system = "http://terminology.hl7.org/CodeSystem/v2-0203"
                            code = "MR"
                        }
                    )
                }
                system = "http://hospital.example.org/patients"
                value = "DEBUG-TEST-$(Get-Random)"
            }
        )
        name = @(
            @{
                use = "official"
                family = "DebugUser"
                given = @("Test")
            }
        )
        gender = "female"
        birthDate = "1995-05-05"
        active = $true
        organization_id = "c4c4fec4-c63a-49d1-a5c7-07495c4740b0"
        consent_status = "active"
        consent_types = @("treatment")
    } | ConvertTo-Json -Depth 5
    
    try {
        $patientResponse = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/healthcare/patients" -Method POST -Headers $headers -Body $patientData
        Write-Host "✅ Patient created: $($patientResponse.id)" -ForegroundColor Green
        
        # Wait a bit and check again
        Start-Sleep -Seconds 2
        Write-Host "`n5. Checking activities after patient creation..." -ForegroundColor Yellow
        $auditResponse2 = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/audit/recent-activities?limit=10" -Method GET -Headers $headers
        Write-Host "Activities count: $($auditResponse2.activities.Count)" -ForegroundColor White
        
        if ($auditResponse2.activities.Count -gt 0) {
            Write-Host "✅ Found activities after patient creation!" -ForegroundColor Green
            foreach ($activity in $auditResponse2.activities) {
                Write-Host "   - $($activity.description) (Type: $($activity.type))" -ForegroundColor White
            }
        } else {
            Write-Host "⚠️ Still no activities - database issue possible" -ForegroundColor Yellow
        }
        
    } catch {
        Write-Host "❌ Patient creation failed: $($_.Exception.Message)" -ForegroundColor Red
    }
    
} catch {
    Write-Host "❌ Login failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== DEBUG COMPLETE ===" -ForegroundColor Cyan