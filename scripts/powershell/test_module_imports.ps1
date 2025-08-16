# Test Clinical Workflows Module Imports
# Verifies that all clinical workflows components can be imported properly

Write-Host "🧪 CLINICAL WORKFLOWS MODULE IMPORT TESTING" -ForegroundColor Green
Write-Host "============================================"

Write-Host "`n📦 Testing module imports inside Docker container..." -ForegroundColor Cyan

# Test 1: Router Import
Write-Host "`n1. Testing Router Import..." -ForegroundColor Yellow
try {
    $routerTest = docker-compose exec -T app python -c "from app.modules.clinical_workflows.router import router; print('SUCCESS: Router imported')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Router: Import successful" -ForegroundColor Green
        Write-Host "   $routerTest" -ForegroundColor Gray
    } else {
        Write-Host "❌ Router: Import failed" -ForegroundColor Red
        Write-Host "   Error: $routerTest" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Router: Test failed - $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Models Import
Write-Host "`n2. Testing Models Import..." -ForegroundColor Yellow
try {
    $modelsTest = docker-compose exec -T app python -c "from app.modules.clinical_workflows.models import ClinicalWorkflow, ClinicalWorkflowStep; print('SUCCESS: Models imported')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Models: Import successful" -ForegroundColor Green
        Write-Host "   $modelsTest" -ForegroundColor Gray
    } else {
        Write-Host "❌ Models: Import failed" -ForegroundColor Red
        Write-Host "   Error: $modelsTest" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Models: Test failed - $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Service Import
Write-Host "`n3. Testing Service Import..." -ForegroundColor Yellow
try {
    $serviceTest = docker-compose exec -T app python -c "from app.modules.clinical_workflows.service import ClinicalWorkflowService; print('SUCCESS: Service imported')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Service: Import successful" -ForegroundColor Green
        Write-Host "   $serviceTest" -ForegroundColor Gray
    } else {
        Write-Host "❌ Service: Import failed" -ForegroundColor Red
        Write-Host "   Error: $serviceTest" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Service: Test failed - $($_.Exception.Message)" -ForegroundColor Red
}

# Test 4: Schemas Import
Write-Host "`n4. Testing Schemas Import..." -ForegroundColor Yellow
try {
    $schemasTest = docker-compose exec -T app python -c "from app.modules.clinical_workflows.schemas import ClinicalWorkflowCreate; print('SUCCESS: Schemas imported')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Schemas: Import successful" -ForegroundColor Green
        Write-Host "   $schemasTest" -ForegroundColor Gray
    } else {
        Write-Host "❌ Schemas: Import failed" -ForegroundColor Red
        Write-Host "   Error: $schemasTest" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Schemas: Test failed - $($_.Exception.Message)" -ForegroundColor Red
}

# Test 5: Complete Module Import
Write-Host "`n5. Testing Complete Module Import..." -ForegroundColor Yellow
try {
    $moduleTest = docker-compose exec -T app python -c "import app.modules.clinical_workflows; print('SUCCESS: Complete module imported')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Complete Module: Import successful" -ForegroundColor Green
        Write-Host "   $moduleTest" -ForegroundColor Gray
    } else {
        Write-Host "❌ Complete Module: Import failed" -ForegroundColor Red
        Write-Host "   Error: $moduleTest" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Complete Module: Test failed - $($_.Exception.Message)" -ForegroundColor Red
}

# Test 6: Database Models Registration
Write-Host "`n6. Testing Database Models Registration..." -ForegroundColor Yellow
try {
    $dbTest = docker-compose exec -T app python -c "from app.core.database_unified import ClinicalWorkflow; print('SUCCESS: DB models registered')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Database Registration: Successful" -ForegroundColor Green
        Write-Host "   $dbTest" -ForegroundColor Gray
    } else {
        Write-Host "❌ Database Registration: Failed" -ForegroundColor Red
        Write-Host "   Error: $dbTest" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Database Registration: Test failed - $($_.Exception.Message)" -ForegroundColor Red
}

# Test 7: FastAPI App Import with Clinical Workflows
Write-Host "`n7. Testing FastAPI App with Clinical Workflows..." -ForegroundColor Yellow
try {
    $appTest = docker-compose exec -T app python -c "from app.main import app; print('SUCCESS: FastAPI app with clinical workflows loaded')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ FastAPI App: Import successful" -ForegroundColor Green
        Write-Host "   $appTest" -ForegroundColor Gray
    } else {
        Write-Host "❌ FastAPI App: Import failed" -ForegroundColor Red
        Write-Host "   Error: $appTest" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ FastAPI App: Test failed - $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n============================================" -ForegroundColor Green
Write-Host "IMPORT TEST SUMMARY" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green

Write-Host "`n📋 Next Steps Based on Results:" -ForegroundColor Cyan
Write-Host "  • If all imports successful: Check router registration in FastAPI" -ForegroundColor Gray
Write-Host "  • If models failed: Fix SQLAlchemy relationship issues" -ForegroundColor Gray
Write-Host "  • If service failed: Check dependency imports" -ForegroundColor Gray
Write-Host "  • If router failed: Check endpoint definitions" -ForegroundColor Gray

Write-Host "`n🔧 If imports are successful but endpoints still 404:" -ForegroundColor Yellow
Write-Host "  1. Check FastAPI startup logs for router registration" -ForegroundColor Gray
Write-Host "  2. Verify router is included in main.py" -ForegroundColor Gray
Write-Host "  3. Restart app service: docker-compose restart app" -ForegroundColor Gray

Write-Host "`n📞 Test endpoints after fixing issues:" -ForegroundColor Green
Write-Host "  .\test_clinical_workflows_endpoints.ps1" -ForegroundColor White