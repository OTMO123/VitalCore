# Development Aliases for IRIS Healthcare Platform
# Source this file to get convenient aliases for testing
# Usage: . .\dev-aliases.ps1

# Set base directory
$IRIS_PROJECT_ROOT = $PSScriptRoot

# Authentication aliases
function Get-IrisToken {
    param(
        [string]$Username = "admin",
        [string]$Password = "admin123"
    )
    & "$IRIS_PROJECT_ROOT\scripts\powershell\Get-AuthToken.ps1" -Username $Username -Password $Password
}

function Test-IrisApi {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Endpoint,
        [string]$Method = "GET",
        [string]$Body = $null
    )
    & "$IRIS_PROJECT_ROOT\scripts\powershell\Test-ApiWithAuth.ps1" -Endpoint $Endpoint -Method $Method -Body $Body
}

# Quick test functions
function Test-Health { Test-IrisApi -Endpoint "/health" }
function Test-Patients { Test-IrisApi -Endpoint "/api/v1/healthcare/patients" }
function Test-Auth { Get-IrisToken }
function Test-Login { 
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -ContentType "application/json" -Body '{"username":"admin","password":"admin123"}'
        Write-Host "✅ Login successful" -ForegroundColor Green
        Write-Host "Token: $($response.access_token)" -ForegroundColor Yellow
        return $response.access_token
    } catch {
        Write-Host "❌ Login failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Clinical workflows testing
function Test-ClinicalWorkflows { Test-IrisApi -Endpoint "/api/v1/clinical-workflows/templates" }

# Document management
function Test-Documents { Test-IrisApi -Endpoint "/api/v1/documents" }

# Display available commands
function Show-IrisCommands {
    Write-Host "🏥 IRIS Healthcare Platform - Development Commands:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Authentication:" -ForegroundColor Yellow
    Write-Host "  Get-IrisToken       # Get authentication token"
    Write-Host "  Test-Auth           # Test authentication"  
    Write-Host "  Test-Login          # Simple login test"
    Write-Host ""
    Write-Host "API Testing:" -ForegroundColor Yellow
    Write-Host "  Test-IrisApi        # Generic API test with auth"
    Write-Host "  Test-Health         # Test health endpoint"
    Write-Host "  Test-Patients       # Test patients endpoint"
    Write-Host "  Test-ClinicalWorkflows # Test clinical workflows"
    Write-Host "  Test-Documents      # Test document management"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Green
    Write-Host '  $token = Get-IrisToken'
    Write-Host '  Test-IrisApi -Endpoint "/api/v1/healthcare/patients" -Method POST -Body "{""name"":""Test Patient""}"'
    Write-Host ""
}

# Auto-show commands when sourced
Show-IrisCommands

Write-Host "✅ IRIS development aliases loaded successfully!" -ForegroundColor Green
Write-Host "Run 'Show-IrisCommands' to see available commands again." -ForegroundColor Gray