# VitalCore Docker Integration Test Script
# Comprehensive testing of Docker frontend-backend connection

param(
    [switch]$Quick,
    [switch]$Detailed,
    [switch]$API,
    [switch]$Frontend,
    [switch]$Voice,
    [int]$Timeout = 30
)

$ErrorActionPreference = "Continue"

# Configuration
$FrontendUrl = "http://localhost:5173"
$BackendUrl = "http://localhost:8000"
$MinIOUrl = "http://localhost:9001"
$ComposeFile = "docker-compose.frontend.yml"

# Test results
$TestResults = @()

function Add-TestResult {
    param(
        [string]$TestName,
        [bool]$Passed,
        [string]$Details = "",
        [string]$Error = ""
    )
    
    $TestResults += [PSCustomObject]@{
        Test = $TestName
        Status = if ($Passed) { "✅ PASS" } else { "❌ FAIL" }
        Details = $Details
        Error = $Error
    }
    
    $color = if ($Passed) { "Green" } else { "Red" }
    $status = if ($Passed) { "✅ PASS" } else { "❌ FAIL" }
    Write-Host "[$status] $TestName" -ForegroundColor $color
    if ($Details) { Write-Host "    Details: $Details" -ForegroundColor "Gray" }
    if ($Error) { Write-Host "    Error: $Error" -ForegroundColor "Red" }
}

function Test-ServiceHealth {
    Write-Host "`n🔍 Testing Service Health..." -ForegroundColor "Blue"
    
    # Test Docker services
    try {
        $services = docker-compose -f $ComposeFile ps --format json | ConvertFrom-Json
        $runningServices = $services | Where-Object { $_.State -eq "running" }
        
        Add-TestResult "Docker Services Running" ($runningServices.Count -ge 5) "Found $($runningServices.Count) running services"
        
        foreach ($service in $runningServices) {
            Add-TestResult "Service: $($service.Service)" $true "Container: $($service.Name), Status: $($service.State)"
        }
    } catch {
        Add-TestResult "Docker Services Check" $false "" $_.Exception.Message
    }
}

function Test-NetworkConnectivity {
    Write-Host "`n🌐 Testing Network Connectivity..." -ForegroundColor "Blue"
    
    # Test backend health endpoint
    try {
        $response = Invoke-WebRequest -Uri "$BackendUrl/health" -TimeoutSec $Timeout -ErrorAction Stop
        $healthData = $response.Content | ConvertFrom-Json
        
        Add-TestResult "Backend Health Endpoint" ($response.StatusCode -eq 200) "Status: $($healthData.status), Version: $($healthData.version)"
    } catch {
        Add-TestResult "Backend Health Endpoint" $false "" $_.Exception.Message
    }
    
    # Test frontend accessibility
    try {
        $response = Invoke-WebRequest -Uri $FrontendUrl -TimeoutSec $Timeout -ErrorAction Stop
        Add-TestResult "Frontend Accessibility" ($response.StatusCode -eq 200) "Response size: $($response.Content.Length) bytes"
    } catch {
        Add-TestResult "Frontend Accessibility" $false "" $_.Exception.Message
    }
    
    # Test MinIO console
    try {
        $response = Invoke-WebRequest -Uri $MinIOUrl -TimeoutSec $Timeout -ErrorAction Stop
        Add-TestResult "MinIO Console" ($response.StatusCode -eq 200) "MinIO console accessible"
    } catch {
        Add-TestResult "MinIO Console" $false "" $_.Exception.Message
    }
}

function Test-APIEndpoints {
    Write-Host "`n🔧 Testing API Endpoints..." -ForegroundColor "Blue"
    
    $endpoints = @(
        @{ Path = "/docs"; Name = "API Documentation" },
        @{ Path = "/openapi.json"; Name = "OpenAPI Schema" },
        @{ Path = "/api/v1/health"; Name = "Health Check V1" },
        @{ Path = "/api/v1/auth/status"; Name = "Auth Status" }
    )
    
    foreach ($endpoint in $endpoints) {
        try {
            $response = Invoke-WebRequest -Uri "$BackendUrl$($endpoint.Path)" -TimeoutSec $Timeout -ErrorAction Stop
            Add-TestResult $endpoint.Name ($response.StatusCode -eq 200) "Status: $($response.StatusCode)"
        } catch {
            $statusCode = $_.Exception.Response.StatusCode.Value__
            if ($statusCode -eq 401 -or $statusCode -eq 403) {
                Add-TestResult $endpoint.Name $true "Protected endpoint (Status: $statusCode)"
            } else {
                Add-TestResult $endpoint.Name $false "" $_.Exception.Message
            }
        }
    }
}

function Test-FrontendIntegration {
    Write-Host "`n🏥 Testing Frontend Integration..." -ForegroundColor "Blue"
    
    $frontendPages = @(
        "/components/core/VitalCore-Production.html",
        "/components/core/MedBrain-Enhanced.html",
        "/components/core/HealthcareApp.html",
        "/api/vitalcore-client.js"
    )
    
    foreach ($page in $frontendPages) {
        try {
            $response = Invoke-WebRequest -Uri "$FrontendUrl$page" -TimeoutSec $Timeout -ErrorAction Stop
            Add-TestResult "Frontend: $page" ($response.StatusCode -eq 200) "Size: $($response.Content.Length) bytes"
        } catch {
            Add-TestResult "Frontend: $page" $false "" $_.Exception.Message
        }
    }
}

function Test-VoiceFeatures {
    Write-Host "`n🎤 Testing Voice Recognition Features..." -ForegroundColor "Blue"
    
    try {
        # Test VitalCore-Production.html for voice features
        $response = Invoke-WebRequest -Uri "$FrontendUrl/components/core/VitalCore-Production.html" -TimeoutSec $Timeout -ErrorAction Stop
        $content = $response.Content
        
        # Check for voice recognition code
        $hasVoiceRecognition = $content -match "SpeechRecognition|webkitSpeechRecognition"
        Add-TestResult "Voice Recognition Code" $hasVoiceRecognition "Found in VitalCore-Production.html"
        
        # Check for speech synthesis
        $hasSpeechSynthesis = $content -match "speechSynthesis|SpeechSynthesisUtterance"
        Add-TestResult "Speech Synthesis Code" $hasSpeechSynthesis "Found in VitalCore-Production.html"
        
        # Check for specialist selection
        $hasSpecialistSelection = $content -match "specialists\[|selectedSpecialist"
        Add-TestResult "Specialist Selection Code" $hasSpecialistSelection "Found in VitalCore-Production.html"
        
        # Check for microphone button
        $hasMicrophoneButton = $content -match "toggleVoiceInput|microphone|fa-microphone"
        Add-TestResult "Microphone Button Code" $hasMicrophoneButton "Found in VitalCore-Production.html"
        
    } catch {
        Add-TestResult "Voice Features Test" $false "" $_.Exception.Message
    }
}

function Test-DatabaseConnection {
    Write-Host "`n🗄️ Testing Database Connection..." -ForegroundColor "Blue"
    
    try {
        # Test database connection through API
        $response = Invoke-WebRequest -Uri "$BackendUrl/api/v1/system/database/status" -TimeoutSec $Timeout -ErrorAction Stop
        $dbStatus = $response.Content | ConvertFrom-Json
        Add-TestResult "Database Connection" ($response.StatusCode -eq 200) "Database accessible via API"
    } catch {
        # Try direct container check
        try {
            $dbCheck = docker-compose -f $ComposeFile exec -T db pg_isready -U postgres
            Add-TestResult "Database Connection" ($LASTEXITCODE -eq 0) "Direct container check"
        } catch {
            Add-TestResult "Database Connection" $false "" $_.Exception.Message
        }
    }
}

function Test-RedisConnection {
    Write-Host "`n🔴 Testing Redis Connection..." -ForegroundColor "Blue"
    
    try {
        $redisCheck = docker-compose -f $ComposeFile exec -T redis redis-cli ping
        $isConnected = $redisCheck -match "PONG"
        Add-TestResult "Redis Connection" $isConnected "Redis ping response: $redisCheck"
    } catch {
        Add-TestResult "Redis Connection" $false "" $_.Exception.Message
    }
}

function Show-TestSummary {
    Write-Host "`n📊 Test Summary" -ForegroundColor "Blue"
    Write-Host "===============" -ForegroundColor "Blue"
    
    $passedTests = ($TestResults | Where-Object { $_.Status -match "✅" }).Count
    $failedTests = ($TestResults | Where-Object { $_.Status -match "❌" }).Count
    $totalTests = $TestResults.Count
    
    Write-Host "Total Tests: $totalTests" -ForegroundColor "White"
    Write-Host "Passed: $passedTests" -ForegroundColor "Green"
    Write-Host "Failed: $failedTests" -ForegroundColor "Red"
    Write-Host "Success Rate: $([math]::Round(($passedTests / $totalTests) * 100, 1))%" -ForegroundColor "Yellow"
    
    if ($failedTests -gt 0) {
        Write-Host "`n❌ Failed Tests:" -ForegroundColor "Red"
        $TestResults | Where-Object { $_.Status -match "❌" } | ForEach-Object {
            Write-Host "  • $($_.Test): $($_.Error)" -ForegroundColor "Red"
        }
    }
    
    Write-Host "`n✅ Passed Tests:" -ForegroundColor "Green"
    $TestResults | Where-Object { $_.Status -match "✅" } | ForEach-Object {
        Write-Host "  • $($_.Test)" -ForegroundColor "Green"
    }
}

function Show-Recommendations {
    Write-Host "`n💡 Recommendations" -ForegroundColor "Yellow"
    Write-Host "==================" -ForegroundColor "Yellow"
    
    $failedTests = $TestResults | Where-Object { $_.Status -match "❌" }
    
    if ($failedTests.Count -eq 0) {
        Write-Host "🎉 All tests passed! Your Docker integration is working perfectly." -ForegroundColor "Green"
        Write-Host "🧪 Try testing the voice recognition by visiting:" -ForegroundColor "Blue"
        Write-Host "   $FrontendUrl/components/core/VitalCore-Production.html" -ForegroundColor "White"
    } else {
        Write-Host "🔧 To fix issues, try:" -ForegroundColor "Yellow"
        Write-Host "  1. .\Deploy-Frontend.ps1 restart" -ForegroundColor "White"
        Write-Host "  2. .\Deploy-Frontend.ps1 logs" -ForegroundColor "White"
        Write-Host "  3. .\Deploy-Frontend.ps1 cleanup" -ForegroundColor "White"
        Write-Host "  4. .\Deploy-Frontend.ps1 deploy" -ForegroundColor "White"
    }
}

# Main execution
Write-Host "🧪 VitalCore Docker Integration Test Suite" -ForegroundColor "Green"
Write-Host "==========================================" -ForegroundColor "Green"
Write-Host "Timeout: $Timeout seconds" -ForegroundColor "Gray"
Write-Host ""

try {
    if ($Quick -or (-not $API -and -not $Frontend -and -not $Voice -and -not $Detailed)) {
        Test-ServiceHealth
        Test-NetworkConnectivity
    }
    
    if ($API -or $Detailed) {
        Test-APIEndpoints
        Test-DatabaseConnection
        Test-RedisConnection
    }
    
    if ($Frontend -or $Detailed) {
        Test-FrontendIntegration
    }
    
    if ($Voice -or $Detailed) {
        Test-VoiceFeatures
    }
    
    if ($Detailed) {
        Test-ServiceHealth
        Test-NetworkConnectivity
        Test-APIEndpoints
        Test-FrontendIntegration
        Test-VoiceFeatures
        Test-DatabaseConnection
        Test-RedisConnection
    }
    
    Show-TestSummary
    Show-Recommendations
    
} catch {
    Write-Host "❌ Test execution failed: $($_.Exception.Message)" -ForegroundColor "Red"
    exit 1
}

Write-Host "`n🏁 Test suite completed" -ForegroundColor "Blue"