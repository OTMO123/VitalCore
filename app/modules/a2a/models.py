"""
A2A Database Models for Healthcare Platform V2.0

SQLAlchemy models for Agent-to-Agent communication with full audit trails.
All models include SOC2/HIPAA compliance tracking and encryption support.
"""

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Float, Text, JSON, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database_unified import Base

class A2ACollaborationSession(Base):
    """Model for agent collaboration sessions with full audit trail."""
    
    __tablename__ = "a2a_collaboration_sessions"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    collaboration_id = Column(String(255), unique=True, nullable=False, index=True)
    case_id = Column(String(255), nullable=False, index=True)
    
    # Session participants
    requesting_agent = Column(String(255), nullable=False, index=True)
    participating_agents = Column(JSON, default=[])  # List of agent IDs
    total_participants = Column(Integer, default=0)
    
    # Session configuration
    collaboration_type = Column(String(100), default="consultation")
    consensus_mechanism = Column(String(100), default="weighted_expertise")
    max_response_time_minutes = Column(Integer, default=30)
    urgency_level = Column(String(50), default="routine")
    
    # Medical case context (anonymized)
    patient_age = Column(Integer)
    patient_gender = Column(String(20))
    patient_id_hash = Column(String(64), index=True)  # Hashed patient ID
    case_summary = Column(Text)  # Truncated summary
    case_summary_encrypted = Column(Text)  # Full encrypted case data
    
    # Clinical data
    chief_complaint = Column(Text)
    symptoms = Column(JSON, default=[])
    vital_signs = Column(JSON, default={})
    lab_results = Column(JSON, default={})
    imaging_results = Column(JSON, default=[])
    medical_history = Column(JSON, default=[])
    current_medications = Column(JSON, default=[])
    allergies = Column(JSON, default=[])
    
    # Collaboration parameters
    requested_specialties = Column(JSON, default=[])
    clinical_questions = Column(JSON, default=[])
    diagnostic_uncertainty = Column(JSON, default=[])
    treatment_dilemmas = Column(JSON, default=[])
    
    # Session status and outcomes
    status = Column(String(50), nullable=False, default="initializing", index=True)
    responses_received = Column(Integer, default=0)
    consensus_reached = Column(Boolean, default=False)
    human_review_required = Column(Boolean, default=False)
    escalation_triggered = Column(Boolean, default=False)
    escalation_reason = Column(Text)
    
    # Quality metrics
    agreement_score = Column(Float, default=0.0)
    confidence_variance = Column(Float, default=0.0)
    average_confidence = Column(Float, default=0.0)
    weighted_confidence = Column(Float, default=0.0)
    
    # Performance tracking
    total_processing_time_ms = Column(Float)
    average_response_time_ms = Column(Float)
    fastest_response_ms = Column(Float)
    slowest_response_ms = Column(Float)
    
    # Final outcomes
    final_recommendation = Column(JSON)  # Serialized final recommendation
    minority_opinions = Column(JSON, default=[])  # List of dissenting opinions
    follow_up_actions = Column(JSON, default=[])
    safety_concerns = Column(JSON, default=[])
    
    # FHIR compliance
    fhir_resources = Column(JSON, default=[])
    fhir_bundle_id = Column(String(255))
    fhir_validated = Column(Boolean, default=False)
    
    # Compliance and security
    anonymized = Column(Boolean, default=True, nullable=False)
    consent_obtained = Column(Boolean, nullable=False, default=False, index=True)
    phi_access_reason = Column(String(255), default="treatment")
    phi_accessed = Column(Boolean, default=False)
    all_agents_hipaa_compliant = Column(Boolean, default=True)
    audit_trail_complete = Column(Boolean, default=True)
    phi_handling_compliant = Column(Boolean, default=True)
    
    # Timing and lifecycle
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
    
    # Audit and integrity
    created_by = Column(String(255), default="a2a_system")
    last_modified_by = Column(String(255), default="a2a_system")
    version = Column(Integer, default=1)
    session_hash = Column(String(64))  # Cryptographic integrity hash
    audit_metadata = Column(JSON, default={})
    
    # SOC2 compliance fields
    data_classification = Column(String(50), default="phi_restricted")
    access_control_applied = Column(Boolean, default=True)
    encryption_applied = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<A2ACollaborationSession(collaboration_id='{self.collaboration_id}', case_id='{self.case_id}', participants={self.total_participants})>"

class A2AAgentInteraction(Base):
    """Model for individual agent interactions within collaboration sessions."""
    
    __tablename__ = "a2a_agent_interactions"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    interaction_id = Column(String(255), unique=True, nullable=False, index=True)
    collaboration_id = Column(String(255), ForeignKey('a2a_collaboration_sessions.collaboration_id'), nullable=False, index=True)
    
    # Agent information
    agent_id = Column(String(255), nullable=False, index=True)
    agent_specialty = Column(String(100), nullable=False, index=True)
    interaction_type = Column(String(100), default="recommendation")  # recommendation, question, clarification
    
    # Agent response
    primary_assessment = Column(Text)
    differential_diagnoses = Column(JSON, default=[])
    treatment_recommendations = Column(JSON, default=[])
    clinical_reasoning = Column(Text)
    
    # Confidence and quality
    overall_confidence = Column(Float, ge=0.0, le=1.0)
    specialist_confidence = Column(Float, ge=0.0, le=1.0)
    evidence_strength = Column(Float, default=0.0, ge=0.0, le=1.0)
    guideline_compliance = Column(Float, default=0.0, ge=0.0, le=1.0)
    
    # Collaboration dynamics
    agrees_with_agents = Column(JSON, default=[])  # Agent IDs agreed with
    disagrees_with_agents = Column(JSON, default=[])  # Agent IDs disagreed with
    requests_consultation_from = Column(JSON, default=[])  # Additional specialties requested
    collaboration_notes = Column(Text)
    
    # Quality assurance
    requires_further_evaluation = Column(Boolean, default=False)
    peer_review_requested = Column(Boolean, default=False)
    human_oversight_recommended = Column(Boolean, default=False)
    
    # Follow-up and monitoring
    follow_up_timeline = Column(String(255))
    warning_signs = Column(JSON, default=[])
    escalation_criteria = Column(JSON, default=[])
    
    # Processing information
    processing_time_ms = Column(Float, nullable=False)
    knowledge_sources = Column(JSON, default=[])
    model_version = Column(String(100))
    tokens_consumed = Column(Integer, default=0)
    
    # Compliance tracking
    phi_accessed = Column(Boolean, default=False)
    phi_access_justified = Column(Boolean, default=True)
    audit_logged = Column(Boolean, default=True)
    hipaa_compliant = Column(Boolean, default=True)
    
    # Timing
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    submitted_at = Column(DateTime(timezone=True))
    
    # Audit trail
    interaction_hash = Column(String(64))
    audit_metadata = Column(JSON, default={})
    
    # Relationship to collaboration session
    collaboration_session = relationship("A2ACollaborationSession", backref="agent_interactions")
    
    def __repr__(self):
        return f"<A2AAgentInteraction(agent_id='{self.agent_id}', specialty='{self.agent_specialty}', confidence={self.overall_confidence})>"

class A2AConsensusRecord(Base):
    """Model for consensus analysis results with detailed metrics."""
    
    __tablename__ = "a2a_consensus_records"
    
    # Primary identification  
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    consensus_id = Column(String(255), unique=True, nullable=False, index=True)
    collaboration_id = Column(String(255), ForeignKey('a2a_collaboration_sessions.collaboration_id'), nullable=False, index=True)
    
    # Consensus configuration
    consensus_type = Column(String(100), nullable=False)
    algorithm_version = Column(String(50), default="1.0")
    participating_agents = Column(JSON, nullable=False)
    total_participants = Column(Integer, nullable=False)
    
    # Consensus results
    consensus_reached = Column(Boolean, nullable=False, index=True)
    agreement_level = Column(Float, nullable=False, ge=0.0, le=1.0)
    consensus_threshold = Column(Float, default=0.7)
    consensus_strength = Column(String(50))  # weak, moderate, strong, unanimous
    
    # Final recommendations
    consensus_recommendation = Column(JSON)  # Final agreed-upon recommendation
    minority_opinions = Column(JSON, default=[])  # Dissenting views
    alternative_recommendations = Column(JSON, default=[])
    
    # Confidence metrics
    average_confidence = Column(Float, nullable=False, ge=0.0, le=1.0)
    confidence_standard_deviation = Column(Float, nullable=False)
    weighted_confidence = Column(Float, nullable=False, ge=0.0, le=1.0)
    min_confidence = Column(Float)
    max_confidence = Column(Float)
    
    # Quality indicators
    evidence_strength = Column(Float, default=0.0, ge=0.0, le=1.0)
    guideline_compliance = Column(Float, default=0.0, ge=0.0, le=1.0)
    risk_assessment = Column(String(50), default="low")
    safety_score = Column(Float, default=1.0, ge=0.0, le=1.0)
    
    # Consensus breakdown by domain
    diagnostic_consensus = Column(JSON, default={})  # Consensus scores for diagnoses
    treatment_consensus = Column(JSON, default={})  # Consensus scores for treatments
    specialty_weights = Column(JSON, default={})  # Weights applied to each specialty
    vote_distribution = Column(JSON, default={})  # How agents voted
    
    # Decision quality metrics
    inter_rater_reliability = Column(Float)  # Statistical measure of agreement
    fleiss_kappa = Column(Float)  # Multi-rater agreement statistic
    consensus_entropy = Column(Float)  # Measure of uncertainty/disagreement
    decision_confidence_interval = Column(JSON, default={})
    
    # Escalation and review
    requires_human_review = Column(Boolean, default=False, index=True)
    human_review_priority = Column(String(50), default="routine")
    escalation_triggered = Column(Boolean, default=False, index=True)
    escalation_reasons = Column(JSON, default=[])
    safety_concerns = Column(JSON, default=[])
    
    # Performance metrics
    processing_time_ms = Column(Float, nullable=False)
    iterations_required = Column(Integer, default=1)  # Number of consensus iterations
    convergence_time_ms = Column(Float)  # Time to reach consensus
    
    # Validation and review
    consensus_validated = Column(Boolean, default=False)
    validation_notes = Column(Text)
    peer_review_completed = Column(Boolean, default=False)
    quality_score = Column(Float, ge=0.0, le=1.0)
    
    # Compliance tracking
    all_participants_compliant = Column(Boolean, default=True)
    audit_trail_verified = Column(Boolean, default=True)
    phi_handling_verified = Column(Boolean, default=True)
    
    # Timing
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    consensus_reached_at = Column(DateTime(timezone=True))
    validated_at = Column(DateTime(timezone=True))
    
    # Audit and integrity
    consensus_hash = Column(String(64), nullable=False)
    digital_signature = Column(Text)  # For non-repudiation
    audit_metadata = Column(JSON, default={})
    
    # Relationship to collaboration session
    collaboration_session = relationship("A2ACollaborationSession", backref="consensus_records")
    
    def __repr__(self):
        return f"<A2AConsensusRecord(consensus_id='{self.consensus_id}', reached={self.consensus_reached}, agreement={self.agreement_level})>"

class A2AAgentProfile(Base):
    """Model for medical agent profiles and performance tracking."""
    
    __tablename__ = "a2a_agent_profiles"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    agent_id = Column(String(255), unique=True, nullable=False, index=True)
    agent_name = Column(String(255), nullable=False)
    
    # Specialty information
    primary_specialty = Column(String(100), nullable=False, index=True)
    sub_specialties = Column(JSON, default=[])
    specialty_certifications = Column(JSON, default=[])
    
    # Model information
    model_type = Column(String(100), nullable=False)
    model_version = Column(String(100), nullable=False)
    model_architecture = Column(String(100))
    training_date = Column(DateTime(timezone=True))
    last_update_date = Column(DateTime(timezone=True))
    
    # Performance metrics
    accuracy_score = Column(Float, default=0.0, ge=0.0, le=1.0)
    precision_score = Column(Float, default=0.0, ge=0.0, le=1.0)
    recall_score = Column(Float, default=0.0, ge=0.0, le=1.0)
    f1_score = Column(Float, default=0.0, ge=0.0, le=1.0)
    auc_score = Column(Float, default=0.0, ge=0.0, le=1.0)
    
    # Collaboration metrics  
    total_collaborations = Column(Integer, default=0)
    successful_collaborations = Column(Integer, default=0)
    consensus_alignment_rate = Column(Float, default=0.0, ge=0.0, le=1.0)
    average_peer_rating = Column(Float, default=0.0, ge=0.0, le=5.0)
    response_time_average_ms = Column(Float, default=0.0)
    
    # Quality metrics
    diagnostic_accuracy = Column(Float, default=0.0, ge=0.0, le=1.0)
    treatment_appropriateness = Column(Float, default=0.0, ge=0.0, le=1.0)
    guideline_adherence = Column(Float, default=0.0, ge=0.0, le=1.0)
    safety_score = Column(Float, default=1.0, ge=0.0, le=1.0)
    
    # Capabilities and features
    emergency_capable = Column(Boolean, default=False)
    research_capable = Column(Boolean, default=False)
    teaching_mode_enabled = Column(Boolean, default=False)
    multilingual_support = Column(JSON, default=["en"])
    supported_fhir_resources = Column(JSON, default=[])
    
    # Compliance and certification
    hipaa_compliant = Column(Boolean, default=True, nullable=False)
    soc2_compliant = Column(Boolean, default=True, nullable=False)
    certification_status = Column(String(50), default="active")
    last_compliance_check = Column(DateTime(timezone=True))
    compliance_expiry_date = Column(DateTime(timezone=True))
    
    # Activity tracking
    last_active_at = Column(DateTime(timezone=True))
    total_cases_handled = Column(Integer, default=0)
    total_processing_time_hours = Column(Float, default=0.0)
    
    # Reputation and feedback
    peer_endorsements = Column(Integer, default=0)
    patient_satisfaction_score = Column(Float, default=0.0, ge=0.0, le=5.0)
    clinical_accuracy_reviews = Column(JSON, default=[])
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    created_by = Column(String(255), default="a2a_system")
    
    # Audit fields
    profile_hash = Column(String(64))
    audit_metadata = Column(JSON, default={})
    
    def __repr__(self):
        return f"<A2AAgentProfile(agent_id='{self.agent_id}', specialty='{self.primary_specialty}', accuracy={self.accuracy_score})>"

# Create indexes for performance and compliance queries
Index('idx_collaboration_case_urgency', A2ACollaborationSession.case_id, A2ACollaborationSession.urgency_level, A2ACollaborationSession.created_at)
Index('idx_collaboration_status_time', A2ACollaborationSession.status, A2ACollaborationSession.created_at)
Index('idx_collaboration_patient_consent', A2ACollaborationSession.patient_id_hash, A2ACollaborationSession.consent_obtained)
Index('idx_interaction_agent_time', A2AAgentInteraction.agent_id, A2AAgentInteraction.created_at)
Index('idx_interaction_specialty_confidence', A2AAgentInteraction.agent_specialty, A2AAgentInteraction.overall_confidence)
Index('idx_consensus_reached_time', A2AConsensusRecord.consensus_reached, A2AConsensusRecord.created_at)
Index('idx_consensus_review_required', A2AConsensusRecord.requires_human_review, A2AConsensusRecord.escalation_triggered)
Index('idx_agent_specialty_performance', A2AAgentProfile.primary_specialty, A2AAgentProfile.accuracy_score)
Index('idx_agent_compliance_status', A2AAgentProfile.certification_status, A2AAgentProfile.last_compliance_check)

# Add table comments for documentation
A2ACollaborationSession.__table__.comment = "Agent collaboration sessions with full medical case context and audit trail"
A2AAgentInteraction.__table__.comment = "Individual agent interactions and recommendations within collaboration sessions"
A2AConsensusRecord.__table__.comment = "Consensus analysis results with detailed quality metrics and validation"
A2AAgentProfile.__table__.comment = "Medical agent profiles with performance tracking and compliance status"