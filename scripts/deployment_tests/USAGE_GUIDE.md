# PowerShell Script Usage Guide

## Quick Start (Recommended)

### Run Simple Test First
```powershell
# Test basic connectivity - Russian PowerShell compatible
.\simple_test.ps1

# Or run quick validation with more details
.\quick_test.ps1

# For verbose output
.\quick_test.ps1 -Verbose
```

### Run Fixed Infrastructure Test
```powershell
# Complete infrastructure validation - Fixed for Russian PowerShell
.\1_infrastructure_validation_fixed.ps1
```

## Common Issues and Solutions

### 1. PowerShell Execution Policy
If you get execution policy errors:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# OR run with bypass:
powershell -ExecutionPolicy Bypass -File .\quick_test.ps1
```

### 2. Services Not Running
Start required services first:
```bash
# In WSL/Linux terminal:
docker-compose up -d
python app/main.py
```

### 3. Environment Variables
Ensure these are set:
```
DATABASE_URL=postgresql://healthcare_user:your_password@localhost:5432/healthcare_db
JWT_SECRET_KEY=your-jwt-secret-key-32-chars-minimum
PHI_ENCRYPTION_KEY=your-phi-encryption-key-32-chars-minimum
```

## Test Scripts Available

- **simple_test.ps1** - Basic connectivity test (most compatible)
- **quick_test.ps1** - Fast validation with error handling 
- **1_infrastructure_validation_fixed.ps1** - Complete infrastructure test (Russian PowerShell compatible)
- Original scripts require fixing for Russian PowerShell syntax

## Expected Output

### Success:
```
Database Connection: PASS
Redis Connection: PASS
Application Health: PASS
Healthcare API: PASS
Docker Service: PASS
Environment Configuration: PASS

SUCCESS: All critical components are working!
```

### If Services Are Down:
```
Database: FAIL - No connection could be made because the target machine actively refused it
```
**Solution**: Start PostgreSQL with `docker-compose up -d`

## Next Steps

1. Run `.\quick_test.ps1` first
2. If all pass, your system is ready
3. If issues found, fix services and re-run
4. For production deployment, run all validation scripts

## Support

- Check Docker containers: `docker ps`
- Check application logs: `python app/main.py`
- Verify environment variables are loaded

