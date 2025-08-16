# Test Execution Failures - Troubleshooting Guide

## Current Test Status Summary

- **Smoke Tests**: 27/47 passing (57% success rate)
- **Full Test Suite**: 363 tests collected, but execution blocked
- **Main Issues**: Authentication format, database connections

## Failed Test Categories

### 1. Authentication Tests (20 failures)
**Root Cause**: Form data vs JSON content type mismatch

```python
# Failing pattern
FAILED app/tests/smoke/test_auth.py::test_login_success - AssertionError: assert 422 == 200
FAILED app/tests/smoke/test_auth.py::test_login_invalid_credentials - AssertionError: assert 422 == 401
```

**Fix Required**: Convert all authentication test calls from `data=` to `json=` parameter

### 2. Database-Dependent Tests
**Root Cause**: Connection to wrong PostgreSQL port

```bash
# Current Docker setup
docker ps | grep postgres
# Shows: 0.0.0.0:5433->5432/tcp

# Tests trying to connect to:
# localhost:5432 (wrong)
# Should connect to:
# localhost:5433 (correct)
```

### 3. Import and Module Issues
**Root Cause**: PYTHONPATH and relative import problems

```
ImportError: attempted relative import with no known parent package
```

## Working Components

### ✅ Successfully Tested
1. **Health Endpoints**
   - `/health` - Basic health check
   - `/health/detailed` - System information

2. **Docker Services**
   - PostgreSQL (port 5433)
   - Redis (port 6379)
   - MinIO (port 9000)
   - Main application (port 8000)

3. **API Structure**
   - 80+ endpoints properly defined
   - Router configuration correct
   - Middleware stack functional

## PowerShell Testing Issues

### Command Syntax Problems
```powershell
# FAILING (line breaks cause issues)
Invoke-RestMethod `
  -Uri "http://localhost:8000/api/v1/auth/login" `
  -Method POST

# WORKING (single line)
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -ContentType "application/json" -Body '{"username":"admin","password":"admin123"}'
```

## Next Steps for Resolution

### Immediate Actions (High Priority)
1. **Fix Authentication Format**
   ```bash
   # Find all test files with authentication calls
   grep -r "data=" app/tests/ | grep -i auth
   
   # Convert to JSON format
   # data={"username": "admin"} → json={"username": "admin"}
   ```

2. **Database Environment Variables**
   ```bash
   # Ensure tests use correct database URL
   export DATABASE_URL="postgresql://test_user:test_password@localhost:5433/test_iris_db"
   ```

3. **Test Isolation Strategy**
   ```bash
   # Run specific working tests first
   pytest app/tests/smoke/test_basic.py::test_health_endpoint -v
   ```

### Medium Priority
1. **Environment Configuration**
   - Create comprehensive `.env.test` file
   - Document all required environment variables
   - Add environment validation in test setup

2. **Test Helper Functions**
   ```python
   # Create authenticated test client helper
   async def get_authenticated_client():
       client = TestClient(app)
       response = client.post(
           "/api/v1/auth/login",
           json={"username": "admin", "password": "admin123"}
       )
       token = response.json()["access_token"]
       client.headers = {"Authorization": f"Bearer {token}"}
       return client
   ```

3. **Docker Test Integration**
   - Implement test commands that ensure Docker services
   - Add service health checks
   - Create test database reset procedures

## Success Metrics

### Target Goals
- **Authentication Tests**: 100% pass rate
- **Smoke Tests**: 90%+ pass rate  
- **Full Test Suite**: 85%+ pass rate
- **CI/CD Integration**: Automated test execution

### Current Blockers
1. Format mismatch (authentication)
2. Database connection configuration
3. Environment variable handling
4. Import path resolution

## Status: ANALYSIS COMPLETE - ACTION PLAN READY

Comprehensive troubleshooting analysis completed. Ready for systematic resolution.
