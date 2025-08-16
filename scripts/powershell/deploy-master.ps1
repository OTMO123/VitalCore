# Master Deployment Orchestrator
# Comprehensive deployment strategy with service prioritization

param(
    [ValidateSet("Development", "Staging", "Production")]
    [string]$Environment = "Development",
    [ValidateSet("Phase1", "Phase2", "Phase3", "All", "Validate")]
    [string]$DeploymentPhase = "All",
    [switch]$GenerateSecrets,
    [switch]$SkipValidation,
    [switch]$ContinueOnFailure,
    [switch]$DryRun
)

Write-Host "🏥 Enterprise Healthcare Platform - Master Deployment" -ForegroundColor Green
Write-Host "====================================================" -ForegroundColor Green
Write-Host "Environment: $Environment | Phase: $DeploymentPhase" -ForegroundColor Cyan

# Deployment phases definition
$DeploymentPhases = @{
    "Phase1" = @{
        Name = "Foundation"
        Description = "Critical P0 services (PostgreSQL, Redis, Core App)"
        Services = @("postgres", "redis", "app", "minio", "prometheus")
        Priority = "CRITICAL"
        EstimatedTime = "5-10 minutes"
        Prerequisites = @("Environment variables", "Docker")
    }
    "Phase2" = @{
        Name = "AI/ML Capabilities" 
        Description = "Vector DB, DICOM, ML Models"
        Services = @("milvus", "orthanc", "tensorflow", "jupyter")
        Priority = "HIGH"
        EstimatedTime = "10-15 minutes"
        Prerequisites = @("Phase1 completed", "Additional 4GB RAM")
    }
    "Phase3" = @{
        Name = "Advanced Analytics"
        Description = "Grafana, Jaeger, ElasticSearch"
        Services = @("grafana", "jaeger", "elasticsearch", "kibana")
        Priority = "MEDIUM"
        EstimatedTime = "15-20 minutes"
        Prerequisites = @("Phase2 completed", "Additional 2GB RAM")
    }
}

# Show deployment plan
Write-Host "`n📋 Deployment Strategy Overview" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

foreach ($phase in $DeploymentPhases.Keys | Sort-Object) {
    $info = $DeploymentPhases[$phase]
    $indicator = if ($DeploymentPhase -eq $phase -or $DeploymentPhase -eq "All") { "▶️" } else { "⏸️" }
    
    Write-Host "`n$indicator $phase - $($info.Name)" -ForegroundColor Yellow
    Write-Host "   Description: $($info.Description)" -ForegroundColor Gray
    Write-Host "   Priority: $($info.Priority)" -ForegroundColor $(if ($info.Priority -eq "CRITICAL") { "Red" } elseif ($info.Priority -eq "HIGH") { "Yellow" } else { "Green" })
    Write-Host "   Services: $($info.Services -join ', ')" -ForegroundColor Gray
    Write-Host "   Time: $($info.EstimatedTime)" -ForegroundColor Gray
    Write-Host "   Prerequisites: $($info.Prerequisites -join ', ')" -ForegroundColor Gray
}

# Validation phase
if ($DeploymentPhase -eq "Validate" -or !$SkipValidation) {
    Write-Host "`n🔍 Pre-deployment Validation" -ForegroundColor Cyan
    Write-Host "============================" -ForegroundColor Cyan
    
    $validationResults = @()
    
    # Check Docker
    Write-Host "`nValidating Docker environment..." -ForegroundColor Yellow
    try {
        $dockerVersion = docker --version
        $dockerComposeVersion = docker-compose --version
        Write-Host "   ✅ Docker: $dockerVersion" -ForegroundColor Green
        Write-Host "   ✅ Docker Compose: $dockerComposeVersion" -ForegroundColor Green
        $validationResults += @{Check="Docker"; Status="PASS"; Details=$dockerVersion}
    } catch {
        Write-Host "   ❌ Docker not available or not running" -ForegroundColor Red
        $validationResults += @{Check="Docker"; Status="FAIL"; Details="Not available"}
    }
    
    # Check system resources
    Write-Host "`nValidating system resources..." -ForegroundColor Yellow
    try {
        $memoryGB = [math]::Round((Get-WmiObject -class "cim_physicalmemory" | Measure-Object -Property Capacity -Sum).Sum / 1GB, 1)
        $diskSpaceGB = [math]::Round((Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='C:'" | Select-Object -ExpandProperty FreeSpace) / 1GB, 1)
        
        $memoryOK = $memoryGB -ge 8
        $diskOK = $diskSpaceGB -ge 20
        
        Write-Host "   $(if ($memoryOK) { '✅' } else { '⚠️' }) RAM: $memoryGB GB $(if (!$memoryOK) { '(Recommend 8GB+)' })" -ForegroundColor $(if ($memoryOK) { "Green" } else { "Yellow" })
        Write-Host "   $(if ($diskOK) { '✅' } else { '❌' }) Disk Space: $diskSpaceGB GB $(if (!$diskOK) { '(Need 20GB+)' })" -ForegroundColor $(if ($diskOK) { "Green" } else { "Red" })
        
        $validationResults += @{Check="Memory"; Status=$(if ($memoryOK) { "PASS" } else { "WARN" }); Details="$memoryGB GB"}
        $validationResults += @{Check="Disk"; Status=$(if ($diskOK) { "PASS" } else { "FAIL" }); Details="$diskSpaceGB GB"}
    } catch {
        Write-Host "   ⚠️ Could not check system resources" -ForegroundColor Yellow
        $validationResults += @{Check="Resources"; Status="WARN"; Details="Could not check"}
    }
    
    # Check environment variables if not generating them
    if (!$GenerateSecrets) {
        Write-Host "`nValidating environment variables..." -ForegroundColor Yellow
        $requiredVars = @('SECRET_KEY', 'JWT_SECRET_KEY', 'PHI_ENCRYPTION_KEY', 'AUDIT_SIGNING_KEY')
        $missingVars = @()
        
        foreach ($var in $requiredVars) {
            if ([string]::IsNullOrEmpty([Environment]::GetEnvironmentVariable($var))) {
                $missingVars += $var
            }
        }
        
        if ($missingVars.Count -eq 0) {
            Write-Host "   ✅ All required environment variables present" -ForegroundColor Green
            $validationResults += @{Check="Environment"; Status="PASS"; Details="All variables set"}
        } else {
            Write-Host "   ❌ Missing environment variables: $($missingVars -join ', ')" -ForegroundColor Red
            Write-Host "   💡 Run with -GenerateSecrets to create them" -ForegroundColor Yellow
            $validationResults += @{Check="Environment"; Status="FAIL"; Details="Missing: $($missingVars -join ', ')"}
        }
    }
    
    # Check existing services
    Write-Host "`nChecking for existing services..." -ForegroundColor Yellow
    $existingServices = docker ps --format "{{.Names}}" 2>$null | Where-Object { $_ -match "iris_" }
    if ($existingServices) {
        Write-Host "   ⚠️ Found existing IRIS services: $($existingServices -join ', ')" -ForegroundColor Yellow
        Write-Host "   💡 These will be updated/replaced during deployment" -ForegroundColor Gray
        $validationResults += @{Check="ExistingServices"; Status="WARN"; Details="$($existingServices.Count) services running"}
    } else {
        Write-Host "   ✅ No conflicting services found" -ForegroundColor Green
        $validationResults += @{Check="ExistingServices"; Status="PASS"; Details="Clean environment"}
    }
    
    # Validation summary
    $failedChecks = $validationResults | Where-Object { $_.Status -eq "FAIL" }
    $warnChecks = $validationResults | Where-Object { $_.Status -eq "WARN" }
    
    Write-Host "`n📊 Validation Summary" -ForegroundColor Cyan
    Write-Host "=====================" -ForegroundColor Cyan
    
    if ($failedChecks.Count -eq 0) {
        Write-Host "✅ VALIDATION PASSED - Ready for deployment" -ForegroundColor Green
        if ($warnChecks.Count -gt 0) {
            Write-Host "⚠️  $($warnChecks.Count) warnings (deployment can continue)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "❌ VALIDATION FAILED - $($failedChecks.Count) critical issues" -ForegroundColor Red
        foreach ($failure in $failedChecks) {
            Write-Host "   • $($failure.Check): $($failure.Details)" -ForegroundColor Red
        }
        
        if (!$ContinueOnFailure) {
            Write-Host "`n❌ Deployment aborted due to validation failures" -ForegroundColor Red
            Write-Host "Use -ContinueOnFailure to override (not recommended)" -ForegroundColor Yellow
            exit 1
        } else {
            Write-Host "⚠️ Continuing despite failures (-ContinueOnFailure specified)" -ForegroundColor Yellow
        }
    }
    
    if ($DeploymentPhase -eq "Validate") {
        Write-Host "`n✅ Validation complete" -ForegroundColor Green
        exit 0
    }
}

# Generate secrets if requested
if ($GenerateSecrets) {
    Write-Host "`n🔐 Generating Secure Environment Variables" -ForegroundColor Cyan
    Write-Host "=========================================" -ForegroundColor Cyan
    
    if (Test-Path "scripts/deployment_tests/generate_secure_env_fixed.ps1") {
        & "scripts/deployment_tests/generate_secure_env_fixed.ps1"
        
        Write-Host "`n⚠️ Please set the generated environment variables before continuing!" -ForegroundColor Yellow
        Write-Host "Copy and execute the QUICK SETUP COMMAND from above." -ForegroundColor Gray
        
        $response = Read-Host "`nPress Enter after setting environment variables (or 'skip' to continue)"
        if ($response -eq "skip") {
            Write-Host "⚠️ Skipping environment variable verification" -ForegroundColor Yellow
        }
    } else {
        Write-Host "❌ Environment generator script not found!" -ForegroundColor Red
        exit 1
    }
}

if ($DryRun) {
    Write-Host "`n🔍 DRY RUN - No actual deployment will occur" -ForegroundColor Yellow
    Write-Host "============================================" -ForegroundColor Yellow
}

# Execute deployment phases
$deploymentResults = @()
$totalStartTime = Get-Date

# Phase 1: Foundation
if ($DeploymentPhase -eq "Phase1" -or $DeploymentPhase -eq "All") {
    Write-Host "`n🏗️ Executing Phase 1: Foundation" -ForegroundColor Green
    Write-Host "================================" -ForegroundColor Green
    
    $phase1Start = Get-Date
    
    if (!$DryRun) {
        $result = & ".\deploy-phase1.ps1" -Environment $Environment
        $phase1Success = $LASTEXITCODE -eq 0
    } else {
        Write-Host "   [DRY RUN] Would execute: .\deploy-phase1.ps1 -Environment $Environment" -ForegroundColor Gray
        $phase1Success = $true
    }
    
    $phase1Duration = (Get-Date) - $phase1Start
    $deploymentResults += @{
        Phase = "Phase1"
        Success = $phase1Success
        Duration = $phase1Duration
        Services = $DeploymentPhases.Phase1.Services
    }
    
    if (!$phase1Success -and !$ContinueOnFailure) {
        Write-Host "❌ Phase 1 failed - Deployment aborted" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "$(if ($phase1Success) { '✅' } else { '❌' }) Phase 1 completed in $([math]::Round($phase1Duration.TotalMinutes, 1)) minutes" -ForegroundColor $(if ($phase1Success) { "Green" } else { "Red" })
}

# Phase 2: AI/ML
if (($DeploymentPhase -eq "Phase2" -or $DeploymentPhase -eq "All") -and ($deploymentResults[-1].Success -or $ContinueOnFailure)) {
    Write-Host "`n🤖 Executing Phase 2: AI/ML Capabilities" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    
    $phase2Start = Get-Date
    
    if (!$DryRun) {
        $result = & ".\deploy-phase2.ps1" -IncludeVectorDB -IncludeDICOM -IncludeMLModels
        $phase2Success = $LASTEXITCODE -eq 0
    } else {
        Write-Host "   [DRY RUN] Would execute: .\deploy-phase2.ps1 -IncludeVectorDB -IncludeDICOM -IncludeMLModels" -ForegroundColor Gray
        $phase2Success = $true
    }
    
    $phase2Duration = (Get-Date) - $phase2Start
    $deploymentResults += @{
        Phase = "Phase2"
        Success = $phase2Success
        Duration = $phase2Duration
        Services = $DeploymentPhases.Phase2.Services
    }
    
    if (!$phase2Success -and !$ContinueOnFailure) {
        Write-Host "❌ Phase 2 failed - Deployment aborted" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "$(if ($phase2Success) { '✅' } else { '❌' }) Phase 2 completed in $([math]::Round($phase2Duration.TotalMinutes, 1)) minutes" -ForegroundColor $(if ($phase2Success) { "Green" } else { "Red" })
}

# Phase 3: Advanced Analytics
if (($DeploymentPhase -eq "Phase3" -or $DeploymentPhase -eq "All") -and ($deploymentResults[-1].Success -or $ContinueOnFailure)) {
    Write-Host "`n📊 Executing Phase 3: Advanced Analytics" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    
    $phase3Start = Get-Date
    
    if (!$DryRun) {
        $result = & ".\deploy-phase3.ps1" -FullStack
        $phase3Success = $LASTEXITCODE -eq 0
    } else {
        Write-Host "   [DRY RUN] Would execute: .\deploy-phase3.ps1 -FullStack" -ForegroundColor Gray
        $phase3Success = $true
    }
    
    $phase3Duration = (Get-Date) - $phase3Start
    $deploymentResults += @{
        Phase = "Phase3"
        Success = $phase3Success
        Duration = $phase3Duration
        Services = $DeploymentPhases.Phase3.Services
    }
    
    Write-Host "$(if ($phase3Success) { '✅' } else { '❌' }) Phase 3 completed in $([math]::Round($phase3Duration.TotalMinutes, 1)) minutes" -ForegroundColor $(if ($phase3Success) { "Green" } else { "Red" })
}

# Final deployment summary
$totalDuration = (Get-Date) - $totalStartTime
$successfulPhases = ($deploymentResults | Where-Object { $_.Success }).Count
$totalPhases = $deploymentResults.Count

Write-Host "`n🎉 Master Deployment Summary" -ForegroundColor Green
Write-Host "============================" -ForegroundColor Green
Write-Host "Environment: $Environment" -ForegroundColor Cyan
Write-Host "Total Duration: $([math]::Round($totalDuration.TotalMinutes, 1)) minutes" -ForegroundColor Cyan
Write-Host "Phases Completed: $successfulPhases/$totalPhases" -ForegroundColor $(if ($successfulPhases -eq $totalPhases) { "Green" } else { "Yellow" })

Write-Host "`n📋 Phase Results:" -ForegroundColor Cyan
foreach ($result in $deploymentResults) {
    $statusIcon = if ($result.Success) { "✅" } else { "❌" }
    $statusColor = if ($result.Success) { "Green" } else { "Red" }
    
    Write-Host "   $statusIcon $($result.Phase): $([math]::Round($result.Duration.TotalMinutes, 1))min - $($result.Services.Count) services" -ForegroundColor $statusColor
}

if ($successfulPhases -eq $totalPhases -and $totalPhases -gt 0) {
    Write-Host "`n🎊 DEPLOYMENT SUCCESSFUL!" -ForegroundColor Green
    Write-Host "================================" -ForegroundColor Green
    
    Write-Host "`n🌐 Access URLs:" -ForegroundColor Yellow
    Write-Host "   Main Application:     http://localhost:8000 (Phase 1)" -ForegroundColor White
    if ($deploymentResults | Where-Object { $_.Phase -eq "Phase2" -and $_.Success }) {
        Write-Host "   Enhanced App:         http://localhost:8001 (Phase 2)" -ForegroundColor White
        Write-Host "   Vector Database:      http://localhost:9091" -ForegroundColor White
        Write-Host "   DICOM Server:         http://localhost:8042" -ForegroundColor White
    }
    if ($deploymentResults | Where-Object { $_.Phase -eq "Phase3" -and $_.Success }) {
        Write-Host "   Advanced App:         http://localhost:8002 (Phase 3)" -ForegroundColor White
        Write-Host "   Grafana Dashboards:   http://localhost:3001" -ForegroundColor White
        Write-Host "   Jaeger Tracing:       http://localhost:16686" -ForegroundColor White
    }
    
    Write-Host "`n🏥 ENTERPRISE HEALTHCARE PLATFORM: FULLY OPERATIONAL" -ForegroundColor Green
    
    Write-Host "`n📚 Next Steps:" -ForegroundColor Yellow
    Write-Host "   1. Review service documentation at /docs endpoints" -ForegroundColor Gray
    Write-Host "   2. Configure monitoring alerts and dashboards" -ForegroundColor Gray
    Write-Host "   3. Set up automated backups and disaster recovery" -ForegroundColor Gray
    Write-Host "   4. Conduct security audit and penetration testing" -ForegroundColor Gray
    Write-Host "   5. Train users on the new platform capabilities" -ForegroundColor Gray
    
    exit 0
} else {
    Write-Host "`n⚠️ PARTIAL DEPLOYMENT" -ForegroundColor Yellow
    Write-Host "===================" -ForegroundColor Yellow
    Write-Host "Some phases failed or were not attempted." -ForegroundColor Yellow
    Write-Host "Review the logs above and retry failed phases individually." -ForegroundColor Gray
    
    exit 1
}