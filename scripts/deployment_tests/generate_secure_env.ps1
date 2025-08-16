# Generate Secure Environment Variables for Healthcare Platform
# Creates cryptographically secure keys and secrets for production deployment

Write-Host "🔐 Generating Secure Environment Variables" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green

# Function to generate secure random string
function Generate-SecureKey {
    param(
        [int]$Length = 64,
        [string]$Type = "base64"
    )
    
    $bytes = New-Object byte[] $Length
    $rng = [System.Security.Cryptography.RNGCryptoServiceProvider]::Create()
    $rng.GetBytes($bytes)
    
    switch ($Type) {
        "base64" { 
            return [Convert]::ToBase64String($bytes)
        }
        "hex" { 
            return [BitConverter]::ToString($bytes).Replace("-", "").ToLower()
        }
        "alphanumeric" {
            $chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
            $result = ""
            for ($i = 0; $i -lt $Length; $i++) {
                $result += $chars[$bytes[$i] % $chars.Length]
            }
            return $result
        }
        default { 
            return [Convert]::ToBase64String($bytes)
        }
    }
}

# Function to generate JWT key pair
function Generate-JWTKeys {
    Write-Host "Generating RSA key pair for JWT..." -ForegroundColor Yellow
    
    try {
        # Generate RSA key pair using .NET crypto
        $rsa = [System.Security.Cryptography.RSA]::Create(2048)
        
        # Export private key (PKCS#8 format)
        $privateKey = [Convert]::ToBase64String($rsa.ExportPkcs8PrivateKey())
        
        # Export public key (SubjectPublicKeyInfo format)  
        $publicKey = [Convert]::ToBase64String($rsa.ExportSubjectPublicKeyInfo())
        
        return @{
            PrivateKey = $privateKey
            PublicKey = $publicKey
        }
    }
    catch {
        Write-Host "⚠️ RSA key generation failed, using fallback method" -ForegroundColor Yellow
        # Fallback to secure random strings
        return @{
            PrivateKey = Generate-SecureKey -Length 64 -Type "base64"
            PublicKey = Generate-SecureKey -Length 64 -Type "base64"
        }
    }
}

Write-Host "`n🔑 Generating cryptographically secure keys..." -ForegroundColor Cyan

# Generate all required keys
$jwtKeys = Generate-JWTKeys
$secretKey = Generate-SecureKey -Length 64 -Type "base64"
$encryptionKey = Generate-SecureKey -Length 32 -Type "base64"  # AES-256 key
$phiEncryptionKey = Generate-SecureKey -Length 32 -Type "base64"  # PHI encryption
$databasePassword = Generate-SecureKey -Length 24 -Type "alphanumeric"
$redisPassword = Generate-SecureKey -Length 24 -Type "alphanumeric"
$minioAccessKey = Generate-SecureKey -Length 20 -Type "alphanumeric"
$minioSecretKey = Generate-SecureKey -Length 40 -Type "base64"
$auditSigningKey = Generate-SecureKey -Length 64 -Type "hex"
$cspNonce = Generate-SecureKey -Length 16 -Type "base64"

# Database URLs with secure passwords
$databaseUrl = "postgresql://postgres:${databasePassword}@localhost:5432/iris_db"
$testDatabaseUrl = "postgresql://postgres:${databasePassword}@localhost:5433/iris_test_db"
$redisUrl = "redis://:${redisPassword}@localhost:6379/0"

Write-Host "`n✅ Keys generated successfully!" -ForegroundColor Green

# Display the environment variables
Write-Host "`n📋 Environment Variables (copy and execute):" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Cyan

$envVars = @"
# Healthcare Platform - Secure Environment Variables
# Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss UTC")

# Core Application
`$env:SECRET_KEY = "$secretKey"
`$env:ENCRYPTION_KEY = "$encryptionKey"
`$env:ENVIRONMENT = "production"
`$env:DEBUG = "false"

# JWT Authentication
`$env:JWT_SECRET_KEY = "$($jwtKeys.PrivateKey)"
`$env:JWT_PUBLIC_KEY = "$($jwtKeys.PublicKey)"
`$env:JWT_ALGORITHM = "RS256"
`$env:JWT_ACCESS_TOKEN_EXPIRE_MINUTES = "60"
`$env:JWT_REFRESH_TOKEN_EXPIRE_DAYS = "7"

# Database Configuration
`$env:DATABASE_URL = "$databaseUrl"
`$env:TEST_DATABASE_URL = "$testDatabaseUrl"
`$env:DB_POOL_SIZE = "20"
`$env:DB_MAX_OVERFLOW = "30"

# Redis Configuration  
`$env:REDIS_URL = "$redisUrl"
`$env:REDIS_PASSWORD = "$redisPassword"

# PHI/PII Encryption (HIPAA Compliance)
`$env:PHI_ENCRYPTION_KEY = "$phiEncryptionKey"
`$env:PII_ENCRYPTION_KEY = "$phiEncryptionKey"
`$env:DATA_ENCRYPTION_ALGORITHM = "AES-256-GCM"

# MinIO Object Storage
`$env:MINIO_ACCESS_KEY = "$minioAccessKey"
`$env:MINIO_SECRET_KEY = "$minioSecretKey"
`$env:MINIO_ENDPOINT = "localhost:9000"
`$env:MINIO_SECURE = "false"

# SOC2 Audit Logging
`$env:AUDIT_SIGNING_KEY = "$auditSigningKey"
`$env:AUDIT_ENCRYPTION_ENABLED = "true"
`$env:SOC2_COMPLIANCE_MODE = "true"

# Security Headers
`$env:CSP_NONCE_KEY = "$cspNonce"
`$env:SECURITY_HEADERS_ENABLED = "true"
`$env:HSTS_MAX_AGE = "31536000"

# External APIs
`$env:IRIS_API_KEY = "your-iris-api-key-here"
`$env:IRIS_API_ENDPOINT = "https://api.iris.healthcare.gov"

# Monitoring & Logging
`$env:LOG_LEVEL = "INFO"
`$env:STRUCTURED_LOGGING = "true"
`$env:PROMETHEUS_ENABLED = "true"
`$env:METRICS_PORT = "9090"

# Performance
`$env:WORKERS = "4"
`$env:MAX_CONNECTIONS = "1000"
`$env:KEEPALIVE_TIMEOUT = "5"

# Development overrides (remove in production)
`$env:ALLOWED_ORIGINS = "http://localhost:3000,http://localhost:8000"
`$env:CORS_ENABLED = "true"
"@

Write-Output $envVars

# Save to file
$envFile = "secure_env_vars_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
$envVars | Out-File -FilePath $envFile -Encoding UTF8

Write-Host "`n💾 Environment variables saved to: $envFile" -ForegroundColor Green

# Create .env file for Docker
$dockerEnvContent = @"
# Healthcare Platform - Docker Environment Variables
# Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss UTC")
# IMPORTANT: This file contains sensitive keys - do not commit to version control!

SECRET_KEY=$secretKey
ENCRYPTION_KEY=$encryptionKey
ENVIRONMENT=production
DEBUG=false

JWT_SECRET_KEY=$($jwtKeys.PrivateKey)
JWT_PUBLIC_KEY=$($jwtKeys.PublicKey)
JWT_ALGORITHM=RS256

DATABASE_URL=$databaseUrl
REDIS_URL=$redisUrl

PHI_ENCRYPTION_KEY=$phiEncryptionKey
PII_ENCRYPTION_KEY=$phiEncryptionKey

MINIO_ACCESS_KEY=$minioAccessKey
MINIO_SECRET_KEY=$minioSecretKey

AUDIT_SIGNING_KEY=$auditSigningKey
SOC2_COMPLIANCE_MODE=true

CSP_NONCE_KEY=$cspNonce
SECURITY_HEADERS_ENABLED=true
"@

$dockerEnvFile = ".env.secure"
$dockerEnvContent | Out-File -FilePath $dockerEnvFile -Encoding UTF8

Write-Host "🐳 Docker .env file saved to: $dockerEnvFile" -ForegroundColor Green

# Security warnings
Write-Host "`n⚠️  SECURITY WARNINGS:" -ForegroundColor Red
Write-Host "🔒 These keys are cryptographically secure - store them safely!" -ForegroundColor Yellow
Write-Host "🚫 Never commit these keys to version control" -ForegroundColor Yellow  
Write-Host "🔄 Rotate keys regularly in production (every 90 days)" -ForegroundColor Yellow
Write-Host "🛡️  Use a secrets manager (Azure Key Vault, AWS Secrets Manager) in production" -ForegroundColor Yellow

Write-Host "`n🚀 Ready to execute! Copy the environment variables above and run:" -ForegroundColor Green
Write-Host ".\scripts\deployment_tests\quick_test.ps1" -ForegroundColor Cyan

# Generate quick setup command
Write-Host "`n⚡ Quick Setup Command:" -ForegroundColor Magenta
Write-Host "Copy and paste this single command to set all variables:" -ForegroundColor Gray

$quickSetup = @"
`$env:SECRET_KEY='$secretKey'; `$env:ENCRYPTION_KEY='$encryptionKey'; `$env:JWT_SECRET_KEY='$($jwtKeys.PrivateKey)'; `$env:DATABASE_URL='$databaseUrl'; `$env:REDIS_URL='$redisUrl'; `$env:PHI_ENCRYPTION_KEY='$phiEncryptionKey'; `$env:MINIO_ACCESS_KEY='$minioAccessKey'; `$env:MINIO_SECRET_KEY='$minioSecretKey'; `$env:AUDIT_SIGNING_KEY='$auditSigningKey'
"@

Write-Host $quickSetup -ForegroundColor White
Write-Host "`nAfter setting variables, run: .\scripts\deployment_tests\quick_test.ps1" -ForegroundColor Cyan