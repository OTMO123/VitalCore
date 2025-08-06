"""add_document_storage_tables

Revision ID: 2025_06_29_1200
Revises: 2025_06_29_0320
Create Date: 2025-06-29 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2025_06_29_1200'
down_revision = '2025_06_29_0320'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create document_type enum
    document_type_enum = postgresql.ENUM(
        'lab_result', 'imaging', 'clinical_note', 'prescription', 
        'discharge_summary', 'operative_report', 'pathology_report',
        'radiology_report', 'consultation_note', 'progress_note',
        'medication_list', 'allergy_list', 'vital_signs', 'insurance_card',
        'identification_document', 'consent_form', 'referral', 'other',
        name='document_type_enum'
    )
    document_type_enum.create(op.get_bind())
    
    # Create document_action enum for audit trail
    document_action_enum = postgresql.ENUM(
        'upload', 'view', 'download', 'update', 'delete', 'share', 
        'print', 'classify', 'extract_text', 'version_create',
        name='document_action_enum'
    )
    document_action_enum.create(op.get_bind())

    # Create document_storage table
    op.create_table('document_storage',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('storage_path', sa.String(length=500), nullable=False),
        sa.Column('storage_bucket', sa.String(length=100), nullable=False, default='documents'),
        sa.Column('file_size_bytes', sa.BigInteger(), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('hash_sha256', sa.String(length=64), nullable=False),
        sa.Column('encryption_key_id', sa.String(length=100), nullable=False),
        
        # Document classification and metadata
        sa.Column('document_type', document_type_enum, nullable=False),
        sa.Column('document_category', sa.String(length=100), nullable=True),
        sa.Column('auto_classification_confidence', sa.Numeric(precision=5, scale=2), nullable=True),
        
        # Content and search
        sa.Column('extracted_text', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, default={}),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True, default=[]),
        
        # Versioning
        sa.Column('version', sa.Integer(), nullable=False, default=1),
        sa.Column('parent_document_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_latest_version', sa.Boolean(), nullable=False, default=True),
        
        # Audit and compliance
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        
        # SOC2 compliance metadata
        sa.Column('access_log_ids', postgresql.ARRAY(postgresql.UUID()), nullable=True, default=[]),
        sa.Column('compliance_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, default={}),
        
        # Soft delete
        sa.Column('soft_deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deletion_reason', sa.String(length=500), nullable=True),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ),
        sa.ForeignKeyConstraint(['parent_document_id'], ['document_storage.id'], ),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['deleted_by'], ['users.id'], ),
        
        # Constraints
        sa.CheckConstraint('file_size_bytes > 0', name='valid_file_size'),
        sa.CheckConstraint('auto_classification_confidence BETWEEN 0 AND 100', name='valid_confidence'),
        sa.CheckConstraint('version > 0', name='valid_version'),
    )

    # Create document_access_audit table for blockchain-like audit trail
    op.create_table('document_access_audit',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', document_action_enum, nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),  # IPv6 support
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('accessed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        
        # Blockchain-like verification
        sa.Column('previous_hash', sa.String(length=64), nullable=True),
        sa.Column('current_hash', sa.String(length=64), nullable=False),
        sa.Column('block_number', sa.BigInteger(), nullable=False),
        
        # Additional metadata
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('request_details', postgresql.JSONB(astext_type=sa.Text()), nullable=True, default={}),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['document_id'], ['document_storage.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        
        # Ensure hash integrity
        sa.UniqueConstraint('current_hash', name='unique_audit_hash'),
    )

    # Create document_shares table for secure document sharing
    op.create_table('document_shares',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('shared_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('shared_with', postgresql.UUID(as_uuid=True), nullable=True),  # Null for public shares
        sa.Column('share_token', sa.String(length=255), nullable=False),  # Encrypted share token
        sa.Column('permissions', postgresql.JSONB(astext_type=sa.Text()), nullable=False, default={'view': True}),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('accessed_count', sa.Integer(), nullable=False, default=0),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_by', postgresql.UUID(as_uuid=True), nullable=True),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['document_id'], ['document_storage.id'], ),
        sa.ForeignKeyConstraint(['shared_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['shared_with'], ['users.id'], ),
        sa.ForeignKeyConstraint(['revoked_by'], ['users.id'], ),
        
        sa.UniqueConstraint('share_token', name='unique_share_token'),
    )

    # Create indexes for performance
    op.create_index('idx_document_storage_patient_id', 'document_storage', ['patient_id'])
    op.create_index('idx_document_storage_type', 'document_storage', ['document_type'])
    op.create_index('idx_document_storage_uploaded_at', 'document_storage', ['uploaded_at'])
    op.create_index('idx_document_storage_tags', 'document_storage', ['tags'], postgresql_using='gin')
    op.create_index('idx_document_storage_metadata', 'document_storage', ['metadata'], postgresql_using='gin')
    op.create_index('idx_document_storage_hash', 'document_storage', ['hash_sha256'])
    op.create_index('idx_document_storage_soft_deleted', 'document_storage', ['soft_deleted_at'])
    
    # Audit table indexes
    op.create_index('idx_document_audit_document_id', 'document_access_audit', ['document_id'])
    op.create_index('idx_document_audit_user_id', 'document_access_audit', ['user_id'])
    op.create_index('idx_document_audit_accessed_at', 'document_access_audit', ['accessed_at'])
    op.create_index('idx_document_audit_action', 'document_access_audit', ['action'])
    op.create_index('idx_document_audit_block_number', 'document_access_audit', ['block_number'])
    
    # Shares table indexes
    op.create_index('idx_document_shares_document_id', 'document_shares', ['document_id'])
    op.create_index('idx_document_shares_shared_with', 'document_shares', ['shared_with'])
    op.create_index('idx_document_shares_expires_at', 'document_shares', ['expires_at'])
    op.create_index('idx_document_shares_revoked_at', 'document_shares', ['revoked_at'])

    # Create full-text search index for extracted text
    op.execute("CREATE INDEX idx_document_storage_extracted_text_fts ON document_storage USING gin(to_tsvector('english', extracted_text))")


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('idx_document_storage_extracted_text_fts', table_name='document_storage')
    op.drop_index('idx_document_shares_revoked_at', table_name='document_shares')
    op.drop_index('idx_document_shares_expires_at', table_name='document_shares')
    op.drop_index('idx_document_shares_shared_with', table_name='document_shares')
    op.drop_index('idx_document_shares_document_id', table_name='document_shares')
    op.drop_index('idx_document_audit_block_number', table_name='document_access_audit')
    op.drop_index('idx_document_audit_action', table_name='document_access_audit')
    op.drop_index('idx_document_audit_accessed_at', table_name='document_access_audit')
    op.drop_index('idx_document_audit_user_id', table_name='document_access_audit')
    op.drop_index('idx_document_audit_document_id', table_name='document_access_audit')
    op.drop_index('idx_document_storage_soft_deleted', table_name='document_storage')
    op.drop_index('idx_document_storage_hash', table_name='document_storage')
    op.drop_index('idx_document_storage_metadata', table_name='document_storage')
    op.drop_index('idx_document_storage_tags', table_name='document_storage')
    op.drop_index('idx_document_storage_uploaded_at', table_name='document_storage')
    op.drop_index('idx_document_storage_type', table_name='document_storage')
    op.drop_index('idx_document_storage_patient_id', table_name='document_storage')
    
    # Drop tables
    op.drop_table('document_shares')
    op.drop_table('document_access_audit')
    op.drop_table('document_storage')
    
    # Drop enums
    document_action_enum = postgresql.ENUM(name='document_action_enum')
    document_action_enum.drop(op.get_bind())
    
    document_type_enum = postgresql.ENUM(name='document_type_enum')
    document_type_enum.drop(op.get_bind())