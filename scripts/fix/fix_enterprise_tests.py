#!/usr/bin/env python3
"""
Enterprise Healthcare Test Dependencies Fixer

Ensures all dependencies are installed and fixes common test issues
for SOC2 Type II, HIPAA, FHIR R4, GDPR compliance testing.
"""

import subprocess
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def install_dependency(package, description):
    """Install a required dependency."""
    try:
        logger.info(f"Installing {description}: {package}")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", package, "--quiet"
        ])
        logger.info(f"✅ {description} installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to install {description}: {e}")
        return False

def verify_import(module_name, description):
    """Verify a module can be imported."""
    try:
        __import__(module_name)
        logger.info(f"✅ {description} import verified")
        return True
    except ImportError as e:
        logger.error(f"❌ {description} import failed: {e}")
        return False

def main():
    """Fix enterprise test dependencies."""
    logger.info("🏥 Enterprise Healthcare Test Dependencies Fixer")
    logger.info("=" * 60)
    
    # Critical dependencies for enterprise compliance testing
    dependencies = [
        ("aiosqlite==0.19.0", "Async SQLite for enterprise database testing"),
        ("pytest-asyncio==0.21.1", "Async pytest support for healthcare workflows"), 
        ("fakeredis==2.20.1", "Redis mocking for enterprise caching tests"),
        ("pytest-mock==3.12.0", "Mocking framework for compliance testing"),
    ]
    
    success_count = 0
    
    for package, description in dependencies:
        if install_dependency(package, description):
            success_count += 1
    
    logger.info("=" * 60)
    logger.info(f"Dependency Installation: {success_count}/{len(dependencies)} successful")
    
    # Verify critical imports
    logger.info("\n🔍 Verifying Critical Imports...")
    import_tests = [
        ("aiosqlite", "Async SQLite Database Driver"),
        ("pytest_asyncio", "Async Test Framework"),
        ("sqlalchemy", "Enterprise Database ORM"),
        ("fastapi", "Healthcare API Framework"),
        ("pydantic", "Data Validation Framework"),
    ]
    
    import_success = 0
    for module, desc in import_tests:
        if verify_import(module, desc):
            import_success += 1
    
    logger.info("=" * 60)
    logger.info(f"Import Verification: {import_success}/{len(import_tests)} successful")
    
    if success_count == len(dependencies) and import_success == len(import_tests):
        logger.info("✅ Enterprise healthcare test environment ready!")
        logger.info("\n🚀 Run tests with: pytest app/tests/api/test_fhir_rest_api_complete.py -v")
        return 0
    else:
        logger.error("❌ Some dependencies failed - check logs above")
        return 1

if __name__ == "__main__":
    sys.exit(main())