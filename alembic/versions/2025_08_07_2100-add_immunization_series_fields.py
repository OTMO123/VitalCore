"""Add immunization series completion fields

Revision ID: add_immunization_series_fields
Revises: 2025_08_04_2200-fix_dataclassification_enum_case_mismatch
Create Date: 2025-08-07 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Boolean, Integer


# revision identifiers, used by Alembic.
revision = 'add_immunization_series_fields'
down_revision = '2025_08_04_2200'
branch_labels = None
depends_on = None


def upgrade():
    """Add series_complete and series_dosed columns to immunizations table."""
    # Add series_complete column (not null with default False)
    op.add_column('immunizations', sa.Column('series_complete', Boolean, nullable=False, default=False, comment='Whether vaccine series is complete'))
    
    # Add series_dosed column (nullable with default 1)
    op.add_column('immunizations', sa.Column('series_dosed', Integer, nullable=True, default=1, comment='Number of doses administered in series'))
    
    # Set existing records to have series_complete=False and series_dosed=1
    op.execute("UPDATE immunizations SET series_complete = false WHERE series_complete IS NULL")
    op.execute("UPDATE immunizations SET series_dosed = 1 WHERE series_dosed IS NULL")


def downgrade():
    """Remove series_complete and series_dosed columns from immunizations table."""
    op.drop_column('immunizations', 'series_dosed')
    op.drop_column('immunizations', 'series_complete')