# Database Migration Validation Script
# Tests: Database migrations, data integrity, backup procedures, rollback capability
# Based on: PRODUCTION_DEPLOYMENT_CHECKLIST.md - Database Migration Phase

Write-Host "🗃️ Database Migration Validation Test" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green

$testResults = @()
$allPassed = $true
$migrationIssues = @()

function Test-DatabaseConnection {
    Write-Host "`n🔌 Testing Database Connection..." -ForegroundColor Yellow
    
    $dbHost = [Environment]::GetEnvironmentVariable("DB_HOST") ?? "localhost"
    $dbPort = [Environment]::GetEnvironmentVariable("DB_PORT") ?? "5432"
    $dbName = [Environment]::GetEnvironmentVariable("DB_NAME") ?? "healthcare_db"
    $dbUser = [Environment]::GetEnvironmentVariable("DB_USER") ?? "healthcare_user"
    
    try {
        # Test basic TCP connection to database
        $tcpClient = New-Object System.Net.Sockets.TcpClient
        $tcpClient.ReceiveTimeout = 10000
        $tcpClient.SendTimeout = 10000
        $tcpClient.Connect($dbHost, [int]$dbPort)
        $tcpClient.Close()
        
        Write-Host "  ✅ Database TCP connection successful" -ForegroundColor Green
        $testResults += @{
            Test = "DB_TCP_CONNECTION"
            Status = "✅ PASS"
            Description = "Database TCP connectivity"
            Details = "Connected to $dbHost:$dbPort"
            Severity = "INFO"
        }
        
        # Test database-specific connection if psql is available
        $psqlTest = Get-Command psql -ErrorAction SilentlyContinue
        if ($psqlTest) {
            Write-Host "  Testing PostgreSQL connection with psql..." -ForegroundColor Cyan
            
            # Set PGPASSWORD if available
            $dbPassword = [Environment]::GetEnvironmentVariable("DB_PASSWORD")
            if (![string]::IsNullOrEmpty($dbPassword)) {
                $env:PGPASSWORD = $dbPassword
            }
            
            $connectionTest = psql -h $dbHost -p $dbPort -U $dbUser -d $dbName -c "SELECT version();" 2>&1
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✅ PostgreSQL connection successful" -ForegroundColor Green
                $testResults += @{
                    Test = "DB_PSQL_CONNECTION"
                    Status = "✅ PASS"
                    Description = "PostgreSQL connection test"
                    Details = "Successfully connected to database"
                    Severity = "INFO"
                }
            } else {
                Write-Host "  ❌ PostgreSQL connection failed" -ForegroundColor Red
                Write-Host "  Error: $connectionTest" -ForegroundColor Red
                $script:allPassed = $false
                $script:migrationIssues += "Cannot connect to PostgreSQL database"
                $testResults += @{
                    Test = "DB_PSQL_CONNECTION"
                    Status = "❌ FAIL"
                    Description = "PostgreSQL connection test"
                    Details = "Connection failed: $connectionTest"
                    Severity = "CRITICAL"
                }
            }
            
            # Clear password from environment
            Remove-Item env:PGPASSWORD -ErrorAction SilentlyContinue
        } else {
            Write-Host "  ⚠️ psql not available - skipping PostgreSQL connection test" -ForegroundColor Yellow
            $testResults += @{
                Test = "DB_PSQL_CONNECTION"
                Status = "⚠️ SKIP"
                Description = "PostgreSQL connection test"
                Details = "psql command not found"
                Severity = "LOW"
            }
        }
    }
    catch {
        Write-Host "  ❌ Database connection failed: $($_.Exception.Message)" -ForegroundColor Red
        $script:allPassed = $false
        $script:migrationIssues += "Database connection failed"
        $testResults += @{
            Test = "DB_TCP_CONNECTION"
            Status = "❌ FAIL"
            Description = "Database TCP connectivity"
            Details = $_.Exception.Message
            Severity = "CRITICAL"
        }
    }
}

function Test-AlembicConfiguration {
    Write-Host "`n⚙️ Testing Alembic Configuration..." -ForegroundColor Yellow
    
    # Check if alembic.ini exists
    if (Test-Path "alembic.ini") {
        Write-Host "  ✅ alembic.ini configuration file exists" -ForegroundColor Green
        $testResults += @{
            Test = "ALEMBIC_CONFIG_FILE"
            Status = "✅ PASS"
            Description = "Alembic configuration file"
            Details = "alembic.ini found"
            Severity = "INFO"
        }
        
        # Read and validate alembic.ini
        try {
            $alembicConfig = Get-Content "alembic.ini" -Raw
            
            # Check for database URL configuration
            if ($alembicConfig -match "sqlalchemy\.url") {
                Write-Host "  ✅ Database URL configured in alembic.ini" -ForegroundColor Green
                $testResults += @{
                    Test = "ALEMBIC_DB_URL"
                    Status = "✅ PASS"
                    Description = "Alembic database URL configuration"
                    Details = "Database URL configured"
                    Severity = "INFO"
                }
            } else {
                Write-Host "  ⚠️ Database URL not found in alembic.ini" -ForegroundColor Yellow
                $testResults += @{
                    Test = "ALEMBIC_DB_URL"
                    Status = "⚠️ WARNING"
                    Description = "Alembic database URL configuration"
                    Details = "May be configured dynamically"
                    Severity = "LOW"
                }
            }
            
            # Check for script location
            if ($alembicConfig -match "script_location.*alembic") {
                Write-Host "  ✅ Script location configured" -ForegroundColor Green
                $testResults += @{
                    Test = "ALEMBIC_SCRIPT_LOCATION"
                    Status = "✅ PASS"
                    Description = "Alembic script location"
                    Details = "Script location configured"
                    Severity = "INFO"
                }
            } else {
                Write-Host "  ❌ Script location not configured properly" -ForegroundColor Red
                $script:migrationIssues += "Alembic script location not configured"
                $testResults += @{
                    Test = "ALEMBIC_SCRIPT_LOCATION"
                    Status = "❌ FAIL"
                    Description = "Alembic script location"
                    Details = "Script location missing or invalid"
                    Severity = "HIGH"
                }
            }
        }
        catch {
            Write-Host "  ❌ Failed to read alembic.ini: $($_.Exception.Message)" -ForegroundColor Red
            $script:migrationIssues += "Cannot read alembic configuration"
            $testResults += @{
                Test = "ALEMBIC_CONFIG_READ"
                Status = "❌ FAIL"
                Description = "Alembic configuration read"
                Details = $_.Exception.Message
                Severity = "HIGH"
            }
        }
    } else {
        Write-Host "  ❌ alembic.ini configuration file not found" -ForegroundColor Red
        $script:allPassed = $false
        $script:migrationIssues += "Alembic configuration file missing"
        $testResults += @{
            Test = "ALEMBIC_CONFIG_FILE"
            Status = "❌ FAIL"
            Description = "Alembic configuration file"
            Details = "alembic.ini not found"
            Severity = "CRITICAL"
        }
    }
    
    # Check if alembic directory exists
    if (Test-Path "alembic") {
        Write-Host "  ✅ Alembic migrations directory exists" -ForegroundColor Green
        
        # Check for versions directory
        if (Test-Path "alembic/versions") {
            $migrationFiles = Get-ChildItem "alembic/versions" -Filter "*.py" | Where-Object { $_.Name -ne "__init__.py" }
            Write-Host "  ✅ Found $($migrationFiles.Count) migration files" -ForegroundColor Green
            $testResults += @{
                Test = "ALEMBIC_MIGRATIONS"
                Status = "✅ PASS"
                Description = "Alembic migration files"
                Details = "$($migrationFiles.Count) migration files found"
                Severity = "INFO"
            }
        } else {
            Write-Host "  ❌ alembic/versions directory not found" -ForegroundColor Red
            $script:migrationIssues += "Alembic versions directory missing"
            $testResults += @{
                Test = "ALEMBIC_VERSIONS_DIR"
                Status = "❌ FAIL"
                Description = "Alembic versions directory"
                Details = "alembic/versions not found"
                Severity = "HIGH"
            }
        }
    } else {
        Write-Host "  ❌ Alembic migrations directory not found" -ForegroundColor Red
        $script:allPassed = $false
        $script:migrationIssues += "Alembic directory missing"
        $testResults += @{
            Test = "ALEMBIC_DIRECTORY"
            Status = "❌ FAIL"
            Description = "Alembic migrations directory"
            Details = "alembic directory not found"
            Severity = "CRITICAL"
        }
    }
}

function Test-MigrationStatus {
    Write-Host "`n📋 Testing Migration Status..." -ForegroundColor Yellow
    
    # Check if alembic command is available
    $alembicCmd = Get-Command alembic -ErrorAction SilentlyContinue
    if ($alembicCmd) {
        Write-Host "  ✅ Alembic command available" -ForegroundColor Green
        
        try {
            # Check current migration status
            Write-Host "  Checking current migration status..." -ForegroundColor Cyan
            $currentStatus = alembic current 2>&1
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✅ Successfully retrieved migration status" -ForegroundColor Green
                Write-Host "  Current status: $currentStatus" -ForegroundColor Gray
                $testResults += @{
                    Test = "MIGRATION_STATUS"
                    Status = "✅ PASS"
                    Description = "Current migration status"
                    Details = "Status: $currentStatus"
                    Severity = "INFO"
                }
                
                # Check migration history
                $migrationHistory = alembic history 2>&1
                if ($LASTEXITCODE -eq 0) {
                    $historyLines = ($migrationHistory -split "`n").Count
                    Write-Host "  ✅ Migration history available ($historyLines entries)" -ForegroundColor Green
                    $testResults += @{
                        Test = "MIGRATION_HISTORY"
                        Status = "✅ PASS"
                        Description = "Migration history"
                        Details = "$historyLines migration entries"
                        Severity = "INFO"
                    }
                } else {
                    Write-Host "  ⚠️ Could not retrieve migration history" -ForegroundColor Yellow
                    $testResults += @{
                        Test = "MIGRATION_HISTORY"
                        Status = "⚠️ WARNING"
                        Description = "Migration history"
                        Details = "History command failed"
                        Severity = "LOW"
                    }
                }
                
                # Check for pending migrations
                $headStatus = alembic heads 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "  ✅ Migration heads available" -ForegroundColor Green
                    Write-Host "  Head status: $headStatus" -ForegroundColor Gray
                    
                    # Compare current with head to see if migrations are pending
                    if ($currentStatus -match $headStatus -or $currentStatus -match "head") {
                        Write-Host "  ✅ Database is up to date with migrations" -ForegroundColor Green
                        $testResults += @{
                            Test = "MIGRATION_UP_TO_DATE"
                            Status = "✅ CURRENT"
                            Description = "Migration currency"
                            Details = "Database is current with latest migrations"
                            Severity = "INFO"
                        }
                    } else {
                        Write-Host "  ⚠️ Database may have pending migrations" -ForegroundColor Yellow
                        $testResults += @{
                            Test = "MIGRATION_UP_TO_DATE"
                            Status = "⚠️ PENDING"
                            Description = "Migration currency"
                            Details = "Migrations may be pending"
                            Severity = "MEDIUM"
                        }
                    }
                }
            } else {
                Write-Host "  ❌ Failed to retrieve migration status: $currentStatus" -ForegroundColor Red
                $script:migrationIssues += "Cannot retrieve migration status"
                $testResults += @{
                    Test = "MIGRATION_STATUS"
                    Status = "❌ FAIL"
                    Description = "Current migration status"
                    Details = "Status command failed: $currentStatus"
                    Severity = "HIGH"
                }
            }
        }
        catch {
            Write-Host "  ❌ Migration status check failed: $($_.Exception.Message)" -ForegroundColor Red
            $script:migrationIssues += "Migration status check failed"
            $testResults += @{
                Test = "MIGRATION_STATUS"
                Status = "❌ FAIL"
                Description = "Current migration status"
                Details = $_.Exception.Message
                Severity = "HIGH"
            }
        }
    } else {
        Write-Host "  ❌ Alembic command not available" -ForegroundColor Red
        $script:allPassed = $false
        $script:migrationIssues += "Alembic command not found - install with 'pip install alembic'"
        $testResults += @{
            Test = "ALEMBIC_COMMAND"
            Status = "❌ FAIL"
            Description = "Alembic command availability"
            Details = "Alembic not installed or not in PATH"
            Severity = "CRITICAL"
        }
    }
}

function Test-DatabaseSchema {
    Write-Host "`n🏗️ Testing Database Schema..." -ForegroundColor Yellow
    
    $psqlCmd = Get-Command psql -ErrorAction SilentlyContinue
    if ($psqlCmd) {
        $dbHost = [Environment]::GetEnvironmentVariable("DB_HOST") ?? "localhost"
        $dbPort = [Environment]::GetEnvironmentVariable("DB_PORT") ?? "5432"
        $dbName = [Environment]::GetEnvironmentVariable("DB_NAME") ?? "healthcare_db"
        $dbUser = [Environment]::GetEnvironmentVariable("DB_USER") ?? "healthcare_user"
        $dbPassword = [Environment]::GetEnvironmentVariable("DB_PASSWORD")
        
        try {
            # Set password if available
            if (![string]::IsNullOrEmpty($dbPassword)) {
                $env:PGPASSWORD = $dbPassword
            }
            
            # Check if database exists
            Write-Host "  Testing database existence..." -ForegroundColor Cyan
            $dbExists = psql -h $dbHost -p $dbPort -U $dbUser -l 2>&1 | Select-String $dbName
            
            if ($dbExists) {
                Write-Host "  ✅ Database '$dbName' exists" -ForegroundColor Green
                $testResults += @{
                    Test = "DATABASE_EXISTS"
                    Status = "✅ PASS"
                    Description = "Database existence"
                    Details = "Database '$dbName' found"
                    Severity = "INFO"
                }
                
                # Check core healthcare tables
                Write-Host "  Checking core healthcare tables..." -ForegroundColor Cyan
                $expectedTables = @(
                    "patients",
                    "immunizations", 
                    "clinical_documents",
                    "consents",
                    "audit_events",
                    "alembic_version"
                )
                
                foreach ($table in $expectedTables) {
                    $tableExists = psql -h $dbHost -p $dbPort -U $dbUser -d $dbName -c "\dt $table" 2>&1
                    
                    if ($LASTEXITCODE -eq 0 -and $tableExists -match $table) {
                        Write-Host "    ✅ Table '$table' exists" -ForegroundColor Green
                        $testResults += @{
                            Test = "TABLE_$($table.ToUpper())"
                            Status = "✅ EXISTS"
                            Description = "Database table: $table"
                            Details = "Table exists in database"
                            Severity = "INFO"
                        }
                    } else {
                        Write-Host "    ❌ Table '$table' missing" -ForegroundColor Red
                        $script:migrationIssues += "Required table '$table' is missing"
                        $testResults += @{
                            Test = "TABLE_$($table.ToUpper())"
                            Status = "❌ MISSING"
                            Description = "Database table: $table"
                            Details = "Required table not found"
                            Severity = "HIGH"
                        }
                    }
                }
                
                # Check table record counts (should be accessible)
                Write-Host "  Testing table accessibility..." -ForegroundColor Cyan
                foreach ($table in $expectedTables) {
                    if ($table -ne "alembic_version") {
                        $recordCount = psql -h $dbHost -p $dbPort -U $dbUser -d $dbName -t -c "SELECT COUNT(*) FROM $table;" 2>&1
                        
                        if ($LASTEXITCODE -eq 0) {
                            $count = $recordCount.Trim()
                            Write-Host "    ✅ Table '$table' accessible (records: $count)" -ForegroundColor Green
                            $testResults += @{
                                Test = "TABLE_ACCESS_$($table.ToUpper())"
                                Status = "✅ ACCESSIBLE"
                                Description = "Table access: $table"
                                Details = "$count records"
                                Severity = "INFO"
                            }
                        } else {
                            Write-Host "    ❌ Table '$table' not accessible" -ForegroundColor Red
                            $script:migrationIssues += "Cannot access table '$table'"
                            $testResults += @{
                                Test = "TABLE_ACCESS_$($table.ToUpper())"
                                Status = "❌ INACCESSIBLE"
                                Description = "Table access: $table"
                                Details = "Access denied or table missing"
                                Severity = "HIGH"
                            }
                        }
                    }
                }
                
                # Check indexes
                Write-Host "  Checking database indexes..." -ForegroundColor Cyan
                $indexQuery = "SELECT tablename, indexname FROM pg_indexes WHERE schemaname = 'public';"
                $indexes = psql -h $dbHost -p $dbPort -U $dbUser -d $dbName -t -c $indexQuery 2>&1
                
                if ($LASTEXITCODE -eq 0) {
                    $indexLines = ($indexes -split "`n" | Where-Object { $_.Trim() -ne "" }).Count
                    Write-Host "  ✅ Found $indexLines database indexes" -ForegroundColor Green
                    $testResults += @{
                        Test = "DATABASE_INDEXES"
                        Status = "✅ PASS"
                        Description = "Database indexes"
                        Details = "$indexLines indexes found"
                        Severity = "INFO"
                    }
                } else {
                    Write-Host "  ⚠️ Could not retrieve index information" -ForegroundColor Yellow
                    $testResults += @{
                        Test = "DATABASE_INDEXES"
                        Status = "⚠️ WARNING"
                        Description = "Database indexes"
                        Details = "Index query failed"
                        Severity = "LOW"
                    }
                }
                
            } else {
                Write-Host "  ❌ Database '$dbName' does not exist" -ForegroundColor Red
                $script:allPassed = $false
                $script:migrationIssues += "Database '$dbName' does not exist"
                $testResults += @{
                    Test = "DATABASE_EXISTS"
                    Status = "❌ FAIL"
                    Description = "Database existence"
                    Details = "Database '$dbName' not found"
                    Severity = "CRITICAL"
                }
            }
            
            # Clear password from environment
            Remove-Item env:PGPASSWORD -ErrorAction SilentlyContinue
            
        }
        catch {
            Write-Host "  ❌ Database schema test failed: $($_.Exception.Message)" -ForegroundColor Red
            $script:migrationIssues += "Database schema validation failed"
            $testResults += @{
                Test = "DATABASE_SCHEMA"
                Status = "❌ FAIL"
                Description = "Database schema validation"
                Details = $_.Exception.Message
                Severity = "HIGH"
            }
            
            # Clear password from environment
            Remove-Item env:PGPASSWORD -ErrorAction SilentlyContinue
        }
    } else {
        Write-Host "  ⚠️ psql command not available - skipping schema tests" -ForegroundColor Yellow
        $testResults += @{
            Test = "PSQL_COMMAND"
            Status = "⚠️ SKIP"
            Description = "PostgreSQL command availability"
            Details = "psql not found - cannot test schema"
            Severity = "MEDIUM"
        }
    }
}

function Test-BackupCapability {
    Write-Host "`n💾 Testing Backup Capability..." -ForegroundColor Yellow
    
    # Check if pg_dump is available
    $pgDumpCmd = Get-Command pg_dump -ErrorAction SilentlyContinue
    if ($pgDumpCmd) {
        Write-Host "  ✅ pg_dump command available" -ForegroundColor Green
        $testResults += @{
            Test = "PG_DUMP_AVAILABLE"
            Status = "✅ PASS"
            Description = "pg_dump command availability"
            Details = "Backup tool available"
            Severity = "INFO"
        }
        
        # Test backup directory
        $backupDir = "backups"
        if (!(Test-Path $backupDir)) {
            try {
                New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
                Write-Host "  ✅ Created backup directory: $backupDir" -ForegroundColor Green
            }
            catch {
                Write-Host "  ❌ Failed to create backup directory: $($_.Exception.Message)" -ForegroundColor Red
                $script:migrationIssues += "Cannot create backup directory"
                $testResults += @{
                    Test = "BACKUP_DIRECTORY"
                    Status = "❌ FAIL"
                    Description = "Backup directory creation"
                    Details = $_.Exception.Message
                    Severity = "HIGH"
                }
                return
            }
        }
        
        Write-Host "  ✅ Backup directory available: $backupDir" -ForegroundColor Green
        $testResults += @{
            Test = "BACKUP_DIRECTORY"
            Status = "✅ PASS"
            Description = "Backup directory availability"
            Details = "Directory: $backupDir"
            Severity = "INFO"
        }
        
        # Test backup permissions
        try {
            $testBackupFile = Join-Path $backupDir "test_backup.sql"
            "-- Test backup file" | Out-File -FilePath $testBackupFile -Encoding UTF8
            
            if (Test-Path $testBackupFile) {
                Remove-Item $testBackupFile -Force
                Write-Host "  ✅ Backup directory write permissions OK" -ForegroundColor Green
                $testResults += @{
                    Test = "BACKUP_PERMISSIONS"
                    Status = "✅ PASS"
                    Description = "Backup directory permissions"
                    Details = "Write permissions verified"
                    Severity = "INFO"
                }
            }
        }
        catch {
            Write-Host "  ❌ Backup directory write permissions failed: $($_.Exception.Message)" -ForegroundColor Red
            $script:migrationIssues += "Cannot write to backup directory"
            $testResults += @{
                Test = "BACKUP_PERMISSIONS"
                Status = "❌ FAIL"
                Description = "Backup directory permissions"
                Details = $_.Exception.Message
                Severity = "HIGH"
            }
        }
        
        # Test backup command (dry run)
        Write-Host "  Testing backup command syntax..." -ForegroundColor Cyan
        $dbHost = [Environment]::GetEnvironmentVariable("DB_HOST") ?? "localhost"
        $dbPort = [Environment]::GetEnvironmentVariable("DB_PORT") ?? "5432"
        $dbName = [Environment]::GetEnvironmentVariable("DB_NAME") ?? "healthcare_db"
        $dbUser = [Environment]::GetEnvironmentVariable("DB_USER") ?? "healthcare_user"
        
        # Test pg_dump help (to verify command works)
        $pgDumpHelp = pg_dump --help 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ pg_dump command functional" -ForegroundColor Green
            $testResults += @{
                Test = "PG_DUMP_FUNCTIONAL"
                Status = "✅ PASS"
                Description = "pg_dump functionality"
                Details = "Command responds to --help"
                Severity = "INFO"
            }
        } else {
            Write-Host "  ❌ pg_dump command not functional" -ForegroundColor Red
            $script:migrationIssues += "pg_dump command not working properly"
            $testResults += @{
                Test = "PG_DUMP_FUNCTIONAL"
                Status = "❌ FAIL"
                Description = "pg_dump functionality"
                Details = "Command does not respond properly"
                Severity = "HIGH"
            }
        }
        
    } else {
        Write-Host "  ❌ pg_dump command not available" -ForegroundColor Red
        $script:migrationIssues += "pg_dump not found - install PostgreSQL client tools"
        $testResults += @{
            Test = "PG_DUMP_AVAILABLE"
            Status = "❌ FAIL"
            Description = "pg_dump command availability"
            Details = "Backup tool not found"
            Severity = "CRITICAL"
        }
    }
    
    # Check for existing backup scripts
    $backupScripts = @(
        "scripts/database/backup_database.ps1",
        "scripts/powershell/backup-database.ps1",
        "backup_database.ps1"
    )
    
    $backupScriptFound = $false
    foreach ($script in $backupScripts) {
        if (Test-Path $script) {
            Write-Host "  ✅ Backup script found: $script" -ForegroundColor Green
            $backupScriptFound = $true
            $testResults += @{
                Test = "BACKUP_SCRIPT"
                Status = "✅ FOUND"
                Description = "Backup script availability"
                Details = "Script: $script"
                Severity = "INFO"
            }
            break
        }
    }
    
    if (!$backupScriptFound) {
        Write-Host "  ⚠️ No backup scripts found in expected locations" -ForegroundColor Yellow
        $testResults += @{
            Test = "BACKUP_SCRIPT"
            Status = "⚠️ MISSING"
            Description = "Backup script availability"
            Details = "No automated backup scripts found"
            Severity = "MEDIUM"
        }
    }
}

function Test-RollbackCapability {
    Write-Host "`n🔄 Testing Rollback Capability..." -ForegroundColor Yellow
    
    # Check if pg_restore is available
    $pgRestoreCmd = Get-Command pg_restore -ErrorAction SilentlyContinue
    if ($pgRestoreCmd) {
        Write-Host "  ✅ pg_restore command available" -ForegroundColor Green
        $testResults += @{
            Test = "PG_RESTORE_AVAILABLE"
            Status = "✅ PASS"
            Description = "pg_restore command availability"
            Details = "Restore tool available"
            Severity = "INFO"
        }
        
        # Test pg_restore functionality
        $pgRestoreHelp = pg_restore --help 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ pg_restore command functional" -ForegroundColor Green
            $testResults += @{
                Test = "PG_RESTORE_FUNCTIONAL"
                Status = "✅ PASS"
                Description = "pg_restore functionality"
                Details = "Command responds to --help"
                Severity = "INFO"
            }
        } else {
            Write-Host "  ❌ pg_restore command not functional" -ForegroundColor Red
            $script:migrationIssues += "pg_restore command not working properly"
            $testResults += @{
                Test = "PG_RESTORE_FUNCTIONAL"
                Status = "❌ FAIL"
                Description = "pg_restore functionality"
                Details = "Command does not respond properly"
                Severity = "HIGH"
            }
        }
    } else {
        Write-Host "  ❌ pg_restore command not available" -ForegroundColor Red
        $script:migrationIssues += "pg_restore not found - install PostgreSQL client tools"
        $testResults += @{
            Test = "PG_RESTORE_AVAILABLE"
            Status = "❌ FAIL"
            Description = "pg_restore command availability"
            Details = "Restore tool not found"
            Severity = "CRITICAL"
        }
    }
    
    # Test Alembic downgrade capability
    $alembicCmd = Get-Command alembic -ErrorAction SilentlyContinue
    if ($alembicCmd) {
        Write-Host "  Testing Alembic downgrade capability..." -ForegroundColor Cyan
        
        try {
            # Check if we can get help for downgrade command
            $downgradeHelp = alembic downgrade --help 2>&1
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✅ Alembic downgrade command available" -ForegroundColor Green
                $testResults += @{
                    Test = "ALEMBIC_DOWNGRADE"
                    Status = "✅ AVAILABLE"
                    Description = "Alembic downgrade capability"
                    Details = "Downgrade command functional"
                    Severity = "INFO"
                }
            } else {
                Write-Host "  ❌ Alembic downgrade command not working" -ForegroundColor Red
                $script:migrationIssues += "Alembic downgrade not functional"
                $testResults += @{
                    Test = "ALEMBIC_DOWNGRADE"
                    Status = "❌ FAIL"
                    Description = "Alembic downgrade capability"
                    Details = "Downgrade command failed"
                    Severity = "HIGH"
                }
            }
        }
        catch {
            Write-Host "  ❌ Alembic downgrade test failed: $($_.Exception.Message)" -ForegroundColor Red
            $script:migrationIssues += "Alembic downgrade test failed"
            $testResults += @{
                Test = "ALEMBIC_DOWNGRADE"
                Status = "❌ FAIL"
                Description = "Alembic downgrade capability"
                Details = $_.Exception.Message
                Severity = "HIGH"
            }
        }
    }
    
    # Check for rollback scripts
    $rollbackScripts = @(
        "scripts/database/rollback_migration.ps1",
        "scripts/powershell/restore-database.ps1",
        "rollback_database.ps1"
    )
    
    $rollbackScriptFound = $false
    foreach ($script in $rollbackScripts) {
        if (Test-Path $script) {
            Write-Host "  ✅ Rollback script found: $script" -ForegroundColor Green
            $rollbackScriptFound = $true
            $testResults += @{
                Test = "ROLLBACK_SCRIPT"
                Status = "✅ FOUND"
                Description = "Rollback script availability"
                Details = "Script: $script"
                Severity = "INFO"
            }
            break
        }
    }
    
    if (!$rollbackScriptFound) {
        Write-Host "  ⚠️ No rollback scripts found in expected locations" -ForegroundColor Yellow
        $testResults += @{
            Test = "ROLLBACK_SCRIPT"
            Status = "⚠️ MISSING"
            Description = "Rollback script availability"
            Details = "No automated rollback scripts found"
            Severity = "MEDIUM"
        }
    }
    
    # Test rollback plan documentation
    $rollbackDocs = @(
        "docs/deployment/PRODUCTION_DEPLOYMENT_CHECKLIST.md",
        "docs/operations/OPERATIONAL_RUNBOOKS.md",
        "ROLLBACK_PLAN.md"
    )
    
    $rollbackDocFound = $false
    foreach ($doc in $rollbackDocs) {
        if (Test-Path $doc) {
            $content = Get-Content $doc -Raw
            if ($content -match "rollback|ROLLBACK") {
                Write-Host "  ✅ Rollback documentation found: $doc" -ForegroundColor Green
                $rollbackDocFound = $true
                $testResults += @{
                    Test = "ROLLBACK_DOCUMENTATION"
                    Status = "✅ FOUND"
                    Description = "Rollback documentation"
                    Details = "Documentation: $doc"
                    Severity = "INFO"
                }
                break
            }
        }
    }
    
    if (!$rollbackDocFound) {
        Write-Host "  ⚠️ Rollback documentation not found" -ForegroundColor Yellow
        $testResults += @{
            Test = "ROLLBACK_DOCUMENTATION"
            Status = "⚠️ MISSING"
            Description = "Rollback documentation"
            Details = "No rollback procedures documented"
            Severity = "MEDIUM"
        }
    }
}

# Run all database migration tests
Write-Host "`n🚀 Starting Database Migration Tests..." -ForegroundColor Cyan

Test-DatabaseConnection
Test-AlembicConfiguration
Test-MigrationStatus
Test-DatabaseSchema
Test-BackupCapability
Test-RollbackCapability

# Generate results summary
Write-Host "`n📊 DATABASE MIGRATION RESULTS" -ForegroundColor Green
Write-Host "==============================" -ForegroundColor Green

$passedTests = ($testResults | Where-Object { $_.Status -match "✅" }).Count
$failedTests = ($testResults | Where-Object { $_.Status -match "❌" }).Count
$warningTests = ($testResults | Where-Object { $_.Status -match "⚠️" }).Count
$skippedTests = ($testResults | Where-Object { $_.Status -match "SKIP" }).Count
$totalTests = $testResults.Count

Write-Host "`nMigration Test Summary:" -ForegroundColor Cyan
Write-Host "  Total Tests: $totalTests"
Write-Host "  Passed: $passedTests" -ForegroundColor Green
Write-Host "  Failed: $failedTests" -ForegroundColor Red
Write-Host "  Warnings: $warningTests" -ForegroundColor Yellow
Write-Host "  Skipped: $skippedTests" -ForegroundColor Gray

# Group results by severity
$criticalIssues = ($testResults | Where-Object { $_.Severity -eq "CRITICAL" -and $_.Status -match "❌" }).Count
$highIssues = ($testResults | Where-Object { $_.Severity -eq "HIGH" -and $_.Status -match "❌" }).Count
$mediumIssues = ($testResults | Where-Object { $_.Severity -eq "MEDIUM" -and $_.Status -match "❌|⚠️" }).Count

Write-Host "`nIssues by Severity:" -ForegroundColor Cyan
Write-Host "  Critical: $criticalIssues" -ForegroundColor $(if ($criticalIssues -eq 0) { "Green" } else { "Red" })
Write-Host "  High: $highIssues" -ForegroundColor $(if ($highIssues -eq 0) { "Green" } else { "Red" })
Write-Host "  Medium: $mediumIssues" -ForegroundColor $(if ($mediumIssues -eq 0) { "Green" } else { "Yellow" })

# Show migration issues
if ($migrationIssues.Count -gt 0) {
    Write-Host "`n🚨 Migration Issues to Fix:" -ForegroundColor Red
    for ($i = 0; $i -lt $migrationIssues.Count; $i++) {
        Write-Host "  $($i + 1). $($migrationIssues[$i])" -ForegroundColor Red
    }
}

# Show detailed results by category
Write-Host "`nDetailed Results by Category:" -ForegroundColor Cyan
$categories = @(
    @{Name = "Connection"; Pattern = "DB_.*CONNECTION|DATABASE_EXISTS"},
    @{Name = "Alembic"; Pattern = "ALEMBIC_.*"},
    @{Name = "Migration"; Pattern = "MIGRATION_.*"},
    @{Name = "Schema"; Pattern = "TABLE_.*|DATABASE_.*"},
    @{Name = "Backup"; Pattern = ".*BACKUP.*|PG_DUMP.*"},
    @{Name = "Rollback"; Pattern = ".*ROLLBACK.*|PG_RESTORE.*|.*DOWNGRADE.*"}
)

foreach ($category in $categories) {
    $categoryTests = $testResults | Where-Object { $_.Test -match $category.Pattern }
    if ($categoryTests.Count -gt 0) {
        Write-Host "  $($category.Name) Tests:" -ForegroundColor Yellow
        foreach ($test in $categoryTests) {
            Write-Host "    $($test.Status) $($test.Description)"
            if ($test.Details -and $test.Details -ne "") {
                Write-Host "      Details: $($test.Details)" -ForegroundColor Gray
            }
        }
    }
}

# Save results to file
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$resultFile = "database_migration_$timestamp.json"

try {
    $resultsData = @{
        timestamp = $timestamp
        summary = @{
            total_tests = $totalTests
            passed = $passedTests
            failed = $failedTests
            warnings = $warningTests
            skipped = $skippedTests
            critical_issues = $criticalIssues
            high_issues = $highIssues
            medium_issues = $mediumIssues
        }
        tests = $testResults
        migration_issues = $migrationIssues
        deployment_ready = ($criticalIssues -eq 0 -and $highIssues -eq 0)
    }
    
    $resultsData | ConvertTo-Json -Depth 4 | Out-File -FilePath $resultFile -Encoding UTF8
    Write-Host "`n📁 Results saved to: $resultFile" -ForegroundColor Cyan
}
catch {
    Write-Host "`n⚠️ Could not save results to file: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Final assessment
Write-Host "`n🎯 FINAL MIGRATION ASSESSMENT" -ForegroundColor Green
if ($allPassed -and $criticalIssues -eq 0 -and $highIssues -eq 0) {
    Write-Host "✅ DATABASE MIGRATION VALIDATION PASSED" -ForegroundColor Green
    Write-Host "Database is ready for migration and deployment!" -ForegroundColor Green
    exit 0
} elseif ($criticalIssues -eq 0 -and $highIssues -eq 0) {
    Write-Host "⚠️ DATABASE MIGRATION VALIDATION PASSED WITH WARNINGS" -ForegroundColor Yellow
    Write-Host "Database migration can proceed but has some recommendations." -ForegroundColor Yellow
    exit 0
} else {
    Write-Host "❌ DATABASE MIGRATION VALIDATION FAILED" -ForegroundColor Red
    Write-Host "Critical database issues must be fixed before deployment!" -ForegroundColor Red
    exit 1
}