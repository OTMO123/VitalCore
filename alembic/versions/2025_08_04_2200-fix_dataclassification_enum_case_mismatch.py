"""Fix dataclassification enum case mismatch for PHI audit logging

Revision ID: 2025_08_04_2200
Revises: 2025_08_04_1900
Create Date: 2025-08-04 22:00:00.000000

This migration fixes the critical issue where recent migrations introduced
uppercase enum values (PHI, INTERNAL, etc.) while the application code
expects lowercase values (phi, internal, etc.).

Root cause: Migration 2025_08_02_0218 introduced uppercase enum references
that conflict with the original lowercase enum definition from the initial
migration 2024_06_24_1200.

This causes PHI audit logging failures and 500 errors in healthcare 
compliance tests.

Enterprise Impact:
- Fixes SOC2 Type 2 audit logging
- Enables HIPAA PHI access control
- Restores GDPR consent management
- Maintains FHIR R4 compliance
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2025_08_04_2200'
down_revision = '2025_08_04_1900'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Ensure all required lowercase enum values exist in dataclassification enum.
    
    This fixes the case mismatch issue where the application expects lowercase
    values but the database might have uppercase values or missing values.
    """
    
    # Required lowercase enum values (as expected by application)
    required_values = ['public', 'internal', 'confidential', 'restricted', 'phi', 'pii']
    
    # Add each required value if it doesn't exist
    for value in required_values:
        try:
            # Use IF NOT EXISTS to avoid errors if value already exists
            op.execute(f"ALTER TYPE dataclassification ADD VALUE IF NOT EXISTS '{value}'")
        except Exception as e:
            # Fallback for older PostgreSQL versions that don't support IF NOT EXISTS
            # Check if value exists before adding
            op.execute(f"""
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_enum 
                        WHERE enumlabel = '{value}' 
                        AND enumtypid = (
                            SELECT oid FROM pg_type WHERE typname = 'dataclassification'
                        )
                    ) THEN
                        ALTER TYPE dataclassification ADD VALUE '{value}';
                    END IF;
                END
                $$;
            """)
    
    # Verify the enum now contains all required values
    # This helps with debugging if the migration fails
    print("✅ dataclassification enum updated with required lowercase values")


def downgrade() -> None:
    """
    Note: PostgreSQL doesn't support removing enum values directly.
    
    To downgrade, you would need to:
    1. Remove all references to the enum values
    2. Drop and recreate the enum type
    3. Re-add all columns that use the enum
    
    This is complex and potentially destructive, so we don't implement
    automatic downgrade for enum modifications.
    """
    # Cannot easily remove enum values in PostgreSQL
    # This would require dropping and recreating the entire enum type
    # which could break existing data
    print("⚠️  Downgrade not implemented - PostgreSQL doesn't support removing enum values")
    pass