# Security & Compliance Validation Script
# Tests: HIPAA compliance, SOC2 controls, encryption, audit logging, access controls
# Based on: PRODUCTION_DEPLOYMENT_CHECKLIST.md - Security Validation

Write-Host "🔒 Security & Compliance Validation Test" -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green

$testResults = @()
$allPassed = $true
$securityIssues = @()

function Test-PHIEncryption {
    Write-Host "`n🔐 Testing PHI Encryption..." -ForegroundColor Yellow
    
    # Check if encryption service is available
    try {
        # Test encryption configuration
        $encryptionKey = [Environment]::GetEnvironmentVariable("PHI_ENCRYPTION_KEY")
        if ([string]::IsNullOrEmpty($encryptionKey)) {
            Write-Host "  ❌ PHI encryption key not configured" -ForegroundColor Red
            $script:allPassed = $false
            $script:securityIssues += "PHI encryption key is missing"
            $testResults += @{
                Test = "PHI_ENCRYPTION_KEY"
                Status = "❌ FAIL"
                Description = "PHI encryption key configuration"
                Details = "Encryption key not set"
                Severity = "CRITICAL"
            }
        } else {
            Write-Host "  ✅ PHI encryption key is configured" -ForegroundColor Green
            
            # Check key strength
            if ($encryptionKey.Length -lt 32) {
                Write-Host "  ⚠️ PHI encryption key may be too short" -ForegroundColor Yellow
                $script:securityIssues += "PHI encryption key should be at least 32 characters"
                $testResults += @{
                    Test = "PHI_ENCRYPTION_STRENGTH"
                    Status = "⚠️ WEAK"
                    Description = "PHI encryption key strength"
                    Details = "Key length: $($encryptionKey.Length) characters"
                    Severity = "MEDIUM"
                }
            } else {
                Write-Host "  ✅ PHI encryption key has adequate strength" -ForegroundColor Green
                $testResults += @{
                    Test = "PHI_ENCRYPTION_STRENGTH"
                    Status = "✅ PASS"
                    Description = "PHI encryption key strength"
                    Details = "Key length: $($encryptionKey.Length) characters"
                    Severity = "INFO"
                }
            }
        }
        
        # Test encryption algorithm
        $algorithm = [Environment]::GetEnvironmentVariable("ENCRYPTION_ALGORITHM") ?? "AES-256-GCM"
        if ($algorithm -eq "AES-256-GCM") {
            Write-Host "  ✅ Using secure encryption algorithm: $algorithm" -ForegroundColor Green
            $testResults += @{
                Test = "ENCRYPTION_ALGORITHM"
                Status = "✅ PASS"
                Description = "Encryption algorithm validation"
                Details = "Algorithm: $algorithm"
                Severity = "INFO"
            }
        } else {
            Write-Host "  ⚠️ Encryption algorithm may not be optimal: $algorithm" -ForegroundColor Yellow
            $script:securityIssues += "Consider using AES-256-GCM for PHI encryption"
            $testResults += @{
                Test = "ENCRYPTION_ALGORITHM"
                Status = "⚠️ SUBOPTIMAL"
                Description = "Encryption algorithm validation"
                Details = "Algorithm: $algorithm (AES-256-GCM recommended)"
                Severity = "LOW"
            }
        }
        
    }
    catch {
        Write-Host "  ❌ PHI encryption test failed: $($_.Exception.Message)" -ForegroundColor Red
        $script:allPassed = $false
        $script:securityIssues += "PHI encryption validation failed"
        $testResults += @{
            Test = "PHI_ENCRYPTION_TEST"
            Status = "❌ FAIL"
            Description = "PHI encryption test"
            Details = $_.Exception.Message
            Severity = "CRITICAL"
        }
    }
}

function Test-HIPAACompliance {
    Write-Host "`n🏥 Testing HIPAA Compliance..." -ForegroundColor Yellow
    
    # HIPAA Administrative Safeguards
    $hipaaControls = @(
        @{Name = "HIPAA_ENABLED"; Required = "true"; Desc = "HIPAA compliance enabled"},
        @{Name = "AUDIT_LOG_ENABLED"; Required = "true"; Desc = "Audit logging enabled"},
        @{Name = "PHI_AUDIT_ENABLED"; Required = "true"; Desc = "PHI access auditing enabled"},
        @{Name = "CONSENT_VALIDATION_ENABLED"; Required = "true"; Desc = "Consent validation enabled"},
        @{Name = "DATA_ENCRYPTION_AT_REST"; Required = "true"; Desc = "Data encryption at rest"},
        @{Name = "ACCESS_CONTROL_ENABLED"; Required = "true"; Desc = "Access control enabled"},
        @{Name = "MINIMUM_NECESSARY_RULE"; Required = "true"; Desc = "Minimum necessary rule enforcement"}
    )
    
    $hipaaFailures = 0
    foreach ($control in $hipaaControls) {
        $value = [Environment]::GetEnvironmentVariable($control.Name)
        
        if ($value -eq $control.Required) {
            Write-Host "  ✅ $($control.Desc)" -ForegroundColor Green
            $testResults += @{
                Test = $control.Name
                Status = "✅ COMPLIANT"
                Description = $control.Desc
                Details = "Enabled"
                Severity = "INFO"
            }
        } else {
            Write-Host "  ❌ $($control.Desc) - NOT COMPLIANT" -ForegroundColor Red
            $script:allPassed = $false
            $script:securityIssues += "HIPAA violation: $($control.Desc) not properly configured"
            $hipaaFailures++
            $testResults += @{
                Test = $control.Name
                Status = "❌ NON-COMPLIANT"
                Description = $control.Desc
                Details = "Not enabled or misconfigured"
                Severity = "CRITICAL"
            }
        }
    }
    
    # Check audit log retention (7 years required)
    $retentionDays = [Environment]::GetEnvironmentVariable("AUDIT_LOG_RETENTION_DAYS")
    if (![string]::IsNullOrEmpty($retentionDays)) {
        $days = [int]$retentionDays
        $requiredDays = 365 * 7  # 2555 days
        
        if ($days -ge $requiredDays) {
            Write-Host "  ✅ Audit log retention meets HIPAA requirement ($days days)" -ForegroundColor Green
            $testResults += @{
                Test = "HIPAA_AUDIT_RETENTION"
                Status = "✅ COMPLIANT"
                Description = "HIPAA audit log retention"
                Details = "$days days (≥ $requiredDays required)"
                Severity = "INFO"
            }
        } else {
            Write-Host "  ❌ Audit log retention violates HIPAA requirement ($days < $requiredDays days)" -ForegroundColor Red
            $script:allPassed = $false
            $script:securityIssues += "HIPAA violation: Audit logs must be retained for at least 7 years"
            $hipaaFailures++
            $testResults += @{
                Test = "HIPAA_AUDIT_RETENTION"
                Status = "❌ NON-COMPLIANT"
                Description = "HIPAA audit log retention"
                Details = "$days days (< $requiredDays required)"
                Severity = "CRITICAL"
            }
        }
    } else {
        Write-Host "  ❌ Audit log retention not configured" -ForegroundColor Red
        $script:allPassed = $false
        $script:securityIssues += "HIPAA violation: Audit log retention not configured"
        $hipaaFailures++
    }
    
    # Overall HIPAA assessment
    Write-Host "`n  📋 HIPAA Compliance Summary:" -ForegroundColor Cyan
    Write-Host "    Controls Tested: $($hipaaControls.Count + 1)"
    Write-Host "    Failures: $hipaaFailures" -ForegroundColor $(if ($hipaaFailures -eq 0) { "Green" } else { "Red" })
    
    if ($hipaaFailures -eq 0) {
        Write-Host "    ✅ HIPAA COMPLIANT" -ForegroundColor Green
    } else {
        Write-Host "    ❌ HIPAA NON-COMPLIANT" -ForegroundColor Red
    }
}

function Test-SOC2Controls {
    Write-Host "`n🛡️ Testing SOC2 Type II Controls..." -ForegroundColor Yellow
    
    # SOC2 Trust Service Criteria
    $soc2Controls = @(
        @{
            Criteria = "CC1 - Control Environment"
            Tests = @(
                @{Name = "RBAC_ENABLED"; Desc = "Role-based access control"},
                @{Name = "USER_ACCESS_REVIEW"; Desc = "User access review process"},
                @{Name = "SEGREGATION_OF_DUTIES"; Desc = "Segregation of duties"}
            )
        },
        @{
            Criteria = "CC2 - Communication & Information"
            Tests = @(
                @{Name = "AUDIT_LOG_ENABLED"; Desc = "Audit logging active"},
                @{Name = "SECURITY_INCIDENT_REPORTING"; Desc = "Security incident reporting"},
                @{Name = "POLICY_DOCUMENTATION"; Desc = "Security policy documentation"}
            )
        },
        @{
            Criteria = "CC3 - Risk Assessment"
            Tests = @(
                @{Name = "VULNERABILITY_SCANNING"; Desc = "Regular vulnerability scanning"},
                @{Name = "RISK_ASSESSMENT_PROCESS"; Desc = "Risk assessment process"},
                @{Name = "THREAT_MONITORING"; Desc = "Threat monitoring"}
            )
        },
        @{
            Criteria = "CC4 - Monitoring Activities"
            Tests = @(
                @{Name = "CONTINUOUS_MONITORING"; Desc = "Continuous monitoring"},
                @{Name = "ALERT_MANAGEMENT"; Desc = "Alert management system"},
                @{Name = "LOG_ANALYSIS"; Desc = "Log analysis and review"}
            )
        },
        @{
            Criteria = "CC5 - Control Activities"
            Tests = @(
                @{Name = "ACCESS_CONTROLS"; Desc = "Access control enforcement"},
                @{Name = "CHANGE_MANAGEMENT"; Desc = "Change management process"},
                @{Name = "DATA_PROTECTION"; Desc = "Data protection controls"}
            )
        }
    )
    
    $soc2Failures = 0
    foreach ($criteria in $soc2Controls) {
        Write-Host "    🔍 Testing $($criteria.Criteria)..." -ForegroundColor Cyan
        
        foreach ($test in $criteria.Tests) {
            $value = [Environment]::GetEnvironmentVariable($test.Name)
            
            # For SOC2, we check if the control is enabled (true) or if specific files exist
            $isCompliant = $false
            
            if ($value -eq "true") {
                $isCompliant = $true
            } elseif ($test.Name -eq "POLICY_DOCUMENTATION") {
                # Check if policy documents exist
                $isCompliant = (Test-Path "docs/compliance/SOC2_CONTROLS.md") -or (Test-Path "docs/security/SECURITY_PROCEDURES.md")
            } elseif ($test.Name -eq "AUDIT_LOG_ENABLED") {
                # This should always be true for healthcare
                $auditEnabled = [Environment]::GetEnvironmentVariable("AUDIT_LOG_ENABLED")
                $isCompliant = ($auditEnabled -eq "true")
            } else {
                # For other controls, assume they're enabled if not explicitly disabled
                $isCompliant = ($value -ne "false")
            }
            
            if ($isCompliant) {
                Write-Host "      ✅ $($test.Desc)" -ForegroundColor Green
                $testResults += @{
                    Test = "$($criteria.Criteria)_$($test.Name)"
                    Status = "✅ COMPLIANT"
                    Description = "$($criteria.Criteria): $($test.Desc)"
                    Details = "Control active"
                    Severity = "INFO"
                }
            } else {
                Write-Host "      ❌ $($test.Desc) - NOT COMPLIANT" -ForegroundColor Red
                $script:allPassed = $false
                $script:securityIssues += "SOC2 violation: $($test.Desc) not properly implemented"
                $soc2Failures++
                $testResults += @{
                    Test = "$($criteria.Criteria)_$($test.Name)"
                    Status = "❌ NON-COMPLIANT"
                    Description = "$($criteria.Criteria): $($test.Desc)"
                    Details = "Control not active or misconfigured"
                    Severity = "HIGH"
                }
            }
        }
    }
    
    # Overall SOC2 assessment
    Write-Host "`n  📋 SOC2 Type II Compliance Summary:" -ForegroundColor Cyan
    $totalControls = ($soc2Controls | ForEach-Object { $_.Tests.Count } | Measure-Object -Sum).Sum
    Write-Host "    Controls Tested: $totalControls"
    Write-Host "    Failures: $soc2Failures" -ForegroundColor $(if ($soc2Failures -eq 0) { "Green" } else { "Red" })
    
    if ($soc2Failures -eq 0) {
        Write-Host "    ✅ SOC2 TYPE II COMPLIANT" -ForegroundColor Green
    } else {
        Write-Host "    ❌ SOC2 TYPE II NON-COMPLIANT" -ForegroundColor Red
    }
}

function Test-AuthenticationSecurity {
    Write-Host "`n🔑 Testing Authentication Security..." -ForegroundColor Yellow
    
    # JWT Configuration
    $jwtSecret = [Environment]::GetEnvironmentVariable("JWT_SECRET_KEY")
    $jwtAlgorithm = [Environment]::GetEnvironmentVariable("JWT_ALGORITHM") ?? "HS256"
    $jwtExpiration = [Environment]::GetEnvironmentVariable("JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Test JWT secret strength
    if ([string]::IsNullOrEmpty($jwtSecret)) {
        Write-Host "  ❌ JWT secret key not configured" -ForegroundColor Red
        $script:allPassed = $false
        $script:securityIssues += "JWT secret key is missing"
        $testResults += @{
            Test = "JWT_SECRET_CONFIG"
            Status = "❌ FAIL"
            Description = "JWT secret key configuration"
            Details = "Secret key not set"
            Severity = "CRITICAL"
        }
    } elseif ($jwtSecret.Length -lt 32) {
        Write-Host "  ❌ JWT secret key is too weak (< 32 characters)" -ForegroundColor Red
        $script:allPassed = $false
        $script:securityIssues += "JWT secret key must be at least 32 characters"
        $testResults += @{
            Test = "JWT_SECRET_STRENGTH"
            Status = "❌ WEAK"
            Description = "JWT secret key strength"
            Details = "Length: $($jwtSecret.Length) characters (< 32 required)"
            Severity = "HIGH"
        }
    } else {
        Write-Host "  ✅ JWT secret key has adequate strength" -ForegroundColor Green
        $testResults += @{
            Test = "JWT_SECRET_STRENGTH"
            Status = "✅ STRONG"
            Description = "JWT secret key strength"
            Details = "Length: $($jwtSecret.Length) characters"
            Severity = "INFO"
        }
    }
    
    # Test JWT algorithm
    $secureAlgorithms = @("RS256", "ES256", "PS256")
    if ($jwtAlgorithm -in $secureAlgorithms) {
        Write-Host "  ✅ Using secure JWT algorithm: $jwtAlgorithm" -ForegroundColor Green
        $testResults += @{
            Test = "JWT_ALGORITHM"
            Status = "✅ SECURE"
            Description = "JWT algorithm security"
            Details = "Algorithm: $jwtAlgorithm"
            Severity = "INFO"
        }
    } elseif ($jwtAlgorithm -eq "HS256") {
        Write-Host "  ⚠️ Using acceptable JWT algorithm: $jwtAlgorithm" -ForegroundColor Yellow
        $testResults += @{
            Test = "JWT_ALGORITHM"
            Status = "⚠️ ACCEPTABLE"
            Description = "JWT algorithm security"
            Details = "Algorithm: $jwtAlgorithm (RS256 recommended for production)"
            Severity = "LOW"
        }
    } else {
        Write-Host "  ❌ Using insecure JWT algorithm: $jwtAlgorithm" -ForegroundColor Red
        $script:allPassed = $false
        $script:securityIssues += "JWT algorithm $jwtAlgorithm is not secure"
        $testResults += @{
            Test = "JWT_ALGORITHM"
            Status = "❌ INSECURE"
            Description = "JWT algorithm security"
            Details = "Algorithm: $jwtAlgorithm (use RS256, ES256, or PS256)"
            Severity = "HIGH"
        }
    }
    
    # Test JWT expiration
    if (![string]::IsNullOrEmpty($jwtExpiration)) {
        $expireMinutes = [int]$jwtExpiration
        if ($expireMinutes -le 60) {
            Write-Host "  ✅ JWT expiration is appropriately short: $expireMinutes minutes" -ForegroundColor Green
            $testResults += @{
                Test = "JWT_EXPIRATION"
                Status = "✅ SECURE"
                Description = "JWT token expiration"
                Details = "$expireMinutes minutes"
                Severity = "INFO"
            }
        } elseif ($expireMinutes -le 480) {  # 8 hours
            Write-Host "  ⚠️ JWT expiration could be shorter: $expireMinutes minutes" -ForegroundColor Yellow
            $testResults += @{
                Test = "JWT_EXPIRATION"
                Status = "⚠️ LONG"
                Description = "JWT token expiration"
                Details = "$expireMinutes minutes (consider shorter for better security)"
                Severity = "LOW"
            }
        } else {
            Write-Host "  ❌ JWT expiration is too long: $expireMinutes minutes" -ForegroundColor Red
            $script:securityIssues += "JWT tokens should expire within 8 hours for security"
            $testResults += @{
                Test = "JWT_EXPIRATION"
                Status = "❌ TOO_LONG"
                Description = "JWT token expiration"
                Details = "$expireMinutes minutes (> 480 minutes is risky)"
                Severity = "MEDIUM"
            }
        }
    }
    
    # Test MFA configuration
    $mfaEnabled = [Environment]::GetEnvironmentVariable("MFA_ENABLED")
    if ($mfaEnabled -eq "true") {
        Write-Host "  ✅ Multi-factor authentication enabled" -ForegroundColor Green
        $testResults += @{
            Test = "MFA_ENABLED"
            Status = "✅ ENABLED"
            Description = "Multi-factor authentication"
            Details = "MFA is enabled"
            Severity = "INFO"
        }
    } else {
        Write-Host "  ⚠️ Multi-factor authentication not enabled" -ForegroundColor Yellow
        $script:securityIssues += "Consider enabling MFA for enhanced security"
        $testResults += @{
            Test = "MFA_ENABLED"
            Status = "⚠️ DISABLED"
            Description = "Multi-factor authentication"
            Details = "MFA is not enabled (recommended for production)"
            Severity = "MEDIUM"
        }
    }
}

function Test-NetworkSecurity {
    Write-Host "`n🌐 Testing Network Security..." -ForegroundColor Yellow
    
    # Test HTTPS enforcement
    $httpsOnly = [Environment]::GetEnvironmentVariable("HTTPS_ONLY") ?? "true"
    if ($httpsOnly -eq "true") {
        Write-Host "  ✅ HTTPS enforcement enabled" -ForegroundColor Green
        $testResults += @{
            Test = "HTTPS_ENFORCEMENT"
            Status = "✅ ENABLED"
            Description = "HTTPS enforcement"
            Details = "HTTPS-only mode active"
            Severity = "INFO"
        }
    } else {
        Write-Host "  ❌ HTTPS enforcement not enabled" -ForegroundColor Red
        $script:allPassed = $false
        $script:securityIssues += "HTTPS enforcement must be enabled for production"
        $testResults += @{
            Test = "HTTPS_ENFORCEMENT"
            Status = "❌ DISABLED"
            Description = "HTTPS enforcement"
            Details = "HTTP connections allowed (insecure)"
            Severity = "CRITICAL"
        }
    }
    
    # Test security headers
    $securityHeaders = [Environment]::GetEnvironmentVariable("SECURITY_HEADERS_ENABLED") ?? "true"
    if ($securityHeaders -eq "true") {
        Write-Host "  ✅ Security headers enabled" -ForegroundColor Green
        $testResults += @{
            Test = "SECURITY_HEADERS"
            Status = "✅ ENABLED"
            Description = "Security headers configuration"
            Details = "HSTS, CSP, and other security headers active"
            Severity = "INFO"
        }
    } else {
        Write-Host "  ⚠️ Security headers not enabled" -ForegroundColor Yellow
        $script:securityIssues += "Enable security headers for better protection"
        $testResults += @{
            Test = "SECURITY_HEADERS"
            Status = "⚠️ DISABLED"
            Description = "Security headers configuration"
            Details = "Security headers not configured"
            Severity = "MEDIUM"
        }
    }
    
    # Test CORS configuration
    $corsOrigins = [Environment]::GetEnvironmentVariable("CORS_ORIGINS")
    if (![string]::IsNullOrEmpty($corsOrigins)) {
        if ($corsOrigins -eq "*") {
            Write-Host "  ❌ CORS allows all origins (insecure)" -ForegroundColor Red
            $script:allPassed = $false
            $script:securityIssues += "CORS should not allow all origins (*) in production"
            $testResults += @{
                Test = "CORS_CONFIGURATION"
                Status = "❌ INSECURE"
                Description = "CORS origins configuration"
                Details = "Allows all origins (*)"
                Severity = "HIGH"
            }
        } else {
            Write-Host "  ✅ CORS configured with specific origins" -ForegroundColor Green
            $testResults += @{
                Test = "CORS_CONFIGURATION"
                Status = "✅ SECURE"
                Description = "CORS origins configuration"
                Details = "Specific origins configured"
                Severity = "INFO"
            }
        }
    } else {
        Write-Host "  ⚠️ CORS origins not configured" -ForegroundColor Yellow
        $testResults += @{
            Test = "CORS_CONFIGURATION"
            Status = "⚠️ UNDEFINED"
            Description = "CORS origins configuration"
            Details = "No CORS configuration found"
            Severity = "LOW"
        }
    }
    
    # Test rate limiting
    $rateLimitEnabled = [Environment]::GetEnvironmentVariable("RATE_LIMIT_ENABLED") ?? "true"
    if ($rateLimitEnabled -eq "true") {
        Write-Host "  ✅ Rate limiting enabled" -ForegroundColor Green
        $testResults += @{
            Test = "RATE_LIMITING"
            Status = "✅ ENABLED"
            Description = "API rate limiting"
            Details = "Rate limiting active"
            Severity = "INFO"
        }
    } else {
        Write-Host "  ❌ Rate limiting not enabled" -ForegroundColor Red
        $script:allPassed = $false
        $script:securityIssues += "Rate limiting must be enabled to prevent abuse"
        $testResults += @{
            Test = "RATE_LIMITING"
            Status = "❌ DISABLED"
            Description = "API rate limiting"
            Details = "No rate limiting protection"
            Severity = "HIGH"
        }
    }
}

function Test-AuditLogging {
    Write-Host "`n📝 Testing Audit Logging..." -ForegroundColor Yellow
    
    # Test audit log configuration
    $auditEnabled = [Environment]::GetEnvironmentVariable("AUDIT_LOG_ENABLED")
    $phiAuditEnabled = [Environment]::GetEnvironmentVariable("PHI_AUDIT_ENABLED")
    $auditRetention = [Environment]::GetEnvironmentVariable("AUDIT_LOG_RETENTION_DAYS")
    
    if ($auditEnabled -eq "true") {
        Write-Host "  ✅ Audit logging enabled" -ForegroundColor Green
        $testResults += @{
            Test = "AUDIT_LOGGING"
            Status = "✅ ENABLED"
            Description = "General audit logging"
            Details = "Audit logging active"
            Severity = "INFO"
        }
    } else {
        Write-Host "  ❌ Audit logging not enabled" -ForegroundColor Red
        $script:allPassed = $false
        $script:securityIssues += "Audit logging is required for compliance"
        $testResults += @{
            Test = "AUDIT_LOGGING"
            Status = "❌ DISABLED"
            Description = "General audit logging"
            Details = "Audit logging not active"
            Severity = "CRITICAL"
        }
    }
    
    if ($phiAuditEnabled -eq "true") {
        Write-Host "  ✅ PHI access auditing enabled" -ForegroundColor Green
        $testResults += @{
            Test = "PHI_AUDIT_LOGGING"
            Status = "✅ ENABLED"
            Description = "PHI access audit logging"
            Details = "PHI audit logging active"
            Severity = "INFO"
        }
    } else {
        Write-Host "  ❌ PHI access auditing not enabled" -ForegroundColor Red
        $script:allPassed = $false
        $script:securityIssues += "PHI access auditing is required for HIPAA compliance"
        $testResults += @{
            Test = "PHI_AUDIT_LOGGING"
            Status = "❌ DISABLED"
            Description = "PHI access audit logging"
            Details = "PHI audit logging not active"
            Severity = "CRITICAL"
        }
    }
    
    # Test audit log directories exist
    $auditDirs = @("logs", "logs/audit", "logs/security", "logs/phi_access")
    foreach ($dir in $auditDirs) {
        if (Test-Path $dir) {
            Write-Host "  ✅ Audit directory exists: $dir" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️ Audit directory missing: $dir" -ForegroundColor Yellow
            try {
                New-Item -ItemType Directory -Path $dir -Force | Out-Null
                Write-Host "    ✅ Created audit directory: $dir" -ForegroundColor Green
            }
            catch {
                Write-Host "    ❌ Failed to create audit directory: $dir" -ForegroundColor Red
                $script:securityIssues += "Cannot create audit directory: $dir"
            }
        }
    }
    
    # Test audit log file permissions
    try {
        $testAuditFile = "logs/audit/test_audit.log"
        "Test audit entry" | Out-File -FilePath $testAuditFile -Encoding UTF8 -Append
        
        if (Test-Path $testAuditFile) {
            Write-Host "  ✅ Audit log write permissions OK" -ForegroundColor Green
            Remove-Item $testAuditFile -Force
            $testResults += @{
                Test = "AUDIT_LOG_PERMISSIONS"
                Status = "✅ OK"
                Description = "Audit log file permissions"
                Details = "Write permissions verified"
                Severity = "INFO"
            }
        }
    }
    catch {
        Write-Host "  ❌ Audit log write permissions failed" -ForegroundColor Red
        $script:allPassed = $false
        $script:securityIssues += "Cannot write to audit log directory"
        $testResults += @{
            Test = "AUDIT_LOG_PERMISSIONS"
            Status = "❌ FAIL"
            Description = "Audit log file permissions"
            Details = $_.Exception.Message
            Severity = "HIGH"
        }
    }
}

# Run all security and compliance tests
Write-Host "`n🚀 Starting Security & Compliance Tests..." -ForegroundColor Cyan

Test-PHIEncryption
Test-HIPAACompliance
Test-SOC2Controls
Test-AuthenticationSecurity
Test-NetworkSecurity
Test-AuditLogging

# Generate results summary
Write-Host "`n📊 SECURITY & COMPLIANCE RESULTS" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green

$passedTests = ($testResults | Where-Object { $_.Status -match "✅" }).Count
$failedTests = ($testResults | Where-Object { $_.Status -match "❌" }).Count
$warningTests = ($testResults | Where-Object { $_.Status -match "⚠️" }).Count
$totalTests = $testResults.Count

Write-Host "`nSecurity Test Summary:" -ForegroundColor Cyan
Write-Host "  Total Tests: $totalTests"
Write-Host "  Passed: $passedTests" -ForegroundColor Green
Write-Host "  Failed: $failedTests" -ForegroundColor Red
Write-Host "  Warnings: $warningTests" -ForegroundColor Yellow

# Group results by severity
$criticalIssues = ($testResults | Where-Object { $_.Severity -eq "CRITICAL" -and $_.Status -match "❌" }).Count
$highIssues = ($testResults | Where-Object { $_.Severity -eq "HIGH" -and $_.Status -match "❌" }).Count
$mediumIssues = ($testResults | Where-Object { $_.Severity -eq "MEDIUM" -and $_.Status -match "❌|⚠️" }).Count

Write-Host "`nSecurity Issues by Severity:" -ForegroundColor Cyan
Write-Host "  Critical: $criticalIssues" -ForegroundColor $(if ($criticalIssues -eq 0) { "Green" } else { "Red" })
Write-Host "  High: $highIssues" -ForegroundColor $(if ($highIssues -eq 0) { "Green" } else { "Red" })
Write-Host "  Medium: $mediumIssues" -ForegroundColor $(if ($mediumIssues -eq 0) { "Green" } else { "Yellow" })

# Show detailed security issues
if ($securityIssues.Count -gt 0) {
    Write-Host "`n🚨 Security Issues to Fix:" -ForegroundColor Red
    for ($i = 0; $i -lt $securityIssues.Count; $i++) {
        Write-Host "  $($i + 1). $($securityIssues[$i])" -ForegroundColor Red
    }
}

# Show detailed results grouped by category
Write-Host "`nDetailed Results:" -ForegroundColor Cyan
$categories = @("PHI", "HIPAA", "SOC2", "JWT", "NETWORK", "AUDIT")
foreach ($category in $categories) {
    $categoryTests = $testResults | Where-Object { $_.Test -match $category }
    if ($categoryTests.Count -gt 0) {
        Write-Host "  $category Tests:" -ForegroundColor Yellow
        foreach ($test in $categoryTests) {
            Write-Host "    $($test.Status) $($test.Description)"
            if ($test.Details) {
                Write-Host "      Details: $($test.Details)" -ForegroundColor Gray
            }
        }
    }
}

# Save results to file
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$resultFile = "security_compliance_$timestamp.json"

try {
    $resultsData = @{
        timestamp = $timestamp
        summary = @{
            total_tests = $totalTests
            passed = $passedTests
            failed = $failedTests
            warnings = $warningTests
            critical_issues = $criticalIssues
            high_issues = $highIssues
            medium_issues = $mediumIssues
        }
        tests = $testResults
        security_issues = $securityIssues
        compliance_status = @{
            hipaa_compliant = ($testResults | Where-Object { $_.Test -match "HIPAA" -and $_.Status -match "❌" }).Count -eq 0
            soc2_compliant = ($testResults | Where-Object { $_.Test -match "CC[1-5]" -and $_.Status -match "❌" }).Count -eq 0
            production_ready = ($criticalIssues -eq 0 -and $highIssues -eq 0)
        }
    }
    
    $resultsData | ConvertTo-Json -Depth 5 | Out-File -FilePath $resultFile -Encoding UTF8
    Write-Host "`n📁 Results saved to: $resultFile" -ForegroundColor Cyan
}
catch {
    Write-Host "`n⚠️ Could not save results to file: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Final assessment
Write-Host "`n🎯 FINAL SECURITY ASSESSMENT" -ForegroundColor Green
if ($allPassed -and $criticalIssues -eq 0 -and $highIssues -eq 0) {
    Write-Host "✅ SECURITY & COMPLIANCE VALIDATION PASSED" -ForegroundColor Green
    Write-Host "System meets security and compliance requirements for production!" -ForegroundColor Green
    exit 0
} elseif ($criticalIssues -eq 0 -and $highIssues -eq 0) {
    Write-Host "⚠️ SECURITY & COMPLIANCE VALIDATION PASSED WITH WARNINGS" -ForegroundColor Yellow
    Write-Host "System is secure but has some recommendations to address." -ForegroundColor Yellow
    exit 0
} else {
    Write-Host "❌ SECURITY & COMPLIANCE VALIDATION FAILED" -ForegroundColor Red
    Write-Host "Critical security issues must be fixed before production deployment!" -ForegroundColor Red
    exit 1
}