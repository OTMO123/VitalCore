# Test Reliability Fixes - Phase 2 Plan

## Overview

Phase 1 is complete with utilities created and 2 critical tests fixed.
This document outlines Phase 2 fixes based on analysis of remaining issues.

**Date:** 2025-11-08
**Branch:** claude/audit-test-reliability-011CUvVdL7NDTpA777eAanrq

---

## Current State

### ✅ Phase 1 Complete

- **Test utilities created:** 3 modules (~550 lines)
- **Timing dependencies fixed:** 2 critical tests
- **Skip-on-error patterns fixed:** 2 tests
- **Documentation created:** 3 comprehensive documents
- **Demonstration:** Fully working test utilities demo

### 📊 Remaining Issues

| Issue Type | Count | Priority |
|------------|-------|----------|
| Timing dependencies (`sleep` calls) | 68 | HIGH |
| Skip-on-error patterns | 38 | HIGH |
| Mock-based tests needing separation | 46 | MEDIUM |
| Tests requiring reorganization | 90 | MEDIUM |

---

## Phase 2 Priority Fixes

### 1. High-Priority Timing Dependencies

Files with most `sleep()` calls requiring immediate fixes:

#### **app/tests/core/test_clinical_decision_support.py** (20 sleep calls)
**Impact:** Critical healthcare decision logic tests
**Action:** Replace all sleeps with EventCollector pattern
**Estimated effort:** 2-3 hours

#### **app/tests/core/test_event_bus.py** (12 sleep calls)
**Impact:** Core event system reliability
**Action:** Use EventCollector for all event waiting
**Estimated effort:** 1-2 hours

#### **app/tests/test_containers_config.py** (6 sleep calls)
**Impact:** Container startup reliability
**Action:** Replace with proper container health checks
**Estimated effort:** 1 hour

#### **app/tests/performance/test_***.py** (Multiple files, ~12 sleep calls)
**Impact:** Performance test reliability
**Action:** Use condition-based waiting with metrics
**Estimated effort:** 2-3 hours

#### **app/tests/core/test_load_testing.py** (3 sleep calls)
**Impact:** Load testing accuracy
**Action:** Event-based synchronization
**Estimated effort:** 1 hour

#### **app/tests/core/test_disaster_recovery.py** (3 sleep calls)
**Impact:** Critical disaster recovery tests
**Action:** Proper async coordination
**Estimated effort:** 1 hour

#### **app/tests/core/test_api_optimization.py** (3 sleep calls)
**Impact:** API performance tests
**Action:** Metrics-based waiting
**Estimated effort:** 1 hour

#### **app/tests/smoke/test_auth_flow.py** (2 sleep calls)
**Impact:** Authentication smoke tests
**Action:** Event-based auth flow validation
**Estimated effort:** 30 minutes

#### **app/tests/integration/test_example_integration.py** (2 remaining)
**Impact:** Example integration tests
**Action:** Apply EventCollector pattern
**Estimated effort:** 30 minutes

### 2. High-Priority Skip-on-Error Patterns

Files requiring fail-on-error conversion (38 instances):

#### **app/tests/test_containers_config.py**
- 3 skip conditions for testcontainers
- **Action:** Convert to fail with installation instructions
- **Status:** 1 already fixed in conftest.py

#### **app/tests/security/test_ml_security_comprehensive.py**
- 7 skip conditions for ML dependencies
- **Action:** Fail with clear dependency installation guide
- **Impact:** ML security tests properly validated

#### **app/tests/api/test_fhir_rest_api_complete.py**
- 2 skip conditions for database dependencies
- **Action:** Fail if aiosqlite missing
- **Impact:** FHIR API tests always run

#### **app/tests/integration/test_iris_api_comprehensive.py**
- 2 skip conditions (timeout, database)
- **Action:** Fail with specific error messages
- **Status:** 1 already fixed (timeout)

#### **Remaining files with skip patterns:**
Check each of these:
```bash
app/tests/infrastructure/test_system_health.py
app/tests/performance/test_windows_performance_fixes.py
app/tests/core/security/test_authorization.py
app/tests/core/security/test_audit_logging.py
app/tests/core/healthcare_records/test_consent_management.py
app/tests/core/healthcare_records/test_phi_encryption.py
```

---

## Detailed Fix Plans

### Fix Template for Timing Dependencies

**Before:**
```python
async def test_something():
    await trigger_event()
    await asyncio.sleep(0.1)  # Hope it completes
    assert result_exists()
```

**After:**
```python
from app.tests.utils.event_utils import EventCollector

async def test_something():
    collector = EventCollector()

    async def wrapped_handler(event):
        # Original handler logic
        await collector.collect(event)

    await trigger_event()
    received = await collector.wait_for_event(timeout=5.0)
    assert received, "Event not processed within timeout"
    assert result_exists()
```

### Fix Template for Skip-on-Error

**Before:**
```python
try:
    import optional_dependency
except ImportError:
    pytest.skip("optional_dependency not available")
```

**After:**
```python
try:
    import optional_dependency
except ImportError as e:
    pytest.fail(
        f"Test requires 'optional_dependency' but it is not installed: {e}\n"
        f"Install with: pip install optional_dependency\n"
        f"Or: pip install -r requirements-test.txt"
    )
```

---

## Execution Plan

### Week 1: Critical Timing Dependencies

**Day 1-2:** Fix top 3 files
- `test_clinical_decision_support.py` (20 sleeps)
- `test_event_bus.py` (12 sleeps)
- `test_containers_config.py` (6 sleeps)

**Day 3-4:** Fix performance tests
- All `test_performance_*.py` files
- `test_load_testing*.py` files

**Day 5:** Fix remaining high-priority
- `test_disaster_recovery.py`
- `test_api_optimization.py`
- `test_auth_flow.py`

### Week 2: Skip-on-Error Patterns

**Day 1-2:** Fix ML and security tests
- `test_ml_security_comprehensive.py` (7 skips)
- All security test files with skips

**Day 3-4:** Fix integration tests
- `test_fhir_rest_api_complete.py`
- `test_iris_api_comprehensive.py`
- Other integration test skips

**Day 5:** Verify and test all fixes
- Run full test suite
- Document fixes
- Update audit report

### Week 3: Reorganization

**Day 1-3:** Create new structure
```
app/tests/
├── unit/               # Pure unit tests (mocks OK)
├── integration/        # Real service integration
├── e2e/               # End-to-end workflows
├── performance/       # Load and performance
└── utils/            # Test utilities ✓ (done)
```

**Day 4-5:** Move tests to appropriate directories
- Identify unit vs integration tests
- Move files with updates to imports
- Update documentation

---

## Success Metrics

### Phase 2 Goals

| Metric | Target | Current |
|--------|--------|---------|
| Timing dependencies | 0 | 68 |
| Skip-on-error patterns | 0 | 38 |
| Tests using EventCollector | 30+ | 2 |
| Properly categorized tests | 100% | ~20% |

### Expected Outcomes

After Phase 2 completion:

1. **Zero arbitrary sleeps** in test suite
2. **Zero silent skips** - all failures are explicit
3. **Clear test categories** - unit/integration/e2e
4. **Reliable test execution** on all systems
5. **Fast test runs** - no unnecessary waits
6. **Clear error messages** when tests fail

---

## Commands for Implementation

### Find Files to Fix

```bash
# Find files with most timing dependencies
grep -r "asyncio\.sleep\|time\.sleep" app/tests --include="*.py" | \
  grep -v "utils/" | cut -d: -f1 | sort | uniq -c | sort -rn

# Find files with skip patterns
grep -r "pytest\.skip" app/tests --include="*.py" | \
  grep -v "utils/" | cut -d: -f1 | sort | uniq

# Check specific file
grep -n "asyncio\.sleep\|pytest\.skip" app/tests/core/test_event_bus.py
```

### Test Individual Fixes

```bash
# Test fixed file
pytest app/tests/core/test_event_bus.py -v

# Run only tests using new utilities
pytest -k "test_event_bus_integration" -v

# Verify no timing dependencies in fixed file
grep "asyncio\.sleep" app/tests/core/test_event_bus.py && \
  echo "Still has sleeps!" || echo "Clean!"
```

### Progress Tracking

```bash
# Count remaining issues
echo "Timing dependencies: $(grep -r 'asyncio\.sleep\|time\.sleep' app/tests \
  --include='*.py' | grep -v 'utils/' | wc -l)"

echo "Skip patterns: $(grep -r 'pytest\.skip' app/tests \
  --include='*.py' | grep -v 'utils/' | wc -l)"
```

---

## Risk Assessment

### Low Risk Fixes
- Individual test file timing dependencies
- Skip-on-error in standalone tests
- Mock test categorization

### Medium Risk Fixes
- Event bus timing dependencies (affects many tests)
- Performance test changes (may need threshold adjustments)
- Container health check changes

### High Risk Fixes
- Core test infrastructure changes (conftest.py)
- Test reorganization (may break imports)
- Pytest configuration changes

**Mitigation:** Fix and test incrementally, commit after each file

---

## Rollback Plan

If fixes cause issues:

1. **Individual test failures:** Revert specific test file
2. **Infrastructure issues:** Revert conftest.py changes
3. **Import errors:** Check and fix moved file imports
4. **Complete rollback:** Git revert to Phase 1 completion

---

## Documentation Updates

After Phase 2, update:

1. **TEST_RELIABILITY_AUDIT_REPORT.md**
   - Update statistics
   - Mark fixed issues
   - Update reliability scores

2. **TEST_IMPROVEMENT_PLAN.md**
   - Mark Phase 2 complete
   - Update progress percentages

3. **test_reliability_issues.csv**
   - Mark fixed issues as resolved
   - Add resolution notes

4. **Create PHASE_2_COMPLETION_REPORT.md**
   - Summary of all fixes
   - Before/after metrics
   - Lessons learned

---

## Next Phase Preview

### Phase 3: Test Quality Improvements

1. **Add contract testing** for external APIs
2. **Implement test containers** for integration tests
3. **Performance test baselines** and thresholds
4. **Test data management** improvements
5. **CI/CD pipeline** configuration

### Phase 4: Maintenance & Monitoring

1. **Automated reliability checks** in CI
2. **Test execution time** monitoring
3. **Flaky test detection** and prevention
4. **Regular test suite audits**
5. **Developer documentation** and training

---

## Resources

- **Test utilities:** `app/tests/utils/`
- **Demonstration:** `test_utilities_demo.py`
- **Audit report:** `TEST_RELIABILITY_AUDIT_REPORT.md`
- **Issue tracking:** `test_reliability_issues.csv`

---

## Questions & Support

### Common Questions

**Q: Why fail instead of skip?**
A: Skips hide environment problems. Failures force fixes.

**Q: Why replace all sleeps?**
A: Sleeps are unreliable and waste time. Event-based waiting is deterministic.

**Q: Can I keep sleeps in performance tests?**
A: No. Use metrics and condition-based waiting for reliable performance tests.

**Q: What about third-party code with sleeps?**
A: That's fine. Only our test code needs fixes.

### Getting Help

- Review `test_utilities_demo.py` for examples
- Check `app/tests/integration/test_example_integration.py` for real usage
- See `TEST_FIXES_SUMMARY.md` for patterns

---

**Status:** Ready for Phase 2 implementation
**Estimated Duration:** 3 weeks
**Expected Improvement:** 70% → 90% test reliability
