"""add compliance reports table

Revision ID: add_compliance_reports
Revises: 09fbede3d137
Create Date: 2025-07-30 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_compliance_reports'
down_revision = '09fbede3d137'
branch_labels = None
depends_on = None


def upgrade():
    """Add compliance_reports table for SOC2 compliance reporting"""
    op.create_table('compliance_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('report_type', sa.String(length=100), nullable=False),
        sa.Column('reporting_period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('reporting_period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('generated_by', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('summary', sa.JSON(), nullable=True),
        sa.Column('findings', sa.JSON(), nullable=True),
        sa.Column('recommendations', sa.JSON(), nullable=True),
        sa.Column('metrics', sa.JSON(), nullable=True),
        sa.Column('total_events_analyzed', sa.Integer(), nullable=True),
        sa.Column('data_sources', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('export_format', sa.String(length=50), nullable=True),
        sa.Column('file_path', sa.String(length=512), nullable=True),
        sa.Column('file_size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('checksum', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_compliance_reports_report_type'), 'compliance_reports', ['report_type'], unique=False)
    op.create_index(op.f('ix_compliance_reports_created_at'), 'compliance_reports', ['created_at'], unique=False)
    op.create_index(op.f('ix_compliance_reports_status'), 'compliance_reports', ['status'], unique=False)


def downgrade():
    """Remove compliance_reports table"""
    op.drop_index(op.f('ix_compliance_reports_status'), table_name='compliance_reports')
    op.drop_index(op.f('ix_compliance_reports_created_at'), table_name='compliance_reports')
    op.drop_index(op.f('ix_compliance_reports_report_type'), table_name='compliance_reports')
    op.drop_table('compliance_reports')