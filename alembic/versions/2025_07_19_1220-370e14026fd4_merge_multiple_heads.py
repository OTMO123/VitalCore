"""merge_multiple_heads

Revision ID: 370e14026fd4
Revises: 2025_06_29_1200, fix_audit_enum, fix_metadata_column
Create Date: 2025-07-19 12:20:57.140706

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '370e14026fd4'
down_revision = ('2025_06_29_1200', 'fix_audit_enum', 'fix_metadata_column')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass