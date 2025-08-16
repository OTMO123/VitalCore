# IRIS Healthcare API - Simple Pipeline Launcher
param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

# Map commands
$CommandMap = @{
    "s" = "status"
    "t" = "test" 
    "i" = "infrastructure"
    "sm" = "smoke"
    "sec" = "security"
    "h" = "help"
}

# Get full command
if ($CommandMap.ContainsKey($Command)) {
    $FullCommand = $CommandMap[$Command]
} else {
    $FullCommand = $Command
}

# Find manager script
$ManagerScript = Join-Path $PSScriptRoot "scripts\powershell\CICD-Pipeline-Manager.ps1"

# Execute
Write-Host "IRIS Healthcare API - Pipeline Launcher" -ForegroundColor Cyan
Write-Host "Command: $FullCommand" -ForegroundColor Gray

if (Test-Path $ManagerScript) {
    & $ManagerScript -Action $FullCommand
} else {
    Write-Host "Manager script not found: $ManagerScript" -ForegroundColor Red
    Write-Host "Available commands: status, test, infrastructure, smoke, security, help" -ForegroundColor Yellow
}