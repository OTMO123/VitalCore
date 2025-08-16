# Get the 7th root cause
Write-Host "Finding 7th root cause..." -ForegroundColor Yellow

# Get comprehensive error logs
docker logs iris_app 2>&1 | Select-String -Pattern "error|Error|ERROR|Failed|failed|Exception|exception|invalid|Invalid" | Select-Object -Last 15