# IRIS API Diagnostic Scripts

These PowerShell scripts provide comprehensive diagnostic capabilities for the IRIS API system, designed to support systematic 5 Whys root cause analysis.

## 📋 Scripts Overview

### 1. `Check-SystemHealth.ps1`
**Purpose**: Comprehensive system health check and diagnostics
**When to use**: First step in troubleshooting, before starting services

```powershell
# Basic health check
.\diagnostic_scripts\Check-SystemHealth.ps1

# Verbose output for detailed analysis
.\diagnostic_scripts\Check-SystemHealth.ps1 -Verbose

# Check specific URL
.\diagnostic_scripts\Check-SystemHealth.ps1 -BaseUrl "http://localhost:8000"
```

**What it checks**:
- ✅ Docker daemon status and accessibility
- ✅ Container status (PostgreSQL, Redis, MinIO, Application)
- ✅ Python environment and application imports
- ✅ Configuration files and environment variables
- ✅ Network connectivity and port accessibility

### 2. `Start-Services.ps1`
**Purpose**: Start all required services in correct order
**When to use**: After health check, to ensure all services are running

```powershell
# Normal startup
.\diagnostic_scripts\Start-Services.ps1

# Clean restart (stops existing services first)
.\diagnostic_scripts\Start-Services.ps1 -CleanStart

# Force mode (ignore some errors)
.\diagnostic_scripts\Start-Services.ps1 -Force

# Verbose output
.\diagnostic_scripts\Start-Services.ps1 -Verbose
```

**What it does**:
- 🐳 Starts Docker Compose services
- ⏰ Waits for services to be ready
- 🗄️ Tests database connectivity
- 🔄 Tests Redis connectivity
- 🚀 Attempts to start Python application
- 📊 Provides comprehensive status summary

### 3. `Test-ApiEndpoints.ps1`
**Purpose**: Detailed API endpoint testing with 5 Whys analysis
**When to use**: After services are running, to test API functionality

```powershell
# Standard API testing
.\diagnostic_scripts\Test-ApiEndpoints.ps1

# Verbose output with detailed error analysis
.\diagnostic_scripts\Test-ApiEndpoints.ps1 -Verbose

# Save diagnostic logs to file
.\diagnostic_scripts\Test-ApiEndpoints.ps1 -SaveLogs

# Test different base URL
.\diagnostic_scripts\Test-ApiEndpoints.ps1 -BaseUrl "http://localhost:8001"
```

**What it tests**:
- 🔐 Authentication flow
- 📄 Documents health endpoint (fixed)
- 👤 Patient creation, retrieval, and updates
- 📋 Audit logs functionality
- ⚠️ Error handling (404 vs 500 errors)
- 🏥 All module health endpoints

**5 Whys Analysis Features**:
- Detailed error logging with timestamps
- Root cause analysis for each failure
- Specific recommendations for fixes
- Comprehensive success rate reporting

## 🔍 5 Whys Integration

Each script is designed to support systematic root cause analysis:

### Why Level 1: What's failing?
Scripts identify specific failing components with detailed error messages.

### Why Level 2: Why is it failing?
Scripts provide context like HTTP status codes, error responses, and system state.

### Why Level 3: Why is that causing the failure?
Scripts check dependencies, imports, and configuration issues.

### Why Level 4: Why weren't these caught earlier?
Scripts validate testing coverage and system monitoring.

### Why Level 5: Why do these root causes exist?
Scripts provide architectural recommendations and preventive measures.

## 📊 Usage Workflow

### For New System Setup:
```powershell
# 1. Check if system is ready
.\diagnostic_scripts\Check-SystemHealth.ps1 -Verbose

# 2. Start all services
.\diagnostic_scripts\Start-Services.ps1 -CleanStart

# 3. Test API endpoints
.\diagnostic_scripts\Test-ApiEndpoints.ps1 -SaveLogs
```

### For Troubleshooting Existing Issues:
```powershell
# 1. Quick health check
.\diagnostic_scripts\Check-SystemHealth.ps1

# 2. Test specific endpoints with detailed analysis
.\diagnostic_scripts\Test-ApiEndpoints.ps1 -Verbose

# 3. If services need restart
.\diagnostic_scripts\Start-Services.ps1 -Force
```

### For Deployment Readiness:
```powershell
# Complete validation suite
.\diagnostic_scripts\Check-SystemHealth.ps1 -Verbose
.\diagnostic_scripts\Start-Services.ps1
.\diagnostic_scripts\Test-ApiEndpoints.ps1 -SaveLogs -Verbose
```

## 📈 Success Criteria

### System Health Check:
- **90-100%**: ✅ System ready
- **70-89%**: ⚠️ Minor issues, mostly working
- **<70%**: ❌ Major issues, needs attention

### API Endpoint Tests:
- **100%**: 🚀 Ready for deployment
- **80-99%**: ⚠️ Minor fixes needed
- **<80%**: ❌ Major fixes required

## 🔧 Common Issues and Solutions

### Docker Issues:
```powershell
# If Docker not accessible
# Solution: Start Docker Desktop, enable WSL2 integration

# If containers won't start
.\diagnostic_scripts\Start-Services.ps1 -CleanStart -Force
```

### Database Issues:
```powershell
# If database connection fails
docker compose logs postgres
docker exec -it iris_postgres psql -U postgres -c "\l"
```

### Application Issues:
```powershell
# If Python app won't start
python -c "from app.main import create_app; print('OK')"
pip install -r requirements.txt
```

### API Issues:
```powershell
# If endpoints return 500 errors
.\diagnostic_scripts\Test-ApiEndpoints.ps1 -Verbose
# Check the detailed 5 Whys analysis in output
```

## 📁 Output Files

Scripts generate diagnostic files in `diagnostic_scripts/`:
- `system_health_YYYYMMDD_HHMMSS.log`
- `api_test_report_YYYYMMDD_HHMMSS.json`

These files can be shared for remote debugging and analysis.

## 🎯 Integration with 5 Whys Framework

The scripts are specifically designed to support Claude's 5 Whys analysis:

1. **Automated Why Level 1-3**: Scripts automatically identify and log the first 3 levels of why analysis
2. **Detailed Error Context**: Provides all necessary information for deeper analysis
3. **Systematic Testing**: Ensures all components are tested in logical order
4. **Actionable Recommendations**: Each failure includes specific next steps

Use these scripts to gather comprehensive diagnostic information, then share the output for systematic 5 Whys root cause analysis and resolution.

## 🚀 Quick Start

```powershell
# One-command system validation
.\diagnostic_scripts\Check-SystemHealth.ps1 -Verbose; .\diagnostic_scripts\Start-Services.ps1; .\diagnostic_scripts\Test-ApiEndpoints.ps1 -SaveLogs
```

This will provide complete system diagnostics for 100% deployment readiness verification.