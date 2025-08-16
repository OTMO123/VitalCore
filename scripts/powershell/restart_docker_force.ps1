# Принудительный перезапуск Docker - Force Restart
# Полная очистка и перезапуск Docker Desktop

Write-Host "🐳 Docker Force Restart - Принудительный перезапуск" -ForegroundColor Red
Write-Host "=================================================" -ForegroundColor Red

Write-Host ""
Write-Host "Шаг 1: Остановка всех Docker процессов..." -ForegroundColor Yellow

try {
    # Остановить все контейнеры принудительно
    Write-Host "Останавливаем все контейнеры..." -ForegroundColor Cyan
    docker stop $(docker ps -aq) 2>$null
    
    # Удалить все контейнеры принудительно
    Write-Host "Удаляем все контейнеры..." -ForegroundColor Cyan
    docker rm $(docker ps -aq) 2>$null
    
    Write-Host "✅ Docker контейнеры очищены" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Docker контейнеры уже остановлены" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Шаг 2: Принудительная остановка Docker Desktop..." -ForegroundColor Yellow

try {
    # Остановить Docker Desktop через процессы
    Write-Host "Останавливаем Docker Desktop процессы..." -ForegroundColor Cyan
    Get-Process "*docker*" | Stop-Process -Force -ErrorAction SilentlyContinue
    
    # Остановить Docker службы
    Write-Host "Останавливаем Docker службы..." -ForegroundColor Cyan
    Stop-Service "Docker Desktop Service" -Force -ErrorAction SilentlyContinue
    Stop-Service "com.docker.service" -Force -ErrorAction SilentlyContinue
    
    Write-Host "✅ Docker процессы остановлены" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Некоторые процессы уже остановлены" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Шаг 3: Ожидание полной остановки..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "Шаг 4: Запуск Docker Desktop..." -ForegroundColor Yellow

try {
    # Найти Docker Desktop
    $dockerPath = @(
        "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe",
        "${env:LOCALAPPDATA}\Programs\Docker\Docker\Docker Desktop.exe",
        "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    ) | Where-Object { Test-Path $_ } | Select-Object -First 1
    
    if ($dockerPath) {
        Write-Host "Запускаем Docker Desktop: $dockerPath" -ForegroundColor Cyan
        Start-Process "$dockerPath" -WindowStyle Hidden
        
        Write-Host "⏳ Ожидаем запуск Docker (30 секунд)..." -ForegroundColor Yellow
        Start-Sleep -Seconds 30
        
        # Проверяем статус Docker
        $dockerTest = docker version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Docker Desktop успешно запущен!" -ForegroundColor Green
        } else {
            Write-Host "⚠️ Docker еще запускается, подождите еще немного..." -ForegroundColor Yellow
        }
    } else {
        Write-Host "❌ Docker Desktop не найден!" -ForegroundColor Red
        Write-Host "Установите Docker Desktop с: https://www.docker.com/products/docker-desktop" -ForegroundColor White
    }
} catch {
    Write-Host "❌ Ошибка запуска Docker: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "Шаг 5: Проверка статуса Docker..." -ForegroundColor Yellow

for ($i = 1; $i -le 6; $i++) {
    Write-Host "Попытка $i/6: Проверяем Docker..." -ForegroundColor Cyan
    
    try {
        $dockerInfo = docker info 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Docker работает нормально!" -ForegroundColor Green
            Write-Host ""
            Write-Host "🎯 Docker успешно перезапущен!" -ForegroundColor Green
            Write-Host "Теперь можно запускать: docker-compose up -d db" -ForegroundColor White
            break
        } else {
            Write-Host "⏳ Docker еще запускается..." -ForegroundColor Yellow
            Start-Sleep -Seconds 10
        }
    } catch {
        Write-Host "⏳ Ожидаем Docker..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
    }
    
    if ($i -eq 6) {
        Write-Host "❌ Docker не отвечает после перезапуска" -ForegroundColor Red
        Write-Host ""
        Write-Host "Попробуйте вручную:" -ForegroundColor Yellow
        Write-Host "1. Откройте Task Manager (Ctrl+Shift+Esc)" -ForegroundColor White
        Write-Host "2. Завершите все процессы Docker" -ForegroundColor White
        Write-Host "3. Запустите Docker Desktop из меню Пуск" -ForegroundColor White
    }
}

Write-Host ""
Write-Host "🚀 Готово! Docker должен быть перезапущен." -ForegroundColor Green