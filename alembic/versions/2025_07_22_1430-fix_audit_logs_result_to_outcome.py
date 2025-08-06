"""Fix audit_logs.result column to audit_logs.outcome

Revision ID: fix_audit_result_outcome
Revises: fix_inet_compatibility
Create Date: 2025-07-22 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'fix_audit_result_outcome'
down_revision = 'fix_inet_compatibility'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Rename audit_logs.result column to outcome to match the model."""
    
    # Step 1: Add the new outcome column
    op.add_column('audit_logs', 
        sa.Column('outcome', sa.String(50), nullable=True)
    )
    
    # Step 2: Copy data from result to outcome
    op.execute("UPDATE audit_logs SET outcome = result WHERE result IS NOT NULL")
    
    # Step 3: Make outcome NOT NULL
    op.alter_column('audit_logs', 'outcome',
        existing_type=sa.String(50),
        nullable=False
    )
    
    # Step 4: Drop the old result column
    op.drop_column('audit_logs', 'result')
    
    # Step 5: Update the check constraint
    op.drop_constraint('check_result', 'audit_logs', type_='check')
    op.create_check_constraint(
        'check_outcome', 
        'audit_logs',
        "outcome IN ('success', 'failure', 'error', 'denied')"
    )


def downgrade() -> None:
    """Rename audit_logs.outcome column back to result."""
    
    # Step 1: Add the result column back
    op.add_column('audit_logs', 
        sa.Column('result', sa.String(50), nullable=True)
    )
    
    # Step 2: Copy data from outcome to result
    op.execute("UPDATE audit_logs SET result = outcome WHERE outcome IS NOT NULL")
    
    # Step 3: Make result NOT NULL
    op.alter_column('audit_logs', 'result',
        existing_type=sa.String(50),
        nullable=False
    )
    
    # Step 4: Drop the outcome column
    op.drop_column('audit_logs', 'outcome')
    
    # Step 5: Update the check constraint back
    op.drop_constraint('check_outcome', 'audit_logs', type_='check')
    op.create_check_constraint(
        'check_result', 
        'audit_logs',
        "result IN ('success', 'failure', 'error', 'denied')"
    )