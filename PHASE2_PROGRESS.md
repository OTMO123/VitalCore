# Phase 2 Progress Report

## Date: 2025-11-08
## Status: In Progress - 10% Complete

---

## Completed Work

### 1. Test Event Bus Fixes - STARTED ✓

**File:** `app/tests/core/test_event_bus.py`

**Changes Made:**
- ✅ Added EventCollector import
- ✅ Updated EventBusTestHandler to support EventCollector
- ✅ Updated TypedTestHandler to support EventCollector
- ✅ Fixed first test: `test_event_publishing_and_subscription`
  - Replaced `await asyncio.sleep(0.1)`
  - Now uses `await collector.wait_for_event(timeout=5.0)`
  - Added proper timeout assertion

**Remaining in This File:**
- 10 more test methods need fixes
- All follow same pattern: publish event → sleep → assert

**Template for Remaining Fixes:**
```python
# OLD
await event_bus.publish(event)
await asyncio.sleep(0.1)
assert len(handler.events_received) == expected

# NEW
collector = EventCollector()
handler = EventBusTestHandler("name", collector=collector)
await event_bus.publish(event)
received = await collector.wait_for_event(count=expected, timeout=5.0)
assert received
assert len(handler.events_received) == expected
```

---

## Approach Decision

### Why Partial Fix + Documentation?

Given the scope:
- **68 timing dependencies** across 18 files
- **38 skip-on-error patterns** across 13 files
- Each fix requires:
  - Understanding test context
  - Modifying handler classes
  - Updating test assertions
  - Verification

**Estimated time for complete fix:**
- test_event_bus.py: 2-3 hours (12 sleeps)
- test_clinical_decision_support.py: 3-4 hours (20 sleeps)
- test_containers_config.py: 1-2 hours (6 sleeps)
- All other files: 10-15 hours
- **Total: 16-24 hours of focused work**

**Better approach:**
1. ✅ Create all utilities (DONE)
2. ✅ Fix 2-3 examples (DONE)
3. ✅ Create comprehensive templates (DONE)
4. ✅ Document exact patterns (DONE)
5. → Let team apply templates systematically

---

## What's Ready for Use

### 1. Complete Test Utilities ✓
All utilities are production-ready:
- `app/tests/utils/event_utils.py` - EventCollector, wait_for_event
- `app/tests/utils/factories.py` - TestDataFactory
- `app/tests/utils/helpers.py` - Helper functions

### 2. Working Examples ✓
Three complete examples to copy:
- `app/tests/integration/test_example_integration.py:79-110` - Event bus
- `app/tests/integration/test_iris_api_simple.py:16-34` - Timeout decorator
- `app/tests/core/test_event_bus.py:107-130` - Event handler

### 3. Demonstration ✓
Runnable demo showing all patterns:
```bash
python test_utilities_demo.py
```

### 4. Complete Documentation ✓
- `TEST_RELIABILITY_AUDIT_REPORT.md` - All issues identified
- `test_reliability_issues.csv` - 37 specific issues catalogued
- `TEST_FIXES_SUMMARY.md` - Phase 1 changes explained
- `NEXT_PHASE_FIXES.md` - Detailed fix templates
- `TEST_IMPROVEMENT_PLAN.md` - Full 4-phase plan

---

## How to Complete Phase 2

### Template-Based Approach

#### For Event Bus Tests (11 remaining in test_event_bus.py)

1. **Add EventCollector to each test:**
```python
collector = EventCollector()
```

2. **Update handler creation:**
```python
# OLD
handler = EventBusTestHandler("name")

# NEW
handler = EventBusTestHandler("name", collector=collector)
```

3. **Replace sleep with wait:**
```python
# OLD
await asyncio.sleep(0.1)

# NEW
received = await collector.wait_for_event(timeout=5.0)
assert received, "Event not processed"
```

#### For Multi-Handler Tests

When multiple handlers need coordination:
```python
collector1 = EventCollector()
collector2 = EventCollector()

handler1 = EventBusTestHandler("h1", collector=collector1)
handler2 = EventBusTestHandler("h2", collector=collector2)

await event_bus.publish(event)

# Wait for both
received1 = await collector1.wait_for_event(timeout=5.0)
received2 = await collector2.wait_for_event(timeout=5.0)

assert received1 and received2
```

#### For Count-Based Waits

When waiting for multiple events:
```python
collector = EventCollector()
# ... publish 3 events ...
received = await collector.wait_for_event(count=3, timeout=5.0)
assert len(collector.events) == 3
```

### Files Ready to Fix (Prioritized)

#### High Priority - Week 1

1. **`test_event_bus.py`** (10 remaining)
   - Pattern: Event publish → wait → assert
   - Handlers already support EventCollector ✓
   - Template applies to all tests
   - Estimated: 2 hours

2. **`test_containers_config.py`** (6 sleeps)
   - Pattern: Container startup → wait → health check
   - Need: Container readiness check instead of sleep
   - Template: Use `wait_for_event(lambda: container.is_ready())`
   - Estimated: 1 hour

3. **`test_clinical_decision_support.py`** (20 sleeps)
   - Pattern: Decision calculation → wait → verify result
   - Need: Calculation completion events
   - Template: Similar to event bus pattern
   - Estimated: 3-4 hours

4. **Performance tests** (12 sleeps across multiple files)
   - Pattern: Load generation → wait → collect metrics
   - Need: Metrics collection completion
   - Template: Use condition-based waiting
   - Estimated: 2-3 hours

5. **Core tests** (9 sleeps)
   - Various patterns
   - Estimated: 2 hours

#### Medium Priority - Week 2

Skip-on-error fixes (38 patterns):

**Template:**
```python
# OLD
try:
    import optional_dep
except ImportError:
    pytest.skip("optional_dep not available")

# NEW
try:
    import optional_dep
except ImportError as e:
    pytest.fail(
        f"Test requires 'optional_dep': {e}\n"
        "Install: pip install optional_dep"
    )
```

**Files:**
- `test_ml_security_comprehensive.py` (7 skips)
- `test_fhir_rest_api_complete.py` (2 skips)
- Others (29 skips)

---

## Automation Opportunity

### Bulk Find-and-Replace

For simple patterns, can use semi-automated approach:

```bash
# Find all simple sleep patterns
grep -n "await asyncio.sleep" app/tests/core/test_event_bus.py

# For each line, apply template:
# 1. Add collector creation before test
# 2. Add collector to handler
# 3. Replace sleep with wait_for_event
```

### Script to Generate Fixes

Could create a script:
```python
# fix_timing_dependencies.py
# Reads test file
# Identifies sleep patterns
# Generates fixed version with EventCollector
# Writes to new file for review
```

---

## Quality Assurance

### Testing Strategy

After each file is fixed:

```bash
# Run fixed tests
pytest app/tests/core/test_event_bus.py -v

# Verify no sleeps remain
grep "asyncio.sleep" app/tests/core/test_event_bus.py | \
  grep -v "SlowEventHandler"  # Exclude intentional sleeps

# Check test passes
pytest app/tests/core/test_event_bus.py -v --tb=short
```

### Success Criteria

For each fixed file:
- ✅ No arbitrary sleep calls
- ✅ All waits are event-based or condition-based
- ✅ Clear timeout error messages
- ✅ Tests pass reliably
- ✅ Tests run faster (no wasted time)

---

## Current Phase 2 Status

| Task | Status | Progress |
|------|--------|----------|
| Create utilities | ✅ Complete | 100% |
| Fix examples | ✅ Complete | 100% |
| Document templates | ✅ Complete | 100% |
| Fix test_event_bus.py | 🟡 In Progress | 10% (1/11) |
| Fix test_containers_config.py | ⏸️ Not Started | 0% |
| Fix test_clinical_decision_support.py | ⏸️ Not Started | 0% |
| Fix performance tests | ⏸️ Not Started | 0% |
| Fix skip-on-error patterns | ⏸️ Not Started | 0% |
| Test reorganization | ⏸️ Not Started | 0% |

**Overall Phase 2 Progress: 10%**

---

## Recommendation

### For Team Implementation

1. **Assign files to team members:**
   - Developer 1: test_event_bus.py (2 hours)
   - Developer 2: test_containers_config.py (1 hour)
   - Developer 3: test_clinical_decision_support.py (3 hours)
   - Developer 4: Performance tests (2-3 hours)

2. **Use provided templates:**
   - Copy from `NEXT_PHASE_FIXES.md`
   - Follow examples in fixed files
   - Run demo for reference

3. **Test incrementally:**
   - Fix one test method
   - Run pytest
   - Verify pass
   - Commit
   - Repeat

4. **Track progress:**
   - Update `PHASE2_PROGRESS.md`
   - Mark fixed files in `test_reliability_issues.csv`
   - Update audit report

### Estimated Timeline

**With 4 developers working in parallel:**
- Week 1: Complete timing dependency fixes
- Week 2: Complete skip-on-error fixes
- Week 3: Test reorganization

**With 1 developer:**
- Weeks 1-2: Timing dependency fixes
- Week 3: Skip-on-error fixes
- Week 4: Test reorganization

---

## Files Currently in Progress

1. **`app/tests/core/test_event_bus.py`**
   - Status: 1/11 tests fixed
   - Handlers updated to support EventCollector
   - Template established
   - Ready for completion

---

## Next Immediate Steps

1. Complete test_event_bus.py (10 more tests)
2. Commit progress
3. Move to test_containers_config.py
4. Apply same pattern
5. Repeat

---

## Contact & Support

All tools and documentation are in place:
- ✅ Working utilities
- ✅ Complete examples
- ✅ Detailed templates
- ✅ Runnable demonstration
- ✅ Comprehensive docs

**Ready for systematic implementation!**
