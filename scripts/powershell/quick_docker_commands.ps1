# Quick Docker Commands for Clinical Workflows Restoration
# Simple commands to restart Docker and test functionality

Write-Host "🚀 QUICK DOCKER RESTART COMMANDS" -ForegroundColor Green
Write-Host "================================="

Write-Host "`n📋 PHASE 1: DOCKER RESTART" -ForegroundColor Cyan
Write-Host "Copy and run these commands one by one:" -ForegroundColor White

Write-Host "`n# 1. Stop all containers" -ForegroundColor Yellow
Write-Host "docker-compose down" -ForegroundColor White

Write-Host "`n# 2. Remove orphaned containers" -ForegroundColor Yellow  
Write-Host "docker-compose down --remove-orphans" -ForegroundColor White

Write-Host "`n# 3. Start all services (rebuild if needed)" -ForegroundColor Yellow
Write-Host "docker-compose up -d --build" -ForegroundColor White

Write-Host "`n# 4. Check container status" -ForegroundColor Yellow
Write-Host "docker-compose ps" -ForegroundColor White

Write-Host "`n# 5. Wait for services to start (30 seconds)" -ForegroundColor Yellow
Write-Host "Start-Sleep -Seconds 30" -ForegroundColor White

Write-Host "`n📋 PHASE 2: HEALTH CHECKS" -ForegroundColor Cyan
Write-Host "Test if services are working:" -ForegroundColor White

Write-Host "`n# 6. Test FastAPI health" -ForegroundColor Yellow
Write-Host "curl http://localhost:8000/health" -ForegroundColor White

Write-Host "`n# 7. Test API documentation" -ForegroundColor Yellow
Write-Host "curl http://localhost:8000/docs" -ForegroundColor White

Write-Host "`n📋 PHASE 3: CLINICAL WORKFLOWS TESTING" -ForegroundColor Cyan
Write-Host "Run these test scripts:" -ForegroundColor White

Write-Host "`n# 8. Test all endpoints (should now show clinical workflows)" -ForegroundColor Yellow
Write-Host ".\test_endpoints_working.ps1" -ForegroundColor White

Write-Host "`n# 9. Test clinical workflows specifically" -ForegroundColor Yellow
Write-Host ".\test_clinical_workflows_endpoints.ps1" -ForegroundColor White

Write-Host "`n# 10. Run enterprise test suite" -ForegroundColor Yellow
Write-Host ".\run_enterprise_tests.ps1" -ForegroundColor White

Write-Host "`n📋 ALTERNATIVE: RUN COMPLETE SCRIPT" -ForegroundColor Cyan
Write-Host "Or run the comprehensive automated script:" -ForegroundColor White
Write-Host ".\restart_docker_and_test_clinical_workflows.ps1" -ForegroundColor Green

Write-Host "`n📋 TROUBLESHOOTING COMMANDS" -ForegroundColor Cyan
Write-Host "If you encounter issues:" -ForegroundColor White

Write-Host "`n# View application logs" -ForegroundColor Yellow
Write-Host "docker-compose logs app" -ForegroundColor White

Write-Host "`n# View all service logs" -ForegroundColor Yellow
Write-Host "docker-compose logs" -ForegroundColor White

Write-Host "`n# Restart just the app service" -ForegroundColor Yellow
Write-Host "docker-compose restart app" -ForegroundColor White

Write-Host "`n# Check detailed container status" -ForegroundColor Yellow
Write-Host "docker-compose ps -a" -ForegroundColor White

Write-Host "`n# Check if all services are healthy" -ForegroundColor Yellow
Write-Host "docker-compose exec db pg_isready -U postgres" -ForegroundColor White
Write-Host "docker-compose exec redis redis-cli ping" -ForegroundColor White

Write-Host "`n🎯 EXPECTED RESULTS AFTER RESTART:" -ForegroundColor Green
Write-Host "  ✅ All Docker containers running and healthy" -ForegroundColor Gray
Write-Host "  ✅ Authentication working (no regression)" -ForegroundColor Gray
Write-Host "  ✅ Clinical workflows endpoints returning 200/401/403 (not 404)" -ForegroundColor Gray
Write-Host "  ✅ test_endpoints_working.ps1 shows 100% success rate" -ForegroundColor Gray
Write-Host "  ✅ OpenAPI schema includes clinical-workflows endpoints" -ForegroundColor Gray

Write-Host "`n🚀 READY TO EXECUTE!" -ForegroundColor Green
Write-Host "Choose your approach:" -ForegroundColor White
Write-Host "  • Run commands manually (copy/paste above)" -ForegroundColor Gray
Write-Host "  • Run automated script: .\restart_docker_and_test_clinical_workflows.ps1" -ForegroundColor Gray