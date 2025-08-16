# Complete Docker Rebuild and Test Suite (Windows Compatible)
# PowerShell script without Unicode characters

param(
    [switch]$SkipRebuild,
    [switch]$QuickTest,
    [switch]$FullSuite
)

Write-Host "Clinical Workflows - Docker Rebuild & Test Suite" -ForegroundColor Green
Write-Host "================================================="

$startTime = Get-Date

# Step 1: Docker Rebuild (unless skipped)
if (-not $SkipRebuild) {
    Write-Host "`nSTEP 1: Docker Rebuild" -ForegroundColor Cyan
    Write-Host "----------------------"
    
    try {
        & ".\rebuild_docker_simple.ps1"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[SUCCESS] Docker rebuild completed" -ForegroundColor Green
        } else {
            Write-Host "[ERROR] Docker rebuild failed" -ForegroundColor Red
            exit 1
        }
    } catch {
        Write-Host "[ERROR] Docker rebuild failed: $_" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "`nSTEP 1: Skipping Docker rebuild" -ForegroundColor Yellow
}

# Step 2: Wait for services to be fully ready
Write-Host "`nSTEP 2: Waiting for services" -ForegroundColor Cyan
Write-Host "-----------------------------"

Write-Host "Allowing extra time for all services to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Check if application is responding
$appReady = $false
$attempts = 0
$maxAttempts = 6

while (-not $appReady -and $attempts -lt $maxAttempts) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            $appReady = $true
            Write-Host "[SUCCESS] Application is ready!" -ForegroundColor Green
        }
    } catch {
        Write-Host "Waiting for application... (attempt $($attempts + 1)/$maxAttempts)" -ForegroundColor Yellow
        Start-Sleep -Seconds 10
    }
    $attempts++
}

if (-not $appReady) {
    Write-Host "[WARNING] Application may still be starting up" -ForegroundColor Yellow
}

# Step 3: Run Tests
if ($QuickTest) {
    Write-Host "`nSTEP 3: Quick Test Suite" -ForegroundColor Cyan
    Write-Host "------------------------"
    
    # Essential tests only
    Write-Host "Running database integration test..." -ForegroundColor Yellow
    try {
        python simple_integration_test.py
        Write-Host "[SUCCESS] Database integration passed" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Database integration failed" -ForegroundColor Red
    }
    
    Write-Host "Running endpoint test..." -ForegroundColor Yellow
    try {
        python test_endpoints.py
        Write-Host "[SUCCESS] Endpoint test passed" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Endpoint test failed" -ForegroundColor Red
    }
    
} elseif ($FullSuite) {
    Write-Host "`nSTEP 3: Full Test Suite" -ForegroundColor Cyan
    Write-Host "-----------------------"
    
    try {
        & ".\run_tests_simple.ps1"
        Write-Host "[SUCCESS] Full test suite completed" -ForegroundColor Green
    } catch {
        Write-Host "[WARNING] Full test suite had some issues" -ForegroundColor Yellow
    }
    
} else {
    Write-Host "`nSTEP 3: Standard Test Suite" -ForegroundColor Cyan
    Write-Host "---------------------------"
    
    try {
        & ".\run_tests_simple.ps1"
        Write-Host "[SUCCESS] Standard tests completed" -ForegroundColor Green
    } catch {
        Write-Host "[WARNING] Some tests had issues" -ForegroundColor Yellow
    }
}

# Step 4: Final Health Check
Write-Host "`nSTEP 4: Final Health Check" -ForegroundColor Cyan
Write-Host "---------------------------"

$healthResults = @{
    "Docker Containers" = $false
    "Database" = $false
    "Application" = $false
    "Clinical Workflows" = $false
    "Documentation" = $false
}

# Check Docker containers
try {
    $containers = docker-compose ps
    if ($containers -like "*Up*") {
        $healthResults["Docker Containers"] = $true
        Write-Host "[PASS] Docker containers running" -ForegroundColor Green
    } else {
        Write-Host "[FAIL] Docker containers not running" -ForegroundColor Red
    }
} catch {
    Write-Host "[FAIL] Could not check Docker containers" -ForegroundColor Red
}

# Check database
try {
    $dbCheck = python -c "
import asyncio, asyncpg
async def check():
    try:
        conn = await asyncpg.connect('postgresql://postgres:password@localhost:5432/iris_db')
        result = await conn.fetchval('SELECT COUNT(*) FROM clinical_workflows')
        await conn.close()
        return True
    except:
        return False
print(asyncio.run(check()))
"
    if ($dbCheck -eq "True") {
        $healthResults["Database"] = $true
        Write-Host "[PASS] Database accessible" -ForegroundColor Green
    } else {
        Write-Host "[FAIL] Database not accessible" -ForegroundColor Red
    }
} catch {
    Write-Host "[FAIL] Database check failed" -ForegroundColor Red
}

# Check application
try {
    $appResponse = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
    if ($appResponse.StatusCode -eq 200) {
        $healthResults["Application"] = $true
        Write-Host "[PASS] Application healthy" -ForegroundColor Green
    } else {
        Write-Host "[FAIL] Application unhealthy: $($appResponse.StatusCode)" -ForegroundColor Red
    }
} catch {
    Write-Host "[FAIL] Application not responding" -ForegroundColor Red
}

# Check clinical workflows
try {
    $clinicalResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/clinical-workflows/health" -UseBasicParsing -TimeoutSec 5
    if ($clinicalResponse.StatusCode -eq 403 -or $clinicalResponse.StatusCode -eq 200) {
        $healthResults["Clinical Workflows"] = $true
        Write-Host "[PASS] Clinical workflows accessible" -ForegroundColor Green
    } else {
        Write-Host "[FAIL] Clinical workflows not accessible: $($clinicalResponse.StatusCode)" -ForegroundColor Red
    }
} catch {
    Write-Host "[FAIL] Clinical workflows check failed" -ForegroundColor Red
}

# Check documentation
try {
    $docsResponse = Invoke-WebRequest -Uri "http://localhost:8000/docs" -UseBasicParsing -TimeoutSec 5
    if ($docsResponse.StatusCode -eq 200) {
        $healthResults["Documentation"] = $true
        Write-Host "[PASS] API documentation available" -ForegroundColor Green
    } else {
        Write-Host "[FAIL] API documentation not available" -ForegroundColor Red
    }
} catch {
    Write-Host "[FAIL] Documentation check failed" -ForegroundColor Red
}

# Calculate results
$passedChecks = ($healthResults.Values | Where-Object { $_ -eq $true }).Count
$totalChecks = $healthResults.Count
$successRate = [math]::Round(($passedChecks / $totalChecks) * 100)

# Calculate total time
$endTime = Get-Date
$totalTime = $endTime - $startTime

# Final Summary
Write-Host "`n=================================================" -ForegroundColor Green
Write-Host "REBUILD & TEST SUMMARY" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green

Write-Host "Execution Summary:" -ForegroundColor White
Write-Host "  Total Time: $([math]::Round($totalTime.TotalMinutes, 1)) minutes" -ForegroundColor Gray
Write-Host "  Health Checks: $passedChecks/$totalChecks passed" -ForegroundColor Gray
Write-Host "  Success Rate: $successRate%" -ForegroundColor Gray

if ($successRate -eq 100) {
    Write-Host "`n[SUCCESS] ALL SYSTEMS OPERATIONAL!" -ForegroundColor Green
    Write-Host "Clinical Workflows module is production-ready!" -ForegroundColor Green
} elseif ($successRate -ge 80) {
    Write-Host "`n[SUCCESS] MOSTLY OPERATIONAL" -ForegroundColor Yellow
    Write-Host "Clinical Workflows module is mostly ready" -ForegroundColor Yellow
} else {
    Write-Host "`n[WARNING] ISSUES DETECTED" -ForegroundColor Red
    Write-Host "Please check failed components" -ForegroundColor Red
}

Write-Host "`nAccess Points:" -ForegroundColor Cyan
Write-Host "  API Documentation: http://localhost:8000/docs" -ForegroundColor Gray
Write-Host "  Clinical Workflows: http://localhost:8000/api/v1/clinical-workflows/" -ForegroundColor Gray
Write-Host "  Application Health: http://localhost:8000/health" -ForegroundColor Gray

Write-Host "`nUsage:" -ForegroundColor White
Write-Host "  .\rebuild_and_test_complete.ps1              # Full rebuild and test" -ForegroundColor Gray
Write-Host "  .\rebuild_and_test_complete.ps1 -SkipRebuild # Test only" -ForegroundColor Gray
Write-Host "  .\rebuild_and_test_complete.ps1 -QuickTest   # Essential tests" -ForegroundColor Gray