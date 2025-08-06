#!/usr/bin/env python3
"""
System Health Diagnostic Script
Checks Docker, database, and service health to identify root causes
"""

import subprocess
import json
import sys
import os
import time
from datetime import datetime
from pathlib import Path

def run_command(cmd, description="", timeout=30):
    """Run command and return result with error handling"""
    print(f"🔍 {description}")
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=timeout
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Command timed out after {timeout}s",
            "returncode": -1
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1
        }

def check_docker_status():
    """Check Docker and container status"""
    print("\n📦 DOCKER STATUS CHECK")
    print("=" * 50)
    
    # Check if Docker is running
    docker_check = run_command("docker version", "Checking Docker daemon")
    if not docker_check["success"]:
        print("❌ Docker not accessible")
        print(f"Error: {docker_check['stderr']}")
        return False
    
    print("✅ Docker daemon running")
    
    # Check containers
    containers_check = run_command("docker ps -a", "Checking all containers")
    if containers_check["success"]:
        print("📋 Container Status:")
        print(containers_check["stdout"])
    
    # Check specific IRIS containers
    iris_check = run_command("docker ps | grep iris", "Checking IRIS containers")
    if iris_check["success"] and iris_check["stdout"]:
        print("✅ IRIS containers found:")
        print(iris_check["stdout"])
        return True
    else:
        print("❌ No IRIS containers running")
        return False

def check_database_connectivity():
    """Check database connection"""
    print("\n🗄️ DATABASE CONNECTIVITY CHECK")
    print("=" * 50)
    
    # Check if PostgreSQL container is running
    pg_check = run_command("docker ps | grep postgres", "Checking PostgreSQL container")
    if not pg_check["success"] or not pg_check["stdout"]:
        print("❌ PostgreSQL container not running")
        return False
    
    print("✅ PostgreSQL container running")
    
    # Try to connect to database
    db_connect = run_command(
        "docker exec -it $(docker ps -q --filter name=postgres) pg_isready -U postgres",
        "Testing database connection"
    )
    
    if db_connect["success"]:
        print("✅ Database accepting connections")
        return True
    else:
        print("❌ Database connection failed")
        print(f"Error: {db_connect['stderr']}")
        return False

def check_application_startup():
    """Check if application can start"""
    print("\n🚀 APPLICATION STARTUP CHECK")
    print("=" * 50)
    
    # Check if main.py can be imported
    import_check = run_command(
        "python3 -c 'from app.main import create_app; print(\"App import successful\")'",
        "Testing application import"
    )
    
    if import_check["success"]:
        print("✅ Application imports successfully")
    else:
        print("❌ Application import failed")
        print(f"Error: {import_check['stderr']}")
        return False
    
    # Check database models import
    models_check = run_command(
        "python3 -c 'from app.core.database_unified import Patient, User; print(\"Models import successful\")'",
        "Testing database models import"
    )
    
    if models_check["success"]:
        print("✅ Database models import successfully")
    else:
        print("❌ Database models import failed")
        print(f"Error: {models_check['stderr']}")
        return False
    
    return True

def check_configuration():
    """Check configuration files and environment"""
    print("\n⚙️ CONFIGURATION CHECK")
    print("=" * 50)
    
    # Check if required files exist
    required_files = [
        "app/main.py",
        "app/core/database_unified.py",
        "app/modules/healthcare_records/router.py",
        "docker-compose.yml",
        "requirements.txt"
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING")
    
    # Check environment variables
    env_vars = [
        "DATABASE_URL",
        "REDIS_URL", 
        "SECRET_KEY"
    ]
    
    print("\n🔐 Environment Variables:")
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var} - Set")
        else:
            print(f"❌ {var} - Not set")

def generate_diagnostic_report():
    """Generate comprehensive diagnostic report"""
    print("\n📊 DIAGNOSTIC REPORT")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"System: {os.name}")
    print(f"Python: {sys.version}")
    print(f"Working Directory: {os.getcwd()}")
    
    # Run all checks
    docker_ok = check_docker_status()
    db_ok = check_database_connectivity() if docker_ok else False
    app_ok = check_application_startup()
    check_configuration()
    
    print("\n🎯 SUMMARY")
    print("=" * 50)
    print(f"Docker Status: {'✅ OK' if docker_ok else '❌ FAIL'}")
    print(f"Database Status: {'✅ OK' if db_ok else '❌ FAIL'}")
    print(f"Application Status: {'✅ OK' if app_ok else '❌ FAIL'}")
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS")
    print("=" * 50)
    
    if not docker_ok:
        print("1. Start Docker Desktop or Docker daemon")
        print("2. Run: docker-compose up -d")
    
    if not db_ok and docker_ok:
        print("1. Check PostgreSQL container logs: docker logs iris_postgres")
        print("2. Verify database configuration in docker-compose.yml")
    
    if not app_ok:
        print("1. Check Python dependencies: pip install -r requirements.txt")
        print("2. Check for import errors in application code")
    
    overall_status = docker_ok and db_ok and app_ok
    print(f"\n🏁 OVERALL STATUS: {'✅ READY' if overall_status else '❌ NEEDS ATTENTION'}")
    
    return overall_status

if __name__ == "__main__":
    print("🔍 IRIS API SYSTEM HEALTH DIAGNOSTIC")
    print("=" * 80)
    generate_diagnostic_report()