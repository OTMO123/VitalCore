#!/usr/bin/env python3
"""
Fix Audit Logs Schema - Column Rename (result -> outcome)

This script applies the specific fix for the audit_logs table column mismatch
that prevents proper SOC2 audit logging compliance.

SECURITY CRITICAL: This fixes the schema mismatch that causes audit logging failures,
which is a SOC2 Type II compliance violation.
"""

import sqlite3
import sys
import os
from pathlib import Path

def fix_audit_logs_schema():
    """Apply the audit_logs schema fix for result->outcome column rename"""
    
    print("CRITICAL SECURITY FIX: Fixing audit_logs schema for SOC2 compliance")
    print("=" * 60)
    
    # Database file path - check common locations
    possible_paths = [
        Path(__file__).parent / "data" / "temp" / "iris_dev.db",
        Path(__file__).parent / "data" / "temp" / "test.db",
        Path(__file__).parent / "iris_dev.db",
        Path(__file__).parent / "test.db"
    ]
    
    db_path = None
    for path in possible_paths:
        if path.exists():
            db_path = path
            break
    
    if db_path is None:
        print("No SQLite database found - system may be using PostgreSQL")
        print("For PostgreSQL, run: python3 -c \"from alembic import command; from alembic.config import Config; cfg = Config('alembic.ini'); command.upgrade(cfg, 'head')\"")
        return True
    
    try:
        print(f"Found database at: {db_path}")
        
        # Connect to SQLite database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        print("Step 1: Checking current audit_logs table structure...")
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='audit_logs'")
        if not cursor.fetchone():
            print("audit_logs table does not exist - no fix needed")
            return True
            
        cursor.execute("PRAGMA table_info(audit_logs)")
        columns = cursor.fetchall()
        
        column_names = [col[1] for col in columns]
        print(f"Current columns: {column_names}")
        
        # Check if we need to apply the fix
        has_result = 'result' in column_names
        has_outcome = 'outcome' in column_names
        
        if has_outcome and not has_result:
            print("SUCCESS: Schema already fixed - outcome column exists")
            return True
        
        if not has_result:
            print("No result column found - schema may already be correct")
            return True
            
        print("Step 2: Schema mismatch detected - applying fix...")
        print("Renaming 'result' column to 'outcome' for SOC2 compliance")
        
        # Begin transaction
        cursor.execute("BEGIN TRANSACTION")
        
        # For SQLite, we need to recreate the table with the correct column name
        # Get current data
        cursor.execute("SELECT * FROM audit_logs LIMIT 5")
        sample_data = cursor.fetchall()
        print(f"Found {len(sample_data)} sample records to migrate")
        
        # Create backup table
        cursor.execute("""
            CREATE TABLE audit_logs_backup AS 
            SELECT * FROM audit_logs
        """)
        print("Created backup of existing data")
        
        # Drop original table
        cursor.execute("DROP TABLE audit_logs")
        
        # Create new table with correct schema
        cursor.execute("""
            CREATE TABLE audit_logs (
                id TEXT PRIMARY KEY,
                timestamp DATETIME NOT NULL,
                event_type TEXT NOT NULL,
                user_id TEXT,
                session_id TEXT,
                correlation_id TEXT,
                resource_type TEXT,
                resource_id TEXT,
                action TEXT,
                outcome TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                request_method TEXT,
                request_path TEXT,
                request_body_hash TEXT,
                response_status_code INTEGER,
                error_message TEXT,
                config_metadata TEXT,
                compliance_tags TEXT,
                data_classification TEXT,
                previous_log_hash TEXT,
                log_hash TEXT NOT NULL
            )
        """)
        print("Created new audit_logs table with 'outcome' column")
        
        # Migrate data from backup to new table
        cursor.execute("""
            INSERT INTO audit_logs (
                id, timestamp, event_type, user_id, session_id, correlation_id,
                resource_type, resource_id, action, outcome, ip_address, user_agent,
                request_method, request_path, request_body_hash, response_status_code,
                error_message, config_metadata, compliance_tags, data_classification,
                previous_log_hash, log_hash
            )
            SELECT 
                id, timestamp, event_type, user_id, session_id, correlation_id,
                resource_type, resource_id, action, result as outcome, ip_address, user_agent,
                request_method, request_path, request_body_hash, response_status_code,
                error_message, config_metadata, compliance_tags, data_classification,
                previous_log_hash, log_hash
            FROM audit_logs_backup
        """)
        
        # Verify the migration
        cursor.execute("SELECT COUNT(*) FROM audit_logs")
        new_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM audit_logs_backup")
        old_count = cursor.fetchone()[0]
        
        if new_count != old_count:
            print(f"ERROR: Data migration failed - {old_count} -> {new_count}")
            cursor.execute("ROLLBACK")
            return False
        
        print(f"Successfully migrated {new_count} audit log records")
        
        # Verify the fix
        print("Step 3: Verifying schema fix...")
        cursor.execute("PRAGMA table_info(audit_logs)")
        new_columns = cursor.fetchall()
        new_column_names = [col[1] for col in new_columns]
        
        if 'outcome' in new_column_names and 'result' not in new_column_names:
            print("SUCCESS: Schema fix verified")
            print(f"Fixed columns: {new_column_names}")
            
            # Commit changes
            cursor.execute("COMMIT")
            print("Changes committed to database")
            
            # Clean up backup table
            cursor.execute("DROP TABLE audit_logs_backup")
            print("Backup table cleaned up")
            
        else:
            print("ERROR: Schema fix verification failed")
            cursor.execute("ROLLBACK")
            return False
            
        conn.close()
        print("SECURITY FIX COMPLETE: SOC2 audit logging schema now compliant")
        return True
        
    except Exception as e:
        print(f"ERROR applying schema fix: {e}")
        if 'conn' in locals():
            try:
                conn.rollback()
                conn.close()
            except:
                pass
        return False

if __name__ == "__main__":
    success = fix_audit_logs_schema()
    if success:
        print("\nAudit logs schema fix completed successfully")
        print("SOC2 compliance restored - audit logging will now work properly")
    else:
        print("\nSchema fix failed - manual intervention may be required")
        sys.exit(1)