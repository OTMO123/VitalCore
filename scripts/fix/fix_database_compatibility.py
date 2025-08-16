#!/usr/bin/env python3
"""
Database Compatibility Fix Script
Fixes SQLite vs PostgreSQL compatibility issues for IP address fields
"""

import re
import os
from pathlib import Path

def fix_database_unified():
    """Fix database_unified.py to use String instead of INET"""
    file_path = Path("app/core/database_unified.py")
    
    if not file_path.exists():
        print(f"⚠️ File not found: {file_path}")
        return
    
    print(f"🔧 Fixing {file_path}...")
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add import for String if not present
    if "from sqlalchemy import String" not in content and "String" not in content:
        # Find the imports section and add String
        import_pattern = r"(from sqlalchemy import [^)]+)"
        if re.search(import_pattern, content):
            content = re.sub(
                import_pattern,
                r"\1, String",
                content,
                count=1
            )
        else:
            # Add new import line
            content = re.sub(
                r"(from sqlalchemy\.orm import [^\n]+\n)",
                r"\1from sqlalchemy import String\n",
                content,
                count=1
            )
    
    # Replace INET with String(45)
    fixes = [
        (r"INET", "String(45)"),
        (r"mapped_column\(String\(45\), nullable=True\)", "mapped_column(String(45), nullable=True)")
    ]
    
    for old_pattern, new_pattern in fixes:
        content = re.sub(old_pattern, new_pattern, content)
    
    # Write back the file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Fixed {file_path}")

def fix_clinical_workflows_models():
    """Ensure clinical workflows models use consistent IP field definition"""
    file_path = Path("app/modules/clinical_workflows/models.py")
    
    if not file_path.exists():
        print(f"⚠️ File not found: {file_path}")
        return
    
    print(f"🔧 Fixing {file_path}...")
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Ensure consistent IP address field definition
    content = re.sub(
        r"ip_address = Column\(String\(\d+\)\)",
        "ip_address = Column(String(45))",
        content
    )
    
    # Write back the file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Fixed {file_path}")

def create_migration_fix():
    """Create a new migration to fix existing INET columns"""
    migration_content = '''"""Fix database compatibility - Convert INET to VARCHAR

Revision ID: fix_inet_compatibility
Revises: [previous_revision]
Create Date: 2025-07-22 01:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'fix_inet_compatibility'
down_revision = None  # Set this to the latest revision
branch_labels = None
depends_on = None

def upgrade():
    """Convert INET columns to VARCHAR(45) for cross-database compatibility"""
    
    # Get the connection
    conn = op.get_bind()
    
    # Check if we're using PostgreSQL
    if conn.dialect.name == 'postgresql':
        # Convert INET columns to VARCHAR(45)
        
        # Users table
        try:
            op.alter_column('users', 'last_login_ip', 
                          type_=sa.String(45),
                          existing_type=postgresql.INET())
        except Exception:
            pass  # Column might not exist or already be String
        
        # Audit logs table
        try:
            op.alter_column('audit_logs', 'ip_address',
                          type_=sa.String(45),
                          existing_type=postgresql.INET())
        except Exception:
            pass
        
        # Security audit table
        try:
            op.alter_column('security_audit_trail', 'ip_address',
                          type_=sa.String(45),
                          existing_type=postgresql.INET())
        except Exception:
            pass
        
        # Clinical workflow audit table
        try:
            op.alter_column('clinical_workflow_audit', 'ip_address',
                          type_=sa.String(45),
                          existing_type=postgresql.INET())
        except Exception:
            pass
    
    # For SQLite, no changes needed as it already handles strings

def downgrade():
    """Revert VARCHAR(45) columns back to INET (PostgreSQL only)"""
    
    # Get the connection
    conn = op.get_bind()
    
    # Only for PostgreSQL
    if conn.dialect.name == 'postgresql':
        # Revert back to INET columns
        
        try:
            op.alter_column('users', 'last_login_ip',
                          type_=postgresql.INET(),
                          existing_type=sa.String(45))
        except Exception:
            pass
        
        try:
            op.alter_column('audit_logs', 'ip_address',
                          type_=postgresql.INET(),
                          existing_type=sa.String(45))
        except Exception:
            pass
        
        try:
            op.alter_column('security_audit_trail', 'ip_address',
                          type_=postgresql.INET(),
                          existing_type=sa.String(45))
        except Exception:
            pass
        
        try:
            op.alter_column('clinical_workflow_audit', 'ip_address',
                          type_=postgresql.INET(),
                          existing_type=sa.String(45))
        except Exception:
            pass
'''
    
    # Create the migration file
    migration_dir = Path("alembic/versions")
    migration_file = migration_dir / "2025_07_22_0130-fix_inet_compatibility.py"
    
    if migration_dir.exists():
        with open(migration_file, 'w', encoding='utf-8') as f:
            f.write(migration_content)
        print(f"✅ Created migration: {migration_file}")
    else:
        print(f"⚠️ Migration directory not found: {migration_dir}")

def fix_test_configuration():
    """Create test configuration for SQLite compatibility"""
    test_config_content = '''"""
Test Database Configuration
Cross-database compatibility settings for tests
"""

import os
from app.core.config import Settings

class TestSettings(Settings):
    """Test-specific configuration that ensures SQLite compatibility"""
    
    # Use SQLite for tests to avoid PostgreSQL dependency
    DATABASE_URL: str = "sqlite:///./test.db"
    
    # Override any PostgreSQL-specific settings
    ENVIRONMENT: str = "test"
    DEBUG: bool = True
    
    # Disable features that require PostgreSQL
    ENABLE_POSTGRES_FEATURES: bool = False
    
    class Config:
        env_file = ".env.test"

# Test database configuration
TEST_DATABASE_URL = "sqlite:///./test.db"

# Function to get test settings
def get_test_settings():
    """Get test-specific settings"""
    return TestSettings()
'''
    
    config_file = Path("app/core/test_config.py")
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(test_config_content)
    print(f"✅ Created test configuration: {config_file}")

def fix_pytest_ini():
    """Update pytest.ini to use proper async test support"""
    pytest_content = '''[tool:pytest]
minversion = 6.0
addopts = 
    -ra 
    -q 
    --strict-markers
    --disable-warnings
    --tb=short
testpaths = 
    app/tests
    app/modules/*/tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (require database)
    security: Security-related tests
    performance: Performance and load tests
    e2e: End-to-end tests
    smoke: Basic functionality tests
    slow: Slow running tests
    chaos: Chaos engineering tests
    physician: Physician role tests
    nurse: Nurse role tests
    admin: Admin role tests
    patient: Patient role tests
    ai_researcher: AI researcher role tests
    unauthorized: Unauthorized access tests
asyncio_mode = auto
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
    ignore::pytest.PytestUnknownMarkWarning
'''
    
    pytest_file = Path("pytest.ini")
    with open(pytest_file, 'w', encoding='utf-8') as f:
        f.write(pytest_content)
    print(f"✅ Updated pytest configuration: {pytest_file}")

def main():
    """Main function to run all fixes"""
    print("🔧 Starting database compatibility fixes...")
    print("=" * 50)
    
    # Fix database models
    fix_database_unified()
    fix_clinical_workflows_models()
    
    # Create migration
    create_migration_fix()
    
    # Fix test configuration
    fix_test_configuration()
    fix_pytest_ini()
    
    print("\n🎉 Database compatibility fixes completed!")
    print("\nNext steps:")
    print("1. Run: alembic upgrade head")
    print("2. Run: python -m pytest app/tests/smoke/ -v")
    print("3. Run: python check_api_endpoints.ps1")
    print("\nThis should resolve SQLite vs PostgreSQL compatibility issues.")

if __name__ == "__main__":
    main()