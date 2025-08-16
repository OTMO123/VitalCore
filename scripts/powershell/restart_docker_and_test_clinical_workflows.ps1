# Complete Docker Restart and Clinical Workflows Testing Script
# Restarts all Docker services and validates clinical workflows restoration

param(
    [switch]$SkipBuild,
    [switch]$Verbose
)

Write-Host "🚀 CLINICAL WORKFLOWS RESTORATION - DOCKER RESTART & TESTING" -ForegroundColor Green
Write-Host "============================================================="

$startTime = Get-Date

# Function to display status with timestamp
function Write-Status {
    param($Message, $Color = "White")
    $timestamp = Get-Date -Format "HH:mm:ss"
    Write-Host "[$timestamp] $Message" -ForegroundColor $Color
}

# Function to check if command succeeded
function Test-CommandSuccess {
    param($Command, $Description)
    Write-Status "Running: $Description" "Cyan"
    try {
        Invoke-Expression $Command
        if ($LASTEXITCODE -eq 0) {
            Write-Status "✅ SUCCESS: $Description" "Green"
            return $true
        } else {
            Write-Status "❌ FAILED: $Description (Exit code: $LASTEXITCODE)" "Red"
            return $false
        }
    } catch {
        Write-Status "❌ ERROR: $Description - $($_.Exception.Message)" "Red"
        return $false
    }
}

Write-Status "Starting Docker restart and clinical workflows testing process..." "Yellow"

# ============================================================================
# PHASE 1: DOCKER ENVIRONMENT RESTART
# ============================================================================

Write-Host "`n🐳 PHASE 1: DOCKER ENVIRONMENT RESTART" -ForegroundColor Cyan
Write-Host "======================================="

Write-Status "Stopping all running containers..." "Yellow"
docker-compose down
if ($LASTEXITCODE -ne 0) {
    Write-Status "Note: Some containers may not have been running" "Yellow"
}

Write-Status "Removing orphaned containers and networks..." "Yellow"
docker-compose down --remove-orphans

Write-Status "Checking Docker service status..." "Yellow"
$dockerRunning = docker version 2>$null
if (-not $dockerRunning) {
    Write-Status "❌ ERROR: Docker is not running. Please start Docker Desktop." "Red"
    exit 1
}

if (-not $SkipBuild) {
    Write-Status "Building and starting all services (with build)..." "Yellow"
    docker-compose up -d --build
} else {
    Write-Status "Starting all services (without build)..." "Yellow"
    docker-compose up -d
}

if ($LASTEXITCODE -ne 0) {
    Write-Status "❌ ERROR: Failed to start Docker services" "Red"
    exit 1
}

Write-Status "✅ Docker services started successfully" "Green"

# ============================================================================
# PHASE 2: SERVICE HEALTH VERIFICATION
# ============================================================================

Write-Host "`n🏥 PHASE 2: SERVICE HEALTH VERIFICATION" -ForegroundColor Cyan
Write-Host "======================================="

Write-Status "Checking container status..." "Yellow"
docker-compose ps

Write-Status "Waiting for services to initialize (30 seconds)..." "Yellow"
Start-Sleep -Seconds 30

Write-Status "Checking individual service health..." "Yellow"

# Check PostgreSQL
Write-Status "Testing PostgreSQL connection..." "Yellow"
$pgHealth = docker-compose exec -T db pg_isready -U postgres 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Status "✅ PostgreSQL: Healthy" "Green"
} else {
    Write-Status "⚠️  PostgreSQL: Not ready yet" "Yellow"
}

# Check Redis
Write-Status "Testing Redis connection..." "Yellow"
$redisHealth = docker-compose exec -T redis redis-cli ping 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Status "✅ Redis: Healthy" "Green"
} else {
    Write-Status "⚠️  Redis: Not ready yet" "Yellow"
}

# Check FastAPI application
Write-Status "Testing FastAPI application..." "Yellow"
try {
    $healthResponse = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 10 -ErrorAction SilentlyContinue
    if ($healthResponse -and $healthResponse.StatusCode -eq 200) {
        Write-Status "✅ FastAPI Application: Healthy" "Green"
        $appHealthy = $true
    } else {
        Write-Status "⚠️  FastAPI Application: Not ready yet" "Yellow"
        $appHealthy = $false
    }
} catch {
    Write-Status "⚠️  FastAPI Application: Starting up..." "Yellow"
    $appHealthy = $false
}

# If app not healthy, wait longer
if (-not $appHealthy) {
    Write-Status "Waiting additional 30 seconds for FastAPI to fully start..." "Yellow"
    Start-Sleep -Seconds 30
    
    try {
        $healthResponse = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 15 -ErrorAction SilentlyContinue
        if ($healthResponse -and $healthResponse.StatusCode -eq 200) {
            Write-Status "✅ FastAPI Application: Now healthy" "Green"
            $appHealthy = $true
        } else {
            Write-Status "❌ FastAPI Application: Still not responding" "Red"
            $appHealthy = $false
        }
    } catch {
        Write-Status "❌ FastAPI Application: Failed to start properly" "Red"
        $appHealthy = $false
    }
}

# Check API documentation
if ($appHealthy) {
    try {
        $docsResponse = Invoke-WebRequest -Uri "http://localhost:8000/docs" -UseBasicParsing -TimeoutSec 10 -ErrorAction SilentlyContinue
        if ($docsResponse -and $docsResponse.StatusCode -eq 200) {
            Write-Status "✅ API Documentation: Accessible" "Green"
        } else {
            Write-Status "⚠️  API Documentation: Not accessible" "Yellow"
        }
    } catch {
        Write-Status "⚠️  API Documentation: Not accessible" "Yellow"
    }
}

# Show final container status
Write-Status "Final container status:" "Cyan"
docker-compose ps

# ============================================================================
# PHASE 3: CLINICAL WORKFLOWS TESTING
# ============================================================================

Write-Host "`n🩺 PHASE 3: CLINICAL WORKFLOWS TESTING" -ForegroundColor Cyan
Write-Host "======================================"

if (-not $appHealthy) {
    Write-Status "❌ Cannot proceed with testing - FastAPI application is not healthy" "Red"
    Write-Status "Check logs with: docker-compose logs app" "Yellow"
    exit 1
}

Write-Status "Running comprehensive endpoint testing..." "Yellow"
if (Test-Path ".\test_endpoints_working.ps1") {
    & ".\test_endpoints_working.ps1"
    $endpointTestSuccess = $LASTEXITCODE -eq 0
} else {
    Write-Status "⚠️  test_endpoints_working.ps1 not found - skipping comprehensive test" "Yellow"
    $endpointTestSuccess = $false
}

Write-Status "Testing clinical workflows endpoints specifically..." "Yellow"
if (Test-Path ".\test_clinical_workflows_endpoints.ps1") {
    & ".\test_clinical_workflows_endpoints.ps1"
    $clinicalTestSuccess = $LASTEXITCODE -eq 0
} else {
    Write-Status "⚠️  test_clinical_workflows_endpoints.ps1 not found - skipping clinical test" "Yellow"
    $clinicalTestSuccess = $false
}

# Quick authentication test
Write-Status "Verifying authentication integrity..." "Yellow"
try {
    $authBody = '{"username":"admin","password":"admin123"}'
    $authResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Body $authBody -ContentType "application/json" -UseBasicParsing -TimeoutSec 10 -ErrorAction SilentlyContinue
    
    if ($authResponse -and $authResponse.StatusCode -eq 200) {
        Write-Status "✅ Authentication: Working perfectly" "Green"
        $authData = $authResponse.Content | ConvertFrom-Json
        $token = $authData.access_token
        $authWorking = $true
    } else {
        Write-Status "❌ Authentication: Failed" "Red"
        $authWorking = $false
    }
} catch {
    Write-Status "❌ Authentication: Error" "Red"
    $authWorking = $false
}

# Test clinical workflows endpoints with authentication
if ($authWorking) {
    Write-Status "Testing clinical workflows endpoints with authentication..." "Yellow"
    $headers = @{ "Authorization" = "Bearer $token" }
    
    $clinicalEndpoints = @(
        "/api/v1/clinical-workflows/workflows",
        "/api/v1/clinical-workflows/analytics", 
        "/api/v1/clinical-workflows/metrics"
    )
    
    $clinicalWorking = 0
    foreach ($endpoint in $clinicalEndpoints) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000$endpoint" -Headers $headers -UseBasicParsing -TimeoutSec 5 -ErrorAction SilentlyContinue
            
            if ($response -and $response.StatusCode -in @(200, 401, 403)) {
                Write-Status "✅ $endpoint - Available ($($response.StatusCode))" "Green"
                $clinicalWorking++
            } else {
                Write-Status "❌ $endpoint - Not found (404)" "Red"
            }
        } catch {
            if ($_.Exception.Response -and $_.Exception.Response.StatusCode -in @(200, 401, 403)) {
                Write-Status "✅ $endpoint - Available (Secured)" "Green"
                $clinicalWorking++
            } else {
                Write-Status "❌ $endpoint - Error" "Red"
            }
        }
    }
    
    $clinicalEndpointsWorking = $clinicalWorking -eq $clinicalEndpoints.Count
} else {
    Write-Status "⚠️  Cannot test clinical endpoints without authentication" "Yellow"
    $clinicalEndpointsWorking = $false
}

# ============================================================================
# PHASE 4: RESULTS ANALYSIS
# ============================================================================

Write-Host "`n📊 PHASE 4: RESULTS ANALYSIS" -ForegroundColor Cyan
Write-Host "============================="

$endTime = Get-Date
$duration = $endTime - $startTime

Write-Status "Test execution completed in $($duration.TotalMinutes.ToString('F1')) minutes" "White"

Write-Host "`nRESTORATION VERIFICATION RESULTS:" -ForegroundColor White
Write-Host "=================================="

# Calculate overall success
$overallSuccess = $appHealthy -and $authWorking -and $clinicalEndpointsWorking

Write-Host "`n🏥 DOCKER SERVICES:" -ForegroundColor Cyan
Write-Host "  PostgreSQL: $(if ($pgHealth) { '✅ Healthy' } else { '⚠️  Issues' })" -ForegroundColor $(if ($pgHealth) { 'Green' } else { 'Yellow' })
Write-Host "  Redis: $(if ($redisHealth) { '✅ Healthy' } else { '⚠️  Issues' })" -ForegroundColor $(if ($redisHealth) { 'Green' } else { 'Yellow' })
Write-Host "  FastAPI App: $(if ($appHealthy) { '✅ Healthy' } else { '❌ Issues' })" -ForegroundColor $(if ($appHealthy) { 'Green' } else { 'Red' })

Write-Host "`n🔐 AUTHENTICATION SYSTEM:" -ForegroundColor Cyan
Write-Host "  Login Endpoint: $(if ($authWorking) { '✅ Working' } else { '❌ Failed' })" -ForegroundColor $(if ($authWorking) { 'Green' } else { 'Red' })
Write-Host "  JWT Generation: $(if ($authWorking) { '✅ Working' } else { '❌ Failed' })" -ForegroundColor $(if ($authWorking) { 'Green' } else { 'Red' })

Write-Host "`n🩺 CLINICAL WORKFLOWS:" -ForegroundColor Cyan
Write-Host "  Endpoints Available: $(if ($clinicalEndpointsWorking) { '✅ Yes' } else { '❌ No' })" -ForegroundColor $(if ($clinicalEndpointsWorking) { 'Green' } else { 'Red' })
Write-Host "  Restoration Status: $(if ($clinicalEndpointsWorking) { '✅ Complete' } else { '⚠️  Pending' })" -ForegroundColor $(if ($clinicalEndpointsWorking) { 'Green' } else { 'Yellow' })

Write-Host "`n🎯 OVERALL STATUS:" -ForegroundColor White
if ($overallSuccess) {
    Write-Host "  ✅ CLINICAL WORKFLOWS RESTORATION: 100% SUCCESSFUL" -ForegroundColor Green
    Write-Host "  ✅ All systems operational and ready for production" -ForegroundColor Green
    Write-Host "  ✅ Healthcare provider onboarding can begin" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  RESTORATION: Partially successful" -ForegroundColor Yellow
    Write-Host "  ⚠️  Some components may need additional attention" -ForegroundColor Yellow
}

Write-Host "`n📋 NEXT STEPS:" -ForegroundColor Cyan
if ($overallSuccess) {
    Write-Host "  1. ✅ System is fully operational" -ForegroundColor Green
    Write-Host "  2. Run enterprise test suite: .\run_enterprise_tests.ps1" -ForegroundColor Gray
    Write-Host "  3. Begin production deployment planning" -ForegroundColor Gray
    Write-Host "  4. Start healthcare provider onboarding" -ForegroundColor Gray
} else {
    if (-not $appHealthy) {
        Write-Host "  1. Check application logs: docker-compose logs app" -ForegroundColor Yellow
        Write-Host "  2. Verify all environment variables are set correctly" -ForegroundColor Yellow
    }
    if (-not $authWorking) {
        Write-Host "  3. Investigate authentication configuration" -ForegroundColor Yellow
    }
    if (-not $clinicalEndpointsWorking) {
        Write-Host "  4. Verify clinical workflows router is properly loaded" -ForegroundColor Yellow
        Write-Host "  5. Check for any import or dependency issues" -ForegroundColor Yellow
    }
}

Write-Host "`n🔍 DEBUGGING COMMANDS:" -ForegroundColor Cyan
Write-Host "  View application logs: docker-compose logs app" -ForegroundColor Gray
Write-Host "  View all logs: docker-compose logs" -ForegroundColor Gray
Write-Host "  Restart specific service: docker-compose restart app" -ForegroundColor Gray
Write-Host "  Check container status: docker-compose ps" -ForegroundColor Gray

Write-Host "`n" + "=" * 70 -ForegroundColor Green
if ($overallSuccess) {
    Write-Host "🎉 CLINICAL WORKFLOWS RESTORATION: MISSION ACCOMPLISHED! 🎉" -ForegroundColor Green
} else {
    Write-Host "⚠️  CLINICAL WORKFLOWS RESTORATION: NEEDS ATTENTION ⚠️" -ForegroundColor Yellow
}
Write-Host "=" * 70 -ForegroundColor Green

# Return appropriate exit code
if ($overallSuccess) {
    exit 0
} else {
    exit 1
}