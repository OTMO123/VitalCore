# Application Configuration Validation Script
# Tests: Environment variables, encryption keys, JWT config, database connections
# Based on: PRODUCTION_DEPLOYMENT_CHECKLIST.md - Application Configuration

Write-Host "⚙️ Application Configuration Validation Test" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Green

$testResults = @()
$allPassed = $true
$configIssues = @()

function Test-EnvironmentVariable {
    param(
        [string]$VariableName,
        [string]$Description,
        [bool]$Required = $true,
        [string]$ExpectedPattern = $null
    )
    
    $value = [Environment]::GetEnvironmentVariable($VariableName)
    
    if ([string]::IsNullOrEmpty($value)) {
        if ($Required) {
            Write-Host "  ❌ $VariableName is missing (Required)" -ForegroundColor Red
            $script:allPassed = $false
            $script:configIssues += "Missing required environment variable: $VariableName"
            return @{
                Variable = $VariableName
                Status = "❌ MISSING"
                Description = $Description
                Value = "[NOT SET]"
            }
        } else {
            Write-Host "  ⚠️ $VariableName is missing (Optional)" -ForegroundColor Yellow
            return @{
                Variable = $VariableName
                Status = "⚠️ OPTIONAL"
                Description = $Description
                Value = "[NOT SET]"
            }
        }
    }
    
    # Check pattern if provided
    if ($ExpectedPattern -and $value -notmatch $ExpectedPattern) {
        Write-Host "  ❌ $VariableName has invalid format" -ForegroundColor Red
        $script:allPassed = $false
        $script:configIssues += "Invalid format for $VariableName"
        return @{
            Variable = $VariableName
            Status = "❌ INVALID"
            Description = $Description
            Value = "[INVALID FORMAT]"
        }
    }
    
    # Mask sensitive values
    $displayValue = $value
    if ($VariableName -match "(KEY|SECRET|PASSWORD|TOKEN)") {
        $displayValue = "***MASKED***"
    }
    
    Write-Host "  ✅ $VariableName is set" -ForegroundColor Green
    return @{
        Variable = $VariableName
        Status = "✅ SET"
        Description = $Description
        Value = $displayValue
    }
}

function Test-DatabaseConfiguration {
    Write-Host "`n🗃️ Testing Database Configuration..." -ForegroundColor Yellow
    
    # Check database-related environment variables
    $dbVars = @(
        @{Name = "DATABASE_URL"; Desc = "Database connection string"; Required = $true; Pattern = "^postgresql.*://.*"},
        @{Name = "DB_HOST"; Desc = "Database host"; Required = $false},
        @{Name = "DB_PORT"; Desc = "Database port"; Required = $false; Pattern = "^\d+$"},
        @{Name = "DB_NAME"; Desc = "Database name"; Required = $false},
        @{Name = "DB_USER"; Desc = "Database user"; Required = $false},
        @{Name = "DB_PASSWORD"; Desc = "Database password"; Required = $false},
        @{Name = "DATABASE_POOL_SIZE"; Desc = "Connection pool size"; Required = $false; Pattern = "^\d+$"},
        @{Name = "DATABASE_MAX_OVERFLOW"; Desc = "Max overflow connections"; Required = $false; Pattern = "^\d+$"}
    )
    
    foreach ($var in $dbVars) {
        $result = Test-EnvironmentVariable -VariableName $var.Name -Description $var.Desc -Required $var.Required -ExpectedPattern $var.Pattern
        $testResults += $result
    }
    
    # Test database connection if possible
    Write-Host "  Testing database connectivity..." -ForegroundColor Cyan
    
    try {
        # Check if we can reach the database port
        $dbHost = [Environment]::GetEnvironmentVariable("DB_HOST")
        if (-not $dbHost) { $dbHost = "localhost" }
        $dbPort = [Environment]::GetEnvironmentVariable("DB_PORT")
        if (-not $dbPort) { $dbPort = "5432" }
        
        $tcpClient = New-Object System.Net.Sockets.TcpClient
        $tcpClient.ReceiveTimeout = 5000
        $tcpClient.SendTimeout = 5000
        $tcpClient.Connect($dbHost, [int]$dbPort)
        $tcpClient.Close()
        
        Write-Host "  ✅ Database connection test passed" -ForegroundColor Green
        $testResults += @{
            Variable = "DB_CONNECTION_TEST"
            Status = "✅ PASS"
            Description = "Database connectivity test"
            Value = "${dbHost}:${dbPort}"
        }
    }
    catch {
        Write-Host "  ❌ Database connection test failed: $($_.Exception.Message)" -ForegroundColor Red
        $script:allPassed = $false
        $script:configIssues += "Database connection failed"
        $testResults += @{
            Variable = "DB_CONNECTION_TEST"
            Status = "❌ FAIL"
            Description = "Database connectivity test"
            Value = $_.Exception.Message
        }
    }
}

function Test-SecurityConfiguration {
    Write-Host "`n🔒 Testing Security Configuration..." -ForegroundColor Yellow
    
    # Check security-related environment variables
    $securityVars = @(
        @{Name = "JWT_SECRET_KEY"; Desc = "JWT signing secret"; Required = $true},
        @{Name = "JWT_ALGORITHM"; Desc = "JWT signing algorithm"; Required = $false; Pattern = "^(HS256|RS256|ES256)$"},
        @{Name = "JWT_ACCESS_TOKEN_EXPIRE_MINUTES"; Desc = "JWT access token expiration"; Required = $false; Pattern = "^\d+$"},
        @{Name = "PHI_ENCRYPTION_KEY"; Desc = "PHI encryption key"; Required = $true},
        @{Name = "ENCRYPTION_ALGORITHM"; Desc = "Encryption algorithm"; Required = $false; Pattern = "^AES-256-GCM$"},
        @{Name = "SECRET_KEY"; Desc = "Application secret key"; Required = $true},
        @{Name = "CORS_ORIGINS"; Desc = "CORS allowed origins"; Required = $false},
        @{Name = "RATE_LIMIT_ENABLED"; Desc = "Rate limiting enabled"; Required = $false; Pattern = "^(true|false)$"},
        @{Name = "SECURITY_HEADERS_ENABLED"; Desc = "Security headers enabled"; Required = $false; Pattern = "^(true|false)$"}
    )
    
    foreach ($var in $securityVars) {
        $result = Test-EnvironmentVariable -VariableName $var.Name -Description $var.Desc -Required $var.Required -ExpectedPattern $var.Pattern
        $testResults += $result
    }
    
    # Test JWT configuration strength
    $jwtSecret = [Environment]::GetEnvironmentVariable("JWT_SECRET_KEY")
    if (![string]::IsNullOrEmpty($jwtSecret)) {
        if ($jwtSecret.Length -lt 32) {
            Write-Host "  ⚠️ JWT secret key is too short (< 32 characters)" -ForegroundColor Yellow
            $script:configIssues += "JWT secret key should be at least 32 characters"
            $testResults += @{
                Variable = "JWT_SECRET_STRENGTH"
                Status = "⚠️ WEAK"
                Description = "JWT secret key strength"
                Value = "Length: $($jwtSecret.Length) chars"
            }
        } else {
            Write-Host "  ✅ JWT secret key has adequate length" -ForegroundColor Green
            $testResults += @{
                Variable = "JWT_SECRET_STRENGTH"
                Status = "✅ STRONG"
                Description = "JWT secret key strength"
                Value = "Length: $($jwtSecret.Length) chars"
            }
        }
    }
}

function Test-RedisConfiguration {
    Write-Host "`n🔴 Testing Redis Configuration..." -ForegroundColor Yellow
    
    # Check Redis-related environment variables
    $redisVars = @(
        @{Name = "REDIS_URL"; Desc = "Redis connection string"; Required = $false; Pattern = "^redis://.*"},
        @{Name = "REDIS_HOST"; Desc = "Redis host"; Required = $false},
        @{Name = "REDIS_PORT"; Desc = "Redis port"; Required = $false; Pattern = "^\d+$"},
        @{Name = "REDIS_PASSWORD"; Desc = "Redis password"; Required = $false},
        @{Name = "REDIS_DB"; Desc = "Redis database number"; Required = $false; Pattern = "^\d+$"},
        @{Name = "CACHE_TTL"; Desc = "Cache time-to-live"; Required = $false; Pattern = "^\d+$"}
    )
    
    foreach ($var in $redisVars) {
        $result = Test-EnvironmentVariable -VariableName $var.Name -Description $var.Desc -Required $var.Required -ExpectedPattern $var.Pattern
        $testResults += $result
    }
}

function Test-ApplicationConfiguration {
    Write-Host "`n🏥 Testing Application Configuration..." -ForegroundColor Yellow
    
    # Check application-specific environment variables
    $appVars = @(
        @{Name = "API_TITLE"; Desc = "API title"; Required = $false},
        @{Name = "API_VERSION"; Desc = "API version"; Required = $false; Pattern = "^v?\d+\.\d+\.\d+$"},
        @{Name = "DEBUG"; Desc = "Debug mode"; Required = $false; Pattern = "^(true|false)$"},
        @{Name = "ENVIRONMENT"; Desc = "Environment name"; Required = $true; Pattern = "^(development|staging|production)$"},
        @{Name = "LOG_LEVEL"; Desc = "Logging level"; Required = $false; Pattern = "^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"},
        @{Name = "WORKERS"; Desc = "Number of workers"; Required = $false; Pattern = "^\d+$"},
        @{Name = "MAX_CONNECTIONS"; Desc = "Maximum connections"; Required = $false; Pattern = "^\d+$"}
    )
    
    foreach ($var in $appVars) {
        $result = Test-EnvironmentVariable -VariableName $var.Name -Description $var.Desc -Required $var.Required -ExpectedPattern $var.Pattern
        $testResults += $result
    }
    
    # Check if we're in production mode
    $environment = [Environment]::GetEnvironmentVariable("ENVIRONMENT")
    if ($environment -eq "production") {
        Write-Host "  ✅ Running in production mode" -ForegroundColor Green
        
        # Additional production checks
        $debug = [Environment]::GetEnvironmentVariable("DEBUG")
        if ($debug -eq "true") {
            Write-Host "  ⚠️ Debug mode is enabled in production!" -ForegroundColor Yellow
            $script:configIssues += "Debug mode should be disabled in production"
        }
    }
}

function Test-HIPAAConfiguration {
    Write-Host "`n🏥 Testing HIPAA Configuration..." -ForegroundColor Yellow
    
    # Check HIPAA-related environment variables
    $hipaaVars = @(
        @{Name = "HIPAA_ENABLED"; Desc = "HIPAA compliance enabled"; Required = $true; Pattern = "^true$"},
        @{Name = "AUDIT_LOG_ENABLED"; Desc = "Audit logging enabled"; Required = $true; Pattern = "^true$"},
        @{Name = "AUDIT_LOG_RETENTION_DAYS"; Desc = "Audit log retention"; Required = $false; Pattern = "^\d+$"},
        @{Name = "PHI_AUDIT_ENABLED"; Desc = "PHI access auditing"; Required = $true; Pattern = "^true$"},
        @{Name = "CONSENT_VALIDATION_ENABLED"; Desc = "Consent validation"; Required = $true; Pattern = "^true$"},
        @{Name = "DATA_ENCRYPTION_AT_REST"; Desc = "Data encryption at rest"; Required = $true; Pattern = "^true$"}
    )
    
    foreach ($var in $hipaaVars) {
        $result = Test-EnvironmentVariable -VariableName $var.Name -Description $var.Desc -Required $var.Required -ExpectedPattern $var.Pattern
        $testResults += $result
    }
    
    # Check audit log retention (should be 7 years for HIPAA)
    $retentionDays = [Environment]::GetEnvironmentVariable("AUDIT_LOG_RETENTION_DAYS")
    if (![string]::IsNullOrEmpty($retentionDays)) {
        $days = [int]$retentionDays
        $sevenYears = 365 * 7  # 2555 days
        
        if ($days -ge $sevenYears) {
            Write-Host "  ✅ Audit log retention meets HIPAA requirement (7+ years)" -ForegroundColor Green
            $testResults += @{
                Variable = "HIPAA_RETENTION_COMPLIANCE"
                Status = "✅ COMPLIANT"
                Description = "HIPAA audit log retention"
                Value = "$days days (≥ $sevenYears required)"
            }
        } else {
            Write-Host "  ❌ Audit log retention does not meet HIPAA requirement" -ForegroundColor Red
            $script:allPassed = $false
            $script:configIssues += "Audit log retention must be at least 7 years (2555 days) for HIPAA compliance"
            $testResults += @{
                Variable = "HIPAA_RETENTION_COMPLIANCE"
                Status = "❌ NON-COMPLIANT"
                Description = "HIPAA audit log retention"
                Value = "$days days (< $sevenYears required)"
            }
        }
    }
}

function Test-FileSystemConfiguration {
    Write-Host "`n📁 Testing File System Configuration..." -ForegroundColor Yellow
    
    # Check if required directories exist
    $requiredDirs = @(
        @{Path = "logs"; Desc = "Log directory"},
        @{Path = "data"; Desc = "Data directory"},
        @{Path = "backups"; Desc = "Backup directory"},
        @{Path = "temp"; Desc = "Temporary directory"}
    )
    
    foreach ($dir in $requiredDirs) {
        $fullPath = Join-Path $PWD $dir.Path
        
        if (Test-Path $fullPath) {
            Write-Host "  ✅ $($dir.Desc) exists: $fullPath" -ForegroundColor Green
            $testResults += @{
                Variable = "DIR_$($dir.Path.ToUpper())"
                Status = "✅ EXISTS"
                Description = $dir.Desc
                Value = $fullPath
            }
        } else {
            Write-Host "  ⚠️ $($dir.Desc) does not exist: $fullPath" -ForegroundColor Yellow
            $testResults += @{
                Variable = "DIR_$($dir.Path.ToUpper())"
                Status = "⚠️ MISSING"
                Description = $dir.Desc
                Value = $fullPath
            }
            
            # Try to create the directory
            try {
                New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
                Write-Host "    ✅ Created directory: $fullPath" -ForegroundColor Green
            }
            catch {
                Write-Host "    ❌ Failed to create directory: $($_.Exception.Message)" -ForegroundColor Red
                $script:allPassed = $false
                $script:configIssues += "Cannot create required directory: $fullPath"
            }
        }
    }
    
    # Check file permissions
    try {
        $testFile = Join-Path $PWD "config_test.tmp"
        "test" | Out-File -FilePath $testFile -Encoding UTF8
        Remove-Item $testFile -Force
        
        Write-Host "  ✅ File system write permissions OK" -ForegroundColor Green
        $testResults += @{
            Variable = "FS_WRITE_PERMISSIONS"
            Status = "✅ OK"
            Description = "File system write permissions"
            Value = "Test file created and deleted"
        }
    }
    catch {
        Write-Host "  ❌ File system write permissions failed: $($_.Exception.Message)" -ForegroundColor Red
        $script:allPassed = $false
        $script:configIssues += "File system write permissions issue"
        $testResults += @{
            Variable = "FS_WRITE_PERMISSIONS"
            Status = "❌ FAIL"
            Description = "File system write permissions"
            Value = $_.Exception.Message
        }
    }
}

# Run all configuration tests
Write-Host "`n🚀 Starting Application Configuration Tests..." -ForegroundColor Cyan

Test-DatabaseConfiguration
Test-SecurityConfiguration
Test-RedisConfiguration
Test-ApplicationConfiguration
Test-HIPAAConfiguration
Test-FileSystemConfiguration

# Generate results summary
Write-Host "`n📊 APPLICATION CONFIGURATION RESULTS" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green

$validConfigs = ($testResults | Where-Object { $_.Status -match "✅" }).Count
$invalidConfigs = ($testResults | Where-Object { $_.Status -match "❌" }).Count
$missingConfigs = ($testResults | Where-Object { $_.Status -match "⚠️" }).Count
$totalConfigs = $testResults.Count

Write-Host "`nConfiguration Summary:" -ForegroundColor Cyan
Write-Host "  Total Configurations: $totalConfigs"
Write-Host "  Valid: $validConfigs" -ForegroundColor Green
Write-Host "  Invalid/Missing: $invalidConfigs" -ForegroundColor Red
Write-Host "  Warnings: $missingConfigs" -ForegroundColor Yellow

Write-Host "`nDetailed Results:" -ForegroundColor Cyan
foreach ($test in $testResults) {
    Write-Host "  $($test.Status) $($test.Variable) - $($test.Description)"
    if ($test.Value -ne "[NOT SET]" -and $test.Value -ne "***MASKED***") {
        Write-Host "    Value: $($test.Value)" -ForegroundColor Gray
    }
}

# Show configuration issues
if ($configIssues.Count -gt 0) {
    Write-Host "`n🔧 Configuration Issues to Fix:" -ForegroundColor Yellow
    foreach ($issue in $configIssues) {
        Write-Host "  - $issue" -ForegroundColor Red
    }
}

# Save results to file
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$resultFile = "application_configuration_$timestamp.json"

try {
    $resultsData = @{
        timestamp = $timestamp
        summary = @{
            total = $totalConfigs
            valid = $validConfigs
            invalid = $invalidConfigs
            warnings = $missingConfigs
        }
        tests = $testResults
        issues = $configIssues
    }
    
    $resultsData | ConvertTo-Json -Depth 4 | Out-File -FilePath $resultFile -Encoding UTF8
    Write-Host "`n📁 Results saved to: $resultFile" -ForegroundColor Cyan
}
catch {
    Write-Host "`n⚠️ Could not save results to file: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Final assessment
Write-Host "`n🎯 FINAL ASSESSMENT" -ForegroundColor Green
if ($allPassed -and $invalidConfigs -eq 0) {
    Write-Host "✅ ALL CONFIGURATION TESTS PASSED" -ForegroundColor Green
    Write-Host "Application configuration is ready for production!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "❌ CONFIGURATION ISSUES DETECTED" -ForegroundColor Red
    Write-Host "Please fix the configuration issues before proceeding." -ForegroundColor Red
    exit 1
}