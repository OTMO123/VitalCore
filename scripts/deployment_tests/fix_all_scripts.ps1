# Fix PowerShell Script Compatibility Issues
# This script fixes syntax issues for Russian PowerShell version

Write-Host "🔧 Fixing PowerShell Script Compatibility Issues" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green

$scriptsToFix = @(
    "1_infrastructure_validation.ps1",
    "2_application_configuration.ps1", 
    "3_security_compliance.ps1",
    "4_database_migration.ps1",
    "5_application_deployment.ps1",
    "6_performance_validation.ps1",
    "7_monitoring_alerting.ps1",
    "8_master_deployment_runner.ps1"
)

foreach ($script in $scriptsToFix) {
    Write-Host "Fixing $script..." -ForegroundColor Yellow
    
    if (Test-Path $script) {
        # Read the file content
        $content = Get-Content -Path $script -Raw -Encoding UTF8
        
        # Fix common issues
        $content = $content -replace ' \?\? ', ' -or '
        $content = $content -replace '\?\? ', ''
        $content = $content -replace '< (\d+)s', 'less than $1 seconds'
        $content = $content -replace '< (\d+)', 'less than $1'
        $content = $content -replace '\$dbHost:\$dbPort', '${dbHost}:${dbPort}'
        $content = $content -replace '\$([a-zA-Z_][a-zA-Z0-9_]*):(\$[a-zA-Z_][a-zA-Z0-9_]*)', '${$1}:${$2}'
        $content = $content -replace '&', '"&"'
        $content = $content -replace '2>&1', '2>$null'
        $content = $content -replace '2>\$null', '2>$null'
        
        # Fix Unicode issues (checkmarks and other symbols)
        $content = $content -replace 'вњ…', '✅'
        $content = $content -replace 'рџљЂ', '🚀'
        $content = $content -replace 'рџ"Љ', '📊'
        
        # Fix string interpolation issues
        $content = $content -replace '\$\(([^)]+)\) users', '$($1) + " users"'
        $content = $content -replace 'users, \$', 'users", $'
        
        # Fix variable references in strings
        $content = $content -replace '"DeviceID=''C:''"', '"DeviceID=`"C:`""'
        
        # Save the fixed content
        $content | Out-File -FilePath $script -Encoding UTF8
        Write-Host "  ✅ Fixed $script" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Script not found: $script" -ForegroundColor Red
    }
}

Write-Host "`n🎉 Script fixing complete!" -ForegroundColor Green
Write-Host "You can now run the scripts with: .\scriptname.ps1" -ForegroundColor Cyan