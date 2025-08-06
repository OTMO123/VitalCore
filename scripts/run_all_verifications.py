#!/usr/bin/env python3
"""
Master Verification Script

Runs all security and compliance verification scripts in the correct order.

Usage: python scripts/run_all_verifications.py
"""

import asyncio
import subprocess
import sys
import os
from datetime import datetime

def run_script(script_path, description):
    """Run a verification script and return the result."""
    print(f"\n🚀 Running {description}...")
    print("=" * 60)
    
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        # Print the output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        success = result.returncode == 0
        
        if success:
            print(f"✅ {description} completed successfully")
        else:
            print(f"❌ {description} failed with exit code {result.returncode}")
        
        return success
        
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"💥 {description} failed with exception: {e}")
        return False

async def check_prerequisites():
    """Check if system prerequisites are met."""
    print("🔍 CHECKING PREREQUISITES")
    print("=" * 50)
    
    checks = []
    
    # Check if Docker is running
    try:
        result = subprocess.run(["docker", "ps"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker is running")
            checks.append(True)
        else:
            print("❌ Docker is not running")
            checks.append(False)
    except FileNotFoundError:
        print("❌ Docker is not installed")
        checks.append(False)
    
    # Check if Python modules can be imported
    try:
        import asyncio
        import json
        import hashlib
        print("✅ Required Python modules available")
        checks.append(True)
    except ImportError as e:
        print(f"❌ Missing Python modules: {e}")
        checks.append(False)
    
    # Check if scripts directory exists
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.exists(scripts_dir):
        print("✅ Scripts directory found")
        checks.append(True)
    else:
        print("❌ Scripts directory not found")
        checks.append(False)
    
    return all(checks)

def main():
    """Run all verification scripts."""
    print("🔒 ENTERPRISE SECURITY VERIFICATION SUITE")
    print("=" * 60)
    print(f"Started at: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Check prerequisites
    if not asyncio.run(check_prerequisites()):
        print("\n❌ Prerequisites not met. Please fix issues above.")
        return False
    
    # Define verification scripts in order of execution
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    
    verification_scripts = [
        {
            "script": os.path.join(scripts_dir, "verify_security_logic.py"),
            "description": "Core Security Logic Verification",
            "critical": True
        },
        {
            "script": os.path.join(scripts_dir, "verify_security_features.py"),
            "description": "Security Features with Dependencies",
            "critical": False  # May fail due to dependencies
        },
        {
            "script": os.path.join(scripts_dir, "verify_database_security.py"),
            "description": "Database Security Verification",
            "critical": True
        },
        {
            "script": os.path.join(scripts_dir, "test_api_security.py"),
            "description": "API Security Testing",
            "critical": False  # May fail if API not running
        },
        {
            "script": os.path.join(scripts_dir, "test_enterprise_workflow.py"),
            "description": "Enterprise Workflow Testing",
            "critical": False  # May fail due to dependencies
        }
    ]
    
    results = {}
    critical_failures = 0
    
    # Run each verification script
    for script_info in verification_scripts:
        script_path = script_info["script"]
        description = script_info["description"]
        is_critical = script_info["critical"]
        
        if not os.path.exists(script_path):
            print(f"⚠️  Script not found: {script_path}")
            results[description] = False
            if is_critical:
                critical_failures += 1
            continue
        
        success = run_script(script_path, description)
        results[description] = success
        
        if not success and is_critical:
            critical_failures += 1
    
    # Generate summary report
    print("\n" + "=" * 60)
    print("📊 VERIFICATION SUITE SUMMARY")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for description, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {description}: {status}")
    
    print(f"\n🎯 Overall Results:")
    print(f"   Total Tests: {total_tests}")
    print(f"   Passed: {passed_tests}")
    print(f"   Failed: {total_tests - passed_tests}")
    print(f"   Critical Failures: {critical_failures}")
    
    # Final assessment
    if critical_failures == 0:
        print("\n🎉 ALL CRITICAL SECURITY VERIFICATIONS PASSED!")
        print("✅ System is ready for enterprise deployment")
        
        if passed_tests == total_tests:
            print("🏆 PERFECT SCORE - All verifications passed!")
        else:
            print("📝 Some non-critical tests failed (check API availability)")
        
        return True
    else:
        print(f"\n⚠️  {critical_failures} CRITICAL VERIFICATION(S) FAILED")
        print("❌ System needs fixes before enterprise deployment")
        return False

if __name__ == "__main__":
    success = main()
    
    print(f"\n🏁 Verification suite completed at: {datetime.now().isoformat()}")
    
    if success:
        print("🎊 Enterprise security verification: SUCCESS")
        sys.exit(0)
    else:
        print("💥 Enterprise security verification: FAILED")
        sys.exit(1)