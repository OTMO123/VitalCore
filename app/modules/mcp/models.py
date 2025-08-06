"""
MCP Database Models for Healthcare Platform V2.0

SQLAlchemy models for MCP protocol with full audit trails and compliance tracking.
All models include SOC2/HIPAA audit fields and encryption support.
"""

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Float, Text, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from app.core.database_unified import Base

class MCPAgent(Base):
    """Model for registered MCP agents with compliance tracking."""
    
    __tablename__ = "mcp_agents"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    agent_id = Column(String(255), unique=True, nullable=False, index=True)
    agent_name = Column(String(255), nullable=False)
    
    # Agent status and configuration
    status = Column(String(50), nullable=False, default="initializing", index=True)
    capabilities = Column(JSON, nullable=False, default={})
    endpoint_url = Column(String(512))
    public_key = Column(Text)  # For encryption
    
    # Performance tracking
    total_consultations = Column(Integer, default=0)
    successful_consultations = Column(Integer, default=0)
    failed_consultations = Column(Integer, default=0)
    average_rating = Column(Float, default=0.0)
    average_response_time_ms = Column(Float, default=0.0)
    uptime_percentage = Column(Float, default=100.0)
    
    # Heartbeat and connectivity
    last_heartbeat = Column(DateTime(timezone=True))
    last_seen_at = Column(DateTime(timezone=True))
    connection_count = Column(Integer, default=0)
    
    # Compliance and security
    compliance_status = Column(String(50), default="verified")
    last_compliance_check = Column(DateTime(timezone=True))
    security_clearance = Column(String(50), default="internal")
    phi_access_approved = Column(Boolean, default=False)
    hipaa_compliant = Column(Boolean, default=True)
    soc2_compliant = Column(Boolean, default=True)
    
    # Audit and tracking
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    created_by = Column(String(255), default="system")
    
    # SOC2 audit fields
    audit_version = Column(Integer, default=1)
    audit_hash = Column(String(64))  # For integrity verification
    audit_metadata = Column(JSON, default={})
    
    def __repr__(self):
        return f"<MCPAgent(agent_id='{self.agent_id}', status='{self.status}', specialties={len(self.capabilities.get('medical_specialties', []))})>"

class MCPMessageLog(Base):
    """Audit log for all MCP messages with HIPAA compliance."""
    
    __tablename__ = "mcp_message_logs"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    message_id = Column(String(255), nullable=False, unique=True, index=True)
    
    # Message routing
    message_type = Column(String(100), nullable=False, index=True)
    from_agent = Column(String(255), nullable=False, index=True)
    to_agent = Column(String(255), index=True)  # Null for broadcast messages
    
    # Security and compliance
    security_level = Column(String(50), nullable=False, index=True)
    contains_phi = Column(Boolean, nullable=False, default=False, index=True)
    phi_access_reason = Column(String(255))
    encrypted_payload = Column(Boolean, default=False)
    
    # Processing information
    processing_time_ms = Column(Float)
    status = Column(String(50), nullable=False, index=True)
    error_code = Column(String(100))
    error_message = Column(Text)
    
    # Medical context
    urgency_level = Column(String(50), index=True)
    patient_id_hash = Column(String(64), index=True)  # Hashed patient ID
    case_id = Column(String(255), index=True)
    medical_specialties = Column(JSON, default=[])
    
    # FHIR context
    fhir_resources = Column(JSON, default=[])
    fhir_version = Column(String(10), default="R4")
    
    # Compliance tracking
    hipaa_logged = Column(Boolean, default=True, nullable=False)
    soc2_category = Column(String(100), default="agent_communication")
    gdpr_compliant = Column(Boolean, default=True)
    consent_verified = Column(Boolean, default=False)
    
    # Audit and integrity
    timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    audit_hash = Column(String(64), nullable=False)  # Cryptographic integrity hash
    audit_signature = Column(Text)  # Digital signature for non-repudiation
    
    # Retention and lifecycle
    retention_category = Column(String(50), default="standard")  # standard, extended, permanent
    scheduled_deletion_date = Column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<MCPMessageLog(message_id='{self.message_id}', type='{self.message_type}', phi={self.contains_phi})>"

class AgentConsultation(Base):
    """Medical consultations processed through MCP with full audit trail."""
    
    __tablename__ = "agent_consultations"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    consultation_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Consultation participants
    requesting_agent = Column(String(255), nullable=False, index=True)
    consulting_agents = Column(JSON, default=[])  # List of agents that participated
    
    # Patient and case information (anonymized/hashed)
    patient_id_hash = Column(String(64), index=True)  # Hashed for privacy
    case_summary = Column(Text)  # Truncated, anonymized summary
    case_summary_encrypted = Column(Text)  # Encrypted full case data
    
    # Medical context
    symptoms = Column(JSON, default=[])
    vital_signs = Column(JSON, default={})
    medical_history = Column(JSON, default=[])
    current_medications = Column(JSON, default=[])
    
    # Consultation parameters
    requested_specialties = Column(JSON, default=[])
    urgency_level = Column(String(50), nullable=False, index=True)
    max_response_time_seconds = Column(Integer, default=300)
    
    # Results and outcomes
    responses_received = Column(Integer, default=0)
    consensus_reached = Column(Boolean, default=False)
    recommended_actions = Column(JSON, default=[])
    differential_diagnosis = Column(JSON, default=[])
    confidence_scores = Column(JSON, default={})  # Per-agent confidence
    
    # Quality and validation
    human_review_required = Column(Boolean, default=False)
    human_review_completed = Column(Boolean, default=False)
    quality_score = Column(Float)
    accuracy_verified = Column(Boolean, default=False)
    
    # Compliance and security
    anonymized = Column(Boolean, default=True, nullable=False)
    consent_obtained = Column(Boolean, nullable=False, default=False, index=True)
    phi_access_reason = Column(String(255), nullable=False, default="treatment")
    phi_access_logged = Column(Boolean, default=False)
    
    # FHIR compliance
    fhir_resources = Column(JSON, default=[])
    fhir_bundle_id = Column(String(255))
    fhir_validated = Column(Boolean, default=False)
    
    # Processing metrics
    total_processing_time_ms = Column(Float)
    average_agent_response_time_ms = Column(Float)
    tokens_consumed = Column(Integer, default=0)
    
    # Timing and lifecycle
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    completed_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
    
    # Audit and integrity
    audit_trail_id = Column(String(255))
    audit_hash = Column(String(64))
    last_modified_by = Column(String(255), default="system")
    version = Column(Integer, default=1)
    
    # SOC2 compliance fields
    data_classification = Column(String(50), default="phi_restricted")
    access_control_applied = Column(Boolean, default=True)
    encryption_applied = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<AgentConsultation(consultation_id='{self.consultation_id}', urgency='{self.urgency_level}', agents={len(self.consulting_agents)})>"

class MCPPerformanceMetrics(Base):
    """Performance metrics and monitoring for MCP agents."""
    
    __tablename__ = "mcp_performance_metrics"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(String(255), nullable=False, index=True)
    
    # Performance measurements
    measurement_timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    response_time_ms = Column(Float, nullable=False)
    cpu_usage_percent = Column(Float)
    memory_usage_mb = Column(Float)
    active_connections = Column(Integer, default=0)
    
    # Message processing metrics
    messages_processed_last_hour = Column(Integer, default=0)
    messages_failed_last_hour = Column(Integer, default=0)
    average_confidence_score = Column(Float)
    
    # Medical quality metrics
    consultations_completed = Column(Integer, default=0)
    consultations_escalated = Column(Integer, default=0)
    accuracy_score = Column(Float)
    patient_satisfaction_score = Column(Float)
    
    # Availability metrics
    uptime_seconds = Column(Integer, default=0)
    downtime_seconds = Column(Integer, default=0)
    error_rate_percent = Column(Float, default=0.0)
    
    # Compliance metrics
    phi_accesses_compliant = Column(Integer, default=0)
    phi_accesses_total = Column(Integer, default=0)
    audit_logs_generated = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<MCPPerformanceMetrics(agent_id='{self.agent_id}', timestamp='{self.measurement_timestamp}')>"

class MCPSecurityEvent(Base):
    """Security events and violations in MCP communications."""
    
    __tablename__ = "mcp_security_events"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    event_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Event classification
    event_type = Column(String(100), nullable=False, index=True)  # unauthorized_access, encryption_failure, etc.
    severity_level = Column(String(50), nullable=False, index=True)  # low, medium, high, critical
    
    # Event details
    agent_id = Column(String(255), index=True)
    message_id = Column(String(255), index=True)
    source_ip = Column(String(45))  # IPv6 compatible
    user_agent = Column(String(512))
    
    # Security context
    security_violation_type = Column(String(100))
    attempted_action = Column(String(255))
    access_denied_reason = Column(String(255))
    
    # Impact assessment
    phi_potentially_exposed = Column(Boolean, default=False, index=True)
    systems_affected = Column(JSON, default=[])
    estimated_impact = Column(String(100))
    
    # Response and remediation
    automated_response_taken = Column(Boolean, default=False)
    manual_intervention_required = Column(Boolean, default=False)
    incident_resolved = Column(Boolean, default=False)
    resolution_notes = Column(Text)
    
    # Compliance and reporting
    reported_to_authorities = Column(Boolean, default=False)
    breach_notification_sent = Column(Boolean, default=False)
    regulatory_reporting_required = Column(Boolean, default=False)
    
    # Timing
    event_timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    detection_timestamp = Column(DateTime(timezone=True), default=func.now())
    resolution_timestamp = Column(DateTime(timezone=True))
    
    # Audit trail
    created_by = Column(String(255), default="security_monitor")
    investigated_by = Column(String(255))
    audit_hash = Column(String(64))
    
    def __repr__(self):
        return f"<MCPSecurityEvent(event_type='{self.event_type}', severity='{self.severity_level}', resolved={self.incident_resolved})>"

# Create indexes for performance and compliance queries
Index('idx_mcp_agents_status_specialty', MCPAgent.status, MCPAgent.capabilities.op('->>')('medical_specialties'))
Index('idx_mcp_messages_phi_urgency', MCPMessageLog.contains_phi, MCPMessageLog.urgency_level, MCPMessageLog.timestamp)
Index('idx_consultations_urgency_time', AgentConsultation.urgency_level, AgentConsultation.created_at)
Index('idx_consultations_patient_consent', AgentConsultation.patient_id_hash, AgentConsultation.consent_obtained)
Index('idx_security_events_severity_time', MCPSecurityEvent.severity_level, MCPSecurityEvent.event_timestamp)
Index('idx_performance_agent_time', MCPPerformanceMetrics.agent_id, MCPPerformanceMetrics.measurement_timestamp)

# Add comments for documentation
MCPAgent.__table__.comment = "Registry of MCP agents with compliance and performance tracking"
MCPMessageLog.__table__.comment = "Immutable audit log of all MCP messages for HIPAA/SOC2 compliance"
AgentConsultation.__table__.comment = "Medical consultations processed through MCP with full audit trail"
MCPPerformanceMetrics.__table__.comment = "Performance monitoring and quality metrics for MCP agents"
MCPSecurityEvent.__table__.comment = "Security events and violations in MCP communications"