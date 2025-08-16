#!/usr/bin/env python3
"""
Quick fixes for major test collection issues
"""
import os
import shutil
import sys

def clean_cache_files():
    """Remove __pycache__ directories and .pyc files."""
    print("🧹 Cleaning cache files...")
    
    cache_dirs = []
    pyc_files = []
    
    # Find all __pycache__ directories and .pyc files
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            cache_dirs.append(os.path.join(root, '__pycache__'))
        
        for file in files:
            if file.endswith('.pyc') or file.endswith('.pyo'):
                pyc_files.append(os.path.join(root, file))
    
    # Remove cache directories
    for cache_dir in cache_dirs:
        try:
            shutil.rmtree(cache_dir)
            print(f"   ✅ Removed: {cache_dir}")
        except Exception as e:
            print(f"   ⚠️ Failed to remove {cache_dir}: {e}")
    
    # Remove .pyc files
    for pyc_file in pyc_files:
        try:
            os.remove(pyc_file)
            print(f"   ✅ Removed: {pyc_file}")
        except Exception as e:
            print(f"   ⚠️ Failed to remove {pyc_file}: {e}")
    
    print(f"   🎯 Cache cleanup complete: {len(cache_dirs)} dirs, {len(pyc_files)} files")

def fix_missing_imports():
    """Fix common missing import issues."""
    print("\n🔧 Fixing missing imports...")
    
    fixes = [
        {
            'file': 'scripts/performance/production_load_test.py',
            'old': 'class ProductionLoadTester:',
            'new': 'from typing import Any, Dict\n\nclass ProductionLoadTester:'
        },
        {
            'file': 'app/tests/test_containers_config.py',
            'old': 'async def start_postgres(self, postgres_version: str = "15") -> PostgresContainer:',
            'new': 'async def start_postgres(self, postgres_version: str = "15") -> Any:  # PostgresContainer:'
        }
    ]
    
    for fix in fixes:
        file_path = fix['file']
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if fix['old'] in content:
                    content = content.replace(fix['old'], fix['new'])
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"   ✅ Fixed imports in: {file_path}")
                else:
                    print(f"   ℹ️ No changes needed in: {file_path}")
            except Exception as e:
                print(f"   ❌ Failed to fix {file_path}: {e}")
        else:
            print(f"   ⚠️ File not found: {file_path}")

def create_pytest_ini():
    """Create pytest.ini with proper marks configuration."""
    print("\n📝 Creating pytest.ini...")
    
    pytest_ini_content = """[tool:pytest]
# Pytest configuration for enterprise healthcare system

# Test discovery
testpaths = app/tests tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*

# Markers to avoid warnings
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (require database)
    security: Security-focused tests
    performance: Performance and load tests
    smoke: Basic functionality verification
    e2e: End-to-end workflow tests
    
    # Healthcare roles
    admin: Admin role tests
    physician: Physician role tests
    nurse: Nurse role tests
    patient: Patient role tests
    clinical_technician: Clinical technician tests
    billing_staff: Billing staff tests
    
    # Compliance
    compliance: Compliance-related tests
    hipaa: HIPAA compliance tests
    fhir: FHIR R4 standard tests
    soc2: SOC2 compliance tests
    audit: Audit logging tests
    
    # Infrastructure
    infrastructure: Infrastructure tests
    database: Database tests
    api: API endpoint tests
    auth: Authentication tests
    
    # Special categories
    slow: Slow-running tests
    chaos: Chaos engineering tests
    regression: Regression tests
    mock: Tests using mocks
    
    # Healthcare specific
    healthcare: Healthcare domain tests
    clinical_ai: Clinical AI tests
    ml_prediction: ML prediction tests
    predictive_platform: Predictive platform tests
    
    # Test execution
    order: Test execution order
    requires_containers: Requires Docker containers
    
    # Data categories
    phi: PHI-related tests
    immutable: Immutable logging tests
    
    # External integrations
    iris_api: IRIS API integration tests
    
    # Quality gates
    critical: Critical functionality tests
    dependencies: Dependency tests
    phase5: Phase 5 tests

# Logging
log_cli = false
log_cli_level = INFO
log_cli_format = %(asctime)s [%(levelname)8s] %(name)s: %(message)s
log_cli_date_format = %Y-%m-%d %H:%M:%S

# Warnings
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
    ignore::UserWarning:pkg_resources
    ignore::pytest.PytestRemovedIn9Warning
    ignore::sqlalchemy.exc.SAWarning

# Coverage (if pytest-cov is installed)
addopts = 
    --strict-markers
    --tb=short
    -ra
    --maxfail=10
"""
    
    try:
        with open('pytest.ini', 'w', encoding='utf-8') as f:
            f.write(pytest_ini_content)
        print("   ✅ Created pytest.ini with proper markers")
    except Exception as e:
        print(f"   ❌ Failed to create pytest.ini: {e}")

def main():
    """Run all fixes."""
    print("🏥 ENTERPRISE TEST CLEANUP")
    print("=" * 50)
    
    clean_cache_files()
    fix_missing_imports()
    create_pytest_ini()
    
    print("\n" + "=" * 50)
    print("✅ Test cleanup completed!")
    print("📊 Summary:")
    print("   - Cache files cleaned")
    print("   - Import issues fixed")  
    print("   - pytest.ini created with proper markers")
    print("\n💡 Now run: pytest app/tests/smoke/ -v")
    print("   This will test basic functionality with clean environment")

if __name__ == "__main__":
    main()