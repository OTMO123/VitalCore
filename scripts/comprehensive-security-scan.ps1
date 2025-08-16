#!/usr/bin/env pwsh

<#
.SYNOPSIS
    Comprehensive Security Scanner for Router Files
.DESCRIPTION
    Scans all router.py files in the system for security violations including:
    - Direct database imports
    - Direct SQL queries
    - Direct database executions
    - Missing service layer usage
.AUTHOR
    Claude Code Security Team
.DATE
    2025-07-20
#>

param(
    [switch]$Verbose,
    [switch]$ExportJson,
    [string]$OutputPath = "security_scan_results.json"
)

# Set strict mode for better error handling
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Color functions for better output
function Write-ColoredOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Write-Success { param([string]$Message) Write-ColoredOutput $Message "Green" }
function Write-Warning { param([string]$Message) Write-ColoredOutput $Message "Yellow" }
function Write-Error { param([string]$Message) Write-ColoredOutput $Message "Red" }
function Write-Info { param([string]$Message) Write-ColoredOutput $Message "Cyan" }

# Initialize results structure
$ScanResults = @{
    StartTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    TotalFiles = 0
    CleanFiles = 0
    ViolatingFiles = 0
    TotalViolations = 0
    FileResults = @()
    Summary = @{}
}

# Define router files to scan
$RouterFiles = @(
    "app/modules/analytics/router.py",
    "app/modules/audit_logger/router.py",
    "app/modules/audit_logger/security_router.py",
    "app/modules/auth/router.py",
    "app/modules/dashboard/router.py",
    "app/modules/document_management/router.py",
    "app/modules/healthcare_records/router.py",
    "app/modules/iris_api/router.py",
    "app/modules/purge_scheduler/router.py",
    "app/modules/risk_stratification/router.py",
    "app/modules/security_audit/router.py"
)

# Security violation patterns to check
$SecurityPatterns = @{
    "DirectDatabaseImport" = @{
        Pattern = "from app\.core\.database_unified import.*(?:Session|Engine|create_session|get_session)"
        Description = "Direct database session/engine imports"
        Severity = "HIGH"
    }
    "DirectSQLQuery" = @{
        Pattern = "select\([^)]*\)\.where\("
        Description = "Direct SQL query construction"
        Severity = "HIGH"
    }
    "DirectDatabaseExecution" = @{
        Pattern = "await\s+db\.(execute|scalar|fetch|commit)"
        Description = "Direct database execution"
        Severity = "HIGH"
    }
    "DirectORMQuery" = @{
        Pattern = "db\.query\("
        Description = "Direct ORM query usage"
        Severity = "HIGH"
    }
    "DatabaseDependencyInjection" = @{
        Pattern = "db:\s*AsyncSession\s*=\s*Depends\(get_db\)"
        Description = "Database dependency injection in router (should use service layer)"
        Severity = "MEDIUM"
    }
    "DirectModelImport" = @{
        Pattern = "from app\.core\.database_unified import.*(?:User|Patient|AuditLog|Document)"
        Description = "Direct model imports in router"
        Severity = "MEDIUM"
    }
    "SessionDirectAccess" = @{
        Pattern = "session\.(add|merge|delete|flush|commit|rollback)"
        Description = "Direct session manipulation"
        Severity = "HIGH"
    }
}

# Service layer patterns (good practices)
$ServicePatterns = @{
    "ServiceImport" = "from app\.modules\.[^.]+\.service import"
    "ServiceUsage" = "\w+_service\.\w+"
    "ServiceDependency" = "service.*=.*Depends\("
}

Write-Info "=== COMPREHENSIVE ROUTER SECURITY SCANNER ==="
Write-Info "Scanning router files for security violations..."
Write-Info "Target files: $($RouterFiles.Count)"
Write-Info ""

$ScanResults.TotalFiles = $RouterFiles.Count

foreach ($RouterFile in $RouterFiles) {
    $FullPath = Join-Path $PWD $RouterFile
    
    Write-Info "Scanning: $RouterFile"
    
    # Initialize file result
    $FileResult = @{
        FilePath = $RouterFile
        Exists = $false
        Violations = @()
        ServiceLayerUsage = @()
        IsClean = $false
        ViolationCount = 0
    }
    
    # Check if file exists
    if (-not (Test-Path $FullPath)) {
        Write-Warning "  ⚠️  File not found: $RouterFile"
        $FileResult.Exists = $false
        $ScanResults.FileResults += $FileResult
        continue
    }
    
    $FileResult.Exists = $true
    
    try {
        # Read file content
        $Content = Get-Content $FullPath -Raw -ErrorAction Stop
        
        # Check for security violations
        foreach ($PatternName in $SecurityPatterns.Keys) {
            $Pattern = $SecurityPatterns[$PatternName]
            $Matches = [regex]::Matches($Content, $Pattern.Pattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
            
            foreach ($Match in $Matches) {
                $LineNumber = ($Content.Substring(0, $Match.Index) -split "`n").Count
                
                $Violation = @{
                    Type = $PatternName
                    Description = $Pattern.Description
                    Severity = $Pattern.Severity
                    LineNumber = $LineNumber
                    MatchedText = $Match.Value.Trim()
                }
                
                $FileResult.Violations += $Violation
                $FileResult.ViolationCount++
                $ScanResults.TotalViolations++
                
                if ($Verbose) {
                    $SeverityColor = switch ($Pattern.Severity) {
                        "HIGH" { "Red" }
                        "MEDIUM" { "Yellow" }
                        "LOW" { "Cyan" }
                        default { "White" }
                    }
                    Write-ColoredOutput "    ❌ [$($Pattern.Severity)] Line $LineNumber: $($Pattern.Description)" $SeverityColor
                    Write-ColoredOutput "       Code: $($Match.Value.Trim())" "Gray"
                }
            }
        }
        
        # Check for service layer usage (good practices)
        foreach ($PatternName in $ServicePatterns.Keys) {
            $Pattern = $ServicePatterns[$PatternName]
            $Matches = [regex]::Matches($Content, $Pattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
            
            foreach ($Match in $Matches) {
                $LineNumber = ($Content.Substring(0, $Match.Index) -split "`n").Count
                
                $ServiceUsage = @{
                    Type = $PatternName
                    LineNumber = $LineNumber
                    MatchedText = $Match.Value.Trim()
                }
                
                $FileResult.ServiceLayerUsage += $ServiceUsage
                
                if ($Verbose) {
                    Write-Success "    ✅ Line $LineNumber: Service layer usage - $($Match.Value.Trim())"
                }
            }
        }
        
        # Determine if file is clean
        $FileResult.IsClean = ($FileResult.ViolationCount -eq 0)
        
        if ($FileResult.IsClean) {
            $ScanResults.CleanFiles++
            Write-Success "  ✅ CLEAN - No security violations found"
        } else {
            $ScanResults.ViolatingFiles++
            Write-Error "  ❌ VIOLATIONS FOUND - $($FileResult.ViolationCount) security violations"
        }
        
        # Show service layer usage summary
        if ($FileResult.ServiceLayerUsage.Count -gt 0) {
            Write-Success "  📋 Service layer usage: $($FileResult.ServiceLayerUsage.Count) instances"
        } elseif ($FileResult.IsClean) {
            Write-Warning "  ⚠️  No service layer usage detected (may need review)"
        }
        
    } catch {
        Write-Error "  💥 Error reading file: $($_.Exception.Message)"
        $FileResult.Error = $_.Exception.Message
    }
    
    $ScanResults.FileResults += $FileResult
    Write-Info ""
}

# Generate summary
Write-Info "=== SECURITY SCAN SUMMARY ==="
Write-Info "Scan completed at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Info ""

Write-Info "📊 OVERALL STATISTICS:"
Write-Info "  Total files scanned: $($ScanResults.TotalFiles)"
Write-Success "  Clean files: $($ScanResults.CleanFiles)"
Write-Error "  Files with violations: $($ScanResults.ViolatingFiles)"
Write-Error "  Total violations: $($ScanResults.TotalViolations)"
Write-Info ""

# Files status breakdown
Write-Info "📁 FILE STATUS BREAKDOWN:"
foreach ($FileResult in $ScanResults.FileResults) {
    $Status = if (-not $FileResult.Exists) { "❓ NOT FOUND" } 
              elseif ($FileResult.IsClean) { "✅ CLEAN" } 
              else { "❌ VIOLATIONS ($($FileResult.ViolationCount))" }
    
    $StatusColor = if (-not $FileResult.Exists) { "Gray" } 
                   elseif ($FileResult.IsClean) { "Green" } 
                   else { "Red" }
    
    Write-ColoredOutput "  $($FileResult.FilePath): $Status" $StatusColor
}
Write-Info ""

# Violation type breakdown
if ($ScanResults.TotalViolations -gt 0) {
    Write-Info "🔍 VIOLATION TYPE BREAKDOWN:"
    $ViolationTypes = @{}
    foreach ($FileResult in $ScanResults.FileResults) {
        foreach ($Violation in $FileResult.Violations) {
            if ($ViolationTypes.ContainsKey($Violation.Type)) {
                $ViolationTypes[$Violation.Type]++
            } else {
                $ViolationTypes[$Violation.Type] = 1
            }
        }
    }
    
    foreach ($ViolationType in $ViolationTypes.Keys | Sort-Object) {
        $Count = $ViolationTypes[$ViolationType]
        $Description = $SecurityPatterns[$ViolationType].Description
        $Severity = $SecurityPatterns[$ViolationType].Severity
        
        $SeverityColor = switch ($Severity) {
            "HIGH" { "Red" }
            "MEDIUM" { "Yellow" }
            "LOW" { "Cyan" }
            default { "White" }
        }
        
        Write-ColoredOutput "  [$Severity] $ViolationType ($Count): $Description" $SeverityColor
    }
    Write-Info ""
}

# Detailed violations by file
if ($ScanResults.ViolatingFiles -gt 0 -and $Verbose) {
    Write-Info "📝 DETAILED VIOLATIONS BY FILE:"
    foreach ($FileResult in $ScanResults.FileResults | Where-Object { $_.ViolationCount -gt 0 }) {
        Write-Error "  📄 $($FileResult.FilePath) ($($FileResult.ViolationCount) violations):"
        foreach ($Violation in $FileResult.Violations) {
            $SeverityColor = switch ($Violation.Severity) {
                "HIGH" { "Red" }
                "MEDIUM" { "Yellow" }
                "LOW" { "Cyan" }
                default { "White" }
            }
            Write-ColoredOutput "    ❌ Line $($Violation.LineNumber): [$($Violation.Severity)] $($Violation.Description)" $SeverityColor
            Write-ColoredOutput "       Code: $($Violation.MatchedText)" "Gray"
        }
        Write-Info ""
    }
}

# Security score calculation
$SecurityScore = if ($ScanResults.TotalFiles -gt 0) {
    [math]::Round(($ScanResults.CleanFiles / $ScanResults.TotalFiles) * 100, 2)
} else { 0 }

Write-Info "🏆 SECURITY SCORE: $SecurityScore% ($($ScanResults.CleanFiles)/$($ScanResults.TotalFiles) files clean)"

if ($SecurityScore -eq 100) {
    Write-Success "🎉 EXCELLENT! All router files follow security best practices!"
} elseif ($SecurityScore -ge 80) {
    Write-Warning "⚠️  GOOD - Most files are secure, but some violations need attention."
} elseif ($SecurityScore -ge 60) {
    Write-Error "🚨 MODERATE - Significant security violations found. Review required."
} else {
    Write-Error "💥 CRITICAL - Major security violations detected. Immediate action required!"
}

# High-level violation statistics
$HighViolations = 0
$MediumViolations = 0
foreach ($FileResult in $ScanResults.FileResults) {
    foreach ($Violation in $FileResult.Violations) {
        if ($Violation.Severity -eq "HIGH") { $HighViolations++ }
        elseif ($Violation.Severity -eq "MEDIUM") { $MediumViolations++ }
    }
}

Write-Info ""
Write-Info "🔍 VIOLATION SEVERITY BREAKDOWN:"
Write-Error "  HIGH severity violations: $HighViolations"
Write-Warning "  MEDIUM severity violations: $MediumViolations"

# Add summary to results
$ScanResults.Summary = @{
    SecurityScore = $SecurityScore
    CompletionTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Status = if ($SecurityScore -eq 100) { "EXCELLENT" }
             elseif ($SecurityScore -ge 80) { "GOOD" }
             elseif ($SecurityScore -ge 60) { "MODERATE" }
             else { "CRITICAL" }
}

# Export to JSON if requested
if ($ExportJson) {
    try {
        $JsonOutput = $ScanResults | ConvertTo-Json -Depth 10
        $JsonOutput | Out-File -FilePath $OutputPath -Encoding UTF8
        Write-Success "📄 Results exported to: $OutputPath"
    } catch {
        Write-Error "❌ Failed to export JSON: $($_.Exception.Message)"
    }
}

Write-Info ""
Write-Info "=== RECOMMENDATIONS ==="
if ($ScanResults.ViolatingFiles -gt 0) {
    Write-Info "🔧 TO FIX VIOLATIONS:"
    Write-Info "1. Move database logic from routers to service layers"
    Write-Info "2. Use dependency injection for services, not database sessions"
    Write-Info "3. Remove direct SQL queries and use service methods"
    Write-Info "4. Implement proper separation of concerns (Router → Service → Repository)"
    Write-Info "5. Follow the DDD bounded context patterns mentioned in CLAUDE.md"
    Write-Info ""
    Write-Info "🎯 EXAMPLE FIX PATTERN:"
    Write-Info "  BEFORE: db: AsyncSession = Depends(get_db)"
    Write-Info "  AFTER:  service = Depends(get_your_service)"
    Write-Info ""
    Write-Info "  BEFORE: await db.execute(select(Model).where(...))"
    Write-Info "  AFTER:  await service.get_records(...)"
    Write-Info ""
    Write-Info "📋 HIGHEST PRIORITY FILES TO FIX:"
    $SortedFiles = $ScanResults.FileResults | Where-Object { $_.ViolationCount -gt 0 } | Sort-Object ViolationCount -Descending | Select-Object -First 5
    foreach ($File in $SortedFiles) {
        Write-Error "  $($File.FilePath) - $($File.ViolationCount) violations"
    }
} else {
    Write-Success "🎯 All files are following security best practices!"
}

Write-Info ""
Write-Info "=== SECURITY SCAN COMPLETED ==="

# Exit with appropriate code
exit $(if ($ScanResults.ViolatingFiles -gt 0) { 1 } else { 0 })