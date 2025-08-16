# Debug Authentication with Detailed Error Capture
Write-Host "=== DETAILED AUTHENTICATION DEBUG ===" -ForegroundColor Yellow

$apiUrl = "http://localhost:8000/api/v1/auth/login"
$credentials = @{
    username = "admin"
    password = "admin123"
}

Write-Host "Testing URL: $apiUrl" -ForegroundColor Cyan
Write-Host "Credentials: admin/admin123" -ForegroundColor Cyan

try {
    # Test with detailed error handling
    $response = Invoke-RestMethod -Uri $apiUrl -Method POST -Body ($credentials | ConvertTo-Json) -ContentType "application/json" -ErrorAction Stop
    
    Write-Host "SUCCESS: Authentication worked!" -ForegroundColor Green
    Write-Host "Response received:" -ForegroundColor Green
    Write-Host ($response | ConvertTo-Json -Depth 3) -ForegroundColor White
    
} catch {
    Write-Host "AUTHENTICATION ERROR DETAILS:" -ForegroundColor Red
    Write-Host "Status Code: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
    Write-Host "Status Description: $($_.Exception.Response.StatusDescription)" -ForegroundColor Red
    
    # Try to get response content
    if ($_.Exception.Response) {
        $streamReader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $streamReader.ReadToEnd()
        $streamReader.Close()
        
        Write-Host "Error Response Body:" -ForegroundColor Yellow
        Write-Host $responseBody -ForegroundColor White
        
        # Try to parse as JSON for better readability
        try {
            $errorJson = $responseBody | ConvertFrom-Json
            Write-Host "Parsed Error:" -ForegroundColor Yellow
            Write-Host ($errorJson | ConvertTo-Json -Depth 3) -ForegroundColor White
        } catch {
            Write-Host "Could not parse response as JSON" -ForegroundColor Gray
        }
    }
    
    Write-Host "Full Exception:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor White
}

Write-Host "`n=== END DEBUG ===" -ForegroundColor Yellow