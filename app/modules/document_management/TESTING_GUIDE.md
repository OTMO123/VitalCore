# 🧪 Document Management Testing Guide

## Overview
This guide provides comprehensive instructions for testing the Document Management system with full SOC2/HIPAA compliance validation.

## Test Suite Structure

### 📁 Test Files
```
app/modules/document_management/
├── test_router_crud.py           # Unit tests for CRUD endpoints
├── test_schemas_validation.py    # Schema validation and security tests
├── test_security_compliance.py   # SOC2/HIPAA compliance tests
├── test_integration_api.py       # Full API integration tests
└── TESTING_GUIDE.md              # This guide
```

## 🚀 Running Tests

### Prerequisites
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx pytest-mock

# Ensure you're in the project root
cd /mnt/c/Users/aurik/Code_Projects/2_scraper
```

### Run All Tests
```bash
# Run all document management tests
python -m pytest app/modules/document_management/test_*.py -v

# Run with coverage
python -m pytest app/modules/document_management/test_*.py --cov=app.modules.document_management --cov-report=html
```

### Run Specific Test Categories

#### 1. Unit Tests (CRUD Endpoints)
```bash
python -m pytest app/modules/document_management/test_router_crud.py -v
```

**What it tests:**
- GET /documents/{document_id} - Document metadata retrieval
- PATCH /documents/{document_id} - Document metadata updates
- DELETE /documents/{document_id} - Document deletion
- GET /documents/stats - Document statistics
- POST /documents/bulk/* - Bulk operations
- Input validation and error handling
- Authentication and authorization flows

#### 2. Schema Validation Tests
```bash
python -m pytest app/modules/document_management/test_schemas_validation.py -v
```

**What it tests:**
- Pydantic schema validation
- Security input sanitization
- Path traversal prevention
- XSS prevention
- SQL injection prevention
- File upload validation
- UUID format validation
- Tag and metadata validation

#### 3. Security & Compliance Tests
```bash
python -m pytest app/modules/document_management/test_security_compliance.py -v
```

**What it tests:**
- SOC2 Type 2 compliance controls
- HIPAA compliance requirements
- Role-based access control (RBAC)
- PHI access logging and audit trails
- Patient consent verification
- Data retention policy enforcement
- Encryption at rest and in transit
- Secure deletion procedures
- Audit trail integrity verification

#### 4. Integration Tests
```bash
python -m pytest app/modules/document_management/test_integration_api.py -v
```

**What it tests:**
- Full API workflow end-to-end
- Database integration
- File upload and download
- Document search functionality
- Bulk operations
- Error handling in real scenarios
- Performance under load

## 🔍 Test Categories Explained

### Unit Tests (`test_router_crud.py`)

#### Document Metadata Retrieval Tests
```python
class TestDocumentMetadataEndpoint:
    def test_get_document_metadata_success()      # Valid document retrieval
    def test_get_document_metadata_invalid_uuid() # Invalid UUID format
    def test_get_document_metadata_not_found()    # Non-existent document
    def test_get_document_metadata_unauthorized() # Access denied
```

#### Document Update Tests
```python
class TestDocumentUpdateEndpoint:
    def test_update_document_metadata_success()   # Valid metadata update
    def test_update_document_metadata_invalid_reason() # Invalid reason
```

#### Document Deletion Tests
```python
class TestDocumentDeletionEndpoint:
    def test_delete_document_success()            # Valid deletion
    def test_delete_document_invalid_reason()     # Invalid deletion reason
```

### Schema Validation Tests (`test_schemas_validation.py`)

#### Security Validation
```python
class TestSecurityValidationEdgeCases:
    def test_null_byte_injection()               # Null byte attacks
    def test_unicode_normalization_attacks()     # Unicode attacks
    def test_very_long_inputs()                  # Buffer overflow prevention
    def test_script_injection_attempts()         # XSS/script injection
```

#### Input Validation
```python
class TestDocumentUploadRequestValidation:
    def test_dangerous_filename_characters()     # Path traversal prevention
    def test_too_many_tags()                     # Resource exhaustion prevention
    def test_invalid_patient_id()               # UUID validation
```

### Compliance Tests (`test_security_compliance.py`)

#### SOC2 Controls
```python
class TestAccessControlCompliance:
    def test_role_based_access_control()         # CC6.1 - Access Controls
    def test_minimum_necessary_access_principle() # HIPAA minimum necessary
    def test_session_timeout_enforcement()       # CC6.2 - Logical Access
```

#### HIPAA Controls
```python
class TestAuditLoggingCompliance:
    def test_phi_access_audit_logging()          # PHI access tracking
    def test_immutable_audit_trail()             # Tamper-proof logs
    def test_bulk_operation_audit_trail()        # Bulk operation logging
```

### Integration Tests (`test_integration_api.py`)

#### Full Workflow Tests
```python
class TestDocumentCRUDIntegration:
    def test_upload_then_retrieve_workflow()     # Complete CRUD workflow
    def test_search_and_filter_workflow()        # Search functionality
    def test_bulk_operations_workflow()          # Bulk operations
```

## 🛡️ Security Test Scenarios

### 1. Authentication & Authorization
```bash
# Test unauthorized access
curl -X GET http://localhost:8000/api/v1/documents/stats
# Expected: 401 Unauthorized

# Test with invalid token
curl -X GET http://localhost:8000/api/v1/documents/stats \
  -H "Authorization: Bearer invalid_token"
# Expected: 401 Unauthorized
```

### 2. Input Validation
```bash
# Test SQL injection attempt
curl -X POST http://localhost:8000/api/v1/documents/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"search_text": "'; DROP TABLE documents; --"}'
# Expected: Safe handling, no SQL execution

# Test path traversal in filename
curl -X PATCH http://localhost:8000/api/v1/documents/$DOC_ID?reason=test \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"filename": "../../../etc/passwd"}'
# Expected: 400 Bad Request
```

### 3. PHI Access Control
```bash
# Test access to document without patient consent
curl -X GET http://localhost:8000/api/v1/documents/$DOC_ID \
  -H "Authorization: Bearer $NURSE_TOKEN"
# Expected: 403 Forbidden (if no consent)

# Test PHI access logging
curl -X GET http://localhost:8000/api/v1/documents/$DOC_ID \
  -H "Authorization: Bearer $DOCTOR_TOKEN"
# Expected: Access logged in audit trail
```

## 📊 Performance Testing

### Load Testing with pytest-benchmark
```bash
pip install pytest-benchmark

# Run performance tests
python -m pytest app/modules/document_management/test_integration_api.py::TestDocumentUploadIntegration::test_upload_document_success --benchmark-only
```

### Memory Usage Testing
```bash
# Monitor memory during bulk operations
python -m pytest app/modules/document_management/test_integration_api.py::TestBulkOperationsIntegration --memory-profiler
```

## 🔧 Manual Testing Scenarios

### 1. Document Upload Flow
```bash
# 1. Upload a document
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_document.pdf" \
  -F "patient_id=$PATIENT_ID" \
  -F "document_type=LAB_RESULT" \
  -F "document_category=Laboratory" \
  -F "tags=urgent,blood_test" \
  -F "auto_classify=true"

# 2. Verify upload in response
# Expected: document_id, filename, file_size, hash_sha256

# 3. Retrieve document metadata
curl -X GET http://localhost:8000/api/v1/documents/$DOCUMENT_ID \
  -H "Authorization: Bearer $TOKEN"

# 4. Update document metadata
curl -X PATCH http://localhost:8000/api/v1/documents/$DOCUMENT_ID?reason=Manual%20test \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tags": ["updated", "manual_test"]}'

# 5. Download document
curl -X GET http://localhost:8000/api/v1/documents/$DOCUMENT_ID/download \
  -H "Authorization: Bearer $TOKEN" \
  -o downloaded_document.pdf

# 6. Soft delete document
curl -X DELETE http://localhost:8000/api/v1/documents/$DOCUMENT_ID?deletion_reason=Manual%20test \
  -H "Authorization: Bearer $TOKEN"
```

### 2. Search and Filter Testing
```bash
# Search by patient
curl -X POST http://localhost:8000/api/v1/documents/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"patient_id": "'$PATIENT_ID'", "limit": 10}'

# Search by document type
curl -X POST http://localhost:8000/api/v1/documents/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"document_types": ["LAB_RESULT"], "limit": 10}'

# Search by tags
curl -X POST http://localhost:8000/api/v1/documents/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tags": ["urgent"], "limit": 10}'

# Full-text search
curl -X POST http://localhost:8000/api/v1/documents/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"search_text": "blood test", "limit": 10}'
```

### 3. Bulk Operations Testing
```bash
# Bulk delete
curl -X POST http://localhost:8000/api/v1/documents/bulk/delete \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "document_ids": ["'$DOC_ID_1'", "'$DOC_ID_2'"],
    "reason": "Bulk manual test deletion",
    "hard_delete": false
  }'

# Bulk tag update
curl -X POST http://localhost:8000/api/v1/documents/bulk/update-tags \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "document_ids": ["'$DOC_ID_1'", "'$DOC_ID_2'"],
    "tags": ["bulk_updated", "manual_test"],
    "action": "add"
  }'
```

## 📈 Test Coverage Goals

### Coverage Targets
- **Unit Tests**: >95% line coverage
- **Integration Tests**: >90% endpoint coverage
- **Security Tests**: 100% security control coverage
- **Compliance Tests**: 100% SOC2/HIPAA requirement coverage

### Generating Coverage Reports
```bash
# Generate HTML coverage report
python -m pytest app/modules/document_management/test_*.py \
  --cov=app.modules.document_management \
  --cov-report=html \
  --cov-report=term-missing

# View coverage report
open htmlcov/index.html
```

## 🚨 Compliance Validation Checklist

### SOC2 Type 2 Requirements
- [ ] Access controls tested (CC6.1)
- [ ] Logical access controls tested (CC6.2)  
- [ ] System operations monitoring tested (CC7.1)
- [ ] Change management tested (CC8.1)
- [ ] Audit logging completeness verified
- [ ] Data encryption verified
- [ ] Incident response tested

### HIPAA Requirements
- [ ] Administrative safeguards tested
- [ ] Physical safeguards verified
- [ ] Technical safeguards validated
- [ ] PHI access controls tested
- [ ] Audit trail completeness verified
- [ ] Patient consent verification tested
- [ ] Minimum necessary access tested
- [ ] Secure deletion verified

## 🔄 Continuous Integration

### GitHub Actions Example
```yaml
name: Document Management Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-asyncio pytest-cov
    - name: Run tests
      run: |
        python -m pytest app/modules/document_management/test_*.py \
          --cov=app.modules.document_management \
          --cov-fail-under=90
```

## 🐛 Debugging Test Failures

### Common Issues and Solutions

#### 1. Database Connection Issues
```bash
# Check database connection
python -c "
from app.core.database_unified import get_db
print('Database connection test')
"
```

#### 2. Authentication Issues
```bash
# Generate test token
python -c "
from app.core.security import create_access_token
token = create_access_token({'sub': 'test_user'})
print(f'Test token: {token}')
"
```

#### 3. Mock Service Issues
```bash
# Verify mock service setup
python -m pytest app/modules/document_management/test_router_crud.py::TestDocumentMetadataEndpoint::test_get_document_metadata_success -v -s
```

### Debug Mode Testing
```bash
# Run tests with debug output
python -m pytest app/modules/document_management/test_*.py -v -s --tb=long

# Run single test with debugging
python -m pytest app/modules/document_management/test_router_crud.py::TestDocumentMetadataEndpoint::test_get_document_metadata_success -v -s --pdb
```

## 📋 Test Results Documentation

### Expected Test Results
- **Total Tests**: ~150+ test cases
- **Unit Tests**: ~50 test cases
- **Schema Tests**: ~40 test cases  
- **Security Tests**: ~35 test cases
- **Integration Tests**: ~25 test cases

### Sample Test Report
```
====================== test session starts ======================
collected 157 items

test_router_crud.py::TestDocumentMetadataEndpoint::test_get_document_metadata_success PASSED [6%]
test_router_crud.py::TestDocumentMetadataEndpoint::test_get_document_metadata_invalid_uuid PASSED [12%]
test_schemas_validation.py::TestDocumentUploadRequestValidation::test_valid_upload_request PASSED [18%]
test_security_compliance.py::TestAccessControlCompliance::test_role_based_access_control PASSED [24%]
test_integration_api.py::TestDocumentUploadIntegration::test_upload_document_success PASSED [30%]

=================== 157 passed in 45.67s ===================
```

This comprehensive testing guide ensures that the Document Management system meets all security, compliance, and functional requirements while providing clear instructions for validation and debugging.