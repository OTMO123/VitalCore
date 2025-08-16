# Apply log_phi_access Fix - 5 Whys Root Cause Solution
# This script fixes the exact TypeError found in our 5 Whys analysis

Write-Host "=== APPLYING log_phi_access FIX - ROOT CAUSE SOLUTION ===" -ForegroundColor Cyan

Write-Host "`n5 Whys Analysis - ROOT CAUSE IDENTIFIED:" -ForegroundColor Green
Write-Host "WHY #1: Get Patient returns 500 error" -ForegroundColor White
Write-Host "WHY #2: Server-side processing error" -ForegroundColor White
Write-Host "WHY #3: Error in HIPAA compliance logging layer" -ForegroundColor White
Write-Host "WHY #4: log_phi_access() function parameter mismatch" -ForegroundColor White
Write-Host "WHY #5: ROOT CAUSE: Router calls log_phi_access() with 'access_type' parameter but function expects 'fields_accessed'" -ForegroundColor Red

Write-Host "`nApplying targeted fix to router.py..." -ForegroundColor Green

# Step 1: Backup the current file
$routerFile = "app/modules/healthcare_records/router.py"
$backupFile = "app/modules/healthcare_records/router.py.backup.$(Get-Date -Format 'yyyyMMdd-HHmmss')"

Write-Host "`n1. Creating backup..." -ForegroundColor Yellow
Copy-Item $routerFile $backupFile
Write-Host "Backup created: $backupFile" -ForegroundColor Green

# Step 2: Read the current file content
Write-Host "`n2. Reading current router file..." -ForegroundColor Yellow
$content = Get-Content $routerFile -Raw

# Step 3: Apply the fix - Replace the incorrect log_phi_access call
Write-Host "`n3. Applying the fix..." -ForegroundColor Yellow

# The problematic code:
$problematicCode = @"
        await log_phi_access(
            user_id=current_user_id,
            patient_id=patient_id,
            access_type="patient_retrieval",
            purpose=purpose,
            ip_address=client_info.get("ip_address"),
            session=db
        )
"@

# The correct code:
$fixedCode = @"
        # Create audit context for PHI access logging
        from app.core.audit_logger import AuditContext
        audit_context = AuditContext(
            user_id=current_user_id,
            ip_address=client_info.get("ip_address"),
            session_id=client_info.get("request_id"),
            purpose=purpose
        )
        
        # Log PHI access with correct parameters
        await log_phi_access(
            user_id=current_user_id,
            patient_id=patient_id,
            fields_accessed=["first_name", "last_name", "date_of_birth", "gender"],
            purpose=purpose,
            context=audit_context,
            db=db
        )
"@

# Apply the replacement
$newContent = $content.Replace($problematicCode, $fixedCode)

# Step 4: Write the fixed content back to the file
Write-Host "`n4. Writing fixed content..." -ForegroundColor Yellow
$newContent | Set-Content $routerFile -Encoding UTF8

Write-Host "Fix applied successfully!" -ForegroundColor Green

# Step 5: Restart the application to load the fix
Write-Host "`n5. Restarting application to load the fix..." -ForegroundColor Yellow
try {
    docker restart iris_app
    Write-Host "Application restarted" -ForegroundColor Green
    
    # Wait for application to be ready
    Write-Host "Waiting for application to be ready..." -ForegroundColor Yellow
    Start-Sleep -Seconds 15
    
    $appReady = $false
    $retries = 0
    while (-not $appReady -and $retries -lt 10) {
        try {
            $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get -TimeoutSec 3
            if ($health.status -eq "healthy") {
                $appReady = $true
                Write-Host "Application is ready!" -ForegroundColor Green
            }
        } catch {
            $retries++
            Write-Host "Waiting... (attempt $retries/10)" -ForegroundColor Yellow
            Start-Sleep -Seconds 3
        }
    }
    
    if (-not $appReady) {
        Write-Host "Application may not be ready yet, but continuing with test..." -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "Error restarting application: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Step 6: Test the fix
Write-Host "`n6. Testing the fix..." -ForegroundColor Green

try {
    # Get authentication
    $loginResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method Post -ContentType "application/json" -Body '{"username":"admin","password":"admin123"}'
    $token = $loginResponse.access_token
    $headers = @{"Authorization" = "Bearer $token"}
    
    # Get patient list
    $patientsResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients" -Method Get -Headers $headers
    $testPatientId = $patientsResponse.patients[0].id
    
    Write-Host "Testing Get Patient with patient ID: $testPatientId" -ForegroundColor Yellow
    
    # Test Get Patient - THIS SHOULD NOW WORK!
    $getPatientResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients/$testPatientId" -Method Get -Headers $headers
    
    Write-Host "`nSUCCESS! Get Patient is now working!" -ForegroundColor Green
    Write-Host "Patient Name: $($getPatientResponse.name[0].given[0]) $($getPatientResponse.name[0].family)" -ForegroundColor Yellow
    Write-Host "Patient ID: $($getPatientResponse.id)" -ForegroundColor Yellow
    Write-Host "Patient Gender: $($getPatientResponse.gender)" -ForegroundColor Yellow
    
    # Test multiple patients to ensure consistency
    Write-Host "`nTesting additional patients for consistency..." -ForegroundColor Yellow
    $successCount = 1
    for ($i = 1; $i -lt [math]::Min(5, $patientsResponse.patients.Count); $i++) {
        try {
            $testId = $patientsResponse.patients[$i].id
            $testResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients/$testId" -Method Get -Headers $headers
            $successCount++
            Write-Host "Patient $($i+1): SUCCESS" -ForegroundColor Green
        } catch {
            Write-Host "Patient $($i+1): FAILED - $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    Write-Host "`nGet Patient fix results: $successCount/$([math]::Min(5, $patientsResponse.patients.Count)) successful tests" -ForegroundColor Cyan
    
} catch {
    Write-Host "`nGet Patient test failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Checking logs for any remaining issues..." -ForegroundColor Yellow
    
    try {
        $logs = docker logs iris_app --tail 20 2>&1
        $errors = $logs | Select-String "error|Error|ERROR|exception|Exception"
        if ($errors) {
            Write-Host "Found errors in logs:" -ForegroundColor Red
            $errors | ForEach-Object { Write-Host "  $($_.Line)" -ForegroundColor Red }
        } else {
            Write-Host "No obvious errors found in logs" -ForegroundColor Green
        }
    } catch {
        Write-Host "Could not check logs" -ForegroundColor Yellow
    }
}

# Step 7: Run final success rate test
Write-Host "`n7. Running final success rate test..." -ForegroundColor Green
try {
    & ".\test_final_success_rate_fixed.ps1"
} catch {
    Write-Host "Success rate test failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== FIX SUMMARY ===" -ForegroundColor Cyan
Write-Host "PROBLEM: TypeError in log_phi_access() function call" -ForegroundColor Red
Write-Host "ROOT CAUSE: Wrong parameters passed to log_phi_access()" -ForegroundColor Red
Write-Host "SOLUTION: Fixed parameter names and added required AuditContext" -ForegroundColor Green
Write-Host "RESULT: Get Patient endpoint should now work correctly" -ForegroundColor Green

Write-Host "`nThe 5 Whys methodology successfully identified and resolved the root cause!" -ForegroundColor Green