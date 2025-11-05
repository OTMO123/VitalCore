# VitalCore Testing Guide - Complete Verification

This guide covers how to test all Phase 1-3 implementations to verify 98%+ production readiness.

---

## Quick Start - Run All Tests

```bash
# Navigate to project root
cd /home/user/VitalCore

# Run full test suite
pytest app/tests/ -v --tb=short

# Or run with coverage report
pytest app/tests/ -v --cov=app --cov-report=html --cov-report=term
```

---

## 1. Environment Setup

### Step 1: Install Dependencies

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov pytest-mock faker httpx

# Install security dependencies (optional but recommended)
pip install python-magic pyclamd

# Verify installations
python -c "import pytest; print(f'pytest: {pytest.__version__}')"
python -c "import pytest_asyncio; print('pytest-asyncio: OK')"
```

### Step 2: Set Test Environment Variables

```bash
# Option A: Use the provided test environment file
export $(cat .env.test | xargs)

# Option B: Set manually
export ENVIRONMENT=test
export DATABASE_URL="postgresql+asyncpg://test_user:test_password@localhost:5433/test_iris_db"
export PHI_ENCRYPTION_KEY="test_phi_encryption_key_32_characters_minimum_length_for_testing"
export ENCRYPTION_KEY="test_encryption_key_32_characters_minimum_length_for_testing_only"
export ENCRYPTION_SALT="test_encryption_salt_32_characters_minimum_length_for_testing_now"
export JWT_SECRET_KEY="test_jwt_secret_key_32_characters_minimum_length_for_testing_only"
export SECRET_KEY="test_secret_key_32_characters_minimum_length_for_testing_only_use"

# Verify keys are set
echo "Keys configured:"
echo "PHI_ENCRYPTION_KEY length: ${#PHI_ENCRYPTION_KEY}"
echo "ENCRYPTION_KEY length: ${#ENCRYPTION_KEY}"
```

### Step 3: Start Test Database (Optional)

```bash
# If you have Docker and want to run integration tests
cd infrastructure/docker
docker-compose -f docker-compose.test.yml up -d test-postgres test-redis

# Verify containers are running
docker-compose -f docker-compose.test.yml ps

# Check logs
docker-compose -f docker-compose.test.yml logs test-postgres

# Return to project root
cd /home/user/VitalCore
```

---

## 2. Test Categories

### A. Smoke Tests (Quick Validation)

**Purpose:** Verify basic functionality works

```bash
# Run smoke tests only (fast, ~30 seconds)
pytest app/tests/smoke/ -v

# Expected: Most tests should pass
# These test basic API functionality without database
```

### B. Phase 1 Fixes - P0 Blocker Tests

**Purpose:** Verify all 12 P0 fixes from Phase 1

```bash
# Test 1: HL7 Duplicate Enum Fix
pytest app/tests/ -k "hl7" -v --tb=short
# Should not see: "duplicate enum value" error

# Test 2: Document Management Enum Fix
pytest app/tests/core/document_management/ -v --tb=short
# Should not see: "AuditSeverity.INFO" AttributeError

# Test 3: Clinical Decision Support Async Init
pytest app/tests/core/test_clinical_decision_support.py -v
# Should not see: "RuntimeError: no running event loop"

# Test 4: Encryption Key Validation
python -c "
from app.core.config import get_settings
settings = get_settings()
print(f'✅ PHI_ENCRYPTION_KEY: {len(settings.PHI_ENCRYPTION_KEY)} chars')
print(f'✅ ENCRYPTION_KEY: {len(settings.ENCRYPTION_KEY)} chars')
print(f'✅ All keys meet 32+ char requirement')
"
```

### C. Phase 2 Fixes - Integration Tests

**Purpose:** Verify CDS initialization and test configuration

```bash
# Test 1: CDS Engine Initialization
python -c "
import asyncio
from app.core.clinical_decision_support import ClinicalDecisionSupportEngine

async def test_cds():
    engine = ClinicalDecisionSupportEngine()
    await engine.initialize()
    print(f'✅ CDS initialized: {len(engine.rules)} rules, {len(engine.protocols)} protocols')

asyncio.run(test_cds())
"

# Test 2: Application Startup with CDS
python -c "
import asyncio
from app.main import lifespan
from fastapi import FastAPI

async def test_startup():
    app = FastAPI()
    async with lifespan(app):
        print('✅ Application startup successful with CDS initialization')

try:
    asyncio.run(test_startup())
except Exception as e:
    print(f'❌ Startup failed: {e}')
"

# Test 3: Test Database Configuration
pytest app/tests/conftest.py --collect-only
# Should see: test configurations load successfully
```

### D. Phase 3 Fixes - Security & HIPAA Tests

**Purpose:** Verify security hardening and compliance

```bash
# Test 1: File Upload Security (50 tests)
pytest app/tests/core/document_management/test_file_upload_security.py -v
# Expected: 45-50 tests pass (90-100%)

# Test 2: HIPAA Compliance Tests
pytest app/tests/compliance/ -v --tb=short
pytest app/tests/security/ -k "hipaa or audit" -v
# Expected: 85-95% pass rate

# Test 3: Audit Log Immutability
python -c "
from app.core.database_unified import AuditLog

# Test immutability
log = AuditLog(
    user_id=1,
    action='test',
    resource_type='test',
    resource_id=1
)
log.mark_persisted()

try:
    log.action = 'modified'
    print('❌ Immutability failed - modification allowed')
except ValueError as e:
    print(f'✅ Immutability working: {e}')
"

# Test 4: File Type Validation
python -c "
from app.core.validators import FileValidator

validator = FileValidator()

# Test allowed file
is_valid, error = validator.validate_file_extension('test.pdf')
print(f'PDF validation: {\"✅ PASS\" if is_valid else f\"❌ FAIL: {error}\"}')

# Test blocked file
is_valid, error = validator.validate_file_extension('test.exe')
print(f'EXE blocked: {\"✅ PASS\" if not is_valid else \"❌ FAIL: executable allowed\"}')
"
```

---

## 3. Comprehensive Test Runs

### Run All Tests by Category

```bash
# 1. Unit tests (fast, no external dependencies)
pytest app/tests/ -m "unit" -v

# 2. Integration tests (require database)
pytest app/tests/ -m "integration" -v

# 3. Security tests
pytest app/tests/ -m "security" -v

# 4. HIPAA compliance tests
pytest app/tests/compliance/ -v
pytest app/tests/security/ -k "hipaa" -v

# 5. Performance tests
pytest app/tests/ -m "performance" -v --tb=short
```

### Run Complete Test Suite

```bash
# Full test suite with detailed output
pytest app/tests/ -v --tb=short --durations=10

# With coverage report
pytest app/tests/ \
  --cov=app \
  --cov-report=html \
  --cov-report=term-missing \
  --cov-report=xml \
  -v

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Check Test Pass Rate

```bash
# Run all tests and get pass rate
pytest app/tests/ --tb=no -q | tee test_results.txt

# Calculate pass rate
python -c "
import re
with open('test_results.txt', 'r') as f:
    output = f.read()
    match = re.search(r'(\d+) passed.*?(\d+) failed', output)
    if match:
        passed = int(match.group(1))
        failed = int(match.group(2))
        total = passed + failed
        rate = (passed / total * 100) if total > 0 else 0
        print(f'✅ Pass Rate: {rate:.1f}% ({passed}/{total} tests)')
        if rate >= 98:
            print('🎉 TARGET ACHIEVED: 98%+ production ready!')
        elif rate >= 90:
            print('⚠️  Good progress: 90%+ but not quite 98%')
        else:
            print('❌ More work needed')
"
```

---

## 4. Specific Feature Testing

### Test 1: Encryption Key Persistence

```bash
# Verify keys don't regenerate on restart
python -c "
from app.core.config import get_settings

# Get keys
settings1 = get_settings()
key1 = settings1.PHI_ENCRYPTION_KEY

# Reload settings (simulates restart)
from app.core.config import Settings
settings2 = Settings()
key2 = settings2.PHI_ENCRYPTION_KEY

if key1 == key2:
    print('✅ Encryption keys persist (no random generation)')
else:
    print('❌ Keys regenerate - data loss risk!')
"
```

### Test 2: File Upload Security

```bash
# Create test files
mkdir -p /tmp/vitalcore_test
echo "test content" > /tmp/vitalcore_test/test.pdf
echo "malicious" > /tmp/vitalcore_test/test.exe

# Test with Python
python -c "
from app.core.validators import FileValidator

validator = FileValidator()

# Test allowed files
allowed = ['test.pdf', 'test.dcm', 'test.jpg', 'test.xml', 'test.hl7']
for filename in allowed:
    is_valid, error = validator.validate_file_extension(filename)
    status = '✅' if is_valid else '❌'
    print(f'{status} {filename}: {\"allowed\" if is_valid else error}')

print()

# Test blocked files
blocked = ['test.exe', 'test.sh', 'test.bat', 'test.js', 'test.dll']
for filename in blocked:
    is_valid, error = validator.validate_file_extension(filename)
    status = '✅' if not is_valid else '❌'
    print(f'{status} {filename}: {\"blocked\" if not is_valid else \"DANGER: allowed!\"}')
"
```

### Test 3: HIPAA Audit Immutability

```bash
# Test audit log cannot be modified
python -c "
from app.core.database_unified import AuditLog
from datetime import datetime

# Create and persist audit log
log = AuditLog(
    user_id=1,
    action='read_patient_record',
    resource_type='patient',
    resource_id=123,
    event_type='phi_access'
)

# Mark as persisted (simulates database commit)
log.mark_persisted()

# Try to tamper
tests = [
    ('action', 'modified_action'),
    ('user_id', 999),
    ('resource_id', 456),
]

print('Testing audit log immutability:')
for field, new_value in tests:
    try:
        setattr(log, field, new_value)
        print(f'❌ {field}: modification allowed (HIPAA violation!)')
    except ValueError as e:
        print(f'✅ {field}: immutable (HIPAA compliant)')
"
```

### Test 4: Clinical Decision Support

```bash
# Test CDS engine functionality
python -c "
import asyncio
from app.core.clinical_decision_support import ClinicalDecisionSupportEngine

async def test_cds():
    engine = ClinicalDecisionSupportEngine()
    await engine.initialize()

    print('✅ CDS Engine Initialized')
    print(f'   Rules: {len(engine.rules)}')
    print(f'   Protocols: {len(engine.protocols)}')
    print(f'   Quality Measures: {len(engine.quality_measures)}')

    # Test patient evaluation
    patient_data = {
        'id': 'patient_001',
        'age': 65,
        'systolic_bp': 145,
        'diastolic_bp': 92,
        'diagnosis_codes': ['I10']  # Hypertension
    }

    result = await engine.evaluate_patient(patient_data)
    print(f'✅ Patient evaluation completed')
    print(f'   Alerts: {len(result.get(\"alerts\", []))}')
    print(f'   Recommendations: {len(result.get(\"recommendations\", []))}')

asyncio.run(test_cds())
"
```

---

## 5. Manual API Testing

### Start the Application

```bash
# Set environment variables
export $(cat .env.test | xargs)

# Start the application
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# You should see in the logs:
# ✅ Encryption keys validated successfully
# ✅ Clinical Decision Support Engine initialized successfully
# ✅ System initialized successfully
```

### Test API Endpoints

```bash
# In a new terminal

# Test 1: Health check
curl http://localhost:8000/health

# Test 2: OpenAPI documentation
curl http://localhost:8000/docs
# Or open in browser: http://localhost:8000/docs

# Test 3: Authentication
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test_user","password":"test_password"}'

# Test 4: File upload (with authentication token)
TOKEN="<your_token_from_login>"
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/vitalcore_test/test.pdf"

# Should return: security_checks with all validations passed
```

---

## 6. Performance Testing

### Benchmark Key Operations

```bash
# Run performance tests
pytest app/tests/ -m "performance" -v --durations=10

# Or benchmark manually
python -c "
import asyncio
import time
from app.core.security import encryption_service

async def benchmark():
    # Test encryption performance
    test_data = 'sensitive_patient_data' * 100  # ~2KB

    start = time.time()
    for _ in range(1000):
        encrypted = await encryption_service.encrypt(test_data)
        decrypted = await encryption_service.decrypt(encrypted)
    duration = time.time() - start

    ops_per_sec = 1000 / duration
    print(f'✅ Encryption Performance:')
    print(f'   Operations: 1000 encrypt/decrypt cycles')
    print(f'   Duration: {duration:.2f}s')
    print(f'   Throughput: {ops_per_sec:.0f} ops/sec')

asyncio.run(benchmark())
"
```

---

## 7. Troubleshooting Common Issues

### Issue 1: Import Errors

```bash
# If you see ModuleNotFoundError
# Fix: Ensure all __init__.py files exist
find app/tests -type d -exec touch {}/__init__.py \;

# Verify Python path
python -c "import sys; print('\n'.join(sys.path))"

# Should include /home/user/VitalCore
export PYTHONPATH=/home/user/VitalCore:$PYTHONPATH
```

### Issue 2: Database Connection Errors

```bash
# Check database is running
docker ps | grep postgres

# If not running, start it
cd infrastructure/docker
docker-compose -f docker-compose.test.yml up -d test-postgres

# Test connection
psql postgresql://test_user:test_password@localhost:5433/test_iris_db -c "SELECT 1;"

# If connection fails, check port
netstat -an | grep 5433
```

### Issue 3: Encryption Key Errors

```bash
# Verify all keys are set and meet length requirements
python -c "
import os
required_keys = [
    'PHI_ENCRYPTION_KEY',
    'ENCRYPTION_KEY',
    'ENCRYPTION_SALT',
    'JWT_SECRET_KEY',
    'SECRET_KEY'
]

print('Encryption Key Status:')
for key in required_keys:
    value = os.getenv(key, '')
    length = len(value)
    status = '✅' if length >= 32 else '❌'
    print(f'{status} {key}: {length} chars (minimum: 32)')
"

# If any fail, regenerate
python scripts/generate_encryption_keys.py
```

### Issue 4: Async Test Failures

```bash
# If you see async/await errors
# Ensure pytest-asyncio is installed
pip install pytest-asyncio

# Run with async mode
pytest app/tests/core/test_clinical_decision_support.py \
  --asyncio-mode=auto -v
```

---

## 8. Continuous Integration Testing

### GitHub Actions Workflow

```bash
# View current workflow status
cat .github/workflows/tests.yml

# Run tests as CI would
export CI=true
pytest app/tests/ \
  --cov=app \
  --cov-report=xml \
  --junitxml=test-results.xml \
  -v
```

---

## 9. Expected Results

### Target Metrics

| Metric | Target | How to Verify |
|--------|--------|---------------|
| **Test Pass Rate** | 98%+ | `pytest app/tests/ -q` |
| **Security Tests** | 100% | `pytest app/tests/ -m security` |
| **HIPAA Tests** | 85%+ | `pytest app/tests/compliance/` |
| **File Upload Tests** | 90%+ | `pytest app/tests/core/document_management/test_file_upload_security.py` |
| **Code Coverage** | 80%+ | `pytest --cov=app --cov-report=term` |

### Success Indicators

✅ **Application starts without errors**
✅ **CDS engine initializes successfully**
✅ **All encryption keys validate**
✅ **File upload security works**
✅ **Audit logs are immutable**
✅ **HIPAA compliance tests pass**
✅ **No critical security vulnerabilities**

---

## 10. Quick Validation Script

Save this as `test_everything.sh`:

```bash
#!/bin/bash
set -e

echo "🧪 VitalCore Complete Test Suite"
echo "================================"

# Set environment
export $(cat .env.test | xargs)

echo ""
echo "1️⃣ Environment Check..."
python -c "from app.core.config import get_settings; s=get_settings(); print(f'✅ Config loaded: {s.ENVIRONMENT}')"

echo ""
echo "2️⃣ Encryption Keys Check..."
python -c "from app.core.config import get_settings; s=get_settings(); print(f'✅ PHI key: {len(s.PHI_ENCRYPTION_KEY)} chars')"

echo ""
echo "3️⃣ Module Imports Check..."
python -c "from app.core.clinical_decision_support import ClinicalDecisionSupportEngine; print('✅ CDS imports OK')"
python -c "from app.core.validators import FileValidator; print('✅ Validators import OK')"
python -c "from app.core.security_scanning import malware_scanner; print('✅ Security scanning imports OK')"

echo ""
echo "4️⃣ Running Smoke Tests..."
pytest app/tests/smoke/ -q --tb=no

echo ""
echo "5️⃣ Running Security Tests..."
pytest app/tests/core/document_management/test_file_upload_security.py -q --tb=no || echo "⚠️  Some tests need dependencies"

echo ""
echo "6️⃣ Running Full Test Suite..."
pytest app/tests/ -q --tb=no | tail -5

echo ""
echo "✅ Testing Complete!"
echo "See TESTING_GUIDE.md for detailed testing instructions"
```

Run it:
```bash
chmod +x test_everything.sh
./test_everything.sh
```

---

## Summary

**Quick Test:**
```bash
export $(cat .env.test | xargs) && pytest app/tests/ -v --tb=short
```

**Expected Result:**
- 98%+ tests passing
- No critical errors
- Security tests passing
- HIPAA compliance verified

**If tests fail:**
1. Check environment variables
2. Verify database is running (if integration tests)
3. Review error messages
4. See troubleshooting section above

---

**Need help?** Check the comprehensive documentation:
- `P0_FIXES_IMPLEMENTATION_REPORT.md` - Phase 1 details
- `PHASE_2_IMPLEMENTATION_SUMMARY.md` - Phase 2 details
- `PHASE_3_COMPLETION_REPORT.md` - Phase 3 details
- `HIPAA_COMPLIANCE_STATUS.md` - HIPAA compliance
- `docs/FILE_UPLOAD_SECURITY.md` - Security configuration
