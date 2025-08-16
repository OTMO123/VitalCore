#!/usr/bin/env python3
"""
Docker Test Setup Script
Prepares the clinical workflows test environment for Docker execution.
"""

import os
import sys
from pathlib import Path
import subprocess

def setup_docker_tests():
    """Setup test environment for Docker execution."""
    
    print("Clinical Workflows - Docker Test Setup")
    print("=" * 50)
    
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print(f"Project root: {project_root}")
    
    # Check if we're in Docker environment
    in_docker = os.path.exists('/.dockerenv') or os.environ.get('DOCKER_CONTAINER', False)
    print(f"Docker environment: {in_docker}")
    
    # Check required directories exist
    required_dirs = [
        "app/modules/clinical_workflows",
        "app/modules/clinical_workflows/tests",
        "app/modules/clinical_workflows/tests/unit",
        "app/modules/clinical_workflows/tests/integration",
        "app/modules/clinical_workflows/tests/security",
        "app/core"
    ]
    
    print("\nChecking directory structure:")
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        exists = full_path.exists()
        print(f"  {'✓' if exists else '✗'} {dir_path}: {'EXISTS' if exists else 'MISSING'}")
    
    # Check critical files exist
    required_files = [
        "app/modules/clinical_workflows/models.py",
        "app/modules/clinical_workflows/schemas.py", 
        "app/modules/clinical_workflows/service.py",
        "app/modules/clinical_workflows/router.py",
        "app/modules/clinical_workflows/security.py",
        "app/modules/clinical_workflows/tests/conftest.py",
        "app/core/database_unified.py"
    ]
    
    print("\nChecking critical files:")
    missing_files = []
    for file_path in required_files:
        full_path = project_root / file_path
        exists = full_path.exists()
        print(f"  {'✓' if exists else '✗'} {file_path}: {'EXISTS' if exists else 'MISSING'}")
        if not exists:
            missing_files.append(file_path)
    
    # Check Python environment
    print("\nChecking Python environment:")
    try:
        import_checks = [
            ("pytest", "pytest"),
            ("fastapi", "FastAPI"),
            ("sqlalchemy", "SQLAlchemy"), 
            ("httpx", "HTTPX client"),
            ("uuid", "UUID support"),
            ("datetime", "DateTime support")
        ]
        
        for module, description in import_checks:
            try:
                __import__(module)
                print(f"  ✓ {description}: AVAILABLE")
            except ImportError:
                print(f"  ✗ {description}: MISSING")
                
    except Exception as e:
        print(f"  ✗ Python environment check failed: {e}")
    
    # Docker integration readiness
    print("\nDocker Integration Readiness:")
    
    docker_ready_checks = [
        ("All required files exist", len(missing_files) == 0),
        ("Test directory structure", all((project_root / d).exists() for d in required_dirs)),
        ("Docker environment detected", in_docker or os.environ.get('FORCE_DOCKER_MODE', False))
    ]
    
    all_ready = True
    for check_name, passed in docker_ready_checks:
        status = "✓ READY" if passed else "✗ NOT READY"
        print(f"  {status}: {check_name}")
        if not passed:
            all_ready = False
    
    print(f"\n{'=' * 50}")
    if all_ready:
        print("🚀 READY FOR DOCKER INTEGRATION")
        print("\nNext steps:")
        print("1. Start Docker services: docker-compose up -d")
        print("2. Enter container: docker exec -it <container> bash")
        print("3. Install dependencies: pip install pytest pytest-asyncio")
        print("4. Run tests: python app/modules/clinical_workflows/tests/run_tests.py --category fast")
    else:
        print("❌ NOT READY - Missing components detected")
        print("\nMissing files:")
        for file_path in missing_files:
            print(f"  - {file_path}")
    
    print(f"\nSetup completed at: {os.getcwd()}")
    return 0 if all_ready else 1

if __name__ == "__main__":
    exit_code = setup_docker_tests()
    sys.exit(exit_code)