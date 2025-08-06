"""Fix metadata column name conflict

Revision ID: fix_metadata_column
Revises: [previous_revision]
Create Date: 2025-06-29 23:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'fix_metadata_column'
down_revision = None  # Update this to the latest revision
branch_labels = None
depends_on = None

def upgrade():
    """Rename metadata column to document_metadata to avoid SQLAlchemy conflict"""
    # Check if the column exists first
    connection = op.get_bind()
    
    # Check if document_storage table exists
    inspector = sa.Inspector.from_engine(connection)
    tables = inspector.get_table_names()
    
    if 'document_storage' in tables:
        columns = [col['name'] for col in inspector.get_columns('document_storage')]
        
        if 'metadata' in columns and 'document_metadata' not in columns:
            # Rename the column
            op.alter_column('document_storage', 'metadata', 
                          new_column_name='document_metadata')
            print("✅ Renamed metadata column to document_metadata")
        else:
            print("ℹ️  Column already properly named or doesn't exist")
    else:
        print("ℹ️  document_storage table doesn't exist yet")

def downgrade():
    """Revert metadata column name"""
    connection = op.get_bind()
    inspector = sa.Inspector.from_engine(connection)
    tables = inspector.get_table_names()
    
    if 'document_storage' in tables:
        columns = [col['name'] for col in inspector.get_columns('document_storage')]
        
        if 'document_metadata' in columns:
            op.alter_column('document_storage', 'document_metadata',
                          new_column_name='metadata')