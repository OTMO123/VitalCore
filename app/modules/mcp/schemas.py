"""
MCP Protocol Schemas for Healthcare Platform V2.0

Pydantic models for Model Context Protocol with healthcare compliance features.
All schemas include built-in PHI protection, audit trails, and FHIR compatibility.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum
import uuid

class MCPMessageType(str, Enum):
    """Types of MCP messages for agent communication."""
    REGISTRATION = "registration"
    CONSULTATION_REQUEST = "consultation_request"
    CONSULTATION_RESPONSE = "consultation_response"
    AGENT_QUERY = "agent_query"
    AGENT_RESPONSE = "agent_response"
    COLLABORATION_INVITE = "collaboration_invite"
    COLLABORATION_ACCEPT = "collaboration_accept"
    EMERGENCY_ALERT = "emergency_alert"
    STATUS_UPDATE = "status_update"
    HEARTBEAT = "heartbeat"
    ERROR_NOTIFICATION = "error_notification"

class AgentStatus(str, Enum):
    """Status of an MCP agent."""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"
    MAINTENANCE = "maintenance"

class SecurityLevel(str, Enum):
    """Security levels for MCP communications."""
    PUBLIC = "public"           # No PHI, publicly shareable
    INTERNAL = "internal"       # Internal system use only
    PHI_RESTRICTED = "phi_restricted"  # Contains PHI, restricted access
    PHI_ENCRYPTED = "phi_encrypted"    # PHI encrypted, highest security

class MedicalUrgency(str, Enum):
    """Medical urgency levels for prioritizing agent communications."""
    ROUTINE = "routine"
    URGENT = "urgent"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class AgentCapabilities(BaseModel):
    """Capabilities and metadata for an MCP agent."""
    
    # Agent identification
    medical_specialties: List[str] = Field(..., description="Medical specialties this agent handles")
    supported_languages: List[str] = Field(default=["en"], description="Supported languages")
    model_type: str = Field(..., description="Type of AI model (gemma, llama, whisper, etc.)")
    model_version: str = Field(..., description="Version of the AI model")
    
    # Processing capabilities
    max_concurrent_consultations: int = Field(default=5, description="Maximum concurrent consultations")
    average_response_time_ms: int = Field(default=2000, description="Average response time")
    supports_phi_processing: bool = Field(default=False, description="Can process PHI data")
    supports_emergency_cases: bool = Field(default=True, description="Can handle emergency cases")
    
    # FHIR compliance
    supported_fhir_resources: List[str] = Field(default=[], description="Supported FHIR R4 resources")
    fhir_version: str = Field(default="R4", description="FHIR version compatibility")
    
    # Security and compliance
    security_clearance: SecurityLevel = Field(default=SecurityLevel.INTERNAL, description="Security clearance level")
    hipaa_compliant: bool = Field(default=True, description="HIPAA compliance certified")
    soc2_compliant: bool = Field(default=True, description="SOC2 Type II compliant")
    
    # Performance metrics
    accuracy_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Historical accuracy score")
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum confidence for responses")
    
    @validator('medical_specialties')
    def validate_specialties(cls, v):
        valid_specialties = [
            'cardiology', 'neurology', 'emergency_medicine', 'internal_medicine',
            'pulmonology', 'endocrinology', 'psychiatry', 'dermatology', 
            'radiology', 'pathology', 'general_practice'
        ]
        for specialty in v:
            if specialty not in valid_specialties:
                raise ValueError(f'Invalid medical specialty: {specialty}')
        return v

class MCPAgentInfo(BaseModel):
    """Information about an MCP agent."""
    
    agent_id: str = Field(..., description="Unique agent identifier")
    agent_name: str = Field(..., description="Human-readable agent name")
    status: AgentStatus = Field(..., description="Current agent status")
    capabilities: AgentCapabilities = Field(..., description="Agent capabilities")
    
    # Connection info
    endpoint_url: Optional[str] = Field(default=None, description="Agent endpoint URL")
    public_key: Optional[str] = Field(default=None, description="Public key for encryption")
    last_heartbeat: Optional[datetime] = Field(default=None, description="Last heartbeat timestamp")
    
    # Performance tracking
    total_consultations: int = Field(default=0, description="Total consultations handled")
    average_rating: float = Field(default=0.0, ge=0.0, le=5.0, description="Average user rating")
    uptime_percentage: float = Field(default=100.0, ge=0.0, le=100.0, description="Uptime percentage")
    
    # Compliance tracking
    last_compliance_check: Optional[datetime] = Field(default=None, description="Last compliance verification")
    compliance_status: str = Field(default="verified", description="Current compliance status")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Agent registration timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

class MCPMessage(BaseModel):
    """Base MCP message structure with healthcare compliance features."""
    
    # Message identification
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique message ID")
    message_type: MCPMessageType = Field(..., description="Type of MCP message")
    
    # Routing information
    from_agent: str = Field(..., description="Sending agent ID")
    to_agent: Optional[str] = Field(default=None, description="Receiving agent ID (None for broadcast)")
    
    # Message content
    payload: Dict[str, Any] = Field(..., description="Message payload data")
    encrypted_payload: Optional[str] = Field(default=None, description="Encrypted payload for PHI data")
    
    # Security and compliance
    security_level: SecurityLevel = Field(default=SecurityLevel.INTERNAL, description="Security classification")
    contains_phi: bool = Field(default=False, description="Whether message contains PHI")
    requires_audit: bool = Field(default=True, description="Whether to audit this message")
    
    # Medical context
    urgency_level: MedicalUrgency = Field(default=MedicalUrgency.ROUTINE, description="Medical urgency")
    patient_id: Optional[str] = Field(default=None, description="Associated patient ID (if applicable)")
    case_id: Optional[str] = Field(default=None, description="Medical case ID")
    
    # Timing and tracking
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    expires_at: Optional[datetime] = Field(default=None, description="Message expiration time")
    correlation_id: Optional[str] = Field(default=None, description="Correlation ID for request/response matching")
    
    # FHIR compatibility
    fhir_context: Optional[Dict[str, Any]] = Field(default=None, description="FHIR context information")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('payload')
    def validate_payload_size(cls, v):
        """Ensure payload size is within limits."""
        payload_str = str(v)
        if len(payload_str) > 1024 * 1024:  # 1MB limit
            raise ValueError('Message payload too large (max 1MB)')
        return v

class MCPResponse(BaseModel):
    """Response message in MCP protocol."""
    
    # Response identification
    response_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique response ID")
    request_message_id: str = Field(..., description="ID of the original request message")
    
    # Response metadata
    from_agent: str = Field(..., description="Responding agent ID")
    to_agent: str = Field(..., description="Original requesting agent ID")
    status: str = Field(..., description="Response status (success, error, partial)")
    
    # Response content
    response_data: Dict[str, Any] = Field(..., description="Response payload")
    encrypted_response: Optional[str] = Field(default=None, description="Encrypted response for PHI")
    
    # Processing information
    processing_time_ms: float = Field(..., description="Time taken to process request")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence in response")
    
    # Error handling
    error_code: Optional[str] = Field(default=None, description="Error code if status is error")
    error_message: Optional[str] = Field(default=None, description="Human-readable error message")
    
    # Compliance
    contains_phi: bool = Field(default=False, description="Whether response contains PHI")
    audit_logged: bool = Field(default=False, description="Whether response was audited")
    
    # Timing
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")

class ConsultationRequest(BaseModel):
    """Medical consultation request via MCP."""
    
    consultation_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique consultation ID")
    requesting_agent: str = Field(..., description="Agent requesting consultation")
    
    # Medical case information  
    case_summary: str = Field(..., description="Summary of the medical case")
    symptoms: List[str] = Field(default=[], description="List of symptoms")
    vital_signs: Dict[str, float] = Field(default={}, description="Vital signs data")
    medical_history: List[str] = Field(default=[], description="Relevant medical history")
    current_medications: List[str] = Field(default=[], description="Current medications")
    
    # Consultation parameters
    requested_specialties: List[str] = Field(default=[], description="Requested medical specialties")
    urgency_level: MedicalUrgency = Field(default=MedicalUrgency.ROUTINE, description="Case urgency")
    max_response_time_seconds: int = Field(default=300, description="Maximum acceptable response time")
    
    # Patient context (anonymized)
    patient_age: Optional[int] = Field(default=None, description="Patient age")
    patient_gender: Optional[str] = Field(default=None, description="Patient gender")
    patient_id_hash: Optional[str] = Field(default=None, description="Hashed patient ID for tracking")
    
    # FHIR data
    fhir_resources: List[Dict[str, Any]] = Field(default=[], description="Relevant FHIR resources")
    
    # Compliance and security
    anonymized: bool = Field(default=True, description="Whether case data is anonymized")
    consent_obtained: bool = Field(default=False, description="Whether patient consent was obtained")
    phi_access_reason: str = Field(default="treatment", description="Reason for PHI access")
    
    @validator('requested_specialties')
    def validate_specialties(cls, v):
        if len(v) > 10:
            raise ValueError('Too many specialties requested (max 10)')
        return v

class ConsultationResponse(BaseModel):
    """Response to a medical consultation request."""
    
    response_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique response ID")
    consultation_id: str = Field(..., description="Original consultation ID")
    responding_agent: str = Field(..., description="Agent providing the response")
    
    # Medical assessment
    assessment: str = Field(..., description="Medical assessment and findings")
    diagnosis_suggestions: List[str] = Field(default=[], description="Suggested diagnoses")
    recommended_tests: List[str] = Field(default=[], description="Recommended diagnostic tests")
    treatment_recommendations: List[str] = Field(default=[], description="Treatment recommendations")
    
    # Clinical decision support
    differential_diagnosis: List[Dict[str, Any]] = Field(default=[], description="Differential diagnosis with probabilities")
    risk_factors: List[str] = Field(default=[], description="Identified risk factors")
    contraindications: List[str] = Field(default=[], description="Treatment contraindications")
    
    # Confidence and validation
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in assessment")
    evidence_level: str = Field(default="low", description="Level of supporting evidence")
    requires_human_review: bool = Field(default=False, description="Whether human review is needed")
    
    # Follow-up and monitoring
    follow_up_recommendations: List[str] = Field(default=[], description="Follow-up recommendations")
    monitoring_parameters: List[str] = Field(default=[], description="Parameters to monitor")
    escalation_criteria: List[str] = Field(default=[], description="When to escalate care")
    
    # Collaboration
    suggests_collaboration: bool = Field(default=False, description="Whether collaboration with other agents is suggested")
    suggested_specialists: List[str] = Field(default=[], description="Suggested specialist consultations")
    
    # Metadata
    processing_time_ms: float = Field(..., description="Time taken to process consultation")
    knowledge_sources: List[str] = Field(default=[], description="Knowledge sources used")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    # Compliance
    audit_trail_id: Optional[str] = Field(default=None, description="Associated audit trail ID")
    phi_accessed: bool = Field(default=False, description="Whether PHI was accessed")

class AgentCollaborationInvite(BaseModel):
    """Invitation for agents to collaborate on a medical case."""
    
    invite_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique invite ID")
    from_agent: str = Field(..., description="Agent sending the invite")
    to_agents: List[str] = Field(..., description="Agents being invited to collaborate")
    
    # Collaboration context
    case_id: str = Field(..., description="Medical case requiring collaboration")
    collaboration_type: str = Field(..., description="Type of collaboration needed")
    urgency_level: MedicalUrgency = Field(default=MedicalUrgency.ROUTINE, description="Case urgency")
    
    # Case information
    case_summary: str = Field(..., description="Brief case summary")
    specific_questions: List[str] = Field(default=[], description="Specific questions for collaborators")
    shared_context: Dict[str, Any] = Field(default={}, description="Shared case context")
    
    # Constraints
    response_deadline: Optional[datetime] = Field(default=None, description="Response deadline")
    max_collaborators: int = Field(default=5, description="Maximum number of collaborators")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Invite creation time")

class EmergencyAlert(BaseModel):
    """Emergency alert for critical medical situations."""
    
    alert_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique alert ID")
    alerting_agent: str = Field(..., description="Agent raising the alert")
    
    # Emergency details
    emergency_type: str = Field(..., description="Type of emergency detected")
    severity_level: str = Field(..., description="Severity level (critical, life-threatening)")
    time_sensitive: bool = Field(default=True, description="Whether this is time-sensitive")
    
    # Patient information (anonymized)
    patient_summary: Dict[str, Any] = Field(..., description="Anonymized patient summary")
    vital_signs: Dict[str, float] = Field(default={}, description="Current vital signs")
    presenting_symptoms: List[str] = Field(default=[], description="Presenting symptoms")
    
    # Clinical context
    suspected_conditions: List[str] = Field(default=[], description="Suspected emergency conditions")
    recommended_interventions: List[str] = Field(default=[], description="Immediate interventions needed")
    contraindications: List[str] = Field(default=[], description="Known contraindications")
    
    # Urgency and routing
    requires_immediate_response: bool = Field(default=True, description="Requires immediate response")
    escalate_to_human: bool = Field(default=True, description="Should escalate to human clinician")
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Alert timestamp")
    expires_at: Optional[datetime] = Field(default=None, description="Alert expiration time")

class MCPAuditLog(BaseModel):
    """Audit log entry for MCP communications."""
    
    log_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique log ID")
    
    # Message identification
    message_id: str = Field(..., description="MCP message ID")
    message_type: MCPMessageType = Field(..., description="Type of message")
    
    # Routing information
    from_agent: str = Field(..., description="Sending agent")
    to_agent: Optional[str] = Field(default=None, description="Receiving agent")
    
    # Security and compliance
    security_level: SecurityLevel = Field(..., description="Security classification")
    contains_phi: bool = Field(..., description="Whether message contained PHI")
    phi_access_reason: Optional[str] = Field(default=None, description="Reason for PHI access")
    
    # Processing information
    processing_time_ms: Optional[float] = Field(default=None, description="Processing time")
    status: str = Field(..., description="Processing status")
    error_details: Optional[str] = Field(default=None, description="Error details if failed")
    
    # Compliance tracking
    hipaa_logged: bool = Field(default=True, description="Whether logged for HIPAA compliance")
    soc2_category: str = Field(default="agent_communication", description="SOC2 audit category")
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Log timestamp")
    audit_hash: Optional[str] = Field(default=None, description="Cryptographic hash for integrity")