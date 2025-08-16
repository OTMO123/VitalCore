# Comprehensive Test Suite Execution for Enterprise Healthcare AI/ML Platform
# This script runs all 180+ tests to validate complete functionality

Write-Host "🧪 Enterprise Healthcare AI/ML Platform - Comprehensive Test Suite" -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green

# Set environment variables for testing
$env:ENVIRONMENT = "test"
$env:DEBUG = "true"
$env:TESTING = "true"
$env:SECRET_KEY = '3h5dPMCVjESdKNEJFcpgr2pkyb8hLfImMkgBLIJjX8+CBeNHbfLm5s0TZjrKPr4qwvsK3RUU2+dimXdGWSOqAg=='
$env:ENCRYPTION_KEY = 'wLS/8tedW1PE0EoZZLcuWhfIul5+xg05OJVISJHnr/E='
$env:JWT_SECRET_KEY = 'aUEoE2V9yrejA9RdlbyDylcN2NY7fNGEkvmVN7FH+hHkiRzlLIdbYBnitaSwyZiiBmagumE/wcnK6BQ52WUv2Q=='
$env:PHI_ENCRYPTION_KEY = 'xJM+yHn5/5RwwEvOHhRkP01DbbX7wxf1TWEOPOJV+sM='
$env:AUDIT_SIGNING_KEY = 'ac8b33202bb1fafe9bac30d568b51128f05d05a116651cb0b5daf8de55ecb1400261e9ab33c9f2a2de44b203e8ef368bb579e1712527c7d71188be4b7a8cd956'
$env:DATABASE_URL = "postgresql://postgres:password@localhost:5432/iris_db"
$env:REDIS_URL = "redis://localhost:6379/0"

Write-Host "Environment variables set for testing" -ForegroundColor Green

# Check if all platform services are running
Write-Host "`nChecking platform services..." -ForegroundColor Cyan

$requiredServices = @(
    "iris_postgres_p1",
    "iris_redis_p1",
    "iris_app_p1",
    "iris_app_enhanced_p2", 
    "iris_milvus_vector_p2",
    "iris_orthanc_p2",
    "iris_app_advanced_p3",
    "iris_grafana_p3"
)

$missingServices = @()
foreach ($service in $requiredServices) {
    try {
        $status = docker inspect $service --format='{{.State.Status}}' 2>$null
        if ($status -ne "running") {
            $missingServices += $service
        } else {
            Write-Host "   ✓ $service" -ForegroundColor Green
        }
    } catch {
        $missingServices += $service
        Write-Host "   ✗ $service" -ForegroundColor Red
    }
}

if ($missingServices.Count -gt 0) {
    Write-Host "`nWARNING: Some services not running:" -ForegroundColor Yellow
    foreach ($service in $missingServices) {
        Write-Host "   - $service" -ForegroundColor Yellow
    }
    Write-Host "Some tests may fail without all services running" -ForegroundColor Yellow
}

# Test execution phases
Write-Host "`n🔍 PHASE 1: Test Discovery and Count" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan

try {
    $testCount = python -m pytest --collect-only -q | Select-String "test_" | Measure-Object | Select-Object -ExpandProperty Count
    Write-Host "   Discovered $testCount test functions" -ForegroundColor Green
} catch {
    Write-Host "   Could not count tests automatically" -ForegroundColor Yellow
}

# Run tests by category
$testResults = @()

Write-Host "`n🧪 PHASE 2: Smoke Tests (Basic Functionality)" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

try {
    python -m pytest app/tests/smoke/ -v --tb=short --maxfail=5
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ SMOKE TESTS: PASSED" -ForegroundColor Green
        $testResults += "Smoke Tests: PASSED"
    } else {
        Write-Host "   ❌ SMOKE TESTS: FAILED" -ForegroundColor Red
        $testResults += "Smoke Tests: FAILED"
    }
} catch {
    Write-Host "   ❌ SMOKE TESTS: ERROR" -ForegroundColor Red
    $testResults += "Smoke Tests: ERROR"
}

Write-Host "`n🔐 PHASE 3: Security Tests" -ForegroundColor Cyan
Write-Host "==========================" -ForegroundColor Cyan

try {
    python -m pytest app/tests/security/ -v --tb=short --maxfail=5
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ SECURITY TESTS: PASSED" -ForegroundColor Green
        $testResults += "Security Tests: PASSED"
    } else {
        Write-Host "   ❌ SECURITY TESTS: FAILED" -ForegroundColor Red
        $testResults += "Security Tests: FAILED"
    }
} catch {
    Write-Host "   ❌ SECURITY TESTS: ERROR" -ForegroundColor Red
    $testResults += "Security Tests: ERROR"
}

Write-Host "`n📊 PHASE 4: Compliance Tests" -ForegroundColor Cyan
Write-Host "============================" -ForegroundColor Cyan

try {
    python -m pytest app/tests/compliance/ -v --tb=short --maxfail=5
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ COMPLIANCE TESTS: PASSED" -ForegroundColor Green
        $testResults += "Compliance Tests: PASSED"
    } else {
        Write-Host "   ❌ COMPLIANCE TESTS: FAILED" -ForegroundColor Red
        $testResults += "Compliance Tests: FAILED"
    }
} catch {
    Write-Host "   ❌ COMPLIANCE TESTS: ERROR" -ForegroundColor Red
    $testResults += "Compliance Tests: ERROR"
}

Write-Host "`n🔗 PHASE 5: Integration Tests" -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor Cyan

try {
    python -m pytest app/tests/integration/ -v --tb=short --maxfail=5
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ INTEGRATION TESTS: PASSED" -ForegroundColor Green
        $testResults += "Integration Tests: PASSED"
    } else {
        Write-Host "   ❌ INTEGRATION TESTS: FAILED" -ForegroundColor Red
        $testResults += "Integration Tests: FAILED"
    }
} catch {
    Write-Host "   ❌ INTEGRATION TESTS: ERROR" -ForegroundColor Red
    $testResults += "Integration Tests: ERROR"
}

Write-Host "`n🧠 PHASE 6: AI/ML and FHIR Tests" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

try {
    python -m pytest app/tests/fhir/ app/tests/e2e_predictive/ -v --tb=short --maxfail=5
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ AI/ML & FHIR TESTS: PASSED" -ForegroundColor Green
        $testResults += "AI/ML & FHIR Tests: PASSED"
    } else {
        Write-Host "   ❌ AI/ML & FHIR TESTS: FAILED" -ForegroundColor Red  
        $testResults += "AI/ML & FHIR Tests: FAILED"
    }
} catch {
    Write-Host "   ❌ AI/ML & FHIR TESTS: ERROR" -ForegroundColor Red
    $testResults += "AI/ML & FHIR Tests: ERROR"
}

Write-Host "`n🏥 PHASE 7: Healthcare Workflow Tests" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

try {
    python -m pytest app/tests/e2e_healthcare/ app/tests/healthcare_records/ -v --tb=short --maxfail=5
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ HEALTHCARE TESTS: PASSED" -ForegroundColor Green
        $testResults += "Healthcare Tests: PASSED"
    } else {
        Write-Host "   ❌ HEALTHCARE TESTS: FAILED" -ForegroundColor Red
        $testResults += "Healthcare Tests: FAILED"
    }
} catch {
    Write-Host "   ❌ HEALTHCARE TESTS: ERROR" -ForegroundColor Red
    $testResults += "Healthcare Tests: ERROR"
}

Write-Host "`n⚡ PHASE 8: Performance Tests" -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor Cyan

try {
    python -m pytest app/tests/performance/ app/tests/load_testing/ -v --tb=short --maxfail=5
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ PERFORMANCE TESTS: PASSED" -ForegroundColor Green
        $testResults += "Performance Tests: PASSED"
    } else {
        Write-Host "   ❌ PERFORMANCE TESTS: FAILED" -ForegroundColor Red
        $testResults += "Performance Tests: FAILED"
    }
} catch {
    Write-Host "   ❌ PERFORMANCE TESTS: ERROR" -ForegroundColor Red
    $testResults += "Performance Tests: ERROR"
}

Write-Host "`n🔬 PHASE 9: Core Module Tests" -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor Cyan

try {
    python -m pytest app/tests/core/ -v --tb=short --maxfail=5
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ CORE TESTS: PASSED" -ForegroundColor Green
        $testResults += "Core Tests: PASSED"  
    } else {
        Write-Host "   ❌ CORE TESTS: FAILED" -ForegroundColor Red
        $testResults += "Core Tests: FAILED"
    }
} catch {
    Write-Host "   ❌ CORE TESTS: ERROR" -ForegroundColor Red
    $testResults += "Core Tests: ERROR"
}

Write-Host "`n🌐 PHASE 10: Complete Test Suite" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

try {
    Write-Host "Running complete test suite with detailed output..." -ForegroundColor Yellow
    python -m pytest app/tests/ -v --tb=line --durations=10 --maxfail=20 | Tee-Object -FilePath "test_results.txt"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ COMPLETE TEST SUITE: PASSED" -ForegroundColor Green
        $testResults += "Complete Suite: PASSED"
    } else {
        Write-Host "   ❌ COMPLETE TEST SUITE: SOME FAILURES" -ForegroundColor Yellow
        $testResults += "Complete Suite: PARTIAL"
    }
} catch {
    Write-Host "   ❌ COMPLETE TEST SUITE: ERROR" -ForegroundColor Red
    $testResults += "Complete Suite: ERROR"
}

# Summary Report
Write-Host "`n📋 TEST EXECUTION SUMMARY" -ForegroundColor Green
Write-Host "=========================" -ForegroundColor Green

$passedCount = ($testResults | Where-Object { $_ -like "*PASSED*" }).Count
$totalCount = $testResults.Count

Write-Host "Test Categories Executed: $totalCount" -ForegroundColor Cyan
Write-Host "Test Categories Passed: $passedCount" -ForegroundColor Green

foreach ($result in $testResults) {
    if ($result -like "*PASSED*") {
        Write-Host "   ✅ $result" -ForegroundColor Green
    } elseif ($result -like "*FAILED*") {
        Write-Host "   ❌ $result" -ForegroundColor Red  
    } else {
        Write-Host "   ⚠️  $result" -ForegroundColor Yellow
    }
}

# Platform URLs for manual testing
Write-Host "`n🌐 PLATFORM URLS FOR MANUAL VALIDATION" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host "Phase 1 - Foundation:     http://localhost:8000/docs" -ForegroundColor White
Write-Host "Phase 2 - AI/ML Enhanced: http://localhost:8001/docs" -ForegroundColor White  
Write-Host "Phase 3 - Full Platform:  http://localhost:8002/docs" -ForegroundColor White
Write-Host "Grafana Dashboards:       http://localhost:3001" -ForegroundColor White
Write-Host "Jaeger Tracing:           http://localhost:16686" -ForegroundColor White
Write-Host "Kibana Logs:              http://localhost:5601" -ForegroundColor White

if ($passedCount -eq $totalCount) {
    Write-Host "`n🎉 SUCCESS: All test categories passed!" -ForegroundColor Green
    Write-Host "Enterprise Healthcare AI/ML Platform: FULLY VALIDATED" -ForegroundColor Green
} else {
    Write-Host "`n⚠️  PARTIAL SUCCESS: $passedCount/$totalCount test categories passed" -ForegroundColor Yellow
    Write-Host "Review individual test results for details" -ForegroundColor Yellow
}

Write-Host "`nDetailed test results saved to: test_results.txt" -ForegroundColor Cyan