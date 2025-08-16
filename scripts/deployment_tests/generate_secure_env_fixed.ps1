# Generate Secure Environment Variables for Healthcare Platform
# Creates cryptographically secure keys and secrets for production deployment

Write-Host "Generate Secure Environment Variables" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

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

Write-Host ""
Write-Host "Generating cryptographically secure keys..." -ForegroundColor Cyan

# Generate all required keys
$secretKey = Generate-SecureKey -Length 64 -Type "base64"
$encryptionKey = Generate-SecureKey -Length 32 -Type "base64"
$jwtSecretKey = Generate-SecureKey -Length 64 -Type "base64"
$phiEncryptionKey = Generate-SecureKey -Length 32 -Type "base64"
$databasePassword = Generate-SecureKey -Length 24 -Type "alphanumeric"
$redisPassword = Generate-SecureKey -Length 24 -Type "alphanumeric"
$minioAccessKey = Generate-SecureKey -Length 20 -Type "alphanumeric"
$minioSecretKey = Generate-SecureKey -Length 40 -Type "base64"
$auditSigningKey = Generate-SecureKey -Length 64 -Type "hex"

# Database URLs with secure passwords
$databaseUrl = "postgresql://postgres:password@localhost:5432/iris_db"
$redisUrl = "redis://localhost:6379/0"

Write-Host ""
Write-Host "Keys generated successfully!" -ForegroundColor Green

# Display the environment variables
Write-Host ""
Write-Host "Environment Variables (copy and execute):" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "# Core Application Settings" -ForegroundColor Yellow
Write-Host "`$env:SECRET_KEY = '$secretKey'"
Write-Host "`$env:ENCRYPTION_KEY = '$encryptionKey'"
Write-Host "`$env:ENVIRONMENT = 'development'"
Write-Host "`$env:DEBUG = 'true'"

Write-Host ""
Write-Host "# Authentication & JWT" -ForegroundColor Yellow
Write-Host "`$env:JWT_SECRET_KEY = '$jwtSecretKey'"

Write-Host ""
Write-Host "# Database Configuration" -ForegroundColor Yellow
Write-Host "`$env:DATABASE_URL = '$databaseUrl'"
Write-Host "`$env:REDIS_URL = '$redisUrl'"

Write-Host ""
Write-Host "# PHI/PII Encryption (HIPAA Compliance)" -ForegroundColor Yellow
Write-Host "`$env:PHI_ENCRYPTION_KEY = '$phiEncryptionKey'"
Write-Host "`$env:PII_ENCRYPTION_KEY = '$phiEncryptionKey'"

Write-Host ""
Write-Host "# MinIO Object Storage" -ForegroundColor Yellow
Write-Host "`$env:MINIO_ACCESS_KEY = '$minioAccessKey'"
Write-Host "`$env:MINIO_SECRET_KEY = '$minioSecretKey'"

Write-Host ""
Write-Host "# SOC2 Audit Logging" -ForegroundColor Yellow
Write-Host "`$env:AUDIT_SIGNING_KEY = '$auditSigningKey'"
Write-Host "`$env:SOC2_COMPLIANCE_MODE = 'true'"

# Generate timestamp for file names
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$envFile = "secure_env_vars_$timestamp.txt"

# Create content for file
$envVarsContent = @"
# Healthcare Platform - Secure Environment Variables
# Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

# Core Application
`$env:SECRET_KEY = "$secretKey"
`$env:ENCRYPTION_KEY = "$encryptionKey"
`$env:ENVIRONMENT = "development"
`$env:DEBUG = "true"

# JWT Authentication
`$env:JWT_SECRET_KEY = "$jwtSecretKey"

# Database Configuration
`$env:DATABASE_URL = "$databaseUrl"
`$env:REDIS_URL = "$redisUrl"

# PHI/PII Encryption (HIPAA Compliance)
`$env:PHI_ENCRYPTION_KEY = "$phiEncryptionKey"
`$env:PII_ENCRYPTION_KEY = "$phiEncryptionKey"

# MinIO Object Storage
`$env:MINIO_ACCESS_KEY = "$minioAccessKey"
`$env:MINIO_SECRET_KEY = "$minioSecretKey"

# SOC2 Audit Logging
`$env:AUDIT_SIGNING_KEY = "$auditSigningKey"
`$env:SOC2_COMPLIANCE_MODE = "true"
"@

# Save to file
$envVarsContent | Out-File -FilePath $envFile -Encoding UTF8

Write-Host ""
Write-Host "Environment variables saved to: $envFile" -ForegroundColor Green

# Create .env file for Docker
$dockerEnvContent = @"
# Healthcare Platform - Docker Environment Variables
# Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

SECRET_KEY=$secretKey
ENCRYPTION_KEY=$encryptionKey
ENVIRONMENT=development
DEBUG=true

JWT_SECRET_KEY=$jwtSecretKey

DATABASE_URL=$databaseUrl
REDIS_URL=$redisUrl

PHI_ENCRYPTION_KEY=$phiEncryptionKey
PII_ENCRYPTION_KEY=$phiEncryptionKey

MINIO_ACCESS_KEY=$minioAccessKey
MINIO_SECRET_KEY=$minioSecretKey

AUDIT_SIGNING_KEY=$auditSigningKey
SOC2_COMPLIANCE_MODE=true
"@

$dockerEnvFile = ".env.secure"
$dockerEnvContent | Out-File -FilePath $dockerEnvFile -Encoding UTF8

Write-Host "Docker .env file saved to: $dockerEnvFile" -ForegroundColor Green

# Security warnings
Write-Host ""
Write-Host "SECURITY WARNINGS:" -ForegroundColor Red
Write-Host "- These keys are cryptographically secure - store them safely!" -ForegroundColor Yellow
Write-Host "- Never commit these keys to version control" -ForegroundColor Yellow
Write-Host "- Rotate keys regularly in production (every 90 days)" -ForegroundColor Yellow

Write-Host ""
Write-Host "QUICK SETUP COMMAND:" -ForegroundColor Magenta
Write-Host "Copy and paste this to set all variables at once:" -ForegroundColor Gray

# Generate single-line command
$quickCommand = "`$env:SECRET_KEY='$secretKey'; `$env:ENCRYPTION_KEY='$encryptionKey'; `$env:JWT_SECRET_KEY='$jwtSecretKey'; `$env:DATABASE_URL='$databaseUrl'; `$env:REDIS_URL='$redisUrl'; `$env:PHI_ENCRYPTION_KEY='$phiEncryptionKey'; `$env:MINIO_ACCESS_KEY='$minioAccessKey'; `$env:MINIO_SECRET_KEY='$minioSecretKey'; `$env:AUDIT_SIGNING_KEY='$auditSigningKey'; `$env:SOC2_COMPLIANCE_MODE='true'"

Write-Host $quickCommand -ForegroundColor White

Write-Host ""
Write-Host "After setting variables, run: .\scripts\deployment_tests\quick_test.ps1" -ForegroundColor Cyan