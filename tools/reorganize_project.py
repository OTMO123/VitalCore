#!/usr/bin/env python3
"""
Project Reorganization Script
Safely moves files to proper directory structure
"""

import os
import shutil
from pathlib import Path

def create_directories():
    """Create the new directory structure"""
    dirs_to_create = [
        '_archive/debug',
        '_archive/temp_scripts', 
        '_archive/old_tests',
        '_archive/old_docs',
        'tools/database',
        'tools/testing',
        'tools/monitoring',
        'data/backups',
        'data/exports', 
        'data/seeds',
        'docs/context',
        'docs/api',
        'docs/deployment'
    ]
    
    for dir_path in dirs_to_create:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {dir_path}")

def move_files():
    """Move files to appropriate directories"""
    
    # Files to move to _archive/debug/
    debug_files = [
        'debug_application_code.py',
        'debug_backend_issues.py', 
        'debug_events.py',
        'diagnose_exact_issues.py',
        'diagnostic_without_asyncpg.py',
        'comprehensive_diagnostic.py',
        'check_actual_data.py',
        'check_and_fix_users.py',
        'check_backend.py',
        'check_enums.py',
        'check_real_data.py',
        'fix_all_issues.py',
        'fix_audit_id_issue.py',
        'fix_audit_logger_enums.py',
        'fix_audit_timestamps.py',
        'fix_consent_schema.py',
        'fix_database_enum.py',
        'fix_database_tables.py',
        'fix_dataclassification_enum.py',
        'fix_db_simple.py',
        'fix_patient_constraint.py',
        'fix_remaining_endpoints.py',
        'final_100_percent_fix.py',
        'final_comprehensive_fix.py',
        'final_diagnostic_test.py',
        'complete_database_fix.py',
        'nuclear_fix_all_constraints.py',
        'schema_diagnostic.py'
    ]
    
    # Files to move to _archive/temp_scripts/
    temp_scripts = [
        'add_diverse_events.py',
        'add_test_data.py',
        'add_test_data_simple.py',
        'add_test_patients.py',
        'create_test_patients.py',
        'test_api.py',
        'test_bulk_endpoint.py',
        'test_dashboard_data.py',
        'test_dashboard_with_data.py',
        'test_endpoints_quick.py',
        'test_endpoints_simple.py',
        'test_final_fix.py',
        'test_fixes.py',
        'test_frontend_endpoints.py',
        'test_frontend_integration_soc2.py',
        'test_simple.py',
        'test_soc2_basic.py',
        'test_soc2_simple.py',
        'quick_endpoint_test.py',
        'quick_risk_test.py',
        'quick_test.py',
        'smart_endpoint_test.py',
        'start_backend.py',
        'start_backend_simple.py',
        'run_soc2_tests.py'
    ]
    
    # Files to move to tools/database/
    database_tools = [
        'run_migration.py',
        'add_patients.sql',
        'quick_add_data.sql'
    ]
    
    # Files to move to data/
    data_files = [
        'backend.log',
        'soc2_test_results.json'
    ]
    
    # Other files to move to _archive/old_tests/
    old_test_files = [
        'test-backend-connectivity.js',
        'test_dashboard.ps1'
    ]
    
    # Execute moves
    moves = [
        (debug_files, '_archive/debug/'),
        (temp_scripts, '_archive/temp_scripts/'),
        (database_tools, 'tools/database/'),
        (data_files, 'data/'),
        (old_test_files, '_archive/old_tests/')
    ]
    
    for file_list, destination in moves:
        for file_name in file_list:
            if os.path.exists(file_name):
                try:
                    shutil.move(file_name, os.path.join(destination, file_name))
                    print(f"✅ Moved {file_name} to {destination}")
                except Exception as e:
                    print(f"❌ Failed to move {file_name}: {e}")
            else:
                print(f"⚠️  File not found: {file_name}")

def move_directories():
    """Move directories to proper locations"""
    
    directory_moves = [
        ('context', 'docs/context'),
        ('temp', 'data/temp'),
        ('tests', '_archive/old_tests/root_tests')  # Avoid conflict with app/tests
    ]
    
    for src, dest in directory_moves:
        if os.path.exists(src) and os.path.isdir(src):
            try:
                if os.path.exists(dest):
                    shutil.rmtree(dest)  # Remove existing destination
                shutil.move(src, dest)
                print(f"✅ Moved directory {src} to {dest}")
            except Exception as e:
                print(f"❌ Failed to move directory {src}: {e}")
        else:
            print(f"⚠️  Directory not found: {src}")

def cleanup_empty_dirs():
    """Remove empty directories"""
    try:
        # Remove venv if it exists (should be recreated)
        if os.path.exists('venv') and os.path.isdir('venv'):
            print("⚠️  Found venv directory - consider recreating it after reorganization")
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")

def main():
    """Main reorganization function"""
    print("🚀 Starting project reorganization...")
    print("=" * 50)
    
    # Change to project directory
    os.chdir('/mnt/c/Users/aurik/Code_Projects/2_scraper')
    
    create_directories()
    print("\n📁 Moving files...")
    move_files()
    print("\n📂 Moving directories...")
    move_directories()
    print("\n🧹 Cleanup...")
    cleanup_empty_dirs()
    
    print("\n" + "=" * 50)
    print("✨ Project reorganization complete!")
    print("\n📋 Next steps:")
    print("1. Review the new structure")
    print("2. Update any hardcoded paths in scripts")
    print("3. Test that the application still works")
    print("4. Consider removing _archive/ folder after verification")

if __name__ == "__main__":
    main()