# Get full error details for patient creation
Write-Host "Getting full error details..." -ForegroundColor Yellow

# Get more comprehensive logs
Write-Host "Full application logs:" -ForegroundColor Cyan
docker logs iris_app --tail 25

Write-Host "`nChecking for specific error patterns..." -ForegroundColor Yellow
docker logs iris_app 2>&1 | Select-String -Pattern "error|Error|ERROR|Failed|failed|Exception|exception" | Select-Object -Last 10