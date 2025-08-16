# Authenticated API Testing Helper
# Usage: .\Test-ApiWithAuth.ps1 -Endpoint "/api/v1/healthcare/patients" -Method GET

param(
    [string]$Endpoint,
    [string]$Method = "GET",
    [string]$Body = $null,
    [string]$Username = "admin", 
    [string]$Password = "admin123",
    [string]$BaseUrl = "http://localhost:8000"
)

# Get authentication token
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$token = & "$scriptDir\Get-AuthToken.ps1" -Username $Username -Password $Password -BaseUrl $BaseUrl

if (-not $token) {
    Write-Host "❌ Could not get authentication token" -ForegroundColor Red
    exit 1
}

# Prepare headers
$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

# Make authenticated request
try {
    $url = "$BaseUrl$Endpoint"
    
    if ($Body) {
        $response = Invoke-RestMethod -Uri $url -Method $Method -Headers $headers -Body $Body
    } else {
        $response = Invoke-RestMethod -Uri $url -Method $Method -Headers $headers
    }
    
    Write-Host "✅ Request successful to $Endpoint" -ForegroundColor Green
    Write-Host "Response:" -ForegroundColor Yellow
    $response | ConvertTo-Json -Depth 10
    
    return $response
}
catch {
    Write-Host "❌ Request failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Status Code: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
}