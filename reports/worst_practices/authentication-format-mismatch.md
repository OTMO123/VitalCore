# Authentication Format Mismatch - Critical Issue

## Problem Description

The test suite is experiencing a critical authentication format mismatch that prevents proper testing of secured endpoints.

## Root Cause Analysis

### Issue: Form Data vs JSON Content Type
- **Tests sending**: `application/x-www-form-urlencoded` (form data)
- **API expecting**: `application/json` (JSON format)
- **Result**: 422 validation errors instead of proper authentication

### Code Evidence
```python
# INCORRECT (current test implementation)
response = client.post(
    "/api/v1/auth/login",
    data={"username": "admin", "password": "admin123"}
)

# CORRECT (should be)
response = client.post(
    "/api/v1/auth/login",
    json={"username": "admin", "password": "admin123"}
)
```

## Impact Assessment

- **Test Success Rate**: Reduced from potential 100% to 57% (27/47 tests passing)
- **False Negatives**: Authentication tests failing due to format, not logic
- **Development Confidence**: Undermined by unreliable test suite

## Technical Details

### FastAPI Endpoint Configuration
```python
@router.post("/login", response_model=AuthResponse)
async def login(
    credentials: UserLogin,  # Expects JSON via Pydantic model
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> AuthResponse:
```

### Pydantic Model Expectation
```python
class UserLogin(BaseModel):
    username: str
    password: str
```

## Resolution Strategy

1. **Immediate Fix**: Update all authentication test calls to use `json=` parameter
2. **Test Suite Audit**: Review all API test calls for consistent content-type usage
3. **Validation**: Ensure all endpoints properly handle expected content types

## Prevention Measures

- Add content-type validation in test helper functions
- Implement pre-commit hooks to catch format mismatches
- Document API content-type requirements clearly

## Status: CRITICAL - UNRESOLVED

This issue blocks proper testing of the entire authentication system and all secured endpoints.
