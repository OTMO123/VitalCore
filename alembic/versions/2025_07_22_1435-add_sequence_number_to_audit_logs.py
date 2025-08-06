"""Add sequence_number to audit_logs table

Revision ID: add_audit_sequence_num  
Revises: fix_audit_result_outcome
Create Date: 2025-07-22 14:35:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_audit_sequence_num'
down_revision = 'fix_audit_result_outcome'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add sequence_number column to audit_logs table."""
    
    # Add sequence_number column
    op.add_column('audit_logs', 
        sa.Column('sequence_number', sa.Integer(), nullable=True)
    )
    
    # Create an index on sequence_number for performance
    op.create_index(
        'ix_audit_logs_sequence_number',
        'audit_logs',
        ['sequence_number']
    )


def downgrade() -> None:
    """Remove sequence_number column from audit_logs table."""
    
    # Drop the index first
    op.drop_index('ix_audit_logs_sequence_number', table_name='audit_logs')
    
    # Drop the column
    op.drop_column('audit_logs', 'sequence_number')