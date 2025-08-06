"""merge_migration_heads

Revision ID: 09fbede3d137
Revises: 3015d4f5bfb4, add_audit_sequence_num
Create Date: 2025-07-23 04:13:55.785932

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '09fbede3d137'
down_revision = ('3015d4f5bfb4', 'add_audit_sequence_num')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass