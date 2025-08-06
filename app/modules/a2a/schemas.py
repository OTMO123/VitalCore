"""
A2A Schemas for Healthcare Platform V2.0

Pydantic models for Agent-to-Agent communication with healthcare compliance.
All schemas include built-in PHI protection, audit trails, and medical validation.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum
import uuid

class MedicalSpecialty(str, Enum):
    """Medical specialties for agent classification."""
    CARDIOLOGY = "cardiology"
    NEUROLOGY = "neurology"
    EMERGENCY_MEDICINE = "emergency_medicine"
    INTERNAL_MEDICINE = "internal_medicine"
    PULMONOLOGY = "pulmonology"
    ENDOCRINOLOGY = "endocrinology"
    PSYCHIATRY = "psychiatry"
    DERMATOLOGY = "dermatology"
    RADIOLOGY = "radiology"
    PATHOLOGY = "pathology"
    GENERAL_PRACTICE = "general_practice"
    ONCOLOGY = "oncology"
    PEDIATRICS = "pediatrics"
    OBSTETRICS_GYNECOLOGY = "obstetrics_gynecology"
    ORTHOPEDICS = "orthopedics"
    ANESTHESIOLOGY = "anesthesiology"
    INFECTIOUS_DISEASE = "infectious_disease"
    RHEUMATOLOGY = "rheumatology"
    GASTROENTEROLOGY = "gastroenterology"
    NEPHROLOGY = "nephrology"

class ConsensusType(str, Enum):
    """Types of consensus mechanisms for agent collaboration."""
    SIMPLE_MAJORITY = "simple_majority"
    WEIGHTED_EXPERTISE = "weighted_expertise"  # Weighted by agent accuracy scores
    UNANIMOUS = "unanimous"
    BAYESIAN_ENSEMBLE = "bayesian_ensemble"
    CONFIDENCE_WEIGHTED = "confidence_weighted"
    SPECIALIST_PRIORITY = "specialist_priority"  # Specialist takes priority in their domain

class CollaborationStatus(str, Enum):
    """Status of agent collaboration sessions."""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    WAITING_FOR_RESPONSES = "waiting_for_responses"
    ANALYZING_CONSENSUS = "analyzing_consensus"
    COMPLETED = "completed"
    ESCALATED = "escalated"
    FAILED = "failed"
    TIMED_OUT = "timed_out"

class ClinicalEvidence(BaseModel):
    """Clinical evidence and supporting data for medical decisions."""
    
    evidence_type: str = Field(..., description="Type of evidence (lab, imaging, clinical)")
    source: str = Field(..., description="Source of evidence")
    finding: str = Field(..., description="Specific finding or result")
    significance: str = Field(..., description="Clinical significance")
    confidence_level: float = Field(..., ge=0.0, le=1.0, description="Confidence in evidence")
    date_obtained: Optional[datetime] = Field(default=None, description="Date evidence was obtained")
    
class DifferentialDiagnosis(BaseModel):
    """Differential diagnosis with probability and supporting evidence."""
    
    condition: str = Field(..., description="Medical condition")
    icd_10_code: Optional[str] = Field(default=None, description="ICD-10 diagnosis code")
    probability: float = Field(..., ge=0.0, le=1.0, description="Probability of condition")
    supporting_evidence: List[ClinicalEvidence] = Field(default=[], description="Supporting clinical evidence")
    ruling_out_factors: List[str] = Field(default=[], description="Factors that argue against this diagnosis")
    specialist_opinion: Optional[str] = Field(default=None, description="Specialist's specific opinion")

class TreatmentRecommendation(BaseModel):
    """Treatment recommendation with clinical rationale."""
    
    intervention: str = Field(..., description="Recommended intervention")
    priority: str = Field(..., description="Priority level (immediate, urgent, routine)")
    rationale: str = Field(..., description="Clinical rationale for recommendation")
    contraindications: List[str] = Field(default=[], description="Known contraindications")
    monitoring_requirements: List[str] = Field(default=[], description="Required monitoring")
    expected_outcome: Optional[str] = Field(default=None, description="Expected clinical outcome")
    alternatives: List[str] = Field(default=[], description="Alternative treatment options")

class AgentRecommendation(BaseModel):
    """Individual agent's medical recommendation."""
    
    agent_id: str = Field(..., description="Recommending agent identifier")
    specialty: MedicalSpecialty = Field(..., description="Agent's medical specialty")
    
    # Clinical assessment
    primary_assessment: str = Field(..., description="Primary clinical assessment")
    differential_diagnoses: List[DifferentialDiagnosis] = Field(default=[], description="Differential diagnoses")
    treatment_recommendations: List[TreatmentRecommendation] = Field(default=[], description="Treatment recommendations")
    
    # Confidence and validation
    overall_confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence in assessment")
    specialist_confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in specialty-specific aspects")
    requires_further_evaluation: bool = Field(default=False, description="Whether further evaluation is needed")
    
    # Follow-up and monitoring
    follow_up_timeline: Optional[str] = Field(default=None, description="Recommended follow-up timeline")
    warning_signs: List[str] = Field(default=[], description="Warning signs to monitor")
    escalation_criteria: List[str] = Field(default=[], description="Criteria for escalating care")
    
    # Collaboration
    requests_consultation: bool = Field(default=False, description="Whether requesting additional consultation")
    requested_specialties: List[MedicalSpecialty] = Field(default=[], description="Additional specialties requested")
    
    # Metadata
    processing_time_ms: float = Field(..., description="Time taken to generate recommendation")
    knowledge_sources: List[str] = Field(default=[], description="Knowledge sources consulted")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Recommendation timestamp")
    
    @validator('differential_diagnoses')
    def validate_probabilities_sum(cls, v):
        """Ensure differential diagnosis probabilities don't exceed 100%."""
        total_prob = sum(dx.probability for dx in v)
        if total_prob > 1.0:
            # Normalize probabilities
            for dx in v:
                dx.probability = dx.probability / total_prob
        return v

class CollaborationRequest(BaseModel):
    """Request for agent-to-agent collaboration on a medical case."""
    
    # Request identification
    collaboration_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique collaboration ID")
    requesting_agent: str = Field(..., description="Agent initiating collaboration")
    case_id: str = Field(..., description="Medical case identifier")
    
    # Medical case data (anonymized)
    case_summary: str = Field(..., description="Anonymized case summary")
    patient_age: Optional[int] = Field(default=None, ge=0, le=150, description="Patient age")
    patient_gender: Optional[str] = Field(default=None, description="Patient gender")
    patient_id_hash: str = Field(..., description="Hashed patient identifier")
    
    # Clinical data
    chief_complaint: str = Field(..., description="Primary complaint or concern")
    symptoms: List[str] = Field(default=[], description="List of symptoms")
    vital_signs: Dict[str, float] = Field(default={}, description="Current vital signs")
    lab_results: Dict[str, Any] = Field(default={}, description="Laboratory results")
    imaging_results: List[Dict[str, Any]] = Field(default=[], description="Imaging study results")
    medical_history: List[str] = Field(default=[], description="Relevant medical history")
    current_medications: List[str] = Field(default=[], description="Current medications")
    allergies: List[str] = Field(default=[], description="Known allergies")
    
    # Collaboration parameters
    requested_specialties: List[MedicalSpecialty] = Field(default=[], description="Specific specialties requested")
    collaboration_type: str = Field(default="consultation", description="Type of collaboration needed")
    urgency_level: str = Field(default="routine", description="Urgency level")
    max_response_time_minutes: int = Field(default=30, description="Maximum response time allowed")
    consensus_mechanism: ConsensusType = Field(default=ConsensusType.WEIGHTED_EXPERTISE, description="Consensus mechanism")
    
    # Specific questions
    clinical_questions: List[str] = Field(default=[], description="Specific clinical questions")
    diagnostic_uncertainty: List[str] = Field(default=[], description="Areas of diagnostic uncertainty")
    treatment_dilemmas: List[str] = Field(default=[], description="Treatment decision dilemmas")
    
    # FHIR compatibility
    fhir_resources: List[Dict[str, Any]] = Field(default=[], description="Associated FHIR resources")
    
    # Compliance and security
    anonymized: bool = Field(default=True, description="Whether case data is anonymized")
    consent_obtained: bool = Field(default=False, description="Whether patient consent was obtained")
    phi_access_reason: str = Field(default="treatment", description="Reason for PHI access")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Request creation time")
    expires_at: Optional[datetime] = Field(default=None, description="Request expiration time")
    
    @validator('requested_specialties')
    def validate_max_specialties(cls, v):
        """Limit number of requested specialties."""
        if len(v) > 8:
            raise ValueError('Too many specialties requested (max 8)')
        return v

class CollaborationResponse(BaseModel):
    """Response from an agent in a collaboration session."""
    
    # Response identification
    response_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique response ID")
    collaboration_id: str = Field(..., description="Associated collaboration ID")
    responding_agent: str = Field(..., description="Agent providing response")
    
    # Agent recommendation
    recommendation: AgentRecommendation = Field(..., description="Agent's medical recommendation")
    
    # Collaboration feedback
    agrees_with_others: List[str] = Field(default=[], description="Agent IDs this agent agrees with")
    disagrees_with_others: List[str] = Field(default=[], description="Agent IDs this agent disagrees with")
    collaboration_notes: Optional[str] = Field(default=None, description="Additional collaboration notes")
    
    # Quality assurance
    peer_review_requested: bool = Field(default=False, description="Whether peer review is requested")
    human_oversight_recommended: bool = Field(default=False, description="Whether human oversight is recommended")
    
    # Metadata
    processing_time_ms: float = Field(..., description="Time taken to process collaboration")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")

class AgentCollaboration(BaseModel):
    """Complete agent collaboration session with all responses."""
    
    # Session identification
    collaboration_id: str = Field(..., description="Collaboration session ID")
    case_id: str = Field(..., description="Associated medical case ID")
    status: CollaborationStatus = Field(..., description="Current collaboration status")
    
    # Participants
    requesting_agent: str = Field(..., description="Agent that initiated collaboration")
    participating_agents: List[str] = Field(default=[], description="All participating agents")
    
    # Collaboration data
    request: CollaborationRequest = Field(..., description="Original collaboration request")
    responses: List[CollaborationResponse] = Field(default=[], description="Agent responses")
    
    # Consensus and outcomes
    consensus_reached: bool = Field(default=False, description="Whether consensus was reached")
    consensus_mechanism: ConsensusType = Field(..., description="Consensus mechanism used")
    final_recommendation: Optional[AgentRecommendation] = Field(default=None, description="Final consensus recommendation")
    
    # Quality metrics
    agreement_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Inter-agent agreement score")
    confidence_variance: float = Field(default=0.0, description="Variance in confidence scores")
    response_time_ms: float = Field(default=0.0, description="Total collaboration time")
    
    # Escalation and follow-up
    human_review_required: bool = Field(default=False, description="Whether human review is required")
    escalation_reason: Optional[str] = Field(default=None, description="Reason for escalation if applicable")
    follow_up_actions: List[str] = Field(default=[], description="Required follow-up actions")
    
    # Compliance tracking
    all_agents_hipaa_compliant: bool = Field(default=True, description="Whether all agents are HIPAA compliant")
    audit_trail_complete: bool = Field(default=True, description="Whether audit trail is complete")
    phi_handling_compliant: bool = Field(default=True, description="Whether PHI handling was compliant")
    
    # Timing and lifecycle
    started_at: datetime = Field(default_factory=datetime.utcnow, description="Collaboration start time")
    completed_at: Optional[datetime] = Field(default=None, description="Collaboration completion time")
    
    # Audit and integrity
    session_hash: Optional[str] = Field(default=None, description="Cryptographic hash of session data")

class ConsensusResult(BaseModel):
    """Result of consensus analysis among collaborating agents."""
    
    # Consensus identification
    consensus_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique consensus ID")
    collaboration_id: str = Field(..., description="Associated collaboration ID")
    consensus_type: ConsensusType = Field(..., description="Type of consensus mechanism used")
    
    # Consensus analysis
    consensus_reached: bool = Field(..., description="Whether consensus was achieved")
    agreement_level: float = Field(..., ge=0.0, le=1.0, description="Level of agreement (0-1)")
    participating_agents: List[str] = Field(..., description="Agents that participated in consensus")
    
    # Final recommendation
    consensus_recommendation: Optional[AgentRecommendation] = Field(default=None, description="Final consensus recommendation")
    minority_opinions: List[AgentRecommendation] = Field(default=[], description="Dissenting opinions")
    
    # Confidence metrics
    average_confidence: float = Field(..., ge=0.0, le=1.0, description="Average confidence across agents")
    confidence_standard_deviation: float = Field(..., description="Standard deviation of confidence scores")
    weighted_confidence: float = Field(..., ge=0.0, le=1.0, description="Expertise-weighted confidence")
    
    # Decision quality indicators
    evidence_strength: float = Field(default=0.0, ge=0.0, le=1.0, description="Strength of supporting evidence")
    guideline_compliance: float = Field(default=0.0, ge=0.0, le=1.0, description="Compliance with clinical guidelines")
    risk_assessment: str = Field(default="low", description="Risk level of recommendation")
    
    # Consensus breakdown
    diagnostic_consensus: Dict[str, float] = Field(default={}, description="Consensus on diagnoses")
    treatment_consensus: Dict[str, float] = Field(default={}, description="Consensus on treatments")
    specialty_weights: Dict[str, float] = Field(default={}, description="Specialty expertise weights applied")
    
    # Quality assurance
    requires_human_review: bool = Field(default=False, description="Whether human review is required")
    escalation_triggered: bool = Field(default=False, description="Whether escalation was triggered")
    safety_concerns: List[str] = Field(default=[], description="Identified safety concerns")
    
    # Metadata
    processing_time_ms: float = Field(..., description="Time taken for consensus analysis")
    algorithm_version: str = Field(default="1.0", description="Version of consensus algorithm used")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Consensus timestamp")

class MedicalAgentProfile(BaseModel):
    """Profile and capabilities of a medical specialty agent."""
    
    # Agent identification
    agent_id: str = Field(..., description="Unique agent identifier")
    agent_name: str = Field(..., description="Agent display name")
    specialty: MedicalSpecialty = Field(..., description="Primary medical specialty")
    sub_specialties: List[str] = Field(default=[], description="Sub-specializations")
    
    # Model information
    model_type: str = Field(..., description="Type of AI model")
    model_version: str = Field(..., description="Model version")
    training_date: Optional[datetime] = Field(default=None, description="Model training date")
    
    # Performance metrics
    accuracy_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Historical accuracy")
    precision_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Precision metric")
    recall_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Recall metric")
    f1_score: float = Field(default=0.0, ge=0.0, le=1.0, description="F1 score")
    
    # Collaboration metrics
    collaboration_count: int = Field(default=0, description="Number of collaborations participated in")
    consensus_alignment: float = Field(default=0.0, ge=0.0, le=1.0, description="How often agent aligns with consensus")
    peer_rating: float = Field(default=0.0, ge=0.0, le=5.0, description="Rating from peer agents")
    
    # Capabilities
    emergency_capable: bool = Field(default=False, description="Can handle emergency cases")
    research_capable: bool = Field(default=False, description="Can access research databases")
    teaching_mode: bool = Field(default=False, description="Can explain reasoning for education")
    
    # Compliance
    last_compliance_check: Optional[datetime] = Field(default=None, description="Last compliance verification")
    certification_status: str = Field(default="active", description="Certification status")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Profile creation time")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last profile update")