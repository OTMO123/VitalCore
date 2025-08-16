# Healthcare API Security Architecture Checker
# Check endpoints use service layer instead of direct DB access

Write-Host "SECURITY ARCHITECTURE CHECK" -ForegroundColor Cyan
Write-Host "===============================" -ForegroundColor Cyan

$routerFile = "app/modules/healthcare_records/router.py"

if (-not (Test-Path $routerFile)) {
    Write-Host "ERROR: Router file not found: $routerFile" -ForegroundColor Red
    exit 1
}

Write-Host "Analyzing: $routerFile" -ForegroundColor Yellow
Write-Host ""

# 1. Check for direct database imports in routers
Write-Host "1. Checking for direct database imports..." -ForegroundColor Blue
$dbImports = Select-String -Path $routerFile -Pattern "from app\.core\.database_unified import" | Where-Object { $_.Line -notmatch "get_db" }

if ($dbImports) {
    Write-Host "ERROR: FOUND DIRECT DATABASE IMPORTS:" -ForegroundColor Red
    foreach ($import in $dbImports) {
        Write-Host "   Line $($import.LineNumber): $($import.Line.Trim())" -ForegroundColor Red
    }
} else {
    Write-Host "OK: No direct database imports found" -ForegroundColor Green
}

# 2. Check for direct SQL queries
Write-Host ""
Write-Host "2. Checking for direct SQL queries..." -ForegroundColor Blue
$sqlQueries = Select-String -Path $routerFile -Pattern "select\(.*Patient\)" -AllMatches

if ($sqlQueries) {
    Write-Host "ERROR: FOUND DIRECT SQL QUERIES:" -ForegroundColor Red
    foreach ($query in $sqlQueries) {
        Write-Host "   Line $($query.LineNumber): $($query.Line.Trim())" -ForegroundColor Red
    }
} else {
    Write-Host "OK: No direct SQL queries found" -ForegroundColor Green
}

# 3. Check for direct executions
Write-Host ""
Write-Host "3. Checking for direct database executions..." -ForegroundColor Blue
$dbExecutions = Select-String -Path $routerFile -Pattern "await db\.execute\("

if ($dbExecutions) {
    Write-Host "ERROR: FOUND DIRECT DATABASE EXECUTIONS:" -ForegroundColor Red
    foreach ($exec in $dbExecutions) {
        Write-Host "   Line $($exec.LineNumber): $($exec.Line.Trim())" -ForegroundColor Red
    }
} else {
    Write-Host "OK: No direct database executions found" -ForegroundColor Green
}

# 4. Check for proper service layer usage
Write-Host ""
Write-Host "4. Checking for proper service layer usage..." -ForegroundColor Blue
$serviceUsage = Select-String -Path $routerFile -Pattern "get_healthcare_service"

if ($serviceUsage) {
    Write-Host "OK: FOUND SERVICE LAYER USAGE:" -ForegroundColor Green
    Write-Host "   Found $($serviceUsage.Count) proper service layer calls" -ForegroundColor Green
} else {
    Write-Host "ERROR: No service layer usage found" -ForegroundColor Red
}

# Summary
Write-Host ""
Write-Host "SECURITY SUMMARY" -ForegroundColor Cyan
Write-Host "===================" -ForegroundColor Cyan

$violations = 0
if ($dbImports) { $violations += $dbImports.Count }
if ($sqlQueries) { $violations += $sqlQueries.Count }
if ($dbExecutions) { $violations += $dbExecutions.Count }

if ($violations -eq 0) {
    Write-Host "SUCCESS: SECURITY CHECK PASSED!" -ForegroundColor Green
    Write-Host "   All endpoints use proper service layer architecture" -ForegroundColor Green
} else {
    Write-Host "WARNING: SECURITY VIOLATIONS FOUND!" -ForegroundColor Red
    Write-Host "   Total violations: $violations" -ForegroundColor Red
    Write-Host "   Action required: Fix direct database access" -ForegroundColor Red
}

Write-Host ""
Write-Host "Architecture check completed" -ForegroundColor Cyan