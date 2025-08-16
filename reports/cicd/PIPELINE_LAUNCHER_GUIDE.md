# 🚀 Pipeline Launcher (PL) - Quick Reference Guide

## Overview

The Pipeline Launcher (`pl.ps1`) provides a simple, reliable interface for running CI/CD pipeline operations on the IRIS Healthcare API system.

---

## 📋 Quick Start

### Basic Usage
```powershell
# Show help
.\pl.ps1 help

# Check system status  
.\pl.ps1 status

# Run complete pipeline
.\pl.ps1 test

# Run infrastructure tests only
.\pl.ps1 infra

# Run smoke tests only
.\pl.ps1 smoke
```

### Batch File Alternative
```cmd
REM For environments where PowerShell execution policy is restricted
pl.bat help
pl.bat test
pl.bat infra
```

---

## 🎯 Available Commands

| Command | Description | Use Case |
|---------|-------------|----------|
| **help** | Show command reference | Getting started, command discovery |
| **status** | Check system health | Quick health verification |
| **test** | Run complete pipeline | Full validation before commits |
| **infra** | Infrastructure tests only | Database/connectivity validation |
| **smoke** | Smoke tests only | Basic functionality verification |

---

## 📊 Command Details

### `status` - System Health Check
```powershell
.\pl.ps1 status
```
**Output:**
- API server health status
- Database connectivity check
- Service availability verification

**Exit Codes:**
- `0` - All systems healthy
- `1` - Some services unavailable (non-critical)

### `test` - Complete Pipeline
```powershell
.\pl.ps1 test
```
**What it runs:**
1. Prerequisites check (Python, pytest)
2. Infrastructure validation tests
3. Smoke tests for basic functionality
4. Results summary with pass/fail status

**Exit Codes:**
- `0` - All tests passed
- `1` - Some tests failed or issues detected

### `infra` - Infrastructure Validation
```powershell
.\pl.ps1 infra  
```
**What it checks:**
- Database connectivity and schema consistency
- Port availability and service health
- Security dependencies and configurations
- Directory structure and file permissions

**Typical Output:**
```
✓ Database Connectivity: PASSED
✓ Server Health Endpoint: PASSED  
✓ Port Availability: PASSED
✓ Schema Consistency: PASSED (INET type fix verified)
⚠ Environment Variables: FAILED (non-critical)
```

### `smoke` - Basic Functionality Tests
```powershell
.\pl.ps1 smoke
```
**What it verifies:**
- Health endpoint accessibility
- API documentation availability
- Basic authentication flows (when server running)
- Security headers presence

**Typical Output:**
```
✓ Health Endpoint: PASSED
✓ API Documentation: PASSED
✓ Security Headers: PASSED  
⏭ User Registration: SKIPPED (server not running)
```

---

## 🔧 Prerequisites

### Required Components
1. **Python Virtual Environment**
   ```powershell
   # Location: venv\Scripts\python.exe
   # Auto-checked by pipeline launcher
   ```

2. **Pytest Framework**
   ```powershell
   # Auto-verified with: python -m pytest --version
   # Install if missing: pip install pytest pytest-asyncio
   ```

3. **Database Access** (for full tests)
   ```powershell
   # PostgreSQL on localhost:5432
   # Optional - tests will skip if unavailable
   ```

### Environment Setup
```powershell
# Ensure you're in the project root
cd C:\Users\aurik\Code_Projects\2_scraper

# Virtual environment should exist
# If not, create with: python -m venv venv

# Install dependencies
.\venv\Scripts\pip.exe install pytest pytest-asyncio pytest-cov httpx
```

---

## 📈 Integration with Development Workflow

### Daily Development
```powershell
# Morning health check
.\pl.ps1 status

# Before committing changes
.\pl.ps1 test

# Quick infrastructure validation
.\pl.ps1 infra
```

### CI/CD Integration
```yaml
# GitHub Actions integration
- name: Run Pipeline Tests
  run: |
    powershell -ExecutionPolicy Bypass -File pl.ps1 test
```

### Troubleshooting Workflow
```powershell
# 1. Check system health
.\pl.ps1 status

# 2. If issues, run infrastructure tests for details
.\pl.ps1 infra

# 3. Check basic functionality
.\pl.ps1 smoke

# 4. Review test output for specific failures
```

---

## 🛠️ Advanced Usage

### Custom Test Execution
```powershell
# For more detailed control, use pytest directly:
$env:PYTHONPATH = "."
.\venv\Scripts\python.exe -m pytest app\tests\infrastructure\ -v
.\venv\Scripts\python.exe -m pytest app\tests\smoke\ -v --tb=short
```

### Makefile Integration
```bash
# Alternative using Makefile (if available)
make test-infrastructure
make test-smoke  
make ci-test
```

### Server Management
```powershell
# Start development server (if needed for full tests)
python start_server.py

# Then run tests
.\pl.ps1 test
```

---

## 📊 Understanding Test Results

### Success Indicators
```
✓ PASSED - Test completed successfully
✓ OK - Component is healthy
✓ ACCESSIBLE - Service is reachable
```

### Warning Indicators  
```
⚠ ISSUES - Non-critical problems detected
⚠ UNAVAILABLE - Service not running (may be expected)
⏭ SKIPPED - Test skipped due to missing dependencies
```

### Error Indicators
```
✗ FAILED - Critical test failure requiring attention
✗ ERROR - Unexpected error occurred
✗ MISSING - Required component not found
```

### Pass Rate Interpretation
- **90-100%**: Excellent - system ready for production
- **75-89%**: Good - minor issues, safe to proceed
- **60-74%**: Acceptable - investigate failures
- **<60%**: Needs attention - fix issues before proceeding

---

## 🔍 Troubleshooting Common Issues

### "Python environment: MISSING"
```powershell
# Solution: Create virtual environment
python -m venv venv
.\venv\Scripts\pip.exe install -r requirements.txt
```

### "Pytest framework: ERROR" 
```powershell
# Solution: Install pytest
.\venv\Scripts\pip.exe install pytest pytest-asyncio pytest-cov
```

### "API Server: UNAVAILABLE"
```powershell
# Solution: Start the server
python start_server.py
# Or check if running on different port
```

### "Database connectivity issues"
```powershell
# Check PostgreSQL is running
# Check port 5432 accessibility
# Verify connection string in configuration
```

### PowerShell Execution Policy Issues
```powershell
# Temporary bypass
powershell -ExecutionPolicy Bypass -File pl.ps1 help

# Or use batch file
pl.bat help
```

---

## 📚 Related Documentation

- **[CI/CD Implementation Report](./CONSERVATIVE_CICD_IMPLEMENTATION_REPORT.md)** - Detailed implementation status
- **[Status Dashboard](./CICD_STATUS_DASHBOARD.md)** - Real-time system metrics  
- **[GitHub Actions Workflow](../../.github/workflows/conservative-ci.yml)** - Automated pipeline
- **[Test Configuration](../../pytest.ini)** - Pytest settings and markers

---

## 🎯 Next Steps

### Phase 1 (Current) - Basic Pipeline
- ✅ Infrastructure validation
- ✅ Smoke testing
- ✅ Simple command interface

### Phase 2 (Next 30 days) - Enhanced Pipeline  
- 🔄 AI-powered debugging integration
- 🔄 Expanded test coverage
- 🔄 Performance monitoring
- 🔄 Advanced security scanning

### Phase 3 (Next 90 days) - AI-Native Pipeline
- 📅 Predictive failure detection
- 📅 Autonomous issue resolution
- 📅 Zero-downtime deployments
- 📅 Enterprise monitoring dashboard

---

**Quick Reference Card:**
```
DAILY COMMANDS:
.\pl.ps1 status    # Check health
.\pl.ps1 test      # Full pipeline  
.\pl.ps1 infra     # Infrastructure only

EMERGENCY COMMANDS:
.\pl.ps1 help      # Show commands
pl.bat test        # Bypass execution policy
```

*The Pipeline Launcher provides reliable, consistent access to CI/CD operations with minimal dependencies and maximum compatibility.*