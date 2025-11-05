# VitalCore Encryption Key Setup Guide

## 🔐 CRITICAL: PHI Encryption Key Management

This document describes the **MOST CRITICAL** security configuration in VitalCore: the encryption key management system that protects all Protected Health Information (PHI).

---

## ⚠️ CRITICAL WARNINGS

### Data Loss Prevention

- **Loss of encryption keys = PERMANENT DATA LOSS**
- ALL encrypted PHI becomes permanently inaccessible if keys are lost
- Keys MUST persist across application restarts
- **DO NOT** use random key generation in production
- **DO NOT** commit encryption keys to version control

### Compliance Requirements

- **HIPAA**: Encryption keys are considered electronic PHI and must be protected accordingly
- **SOC2**: Key management procedures must be documented and audited
- **GDPR**: Key access must be logged and controlled

---

## 🎯 Quick Start

### 1. Generate Encryption Keys

```bash
# From the VitalCore root directory
python scripts/generate_encryption_keys.py
```

This will generate all required encryption keys with proper cryptographic security.

### 2. Store Keys Securely

**IMMEDIATELY** after generation:

1. Copy keys to your `.env` file
2. Store backup copy in password manager (1Password, LastPass, etc.)
3. Store offline backup in secure physical location
4. Document key location in disaster recovery plan

### 3. Set Environment Variables

**Development (.env file):**

```bash
# Copy generated keys to .env
PHI_ENCRYPTION_KEY=<generated-key>
ENCRYPTION_KEY=<generated-key>
ENCRYPTION_SALT=<generated-key>
JWT_SECRET_KEY=<generated-key>
SECRET_KEY=<generated-key>
```

**Production (environment variables):**

```bash
# Export to environment
export PHI_ENCRYPTION_KEY="<generated-key>"
export ENCRYPTION_KEY="<generated-key>"
export ENCRYPTION_SALT="<generated-key>"
export JWT_SECRET_KEY="<generated-key>"
export SECRET_KEY="<generated-key>"
```

### 4. Verify Configuration

```bash
# Start the application
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Application will fail to start if keys are missing
# This is INTENTIONAL to prevent data loss
```

---

## 📋 Required Encryption Keys

### PHI_ENCRYPTION_KEY (REQUIRED)

- **Purpose**: Primary encryption key for all PHI data
- **Length**: Minimum 32 characters (256-bit security)
- **Algorithm**: Used with AES-256-GCM for PHI encryption
- **Criticality**: **HIGHEST** - Loss causes permanent PHI data loss

```bash
PHI_ENCRYPTION_KEY=<32+ character base64 urlsafe key>
```

### ENCRYPTION_KEY (REQUIRED)

- **Purpose**: General data encryption at rest
- **Length**: Minimum 32 characters (256-bit security)
- **Algorithm**: Used with Fernet and AES-256
- **Criticality**: **HIGH** - Loss causes data loss

```bash
ENCRYPTION_KEY=<32+ character base64 urlsafe key>
```

### ENCRYPTION_SALT (REQUIRED)

- **Purpose**: Salt for key derivation functions (PBKDF2)
- **Length**: Minimum 32 characters
- **Algorithm**: PBKDF2-HMAC-SHA256
- **Criticality**: **HIGH** - Required for decryption

```bash
ENCRYPTION_SALT=<32+ character base64 urlsafe key>
```

### JWT_SECRET_KEY (REQUIRED)

- **Purpose**: JWT token signing and verification
- **Length**: Minimum 32 characters
- **Algorithm**: RS256 / HS256
- **Criticality**: **MEDIUM** - Session security

```bash
JWT_SECRET_KEY=<32+ character base64 urlsafe key>
```

### SECRET_KEY (REQUIRED)

- **Purpose**: General application security functions
- **Length**: Minimum 32 characters
- **Algorithm**: Various security functions
- **Criticality**: **MEDIUM** - Application security

```bash
SECRET_KEY=<32+ character base64 urlsafe key>
```

### PHI_ENCRYPTION_KEY_ROTATION (OPTIONAL)

- **Purpose**: Secondary key for key rotation support
- **Length**: Minimum 32 characters
- **Algorithm**: AES-256-GCM
- **Criticality**: **HIGH** - Enables zero-downtime key rotation

```bash
PHI_ENCRYPTION_KEY_ROTATION=<32+ character base64 urlsafe key>
```

---

## 🔄 Key Rotation Procedure

### Why Rotate Keys?

- Compliance requirement (recommended annually)
- Security best practice
- Limit impact of potential key compromise
- Meet SOC2 Type II requirements

### Rotation Steps

#### Phase 1: Preparation

```bash
# 1. Generate new encryption keys
python scripts/generate_encryption_keys.py

# 2. Set the new key as rotation key
export PHI_ENCRYPTION_KEY_ROTATION="<new-key>"

# 3. Restart application to load rotation key
```

#### Phase 2: Migration (Future Implementation)

```bash
# Run key rotation migration (to be implemented)
python scripts/rotate_encryption_keys.py

# This will:
# - Decrypt all PHI with old key (PHI_ENCRYPTION_KEY)
# - Re-encrypt all PHI with new key (PHI_ENCRYPTION_KEY_ROTATION)
# - Verify all data was successfully re-encrypted
# - Create backup of old encrypted data
```

#### Phase 3: Activation

```bash
# 1. Update primary key to rotation key
export PHI_ENCRYPTION_KEY="<new-key>"

# 2. Generate another rotation key for next rotation
python scripts/generate_encryption_keys.py
export PHI_ENCRYPTION_KEY_ROTATION="<newer-key>"

# 3. Archive old key securely (for disaster recovery)
# Keep old keys for at least 7 years (HIPAA requirement)
```

---

## 🏥 Production Deployment

### Recommended Architecture

#### AWS Deployment

```bash
# Use AWS Secrets Manager
aws secretsmanager create-secret \
  --name vitalcore/phi-encryption-key \
  --secret-string "<generated-key>"

# Retrieve in application startup
PHI_ENCRYPTION_KEY=$(aws secretsmanager get-secret-value \
  --secret-id vitalcore/phi-encryption-key \
  --query SecretString \
  --output text)
```

#### HashiCorp Vault

```bash
# Store in Vault
vault kv put secret/vitalcore \
  phi_encryption_key="<generated-key>" \
  encryption_key="<generated-key>" \
  encryption_salt="<generated-key>"

# Retrieve in application
vault kv get -field=phi_encryption_key secret/vitalcore
```

#### Docker/Kubernetes

```yaml
# docker-compose.yml (use Docker secrets)
version: '3.8'
services:
  vitalcore:
    image: vitalcore:latest
    secrets:
      - phi_encryption_key
    environment:
      - PHI_ENCRYPTION_KEY_FILE=/run/secrets/phi_encryption_key

secrets:
  phi_encryption_key:
    external: true
```

```yaml
# Kubernetes (use sealed secrets or external secrets operator)
apiVersion: v1
kind: Secret
metadata:
  name: vitalcore-encryption-keys
type: Opaque
stringData:
  PHI_ENCRYPTION_KEY: <base64-encoded-key>
  ENCRYPTION_KEY: <base64-encoded-key>
  ENCRYPTION_SALT: <base64-encoded-key>
```

### Environment-Specific Keys

**CRITICAL**: Use different keys for each environment!

- **Development**: Local `.env` file (rotate quarterly)
- **Staging**: Secrets manager (rotate monthly)
- **Production**: Hardware Security Module (HSM) backed secrets (rotate monthly)

**NEVER** use the same keys across environments!

---

## 🆘 Disaster Recovery

### Key Loss Scenarios

#### Scenario 1: Keys Lost, Database Intact

**Result**: **PERMANENT DATA LOSS** - No recovery possible

**Prevention**:
- Store keys in multiple secure locations
- Implement automated backup to secrets manager
- Maintain offline backups in secure physical location
- Test backup retrieval quarterly

#### Scenario 2: Database Lost, Keys Intact

**Result**: Recoverable from database backups

**Recovery**:
```bash
# 1. Restore database from backup
pg_restore -d vitalcore backup.sql

# 2. Start application with SAME encryption keys
export PHI_ENCRYPTION_KEY="<original-key>"

# 3. Verify data decryption
python scripts/verify_encryption.py
```

#### Scenario 3: Both Keys and Database Lost

**Result**: **CATASTROPHIC** - Complete data loss

**Prevention**:
- Implement 3-2-1 backup strategy
- Store keys and database backups in separate locations
- Test disaster recovery procedures quarterly
- Maintain offline encrypted backups

### Backup Strategy

#### Daily Automated Backups

```bash
# Backup database (encrypted)
pg_dump vitalcore | gpg --encrypt > backup-$(date +%Y%m%d).sql.gpg

# Backup encryption keys (encrypted, separate location)
# Store in password manager + offline backup
```

#### Key Backup Locations

1. **Primary**: Password manager (1Password, LastPass)
2. **Secondary**: Secrets manager (AWS Secrets Manager, Vault)
3. **Tertiary**: Offline encrypted USB drive (secure physical location)
4. **Quaternary**: Printed paper backup (bank safe deposit box)

### Testing Disaster Recovery

**Quarterly Verification**:

```bash
# 1. Retrieve keys from backup locations
# 2. Restore database from backup
# 3. Start application with backup keys
# 4. Verify data decryption
# 5. Document results
```

---

## 🔍 Verification and Testing

### Verify Keys Are Set

```bash
# Check if environment variables are set
python -c "from app.core.config import get_settings; settings = get_settings(); print('Keys configured:', bool(settings.PHI_ENCRYPTION_KEY))"
```

### Test Encryption/Decryption

```bash
# Run encryption test
python scripts/debug/debug_encryption.py
```

### Verify Application Fails Without Keys

```bash
# Remove keys from environment
unset PHI_ENCRYPTION_KEY
unset ENCRYPTION_KEY
unset ENCRYPTION_SALT

# Try to start application (should fail gracefully)
python -m uvicorn app.main:app

# Expected: ValidationError with clear error message
```

---

## 📊 Monitoring and Auditing

### Key Access Monitoring

```python
# All encryption key access is logged
# Review logs regularly for:
# - Unauthorized access attempts
# - Failed decryption attempts
# - Unusual encryption patterns
```

### Audit Requirements

**SOC2 Type II**:
- Document key management procedures
- Log all key access
- Quarterly access reviews
- Annual key rotation

**HIPAA**:
- Encrypt all PHI at rest and in transit
- Log all PHI access
- Maintain encryption key backup procedures
- 7-year key retention policy

---

## 🚨 Security Incidents

### Key Compromise Response

If you suspect encryption keys have been compromised:

1. **IMMEDIATE**: Revoke compromised keys
2. **IMMEDIATE**: Rotate to new keys using key rotation procedure
3. **24 HOURS**: Notify security team
4. **72 HOURS**: Notify affected parties if required by HIPAA Breach Notification Rule
5. **7 DAYS**: Complete incident report
6. **30 DAYS**: Implement additional safeguards

### Breach Notification Requirements

**HIPAA Breach Notification Rule**:
- Notify affected individuals within 60 days
- Notify HHS if breach affects 500+ individuals
- Document breach investigation and response

---

## 📞 Support and Questions

### Key Management Issues

1. Review this document thoroughly
2. Check application logs for specific errors
3. Verify environment variables are set correctly
4. Test key generation script
5. Contact security team if issues persist

### Emergency Contacts

- **Security Team**: security@vitalcore.health
- **On-Call Engineer**: oncall@vitalcore.health
- **Compliance Officer**: compliance@vitalcore.health

---

## 📚 Additional Resources

- [NIST Key Management Guidelines](https://csrc.nist.gov/publications/detail/sp/800-57-part-1/rev-5/final)
- [HIPAA Encryption Requirements](https://www.hhs.gov/hipaa/for-professionals/security/laws-regulations/index.html)
- [SOC2 Trust Services Criteria](https://www.aicpa.org/resources/landing/system-and-organization-controls-soc-suite-of-services)

---

## 🔖 Version History

- **v1.0** (2025-11-05): Initial encryption key management implementation
  - Disabled random key generation
  - Implemented required environment variable configuration
  - Added comprehensive validation and error handling
  - Created key generation script and documentation

---

**Last Updated**: 2025-11-05
**Document Owner**: Security Team
**Review Frequency**: Quarterly
