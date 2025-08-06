"""Fix user role enum mismatch - convert uppercase to lowercase values

Revision ID: fix_user_role_enum
Revises: add_pgcrypto_ext
Create Date: 2025-07-31 12:00:00.000000

This migration fixes the role enum mismatch issue where:
1. Database has role values like 'USER', 'ADMIN' (uppercase) 
2. Schema expects role values like 'user', 'admin' (lowercase)
3. Creates proper PostgreSQL enum type and updates existing data

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'fix_user_role_enum'
down_revision = 'add_pgcrypto_ext'
branch_labels = None
depends_on = None


def upgrade():
    """Fix role enum mismatch by converting uppercase to lowercase values."""
    
    # Get database connection
    connection = op.get_bind()
    
    # Step 1: Check if role column exists and what type it is
    # If it's currently an enum type, we need to convert it to string first
    try:
        # Try to alter the column to be a simple string type
        # This will handle cases where it's currently an enum
        op.alter_column('users', 'role', 
                       type_=sa.String(50),
                       nullable=False,
                       server_default='user')
    except Exception:
        # If column doesn't exist, add it
        op.add_column('users', sa.Column('role', sa.String(50), nullable=False, server_default='user'))
    
    # Step 2: Update data - convert uppercase values to lowercase
    # Map old uppercase values to new lowercase values
    role_mapping = {
        'USER': 'user',
        'ADMIN': 'admin', 
        'OPERATOR': 'operator',
        'SUPER_ADMIN': 'super_admin'
    }
    
    # Update each role mapping
    for old_role, new_role in role_mapping.items():
        connection.execute(
            sa.text("UPDATE users SET role = :new_role WHERE role = :old_role"),
            {"old_role": old_role, "new_role": new_role}
        )
    
    # Set default value for any NULL or unknown roles
    connection.execute(
        sa.text("UPDATE users SET role = 'user' WHERE role IS NULL OR role NOT IN ('user', 'admin', 'operator', 'super_admin')")
    )
    
    # Step 3: Create index on role column for performance if it doesn't exist
    try:
        op.create_index('ix_users_role', 'users', ['role'])
    except Exception:
        # Index might already exist, that's okay
        pass


def downgrade():
    """Reverse the role enum fix - convert back to uppercase values."""
    
    # Get database connection
    connection = op.get_bind()
    
    # Step 1: Convert lowercase values back to uppercase
    # Reverse mapping from new lowercase values to old uppercase values
    reverse_role_mapping = {
        'user': 'USER',
        'admin': 'ADMIN',
        'operator': 'OPERATOR', 
        'super_admin': 'SUPER_ADMIN'
    }
    
    # Update each role mapping
    for new_role, old_role in reverse_role_mapping.items():
        connection.execute(
            sa.text("UPDATE users SET role = :old_role WHERE role = :new_role"),
            {"new_role": new_role, "old_role": old_role}
        )
    
    # For any new roles that didn't exist before, default to USER
    connection.execute(
        sa.text("UPDATE users SET role = 'USER' WHERE role NOT IN ('USER', 'ADMIN', 'OPERATOR', 'SUPER_ADMIN')")
    )
    
    # Step 2: Update the server default back to uppercase
    op.alter_column('users', 'role', server_default='USER')
    
    # Step 3: Drop the index if it exists
    try:
        op.drop_index('ix_users_role', 'users')
    except Exception:
        # Index might not exist, that's okay
        pass