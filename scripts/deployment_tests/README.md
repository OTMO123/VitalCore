# Deployment Testing Scripts

This directory contains comprehensive PowerShell scripts for validating production deployment readiness of the Healthcare Records Backend system.

## Overview

These 8 testing scripts provide complete validation coverage based on the Production Deployment Checklist, ensuring HIPAA/SOC2 compliance and production readiness.

## Test Scripts

### 1. Infrastructure Validation (`1_infrastructure_validation.ps1`)
**Critical Test** - Validates core infrastructure components
- Database connectivity (PostgreSQL)
- Redis cache service
- MinIO object storage
- Docker environment
- Network connectivity
- SSL/TLS certificates
- DNS resolution
- Port accessibility

### 2. Application Configuration (`2_application_configuration.ps1`)
**Critical Test** - Validates application configuration
- Environment variables
- Database connection strings
- Security settings (JWT, encryption keys)
- HIPAA compliance configuration
- Redis configuration
- File system permissions
- Production environment settings

### 3. Security & Compliance (`3_security_compliance.ps1`)
**Critical Test** - Validates security and regulatory compliance
- PHI encryption validation
- HIPAA compliance controls (35+ checks)
- SOC2 Type II controls (15+ criteria)
- JWT authentication security
- Network security settings
- Audit logging configuration
- Access control validation

### 4. Database Migration (`4_database_migration.ps1`)
**Critical Test** - Validates database deployment readiness
- Database connectivity
- Alembic migration configuration
- Migration status verification
- Backup and restore capability
- Rollback procedure testing
- Data integrity validation
- Database performance checks

### 5. Application Deployment (`5_application_deployment.ps1`)
**Critical Test** - Validates application deployment
- Docker environment validation
- Container build verification
- Service deployment testing
- Health endpoint validation
- API functionality testing
- Resource configuration
- Load balancer configuration

### 6. Performance Validation (`6_performance_validation.ps1`)
**Optional Test** - Validates performance requirements
- API response time testing (10 requests per endpoint)
- Concurrent load testing (up to 1000 users)
- Sustained load testing (15 minutes)
- Database performance validation
- Memory usage monitoring
- Resource utilization tracking
- Performance threshold validation

### 7. Monitoring & Alerting (`7_monitoring_alerting.ps1`)
**Optional Test** - Validates monitoring infrastructure
- Prometheus service validation
- Grafana dashboard accessibility
- Alertmanager configuration
- Application metrics endpoint
- Health monitoring endpoints
- Logging services (Loki)
- Log directory validation

### 8. Master Deployment Runner (`8_master_deployment_runner.ps1`)
**Orchestration Script** - Runs all tests and provides comprehensive reporting
- Executes all 7 validation scripts in sequence
- Provides real-time progress tracking
- Generates comprehensive summary reports
- Categorizes issues by severity and type
- Determines overall production readiness
- Creates detailed JSON and text reports

## Usage

### Run Individual Tests
```powershell
# Run specific test
.\scripts\deployment_tests\1_infrastructure_validation.ps1

# Run with execution policy bypass
powershell -ExecutionPolicy Bypass -File .\scripts\deployment_tests\1_infrastructure_validation.ps1
```

### Run Complete Validation Suite
```powershell
# Run all tests with master runner (recommended)
.\scripts\deployment_tests\8_master_deployment_runner.ps1

# This will execute all tests and provide comprehensive reporting
```

### PowerShell Execution Policy
If you encounter execution policy restrictions:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Test Results

Each script generates:
- **Console Output**: Real-time test progress and results
- **JSON Report**: Detailed structured results for automation
- **Exit Codes**: 
  - `0` = All tests passed
  - `1` = Critical failures (production deployment not recommended)
  - `2` = Non-critical failures (warnings only)

### Master Runner Output
The master runner creates comprehensive reports:
- `deployment_validation_master_YYYYMMDD_HHMMSS.json` - Detailed JSON report
- `deployment_validation_summary_YYYYMMDD_HHMMSS.txt` - Human-readable summary

## Test Categories

### Critical Tests (Must Pass for Production)
Tests 1-5 are critical and must pass for production deployment:
- Infrastructure components must be accessible
- Configuration must be complete and valid
- Security and compliance requirements must be met
- Database migrations must be ready
- Application deployment must be functional

### Optional Tests (Recommended)
Tests 6-7 are recommended but not blocking:
- Performance validation ensures optimal user experience
- Monitoring validation ensures operational visibility

## Issue Categorization

Issues are automatically categorized by type:
- **HIPAA Compliance**: PHI handling, audit logging, retention
- **SOC2 Compliance**: Security controls, access management
- **Database**: Connection, migration, backup issues
- **Security**: Authentication, encryption, network security
- **Deployment**: Docker, container, service issues
- **Performance**: Response times, load handling, resource usage
- **Monitoring**: Metrics, alerting, dashboard issues

## Compliance Validation

### HIPAA Requirements Validated
- PHI encryption at rest and in transit
- Audit logging (7-year retention)
- Access controls and authentication
- Consent validation
- Minimum necessary rule enforcement
- Security incident detection

### SOC2 Type II Controls Validated
- CC1: Control Environment (RBAC, access review)
- CC2: Communication & Information (audit logging, incident reporting)
- CC3: Risk Assessment (vulnerability scanning, threat monitoring)
- CC4: Monitoring Activities (continuous monitoring, alerting)
- CC5: Control Activities (access controls, change management)

## Prerequisites

### Required Services
Before running tests, ensure these services are running:
```bash
# Start infrastructure services
docker-compose up -d

# Start application
python app/main.py
```

### Required Environment Variables
Key environment variables that tests validate:
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/healthcare_db
DB_HOST=localhost
DB_PORT=5432

# Security
JWT_SECRET_KEY=your-jwt-secret-key-32-chars-min
PHI_ENCRYPTION_KEY=your-phi-encryption-key-32-chars-min
SECRET_KEY=your-app-secret-key

# HIPAA Compliance
HIPAA_ENABLED=true
AUDIT_LOG_ENABLED=true
PHI_AUDIT_ENABLED=true
AUDIT_LOG_RETENTION_DAYS=2555  # 7 years

# Application
ENVIRONMENT=production
DEBUG=false
```

## Troubleshooting

### Common Issues

1. **PowerShell Execution Policy**
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

2. **Service Not Running**
   - Check Docker containers: `docker ps`
   - Start missing services: `docker-compose up -d`
   - Verify application is running: `curl http://localhost:8000/health`

3. **Environment Variables Missing**
   - Check `.env` file exists and has required variables
   - Source environment: `. .env` (Linux/Mac) or load in PowerShell

4. **Network Connectivity Issues**
   - Verify firewall settings
   - Check port availability: `netstat -an | findstr :5432`
   - Test connectivity: `telnet localhost 5432`

### Log Files
Test execution creates log files:
- Individual test results: `test_name_YYYYMMDD_HHMMSS.json`
- Master runner reports: `deployment_validation_*`
- Application logs: `logs/` directory

## Integration with CI/CD

These scripts can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions step
- name: Run Deployment Validation
  run: |
    powershell -ExecutionPolicy Bypass -File scripts/deployment_tests/8_master_deployment_runner.ps1
  shell: pwsh
```

The master runner provides appropriate exit codes for pipeline decision making.

## Production Deployment Decision Matrix

| Critical Tests Status | Optional Tests Status | Deployment Recommendation |
|----------------------|----------------------|---------------------------|
| ✅ All Pass          | ✅ All Pass          | **PRODUCTION READY** - Deploy immediately |
| ✅ All Pass          | ⚠️ Some Warnings     | **PRODUCTION READY WITH WARNINGS** - Deploy with monitoring |
| ✅ All Pass          | ❌ Some Failures     | **PRODUCTION READY WITH WARNINGS** - Deploy with reduced features |
| ❌ Any Failures      | Any Status           | **NOT PRODUCTION READY** - Fix critical issues first |

## Security Considerations

These scripts are designed for secure testing:
- Sensitive values are masked in output
- No credentials are logged
- Temporary files are cleaned up
- Network tests use minimal data exposure
- Results files can contain sensitive information - handle appropriately

## Support

For questions or issues with these testing scripts:
1. Review the PRODUCTION_DEPLOYMENT_CHECKLIST.md
2. Check the operational runbooks in `docs/operations/`
3. Review application logs for detailed error information
4. Ensure all prerequisites are met before running tests

The comprehensive validation provided by these scripts ensures confidence in production deployment while maintaining healthcare compliance requirements.