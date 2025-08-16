# Test login on port 8003
$headers = @{
    'Content-Type' = 'application/x-www-form-urlencoded'
}

$body = "username=admin&password=admin123"

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/auth/login" -Method POST -Headers $headers -Body $body
    Write-Host "SUCCESS: Login worked!" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 3
} catch {
    Write-Host "FAILED: Login failed" -ForegroundColor Red
    Write-Host "Status: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}