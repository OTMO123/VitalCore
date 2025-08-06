#!/usr/bin/env python3
"""
Clinical Workflows Module Validation
Validates that all components are properly structured and ready for integration.
"""

import os
import sys
from pathlib import Path
import importlib.util
from datetime import datetime

def validate_file_structure():
    """Validate that all required files exist."""
    print("🔍 VALIDATING FILE STRUCTURE")
    print("=" * 50)
    
    required_files = [
        "app/modules/clinical_workflows/__init__.py",
        "app/modules/clinical_workflows/models.py", 
        "app/modules/clinical_workflows/schemas.py",
        "app/modules/clinical_workflows/service.py",
        "app/modules/clinical_workflows/router.py",
        "app/modules/clinical_workflows/security.py",
        "app/modules/clinical_workflows/domain_events.py",
        "app/modules/clinical_workflows/exceptions.py",
        "app/modules/clinical_workflows/tests/conftest.py",
        "app/modules/clinical_workflows/tests/unit/test_service_unit.py",
        "app/modules/clinical_workflows/tests/integration/test_api_integration.py",
        "app/modules/clinical_workflows/tests/security/test_phi_protection_security.py",
        "app/modules/clinical_workflows/tests/e2e/test_complete_workflow_e2e.py",
        "app/modules/clinical_workflows/tests/run_tests.py",
        "app/modules/clinical_workflows/tests/pytest.ini",
        "app/modules/clinical_workflows/docker_integration_guide.md"
    ]
    
    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} - MISSING")
            missing_files.append(file_path)
    
    return len(missing_files) == 0, missing_files

def validate_code_syntax():
    """Validate Python syntax in core files."""
    print("\n🔍 VALIDATING CODE SYNTAX")
    print("=" * 50)
    
    python_files = [
        "app/modules/clinical_workflows/models.py",
        "app/modules/clinical_workflows/schemas.py", 
        "app/modules/clinical_workflows/service.py",
        "app/modules/clinical_workflows/router.py",
        "app/modules/clinical_workflows/security.py",
        "app/modules/clinical_workflows/domain_events.py",
        "app/modules/clinical_workflows/exceptions.py"
    ]
    
    syntax_errors = []
    for file_path in python_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                compile(code, file_path, 'exec')
                print(f"✓ {file_path} - Valid syntax")
            except SyntaxError as e:
                print(f"✗ {file_path} - Syntax error: {e}")
                syntax_errors.append((file_path, str(e)))
            except Exception as e:
                print(f"⚠ {file_path} - Could not validate: {e}")
        else:
            print(f"✗ {file_path} - File not found")
            syntax_errors.append((file_path, "File not found"))
    
    return len(syntax_errors) == 0, syntax_errors

def validate_test_structure():
    """Validate test directory structure."""
    print("\n🔍 VALIDATING TEST STRUCTURE") 
    print("=" * 50)
    
    test_dirs = [
        "app/modules/clinical_workflows/tests",
        "app/modules/clinical_workflows/tests/unit",
        "app/modules/clinical_workflows/tests/integration", 
        "app/modules/clinical_workflows/tests/security",
        "app/modules/clinical_workflows/tests/performance",
        "app/modules/clinical_workflows/tests/e2e"
    ]
    
    missing_dirs = []
    for dir_path in test_dirs:
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            # Count test files in directory
            test_files = [f for f in os.listdir(dir_path) if f.startswith('test_') and f.endswith('.py')]
            print(f"✓ {dir_path} - {len(test_files)} test files")
        else:
            print(f"✗ {dir_path} - MISSING")
            missing_dirs.append(dir_path)
    
    return len(missing_dirs) == 0, missing_dirs

def validate_configuration():
    """Validate configuration files."""
    print("\n🔍 VALIDATING CONFIGURATION")
    print("=" * 50)
    
    config_files = [
        ("app/modules/clinical_workflows/tests/pytest.ini", "pytest configuration"),
        ("app/modules/clinical_workflows/tests/conftest.py", "pytest fixtures"),
        ("app/modules/clinical_workflows/docker_integration_guide.md", "Docker integration guide"),
        ("tools/database/clinical_workflows_migration.py", "Database migration script")
    ]
    
    config_issues = []
    for file_path, description in config_files:
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"✓ {description}: {file_path} ({file_size} bytes)")
        else:
            print(f"✗ {description}: {file_path} - MISSING")
            config_issues.append(file_path)
    
    return len(config_issues) == 0, config_issues

def check_integration_readiness():
    """Check if module is ready for main app integration."""
    print("\n🔍 INTEGRATION READINESS CHECK")
    print("=" * 50)
    
    checks = [
        ("Router definition", "app/modules/clinical_workflows/router.py"),
        ("Model definitions", "app/modules/clinical_workflows/models.py"), 
        ("Schema definitions", "app/modules/clinical_workflows/schemas.py"),
        ("Service layer", "app/modules/clinical_workflows/service.py"),
        ("Security layer", "app/modules/clinical_workflows/security.py"),
        ("Test suite", "app/modules/clinical_workflows/tests/run_tests.py"),
        ("Database migration", "tools/database/clinical_workflows_migration.py")
    ]
    
    ready_components = 0
    total_components = len(checks)
    
    for component, file_path in checks:
        if os.path.exists(file_path):
            print(f"✓ {component}: READY")
            ready_components += 1
        else:
            print(f"✗ {component}: NOT READY")
    
    readiness_percentage = (ready_components / total_components) * 100
    print(f"\nIntegration Readiness: {readiness_percentage:.1f}% ({ready_components}/{total_components})")
    
    return readiness_percentage >= 100

def generate_summary_report():
    """Generate comprehensive validation summary."""
    print("\n" + "=" * 60)
    print("CLINICAL WORKFLOWS MODULE VALIDATION SUMMARY")  
    print("=" * 60)
    print(f"Validation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run all validations
    file_structure_valid, missing_files = validate_file_structure()
    syntax_valid, syntax_errors = validate_code_syntax()
    test_structure_valid, missing_test_dirs = validate_test_structure()
    config_valid, config_issues = validate_configuration()
    integration_ready = check_integration_readiness()
    
    # Summary
    print(f"\n📊 VALIDATION RESULTS:")
    print(f"✓ File Structure: {'PASS' if file_structure_valid else 'FAIL'}")
    print(f"✓ Code Syntax: {'PASS' if syntax_valid else 'FAIL'}")
    print(f"✓ Test Structure: {'PASS' if test_structure_valid else 'FAIL'}")
    print(f"✓ Configuration: {'PASS' if config_valid else 'FAIL'}")
    print(f"✓ Integration Ready: {'PASS' if integration_ready else 'FAIL'}")
    
    overall_status = all([
        file_structure_valid, syntax_valid, test_structure_valid, 
        config_valid, integration_ready
    ])
    
    print(f"\n🎯 OVERALL STATUS: {'✅ READY FOR INTEGRATION' if overall_status else '⚠️ NEEDS ATTENTION'}")
    
    if not overall_status:
        print(f"\n❌ ISSUES TO RESOLVE:")
        if missing_files:
            print(f"Missing files: {', '.join(missing_files)}")
        if syntax_errors:
            print(f"Syntax errors: {len(syntax_errors)} files")
        if missing_test_dirs:
            print(f"Missing test directories: {', '.join(missing_test_dirs)}")
        if config_issues:
            print(f"Configuration issues: {', '.join(config_issues)}")
    
    if overall_status:
        print(f"\n🚀 NEXT STEPS:")
        print("1. Start Docker services: docker-compose up -d")
        print("2. Run database migration: python tools/database/clinical_workflows_migration.py")
        print("3. Add router to app/main.py:")
        print("   from app.modules.clinical_workflows.router import router as clinical_workflows_router")
        print("   app.include_router(clinical_workflows_router, prefix='/api/v1/clinical-workflows')")
        print("4. Test health endpoint: curl http://localhost:8000/api/v1/clinical-workflows/health")
        print("5. Run comprehensive tests in Docker environment")
    
    return overall_status

if __name__ == "__main__":
    print("Clinical Workflows Module Validation")
    print("🏥 Enterprise Healthcare Platform")
    print("📅 " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    # Change to project root
    project_root = Path(__file__).parent
    os.chdir(project_root)
    print(f"📁 Working directory: {project_root}")
    
    # Run validation
    success = generate_summary_report()
    
    sys.exit(0 if success else 1)