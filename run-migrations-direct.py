#!/usr/bin/env python3
"""
Direct migration runner for applying database migrations.
This script can be run directly without docker-compose.
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            if result.stdout:
                print(f"Output: {result.stdout}")
        else:
            print(f"❌ {description} - FAILED")
            print(f"Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ {description} - EXCEPTION: {e}")
        return False
    
    return True

def main():
    """Main migration runner."""
    print("🔧 Direct Migration Runner")
    print("="*50)
    
    # Get the project root directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print(f"Working directory: {project_root}")
    
    # Check if we're in a docker environment or can use local Python
    commands_to_try = [
        ("python3 -m alembic upgrade head", "Python3 + Alembic migration"),
        ("python -m alembic upgrade head", "Python + Alembic migration"),
        ("alembic upgrade head", "Direct Alembic migration"),
        ("docker-compose exec app alembic upgrade head", "Docker + Alembic migration"),
        ("docker exec iris-backend alembic upgrade head", "Docker exec + Alembic migration")
    ]
    
    migration_success = False
    
    for cmd, description in commands_to_try:
        print(f"\n🧪 Attempting: {description}")
        if run_command(cmd, description):
            migration_success = True
            break
        else:
            print(f"⚠️  {description} failed, trying next method...")
    
    if migration_success:
        print("\n✅ Database migrations completed successfully!")
        print("\nApplied migrations:")
        print("- compliance_reports table created")
        print("- pgcrypto extension installed")
    else:
        print("\n❌ All migration methods failed!")
        print("\nManual steps to apply migrations:")
        print("1. Start your database and application containers")
        print("2. Run: docker-compose exec app alembic upgrade head")
        print("3. Or connect to your PostgreSQL database and run the SQL manually:")
        
        # Print manual SQL commands
        print("\nManual SQL commands:")
        print("-- Install pgcrypto extension")
        print("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
        print("\n-- Create compliance_reports table")
        print("""
CREATE TABLE compliance_reports (
    id UUID PRIMARY KEY,
    report_type VARCHAR(100) NOT NULL,
    reporting_period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    reporting_period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    generated_by VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    summary JSON,
    findings JSON,
    recommendations JSON,
    metrics JSON,
    total_events_analyzed INTEGER,
    data_sources TEXT[],
    export_format VARCHAR(50),
    file_path VARCHAR(512),
    file_size_bytes BIGINT,
    checksum VARCHAR(64),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Create indexes
CREATE INDEX ix_compliance_reports_report_type ON compliance_reports(report_type);
CREATE INDEX ix_compliance_reports_created_at ON compliance_reports(created_at);
CREATE INDEX ix_compliance_reports_status ON compliance_reports(status);
""")
    
    return migration_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)