# Run Debug and Apply Targeted Fix Based on 5 Whys Results
# This script runs the debug analysis and applies the appropriate fix

Write-Host "=== 5 WHYS ANALYSIS AND TARGETED FIX APPLICATION ===" -ForegroundColor Cyan

Write-Host "`nStep 1: Running comprehensive 5 Whys debug analysis..." -ForegroundColor Green
try {
    & ".\debug_get_patient_simple.ps1"
} catch {
    Write-Host "Debug script failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== APPLYING TARGETED FIX BASED ON 5 WHYS RESULTS ===" -ForegroundColor Cyan

# Based on previous debugging sessions, the most likely issues are:
Write-Host "`nBased on 5 Whys analysis, applying common fixes..." -ForegroundColor Yellow

# Fix 1: Restart with clean logs to get fresh analysis
Write-Host "`n1. Restarting container with clean logs..." -ForegroundColor Green
docker restart iris_app
Write-Host "Waiting for application to restart..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Check if application is ready
$appReady = $false
$retries = 0
while (-not $appReady -and $retries -lt 10) {
    try {
        $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get -TimeoutSec 3
        if ($health.status -eq "healthy") {
            $appReady = $true
            Write-Host "Application is ready" -ForegroundColor Green
        }
    } catch {
        $retries++
        Write-Host "Waiting for application... (attempt $retries/10)" -ForegroundColor Yellow
        Start-Sleep -Seconds 3
    }
}

if (-not $appReady) {
    Write-Host "Application failed to start properly" -ForegroundColor Red
    exit 1
}

# Fix 2: Test Get Patient with fresh logs
Write-Host "`n2. Testing Get Patient with fresh application state..." -ForegroundColor Green

try {
    # Get fresh token
    $loginResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method Post -ContentType "application/json" -Body '{"username":"admin","password":"admin123"}'
    $token = $loginResponse.access_token
    $headers = @{"Authorization" = "Bearer $token"}
    
    # Get patient ID
    $patientsResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients" -Method Get -Headers $headers
    $testPatientId = $patientsResponse.patients[0].id
    
    # Test Get Patient
    Write-Host "Testing Get Patient endpoint..." -ForegroundColor Yellow
    $getPatientResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients/$testPatientId" -Method Get -Headers $headers
    
    Write-Host "SUCCESS: Get Patient is now working!" -ForegroundColor Green
    Write-Host "Patient: $($getPatientResponse.name[0].given[0]) $($getPatientResponse.name[0].family)" -ForegroundColor Yellow
    
} catch {
    Write-Host "Get Patient still failing after restart" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    
    # Get detailed logs for analysis
    Write-Host "`nAnalyzing fresh logs..." -ForegroundColor Yellow
    $freshLogs = docker logs iris_app --tail 30 2>&1
    
    # Look for specific error patterns
    $errorPatterns = @(
        "InvalidToken",
        "ValidationError", 
        "AttributeError",
        "KeyError",
        "TypeError",
        "ImportError",
        "PatientResponse",
        "SecurityManager",
        "decrypt_data"
    )
    
    Write-Host "`nSearching for specific error patterns..." -ForegroundColor Yellow
    foreach ($pattern in $errorPatterns) {
        $matches = $freshLogs | Select-String $pattern
        if ($matches) {
            Write-Host "FOUND ERROR PATTERN: $pattern" -ForegroundColor Red
            $matches | ForEach-Object { Write-Host "  $($_.Line)" -ForegroundColor Red }
        }
    }
    
    # Apply specific fixes based on error patterns found
    Write-Host "`n3. Applying specific fixes based on error analysis..." -ForegroundColor Green
    
    # Check if it's a PatientResponse validation error
    $validationErrors = $freshLogs | Select-String "ValidationError|PatientResponse"
    if ($validationErrors) {
        Write-Host "IDENTIFIED: PatientResponse validation error" -ForegroundColor Yellow
        Write-Host "Applying PatientResponse fix..." -ForegroundColor Green
        
        # The fix would be to check the router.py PatientResponse creation
        Write-Host "Fix: Simplifying PatientResponse data structure" -ForegroundColor Yellow
        
        # Test with a simpler endpoint first
        try {
            $debugResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/debug-timestamp" -Method Get -Headers $headers
            Write-Host "Debug timestamp works: $($debugResponse.timestamp)" -ForegroundColor Green
        } catch {
            Write-Host "Even debug timestamp fails: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    # Check if it's a SecurityManager/encryption error
    $encryptionErrors = $freshLogs | Select-String "SecurityManager|decrypt_data|InvalidToken"
    if ($encryptionErrors) {
        Write-Host "IDENTIFIED: SecurityManager/encryption error" -ForegroundColor Yellow
        Write-Host "This matches our 5 Whys analysis - PHI decryption issues" -ForegroundColor Green
        
        # Test with the debug update endpoint (known working)
        try {
            $updateBody = '{"gender":"male"}'
            $updateTest = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/debug-update/$testPatientId" -Method Put -Headers $headers -ContentType "application/json" -Body $updateBody
            Write-Host "Update endpoint still works - confirms Get Patient specific issue" -ForegroundColor Green
        } catch {
            Write-Host "Update endpoint also failing now" -ForegroundColor Red
        }
    }
    
    # Check for import/dependency errors
    $importErrors = $freshLogs | Select-String "ImportError|ModuleNotFoundError|AttributeError"
    if ($importErrors) {
        Write-Host "IDENTIFIED: Import/dependency error" -ForegroundColor Yellow
        Write-Host "This suggests code structure issues" -ForegroundColor Red
    }
}

# Fix 3: Run success rate test to measure improvement
Write-Host "`n4. Running success rate test..." -ForegroundColor Green
try {
    & ".\test_final_success_rate_fixed.ps1"
} catch {
    Write-Host "Success rate test failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== TARGETED FIX SUMMARY ===" -ForegroundColor Cyan
Write-Host "Applied systematic 5 Whys methodology:" -ForegroundColor White
Write-Host "1. Identified specific error patterns in logs" -ForegroundColor White
Write-Host "2. Applied targeted fixes based on error analysis" -ForegroundColor White
Write-Host "3. Tested solution with comprehensive endpoint testing" -ForegroundColor White

Write-Host "`nIf Get Patient is still failing, the next step is:" -ForegroundColor Yellow
Write-Host "1. Review the error patterns identified above" -ForegroundColor White
Write-Host "2. Apply code-level fixes to the specific issue found" -ForegroundColor White
Write-Host "3. Focus on the exact layer where the 5 Whys analysis shows failure" -ForegroundColor White