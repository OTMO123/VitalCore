# Check why the FastAPI server is crashing
Write-Host "🚨 CHECKING SERVER CRASH LOGS..." -ForegroundColor Red

try {
    Write-Host "Getting Docker container status..." -ForegroundColor Yellow
    $containerStatus = docker ps -a --filter "name=iris_app" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    Write-Host $containerStatus -ForegroundColor Cyan
    
    Write-Host "`n📋 Getting recent logs from iris_app container..." -ForegroundColor Yellow
    $logs = docker logs iris_app --tail 50 2>&1
    
    Write-Host "`n🔍 FULL RECENT LOGS:" -ForegroundColor Red
    $logs | ForEach-Object { 
        if ($_ -like "*ERROR*" -or $_ -like "*Exception*" -or $_ -like "*Traceback*") {
            Write-Host $_ -ForegroundColor Red
        } elseif ($_ -like "*WARNING*" -or $_ -like "*WARN*") {
            Write-Host $_ -ForegroundColor Yellow  
        } else {
            Write-Host $_
        }
    }
    
    Write-Host "`n🔄 Trying to restart container..." -ForegroundColor Yellow
    docker restart iris_app
    
    Write-Host "Waiting 10 seconds for startup..." -ForegroundColor Gray
    Start-Sleep 10
    
    Write-Host "`n📋 Getting startup logs after restart..." -ForegroundColor Yellow
    $startupLogs = docker logs iris_app --tail 20 2>&1
    
    Write-Host "`n🆕 STARTUP LOGS:" -ForegroundColor Green
    $startupLogs | ForEach-Object { 
        if ($_ -like "*ERROR*" -or $_ -like "*Exception*" -or $_ -like "*Traceback*") {
            Write-Host $_ -ForegroundColor Red
        } elseif ($_ -like "*WARNING*" -or $_ -like "*WARN*") {
            Write-Host $_ -ForegroundColor Yellow  
        } else {
            Write-Host $_
        }
    }
    
} catch {
    Write-Host "❌ Error getting logs: $_" -ForegroundColor Red
}

Write-Host "`n✅ Log analysis complete!" -ForegroundColor Green