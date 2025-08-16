# Docker Emergency Restart - Экстренный перезапуск
# Самый быстрый способ принудительно перезапустить Docker

Write-Host "🚨 Docker Emergency Restart" -ForegroundColor Red
Write-Host "============================" -ForegroundColor Red

# Метод 1: Через Task Manager команды
Write-Host "Метод 1: Принудительная остановка через процессы..." -ForegroundColor Yellow
taskkill /f /im "Docker Desktop.exe" 2>$null
taskkill /f /im "dockerd.exe" 2>$null  
taskkill /f /im "docker.exe" 2>$null
taskkill /f /im "com.docker.service.exe" 2>$null

Write-Host "Ожидание 3 секунды..." -ForegroundColor Cyan
Start-Sleep -Seconds 3

# Метод 2: Запуск Docker Desktop
Write-Host "Метод 2: Запуск Docker Desktop..." -ForegroundColor Yellow

# Поиск Docker Desktop
$dockerPaths = @(
    "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe",
    "${env:LOCALAPPDATA}\Programs\Docker\Docker\Docker Desktop.exe"
)

$dockerFound = $false
foreach ($path in $dockerPaths) {
    if (Test-Path $path) {
        Write-Host "Найден Docker: $path" -ForegroundColor Green
        Start-Process "$path"
        $dockerFound = $true
        break
    }
}

if (-not $dockerFound) {
    Write-Host "❌ Docker Desktop не найден!" -ForegroundColor Red
    Write-Host "Попробуйте вручную из меню Пуск" -ForegroundColor White
}

Write-Host ""
Write-Host "✅ Docker перезапуск инициирован!" -ForegroundColor Green
Write-Host "Подождите 1-2 минуты для полного запуска" -ForegroundColor Yellow