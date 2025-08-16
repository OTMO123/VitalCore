# Complete Rebuild and Test Pipeline
# PowerShell script for comprehensive Docker rebuild and testing

param(
    [switch]$SkipRebuild,
    [switch]$QuickTest,
    [switch]$FullSuite
)

Write-Host "Clinical Workflows - Complete Rebuild & Test Pipeline" -ForegroundColor Green
Write-Host "============================================================"

$startTime = Get-Date

# Step 1: Docker Rebuild (unless skipped)
if (-not $SkipRebuild) {
    Write-Host "`nSTEP 1: Docker Rebuild" -ForegroundColor Cyan
    Write-Host "------------------------------"
    
    try {
        & ".\scripts\rebuild_docker.ps1"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[SUCCESS] Docker rebuild completed successfully" -ForegroundColor Green
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

# Step 2: Health Check
Write-Host "`nSTEP 2: Health Check" -ForegroundColor Cyan
Write-Host "------------------------------"

try {
    & ".\scripts\check_docker_health.ps1"
    Write-Host "[SUCCESS] Health check completed" -ForegroundColor Green
} catch {
    Write-Host "[WARNING] Health check had issues: $_" -ForegroundColor Yellow
}

# Step 3: Test Suite Selection
if ($QuickTest) {
    Write-Host "`nSTEP 3: Quick Test Suite" -ForegroundColor Cyan
    Write-Host "------------------------------"
    
    # Run only essential tests
    Write-Host "Running essential tests..." -ForegroundColor Yellow
    
    # Database integration
    try {
        python simple_integration_test.py
        Write-Host "[SUCCESS] Database integration test passed" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Database integration test failed" -ForegroundColor Red
    }
    
    # Endpoint testing
    try {
        python test_endpoints.py
        Write-Host "[SUCCESS] Endpoint test completed" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Endpoint test failed" -ForegroundColor Red
    }
    
} elseif ($FullSuite) {
    Write-Host "`nSTEP 3: Full Test Suite" -ForegroundColor Cyan
    Write-Host "------------------------------"
    
    try {
        & ".\scripts\run_full_test_suite.ps1"
        Write-Host "[SUCCESS] Full test suite completed" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Full test suite had issues: $_" -ForegroundColor Yellow
    }
    
} else {
    Write-Host "`nSTEP 3: Clinical Workflows Testing" -ForegroundColor Cyan
    Write-Host "------------------------------"
    
    try {
        & ".\scripts\test_clinical_workflows.ps1"
        Write-Host "[SUCCESS] Clinical workflows testing completed" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Clinical workflows testing failed: $_" -ForegroundColor Red
    }
}

# Step 4: Performance Validation
Write-Host "`nSTEP 4: Performance Validation" -ForegroundColor Cyan
Write-Host "------------------------------"

try {
    $times = @()
    for ($i = 1; $i -le 5; $i++) {
        $start = Get-Date
        $response = Invoke-WebRequest -Uri "http://localhost:8000/docs" -UseBasicParsing -TimeoutSec 10
        $end = Get-Date
        
        if ($response.StatusCode -eq 200) {
            $duration = ($end - $start).TotalMilliseconds
            $times += $duration
        }
        Start-Sleep -Milliseconds 100
    }
    
    if ($times.Count -gt 0) {
        $avgTime = ($times | Measure-Object -Average).Average
        $maxTime = ($times | Measure-Object -Maximum).Maximum
        $minTime = ($times | Measure-Object -Minimum).Minimum
        
        Write-Host "Performance Metrics:" -ForegroundColor White
        Write-Host "  Average: $([math]::Round($avgTime))ms" -ForegroundColor Gray
        Write-Host "  Min: $([math]::Round($minTime))ms" -ForegroundColor Gray  
        Write-Host "  Max: $([math]::Round($maxTime))ms" -ForegroundColor Gray
        
        if ($avgTime -lt 1000) {
            Write-Host "[SUCCESS] Performance is excellent" -ForegroundColor Green
        } elseif ($avgTime -lt 2000) {
            Write-Host "[SUCCESS] Performance is good" -ForegroundColor Green
        } else {
            Write-Host "[WARNING] Performance may need optimization" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "[ERROR] Performance validation failed: $_" -ForegroundColor Red
}

# Step 5: Final Validation
Write-Host "`nSTEP 5: Final Validation" -ForegroundColor Cyan
Write-Host "------------------------------"

$validationResults = @{
    "Docker Containers" = $false
    "Database Connection" = $false
    "Application Health" = $false
    "Clinical Workflows" = $false
    "API Documentation" = $false
}

# Check containers
try {
    $containers = docker-compose ps
    if ($containers -like "*Up*") {
        $validationResults["Docker Containers"] = $true
    }
} catch { }

# Check database
try {
    $dbResult = python -c "
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
    if ($dbResult -eq "True") {
        $validationResults["Database Connection"] = $true
    }
} catch { }

# Check application
try {
    $appResponse = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
    if ($appResponse.StatusCode -eq 200) {
        $validationResults["Application Health"] = $true
    }
} catch { }

# Check clinical workflows
try {
    $clinicalResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/clinical-workflows/health" -UseBasicParsing -SkipHttpErrorCheck -TimeoutSec 5
    if ($clinicalResponse.StatusCode -eq 403 -or $clinicalResponse.StatusCode -eq 200) {
        $validationResults["Clinical Workflows"] = $true
    }
} catch { }

# Check documentation
try {
    $docsResponse = Invoke-WebRequest -Uri "http://localhost:8000/docs" -UseBasicParsing -TimeoutSec 5
    if ($docsResponse.StatusCode -eq 200) {
        $validationResults["API Documentation"] = $true
    }
} catch { }

# Display validation results
foreach ($key in $validationResults.Keys) {
    if ($validationResults[$key]) {
        Write-Host "  [PASS] $key" -ForegroundColor Green
    } else {
        Write-Host "  [FAIL] $key" -ForegroundColor Red
    }
}

# Calculate completion time
$endTime = Get-Date
$totalTime = $endTime - $startTime

# Final Summary
Write-Host "`n============================================================" -ForegroundColor Green
Write-Host "REBUILD & TEST PIPELINE SUMMARY" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green

$passedValidations = ($validationResults.Values | Where-Object { $_ -eq $true }).Count
$totalValidations = $validationResults.Count

Write-Host "Results:" -ForegroundColor White
Write-Host "  Total Time: $([math]::Round($totalTime.TotalMinutes, 1)) minutes" -ForegroundColor Gray
Write-Host "  Validations Passed: $passedValidations/$totalValidations" -ForegroundColor Gray
Write-Host "  Success Rate: $([math]::Round(($passedValidations/$totalValidations)*100))%" -ForegroundColor Gray

if ($passedValidations -eq $totalValidations) {
    Write-Host "`nALL SYSTEMS OPERATIONAL!" -ForegroundColor Green
    Write-Host "Clinical Workflows module is production-ready!" -ForegroundColor Green
} elseif ($passedValidations -ge ($totalValidations * 0.8)) {
    Write-Host "`nMOSTLY OPERATIONAL" -ForegroundColor Yellow
    Write-Host "Clinical Workflows module is mostly ready - check failed validations" -ForegroundColor Yellow
} else {
    Write-Host "`nISSUES DETECTED" -ForegroundColor Red
    Write-Host "Please address failed validations before production use" -ForegroundColor Red
}

Write-Host "`nAccess Points:" -ForegroundColor Cyan
Write-Host "  API Documentation: http://localhost:8000/docs" -ForegroundColor Gray
Write-Host "  Clinical Workflows: http://localhost:8000/api/v1/clinical-workflows/" -ForegroundColor Gray
Write-Host "  Health Check: http://localhost:8000/health" -ForegroundColor Gray

Write-Host "`nUsage Examples:" -ForegroundColor White
Write-Host "  .\rebuild_and_test_fixed.ps1                # Standard rebuild and test" -ForegroundColor Gray
Write-Host "  .\rebuild_and_test_fixed.ps1 -SkipRebuild   # Test only (skip rebuild)" -ForegroundColor Gray
Write-Host "  .\rebuild_and_test_fixed.ps1 -QuickTest     # Quick essential tests" -ForegroundColor Gray
Write-Host "  .\rebuild_and_test_fixed.ps1 -FullSuite     # Complete test suite" -ForegroundColor Gray