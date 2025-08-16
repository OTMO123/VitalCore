# Test automatic audit table creation
Write-Host "=== TESTING AUTOMATIC AUDIT TABLE CREATION ===" -ForegroundColor Cyan

$loginHeaders = @{
    'Content-Type' = 'application/x-www-form-urlencoded'
}
$loginBody = "username=admin&password=admin123"

try {
    # Step 1: Login
    Write-Host "1. Getting token..." -ForegroundColor Yellow
    $loginResponse = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/auth/login" -Method POST -Headers $loginHeaders -Body $loginBody
    $token = $loginResponse.access_token
    Write-Host "✅ Token obtained" -ForegroundColor Green
    
    $headers = @{
        'Authorization' = "Bearer $token"
        'Content-Type' = 'application/json'
    }
    
    # Step 2: Call recent activities (this should auto-create table)
    Write-Host "`n2. Calling recent activities (auto-creating table)..." -ForegroundColor Yellow
    $activitiesResponse = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/audit/recent-activities?limit=5" -Method GET -Headers $headers
    
    Write-Host "✅ Recent activities response received" -ForegroundColor Green
    Write-Host "Activities count: $($activitiesResponse.activities.Count)" -ForegroundColor White
    
    if ($activitiesResponse.activities.Count -gt 0) {
        Write-Host "🎉 Found activities after table creation!" -ForegroundColor Green
        foreach ($activity in $activitiesResponse.activities) {
            Write-Host "   - $($activity.description)" -ForegroundColor White
        }
    } else {
        Write-Host "⚠️ No activities yet, but table should be created" -ForegroundColor Yellow
    }
    
    # Step 3: Create patient to generate audit log
    Write-Host "`n3. Creating patient to test audit logging..." -ForegroundColor Yellow
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
                value = "AUTO-TABLE-TEST-$(Get-Random)"
            }
        )
        name = @(
            @{
                use = "official"
                family = "AutoTest"
                given = @("Table")
            }
        )
        gender = "other"
        birthDate = "2000-01-01"
        active = $true
        organization_id = "c4c4fec4-c63a-49d1-a5c7-07495c4740b0"
        consent_status = "active"
        consent_types = @("treatment")
    } | ConvertTo-Json -Depth 5
    
    try {
        $patientResponse = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/healthcare/patients" -Method POST -Headers $headers -Body $patientData
        Write-Host "✅ Patient created: $($patientResponse.id)" -ForegroundColor Green
        
        # Step 4: Check activities again
        Write-Host "`n4. Checking activities after patient creation..." -ForegroundColor Yellow
        Start-Sleep -Seconds 1
        $activitiesResponse2 = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/audit/recent-activities?limit=10" -Method GET -Headers $headers
        
        Write-Host "Activities count after patient creation: $($activitiesResponse2.activities.Count)" -ForegroundColor White
        
        if ($activitiesResponse2.activities.Count -gt 0) {
            Write-Host "🎉 SUCCESS! Real audit logging is working!" -ForegroundColor Green
            foreach ($activity in $activitiesResponse2.activities) {
                $timeAgo = [math]::Round(((Get-Date) - [datetime]$activity.timestamp).TotalMinutes, 1)
                Write-Host "   - $($activity.description) ($($timeAgo) min ago)" -ForegroundColor White
                Write-Host "     Type: $($activity.type), Severity: $($activity.severity)" -ForegroundColor Gray
            }
        } else {
            Write-Host "⚠️ Still no activities - check server logs for errors" -ForegroundColor Yellow
        }
        
    } catch {
        Write-Host "❌ Patient creation failed: $($_.Exception.Message)" -ForegroundColor Red
    }
    
} catch {
    Write-Host "❌ Test failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== AUTO TABLE CREATION TEST COMPLETE ===" -ForegroundColor Cyan
Write-Host "Dashboard at http://localhost:5173 should now show real activities!" -ForegroundColor Green