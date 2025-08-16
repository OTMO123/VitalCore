# IRIS API Integration System - Testing Guide

This document provides comprehensive guidance for testing the IRIS API Integration System, including setup, execution, and best practices.

## Table of Contents

- [Overview](#overview)
- [Test Infrastructure](#test-infrastructure)
- [Quick Start](#quick-start)
- [Test Categories](#test-categories)
- [Running Tests](#running-tests)
- [Test Configuration](#test-configuration)
- [Fixtures and Utilities](#fixtures-and-utilities)
- [Best Practices](#best-practices)
- [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#troubleshooting)

## Overview

The testing infrastructure is designed to support comprehensive testing of the IRIS API Integration System with:

- **Multiple test categories**: Unit, integration, security, performance, and end-to-end tests
- **Async support**: Full async/await testing capabilities
- **Test containers**: Real database and service testing with Docker containers
- **Coverage reporting**: Comprehensive code coverage analysis
- **Performance monitoring**: Benchmarking and performance regression detection
- **Security testing**: Authentication, authorization, and security compliance tests

## Test Infrastructure

### Key Components

1. **pytest.ini**: Main pytest configuration with markers and settings
2. **conftest.py**: Comprehensive fixtures for all testing scenarios
3. **pyproject.toml**: Modern Python project configuration with tool settings
4. **.coveragerc**: Coverage configuration for detailed reporting
5. **docker-compose.test.yml**: Test services orchestration
6. **run_tests.py**: Advanced test runner with rich reporting
7. **Makefile**: Convenient commands for all testing scenarios

### Test Markers

Tests are categorized using pytest markers:

- `unit`: Fast, isolated unit tests
- `integration`: Integration tests with external dependencies
- `security`: Security and authentication tests
- `performance`: Performance and benchmark tests
- `api`: API endpoint tests
- `database`: Database-related tests
- `event_bus`: Event bus and messaging tests
- `iris_api`: IRIS API integration tests
- `auth`: Authentication and authorization tests
- `audit`: Audit logging tests
- `purge`: Data purge and retention tests
- `smoke`: Basic functionality smoke tests
- `regression`: Regression tests
- `e2e`: End-to-end tests
- `slow`: Tests that take significant time
- `requires_containers`: Tests requiring Docker containers

## Quick Start

### 1. Install Dependencies

```bash
# Install all dependencies including test tools
pip install -r requirements.txt

# Or install with optional dependencies
pip install -e ".[test,dev]"
```

### 2. Setup Test Environment

```bash
# Set up test environment
make setup-test-env

# Start test services (PostgreSQL, Redis, Mock API)
make start-services
```

### 3. Run Tests

```bash
# Run all tests
make test

# Run specific test categories
make test-unit
make test-integration
make test-security

# Run with coverage
make test-coverage

# Use the advanced test runner
python run_tests.py --all --coverage --report
```

## Test Categories

### Unit Tests
- **Purpose**: Test individual components in isolation
- **Speed**: Fast (< 1 second per test)
- **Dependencies**: None (mocked)
- **Command**: `pytest -m "unit"`

```python
@pytest.mark.unit
def test_password_hashing():
    password = "test_password"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed)
```

### Integration Tests
- **Purpose**: Test component interactions
- **Speed**: Medium (1-10 seconds per test)
- **Dependencies**: Database, Redis, external APIs
- **Command**: `pytest -m "integration"`

```python
@pytest.mark.integration
@pytest.mark.database
async def test_user_creation(db_session: AsyncSession):
    user = User(username="test", email="test@example.com")
    db_session.add(user)
    await db_session.commit()
    assert user.id is not None
```

### Security Tests
- **Purpose**: Test authentication, authorization, and security
- **Speed**: Medium (1-5 seconds per test)
- **Dependencies**: Database, authentication services
- **Command**: `pytest -m "security"`

```python
@pytest.mark.security
@pytest.mark.auth
async def test_unauthorized_access(async_test_client: AsyncClient):
    response = await async_test_client.get("/protected")
    assert response.status_code == 401
```

### Performance Tests
- **Purpose**: Benchmark performance and detect regressions
- **Speed**: Slow (10+ seconds per test)
- **Dependencies**: Database, full services
- **Command**: `pytest -m "performance" --benchmark-only`

```python
@pytest.mark.performance
def test_user_query_performance(benchmark, db_session):
    result = benchmark(lambda: db_session.query(User).all())
    assert len(result) > 0
```

### API Tests
- **Purpose**: Test REST API endpoints
- **Speed**: Medium (1-5 seconds per test)
- **Dependencies**: Full application, database
- **Command**: `pytest -m "api"`

```python
@pytest.mark.api
async def test_user_registration(async_test_client: AsyncClient):
    response = await async_test_client.post("/auth/register", json={
        "username": "newuser",
        "email": "new@example.com",
        "password": "password123"
    })
    assert response.status_code == 201
```

## Running Tests

### Using Make Commands

```bash
# Basic test commands
make test                 # Run all tests
make test-unit           # Unit tests only
make test-integration    # Integration tests only
make test-security       # Security tests only
make test-performance    # Performance tests only

# Advanced test commands
make test-coverage       # Run with coverage report
make test-parallel       # Run tests in parallel
make test-containers     # Run with real containers
make test-watch          # Watch mode for development

# Service management
make start-services      # Start test services
make stop-services       # Stop test services
```

### Using pytest Directly

```bash
# Run specific test categories
pytest -m "unit and not slow"
pytest -m "integration"
pytest -m "security"

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test files
pytest app/tests/test_auth.py
pytest app/tests/test_event_bus.py

# Run with parallel execution
pytest -n auto

# Run with verbose output
pytest -v --tb=short
```

### Using the Advanced Test Runner

```bash
# Run all tests with rich output
python run_tests.py --all

# Run specific suites
python run_tests.py unit integration

# Run with coverage and generate reports
python run_tests.py --all --coverage --report --json-report

# Quick development cycle
python run_tests.py --quick

# CI/CD mode
python run_tests.py --ci
```

## Test Configuration

### Environment Variables

Tests use the following environment variables:

```bash
ENVIRONMENT=test
DEBUG=false
DATABASE_URL=postgresql://test_user:test_pass@localhost:5432/test_iris_db
REDIS_URL=redis://localhost:6379/1
SECRET_KEY=test_secret_key_32_characters_long
ENCRYPTION_KEY=test_encryption_key_32_chars_long
IRIS_API_BASE_URL=http://localhost:8001/mock
```

### pytest.ini Configuration

Key configuration options:

```ini
[tool:pytest]
testpaths = app/tests
addopts = --strict-markers --cov=app --cov-fail-under=80
markers = unit: Unit tests (fast, isolated)
asyncio_mode = auto
timeout = 300
```

### Coverage Configuration

Coverage settings in `.coveragerc`:

```ini
[run]
source = app
branch = True
parallel = True

[report]
show_missing = True
fail_under = 80
exclude_lines = pragma: no cover
```

## Fixtures and Utilities

### Database Fixtures

```python
# Test database session
async def test_with_db(db_session: AsyncSession):
    user = User(username="test")
    db_session.add(user)
    await db_session.commit()

# Test user creation
async def test_with_user(test_user: User):
    assert test_user.username == "testuser"
```

### Authentication Fixtures

```python
# Authenticated requests
async def test_protected_endpoint(auth_headers: Dict[str, str], async_test_client: AsyncClient):
    response = await async_test_client.get("/protected", headers=auth_headers)
    assert response.status_code == 200
```

### Event Bus Fixtures

```python
# Event bus testing
async def test_events(test_event_bus: EventBus, mock_event_handler: AsyncMock):
    test_event_bus.subscribe(EventType.USER_LOGIN, mock_event_handler)
    await test_event_bus.publish(Event(event_type=EventType.USER_LOGIN))
```

### Container Fixtures

```python
# Real containers (requires testcontainers)
@pytest.mark.requires_containers
async def test_with_containers(container_db_session: AsyncSession):
    # Test with real PostgreSQL container
    pass
```

## Best Practices

### Test Structure

1. **Arrange-Act-Assert**: Structure tests clearly
2. **One assertion per test**: Focus on single behavior
3. **Descriptive names**: Use clear, descriptive test names
4. **Use fixtures**: Leverage pytest fixtures for setup

```python
@pytest.mark.unit
def test_password_validation_rejects_weak_passwords():
    # Arrange
    weak_password = "123"
    
    # Act
    is_valid = validate_password(weak_password)
    
    # Assert
    assert is_valid is False
```

### Async Testing

```python
@pytest.mark.asyncio
async def test_async_operation():
    result = await async_function()
    assert result is not None
```

### Mocking External Services

```python
@pytest.mark.unit
@patch('app.services.external_api.make_request')
def test_external_api_integration(mock_request):
    mock_request.return_value = {"status": "success"}
    result = call_external_api()
    assert result["status"] == "success"
```

### Performance Testing

```python
@pytest.mark.performance
def test_query_performance(benchmark):
    result = benchmark(expensive_operation)
    assert result is not None
```

### Security Testing

```python
@pytest.mark.security
async def test_sql_injection_protection(async_test_client: AsyncClient):
    malicious_input = "'; DROP TABLE users; --"
    response = await async_test_client.get(f"/search?q={malicious_input}")
    assert response.status_code != 500
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: make ci-install
      - name: Run tests
        run: python run_tests.py --ci --coverage --json-report
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Test Reports

The test runner generates multiple report formats:

- **HTML Coverage**: `htmlcov/index.html`
- **XML Coverage**: `coverage.xml` (for CI/CD)
- **JSON Report**: `test-report.json`
- **JUnit XML**: `test-results.xml`

## Troubleshooting

### Common Issues

1. **Database connection errors**:
   ```bash
   make start-services
   # Wait for services to be ready
   ```

2. **Import errors**:
   ```bash
   pip install -e .
   export PYTHONPATH=.
   ```

3. **Async test issues**:
   ```python
   # Ensure asyncio mode is set
   pytest_plugins = ['pytest_asyncio']
   ```

4. **Container issues**:
   ```bash
   # Check Docker is running
   docker ps
   # Clean up containers
   make clean-containers
   ```

### Debug Mode

```bash
# Run tests with debugging
pytest --pdb --tb=long

# Use the test runner debug mode
python run_tests.py unit --debug
```

### Verbose Logging

```bash
# Enable verbose logging
pytest -v --log-cli-level=DEBUG

# Show test output
pytest -s
```

## Advanced Features

### Test Containers

Real service testing with Docker containers:

```python
@pytest.mark.requires_containers
async def test_with_real_postgres(container_db_session):
    # Uses real PostgreSQL container
    pass
```

### Performance Benchmarking

```python
@pytest.mark.performance
def test_benchmark(benchmark):
    result = benchmark(function_to_benchmark)
    assert result is not None
```

### Security Scanning

```bash
# Run security scans
make security-scan

# Check for vulnerabilities
bandit -r app/
safety check
```

### Load Testing

```bash
# Start load testing environment
make test-load

# Run custom load tests
locust -f app/tests/load_tests.py
```

This comprehensive testing infrastructure ensures high code quality, security compliance, and performance standards for the IRIS API Integration System.