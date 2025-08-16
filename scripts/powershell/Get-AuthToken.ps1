# Quick Authentication Helper for Development
# Usage: $token = .\Get-AuthToken.ps1 -Username admin -Password admin123

param(
    [string]$Username = "admin",
    [string]$Password = "admin123",
    [string]$BaseUrl = "http://localhost:8000"
)

try {
    $loginBody = @{
        username = $Username
        password = $Password
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "$BaseUrl/api/v1/auth/login" -Method POST -ContentType "application/json" -Body $loginBody
    
    Write-Host "✅ Authentication successful" -ForegroundColor Green
    Write-Host "Token: $($response.access_token)" -ForegroundColor Yellow
    
    # Export for easy use
    $env:AUTH_TOKEN = $response.access_token
    
    return $response.access_token
}
catch {
    Write-Host "❌ Authentication failed: $($_.Exception.Message)" -ForegroundColor Red
    return $null
}