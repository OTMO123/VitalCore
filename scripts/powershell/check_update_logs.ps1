# Check Docker logs for Update Patient debugging
Write-Host "🔍 Checking Docker logs for Update Patient step-by-step debugging..." -ForegroundColor Cyan

# Get the last 100 lines of logs from the FastAPI container
Write-Host "📋 Getting recent logs from iris_app container..." -ForegroundColor Yellow

try {
    $logs = docker logs iris_app --tail 100 2>&1
    
    # Filter for our specific debugging logs
    $updateLogs = $logs | Where-Object { 
        $_ -like "*STEP*" -or 
        $_ -like "*UPDATE*" -or 
        $_ -like "*🟢*" -or 
        $_ -like "*❌*" -or
        $_ -like "*🎉*" -or
        $_ -like "*249b1e26-9d42-4991-a557-f0d6a12d5ab7*"
    }
    
    if ($updateLogs) {
        Write-Host "`n🎯 Found Update Patient debugging logs:" -ForegroundColor Green
        $updateLogs | ForEach-Object { 
            if ($_ -like "*❌*") {
                Write-Host $_ -ForegroundColor Red
            } elseif ($_ -like "*🟢*") {
                Write-Host $_ -ForegroundColor Green  
            } elseif ($_ -like "*🎉*") {
                Write-Host $_ -ForegroundColor Cyan
            } else {
                Write-Host $_
            }
        }
    } else {
        Write-Host "❌ No specific Update Patient logs found. Showing all recent logs:" -ForegroundColor Yellow
        $logs | Select-Object -Last 20 | ForEach-Object { Write-Host $_ }
    }
    
    # Also check for any exception traces
    $errorLogs = $logs | Where-Object { 
        $_ -like "*ERROR*" -or 
        $_ -like "*Exception*" -or 
        $_ -like "*Traceback*" -or
        $_ -like "*FAILED*"
    }
    
    if ($errorLogs) {
        Write-Host "`n🚨 Found error logs:" -ForegroundColor Red
        $errorLogs | Select-Object -Last 10 | ForEach-Object { 
            Write-Host $_ -ForegroundColor Red
        }
    }
    
} catch {
    Write-Host "❌ Error getting Docker logs: $_" -ForegroundColor Red
    Write-Host "💡 Make sure Docker is running and iris_app container exists" -ForegroundColor Yellow
}

Write-Host "`n✅ Log analysis complete!" -ForegroundColor Green