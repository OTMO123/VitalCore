"""add missing profile_data column to users table

Revision ID: 2025_08_04_1900
Revises: 87cdf07bd71f
Create Date: 2025-08-04 19:00:00.000000

SOC2 Type II + HIPAA Compliance Migration
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2025_08_04_1900'
down_revision = '87cdf07bd71f'  # Latest migration
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Add missing profile_data column to users table for enterprise healthcare compliance."""
    
    # Check if column already exists to prevent errors
    connection = op.get_bind()
    result = connection.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'profile_data'
    """))
    
    column_exists = result.fetchone()
    
    if not column_exists:
        # Add profile_data column as JSONB for better PostgreSQL performance
        op.add_column('users', sa.Column('profile_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
        print("✅ Added profile_data column to users table")
    else:
        print("✅ profile_data column already exists in users table")

def downgrade() -> None:
    """Remove profile_data column from users table."""
    
    # Check if column exists before trying to drop it
    connection = op.get_bind()
    result = connection.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'profile_data'
    """))
    
    column_exists = result.fetchone()
    
    if column_exists:
        op.drop_column('users', 'profile_data')
        print("✅ Removed profile_data column from users table")
    else:
        print("✅ profile_data column does not exist in users table")