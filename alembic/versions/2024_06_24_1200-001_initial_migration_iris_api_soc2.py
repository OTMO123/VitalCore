"""Initial migration - IRIS API system with SOC2 compliance

Revision ID: 001
Revises: 
Create Date: 2024-06-24 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create custom enums
    api_status_enum = postgresql.ENUM('active', 'inactive', 'maintenance', 'deprecated', name='apistatus')
    api_status_enum.create(op.get_bind())
    
    request_status_enum = postgresql.ENUM('pending', 'in_progress', 'completed', 'failed', 'timeout', 'circuit_broken', name='requeststatus')
    request_status_enum.create(op.get_bind())
    
    audit_event_type_enum = postgresql.ENUM('access', 'modify', 'delete', 'authenticate', 'authorize', 'api_call', 'purge', 'export', 'configuration_change', name='auditeventtype')
    audit_event_type_enum.create(op.get_bind())
    
    data_classification_enum = postgresql.ENUM('public', 'internal', 'confidential', 'restricted', 'phi', 'pii', name='dataclassification')
    data_classification_enum.create(op.get_bind())
    
    # Core System Configuration Table
    op.create_table('system_configuration',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('key', sa.String(255), unique=True, nullable=False),
        sa.Column('value', postgresql.JSONB(), nullable=False),
        sa.Column('encrypted', sa.Boolean(), default=False),
        sa.Column('data_classification', data_classification_enum, default='internal'),
        sa.Column('description', sa.Text()),
        sa.Column('valid_from', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('valid_to', sa.DateTime(timezone=True)),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('modified_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('modified_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.Integer(), default=1),
        sa.CheckConstraint('valid_to IS NULL OR valid_to > valid_from', name='check_valid_dates')
    )
    
    # Users table with enhanced security
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('email_verified', sa.Boolean(), default=False),
        sa.Column('username', sa.String(100), unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('mfa_secret', sa.String(255)),
        sa.Column('mfa_enabled', sa.Boolean(), default=False),
        sa.Column('failed_login_attempts', sa.Integer(), default=0),
        sa.Column('locked_until', sa.DateTime(timezone=True)),
        sa.Column('last_login_at', sa.DateTime(timezone=True)),
        sa.Column('last_login_ip', postgresql.INET()),
        sa.Column('password_changed_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('must_change_password', sa.Boolean(), default=False),
        sa.Column('api_key_hash', sa.String(255), unique=True),
        sa.Column('api_key_last_used', sa.DateTime(timezone=True)),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_system_user', sa.Boolean(), default=False),
        sa.Column('deactivated_at', sa.DateTime(timezone=True)),
        sa.CheckConstraint('locked_until IS NULL OR locked_until > CURRENT_TIMESTAMP', name='check_lock_validity')
    )
    
    # Roles table
    op.create_table('roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('name', sa.String(100), unique=True, nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('parent_role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('roles.id')),
        sa.Column('is_system_role', sa.Boolean(), default=False)
    )
    
    # Permissions table
    op.create_table('permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('resource', sa.String(255), nullable=False),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('is_system_permission', sa.Boolean(), default=False)
    )
    op.create_index('unique_resource_action', 'permissions', ['resource', 'action'], unique=True)
    
    # Role-Permission mapping
    op.create_table('role_permissions',
        sa.Column('role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('permission_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('granted_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('granted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False)
    )
    
    # User-Role assignments
    op.create_table('user_roles',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('valid_from', sa.DateTime(timezone=True), server_default=sa.func.now(), primary_key=True),
        sa.Column('valid_to', sa.DateTime(timezone=True)),
        sa.Column('assigned_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('assignment_reason', sa.Text()),
        sa.CheckConstraint('valid_to IS NULL OR valid_to > valid_from', name='check_role_validity')
    )
    
    # API Endpoints configuration
    op.create_table('api_endpoints',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('name', sa.String(255), unique=True, nullable=False),
        sa.Column('base_url', sa.String(500), nullable=False),
        sa.Column('api_version', sa.String(50)),
        sa.Column('status', api_status_enum, default='active'),
        sa.Column('auth_type', sa.String(50), nullable=False),
        sa.Column('rate_limit_requests', sa.Integer()),
        sa.Column('rate_limit_window_seconds', sa.Integer()),
        sa.Column('timeout_seconds', sa.Integer(), default=30),
        sa.Column('retry_attempts', sa.Integer(), default=3),
        sa.Column('retry_delay_seconds', sa.Integer(), default=1),
        sa.Column('circuit_breaker_threshold', sa.Integer(), default=5),
        sa.Column('circuit_breaker_timeout_seconds', sa.Integer(), default=60),
        sa.Column('ssl_verify', sa.Boolean(), default=True),
        sa.Column('health_check_endpoint', sa.String(500)),
        sa.Column('health_check_interval_seconds', sa.Integer(), default=300),
        sa.Column('last_health_check_at', sa.DateTime(timezone=True)),
        sa.Column('last_health_check_status', sa.Boolean()),
        sa.Column('metadata', postgresql.JSONB(), default={}),
        sa.CheckConstraint("auth_type IN ('oauth2', 'hmac', 'jwt', 'api_key', 'basic')", name='check_auth_type')
    )
    
    # API Credentials vault
    op.create_table('api_credentials',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('api_endpoint_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('api_endpoints.id', ondelete='CASCADE'), nullable=False),
        sa.Column('credential_name', sa.String(255), nullable=False),
        sa.Column('encrypted_value', sa.Text(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True)),
        sa.Column('last_rotated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('rotation_reminder_at', sa.DateTime(timezone=True)),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False)
    )
    op.create_index('unique_endpoint_credential', 'api_credentials', ['api_endpoint_id', 'credential_name'], unique=True)
    
    # API Request tracking
    op.create_table('api_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('api_endpoint_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('api_endpoints.id'), nullable=False),
        sa.Column('correlation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('method', sa.String(20), nullable=False),
        sa.Column('endpoint_path', sa.String(500), nullable=False),
        sa.Column('request_headers', postgresql.JSONB()),
        sa.Column('request_body', postgresql.JSONB()),
        sa.Column('request_hash', sa.String(64)),
        sa.Column('response_status_code', sa.Integer()),
        sa.Column('response_headers', postgresql.JSONB()),
        sa.Column('response_body', postgresql.JSONB()),
        sa.Column('status', request_status_enum, default='pending'),
        sa.Column('attempt_count', sa.Integer(), default=1),
        sa.Column('total_duration_ms', sa.Integer()),
        sa.Column('error_message', sa.Text()),
        sa.Column('error_stack_trace', sa.Text()),
        sa.Column('ip_address', postgresql.INET()),
        sa.Column('user_agent', sa.Text()),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.CheckConstraint(
            "(status IN ('completed', 'failed', 'timeout') AND completed_at IS NOT NULL) OR "
            "(status IN ('pending', 'in_progress') AND completed_at IS NULL)",
            name='check_completion'
        )
    )
    
    # Immutable audit log table
    op.create_table('audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('timestamp', sa.DateTime(timezone=True), primary_key=True, server_default=sa.func.now()),
        sa.Column('event_type', audit_event_type_enum, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('session_id', postgresql.UUID(as_uuid=True)),
        sa.Column('correlation_id', postgresql.UUID(as_uuid=True)),
        sa.Column('resource_type', sa.String(100)),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True)),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('result', sa.String(50), nullable=False),
        sa.Column('ip_address', postgresql.INET()),
        sa.Column('user_agent', sa.Text()),
        sa.Column('request_method', sa.String(20)),
        sa.Column('request_path', sa.String(500)),
        sa.Column('request_body_hash', sa.String(64)),
        sa.Column('response_status_code', sa.Integer()),
        sa.Column('error_message', sa.Text()),
        sa.Column('metadata', postgresql.JSONB(), default={}),
        sa.Column('compliance_tags', postgresql.ARRAY(sa.String())),
        sa.Column('data_classification', data_classification_enum),
        sa.Column('previous_log_hash', sa.String(64)),
        sa.Column('log_hash', sa.String(64), nullable=False),
        sa.CheckConstraint("result IN ('success', 'failure', 'error', 'denied')", name='check_result')
    )
    
    # Healthcare: Patients table
    op.create_table('patients',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('external_id', sa.String(255), unique=True),
        sa.Column('mrn', sa.String(100)),
        sa.Column('first_name_encrypted', sa.Text(), nullable=False),
        sa.Column('last_name_encrypted', sa.Text(), nullable=False),
        sa.Column('date_of_birth_encrypted', sa.Text(), nullable=False),
        sa.Column('ssn_encrypted', sa.Text()),
        sa.Column('data_classification', data_classification_enum, default='phi'),
        sa.Column('consent_status', postgresql.JSONB(), default={}),
        sa.Column('iris_sync_status', sa.String(50)),
        sa.Column('iris_last_sync_at', sa.DateTime(timezone=True)),
        sa.Column('soft_deleted_at', sa.DateTime(timezone=True))
    )
    
    # Healthcare: Immunizations table
    op.create_table('immunizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('vaccine_code', sa.String(50), nullable=False),
        sa.Column('vaccine_name', sa.String(255)),
        sa.Column('administration_date', sa.DATE(), nullable=False),
        sa.Column('lot_number', sa.String(100)),
        sa.Column('manufacturer', sa.String(255)),
        sa.Column('dose_number', sa.Integer()),
        sa.Column('series_complete', sa.Boolean(), default=False),
        sa.Column('administered_by', sa.String(255)),
        sa.Column('administration_site', sa.String(100)),
        sa.Column('route', sa.String(50)),
        sa.Column('iris_record_id', sa.String(255)),
        sa.Column('data_source', sa.String(100)),
        sa.Column('soft_deleted_at', sa.DateTime(timezone=True))
    )
    
    # Healthcare: Clinical Documents table
    op.create_table('clinical_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('document_type', sa.String(100), nullable=False, index=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, default='final'),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=False, index=True),
        sa.Column('encounter_id', postgresql.UUID(as_uuid=True)),
        sa.Column('content_encrypted', sa.Text(), nullable=False),
        sa.Column('content_type', sa.String(100), default='text/plain'),
        sa.Column('content_hash', sa.String(64), nullable=False),
        sa.Column('data_classification', data_classification_enum, default='phi'),
        sa.Column('confidentiality_level', sa.String(20), default='R'),
        sa.Column('access_level', sa.String(50), default='restricted'),
        sa.Column('fhir_resource_type', sa.String(100), default='DocumentReference'),
        sa.Column('fhir_identifier', sa.String(255)),
        sa.Column('category', postgresql.JSONB()),
        sa.Column('author_references', postgresql.ARRAY(sa.String()), default=[]),
        sa.Column('custodian_reference', sa.String(255)),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('authorized_roles', postgresql.ARRAY(sa.String()), default=[]),
        sa.Column('authorized_users', postgresql.ARRAY(sa.String())),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True)),
        sa.Column('access_count', sa.Integer(), default=0),
        sa.Column('retention_date', sa.DateTime(timezone=True)),
        sa.Column('soft_deleted_at', sa.DateTime(timezone=True)),
        sa.CheckConstraint("status IN ('preliminary', 'final', 'amended', 'entered-in-error')", name='check_document_status'),
        sa.CheckConstraint("access_level IN ('public', 'restricted', 'confidential', 'secret')", name='check_access_level')
    )
    op.create_index('idx_patient_document_type', 'clinical_documents', ['patient_id', 'document_type'])
    op.create_index('idx_document_created_at', 'clinical_documents', [sa.text('created_at DESC')])
    
    # Healthcare: Consents table
    op.create_table('consents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=False, index=True),
        sa.Column('consent_types', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, default='active'),
        sa.Column('purpose_codes', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('data_types', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('categories', postgresql.ARRAY(sa.String())),
        sa.Column('effective_period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('effective_period_end', sa.DateTime(timezone=True)),
        sa.Column('legal_basis', sa.String(255), nullable=False),
        sa.Column('jurisdiction', sa.String(100)),
        sa.Column('policy_references', postgresql.ARRAY(sa.String())),
        sa.Column('consent_method', sa.String(100), nullable=False),
        sa.Column('consent_source', sa.String(255)),
        sa.Column('witness_signature', sa.Text()),
        sa.Column('signature_data', postgresql.JSONB()),
        sa.Column('patient_signature', sa.Text()),
        sa.Column('guardian_signature', sa.Text()),
        sa.Column('guardian_relationship', sa.String(100)),
        sa.Column('granted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('verification_method', sa.String(100)),
        sa.Column('verification_date', sa.DateTime(timezone=True)),
        sa.Column('withdrawal_allowed', sa.Boolean(), default=True),
        sa.Column('withdrawal_method', sa.String(255)),
        sa.Column('objection_handling', sa.Text()),
        sa.Column('version', sa.Integer(), default=1),
        sa.Column('superseded_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('consents.id')),
        sa.Column('supersedes', postgresql.UUID(as_uuid=True)),
        sa.CheckConstraint("status IN ('draft', 'proposed', 'active', 'rejected', 'inactive', 'entered-in-error')", name='check_consent_status'),
        sa.CheckConstraint('effective_period_end IS NULL OR effective_period_end > effective_period_start', name='check_consent_validity'),
        sa.CheckConstraint("consent_method IN ('written', 'verbal', 'electronic', 'implied')", name='check_consent_method')
    )
    op.create_index('idx_patient_consent_status', 'consents', ['patient_id', 'status'])
    op.create_index('idx_consent_effective_period', 'consents', ['effective_period_start', 'effective_period_end'])
    
    # Healthcare: PHI Access Log table
    op.create_table('phi_access_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('access_session_id', sa.String(255), nullable=False, index=True),
        sa.Column('correlation_id', postgresql.UUID(as_uuid=True)),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=False, index=True),
        sa.Column('clinical_document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('clinical_documents.id')),
        sa.Column('consent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('consents.id')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('user_role', sa.String(100), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True)),
        sa.Column('access_type', sa.String(50), nullable=False),
        sa.Column('phi_fields_accessed', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('access_purpose', sa.String(255), nullable=False),
        sa.Column('legal_basis', sa.String(255), nullable=False),
        sa.Column('request_method', sa.String(20)),
        sa.Column('request_path', sa.String(500)),
        sa.Column('request_parameters', postgresql.JSONB()),
        sa.Column('access_granted', sa.Boolean(), nullable=False),
        sa.Column('denial_reason', sa.String(255)),
        sa.Column('data_returned', sa.Boolean(), default=False),
        sa.Column('data_hash', sa.String(64)),
        sa.Column('ip_address', postgresql.INET()),
        sa.Column('user_agent', sa.Text()),
        sa.Column('session_duration_ms', sa.Integer()),
        sa.Column('consent_verified', sa.Boolean(), default=False),
        sa.Column('minimum_necessary_applied', sa.Boolean(), default=False),
        sa.Column('data_classification', data_classification_enum, default='phi'),
        sa.Column('retention_category', sa.String(100), default='audit_log'),
        sa.Column('emergency_access', sa.Boolean(), default=False),
        sa.Column('emergency_justification', sa.Text()),
        sa.Column('supervisor_approval', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('unusual_access_pattern', sa.Boolean(), default=False),
        sa.Column('risk_score', sa.Integer()),
        sa.Column('flagged_for_review', sa.Boolean(), default=False),
        sa.Column('access_started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('access_ended_at', sa.DateTime(timezone=True)),
        sa.CheckConstraint("access_type IN ('view', 'edit', 'print', 'export', 'delete', 'bulk_access')", name='check_access_type'),
        sa.CheckConstraint('access_ended_at IS NULL OR access_ended_at >= access_started_at', name='check_access_duration'),
        sa.CheckConstraint('risk_score IS NULL OR (risk_score >= 0 AND risk_score <= 100)', name='check_risk_score_range')
    )
    op.create_index('idx_access_timestamp', 'phi_access_logs', [sa.text('access_started_at DESC')])
    op.create_index('idx_patient_access_audit', 'phi_access_logs', ['patient_id', 'access_started_at'])
    op.create_index('idx_user_access_audit', 'phi_access_logs', ['user_id', 'access_started_at'])
    op.create_index('idx_unusual_access', 'phi_access_logs', ['unusual_access_pattern', 'flagged_for_review'])


def downgrade() -> None:
    # Drop tables in reverse order to handle foreign key constraints
    op.drop_table('phi_access_logs')
    op.drop_table('consents')
    op.drop_table('clinical_documents')
    op.drop_table('immunizations')
    op.drop_table('patients')
    op.drop_table('audit_logs')
    op.drop_table('api_requests')
    op.drop_table('api_credentials')
    op.drop_table('api_endpoints')
    op.drop_table('user_roles')
    op.drop_table('role_permissions')
    op.drop_table('permissions')
    op.drop_table('roles')
    op.drop_table('users')
    op.drop_table('system_configuration')
    
    # Drop custom enums
    op.execute('DROP TYPE IF EXISTS dataclassification')
    op.execute('DROP TYPE IF EXISTS auditeventtype')
    op.execute('DROP TYPE IF EXISTS requeststatus')
    op.execute('DROP TYPE IF EXISTS apistatus')