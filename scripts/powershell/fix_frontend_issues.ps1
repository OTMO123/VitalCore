# Fix frontend connection issues
Write-Host "=== FIXING FRONTEND CONNECTION ISSUES ===" -ForegroundColor Cyan

Write-Host "1. Current status:" -ForegroundColor Yellow
Write-Host "   - Frontend running on: http://localhost:3000" -ForegroundColor White
Write-Host "   - Backend should be on: http://localhost:8003" -ForegroundColor White
Write-Host "   - Proxy errors: ECONNREFUSED to backend" -ForegroundColor Red

Write-Host "`n2. Checking backend status..." -ForegroundColor Yellow
try {
    $backendTest = Invoke-WebRequest -Uri "http://localhost:8003/health" -UseBasicParsing -TimeoutSec 3
    Write-Host "   Backend Status: RUNNING ($($backendTest.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "   Backend Status: NOT RUNNING" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "`n   To start backend:" -ForegroundColor Yellow
    Write-Host "   uvicorn app.main:app --reload --host 0.0.0.0 --port 8003" -ForegroundColor White
}

Write-Host "`n3. Checking frontend status..." -ForegroundColor Yellow
try {
    $frontendTest = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 3
    Write-Host "   Frontend Status: RUNNING ($($frontendTest.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "   Frontend Status: NOT RESPONDING" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n4. Solutions:" -ForegroundColor Yellow
Write-Host "   Option 1: Use port 3000 (frontend is already running there)" -ForegroundColor Cyan
Write-Host "   Visit: http://localhost:3000" -ForegroundColor White

Write-Host "`n   Option 2: If page is loading forever, stop and restart frontend:" -ForegroundColor Cyan
Write-Host "   - Press Ctrl+C in the terminal running frontend" -ForegroundColor White
Write-Host "   - cd frontend" -ForegroundColor White
Write-Host "   - npm run dev" -ForegroundColor White

Write-Host "`n   Option 3: Check if backend is running:" -ForegroundColor Cyan
Write-Host "   - Backend should be on port 8003" -ForegroundColor White
Write-Host "   - Start with: uvicorn app.main:app --reload --port 8003" -ForegroundColor White

Write-Host "`n=== TROUBLESHOOTING COMPLETE ===" -ForegroundColor Cyan
Write-Host "Try visiting: http://localhost:3000" -ForegroundColor Green