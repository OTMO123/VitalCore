# Quick SQLite Solution
Write-Host "Using SQLite for immediate solution..." -ForegroundColor Yellow

# Stop containers
docker-compose down

# Update config to use SQLite
$configPath = "app/core/config.py"
$content = Get-Content $configPath -Raw
$content = $content -replace 'default="postgresql://postgres:password@localhost:5432/iris_db"', 'default="sqlite:///./iris_app.db"'
Set-Content -Path $configPath -Value $content

# Start only the app (no need for PostgreSQL)
docker-compose up -d app

Write-Host "Waiting for app to start..."
Start-Sleep 15

# Test the API
Write-Host "Testing API..."
$response = Invoke-RestMethod -Uri "http://localhost:8000/health" 
Write-Host "Health check: $($response.status)"

Write-Host "SQLite solution completed!" -ForegroundColor Green