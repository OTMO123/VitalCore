# Quick Server Status Check
Write-Host "🔍 Checking server status..." -ForegroundColor Yellow

# Check if port 8000 is open
try {
    $connection = Test-NetConnection -ComputerName "localhost" -Port 8000 -InformationLevel Quiet
    if ($connection) {
        Write-Host "✅ Port 8000 is open" -ForegroundColor Green
    } else {
        Write-Host "❌ Port 8000 is not open - server is not running" -ForegroundColor Red
        Write-Host "💡 Start the server with: python app/main.py" -ForegroundColor Cyan
    }
}
catch {
    Write-Host "❌ Cannot check port 8000" -ForegroundColor Red
    Write-Host "💡 Start the server with: python app/main.py" -ForegroundColor Cyan
}

# Check if python/uvicorn processes are running
$processes = Get-Process | Where-Object { $_.ProcessName -like "*python*" -or $_.ProcessName -like "*uvicorn*" }
if ($processes) {
    Write-Host "✅ Python processes found:" -ForegroundColor Green
    $processes | Select-Object ProcessName, Id | Format-Table
} else {
    Write-Host "❌ No Python/Uvicorn processes running" -ForegroundColor Red
}

Write-Host "`n🚀 To start the server:" -ForegroundColor Cyan
Write-Host "1. Open a new PowerShell window" -ForegroundColor White  
Write-Host "2. cd C:\Users\aurik\Code_Projects\2_scraper" -ForegroundColor White
Write-Host "3. python app/main.py" -ForegroundColor White
Write-Host "4. Wait for 'Application startup complete'" -ForegroundColor White
Write-Host "5. Then run .\simple_api_test.ps1 again" -ForegroundColor White