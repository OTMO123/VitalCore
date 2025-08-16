# Test All Available Endpoints
# Usage: .\test-endpoints.ps1

Write-Host "🏥 IRIS Healthcare Platform - Endpoint Testing" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Gray

# Test basic endpoints
Write-Host "`n✅ Testing Basic Endpoints:" -ForegroundColor Green
.\quick-test.ps1 "/health"
.\quick-test.ps1 "/health/detailed"

# Test healthcare records
Write-Host "`n🏥 Testing Healthcare Records:" -ForegroundColor Green  
.\quick-test.ps1 "/api/v1/healthcare/patients"
.\quick-test.ps1 "/api/v1/healthcare/immunizations"

# Test clinical workflows (correct paths)
Write-Host "`n🔄 Testing Clinical Workflows:" -ForegroundColor Green
.\quick-test.ps1 "/api/v1/clinical-workflows/workflows"
.\quick-test.ps1 "/api/v1/clinical-workflows/templates"

# Test IRIS API integration
Write-Host "`n🌐 Testing IRIS API Integration:" -ForegroundColor Green
.\quick-test.ps1 "/api/v1/iris/providers"
.\quick-test.ps1 "/api/v1/iris/immunizations"

# Test document management
Write-Host "`n📄 Testing Document Management:" -ForegroundColor Green
.\quick-test.ps1 "/api/v1/documents/health"
.\quick-test.ps1 "/api/v1/documents/upload"

# Test audit and security
Write-Host "`n🔒 Testing Audit & Security:" -ForegroundColor Green
.\quick-test.ps1 "/api/v1/audit/logs"
.\quick-test.ps1 "/api/v1/security/events"

# Test analytics
Write-Host "`n📊 Testing Analytics:" -ForegroundColor Green
.\quick-test.ps1 "/api/v1/analytics/population"
.\quick-test.ps1 "/api/v1/analytics/immunization-coverage"

Write-Host "`n" + "=" * 50 -ForegroundColor Gray
Write-Host "✅ Endpoint testing complete!" -ForegroundColor Green