# Test Improvement Implementation Plan

## Phase 1: Immediate Fixes (Current Sprint)

### 1.1 Install Missing Dependencies ✓
- [x] structlog
- [x] brotli
- [x] aiosqlite
- [x] fakeredis
- [x] marshmallow

### 1.2 Create Test Utilities
- [ ] Event completion utilities (`app/tests/utils/event_utils.py`)
- [ ] Test data factories (`app/tests/utils/factories.py`)
- [ ] Mock fixtures (`app/tests/utils/fixtures.py`)

### 1.3 Fix Critical Timing Dependencies
- [ ] `app/tests/integration/test_example_integration.py:94` - Event bus wait
- [ ] `app/tests/integration/test_iris_api_simple.py:18` - Timeout handling
- [ ] `app/tests/core/test_event_bus.py` - Graceful shutdown waits

### 1.4 Replace Skip-on-Error Pattern
- [ ] `app/tests/test_containers_config.py` - 3 skip conditions
- [ ] `app/tests/security/test_ml_security_comprehensive.py` - 7 skip conditions
- [ ] `app/tests/api/test_fhir_rest_api_complete.py` - 2 skip conditions
- [ ] `app/tests/conftest.py:1165` - Container skip

## Phase 2: Structural Reorganization

### 2.1 New Directory Structure
```
app/tests/
├── unit/                    # Pure unit tests with mocks
│   ├── core/
│   ├── modules/
│   └── services/
├── integration/             # Real service integration
│   ├── database/
│   ├── api/
│   ├── external_services/
│   └── event_bus/
├── e2e/                     # End-to-end workflows
│   ├── healthcare/
│   ├── predictive/
│   └── workflows/
├── performance/             # Load and performance tests
├── utils/                   # Test utilities
│   ├── event_utils.py
│   ├── factories.py
│   ├── fixtures.py
│   └── helpers.py
└── conftest.py
```

### 2.2 Migration Plan
- [ ] Create new directory structure
- [ ] Move unit tests (with mocks) to `unit/`
- [ ] Move integration tests to `integration/`
- [ ] Move e2e tests to `e2e/`
- [ ] Update imports in moved files

## Phase 3: Test Quality Improvements

### 3.1 Fix Event Bus Tests
- [ ] Create event completion utility with timeout
- [ ] Replace `asyncio.sleep(0.1)` with proper event waiting
- [ ] Add event acknowledgment mechanism

### 3.2 Fix IRIS API Tests
- [ ] Remove timeout-based skips
- [ ] Separate mock tests (unit) from integration tests
- [ ] Add contract tests for IRIS API

### 3.3 Fix Performance Tests
- [ ] Add performance test markers and configuration
- [ ] Use percentile-based assertions
- [ ] Document required resources

### 3.4 Fix Database Tests
- [ ] Replace mock database URLs with real test database
- [ ] Use test containers for PostgreSQL
- [ ] Add proper connection pool tests

## Phase 4: Configuration Updates

### 4.1 Update pytest.ini
- [ ] Simplify test markers (reduce from 67 to ~15 essential ones)
- [ ] Add clear test categories
- [ ] Configure separate test stages

### 4.2 Update conftest.py
- [ ] Add utility fixtures
- [ ] Improve container management
- [ ] Add better error handling

### 4.3 Create CI/CD Configuration
- [ ] Stage 1: Unit tests (fast, no containers)
- [ ] Stage 2: Integration tests (with containers)
- [ ] Stage 3: E2E tests (full stack)
- [ ] Stage 4: Performance tests (nightly)

## Implementation Status

| Phase | Status | Progress |
|-------|--------|----------|
| Phase 1: Immediate Fixes | In Progress | 10% |
| Phase 2: Structural Reorganization | Not Started | 0% |
| Phase 3: Test Quality Improvements | Not Started | 0% |
| Phase 4: Configuration Updates | Not Started | 0% |

## Success Criteria

- [ ] All unit tests pass independently (no external dependencies)
- [ ] Integration tests run successfully with containers
- [ ] No timing-based waits (asyncio.sleep) in tests
- [ ] No skip-on-error patterns (fail instead)
- [ ] Test pass rate > 80% for unit tests
- [ ] Test pass rate > 70% for integration tests
- [ ] Clear separation between test types
- [ ] Tests run in < 5 minutes for unit, < 15 minutes for integration

## Notes

- Prioritize fixes that provide immediate reliability improvements
- Maintain backward compatibility during reorganization
- Document all changes in commit messages
- Update TEST_RELIABILITY_AUDIT_REPORT.md with progress
