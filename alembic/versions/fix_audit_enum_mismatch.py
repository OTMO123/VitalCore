"""Fix audit enum mismatch - align database with code expectations

Revision ID: fix_audit_enum
Revises: 2025_06_29_0320-fix_dataclassification_enum
Create Date: 2025-06-29 16:56:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'fix_audit_enum'
down_revision = '2025_06_29_0320'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Fix the audit event type enum to match code expectations"""
    
    # First, rename the old enum
    op.execute("ALTER TYPE auditeventtype RENAME TO auditeventtype_old")
    
    # Create new enum with correct values
    audit_event_type_enum = postgresql.ENUM(
        'user_login', 'user_logout', 'user_login_failed', 
        'user_created', 'user_updated', 'user_deleted',
        'phi_accessed', 'phi_created', 'phi_updated', 'phi_deleted', 'phi_exported',
        'patient_created', 'patient_updated', 'patient_accessed', 'patient_search',
        'document_created', 'document_accessed', 'document_updated', 'document_deleted',
        'consent_granted', 'consent_withdrawn', 'consent_updated',
        'system_access', 'config_changed', 'security_violation', 'data_breach_detected',
        'api_request', 'api_response', 'api_error',
        'iris_sync_started', 'iris_sync_completed', 'iris_sync_failed',
        # Legacy compatibility values
        'access', 'modify', 'delete', 'authenticate', 'authorize', 'api_call', 'purge', 'export', 'configuration_change',
        name='auditeventtype'
    )
    audit_event_type_enum.create(op.get_bind())
    
    # Update audit_logs table to use new enum with value mapping
    op.execute("""
        ALTER TABLE audit_logs 
        ALTER COLUMN event_type TYPE auditeventtype 
        USING CASE 
            WHEN event_type::text = 'access' THEN 'system_access'::auditeventtype
            WHEN event_type::text = 'modify' THEN 'phi_updated'::auditeventtype  
            WHEN event_type::text = 'delete' THEN 'phi_deleted'::auditeventtype
            WHEN event_type::text = 'authenticate' THEN 'user_login'::auditeventtype
            WHEN event_type::text = 'authorize' THEN 'system_access'::auditeventtype
            WHEN event_type::text = 'api_call' THEN 'api_request'::auditeventtype
            WHEN event_type::text = 'purge' THEN 'phi_deleted'::auditeventtype
            WHEN event_type::text = 'export' THEN 'phi_exported'::auditeventtype
            WHEN event_type::text = 'configuration_change' THEN 'config_changed'::auditeventtype
            ELSE event_type::text::auditeventtype
        END
    """)
    
    # Drop old enum
    op.execute("DROP TYPE auditeventtype_old")


def downgrade() -> None:
    """Revert to old enum values"""
    
    # Rename current enum
    op.execute("ALTER TYPE auditeventtype RENAME TO auditeventtype_new")
    
    # Recreate old enum
    audit_event_type_enum_old = postgresql.ENUM(
        'access', 'modify', 'delete', 'authenticate', 'authorize', 
        'api_call', 'purge', 'export', 'configuration_change', 
        name='auditeventtype'
    )
    audit_event_type_enum_old.create(op.get_bind())
    
    # Update audit_logs table back to old enum with reverse mapping
    op.execute("""
        ALTER TABLE audit_logs 
        ALTER COLUMN event_type TYPE auditeventtype 
        USING CASE 
            WHEN event_type::text = 'system_access' THEN 'access'::auditeventtype
            WHEN event_type::text = 'phi_updated' THEN 'modify'::auditeventtype  
            WHEN event_type::text = 'phi_deleted' THEN 'delete'::auditeventtype
            WHEN event_type::text = 'user_login' THEN 'authenticate'::auditeventtype
            WHEN event_type::text = 'api_request' THEN 'api_call'::auditeventtype
            WHEN event_type::text = 'phi_exported' THEN 'export'::auditeventtype
            WHEN event_type::text = 'config_changed' THEN 'configuration_change'::auditeventtype
            ELSE 'access'::auditeventtype  -- Default fallback
        END
    """)
    
    # Drop new enum
    op.execute("DROP TYPE auditeventtype_new")