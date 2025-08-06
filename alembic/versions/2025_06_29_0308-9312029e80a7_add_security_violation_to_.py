"""Add security_violation to auditeventtype enum

Revision ID: 9312029e80a7
Revises: 001
Create Date: 2025-06-29 03:08:13.767687

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9312029e80a7'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add 'security_violation' to the auditeventtype enum
    op.execute("ALTER TYPE auditeventtype ADD VALUE 'security_violation'")


def downgrade() -> None:
    # Note: PostgreSQL does not support removing enum values once added
    # The 'security_violation' value will remain in the enum type
    pass