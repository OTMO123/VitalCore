# Fix Clinical Workflows 404 Issues
# Addresses common causes of clinical workflows endpoints returning 404

Write-Host "🔧 CLINICAL WORKFLOWS 404 FIX SCRIPT" -ForegroundColor Green
Write-Host "====================================="

Write-Host "`n📊 CURRENT SITUATION:" -ForegroundColor Cyan
Write-Host "  ✅ Docker containers are healthy and running" -ForegroundColor Green
Write-Host "  ✅ Authentication working perfectly" -ForegroundColor Green
Write-Host "  ✅ Some clinical endpoints return 403 (secured - good sign)" -ForegroundColor Yellow
Write-Host "  ❌ Most clinical endpoints return 404 (not found)" -ForegroundColor Red

Write-Host "`n🔍 DIAGNOSIS:" -ForegroundColor Cyan
Write-Host "The fact that analytics/metrics return 403 instead of 404 suggests" -ForegroundColor White
Write-Host "the router is partially loaded. This indicates a module loading issue." -ForegroundColor White

Write-Host "`n🎯 FIX STRATEGY:" -ForegroundColor Green

Write-Host "`n1. TEST MODULE IMPORTS" -ForegroundColor Yellow
Write-Host "First, let's check if the modules can be imported:" -ForegroundColor White
Write-Host ".\test_module_imports.ps1" -ForegroundColor Gray

Write-Host "`n2. RESTART APP SERVICE" -ForegroundColor Yellow
Write-Host "Sometimes a simple restart fixes loading issues:" -ForegroundColor White
Write-Host "docker-compose restart app" -ForegroundColor Gray
Write-Host "Start-Sleep -Seconds 30" -ForegroundColor Gray

Write-Host "`n3. CHECK APPLICATION LOGS" -ForegroundColor Yellow
Write-Host "Look for startup errors:" -ForegroundColor White
Write-Host "docker-compose logs app --tail=50" -ForegroundColor Gray

Write-Host "`n4. FORCE REBUILD IF NEEDED" -ForegroundColor Yellow
Write-Host "If restart doesn't work, rebuild the app:" -ForegroundColor White
Write-Host "docker-compose build app" -ForegroundColor Gray
Write-Host "docker-compose up -d app" -ForegroundColor Gray

Write-Host "`n🚀 EXECUTE FIX SEQUENCE:" -ForegroundColor Green
Write-Host "Run these commands in order:" -ForegroundColor White

Write-Host "`n# Step 1: Test imports (diagnostic)" -ForegroundColor Cyan
Write-Host ".\test_module_imports.ps1" -ForegroundColor White

Write-Host "`n# Step 2: Restart app service" -ForegroundColor Cyan
Write-Host "docker-compose restart app" -ForegroundColor White

Write-Host "`n# Step 3: Wait for startup" -ForegroundColor Cyan
Write-Host "Start-Sleep -Seconds 30" -ForegroundColor White

Write-Host "`n# Step 4: Test endpoints" -ForegroundColor Cyan
Write-Host ".\test_clinical_workflows_endpoints.ps1" -ForegroundColor White

Write-Host "`n# Step 5: If still not working, check logs" -ForegroundColor Cyan
Write-Host "docker-compose logs app --tail=100" -ForegroundColor White

Write-Host "`n📋 AUTOMATED FIX SEQUENCE:" -ForegroundColor Green
Write-Host "Or run this automated sequence:" -ForegroundColor White

$choice = Read-Host "`nDo you want to run the automated fix sequence? (y/N)"
if ($choice -eq "y" -or $choice -eq "Y") {
    Write-Host "`n🔧 RUNNING AUTOMATED FIX..." -ForegroundColor Yellow
    
    Write-Host "`n1. Testing module imports..." -ForegroundColor Cyan
    & ".\test_module_imports.ps1"
    
    Write-Host "`n2. Restarting app service..." -ForegroundColor Cyan
    docker-compose restart app
    
    Write-Host "`n3. Waiting for app to restart (30 seconds)..." -ForegroundColor Cyan
    Start-Sleep -Seconds 30
    
    Write-Host "`n4. Testing clinical workflows endpoints..." -ForegroundColor Cyan
    & ".\test_clinical_workflows_endpoints.ps1"
    
    Write-Host "`n5. Checking container status..." -ForegroundColor Cyan
    docker-compose ps
    
} else {
    Write-Host "`nManual fix sequence ready. Run commands above when ready." -ForegroundColor Yellow
}

Write-Host "`n🎯 SUCCESS INDICATORS:" -ForegroundColor Green
Write-Host "After fixing, you should see:" -ForegroundColor White
Write-Host "  ✅ Clinical workflows endpoints return 200/401/403 (not 404)" -ForegroundColor Green
Write-Host "  ✅ OpenAPI schema includes clinical-workflows paths" -ForegroundColor Green
Write-Host "  ✅ Test success rate improves significantly" -ForegroundColor Green

Write-Host "`n🔍 IF STILL NOT WORKING:" -ForegroundColor Yellow
Write-Host "Check application logs for specific error messages:" -ForegroundColor White
Write-Host "docker-compose logs app | grep -i 'error\|clinical\|import'" -ForegroundColor Gray

Write-Host "`n📞 FINAL VERIFICATION:" -ForegroundColor Cyan
Write-Host "After fix, run complete testing:" -ForegroundColor White
Write-Host ".\test_endpoints_working.ps1" -ForegroundColor Gray
Write-Host "Expected: Higher success rate with clinical workflows working" -ForegroundColor Gray