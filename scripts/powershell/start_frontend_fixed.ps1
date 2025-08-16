# Start the React frontend with fixes applied
Write-Host "🚀 Starting React Frontend (Fixed Version)" -ForegroundColor Cyan
Write-Host "=" * 50

# Navigate to frontend directory
Set-Location "frontend"

Write-Host "📁 Current directory: $(Get-Location)" -ForegroundColor Yellow

# Check if node_modules exists
if (Test-Path "node_modules") {
    Write-Host "✅ node_modules found" -ForegroundColor Green
} else {
    Write-Host "❌ node_modules not found - installing dependencies..." -ForegroundColor Red
    npm install
}

# Check if package.json exists
if (Test-Path "package.json") {
    Write-Host "✅ package.json found" -ForegroundColor Green
    
    # Show available scripts
    Write-Host "`n📋 Available scripts:" -ForegroundColor Yellow
    npm run --silent 2>$null | Select-String "dev|start|build" | ForEach-Object { Write-Host "   $_" -ForegroundColor White }
} else {
    Write-Host "❌ package.json not found!" -ForegroundColor Red
    exit 1
}

Write-Host "`n🌐 Starting development server..." -ForegroundColor Green
Write-Host "Backend API: http://localhost:8003" -ForegroundColor White
Write-Host "Frontend will be: http://localhost:5173" -ForegroundColor White

Write-Host "`n⚡ Starting Vite dev server..." -ForegroundColor Cyan

# Start the development server
npm run dev