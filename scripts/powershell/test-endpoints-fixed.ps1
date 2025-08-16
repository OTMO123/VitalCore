# Test All Available Endpoints
# Usage: .\test-endpoints-fixed.ps1

Write-Host "IRIS Healthcare Platform - Endpoint Testing" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Gray

# Test basic endpoints
Write-Host "`nTesting Basic Endpoints:" -ForegroundColor Green
.\quick-test.ps1 "/health"
.\quick-test.ps1 "/health/detailed"

# Test healthcare records
Write-Host "`nTesting Healthcare Records:" -ForegroundColor Green  
.\quick-test.ps1 "/api/v1/healthcare/patients"
.\quick-test.ps1 "/api/v1/healthcare/immunizations"

# Test clinical workflows (correct paths)
Write-Host "`nTesting Clinical Workflows:" -ForegroundColor Green
.\quick-test.ps1 "/api/v1/clinical-workflows/workflows"
.\quick-test.ps1 "/api/v1/clinical-workflows/templates"

# Test IRIS API integration
Write-Host "`nTesting IRIS API Integration:" -ForegroundColor Green
.\quick-test.ps1 "/api/v1/iris/providers"
.\quick-test.ps1 "/api/v1/iris/immunizations"

# Test document management
Write-Host "`nTesting Document Management:" -ForegroundColor Green
.\quick-test.ps1 "/api/v1/documents/health"
.\quick-test.ps1 "/api/v1/documents/upload"

# Test audit and security
Write-Host "`nTesting Audit & Security:" -ForegroundColor Green
.\quick-test.ps1 "/api/v1/audit/logs"
.\quick-test.ps1 "/api/v1/security/events"

# Test analytics
Write-Host "`nTesting Analytics:" -ForegroundColor Green
.\quick-test.ps1 "/api/v1/analytics/population"
.\quick-test.ps1 "/api/v1/analytics/immunization-coverage"

Write-Host "`n" + "=" * 50 -ForegroundColor Gray
Write-Host "Endpoint testing complete!" -ForegroundColor Green