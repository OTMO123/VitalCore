#!/usr/bin/env python3
"""
Install Test Dependencies for Clinical Workflows

Script to install all required testing dependencies.
"""

import subprocess
import sys
import os

def install_dependencies():
    """Install all required test dependencies."""
    
    print("Installing Clinical Workflows Test Dependencies...")
    print("="*60)
    
    # Core testing dependencies
    dependencies = [
        "pytest>=7.4.3",
        "pytest-asyncio>=0.21.1", 
        "pytest-cov>=4.1.0",
        "pytest-mock>=3.12.0",
        "pytest-timeout>=2.2.0",
        "pytest-xdist>=3.5.0",
        "pytest-benchmark>=4.0.0",
        "pytest-html>=4.1.1",
        "pytest-sugar>=0.9.7",
        "pytest-clarity>=1.0.1",
        "httpx>=0.25.2",
        "faker>=20.1.0",
        "factory-boy>=3.3.0",
        "coverage>=7.3.2",
        "psutil>=5.9.0"
    ]
    
    for dep in dependencies:
        print(f"Installing {dep}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"✓ {dep} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install {dep}: {e}")
            return False
    
    print("\n" + "="*60)
    print("All test dependencies installed successfully!")
    print("="*60)
    
    # Verify installation
    print("\nVerifying installation...")
    try:
        import pytest
        print(f"✓ pytest version: {pytest.__version__}")
        
        import coverage
        print(f"✓ coverage version: {coverage.__version__}")
        
        import httpx
        print(f"✓ httpx version: {httpx.__version__}")
        
        print("\n✅ All dependencies verified!")
        return True
        
    except ImportError as e:
        print(f"✗ Verification failed: {e}")
        return False

if __name__ == "__main__":
    success = install_dependencies()
    if not success:
        sys.exit(1)
    
    print("\n🎉 Ready to run tests!")
    print("\nNext steps:")
    print("1. Run: python app/modules/clinical_workflows/tests/run_tests_simple.py")
    print("2. Or: pytest app/modules/clinical_workflows/tests/ -v")