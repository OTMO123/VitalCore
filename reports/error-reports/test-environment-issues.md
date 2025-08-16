# Test Environment Configuration Issues

## Database Connection Problems

### Primary Issue: PostgreSQL Connection Failures
```
psycopg2.OperationalError: connection to server at "localhost" (::1), port 5432 failed: 
Connection refused: could not connect to PostgreSQL server
```

### Root Cause
- Tests attempting to connect to default PostgreSQL port 5432
- Docker PostgreSQL running on port 5433 (non-standard)
- Environment configuration mismatch

### Configuration Analysis
```python
# From Makefile - Correct test configuration
export DATABASE_URL=postgresql://test_user:test_password@localhost:5433/test_iris_db
export REDIS_URL=redis://localhost:6380/0

# But tests may not be picking up these environment variables
```

## Python Environment Issues

### Command Availability
- `python` command not found in Windows environment
- Had to use `python3` as alternative
- Inconsistent Python executable naming across platforms

### Package Installation
- Some tests require packages not in main requirements.txt
- Development dependencies may not be properly installed

## Test Collection Errors

### Import Issues
```
ImportError: attempted relative import with no known parent package
```

### Module Path Problems
- Some test modules can't find relative imports
- PYTHONPATH may not be properly configured
- Test discovery failing for certain modules

## Cache Conflicts

### Pytest Cache Issues
```
pytest --cache-clear
```
Required to resolve some test collection problems

## Docker Integration

### Service Dependencies
- Tests require specific Docker services to be running
- No automatic service startup in test commands
- Manual coordination required between Docker and tests

## Resolution Recommendations

1. **Environment Configuration**
   - Create `.env.test` file with correct database URLs
   - Ensure test commands load proper environment variables

2. **Python Path Issues**
   - Add proper PYTHONPATH configuration
   - Use consistent Python executable naming

3. **Docker Integration**
   - Implement test commands that start required services
   - Add health checks before running tests

4. **Cache Management**
   - Regular cache clearing in CI/CD pipeline
   - Proper .gitignore for test artifacts

## Status: ACTIVE ISSUES - NEEDS RESOLUTION

These environment issues prevent reliable test execution and need immediate attention.
