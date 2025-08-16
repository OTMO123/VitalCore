# Simple Get Patient Debug - 5 Whys Analysis
# This script tests Get Patient with detailed error analysis

Write-Host "=== 5 WHYS ANALYSIS: GET PATIENT DEBUG ===" -ForegroundColor Cyan

# Step 1: Get authentication
Write-Host "`n1. Getting authentication token..." -ForegroundColor Green
try {
    $loginResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method Post -ContentType "application/json" -Body '{"username":"admin","password":"admin123"}'
    $token = $loginResponse.access_token
    $headers = @{"Authorization" = "Bearer $token"}
    Write-Host "Authentication successful" -ForegroundColor Green
} catch {
    Write-Host "Authentication failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Step 2: Get patient list
Write-Host "`n2. Getting patient list..." -ForegroundColor Green
try {
    $patientsResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients" -Method Get -Headers $headers
    if ($patientsResponse.patients -and $patientsResponse.patients.Count -gt 0) {
        $testPatientId = $patientsResponse.patients[0].id
        Write-Host "Found $($patientsResponse.patients.Count) patients" -ForegroundColor Green
        Write-Host "Using patient ID: $testPatientId" -ForegroundColor Yellow
    } else {
        Write-Host "No patients found" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "Failed to get patient list: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Step 3: Test Get Patient and capture detailed error
Write-Host "`n3. WHY #1: Testing Get Patient endpoint..." -ForegroundColor Magenta
try {
    $getPatientResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients/$testPatientId" -Method Get -Headers $headers
    Write-Host "SUCCESS: Get Patient works!" -ForegroundColor Green
    Write-Host "Patient: $($getPatientResponse.name[0].given[0]) $($getPatientResponse.name[0].family)" -ForegroundColor Yellow
} catch {
    Write-Host "WHY #1 CONFIRMED: Get Patient returns 500 error" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Status: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
    
    # WHY #2: Get detailed error information
    Write-Host "`nWHY #2: What is the detailed error response?" -ForegroundColor Magenta
    try {
        $errorResponse = $_.Exception.Response
        $reader = New-Object System.IO.StreamReader($errorResponse.GetResponseStream())
        $errorBody = $reader.ReadToEnd()
        Write-Host "Error Response Body: $errorBody" -ForegroundColor Red
    } catch {
        Write-Host "Could not read error response body" -ForegroundColor Yellow
    }
}

# Step 4: Check server logs for detailed analysis
Write-Host "`n4. WHY #3: Checking server logs for specific failure layer..." -ForegroundColor Magenta
Write-Host "Looking for comprehensive logging markers..." -ForegroundColor Yellow

try {
    $logs = docker logs iris_app --tail 50 2>&1
    
    Write-Host "`nRecent server logs:" -ForegroundColor Cyan
    $logs | ForEach-Object { Write-Host $_ -ForegroundColor Gray }
    
    # Look for our specific logging markers
    Write-Host "`nSearching for 5 Whys analysis markers..." -ForegroundColor Yellow
    
    $routerEntry = $logs | Select-String "ROUTER ENTRY: GET /patients"
    $dependencies = $logs | Select-String "DEPENDENCIES:"
    $clientInfo = $logs | Select-String "CLIENT INFO:"
    $imports = $logs | Select-String "IMPORTS:"
    $uuidValidation = $logs | Select-String "UUID:"
    $database = $logs | Select-String "DATABASE:"
    $responseCreation = $logs | Select-String "RESPONSE CREATION:"
    $errors = $logs | Select-String "ERROR|Exception|exception"
    
    Write-Host "`n=== 5 WHYS LAYER ANALYSIS ===" -ForegroundColor Cyan
    
    if ($routerEntry) {
        Write-Host "LAYER 1 - ROUTER ENTRY: SUCCESS" -ForegroundColor Green
    } else {
        Write-Host "LAYER 1 - ROUTER ENTRY: NOT FOUND" -ForegroundColor Red
    }
    
    if ($dependencies) {
        Write-Host "LAYER 2 - DEPENDENCIES: SUCCESS" -ForegroundColor Green
    } else {
        Write-Host "LAYER 2 - DEPENDENCIES: NOT FOUND" -ForegroundColor Red
    }
    
    if ($clientInfo) {
        Write-Host "LAYER 3 - CLIENT INFO: SUCCESS" -ForegroundColor Green
    } else {
        Write-Host "LAYER 3 - CLIENT INFO: NOT FOUND" -ForegroundColor Red
    }
    
    if ($imports) {
        Write-Host "LAYER 4 - IMPORTS: SUCCESS" -ForegroundColor Green
    } else {
        Write-Host "LAYER 4 - IMPORTS: NOT FOUND" -ForegroundColor Red
    }
    
    if ($uuidValidation) {
        Write-Host "LAYER 5 - UUID VALIDATION: SUCCESS" -ForegroundColor Green
    } else {
        Write-Host "LAYER 5 - UUID VALIDATION: NOT FOUND" -ForegroundColor Red
    }
    
    if ($database) {
        Write-Host "LAYER 6 - DATABASE: SUCCESS" -ForegroundColor Green
    } else {
        Write-Host "LAYER 6 - DATABASE: NOT FOUND" -ForegroundColor Red
    }
    
    if ($responseCreation) {
        Write-Host "LAYER 7 - RESPONSE CREATION: SUCCESS" -ForegroundColor Green
    } else {
        Write-Host "LAYER 7 - RESPONSE CREATION: NOT FOUND" -ForegroundColor Red
    }
    
    if ($errors) {
        Write-Host "`nERRORS FOUND:" -ForegroundColor Red
        $errors | ForEach-Object { Write-Host "  $($_.Line)" -ForegroundColor Red }
    } else {
        Write-Host "`nNO ERRORS FOUND IN LOGS" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "Could not check server logs: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Step 5: Compare with working Update Patient
Write-Host "`n5. WHY #4: Testing working Update Patient for comparison..." -ForegroundColor Magenta

try {
    $updateBody = '{"gender":"male","consent_status":"approved"}'
    $updateResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/debug-update/$testPatientId" -Method Put -Headers $headers -ContentType "application/json" -Body $updateBody
    Write-Host "WHY #4 ANSWER: Update Patient works successfully" -ForegroundColor Green
    Write-Host "This confirms the issue is specific to Get Patient endpoint" -ForegroundColor Yellow
} catch {
    Write-Host "WHY #4 ANSWER: Update Patient also fails" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Step 6: Test the debug endpoint
Write-Host "`n6. WHY #5: Testing step-by-step debug endpoint..." -ForegroundColor Magenta

try {
    $debugResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/step-by-step-debug/$testPatientId" -Method Get -Headers $headers
    Write-Host "WHY #5 ANSWER: Debug endpoint successful" -ForegroundColor Green
    Write-Host "Steps completed:" -ForegroundColor Yellow
    $debugResponse.steps_completed | ForEach-Object { Write-Host "  $_" -ForegroundColor Green }
    
    if ($debugResponse.error) {
        Write-Host "Debug error found: $($debugResponse.error)" -ForegroundColor Red
    }
} catch {
    Write-Host "WHY #5 ANSWER: Debug endpoint also fails" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== 5 WHYS ANALYSIS CONCLUSION ===" -ForegroundColor Cyan
Write-Host "Based on the layer analysis above, the failure occurs at:" -ForegroundColor Yellow
Write-Host "- First layer that shows 'NOT FOUND' is the point of failure" -ForegroundColor White
Write-Host "- Check the errors section for specific exception details" -ForegroundColor White
Write-Host "- Compare with Update Patient behavior to identify differences" -ForegroundColor White

Write-Host "`nNext actions:" -ForegroundColor Yellow
Write-Host "1. Identify the exact layer where logging stops" -ForegroundColor White
Write-Host "2. Check the specific error message in that layer" -ForegroundColor White
Write-Host "3. Apply targeted fix to that specific issue" -ForegroundColor White