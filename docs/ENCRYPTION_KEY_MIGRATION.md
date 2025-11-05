# Encryption Key Migration Guide

## 🚨 CRITICAL: Safe Deployment of Encryption Key Changes

This guide explains how to safely deploy the new persistent encryption key management system to existing VitalCore deployments **WITHOUT DATA LOSS**.

---

## ⚠️ CRITICAL WARNINGS

### Before You Start

- **DO NOT** deploy this change without following this guide exactly
- **DO NOT** restart the application without setting encryption keys
- **DO NOT** generate new keys for existing deployments
- **Existing encrypted data CANNOT be decrypted with new keys**

### What Changed

**BEFORE** (DANGEROUS):
- Encryption keys were randomly generated on every application restart
- ALL encrypted PHI data became inaccessible after any restart
- This caused **PERMANENT DATA LOSS**

**AFTER** (SAFE):
- Encryption keys are required from environment variables
- Keys persist across application restarts
- Application **FAILS TO START** without proper keys (prevents data loss)

---

## 📋 Migration Scenarios

### Scenario 1: New Deployment (No Existing Data)

**Safe**: Generate new keys and deploy

```bash
# 1. Generate new encryption keys
python scripts/generate_encryption_keys.py

# 2. Add keys to environment
export PHI_ENCRYPTION_KEY="<generated-key>"
export ENCRYPTION_KEY="<generated-key>"
export ENCRYPTION_SALT="<generated-key>"
export JWT_SECRET_KEY="<generated-key>"
export SECRET_KEY="<generated-key>"

# 3. Start application
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Result**: ✅ Safe - No existing data to lose

---

### Scenario 2: Existing Deployment WITHOUT Encrypted Data

**Safe**: Generate new keys and deploy

If you have an existing deployment but haven't encrypted any PHI data yet:

```bash
# 1. Verify no encrypted data exists
# Check database for encrypted records

# 2. Generate new encryption keys
python scripts/generate_encryption_keys.py

# 3. Deploy with new keys
export PHI_ENCRYPTION_KEY="<generated-key>"
export ENCRYPTION_KEY="<generated-key>"
export ENCRYPTION_SALT="<generated-key>"
export JWT_SECRET_KEY="<generated-key>"
export SECRET_KEY="<generated-key>"

# 4. Restart application
```

**Result**: ✅ Safe - No encrypted data exists

---

### Scenario 3: Existing Deployment WITH Encrypted Data

**CRITICAL**: This is the most dangerous scenario

#### ⚠️ STOP AND READ THIS CAREFULLY

**THE PROBLEM**:
- Your application has been generating random encryption keys on every restart
- Each time it restarted, it encrypted NEW data with NEW random keys
- ALL previously encrypted data became permanently inaccessible
- **You have already lost access to all encrypted PHI data except data encrypted since the last restart**

#### Reality Check

**Q**: Can I recover the old encrypted data?
**A**: **NO** - The random keys from previous sessions are lost forever

**Q**: What data can I still access?
**A**: Only PHI data encrypted since the LAST application restart

**Q**: Should I still deploy this fix?
**A**: **YES** - To prevent FUTURE data loss

#### Migration Steps (Data Loss Acceptance Required)

```bash
# 1. ACKNOWLEDGE DATA LOSS
# All PHI encrypted before the last restart is permanently lost
# Document this in your incident report

# 2. Extract accessible data (encrypted since last restart)
# Only if application is CURRENTLY RUNNING
# DO NOT RESTART before doing this!

# If application is running:
# a. Connect to running application
# b. Export all currently accessible PHI data
# c. Save decrypted copies to secure temporary storage

# 3. Generate new persistent keys
python scripts/generate_encryption_keys.py

# 4. Clear old encrypted data (already inaccessible)
# Document which records are being purged
# Maintain audit trail for compliance

# 5. Deploy with new persistent keys
export PHI_ENCRYPTION_KEY="<generated-key>"
export ENCRYPTION_KEY="<generated-key>"
export ENCRYPTION_SALT="<generated-key>"
export JWT_SECRET_KEY="<generated-key>"
export SECRET_KEY="<generated-key>"

# 6. Restart application
# Application will now use persistent keys

# 7. Re-import accessible data with new persistent keys
# Only re-encrypt data that was successfully extracted in step 2

# 8. Document data loss incident
# Follow HIPAA Breach Notification requirements if applicable
```

**Result**: ⚠️ Data loss occurred (pre-existing issue, now fixed)

---

### Scenario 4: Development/Testing Environment

**Safe**: Generate new keys, clear database, start fresh

```bash
# 1. Back up any important test data (if needed)

# 2. Drop and recreate database
dropdb vitalcore_dev
createdb vitalcore_dev

# 3. Generate new encryption keys
python scripts/generate_encryption_keys.py

# 4. Add to .env file
cat >> .env << EOF
PHI_ENCRYPTION_KEY=<generated-key>
ENCRYPTION_KEY=<generated-key>
ENCRYPTION_SALT=<generated-key>
JWT_SECRET_KEY=<generated-key>
SECRET_KEY=<generated-key>
EOF

# 5. Run migrations
alembic upgrade head

# 6. Start application
python -m uvicorn app.main:app --reload
```

**Result**: ✅ Safe - Fresh start with persistent keys

---

## 🔍 Pre-Migration Verification

Before migrating, verify your deployment scenario:

### Check 1: Is Application Currently Running?

```bash
# Check if VitalCore is running
curl http://localhost:8000/health
```

- **Running**: Proceed with caution (Scenario 3)
- **Not Running**: Data already lost (Scenario 3)

### Check 2: Do You Have Encrypted Data?

```sql
-- Connect to database
psql vitalcore

-- Check for encrypted PHI records
SELECT COUNT(*) FROM patients WHERE encrypted_ssn IS NOT NULL;
SELECT COUNT(*) FROM healthcare_records WHERE encrypted_data IS NOT NULL;
```

- **Count > 0**: You have encrypted data (Scenario 3)
- **Count = 0**: No encrypted data (Scenario 2)

### Check 3: Can You Access Current Environment Variables?

```bash
# Check if running in container
docker exec vitalcore-api env | grep ENCRYPTION_KEY

# Check if running locally
echo $ENCRYPTION_KEY
```

- **Has value**: These were temporary random keys (already lost if restarted)
- **No value**: Application not configured correctly

---

## 📊 Post-Migration Verification

After deploying the fix, verify everything works:

### Test 1: Application Starts Successfully

```bash
# Application should start and log:
# "✅ Encryption keys validated successfully"
# "✅ Encryption service initialized and validated successfully"

# Check logs
tail -f logs/healthcare.log | grep -i encryption
```

### Test 2: Encryption/Decryption Works

```bash
# Test encryption round-trip
python scripts/debug/debug_encryption.py
```

### Test 3: Keys Persist Across Restarts

```bash
# Encrypt some test data
curl -X POST http://localhost:8000/api/v1/healthcare/patients \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name": "Test Patient", "ssn": "123-45-6789"}'

# Restart application
kill -HUP $(pidof uvicorn)
sleep 5

# Verify data is still accessible
curl http://localhost:8000/api/v1/healthcare/patients/1 \
  -H "Authorization: Bearer $TOKEN"

# Should return decrypted data successfully
```

### Test 4: Application Fails Without Keys

```bash
# Remove encryption keys
unset PHI_ENCRYPTION_KEY

# Try to start application
python -m uvicorn app.main:app

# Expected: RuntimeError with clear error message
# "CRITICAL CONFIGURATION ERROR: Missing required encryption keys"
```

---

## 🚨 HIPAA Breach Notification

If you discover data loss due to this issue:

### Notification Timeline

- **Immediately**: Document the incident
- **Within 24 hours**: Notify security team and management
- **Within 60 days**: Notify affected individuals (if PHI was compromised)
- **Within 60 days**: Notify HHS if breach affects 500+ individuals

### Required Documentation

1. **Incident Description**
   - What: Encryption key randomization caused data loss
   - When: Since application deployment (all restart events)
   - Impact: PHI encrypted before last restart permanently lost

2. **Root Cause Analysis**
   - Encryption keys were randomly generated on startup
   - No key persistence mechanism
   - Data encrypted with session-specific keys became inaccessible

3. **Remediation**
   - Implemented persistent encryption key management
   - Added startup validation to prevent future occurrences
   - Created key backup and rotation procedures

4. **Affected Individuals**
   - List of patients whose PHI may have been lost
   - Data loss does not equal unauthorized disclosure
   - May not require individual notification if data not disclosed

### Risk Assessment

**Good News**:
- Data was NOT disclosed to unauthorized parties
- Data was NOT exfiltrated or stolen
- Data was encrypted (albeit temporarily inaccessible)

**Bad News**:
- Data loss may affect treatment continuity
- Backup restoration may be incomplete
- Some patient records may be permanently lost

**Notification Requirement**:
- **Likely NOT required** if data was only lost (not disclosed)
- Consult with privacy officer and legal counsel
- Document decision rationale

---

## 📞 Emergency Support

### If Something Goes Wrong

1. **DO NOT PANIC**
2. **DO NOT restart the application**
3. **DO NOT generate new keys**
4. Contact:
   - Security Team: security@vitalcore.health
   - On-Call Engineer: oncall@vitalcore.health
   - Compliance Officer: compliance@vitalcore.health

### Rollback Plan

If migration fails:

```bash
# 1. Stop new version
systemctl stop vitalcore

# 2. Restore database backup
pg_restore -d vitalcore backup_pre_migration.sql

# 3. Restore previous application version
git checkout <previous-version>

# 4. Start old version
# WARNING: Still has encryption key issue!

# 5. Plan new migration attempt with support
```

---

## 📚 Additional Resources

- [Encryption Key Setup Guide](./ENCRYPTION_KEY_SETUP.md)
- [HIPAA Breach Notification Rule](https://www.hhs.gov/hipaa/for-professionals/breach-notification/index.html)
- [NIST Key Management Guidelines](https://csrc.nist.gov/publications/detail/sp/800-57-part-1/rev-5/final)

---

**Last Updated**: 2025-11-05
**Document Owner**: Security Team
**Approved By**: Compliance Officer
