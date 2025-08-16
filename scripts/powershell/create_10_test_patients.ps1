# Create 10 test patients to generate audit logs
Write-Host "=== CREATING 10 TEST PATIENTS FOR AUDIT TESTING ===" -ForegroundColor Cyan

$loginHeaders = @{
    'Content-Type' = 'application/x-www-form-urlencoded'
}
$loginBody = "username=admin&password=admin123"

# Test patient data templates
$testPatients = @(
    @{ FirstName = "Alice"; LastName = "Johnson"; Gender = "female"; DOB = "1990-03-15"; Phone = "(555) 100-0001" },
    @{ FirstName = "Bob"; LastName = "Smith"; Gender = "male"; DOB = "1985-07-22"; Phone = "(555) 100-0002" },
    @{ FirstName = "Carol"; LastName = "Williams"; Gender = "female"; DOB = "1992-11-08"; Phone = "(555) 100-0003" },
    @{ FirstName = "David"; LastName = "Brown"; Gender = "male"; DOB = "1988-01-30"; Phone = "(555) 100-0004" },
    @{ FirstName = "Emma"; LastName = "Davis"; Gender = "female"; DOB = "1995-05-14"; Phone = "(555) 100-0005" },
    @{ FirstName = "Frank"; LastName = "Miller"; Gender = "male"; DOB = "1982-09-03"; Phone = "(555) 100-0006" },
    @{ FirstName = "Grace"; LastName = "Wilson"; Gender = "female"; DOB = "1993-12-21"; Phone = "(555) 100-0007" },
    @{ FirstName = "Henry"; LastName = "Moore"; Gender = "male"; DOB = "1987-04-17"; Phone = "(555) 100-0008" },
    @{ FirstName = "Ivy"; LastName = "Taylor"; Gender = "female"; DOB = "1991-08-25"; Phone = "(555) 100-0009" },
    @{ FirstName = "Jack"; LastName = "Anderson"; Gender = "male"; DOB = "1989-06-12"; Phone = "(555) 100-0010" }
)

try {
    # Step 1: Login
    Write-Host "1. Getting authentication token..." -ForegroundColor Yellow
    $loginResponse = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/auth/login" -Method POST -Headers $loginHeaders -Body $loginBody
    $token = $loginResponse.access_token
    Write-Host "✅ Token obtained successfully" -ForegroundColor Green
    
    $headers = @{
        'Authorization' = "Bearer $token"
        'Content-Type' = 'application/json'
    }
    
    # Step 2: Create 10 patients
    Write-Host "`n2. Creating 10 test patients..." -ForegroundColor Yellow
    $createdPatients = @()
    $failedCreations = 0
    
    for ($i = 0; $i -lt $testPatients.Length; $i++) {
        $patient = $testPatients[$i]
        $patientNumber = $i + 1
        
        Write-Host "   Creating patient $patientNumber/10: $($patient.FirstName) $($patient.LastName)..." -ForegroundColor White
        
        # Generate unique MRN
        $timestamp = [int][double]::Parse((Get-Date -UFormat %s))
        $randomId = Get-Random -Minimum 1000 -Maximum 9999
        $uniqueMRN = "TEST-$timestamp-$randomId"
        
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
                    value = $uniqueMRN
                }
            )
            name = @(
                @{
                    use = "official"
                    family = $patient.LastName
                    given = @($patient.FirstName)
                }
            )
            telecom = @(
                @{
                    system = "phone"
                    value = $patient.Phone
                    use = "mobile"
                }
            )
            gender = $patient.Gender
            birthDate = $patient.DOB
            address = @(
                @{
                    use = "home"
                    line = @("$($patientNumber)00 Test Street")
                    city = "TestCity"
                    state = "TX"
                    postalCode = "7300$patientNumber"
                    country = "US"
                }
            )
            active = $true
            organization_id = "c4c4fec4-c63a-49d1-a5c7-07495c4740b0"
            consent_status = "active"
            consent_types = @("treatment", "payment")
        } | ConvertTo-Json -Depth 5
        
        try {
            $patientResponse = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/healthcare/patients" -Method POST -Headers $headers -Body $patientData
            
            $createdPatients += @{
                Number = $patientNumber
                Name = "$($patient.FirstName) $($patient.LastName)"
                ID = $patientResponse.id
                MRN = $uniqueMRN
                Status = "✅ Success"
            }
            
            Write-Host "      ✅ Created: ID $($patientResponse.id)" -ForegroundColor Green
            
            # Small delay to spread out the audit logs
            Start-Sleep -Milliseconds 500
            
        } catch {
            $failedCreations++
            Write-Host "      ❌ Failed: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    # Step 3: Check audit logs
    Write-Host "`n3. Checking recent audit activities..." -ForegroundColor Yellow
    Start-Sleep -Seconds 2  # Wait for logs to be written
    
    try {
        $activitiesResponse = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/audit/recent-activities?limit=15" -Method GET -Headers $headers
        
        Write-Host "✅ Audit activities retrieved:" -ForegroundColor Green
        Write-Host "   Total activities found: $($activitiesResponse.activities.Count)" -ForegroundColor White
        
        if ($activitiesResponse.activities.Count -gt 0) {
            Write-Host "`n   Recent audit logs:" -ForegroundColor Cyan
            foreach ($activity in $activitiesResponse.activities) {
                $timeAgo = [math]::Round(((Get-Date) - [datetime]$activity.timestamp).TotalMinutes, 1)
                $user = if ($activity.user) { " by $($activity.user)" } else { "" }
                Write-Host "      $($activity.description)$user ($($timeAgo) min ago)" -ForegroundColor Gray
            }
        } else {
            Write-Host "   ⚠️ No audit activities found - check server logs" -ForegroundColor Yellow
        }
        
    } catch {
        Write-Host "❌ Failed to retrieve audit activities: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Step 4: Summary
    Write-Host "`n4. Test Results Summary:" -ForegroundColor Yellow
    Write-Host "   ✅ Patients created successfully: $($createdPatients.Count)" -ForegroundColor Green
    Write-Host "   ❌ Failed creations: $failedCreations" -ForegroundColor Red
    Write-Host "   📊 Total audit events expected: $($createdPatients.Count + 1)" -ForegroundColor Cyan  # +1 for login
    
    if ($createdPatients.Count -gt 0) {
        Write-Host "`n   Created patients:" -ForegroundColor White
        foreach ($patient in $createdPatients) {
            Write-Host "      $($patient.Number). $($patient.Name) (ID: $($patient.ID.Substring(0,8))...)" -ForegroundColor Gray
        }
    }
    
    # Step 5: Dashboard check
    Write-Host "`n5. Dashboard Check:" -ForegroundColor Yellow
    Write-Host "   🎯 Visit: http://localhost:5173" -ForegroundColor Cyan
    Write-Host "   📈 Recent Activity card should now show real audit logs!" -ForegroundColor Green
    Write-Host "   🔄 Dashboard auto-refreshes every 30 seconds" -ForegroundColor Gray
    
} catch {
    Write-Host "❌ Script failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Error details: $($_.ErrorDetails.Message)" -ForegroundColor Red
}

Write-Host "`n=== TEST PATIENT CREATION COMPLETE ===" -ForegroundColor Cyan
Write-Host "🎉 Audit logging test complete!" -ForegroundColor Green
Write-Host "💡 Check the dashboard Recent Activity card for real-time audit logs" -ForegroundColor Yellow