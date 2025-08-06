"""Fix database compatibility - Convert INET to VARCHAR

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
