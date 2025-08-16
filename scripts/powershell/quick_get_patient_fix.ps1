# Quick Get Patient Fix - 5 Whys Based Solution
# This script applies the targeted fix based on 5 Whys analysis

Write-Host "=== QUICK GET PATIENT FIX - 5 WHYS SOLUTION ===" -ForegroundColor Cyan

Write-Host "`n5 Whys Analysis Summary:" -ForegroundColor Yellow
Write-Host "WHY #1: Get Patient returns 500 error" -ForegroundColor White
Write-Host "WHY #2: Server-side processing error during response creation" -ForegroundColor White
Write-Host "WHY #3: PHI decryption or PatientResponse validation fails" -ForegroundColor White
Write-Host "WHY #4: SecurityManager or response data structure issues" -ForegroundColor White
Write-Host "WHY #5: Root cause likely in complex response building with encrypted data" -ForegroundColor White

Write-Host "`nApplying targeted fix..." -ForegroundColor Green

# Step 1: Check current system status
Write-Host "`n1. Checking current system status..." -ForegroundColor Green
try {
    $healthCheck = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get -TimeoutSec 5
    Write-Host "System is healthy" -ForegroundColor Green
} catch {
    Write-Host "System health check failed - ensure containers are running" -ForegroundColor Red
    exit 1
}

# Step 2: Test current Get Patient behavior
Write-Host "`n2. Testing current Get Patient behavior..." -ForegroundColor Green
try {
    # Get auth token
    $loginResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method Post -ContentType "application/json" -Body '{"username":"admin","password":"admin123"}'
    $token = $loginResponse.access_token
    $headers = @{"Authorization" = "Bearer $token"}
    
    # Get patient list
    $patientsResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients" -Method Get -Headers $headers
    if ($patientsResponse.patients.Count -gt 0) {
        $testPatientId = $patientsResponse.patients[0].id
        Write-Host "Testing with patient ID: $testPatientId" -ForegroundColor Yellow
        
        # Try Get Patient
        try {
            $getPatientResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients/$testPatientId" -Method Get -Headers $headers
            Write-Host "SUCCESS: Get Patient is already working!" -ForegroundColor Green
            Write-Host "Patient: $($getPatientResponse.name[0].given[0]) $($getPatientResponse.name[0].family)" -ForegroundColor Yellow
            exit 0
        } catch {
            Write-Host "CONFIRMED: Get Patient fails with: $($_.Exception.Message)" -ForegroundColor Red
            $getPatientError = $_.Exception.Response.StatusCode
            Write-Host "Status Code: $getPatientError" -ForegroundColor Red
        }
    }
} catch {
    Write-Host "Initial testing failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Step 3: Apply the fix by restarting the application container
Write-Host "`n3. Applying fix by restarting application container..." -ForegroundColor Green
Write-Host "This ensures any recent code changes are loaded" -ForegroundColor Yellow

try {
    # Restart the application container
    docker restart iris_app
    Write-Host "Container restarted successfully" -ForegroundColor Green
    
    # Wait for application to be ready
    Write-Host "Waiting for application to be ready..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    $retries = 0
    $maxRetries = 12
    $appReady = $false
    
    while (-not $appReady -and $retries -lt $maxRetries) {
        try {
            $healthCheck = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get -TimeoutSec 3
            if ($healthCheck.status -eq "healthy") {
                $appReady = $true
                Write-Host "Application is ready" -ForegroundColor Green
            }
        } catch {
            $retries++
            Write-Host "Waiting for application... (attempt $retries/$maxRetries)" -ForegroundColor Yellow
            Start-Sleep -Seconds 5
        }
    }
    
    if (-not $appReady) {
        Write-Host "Application failed to start within timeout" -ForegroundColor Red
        exit 1
    }
    
} catch {
    Write-Host "Container restart failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Step 4: Test Get Patient after restart
Write-Host "`n4. Testing Get Patient after restart..." -ForegroundColor Green

try {
    # Re-authenticate after restart
    $loginResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method Post -ContentType "application/json" -Body '{"username":"admin","password":"admin123"}'
    $token = $loginResponse.access_token
    $headers = @{"Authorization" = "Bearer $token"}
    
    # Test Get Patient again
    $getPatientResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients/$testPatientId" -Method Get -Headers $headers
    Write-Host "SUCCESS: Get Patient is now working!" -ForegroundColor Green
    Write-Host "Patient: $($getPatientResponse.name[0].given[0]) $($getPatientResponse.name[0].family)" -ForegroundColor Yellow
    Write-Host "Patient ID: $($getPatientResponse.id)" -ForegroundColor Yellow
    
    # Test a few more patients to ensure consistency
    Write-Host "`nTesting additional patients for consistency..." -ForegroundColor Yellow
    $successCount = 1
    for ($i = 1; $i -lt [math]::Min(3, $patientsResponse.patients.Count); $i++) {
        try {
            $testId = $patientsResponse.patients[$i].id
            $testResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients/$testId" -Method Get -Headers $headers
            $successCount++
            Write-Host "Patient $($i+1): SUCCESS" -ForegroundColor Green
        } catch {
            Write-Host "Patient $($i+1): FAILED" -ForegroundColor Red
        }
    }
    
    Write-Host "`nGet Patient fix results: $successCount successful tests" -ForegroundColor Cyan
    
} catch {
    Write-Host "Get Patient still fails after restart: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Additional investigation needed" -ForegroundColor Yellow
    
    # Run comprehensive debug
    Write-Host "`nRunning comprehensive debug..." -ForegroundColor Yellow
    try {
        & ".\debug_get_patient_comprehensive.ps1"
    } catch {
        Write-Host "Debug script failed: $($_.Exception.Message)" -ForegroundColor Red
    }
    exit 1
}

# Step 5: Run full success rate test
Write-Host "`n5. Running full success rate test..." -ForegroundColor Green

try {
    & ".\test_final_success_rate_fixed.ps1"
} catch {
    Write-Host "Success rate test failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== FIX SUMMARY ===" -ForegroundColor Cyan
Write-Host "Applied: Container restart to load latest code changes" -ForegroundColor Green
Write-Host "Result: Get Patient endpoint should now be working" -ForegroundColor Green
Write-Host "Next: Check success rate results above" -ForegroundColor Yellow

Write-Host "`nIf Get Patient is still failing:" -ForegroundColor Yellow
Write-Host "1. Check container logs: docker logs iris_app" -ForegroundColor White
Write-Host "2. Run: .\debug_get_patient_comprehensive.ps1" -ForegroundColor White
Write-Host "3. Look for specific error layers in the detailed logging" -ForegroundColor White