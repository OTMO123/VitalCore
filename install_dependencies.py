#!/usr/bin/env python3
"""
Install missing dependencies for VitalCore
"""
import subprocess
import sys
import os

def install_package(package):
    """Install a Python package using pip"""
    try:
        print(f"📦 Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package}: {e}")
        return False

def install_requirements():
    """Install requirements from file if it exists"""
    requirements_file = "requirements.txt"
    if os.path.exists(requirements_file):
        try:
            print(f"📋 Installing from {requirements_file}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_file])
            print(f"✅ Requirements installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install requirements: {e}")
            return False
    else:
        print(f"⚠️  {requirements_file} not found, installing individual packages...")
        return False

def main():
    print("🚀 VitalCore Dependency Installer")
    print("=" * 50)
    
    # Required packages
    required_packages = [
        "marshmallow",
        "pydantic-settings", 
        "pydantic",
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "alembic",
        "psycopg2-binary",
        "redis",
        "celery",
        "python-jose[cryptography]",
        "passlib[bcrypt]",
        "python-multipart",
        "structlog",
        "cryptography",
        "minio",
        "pytest",
        "pytest-asyncio"
    ]
    
    # Try installing from requirements.txt first
    if not install_requirements():
        # Install individual packages
        failed_packages = []
        for package in required_packages:
            if not install_package(package):
                failed_packages.append(package)
        
        if failed_packages:
            print(f"\n❌ Failed to install: {', '.join(failed_packages)}")
            print("💡 You may need to install these manually")
            return False
    
    print("\n✅ All dependencies installed successfully!")
    print("🎉 You can now run: python run.py")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)