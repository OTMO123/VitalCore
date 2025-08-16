# Simple Commands to Fix Clinical Workflows 404 Issue
# Clean PowerShell commands without syntax issues

Write-Host "CLINICAL WORKFLOWS 404 FIX - SIMPLE COMMANDS" -ForegroundColor Green
Write-Host "============================================="

Write-Host "`nCURRENT STATUS:" -ForegroundColor Cyan
Write-Host "- Docker containers: All healthy" -ForegroundColor Green
Write-Host "- Authentication: Working perfectly" -ForegroundColor Green
Write-Host "- Some clinical endpoints: Return 403 (good sign)" -ForegroundColor Yellow
Write-Host "- Most clinical endpoints: Return 404 (needs fix)" -ForegroundColor Red

Write-Host "`nSTEP 1: CHECK APPLICATION LOGS" -ForegroundColor Yellow
Write-Host "Copy and run this command to see startup errors:" -ForegroundColor White
Write-Host "docker-compose logs app --tail=50" -ForegroundColor Cyan

Write-Host "`nSTEP 2: TEST MODULE IMPORTS" -ForegroundColor Yellow
Write-Host "Test if clinical workflows modules can be imported:" -ForegroundColor White
Write-Host "docker-compose exec app python -c `"from app.modules.clinical_workflows.router import router; print('Router OK')`"" -ForegroundColor Cyan

Write-Host "`nSTEP 3: RESTART APP SERVICE" -ForegroundColor Yellow
Write-Host "Restart just the FastAPI application:" -ForegroundColor White
Write-Host "docker-compose restart app" -ForegroundColor Cyan

Write-Host "`nSTEP 4: WAIT FOR RESTART" -ForegroundColor Yellow
Write-Host "Wait 30 seconds for full startup:" -ForegroundColor White
Write-Host "Start-Sleep -Seconds 30" -ForegroundColor Cyan

Write-Host "`nSTEP 5: TEST ENDPOINTS AGAIN" -ForegroundColor Yellow
Write-Host "Check if clinical workflows are now working:" -ForegroundColor White
Write-Host ".\test_clinical_workflows_endpoints.ps1" -ForegroundColor Cyan

Write-Host "`nIF STILL NOT WORKING:" -ForegroundColor Red
Write-Host "Force rebuild the application:" -ForegroundColor White
Write-Host "docker-compose build app" -ForegroundColor Cyan
Write-Host "docker-compose up -d app" -ForegroundColor Cyan

Write-Host "`nQUICK TEST:" -ForegroundColor Green
Write-Host "After any fix, test with:" -ForegroundColor White
Write-Host ".\test_endpoints_working.ps1" -ForegroundColor Cyan

Write-Host "`nEXPECTED RESULT:" -ForegroundColor Green
Write-Host "Clinical workflows endpoints should return:" -ForegroundColor White
Write-Host "- 200: Working endpoint" -ForegroundColor Green
Write-Host "- 401/403: Secured endpoint (good)" -ForegroundColor Yellow
Write-Host "- NOT 404: Endpoint not found (bad)" -ForegroundColor Red