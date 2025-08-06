#!/usr/bin/env python3
"""
Simple Clinical Workflows Validation (Windows-compatible)
"""

import os
from pathlib import Path

def validate_clinical_workflows():
    """Validate clinical workflows module."""
    print("Clinical Workflows Module Validation")
    print("=" * 50)
    
    # Check required files
    required_files = [
        "app/modules/clinical_workflows/models.py",
        "app/modules/clinical_workflows/schemas.py", 
        "app/modules/clinical_workflows/service.py",
        "app/modules/clinical_workflows/router.py",
        "app/modules/clinical_workflows/security.py",
        "app/modules/clinical_workflows/tests/conftest.py",
        "app/modules/clinical_workflows/tests/run_tests.py",
        "tools/database/clinical_workflows_migration.py"
    ]
    
    print("\nFile Structure Check:")
    all_files_exist = True
    for file_path in required_files:
        exists = os.path.exists(file_path)
        status = "EXISTS" if exists else "MISSING"
        print(f"  {file_path}: {status}")
        if not exists:
            all_files_exist = False
    
    # Check test directories
    test_dirs = [
        "app/modules/clinical_workflows/tests/unit",
        "app/modules/clinical_workflows/tests/integration",
        "app/modules/clinical_workflows/tests/security",
        "app/modules/clinical_workflows/tests/e2e"
    ]
    
    print("\nTest Directory Check:")
    all_dirs_exist = True
    for dir_path in test_dirs:
        exists = os.path.exists(dir_path) and os.path.isdir(dir_path)
        status = "EXISTS" if exists else "MISSING"
        print(f"  {dir_path}: {status}")
        if not exists:
            all_dirs_exist = False
    
    # Summary
    print("\nValidation Summary:")
    print(f"  Core Files: {'PASS' if all_files_exist else 'FAIL'}")
    print(f"  Test Structure: {'PASS' if all_dirs_exist else 'FAIL'}")
    
    if all_files_exist and all_dirs_exist:
        print("\nSTATUS: READY FOR INTEGRATION")
        print("\nNext Steps:")
        print("1. Run database migration")
        print("2. Add router to main.py")
        print("3. Test health endpoint")
        return True
    else:
        print("\nSTATUS: MISSING COMPONENTS")
        return False

if __name__ == "__main__":
    validate_clinical_workflows()