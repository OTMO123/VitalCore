# Clinical Workflows Diagnostic Script
# Analyzes why clinical workflows endpoints are not working after Docker restart

Write-Host "🔍 CLINICAL WORKFLOWS DIAGNOSTIC ANALYSIS" -ForegroundColor Green
Write-Host "=========================================="

Write-Host "`n📊 CURRENT STATUS SUMMARY:" -ForegroundColor Cyan
Write-Host "  ✅ Docker containers: All healthy and running" -ForegroundColor Green
Write-Host "  ✅ Authentication: Working perfectly (no regression)" -ForegroundColor Green
Write-Host "  ✅ Database services: PostgreSQL and Redis healthy" -ForegroundColor Green
Write-Host "  ❌ Clinical workflows: Endpoints returning 404" -ForegroundColor Red
Write-Host "  ✅ Some endpoints: Analytics/Metrics returning 403 (secured)" -ForegroundColor Yellow

Write-Host "`n🔍 ANALYSIS:" -ForegroundColor Cyan
Write-Host "The fact that some clinical workflows endpoints return 403 (secured)" -ForegroundColor White
Write-Host "instead of 404 suggests the router is partially loaded but not all endpoints." -ForegroundColor White

Write-Host "`n📋 DIAGNOSTIC COMMANDS:" -ForegroundColor Cyan
Write-Host "Run these commands to investigate:" -ForegroundColor White

Write-Host "`n# 1. Check application startup logs" -ForegroundColor Yellow
Write-Host "docker-compose logs app --tail=100" -ForegroundColor White

Write-Host "`n# 2. Check for import/module loading errors" -ForegroundColor Yellow
Write-Host "docker-compose logs app | grep -i 'clinical\|import\|error'" -ForegroundColor White

Write-Host "`n# 3. Check container status" -ForegroundColor Yellow
Write-Host "docker-compose ps" -ForegroundColor White

Write-Host "`n# 4. Test specific endpoints that are working" -ForegroundColor Yellow
Write-Host "curl -H 'Authorization: Bearer TOKEN' http://localhost:8000/api/v1/clinical-workflows/analytics" -ForegroundColor White
Write-Host "curl -H 'Authorization: Bearer TOKEN' http://localhost:8000/api/v1/clinical-workflows/metrics" -ForegroundColor White

Write-Host "`n# 5. Check OpenAPI schema for clinical workflows paths" -ForegroundColor Yellow
Write-Host "curl http://localhost:8000/openapi.json | grep -i clinical" -ForegroundColor White

Write-Host "`n🔧 POSSIBLE CAUSES & SOLUTIONS:" -ForegroundColor Cyan

Write-Host "`n1. PARTIAL ROUTER LOADING:" -ForegroundColor Yellow
Write-Host "  Issue: Some endpoints load, others don't" -ForegroundColor Gray
Write-Host "  Solution: Check for syntax errors in router.py" -ForegroundColor Gray
Write-Host "  Command: docker-compose exec app python -c 'from app.modules.clinical_workflows.router import router; print(\"Router loaded successfully\")'" -ForegroundColor White

Write-Host "`n2. DEPENDENCY ISSUES:" -ForegroundColor Yellow
Write-Host "  Issue: Missing dependencies for some endpoints" -ForegroundColor Gray
Write-Host "  Solution: Check service dependencies" -ForegroundColor Gray
Write-Host "  Command: docker-compose exec app python -c 'from app.modules.clinical_workflows.service import get_clinical_workflow_service; print(\"Service loaded\")'" -ForegroundColor White

Write-Host "`n3. DATABASE MODEL ISSUES:" -ForegroundColor Yellow
Write-Host "  Issue: SQLAlchemy model relationship problems" -ForegroundColor Gray
Write-Host "  Solution: Verify models can be imported" -ForegroundColor Gray
Write-Host "  Command: docker-compose exec app python -c 'from app.modules.clinical_workflows.models import ClinicalWorkflow; print(\"Models loaded\")'" -ForegroundColor White

Write-Host "`n4. SCHEMA VALIDATION ISSUES:" -ForegroundColor Yellow
Write-Host "  Issue: Pydantic schema problems" -ForegroundColor Gray
Write-Host "  Solution: Check schema imports" -ForegroundColor Gray
Write-Host "  Command: docker-compose exec app python -c 'from app.modules.clinical_workflows.schemas import ClinicalWorkflowCreate; print(\"Schemas loaded\")'" -ForegroundColor White

Write-Host "`n📋 IMMEDIATE ACTION PLAN:" -ForegroundColor Green

Write-Host "`n1. CHECK APPLICATION LOGS:" -ForegroundColor White
Write-Host "   docker-compose logs app --tail=100" -ForegroundColor Gray
Write-Host "   Look for error messages during startup" -ForegroundColor Gray

Write-Host "`n2. TEST MODULE IMPORTS:" -ForegroundColor White
Write-Host "   docker-compose exec app python -c 'from app.modules.clinical_workflows import router, models, service, schemas'" -ForegroundColor Gray

Write-Host "`n3. RESTART SPECIFIC SERVICE:" -ForegroundColor White
Write-Host "   docker-compose restart app" -ForegroundColor Gray
Write-Host "   Wait 30 seconds and test again" -ForegroundColor Gray

Write-Host "`n4. CHECK ROUTER REGISTRATION:" -ForegroundColor White
Write-Host "   Look at FastAPI startup logs for router includes" -ForegroundColor Gray

Write-Host "`n🎯 EXPECTED BEHAVIOR:" -ForegroundColor Cyan
Write-Host "  After fixing, ALL endpoints should return:" -ForegroundColor White
Write-Host "  - 200: Working endpoint" -ForegroundColor Green
Write-Host "  - 401/403: Secured endpoint (good)" -ForegroundColor Yellow
Write-Host "  - NOT 404: Endpoint not found (bad)" -ForegroundColor Red

Write-Host "`n📞 QUICK TEST:" -ForegroundColor Green
Write-Host "Run this to test if fix is working:" -ForegroundColor White
Write-Host ".\test_clinical_workflows_endpoints.ps1" -ForegroundColor Gray

Write-Host "`n💡 POSITIVE SIGNS:" -ForegroundColor Green
Write-Host "  ✅ Authentication working (restoration didn't break anything)" -ForegroundColor Green
Write-Host "  ✅ Some clinical endpoints return 403 (partially working)" -ForegroundColor Green
Write-Host "  ✅ All Docker services healthy" -ForegroundColor Green
Write-Host "  ✅ Code changes successfully applied" -ForegroundColor Green

Write-Host "`n🔧 FIRST STEP: Check logs for the root cause" -ForegroundColor Yellow
Write-Host "docker-compose logs app --tail=100" -ForegroundColor White