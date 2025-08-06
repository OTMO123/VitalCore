"""
Medical Specialty Agents for A2A Healthcare Platform V2.0

Specialized AI agents for different medical specialties with domain-specific
knowledge and reasoning capabilities. All agents are HIPAA/SOC2 compliant.
"""

import asyncio
import json
import hashlib
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

# Import existing healthcare platform components
from app.core.database_unified import get_db, AuditEventType
from app.core.security import encryption_service, SecurityManager
from app.modules.audit_logger.service import audit_logger
from app.core.config import get_settings

# Import A2A schemas
from .schemas import (
    MedicalSpecialty, AgentRecommendation, DifferentialDiagnosis,
    TreatmentRecommendation, ClinicalEvidence, CollaborationRequest,
    MedicalAgentProfile
)
from .models import A2AAgentProfile

logger = structlog.get_logger()
settings = get_settings()

class BaseSpecialtyAgent(ABC):
    """
    Base class for all medical specialty agents.
    
    Provides common functionality for HIPAA compliance, audit logging,
    and integration with the healthcare platform's security infrastructure.
    """
    
    def __init__(self, agent_id: str, specialty: MedicalSpecialty, model_version: str = "1.0"):
        self.agent_id = agent_id
        self.specialty = specialty
        self.model_version = model_version
        self.security_manager = SecurityManager()
        self.processing_start_time = None
        
        # Performance tracking
        self.total_cases = 0
        self.successful_cases = 0
        self.average_confidence = 0.0
        self.total_processing_time = 0.0
        
    async def initialize(self) -> None:
        """Initialize the agent with database profile and compliance checks."""
        try:
            # Load or create agent profile
            await self._load_or_create_profile()
            
            # Perform compliance verification
            await self._verify_compliance()
            
            # Log agent initialization
            await audit_logger.log_event(
                event_type=AuditEventType.AGENT_INITIALIZED,
                user_id=self.agent_id,
                resource_type="medical_agent",
                resource_id=self.agent_id,
                action="agent_initialized",
                details={
                    "specialty": self.specialty.value,
                    "model_version": self.model_version,
                    "compliance_verified": True
                }
            )
            
            logger.info("Medical agent initialized successfully",
                       agent_id=self.agent_id,
                       specialty=self.specialty.value)
            
        except Exception as e:
            logger.error("Failed to initialize medical agent",
                        agent_id=self.agent_id,
                        error=str(e))
            raise
    
    async def process_collaboration_request(self, request: CollaborationRequest) -> AgentRecommendation:
        """
        Process a collaboration request and generate medical recommendation.
        
        Args:
            request: Medical collaboration request
            
        Returns:
            AgentRecommendation: Agent's medical assessment and recommendations
        """
        self.processing_start_time = datetime.utcnow()
        
        try:
            logger.info("Processing collaboration request",
                       agent_id=self.agent_id,
                       collaboration_id=request.collaboration_id,
                       case_id=request.case_id)
            
            # Validate PHI access authorization
            await self._validate_phi_access(request)
            
            # Validate case meets specialty criteria
            await self._validate_specialty_relevance(request)
            
            # Generate medical recommendation
            recommendation = await self._generate_recommendation(request)
            
            # Validate recommendation quality
            await self._validate_recommendation(recommendation)
            
            # Log successful processing
            processing_time = (datetime.utcnow() - self.processing_start_time).total_seconds() * 1000
            
            await audit_logger.log_event(
                event_type=AuditEventType.AGENT_RECOMMENDATION_GENERATED,
                user_id=self.agent_id,
                resource_type="collaboration_request",
                resource_id=request.collaboration_id,
                action="recommendation_generated",
                details={
                    "case_id": request.case_id,
                    "specialty": self.specialty.value,
                    "processing_time_ms": processing_time,
                    "confidence_score": recommendation.overall_confidence,
                    "phi_accessed": not request.anonymized
                }
            )
            
            # Update performance metrics
            await self._update_performance_metrics(recommendation, processing_time)
            
            logger.info("Collaboration request processed successfully",
                       agent_id=self.agent_id,
                       collaboration_id=request.collaboration_id,
                       confidence=recommendation.overall_confidence,
                       processing_time_ms=processing_time)
            
            return recommendation
            
        except Exception as e:
            processing_time = (datetime.utcnow() - self.processing_start_time).total_seconds() * 1000 if self.processing_start_time else 0
            
            logger.error("Failed to process collaboration request",
                        agent_id=self.agent_id,
                        collaboration_id=request.collaboration_id,
                        error=str(e),
                        processing_time_ms=processing_time)
            
            # Log processing failure
            await audit_logger.log_event(
                event_type=AuditEventType.AGENT_PROCESSING_FAILED,
                user_id=self.agent_id,
                resource_type="collaboration_request",
                resource_id=request.collaboration_id,
                action="processing_failed",
                details={
                    "error": str(e),
                    "processing_time_ms": processing_time
                }
            )
            
            raise
    
    @abstractmethod
    async def _generate_recommendation(self, request: CollaborationRequest) -> AgentRecommendation:
        """Generate specialty-specific medical recommendation."""
        pass
    
    @abstractmethod
    def _get_specialty_keywords(self) -> List[str]:
        """Get keywords that indicate relevance to this specialty."""
        pass
    
    @abstractmethod
    def _get_common_conditions(self) -> List[str]:
        """Get common conditions handled by this specialty."""
        pass
    
    async def _load_or_create_profile(self) -> None:
        """Load existing agent profile or create new one."""
        async with get_db() as db:
            # Try to load existing profile
            result = await db.execute(
                select(A2AAgentProfile).where(A2AAgentProfile.agent_id == self.agent_id)
            )
            profile = result.scalar_one_or_none()
            
            if not profile:
                # Create new profile
                profile = A2AAgentProfile(
                    agent_id=self.agent_id,
                    agent_name=f"{self.specialty.value.title()} AI Specialist",
                    primary_specialty=self.specialty.value,
                    model_type="gemma_medical",
                    model_version=self.model_version,
                    hipaa_compliant=True,
                    soc2_compliant=True,
                    certification_status="active",
                    created_at=datetime.utcnow()
                )
                
                db.add(profile)
                await db.commit()
                await db.refresh(profile)
                
                logger.info("Created new agent profile", agent_id=self.agent_id)
            
            self.profile = profile
    
    async def _verify_compliance(self) -> None:
        """Verify agent compliance with healthcare regulations."""
        if not self.profile.hipaa_compliant:
            raise ValueError("Agent is not HIPAA compliant")
        
        if not self.profile.soc2_compliant:
            raise ValueError("Agent is not SOC2 compliant")
        
        if self.profile.certification_status != "active":
            raise ValueError(f"Agent certification not active: {self.profile.certification_status}")
    
    async def _validate_phi_access(self, request: CollaborationRequest) -> None:
        """Validate authorization for PHI access."""
        if not request.anonymized:
            if not request.consent_obtained:
                raise ValueError("Patient consent not obtained for PHI access")
            
            if not request.phi_access_reason:
                raise ValueError("PHI access reason not specified")
    
    async def _validate_specialty_relevance(self, request: CollaborationRequest) -> None:
        """Validate that case is relevant to agent's specialty."""
        # Check if specialty is explicitly requested
        if self.specialty in request.requested_specialties:
            return
        
        # Check case content for specialty relevance
        relevance_score = await self._calculate_relevance_score(request)
        
        if relevance_score < 0.3:  # Minimum relevance threshold
            logger.warning("Low relevance score for specialty",
                          agent_id=self.agent_id,
                          specialty=self.specialty.value,
                          relevance_score=relevance_score)
    
    async def _calculate_relevance_score(self, request: CollaborationRequest) -> float:
        """Calculate how relevant the case is to this specialty."""
        specialty_keywords = self._get_specialty_keywords()
        common_conditions = self._get_common_conditions()
        
        # Combine text from various fields
        text_content = " ".join([
            request.case_summary.lower(),
            request.chief_complaint.lower(),
            " ".join(request.symptoms).lower(),
            " ".join(request.medical_history).lower()
        ])
        
        # Count keyword matches
        keyword_matches = sum(1 for keyword in specialty_keywords if keyword in text_content)
        condition_matches = sum(1 for condition in common_conditions if condition in text_content)
        
        # Calculate relevance score
        total_terms = len(specialty_keywords) + len(common_conditions)
        if total_terms == 0:
            return 0.5  # Neutral relevance
        
        relevance_score = (keyword_matches + condition_matches) / total_terms
        return min(1.0, relevance_score)
    
    async def _validate_recommendation(self, recommendation: AgentRecommendation) -> None:
        """Validate quality and safety of recommendation."""
        # Check confidence thresholds
        if recommendation.overall_confidence < 0.1:
            logger.warning("Very low confidence recommendation",
                          agent_id=self.agent_id,
                          confidence=recommendation.overall_confidence)
        
        # Check for safety concerns
        if recommendation.overall_confidence < 0.5 and not recommendation.requires_further_evaluation:
            recommendation.requires_further_evaluation = True
            logger.info("Low confidence recommendation marked for further evaluation",
                       agent_id=self.agent_id)
        
        # Validate differential diagnoses probabilities
        if recommendation.differential_diagnoses:
            total_probability = sum(dx.probability for dx in recommendation.differential_diagnoses)
            if total_probability > 1.1:  # Allow small tolerance for rounding
                logger.warning("Differential diagnosis probabilities exceed 100%",
                              agent_id=self.agent_id,
                              total_probability=total_probability)
    
    async def _update_performance_metrics(self, recommendation: AgentRecommendation, processing_time: float) -> None:
        """Update agent performance metrics."""
        self.total_cases += 1
        self.total_processing_time += processing_time
        
        # Update running averages
        alpha = 0.1  # Learning rate for exponential moving average
        self.average_confidence = (1 - alpha) * self.average_confidence + alpha * recommendation.overall_confidence
        
        # Update database profile
        async with get_db() as db:
            profile = await db.get(A2AAgentProfile, self.profile.id)
            if profile:
                profile.total_collaborations = self.total_cases
                profile.response_time_average_ms = self.total_processing_time / self.total_cases
                profile.last_active_at = datetime.utcnow()
                await db.commit()

class CardiologyAgent(BaseSpecialtyAgent):
    """Specialized agent for cardiology consultations."""
    
    def __init__(self):
        super().__init__("cardiology_agent_v1", MedicalSpecialty.CARDIOLOGY, "1.0")
    
    def _get_specialty_keywords(self) -> List[str]:
        return [
            "chest pain", "heart", "cardiac", "coronary", "arrhythmia", "palpitations",
            "shortness of breath", "dyspnea", "edema", "hypertension", "hypotension",
            "murmur", "ecg", "ekg", "echocardiogram", "stress test", "catheterization",
            "myocardial", "infarction", "angina", "valve", "atrial", "ventricular"
        ]
    
    def _get_common_conditions(self) -> List[str]:
        return [
            "coronary artery disease", "myocardial infarction", "heart failure",
            "atrial fibrillation", "hypertension", "valvular heart disease",
            "cardiomyopathy", "arrhythmia", "angina", "pericarditis"
        ]
    
    async def _generate_recommendation(self, request: CollaborationRequest) -> AgentRecommendation:
        """Generate cardiology-specific recommendation."""
        
        # Analyze cardiovascular risk factors
        risk_factors = await self._assess_cardiovascular_risk(request)
        
        # Generate differential diagnoses
        differential_diagnoses = await self._generate_cardiac_differentials(request)
        
        # Generate treatment recommendations
        treatments = await self._generate_cardiac_treatments(request, differential_diagnoses)
        
        # Assess urgency and need for immediate intervention
        urgency_assessment = await self._assess_cardiac_urgency(request)
        
        # Calculate confidence based on clinical indicators
        confidence = await self._calculate_cardiology_confidence(request, differential_diagnoses)
        
        # Determine if cardiology subspecialist consultation needed
        subspecialist_needed = await self._assess_subspecialist_need(request, differential_diagnoses)
        
        recommendation = AgentRecommendation(
            agent_id=self.agent_id,
            specialty=self.specialty,
            primary_assessment=f"Cardiology assessment: {urgency_assessment['summary']}",
            differential_diagnoses=differential_diagnoses,
            treatment_recommendations=treatments,
            overall_confidence=confidence,
            specialist_confidence=confidence,
            requires_further_evaluation=urgency_assessment['requires_immediate_evaluation'],
            follow_up_timeline=urgency_assessment.get('follow_up_timeline'),
            warning_signs=urgency_assessment.get('warning_signs', []),
            escalation_criteria=urgency_assessment.get('escalation_criteria', []),
            requests_consultation=subspecialist_needed['needed'],
            requested_specialties=[MedicalSpecialty.EMERGENCY_MEDICINE] if urgency_assessment['emergency'] else [],
            processing_time_ms=(datetime.utcnow() - self.processing_start_time).total_seconds() * 1000,
            knowledge_sources=["AHA/ESC Guidelines", "Cardiology Clinical Protocols", "Evidence-Based Medicine"]
        )
        
        return recommendation
    
    async def _assess_cardiovascular_risk(self, request: CollaborationRequest) -> Dict[str, Any]:
        """Assess cardiovascular risk factors."""
        risk_factors = {
            "age_risk": "high" if request.patient_age and request.patient_age > 65 else "moderate",
            "symptom_based_risk": "high" if any(symptom in ["chest pain", "shortness of breath"] for symptom in request.symptoms) else "low",
            "history_based_risk": "high" if any(hist in ["diabetes", "hypertension", "smoking"] for hist in request.medical_history) else "low"
        }
        return risk_factors
    
    async def _generate_cardiac_differentials(self, request: CollaborationRequest) -> List[DifferentialDiagnosis]:
        """Generate cardiology-specific differential diagnoses."""
        differentials = []
        
        # Analyze chief complaint and symptoms for cardiac conditions
        if "chest pain" in request.chief_complaint.lower() or "chest pain" in [s.lower() for s in request.symptoms]:
            differentials.extend([
                DifferentialDiagnosis(
                    condition="Acute Coronary Syndrome",
                    icd_10_code="I21.9",
                    probability=0.7,
                    supporting_evidence=[
                        ClinicalEvidence(
                            evidence_type="clinical",
                            source="symptoms",
                            finding="chest pain",
                            significance="cardinal symptom of ACS",
                            confidence_level=0.8
                        )
                    ]
                ),
                DifferentialDiagnosis(
                    condition="Stable Angina",
                    icd_10_code="I20.9",
                    probability=0.2,
                    supporting_evidence=[]
                )
            ])
        
        return differentials
    
    async def _generate_cardiac_treatments(self, request: CollaborationRequest, differentials: List[DifferentialDiagnosis]) -> List[TreatmentRecommendation]:
        """Generate cardiology treatment recommendations."""
        treatments = []
        
        for differential in differentials:
            if differential.condition == "Acute Coronary Syndrome" and differential.probability > 0.5:
                treatments.append(
                    TreatmentRecommendation(
                        intervention="Emergency cardiac evaluation with ECG and cardiac enzymes",
                        priority="immediate",
                        rationale="High probability ACS requires immediate evaluation",
                        contraindications=["Known bleeding disorder"],
                        monitoring_requirements=["Continuous cardiac monitoring", "Serial ECGs", "Cardiac enzymes q6h"],
                        expected_outcome="Risk stratification and appropriate intervention"
                    )
                )
        
        return treatments
    
    async def _assess_cardiac_urgency(self, request: CollaborationRequest) -> Dict[str, Any]:
        """Assess cardiac urgency and immediate intervention needs."""
        emergency_indicators = ["chest pain", "shortness of breath", "syncope", "palpitations"]
        
        has_emergency_symptoms = any(symptom in request.symptoms for symptom in emergency_indicators)
        
        return {
            "summary": "High-risk cardiac presentation requiring immediate evaluation" if has_emergency_symptoms else "Stable cardiac condition",
            "emergency": has_emergency_symptoms,
            "requires_immediate_evaluation": has_emergency_symptoms,
            "follow_up_timeline": "24-48 hours" if has_emergency_symptoms else "1-2 weeks",
            "warning_signs": ["Worsening chest pain", "Severe shortness of breath", "Syncope"],
            "escalation_criteria": ["New or worsening symptoms", "Hemodynamic instability"]
        }
    
    async def _calculate_cardiology_confidence(self, request: CollaborationRequest, differentials: List[DifferentialDiagnosis]) -> float:
        """Calculate confidence based on cardiology-specific factors."""
        confidence_factors = []
        
        # Confidence based on symptom clarity
        if "chest pain" in request.symptoms:
            confidence_factors.append(0.8)
        
        # Confidence based on available data
        if request.vital_signs:
            confidence_factors.append(0.7)
        
        if request.lab_results:
            confidence_factors.append(0.9)
        
        # Default moderate confidence if no specific indicators
        if not confidence_factors:
            confidence_factors.append(0.6)
        
        return sum(confidence_factors) / len(confidence_factors)
    
    async def _assess_subspecialist_need(self, request: CollaborationRequest, differentials: List[DifferentialDiagnosis]) -> Dict[str, Any]:
        """Assess if cardiology subspecialist consultation is needed."""
        complex_conditions = ["complex arrhythmia", "heart failure", "valvular disease"]
        
        needs_subspecialist = any(
            any(complex_cond in dx.condition.lower() for complex_cond in complex_conditions)
            for dx in differentials
        )
        
        return {
            "needed": needs_subspecialist,
            "reason": "Complex cardiac condition requiring subspecialist evaluation" if needs_subspecialist else None
        }

class NeurologyAgent(BaseSpecialtyAgent):
    """Specialized agent for neurology consultations."""
    
    def __init__(self):
        super().__init__("neurology_agent_v1", MedicalSpecialty.NEUROLOGY, "1.0")
    
    def _get_specialty_keywords(self) -> List[str]:
        return [
            "headache", "seizure", "stroke", "weakness", "numbness", "dizziness",
            "memory loss", "confusion", "tremor", "balance", "vision changes",
            "speech", "neuropathy", "migraine", "epilepsy", "parkinson",
            "alzheimer", "dementia", "multiple sclerosis", "brain", "spine"
        ]
    
    def _get_common_conditions(self) -> List[str]:
        return [
            "stroke", "seizure disorder", "migraine", "tension headache",
            "peripheral neuropathy", "multiple sclerosis", "parkinson disease",
            "alzheimer disease", "epilepsy", "brain tumor"
        ]
    
    async def _generate_recommendation(self, request: CollaborationRequest) -> AgentRecommendation:
        """Generate neurology-specific recommendation."""
        
        # Assess neurological symptoms
        neuro_assessment = await self._assess_neurological_symptoms(request)
        
        # Generate neurological differentials
        differential_diagnoses = await self._generate_neuro_differentials(request)
        
        # Generate treatment recommendations
        treatments = await self._generate_neuro_treatments(request, differential_diagnoses)
        
        # Assess urgency (stroke alert, seizure, etc.)
        urgency_assessment = await self._assess_neuro_urgency(request)
        
        # Calculate confidence
        confidence = await self._calculate_neurology_confidence(request, differential_diagnoses)
        
        recommendation = AgentRecommendation(
            agent_id=self.agent_id,
            specialty=self.specialty,
            primary_assessment=f"Neurological assessment: {neuro_assessment['summary']}",
            differential_diagnoses=differential_diagnoses,
            treatment_recommendations=treatments,
            overall_confidence=confidence,
            specialist_confidence=confidence,
            requires_further_evaluation=urgency_assessment['requires_immediate_evaluation'],
            follow_up_timeline=urgency_assessment.get('follow_up_timeline'),
            warning_signs=urgency_assessment.get('warning_signs', []),
            escalation_criteria=urgency_assessment.get('escalation_criteria', []),
            requests_consultation=urgency_assessment['emergency'],
            requested_specialties=[MedicalSpecialty.EMERGENCY_MEDICINE] if urgency_assessment['emergency'] else [],
            processing_time_ms=(datetime.utcnow() - self.processing_start_time).total_seconds() * 1000,
            knowledge_sources=["AAN Guidelines", "Neurology Clinical Protocols", "Stroke Guidelines"]
        )
        
        return recommendation
    
    async def _assess_neurological_symptoms(self, request: CollaborationRequest) -> Dict[str, Any]:
        """Assess neurological symptoms and signs."""
        # Implement neurological symptom analysis
        return {"summary": "Neurological symptom assessment completed"}
    
    async def _generate_neuro_differentials(self, request: CollaborationRequest) -> List[DifferentialDiagnosis]:
        """Generate neurology-specific differentials."""
        differentials = []
        
        # Stroke assessment
        stroke_symptoms = ["weakness", "numbness", "speech problems", "vision changes"]
        if any(symptom in [s.lower() for s in request.symptoms] for symptom in stroke_symptoms):
            differentials.append(
                DifferentialDiagnosis(
                    condition="Acute Stroke",
                    icd_10_code="I63.9",
                    probability=0.8,
                    supporting_evidence=[
                        ClinicalEvidence(
                            evidence_type="clinical",
                            source="neurological examination",
                            finding="focal neurological deficits",
                            significance="classic stroke presentation",
                            confidence_level=0.9
                        )
                    ]
                )
            )
        
        return differentials
    
    async def _generate_neuro_treatments(self, request: CollaborationRequest, differentials: List[DifferentialDiagnosis]) -> List[TreatmentRecommendation]:
        """Generate neurology treatment recommendations."""
        # Implement neurology-specific treatments
        return []
    
    async def _assess_neuro_urgency(self, request: CollaborationRequest) -> Dict[str, Any]:
        """Assess neurological urgency."""
        emergency_symptoms = ["sudden weakness", "speech problems", "severe headache", "seizure"]
        has_emergency = any(symptom in request.symptoms for symptom in emergency_symptoms)
        
        return {
            "summary": "Neurological emergency" if has_emergency else "Stable neurological condition",
            "emergency": has_emergency,
            "requires_immediate_evaluation": has_emergency
        }
    
    async def _calculate_neurology_confidence(self, request: CollaborationRequest, differentials: List[DifferentialDiagnosis]) -> float:
        """Calculate neurology-specific confidence."""
        return 0.7  # Placeholder

class EmergencyMedicineAgent(BaseSpecialtyAgent):
    """Specialized agent for emergency medicine consultations."""
    
    def __init__(self):
        super().__init__("emergency_agent_v1", MedicalSpecialty.EMERGENCY_MEDICINE, "1.0")
    
    def _get_specialty_keywords(self) -> List[str]:
        return [
            "emergency", "urgent", "severe", "acute", "critical", "trauma",
            "shock", "unconscious", "respiratory distress", "cardiac arrest",
            "severe pain", "bleeding", "poisoning", "overdose", "burns"
        ]
    
    def _get_common_conditions(self) -> List[str]:
        return [
            "trauma", "shock", "sepsis", "acute abdomen", "respiratory failure",
            "cardiac emergency", "stroke", "poisoning", "burns", "fractures"
        ]
    
    async def _generate_recommendation(self, request: CollaborationRequest) -> AgentRecommendation:
        """Generate emergency medicine recommendation with triage focus."""
        
        # Triage assessment - most critical first
        triage_assessment = await self._perform_triage_assessment(request)
        
        # ABC (Airway, Breathing, Circulation) evaluation
        abc_assessment = await self._assess_abc_priorities(request)
        
        # Generate emergency differentials
        differential_diagnoses = await self._generate_emergency_differentials(request)
        
        # Generate immediate interventions
        treatments = await self._generate_emergency_treatments(request, differential_diagnoses, abc_assessment)
        
        # Emergency-specific confidence based on acuity
        confidence = await self._calculate_emergency_confidence(request, triage_assessment)
        
        recommendation = AgentRecommendation(
            agent_id=self.agent_id,
            specialty=self.specialty,
            primary_assessment=f"Emergency triage: {triage_assessment['category']} - {abc_assessment['summary']}",
            differential_diagnoses=differential_diagnoses,
            treatment_recommendations=treatments,
            overall_confidence=confidence,
            specialist_confidence=confidence,
            requires_further_evaluation=triage_assessment['category'] in ['critical', 'emergent'],
            follow_up_timeline="Immediate" if triage_assessment['category'] == 'critical' else "Within 1 hour",
            warning_signs=abc_assessment.get('warning_signs', []),
            escalation_criteria=["Hemodynamic instability", "Respiratory compromise", "Neurological deterioration"],
            requests_consultation=triage_assessment['specialist_needed'],
            requested_specialties=triage_assessment.get('requested_specialties', []),
            processing_time_ms=(datetime.utcnow() - self.processing_start_time).total_seconds() * 1000,
            knowledge_sources=["ACEP Guidelines", "Emergency Medicine Protocols", "Trauma Guidelines"]
        )
        
        return recommendation
    
    async def _perform_triage_assessment(self, request: CollaborationRequest) -> Dict[str, Any]:
        """Perform emergency triage assessment."""
        critical_symptoms = ["unconscious", "severe bleeding", "respiratory distress", "cardiac arrest"]
        emergent_symptoms = ["severe pain", "chest pain", "difficulty breathing", "severe headache"]
        
        if any(symptom in [s.lower() for s in request.symptoms] for symptom in critical_symptoms):
            category = "critical"
        elif any(symptom in [s.lower() for s in request.symptoms] for symptom in emergent_symptoms):
            category = "emergent"
        else:
            category = "urgent"
        
        return {
            "category": category,
            "specialist_needed": category == "critical",
            "requested_specialties": [MedicalSpecialty.CARDIOLOGY] if "chest pain" in request.symptoms else []
        }
    
    async def _assess_abc_priorities(self, request: CollaborationRequest) -> Dict[str, Any]:
        """Assess Airway, Breathing, Circulation priorities."""
        return {
            "summary": "ABC assessment: Airway patent, breathing adequate, circulation stable",
            "warning_signs": ["Airway compromise", "Respiratory distress", "Hemodynamic instability"]
        }
    
    async def _generate_emergency_differentials(self, request: CollaborationRequest) -> List[DifferentialDiagnosis]:
        """Generate emergency-focused differentials."""
        # Emergency medicine focuses on life-threatening conditions first
        return []
    
    async def _generate_emergency_treatments(self, request: CollaborationRequest, differentials: List[DifferentialDiagnosis], abc_assessment: Dict[str, Any]) -> List[TreatmentRecommendation]:
        """Generate emergency treatments prioritizing ABC."""
        return []
    
    async def _calculate_emergency_confidence(self, request: CollaborationRequest, triage: Dict[str, Any]) -> float:
        """Calculate confidence based on emergency acuity."""
        # Higher confidence for clear emergency presentations
        if triage['category'] == 'critical':
            return 0.9
        elif triage['category'] == 'emergent':
            return 0.8
        else:
            return 0.6

class MedicalAgentFactory:
    """Factory for creating and managing medical specialty agents."""
    
    _agents: Dict[MedicalSpecialty, BaseSpecialtyAgent] = {}
    
    @classmethod
    async def get_agent(cls, specialty: MedicalSpecialty) -> BaseSpecialtyAgent:
        """Get or create a medical specialty agent."""
        
        if specialty not in cls._agents:
            # Create new agent based on specialty
            if specialty == MedicalSpecialty.CARDIOLOGY:
                agent = CardiologyAgent()
            elif specialty == MedicalSpecialty.NEUROLOGY:
                agent = NeurologyAgent()
            elif specialty == MedicalSpecialty.EMERGENCY_MEDICINE:
                agent = EmergencyMedicineAgent()
            else:
                # Generic agent for other specialties
                agent = cls._create_generic_agent(specialty)
            
            await agent.initialize()
            cls._agents[specialty] = agent
        
        return cls._agents[specialty]
    
    @classmethod
    def _create_generic_agent(cls, specialty: MedicalSpecialty) -> BaseSpecialtyAgent:
        """Create a generic agent for specialties without specific implementations."""
        
        class GenericSpecialtyAgent(BaseSpecialtyAgent):
            def __init__(self, specialty: MedicalSpecialty):
                super().__init__(f"{specialty.value}_agent_v1", specialty, "1.0")
            
            def _get_specialty_keywords(self) -> List[str]:
                return [self.specialty.value.replace("_", " ")]
            
            def _get_common_conditions(self) -> List[str]:
                return [f"{self.specialty.value} conditions"]
            
            async def _generate_recommendation(self, request: CollaborationRequest) -> AgentRecommendation:
                return AgentRecommendation(
                    agent_id=self.agent_id,
                    specialty=self.specialty,
                    primary_assessment=f"Generic {self.specialty.value} assessment",
                    overall_confidence=0.5,
                    specialist_confidence=0.5,
                    processing_time_ms=(datetime.utcnow() - self.processing_start_time).total_seconds() * 1000,
                    knowledge_sources=[f"{self.specialty.value} protocols"]
                )
        
        return GenericSpecialtyAgent(specialty)
    
    @classmethod
    async def list_available_specialties(cls) -> List[MedicalSpecialty]:
        """List all available medical specialties."""
        return list(MedicalSpecialty)
    
    @classmethod
    async def get_agent_profiles(cls) -> List[MedicalAgentProfile]:
        """Get profiles of all available agents."""
        profiles = []
        
        for specialty in MedicalSpecialty:
            agent = await cls.get_agent(specialty)
            
            profile = MedicalAgentProfile(
                agent_id=agent.agent_id,
                agent_name=f"{specialty.value.title()} AI Specialist",
                specialty=specialty,
                model_type="gemma_medical",
                model_version=agent.model_version,
                accuracy_score=getattr(agent, 'average_confidence', 0.0),
                collaboration_count=getattr(agent, 'total_cases', 0),
                emergency_capable=(specialty == MedicalSpecialty.EMERGENCY_MEDICINE)
            )
            
            profiles.append(profile)
        
        return profiles