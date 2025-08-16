# Comprehensive Security Scanner

## Overview

The `comprehensive-security-scan.ps1` script is a security audit tool that scans all router files in the system for security violations, specifically focusing on violations of the service layer architecture pattern.

## What It Checks

### High Severity Violations (🚨)
- **Direct SQL Query Construction**: `select(Model).where()`
- **Direct Database Execution**: `await db.execute()`, `await db.commit()`
- **Direct ORM Query Usage**: `db.query()`
- **Direct Session Manipulation**: `session.add()`, `session.commit()`, etc.

### Medium Severity Violations (⚠️)
- **Database Dependency Injection**: `db: AsyncSession = Depends(get_db)` in routers
- **Direct Model Imports**: Importing database models directly in routers

## Usage

### Basic Scan
```powershell
.\scripts\comprehensive-security-scan.ps1
```

### Verbose Output
```powershell
.\scripts\comprehensive-security-scan.ps1 -Verbose
```

### Export Results to JSON
```powershell
.\scripts\comprehensive-security-scan.ps1 -ExportJson -OutputPath "security_results.json"
```

### Combined Options
```powershell
.\scripts\comprehensive-security-scan.ps1 -Verbose -ExportJson
```

## Output

The script provides:

1. **File-by-file analysis** with violation counts
2. **Security score** (percentage of clean files)
3. **Violation type breakdown** by severity
4. **Detailed violation listings** (with -Verbose)
5. **Priority fix recommendations**
6. **JSON export** for automation (with -ExportJson)

## Interpretation

### Security Scores
- **100%**: 🎉 Excellent - All files follow best practices
- **80-99%**: ⚠️ Good - Minor violations need attention
- **60-79%**: 🚨 Moderate - Significant violations found
- **<60%**: 💥 Critical - Major violations require immediate action

### Current State (as of scan)
- **Total Files**: 11 router files scanned
- **Security Score**: 0% (all files have violations)
- **Total Violations**: 124 violations found
- **High Severity**: Multiple direct database access violations
- **Medium Severity**: All routers bypass service layer

## Fixing Violations

### Service Layer Pattern
Replace direct database access with service layer:

```python
# ❌ VIOLATION - Direct database dependency
@router.get("/patients")
async def get_patients(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Patient).where(...))
    return result.scalars().all()

# ✅ CORRECT - Service layer usage
@router.get("/patients") 
async def get_patients(service = Depends(get_healthcare_service)):
    return await service.get_patients(...)
```

### Architecture Compliance
Follow the DDD bounded context patterns:
- Router → Service → Repository
- No direct database access in routers
- Use dependency injection for services, not database sessions

## Integration

This script can be integrated into:
- **CI/CD pipelines** (exits with code 1 if violations found)
- **Pre-commit hooks** for code quality checks
- **Automated security audits** with JSON output
- **Development workflows** for architecture compliance

## Files Scanned

The script automatically scans these router files:
- `app/modules/analytics/router.py`
- `app/modules/audit_logger/router.py`
- `app/modules/audit_logger/security_router.py`
- `app/modules/auth/router.py`
- `app/modules/dashboard/router.py`
- `app/modules/document_management/router.py`
- `app/modules/healthcare_records/router.py`
- `app/modules/iris_api/router.py`
- `app/modules/purge_scheduler/router.py`
- `app/modules/risk_stratification/router.py`
- `app/modules/security_audit/router.py`