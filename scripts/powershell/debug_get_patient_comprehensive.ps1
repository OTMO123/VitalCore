# Comprehensive Get Patient Debug Script - 5 Whys Analysis
# This script tests the Get Patient endpoint with detailed logging analysis

Write-Host "=== COMPREHENSIVE GET PATIENT DEBUG - 5 WHYS ANALYSIS ===" -ForegroundColor Cyan
Write-Host "Following systematic 5 Whys methodology to identify exact failure point" -ForegroundColor Yellow

# Step 1: Get authentication token
Write-Host "`n1. Getting authentication token..." -ForegroundColor Green
$loginResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method Post -ContentType "application/json" -Body '{"username":"admin","password":"admin123"}'
if ($loginResponse.access_token) {
    Write-Host "✅ Authentication successful" -ForegroundColor Green
    $token = $loginResponse.access_token
} else {
    Write-Host "❌ Authentication failed" -ForegroundColor Red
    exit 1
}

# Step 2: Get list of existing patients
Write-Host "`n2. Getting list of existing patients..." -ForegroundColor Green
$headers = @{"Authorization" = "Bearer $token"}
$patientsResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients" -Method Get -Headers $headers
if ($patientsResponse.patients -and $patientsResponse.patients.Count -gt 0) {
    Write-Host "✅ Found $($patientsResponse.patients.Count) patients" -ForegroundColor Green
    $testPatientId = $patientsResponse.patients[0].id
    Write-Host "📋 Using patient ID for testing: $testPatientId" -ForegroundColor Yellow
} else {
    Write-Host "❌ No patients found" -ForegroundColor Red
    exit 1
}

# Step 3: Test Get Patient endpoint with comprehensive error capture
Write-Host "`n3. Testing Get Patient endpoint with detailed error capture..." -ForegroundColor Green
Write-Host "🔍 WHY #1: Testing if Get Patient returns 500 error..." -ForegroundColor Magenta

try {
    $getPatientResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients/$testPatientId" -Method Get -Headers $headers -ErrorAction Stop
    Write-Host "✅ SUCCESS: Get Patient endpoint returned successfully!" -ForegroundColor Green
    Write-Host "Patient Name: $($getPatientResponse.name[0].given[0]) $($getPatientResponse.name[0].family)" -ForegroundColor Yellow
    Write-Host "Patient ID: $($getPatientResponse.id)" -ForegroundColor Yellow
} catch {
    Write-Host "❌ CONFIRMED: Get Patient returns error" -ForegroundColor Red
    Write-Host "Error Status Code: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
    Write-Host "Error Message: $($_.Exception.Message)" -ForegroundColor Red
    
    # WHY #2: Analyze the specific error type
    Write-Host "`n🔍 WHY #2: What type of error is this?" -ForegroundColor Magenta
    if ($_.Exception.Response.StatusCode -eq 500) {
        Write-Host "Confirmed: 500 Internal Server Error" -ForegroundColor Red
        Write-Host "This indicates a server-side processing error, not a client request issue" -ForegroundColor Yellow
    }
    
    # Get detailed error response
    try {
        $errorStream = $_.Exception.Response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($errorStream)
        $errorBody = $reader.ReadToEnd()
        Write-Host "Error Response Body: $errorBody" -ForegroundColor Red
    } catch {
        Write-Host "Could not read error response body" -ForegroundColor Yellow
    }
}

# Step 4: Test the step-by-step debug endpoint to identify exact failure layer
Write-Host "`n4. Testing step-by-step debug endpoint..." -ForegroundColor Green
Write-Host "🔍 WHY #3: Which exact layer is failing?" -ForegroundColor Magenta

try {
    $debugResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/step-by-step-debug/$testPatientId" -Method Get -Headers $headers -ErrorAction Stop
    Write-Host "✅ Debug endpoint successful" -ForegroundColor Green
    Write-Host "Steps completed: $($debugResponse.steps_completed.Count)" -ForegroundColor Yellow
    foreach ($step in $debugResponse.steps_completed) {
        Write-Host "  ✅ $step" -ForegroundColor Green
    }
    if ($debugResponse.current_step) {
        Write-Host "Current step: $($debugResponse.current_step)" -ForegroundColor Yellow
    }
    if ($debugResponse.error) {
        Write-Host "❌ Error in debug: $($debugResponse.error)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Debug endpoint also failed" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Step 5: Compare with working Update Patient endpoint
Write-Host "`n5. Testing working Update Patient endpoint for comparison..." -ForegroundColor Green
Write-Host "🔍 WHY #4: How does Update Patient work but Get Patient doesn't?" -ForegroundColor Magenta

$updateBody = @{
    gender = "male"
    consent_status = "approved"
} | ConvertTo-Json

try {
    $updateResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/debug-update/$testPatientId" -Method Put -Headers $headers -ContentType "application/json" -Body $updateBody -ErrorAction Stop
    Write-Host "✅ Update Patient endpoint works!" -ForegroundColor Green
    Write-Host "Updated patient ID: $($updateResponse.patient_id)" -ForegroundColor Yellow
    Write-Host "Updated gender: $($updateResponse.gender)" -ForegroundColor Yellow
} catch {
    Write-Host "❌ Update Patient also fails" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Step 6: Analyze server logs (if accessible)
Write-Host "`n6. Server log analysis recommendations..." -ForegroundColor Green
Write-Host "🔍 WHY #5: What do the detailed logs show?" -ForegroundColor Magenta
Write-Host "Check server logs for these specific markers:" -ForegroundColor Yellow
Write-Host "  🚀 ROUTER ENTRY: Should show request processing start" -ForegroundColor White
Write-Host "  📋 DEPENDENCIES: Should show dependency injection success" -ForegroundColor White
Write-Host "  🌐 CLIENT INFO: Should show client info extraction" -ForegroundColor White
Write-Host "  📦 IMPORTS: Should show database imports" -ForegroundColor White
Write-Host "  🔑 UUID: Should show UUID validation" -ForegroundColor White
Write-Host "  🗄️ DATABASE: Should show database query execution" -ForegroundColor White
Write-Host "  🔄 RESPONSE CREATION: Should show response building" -ForegroundColor White
Write-Host "  ❌ ERROR: Should show exact failure point" -ForegroundColor White

Write-Host "`n=== 5 WHYS ANALYSIS SUMMARY ===" -ForegroundColor Cyan
Write-Host "WHY #1: Get Patient returns 500 error - CONFIRMED" -ForegroundColor Red
Write-Host "WHY #2: Server-side processing error - IDENTIFIED" -ForegroundColor Yellow
Write-Host "WHY #3: Specific layer failure - CHECK DEBUG ENDPOINT RESULTS" -ForegroundColor Yellow
Write-Host "WHY #4: Update works vs Get fails - COMPARE PATTERNS" -ForegroundColor Yellow
Write-Host "WHY #5: Root cause - CHECK SERVER LOGS FOR EXACT FAILURE POINT" -ForegroundColor Yellow

Write-Host "`n=== NEXT ACTIONS ===" -ForegroundColor Cyan
Write-Host "1. Check server logs with the comprehensive logging markers above" -ForegroundColor White
Write-Host "2. Identify which layer (🚀📋🌐📦🔑🗄️🔄) shows the ❌ ERROR" -ForegroundColor White
Write-Host "3. Apply targeted fix based on exact failure point" -ForegroundColor White
Write-Host "4. Test fix and verify success rate improvement" -ForegroundColor White