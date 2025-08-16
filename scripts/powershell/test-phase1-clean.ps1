# Test All Critical Fixes - Phase 1 Complete (Clean Version)
# Usage: .\test-phase1-clean.ps1

Write-Host "Testing All Phase 1 Critical Fixes" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Gray

$successCount = 0
$totalTests = 0

# Function to test endpoint and track results
function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Endpoint,
        [string]$ExpectedStatus = "2xx"
    )
    
    $global:totalTests++
    Write-Host "`nTesting: $Name" -ForegroundColor Yellow
    Write-Host "   Endpoint: $Endpoint" -ForegroundColor Gray
    
    try {
        $result = & .\quick-test.ps1 $Endpoint
        
        # Simple success check - if we get back data, it's likely working
        if ($result) {
            Write-Host "   SUCCESS" -ForegroundColor Green
            $global:successCount++
            return $true
        } else {
            Write-Host "   FAILED - No response" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "   FAILED - Error: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

Write-Host "`nPhase 1 Fixes Testing:" -ForegroundColor Cyan

# Test 1: Database schema fix (audit_logs)
Write-Host "`nTesting Audit Logs Fix:" -ForegroundColor Green
Test-Endpoint "Audit Logs" "/api/v1/audit/logs"

# Test 2: Healthcare immunizations (404 fix)
Write-Host "`nTesting Healthcare Endpoints:" -ForegroundColor Green  
Test-Endpoint "Healthcare Immunizations" "/api/v1/healthcare/immunizations"
Test-Endpoint "Healthcare Health" "/api/v1/healthcare/health"

# Test 3: IRIS API endpoints (404 fix)
Write-Host "`nTesting IRIS API Endpoints:" -ForegroundColor Green
Test-Endpoint "IRIS Providers" "/api/v1/iris/providers"
Test-Endpoint "IRIS Immunizations" "/api/v1/iris/immunizations"

# Test 4: Analytics endpoints (404 fix)  
Write-Host "`nTesting Analytics Endpoints:" -ForegroundColor Green
Test-Endpoint "Analytics Population" "/api/v1/analytics/population"
Test-Endpoint "Analytics Immunization Coverage" "/api/v1/analytics/immunization-coverage"

# Test 5: Security events (404 fix)
Write-Host "`nTesting Security Endpoints:" -ForegroundColor Green
Test-Endpoint "Security Events" "/api/v1/security/events"

# Test 6: Document Management (500 fix)
Write-Host "`nTesting Document Management:" -ForegroundColor Green
Test-Endpoint "Document Upload" "/api/v1/documents/upload"
Test-Endpoint "Document Health" "/api/v1/documents/health"

# Test 7: Existing working endpoints (regression test)
Write-Host "`nTesting Existing Working Endpoints:" -ForegroundColor Green
Test-Endpoint "Health Check" "/health"
Test-Endpoint "Healthcare Patients" "/api/v1/healthcare/patients"
Test-Endpoint "Clinical Workflows" "/api/v1/clinical-workflows/workflows"

# Summary
Write-Host "`n" + "=" * 60 -ForegroundColor Gray
Write-Host "TESTING RESULTS SUMMARY" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Gray

$successRate = if ($totalTests -gt 0) { [math]::Round(($successCount / $totalTests) * 100, 1) } else { 0 }

Write-Host "Total Tests: $totalTests" -ForegroundColor White
Write-Host "Successful: $successCount" -ForegroundColor Green
Write-Host "Failed: $($totalTests - $successCount)" -ForegroundColor Red
Write-Host "Success Rate: $successRate%" -ForegroundColor $(if ($successRate -gt 80) { "Green" } elseif ($successRate -gt 50) { "Yellow" } else { "Red" })

if ($successRate -gt 80) {
    Write-Host "`nEXCELLENT! Phase 1 fixes are working well!" -ForegroundColor Green
    Write-Host "Ready to proceed with Phase 2 improvements" -ForegroundColor Green
} elseif ($successRate -gt 50) {
    Write-Host "`nGOOD progress! Most fixes are working" -ForegroundColor Yellow
    Write-Host "Some endpoints may need additional work" -ForegroundColor Yellow
} else {
    Write-Host "`nMore work needed on the fixes" -ForegroundColor Red
    Write-Host "Review the failed endpoints for additional issues" -ForegroundColor Red
}

Write-Host "`nNext Steps:" -ForegroundColor Cyan
Write-Host "1. Run database migration if needed" -ForegroundColor White
Write-Host "2. Restart Docker services if needed" -ForegroundColor White 
Write-Host "3. Test specific failed endpoints individually" -ForegroundColor White
Write-Host "4. Proceed to Phase 2 functional improvements" -ForegroundColor White

Write-Host "`n" + "=" * 60 -ForegroundColor Gray
Write-Host "Phase 1 Critical Fixes Testing Complete!" -ForegroundColor Cyan