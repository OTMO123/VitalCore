Write-Host "рџ›ЎпёЏ Starting IRIS Healthcare API in Safe Mode" -ForegroundColor Green
Write-Host "=============================================="

Write-Host "рџ”Ќ Running safety checks..." -ForegroundColor Cyan

# Check dependencies
try {
    & python -c "import fastapi, pydantic, sqlalchemy" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "вњ… Dependencies OK" -ForegroundColor Green
    } else {
        Write-Host "вќЊ Dependencies missing" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "вќЊ Dependencies check failed" -ForegroundColor Red
    exit 1
}

Write-Host "рџљЂ Starting services..." -ForegroundColor Cyan

if (Get-Command docker-compose -ErrorAction SilentlyContinue) {
    Write-Host "рџђі Starting Docker services..." -ForegroundColor Blue
    docker-compose up -d postgres redis
    Start-Sleep 5
} else {
    Write-Host "вљ пёЏ  Docker not available" -ForegroundColor Yellow
}

Write-Host "рџ—„пёЏ Running migrations..." -ForegroundColor Blue
try {
    alembic upgrade head
} catch {
    Write-Host "вљ пёЏ  Migration may need manual setup" -ForegroundColor Yellow
}

Write-Host "рџЊџ Starting FastAPI..." -ForegroundColor Green
Write-Host "рџ“Љ API: http://localhost:8000" -ForegroundColor White
Write-Host "рџ“љ Docs: http://localhost:8000/docs" -ForegroundColor White

& python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
