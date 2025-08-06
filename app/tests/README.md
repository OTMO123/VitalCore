# IRIS API Integration System - Test Suite

## Test Structure

```
tests/
├── smoke/                  # Basic system verification (run first)
│   ├── test_system_startup.py      # Database, encryption, services
│   ├── test_auth_flow.py           # Authentication lifecycle  
│   ├── test_core_endpoints.py      # API endpoint accessibility
│   ├── test_basic.py              # Basic smoke test
│   └── test_basic_functionality.py # Core functionality verification
├── core/                   # Critical business logic tests
│   ├── healthcare_records/
│   │   ├── test_patient_api.py      # Patient management
│   │   ├── test_phi_encryption.py   # PHI encryption tests
│   │   └── test_consent_management.py # HIPAA consent
│   ├── security/
│   │   ├── test_authorization.py           # RBAC and permissions
│   │   ├── test_audit_logging.py           # SOC2 compliance
│   │   └── test_security_vulnerabilities.py # Security hardening tests
│   └── test_event_bus.py           # Event system tests
└── integration/            # External service integration
    └── test_example_integration.py # Integration patterns
```

## Test Categories

### 🔥 Smoke Tests (Priority 1)
- **Purpose**: Verify basic system infrastructure is operational
- **Run First**: These tests validate the system can start and connect to dependencies
- **Markers**: `@pytest.mark.smoke`
- **Command**: `python run_tests.py smoke`

**Key Tests**:
- `test_system_startup.py` - Database connection, migrations, encryption service
- `test_auth_flow.py` - Complete authentication lifecycle 
- `test_core_endpoints.py` - API endpoint accessibility and security

### 💼 Core Business Logic (Priority 2)
- **Purpose**: Test critical healthcare and security functionality
- **Markers**: `@pytest.mark.healthcare`, `@pytest.mark.security`, `@pytest.mark.audit`
- **Command**: `python run_tests.py unit`

**Key Areas**:
- Healthcare Records: Patient management, PHI encryption, FHIR compliance
- Security: Authentication, authorization, audit logging, vulnerability testing
- Event System: Domain events, background tasks

### 🔗 Integration Tests (Priority 3)  
- **Purpose**: Test external service integration and end-to-end workflows
- **Markers**: `@pytest.mark.integration`
- **Command**: `python run_tests.py integration`

## Running Tests

### Quick Start
```bash
# Run smoke tests first (most important)
python run_tests.py smoke

# Run all core tests
python run_tests.py unit integration

# Run with coverage
python run_tests.py --all --coverage
```

### Development Workflow
```bash
# Watch mode for development
python run_tests.py smoke --watch

# Run specific test category
python run_tests.py security
python run_tests.py healthcare

# Fast feedback loop
python run_tests.py --quick  # smoke + unit only
```

### CI/CD Pipeline
```bash
# CI test suite
python run_tests.py --ci  # unit + integration + security + api
```

## Test Implementation Status

### ✅ Completed
- **Smoke Tests**: 3 comprehensive smoke test files with 20+ test cases
- **Test Infrastructure**: 40+ fixtures, Docker containers, Rich CLI
- **PHI Encryption Tests**: Basic encryption/decryption functionality
- **Directory Structure**: Organized by priority and domain

### 🔄 In Progress (Placeholder Tests Created)
- **Patient API Tests**: Placeholders for patient management
- **Authorization Tests**: Placeholders for RBAC implementation  
- **Audit Logging Tests**: Placeholders for SOC2 compliance
- **Consent Management**: Placeholders for HIPAA consent tracking

### ⚠️ Dependencies Required
- **Database Migration**: Run `alembic upgrade head` before testing
- **Services**: Start test services with `make start-services`
- **Python Packages**: Install test dependencies with `make install-dev`

## Test Patterns

### Fixture Usage
```python
# Database session with auto-rollback
async def test_example(db_session: AsyncSession):
    # Test uses isolated database session

# Authentication headers for protected endpoints  
async def test_protected_endpoint(async_test_client, auth_headers):
    response = await async_test_client.get("/api/v1/protected", headers=auth_headers)
```

### Markers and Organization
```python
pytestmark = pytest.mark.smoke      # File-level marker
@pytest.mark.order(1)              # Execution order
@pytest.mark.asyncio               # Async test
```

### Security Testing
```python
# Test PHI encryption
def test_phi_encryption(encryption_service):
    encrypted = encryption_service.encrypt("123-45-6789")
    assert encrypted != "123-45-6789"  # Data is encrypted
    
# Test authentication
async def test_auth_required(async_test_client):
    response = await async_test_client.get("/api/v1/protected")
    assert response.status_code == 401  # Requires auth
```

## Key Features

- **Professional Infrastructure**: Rich CLI, Docker containers, performance monitoring
- **Healthcare Focus**: PHI encryption, HIPAA compliance, FHIR validation
- **Security First**: Authentication testing, audit logging, access control
- **SOC2 Ready**: Compliance testing, immutable audit logs, integrity validation
- **Developer Friendly**: Watch mode, fast feedback, clear reporting

## Next Steps

1. **Apply Database Migration**: `alembic upgrade head`
2. **Run Smoke Tests**: Verify system is operational
3. **Implement Core Tests**: Replace placeholders with actual test logic
4. **Add Integration Tests**: Test IRIS API integration and end-to-end workflows