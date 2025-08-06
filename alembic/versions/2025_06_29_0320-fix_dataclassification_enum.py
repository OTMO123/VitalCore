"""Fix dataclassification enum - ensure public value exists

Revision ID: 2025_06_29_0320
Revises: 9312029e80a7
Create Date: 2025-06-29 03:20:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '2025_06_29_0320'
down_revision = '9312029e80a7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if 'public' value exists in dataclassification enum, if not add it
    # This is a safe operation that won't fail if the value already exists
    try:
        op.execute("ALTER TYPE dataclassification ADD VALUE IF NOT EXISTS 'public'")
    except Exception:
        # In case IF NOT EXISTS is not supported, try alternative approach
        op.execute("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'public' AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'dataclassification')) THEN
                    ALTER TYPE dataclassification ADD VALUE 'public';
                END IF;
            END
            $$;
        """)


def downgrade() -> None:
    # Note: PostgreSQL doesn't support removing enum values
    # This would require recreating the enum type which is complex
    pass