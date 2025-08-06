"""add pgcrypto extension

Revision ID: add_pgcrypto_ext
Revises: add_compliance_reports
Create Date: 2025-07-30 18:01:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_pgcrypto_ext'
down_revision = 'add_compliance_reports'
branch_labels = None
depends_on = None


def upgrade():
    """Add pgcrypto extension for enhanced cryptographic functions"""
    # Create pgcrypto extension if it doesn't exist
    op.execute('CREATE EXTENSION IF NOT EXISTS pgcrypto;')


def downgrade():
    """Remove pgcrypto extension"""
    # Note: We don't drop the extension in downgrade as it might be used by other parts
    # op.execute('DROP EXTENSION IF EXISTS pgcrypto;')
    pass