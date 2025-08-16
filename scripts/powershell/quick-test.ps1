# Quick Test Script - Simple API Testing
# Usage: .\quick-test.ps1 [endpoint]

param(
    [string]$Endpoint = "/api/v1/healthcare/patients",
    [string]$Method = "GET",
    [string]$Body = $null
)

# Change to scripts directory if not already there
$currentDir = Get-Location
if ($currentDir.Path -notmatch "scripts\\powershell$") {
    if (Test-Path "scripts\powershell") {
        Set-Location "scripts\powershell"
    }
}

Write-Host "🏥 IRIS API Quick Test" -ForegroundColor Cyan
Write-Host "Endpoint: $Endpoint" -ForegroundColor Yellow

try {
    if ($Body) {
        & .\Test-ApiWithAuth.ps1 -Endpoint $Endpoint -Method $Method -Body $Body
    } else {
        & .\Test-ApiWithAuth.ps1 -Endpoint $Endpoint -Method $Method
    }
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Return to original directory
Set-Location $currentDir