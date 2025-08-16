# Create test patients with minimal data structure
Write-Host "=== CREATING TEST PATIENTS (SIMPLIFIED) ===" -ForegroundColor Cyan

$loginHeaders = @{
    'Content-Type' = 'application/x-www-form-urlencoded'
}
$loginBody = "username=admin&password=admin123"

# Simple patient names
$patientNames = @(
    "Alice Johnson", "Bob Smith", "Carol Williams", "David Brown", "Emma Davis",
    "Frank Miller", "Grace Wilson", "Henry Moore", "Ivy Taylor", "Jack Anderson"
)

try {
    # Step 1: Login
    Write-Host "1. Getting authentication token..." -ForegroundColor Yellow
    $loginResponse = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/auth/login" -Method POST -Headers $loginHeaders -Body $loginBody
    $token = $loginResponse.access_token
    Write-Host "✅ Token obtained" -ForegroundColor Green
    
    $headers = @{
        'Authorization' = "Bearer $token"
        'Content-Type' = 'application/json'
    }
    
    # Step 2: Test with one working patient format first
    Write-Host "`n2. Testing with known working format..." -ForegroundColor Yellow
    
    $testPatientData = @{
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
                value = "TEST-WORKING-001"
            }
        )
        name = @(
            @{
                use = "official"
                family = "TestWorking"
                given = @("Patient")
            }
        )
        gender = "female"
        birthDate = "1990-01-01"
        active = $true
        organization_id = "c4c4fec4-c63a-49d1-a5c7-07495c4740b0"
        consent_status = "active"
        consent_types = @("treatment")
    } | ConvertTo-Json -Depth 5
    
    try {
        Write-Host "   Testing known working format..." -ForegroundColor White
        $testResponse = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/healthcare/patients" -Method POST -Headers $headers -Body $testPatientData
        Write-Host "   ✅ Test patient created: $($testResponse.id)" -ForegroundColor Green
        
        # If test works, create 9 more
        Write-Host "`n3. Creating 9 additional patients..." -ForegroundColor Yellow
        $successCount = 1
        
        for ($i = 1; $i -lt 10; $i++) {
            $nameParts = $patientNames[$i].Split(" ")
            $firstName = $nameParts[0]
            $lastName = $nameParts[1]
            
            Write-Host "   Creating patient $($i+1)/10: $firstName $lastName..." -ForegroundColor White
            
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
                        value = "TEST-BATCH-$(Get-Random -Minimum 1000 -Maximum 9999)"
                    }
                )
                name = @(
                    @{
                        use = "official"
                        family = $lastName
                        given = @($firstName)
                    }
                )
                gender = if ($i % 2 -eq 0) { "male" } else { "female" }
                birthDate = "199$($i % 5)-0$($i % 9 + 1)-15"
                active = $true
                organization_id = "c4c4fec4-c63a-49d1-a5c7-07495c4740b0"
                consent_status = "active"
                consent_types = @("treatment")
            } | ConvertTo-Json -Depth 5
            
            try {
                $patientResponse = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/healthcare/patients" -Method POST -Headers $headers -Body $patientData
                Write-Host "      ✅ Created: $($patientResponse.id.Substring(0,8))..." -ForegroundColor Green
                $successCount++
                
                # Small delay between creations
                Start-Sleep -Milliseconds 300
                
            } catch {
                Write-Host "      ❌ Failed: $($_.Exception.Message)" -ForegroundColor Red
                if ($_.ErrorDetails.Message) {
                    Write-Host "         Details: $($_.ErrorDetails.Message)" -ForegroundColor Gray
                }
            }
        }
        
        Write-Host "`n4. Checking audit activities..." -ForegroundColor Yellow
        Start-Sleep -Seconds 2
        
        $activitiesResponse = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/audit/recent-activities?limit=15" -Method GET -Headers $headers
        
        Write-Host "✅ Audit check complete:" -ForegroundColor Green
        Write-Host "   Activities found: $($activitiesResponse.activities.Count)" -ForegroundColor White
        Write-Host "   Patients created: $successCount" -ForegroundColor White
        Write-Host "   Expected audit logs: $($successCount + 1)" -ForegroundColor Gray  # +1 for login
        
        if ($activitiesResponse.activities.Count -gt 0) {
            Write-Host "`n   Recent activities:" -ForegroundColor Cyan
            foreach ($activity in $activitiesResponse.activities | Select-Object -First 5) {
                $timeAgo = [math]::Round(((Get-Date) - [datetime]$activity.timestamp).TotalMinutes, 1)
                Write-Host "      $($activity.description) ($($timeAgo) min ago)" -ForegroundColor Gray
            }
        }
        
        Write-Host "`n🎯 Dashboard Check:" -ForegroundColor Yellow
        Write-Host "   Visit http://localhost:5173 to see Real Activity updates!" -ForegroundColor Green
        
    } catch {
        Write-Host "   ❌ Test patient failed: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "   Error details: $($_.ErrorDetails.Message)" -ForegroundColor Red
        
        # Try even simpler format
        Write-Host "`n   Trying ultra-simple format..." -ForegroundColor Yellow
        $ultraSimple = @{
            name = @(
                @{
                    family = "Simple"
                    given = @("Test")
                }
            )
            gender = "unknown"
            active = $true
        } | ConvertTo-Json -Depth 3
        
        try {
            $simpleResponse = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/healthcare/patients" -Method POST -Headers $headers -Body $ultraSimple
            Write-Host "   ✅ Ultra-simple patient created: $($simpleResponse.id)" -ForegroundColor Green
        } catch {
            Write-Host "   ❌ Ultra-simple also failed: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
} catch {
    Write-Host "❌ Script failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== TEST COMPLETE ===" -ForegroundColor Cyan