# Fix frontend connection issues
Write-Host "🔧 Fixing Frontend Connection Issues" -ForegroundColor Cyan
Write-Host "=" * 50

Write-Host "Current status:" -ForegroundColor Yellow
Write-Host "✅ Backend: Running on Windows localhost:8003" -ForegroundColor Green  
Write-Host "❌ Frontend: Can't connect via WSL" -ForegroundColor Red

Write-Host "`nTesting backend connection from Windows..." -ForegroundColor Yellow

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8003/health" -Method GET -TimeoutSec 5
    Write-Host "✅ Backend reachable from Windows" -ForegroundColor Green
    Write-Host "Response: $($response | ConvertTo-Json -Compress)" -ForegroundColor White
} catch {
    Write-Host "❌ Backend not reachable: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n🔧 Solution: Update Vite proxy to use Windows host" -ForegroundColor Cyan

Write-Host "`nOptions to fix:" -ForegroundColor Yellow
Write-Host "1. Change Vite proxy from localhost:8003 to host.docker.internal:8003" -ForegroundColor White
Write-Host "2. Or run backend with --host 0.0.0.0 to bind all interfaces" -ForegroundColor White
Write-Host "3. Or use Windows IP address in proxy config" -ForegroundColor White

Write-Host "`n📝 Next steps:" -ForegroundColor Green
Write-Host "1. I'll update the Vite config to fix the proxy" -ForegroundColor White
Write-Host "2. Or restart backend with proper host binding" -ForegroundColor White

Write-Host "`n🌐 Once fixed, frontend will connect properly!" -ForegroundColor Cyan