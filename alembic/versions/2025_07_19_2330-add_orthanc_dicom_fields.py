"""add_orthanc_dicom_fields_to_document_storage

Revision ID: 2025_07_19_2330
Revises: 2025_06_29_1200
Create Date: 2025-07-19 23:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2025_07_19_2330'
down_revision = '2025_06_29_1200'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add Orthanc and DICOM integration fields to document_storage table."""
    # Add DICOM and Orthanc integration fields
    op.add_column('document_storage', sa.Column('orthanc_instance_id', sa.String(100), nullable=True))
    op.add_column('document_storage', sa.Column('orthanc_series_id', sa.String(100), nullable=True))
    op.add_column('document_storage', sa.Column('orthanc_study_id', sa.String(100), nullable=True))
    op.add_column('document_storage', sa.Column('dicom_metadata', sa.JSON(), nullable=True))
    
    # Create indexes for Orthanc fields for efficient lookups
    op.create_index('ix_document_storage_orthanc_instance_id', 'document_storage', ['orthanc_instance_id'])
    op.create_index('ix_document_storage_orthanc_series_id', 'document_storage', ['orthanc_series_id'])
    op.create_index('ix_document_storage_orthanc_study_id', 'document_storage', ['orthanc_study_id'])


def downgrade() -> None:
    """Remove Orthanc and DICOM integration fields from document_storage table."""
    # Drop indexes first
    op.drop_index('ix_document_storage_orthanc_study_id', 'document_storage')
    op.drop_index('ix_document_storage_orthanc_series_id', 'document_storage')
    op.drop_index('ix_document_storage_orthanc_instance_id', 'document_storage')
    
    # Remove columns
    op.drop_column('document_storage', 'dicom_metadata')
    op.drop_column('document_storage', 'orthanc_study_id')
    op.drop_column('document_storage', 'orthanc_series_id')
    op.drop_column('document_storage', 'orthanc_instance_id')