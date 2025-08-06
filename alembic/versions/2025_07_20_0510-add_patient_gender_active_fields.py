"""add_patient_gender_active_fields

Revision ID: 2025_07_20_0510
Revises: 2025_07_19_2330
Create Date: 2025-07-20 05:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2025_07_20_0510'
down_revision = '2025_07_19_2330'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add gender and active fields to patients table."""
    # Add gender field (nullable string)
    op.add_column('patients', sa.Column('gender', sa.String(20), nullable=True))
    
    # Add active field (boolean with default True)
    op.add_column('patients', sa.Column('active', sa.Boolean(), nullable=False, server_default='true'))


def downgrade() -> None:
    """Remove gender and active fields from patients table."""
    op.drop_column('patients', 'active')
    op.drop_column('patients', 'gender')