# Clean restart of frontend
Write-Host "=== CLEAN FRONTEND RESTART ===" -ForegroundColor Cyan

Write-Host "1. Instructions to restart frontend:" -ForegroundColor Yellow
Write-Host "   - Go to the terminal where 'npm run dev' is running" -ForegroundColor White
Write-Host "   - Press Ctrl+C to stop the server" -ForegroundColor White
Write-Host "   - Wait for it to fully stop" -ForegroundColor White

Write-Host "`n2. Then restart with these commands:" -ForegroundColor Yellow
Write-Host "   cd frontend" -ForegroundColor White
Write-Host "   npm run dev" -ForegroundColor White

Write-Host "`n3. Alternative - kill any running processes:" -ForegroundColor Yellow
Write-Host "   If Ctrl+C doesn't work, you may need to:" -ForegroundColor Gray
Write-Host "   - Close the PowerShell/terminal window running frontend" -ForegroundColor Gray
Write-Host "   - Open new terminal in project directory" -ForegroundColor Gray
Write-Host "   - cd frontend" -ForegroundColor Gray
Write-Host "   - npm run dev" -ForegroundColor Gray

Write-Host "`n4. Check vite.config.ts proxy settings:" -ForegroundColor Yellow
try {
    $viteConfig = Get-Content "frontend/vite.config.ts" -Raw
    if ($viteConfig -match "target.*8003") {
        Write-Host "   ✅ Vite proxy configured for port 8003" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️ Vite proxy may need configuration check" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ⚠️ Could not read vite.config.ts" -ForegroundColor Yellow
}

Write-Host "`n5. Expected result:" -ForegroundColor Yellow
Write-Host "   - Frontend will start on http://localhost:5173 OR http://localhost:3000" -ForegroundColor White
Write-Host "   - No proxy errors in console" -ForegroundColor White
Write-Host "   - Dashboard should load properly" -ForegroundColor White

Write-Host "`n=== RESTART INSTRUCTIONS COMPLETE ===" -ForegroundColor Cyan
Write-Host "After restart, visit the URL shown in the terminal output" -ForegroundColor Green