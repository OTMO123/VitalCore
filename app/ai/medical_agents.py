#!/usr/bin/env python3
"""
Gemma3N Specialized Medical Agents - Production AI System

Specialized medical AI agents for different healthcare domains using Gemma 3N
with domain-specific training and medical knowledge integration.

Agents:
- Cardiology Agent: Heart and cardiovascular conditions
- Neurology Agent: Brain and nervous system disorders  
- Pulmonology Agent: Respiratory and lung conditions
- Emergency Agent: Critical care and trauma
- Pediatrics Agent: Child and adolescent medicine
- Infectious Disease Agent: Infections and antimicrobial therapy
- Psychiatry Agent: Mental health and behavioral disorders
- Orthopedics Agent: Musculoskeletal conditions
- General Medicine Agent: Primary care and general conditions
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

from .diagnosis_engine import AgentSpecialization, AgentDiagnosis

try:
    from ..modules.edge_ai.gemma_engine import GemmaOnDeviceEngine
    from ..modules.edge_ai.schemas import GemmaConfig, GemmaOutput, MedicalSpecialty
    from ..modules.edge_ai.specialized_agent_trainer import (
        SpecializedAgentTrainer, AgentTrainingConfig, MedicalDatasetRegistry
    )
except ImportError:
    logger.warning("Edge AI modules not available - using mock implementations")
    # Mock implementations
    class GemmaOnDeviceEngine:
        async def process_multimodal(self, prompt, config):
            class MockOutput:
                raw_response = "Mock medical response"
            return MockOutput()
    
    class GemmaConfig:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    class MedicalSpecialty:
        CARDIOLOGY = "cardiology"
        NEUROLOGY = "neurology"
        PULMONOLOGY = "pulmonology"
        EMERGENCY_MEDICINE = "emergency_medicine"
        INTERNAL_MEDICINE = "internal_medicine"
        PSYCHIATRY = "psychiatry"
        ENDOCRINOLOGY = "endocrinology"
        DERMATOLOGY = "dermatology"
        RADIOLOGY = "radiology"
        PATHOLOGY = "pathology"

@dataclass
class AgentCapabilities:
    """Capabilities and specialization details for medical agents"""
    specialization: AgentSpecialization
    medical_specialty: MedicalSpecialty
    expertise_areas: List[str]
    primary_conditions: List[str]
    diagnostic_strengths: List[str]
    typical_procedures: List[str]
    key_medications: List[str]
    emergency_indicators: List[str]
    confidence_threshold: float
    training_datasets: List[str]

@dataclass
class AgentPerformanceMetrics:
    """Performance tracking for medical agents"""
    agent_id: str
    total_diagnoses: int
    successful_diagnoses: int
    average_confidence: float
    average_processing_time_ms: float
    accuracy_rate: float
    false_positive_rate: float
    false_negative_rate: float
    emergency_detection_rate: float
    last_updated: datetime

class MedicalSpecializedAgent:
    """
    Base class for specialized medical AI agents
    Each agent has domain-specific knowledge and diagnostic capabilities
    """
    
    def __init__(
        self, 
        specialization: AgentSpecialization,
        model_path: Optional[str] = None
    ):
        self.specialization = specialization
        self.capabilities = self._initialize_capabilities()
        self.gemma_engine = GemmaOnDeviceEngine()
        self.performance_metrics = AgentPerformanceMetrics(
            agent_id=f"{specialization.value}_{uuid.uuid4().hex[:8]}",
            total_diagnoses=0,
            successful_diagnoses=0,
            average_confidence=0.0,
            average_processing_time_ms=0.0,
            accuracy_rate=0.0,
            false_positive_rate=0.0,
            false_negative_rate=0.0,
            emergency_detection_rate=0.0,
            last_updated=datetime.now(timezone.utc)
        )
        self.model_path = model_path or f"/models/{specialization.value}"
        self.knowledge_base = self._load_knowledge_base()
        
    def _initialize_capabilities(self) -> AgentCapabilities:
        """Initialize agent-specific capabilities and expertise"""
        
        capabilities_map = {
            AgentSpecialization.CARDIOLOGY: AgentCapabilities(
                specialization=AgentSpecialization.CARDIOLOGY,
                medical_specialty=MedicalSpecialty.CARDIOLOGY,
                expertise_areas=[
                    "coronary artery disease", "heart failure", "arrhythmias", 
                    "valvular disease", "hypertension", "cardiomyopathy"
                ],
                primary_conditions=[
                    "myocardial infarction", "angina", "atrial fibrillation",
                    "heart failure", "hypertension", "cardiac arrest"
                ],
                diagnostic_strengths=[
                    "ECG interpretation", "cardiac enzyme analysis", 
                    "echocardiogram reading", "stress test evaluation"
                ],
                typical_procedures=[
                    "ECG", "echocardiogram", "cardiac catheterization",
                    "stress testing", "holter monitoring"
                ],
                key_medications=[
                    "aspirin", "metoprolol", "lisinopril", "atorvastatin",
                    "clopidogrel", "warfarin", "digoxin"
                ],
                emergency_indicators=[
                    "chest pain", "cardiac arrest", "severe dyspnea",
                    "cardiogenic shock", "acute MI"
                ],
                confidence_threshold=0.75,
                training_datasets=["mimic_iii", "pubmed_abstracts", "medqa", "chest_xray_14"]
            ),
            
            AgentSpecialization.NEUROLOGY: AgentCapabilities(
                specialization=AgentSpecialization.NEUROLOGY,
                medical_specialty=MedicalSpecialty.NEUROLOGY,
                expertise_areas=[
                    "stroke", "epilepsy", "multiple sclerosis", "parkinson's disease",
                    "alzheimer's disease", "migraine", "neuropathy"
                ],
                primary_conditions=[
                    "stroke", "seizure", "migraine", "dementia",
                    "multiple sclerosis", "parkinson's disease"
                ],
                diagnostic_strengths=[
                    "neurological examination", "CT/MRI interpretation",
                    "EEG analysis", "cognitive assessment"
                ],
                typical_procedures=[
                    "CT brain", "MRI brain", "EEG", "lumbar puncture",
                    "neuropsychological testing"
                ],
                key_medications=[
                    "levetiracetam", "phenytoin", "sumatriptan", "levodopa",
                    "donepezil", "gabapentin", "baclofen"
                ],
                emergency_indicators=[
                    "stroke", "status epilepticus", "altered consciousness",
                    "severe headache", "neurological deficit"
                ],
                confidence_threshold=0.8,
                training_datasets=["mimic_iii", "pubmed_abstracts", "medqa", "clinical_notes_n2c2"]
            ),
            
            AgentSpecialization.PULMONOLOGY: AgentCapabilities(
                specialization=AgentSpecialization.PULMONOLOGY,
                medical_specialty=MedicalSpecialty.PULMONOLOGY,
                expertise_areas=[
                    "pneumonia", "asthma", "COPD", "pulmonary embolism",
                    "lung cancer", "sleep apnea", "interstitial lung disease"
                ],
                primary_conditions=[
                    "pneumonia", "asthma exacerbation", "COPD exacerbation",
                    "pulmonary embolism", "pneumothorax"
                ],
                diagnostic_strengths=[
                    "chest X-ray interpretation", "pulmonary function tests",
                    "arterial blood gas analysis", "CT chest reading"
                ],
                typical_procedures=[
                    "chest X-ray", "CT chest", "pulmonary function tests",
                    "bronchoscopy", "sleep study"
                ],
                key_medications=[
                    "albuterol", "prednisone", "azithromycin", "warfarin",
                    "tiotropium", "fluticasone", "theophylline"
                ],
                emergency_indicators=[
                    "severe dyspnea", "respiratory failure", "pulmonary embolism",
                    "pneumothorax", "status asthmaticus"
                ],
                confidence_threshold=0.75,
                training_datasets=["chest_xray_14", "mimic_iii", "pubmed_abstracts", "medqa"]
            ),
            
            AgentSpecialization.EMERGENCY: AgentCapabilities(
                specialization=AgentSpecialization.EMERGENCY,
                medical_specialty=MedicalSpecialty.EMERGENCY_MEDICINE,
                expertise_areas=[
                    "trauma", "shock", "cardiac arrest", "overdose",
                    "severe infections", "respiratory failure", "multi-organ failure"
                ],
                primary_conditions=[
                    "trauma", "septic shock", "cardiac arrest", "respiratory failure",
                    "drug overdose", "anaphylaxis", "severe bleeding"
                ],
                diagnostic_strengths=[
                    "rapid assessment", "triage prioritization", "trauma evaluation",
                    "shock recognition", "airway management"
                ],
                typical_procedures=[
                    "rapid sequence intubation", "central line placement",
                    "chest tube insertion", "FAST exam", "cardioversion"
                ],
                key_medications=[
                    "epinephrine", "norepinephrine", "atropine", "naloxone",
                    "adenosine", "amiodarone", "vasopressin"
                ],
                emergency_indicators=[
                    "cardiac arrest", "respiratory arrest", "severe trauma",
                    "shock", "altered mental status", "severe bleeding"
                ],
                confidence_threshold=0.9,
                training_datasets=["mimic_iii", "clinical_notes_n2c2", "symptom_disease_dataset"]
            ),
            
            AgentSpecialization.PEDIATRICS: AgentCapabilities(
                specialization=AgentSpecialization.PEDIATRICS,
                medical_specialty=MedicalSpecialty.EMERGENCY_MEDICINE,  # No direct pediatrics in enum
                expertise_areas=[
                    "pediatric emergency", "febrile seizures", "dehydration",
                    "respiratory infections", "developmental disorders"
                ],
                primary_conditions=[
                    "febrile seizure", "viral syndrome", "dehydration",
                    "bronchiolitis", "gastroenteritis"
                ],
                diagnostic_strengths=[
                    "pediatric assessment", "growth evaluation",
                    "developmental screening", "vaccination status"
                ],
                typical_procedures=[
                    "pediatric physical exam", "developmental assessment",
                    "vaccination", "growth measurement"
                ],
                key_medications=[
                    "acetaminophen", "ibuprofen", "amoxicillin", "albuterol",
                    "oral rehydration solution", "epinephrine auto-injector"
                ],
                emergency_indicators=[
                    "febrile seizure", "severe dehydration", "respiratory distress",
                    "altered consciousness", "severe allergic reaction"
                ],
                confidence_threshold=0.8,
                training_datasets=["pubmed_abstracts", "medqa", "symptom_disease_dataset"]
            ),
            
            AgentSpecialization.INFECTIOUS_DISEASE: AgentCapabilities(
                specialization=AgentSpecialization.INFECTIOUS_DISEASE,
                medical_specialty=MedicalSpecialty.INTERNAL_MEDICINE,
                expertise_areas=[
                    "sepsis", "pneumonia", "urinary tract infections",
                    "skin and soft tissue infections", "antimicrobial resistance"
                ],
                primary_conditions=[
                    "sepsis", "pneumonia", "UTI", "cellulitis", "endocarditis"
                ],
                diagnostic_strengths=[
                    "infection source identification", "antimicrobial selection",
                    "resistance pattern recognition", "severity assessment"
                ],
                typical_procedures=[
                    "blood cultures", "urine cultures", "imaging studies",
                    "lumbar puncture", "tissue biopsy"
                ],
                key_medications=[
                    "vancomycin", "piperacillin-tazobactam", "ceftriaxone",
                    "azithromycin", "metronidazole", "fluconazole"
                ],
                emergency_indicators=[
                    "septic shock", "meningitis", "severe pneumonia",
                    "endocarditis", "necrotizing fasciitis"
                ],
                confidence_threshold=0.75,
                training_datasets=["mimic_iii", "drugbank_open", "pubmed_abstracts", "medqa"]
            ),
            
            AgentSpecialization.PSYCHIATRY: AgentCapabilities(
                specialization=AgentSpecialization.PSYCHIATRY,
                medical_specialty=MedicalSpecialty.PSYCHIATRY,
                expertise_areas=[
                    "major depression", "anxiety disorders", "bipolar disorder",
                    "schizophrenia", "substance abuse", "suicidal ideation"
                ],
                primary_conditions=[
                    "major depressive disorder", "generalized anxiety disorder",
                    "bipolar disorder", "panic disorder", "substance use disorder"
                ],
                diagnostic_strengths=[
                    "mental status examination", "risk assessment",
                    "substance abuse screening", "cognitive assessment"
                ],
                typical_procedures=[
                    "psychiatric interview", "mental status exam",
                    "substance abuse screening", "suicide risk assessment"
                ],
                key_medications=[
                    "sertraline", "fluoxetine", "lithium", "quetiapine",
                    "lorazepam", "haloperidol", "naltrexone"
                ],
                emergency_indicators=[
                    "suicidal ideation", "homicidal ideation", "psychosis",
                    "severe agitation", "substance overdose"
                ],
                confidence_threshold=0.7,
                training_datasets=["mimic_iii", "pubmed_abstracts", "medqa", "clinical_notes_n2c2"]
            ),
            
            AgentSpecialization.ORTHOPEDICS: AgentCapabilities(
                specialization=AgentSpecialization.ORTHOPEDICS,
                medical_specialty=MedicalSpecialty.EMERGENCY_MEDICINE,  # No direct orthopedics in enum
                expertise_areas=[
                    "fractures", "joint injuries", "sports medicine",
                    "arthritis", "back pain", "tendon injuries"
                ],
                primary_conditions=[
                    "fracture", "sprain", "strain", "arthritis", "back pain"
                ],
                diagnostic_strengths=[
                    "musculoskeletal examination", "X-ray interpretation",
                    "joint assessment", "range of motion testing"
                ],
                typical_procedures=[
                    "X-ray", "MRI", "joint injection", "physical therapy",
                    "orthopedic surgery consultation"
                ],
                key_medications=[
                    "ibuprofen", "naproxen", "acetaminophen", "tramadol",
                    "prednisone", "hyaluronic acid", "cortisone"
                ],
                emergency_indicators=[
                    "open fracture", "compartment syndrome", "joint dislocation",
                    "severe trauma", "neurovascular compromise"
                ],
                confidence_threshold=0.7,
                training_datasets=["pubmed_abstracts", "medqa", "symptom_disease_dataset"]
            ),
            
            AgentSpecialization.GENERAL_MEDICINE: AgentCapabilities(
                specialization=AgentSpecialization.GENERAL_MEDICINE,
                medical_specialty=MedicalSpecialty.INTERNAL_MEDICINE,
                expertise_areas=[
                    "diabetes", "hypertension", "chronic diseases",
                    "preventive care", "health maintenance"
                ],
                primary_conditions=[
                    "diabetes mellitus", "hypertension", "hyperlipidemia",
                    "obesity", "chronic kidney disease"
                ],
                diagnostic_strengths=[
                    "comprehensive assessment", "chronic disease management",
                    "preventive screening", "risk factor modification"
                ],
                typical_procedures=[
                    "routine physical exam", "laboratory studies",
                    "screening tests", "immunizations"
                ],
                key_medications=[
                    "metformin", "lisinopril", "atorvastatin", "aspirin",
                    "metoprolol", "amlodipine", "omeprazole"
                ],
                emergency_indicators=[
                    "diabetic ketoacidosis", "hypertensive crisis",
                    "acute renal failure", "severe hypoglycemia"
                ],
                confidence_threshold=0.6,
                training_datasets=["pubmed_abstracts", "medqa", "symptom_disease_dataset"]
            )
        }
        
        return capabilities_map.get(self.specialization, capabilities_map[AgentSpecialization.GENERAL_MEDICINE])
    
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load agent-specific medical knowledge base"""
        
        # This would load from actual knowledge base files
        # For now, return structured knowledge based on capabilities
        knowledge_base = {
            "conditions": {
                condition: {
                    "description": f"Medical condition: {condition}",
                    "symptoms": [],
                    "treatments": [],
                    "complications": []
                }
                for condition in self.capabilities.primary_conditions
            },
            "medications": {
                med: {
                    "indications": [],
                    "contraindications": [],
                    "dosing": "",
                    "side_effects": []
                }
                for med in self.capabilities.key_medications
            },
            "procedures": {
                proc: {
                    "indications": [],
                    "contraindications": [],
                    "preparation": "",
                    "interpretation": ""
                }
                for proc in self.capabilities.typical_procedures
            },
            "emergency_protocols": {
                indicator: {
                    "assessment": "",
                    "immediate_actions": [],
                    "monitoring": []
                }
                for indicator in self.capabilities.emergency_indicators
            }
        }
        
        return knowledge_base
    
    async def process_diagnosis(
        self,
        patient_data: Dict[str, Any],
        symptoms: List[str],
        vital_signs: Dict[str, float],
        medical_history: List[str],
        context: Dict[str, Any] = None
    ) -> AgentDiagnosis:
        """
        Process diagnosis using agent's specialized knowledge
        
        Args:
            patient_data: Patient demographic and basic information
            symptoms: List of patient symptoms
            vital_signs: Vital sign measurements
            medical_history: Patient's medical history
            context: Additional context information
            
        Returns:
            AgentDiagnosis: Specialized diagnosis from this agent
        """
        
        start_time = datetime.now()
        
        try:
            # Analyze relevance to this agent's specialty
            relevance_score = await self._calculate_relevance(symptoms, medical_history)
            
            if relevance_score < 0.3:
                # Low relevance - provide minimal assessment
                return self._create_low_relevance_diagnosis()
            
            # Create specialized diagnostic prompt
            diagnostic_prompt = await self._create_diagnostic_prompt(
                patient_data, symptoms, vital_signs, medical_history, context
            )
            
            # Configure Gemma for this agent
            agent_config = self._get_agent_config()
            
            # Process with domain-specific analysis
            gemma_output = await self.gemma_engine.process_multimodal(
                prompt=diagnostic_prompt,
                config=agent_config
            )
            
            # Parse and enhance with knowledge base
            diagnosis = await self._parse_and_enhance_diagnosis(
                gemma_output, patient_data, symptoms, vital_signs
            )
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            diagnosis.processing_time_ms = processing_time
            
            # Update performance metrics
            await self._update_performance_metrics(diagnosis)
            
            return diagnosis
            
        except Exception as e:
            logger.error(
                f"Agent {self.specialization.value} diagnosis failed",
                error=str(e),
                exc_info=True
            )
            
            return self._create_error_diagnosis(str(e))
    
    async def _calculate_relevance(
        self, 
        symptoms: List[str], 
        medical_history: List[str]
    ) -> float:
        """Calculate how relevant this case is to the agent's specialty"""
        
        relevance_score = 0.0
        total_weight = 0.0
        
        combined_text = " ".join(symptoms + medical_history).lower()
        
        # Check expertise areas
        for area in self.capabilities.expertise_areas:
            if area.lower() in combined_text:
                relevance_score += 0.4
                total_weight += 0.4
        
        # Check primary conditions
        for condition in self.capabilities.primary_conditions:
            if condition.lower() in combined_text:
                relevance_score += 0.3
                total_weight += 0.3
        
        # Check emergency indicators
        for indicator in self.capabilities.emergency_indicators:
            if indicator.lower() in combined_text:
                relevance_score += 0.5
                total_weight += 0.5
        
        # Normalize score
        if total_weight > 0:
            normalized_score = min(relevance_score / total_weight, 1.0)
        else:
            normalized_score = 0.1  # Minimal relevance for all cases
        
        return normalized_score
    
    async def _create_diagnostic_prompt(
        self,
        patient_data: Dict[str, Any],
        symptoms: List[str],
        vital_signs: Dict[str, float],
        medical_history: List[str],
        context: Dict[str, Any] = None
    ) -> str:
        """Create specialized diagnostic prompt for this agent"""
        
        specialty_name = self.specialization.value.replace('_', ' ').title()
        
        prompt = f"""
You are a specialized {specialty_name} AI assistant with expertise in {', '.join(self.capabilities.expertise_areas[:3])}.

PATIENT INFORMATION:
Age: {patient_data.get('age', 'Unknown')}
Gender: {patient_data.get('gender', 'Unknown')}
Weight: {patient_data.get('weight', 'Unknown')} kg

PRESENTING SYMPTOMS:
{', '.join(symptoms)}

VITAL SIGNS:
{json.dumps(vital_signs, indent=2)}

MEDICAL HISTORY:
{', '.join(medical_history) if medical_history else 'No significant history'}

SPECIALTY FOCUS:
As a {specialty_name} specialist, focus on conditions within your expertise:
- Primary conditions: {', '.join(self.capabilities.primary_conditions[:5])}
- Emergency indicators: {', '.join(self.capabilities.emergency_indicators[:3])}

DIAGNOSTIC APPROACH:
1. Assess the clinical presentation from your specialty perspective
2. Consider differential diagnoses within your domain
3. Evaluate emergency indicators specific to your specialty
4. Recommend appropriate next steps and monitoring

RESPONSE FORMAT:
Primary Diagnosis: [Most likely diagnosis from your specialty perspective]
Differential Diagnoses: [Alternative diagnoses to consider in your field]
Confidence Score: [0.0 to 1.0 - your confidence in this assessment]
Clinical Reasoning: [Your step-by-step diagnostic reasoning]
Immediate Actions: [Recommended immediate actions from your specialty]
Risk Factors: [Relevant risk factors you've identified]
Contraindications: [Important contraindications to consider]
Specialty Recommendations: [Specific recommendations from your specialty]

Focus on your area of expertise while considering the patient's overall clinical picture.
"""

        return prompt.strip()
    
    def _get_agent_config(self) -> GemmaConfig:
        """Get Gemma configuration optimized for this agent"""
        
        base_config = {
            "model_path": self.model_path,
            "model_version": f"gemma-3n-{self.specialization.value}",
            "device": "cpu",
            "temperature": 0.15,
            "max_context_length": 2048,
            "max_response_tokens": 800,
            "quantization_enabled": True,
            "emergency_mode_enabled": False
        }
        
        # Agent-specific optimizations
        if self.specialization == AgentSpecialization.EMERGENCY:
            base_config.update({
                "temperature": 0.1,  # Lower temperature for emergency precision
                "emergency_mode_enabled": True,
                "max_response_tokens": 1024
            })
        elif self.specialization in [AgentSpecialization.CARDIOLOGY, AgentSpecialization.NEUROLOGY]:
            base_config.update({
                "temperature": 0.12,  # Slightly lower for critical specialties
                "max_response_tokens": 900
            })
        
        return GemmaConfig(**base_config)
    
    async def _parse_and_enhance_diagnosis(
        self,
        gemma_output: Any,  # Using Any instead of GemmaOutput to avoid import issues
        patient_data: Dict[str, Any],
        symptoms: List[str],
        vital_signs: Dict[str, float]
    ) -> AgentDiagnosis:
        """Parse Gemma output and enhance with knowledge base"""
        
        raw_response = gemma_output.raw_response
        
        # Parse structured fields
        primary_diagnosis = self._extract_field(raw_response, "Primary Diagnosis")
        differential_diagnoses = self._extract_list_field(raw_response, "Differential Diagnoses")
        confidence_score = self._extract_confidence(raw_response)
        reasoning_chain = self._extract_list_field(raw_response, "Clinical Reasoning")
        recommended_actions = self._extract_list_field(raw_response, "Immediate Actions")
        risk_factors = self._extract_list_field(raw_response, "Risk Factors")
        contraindications = self._extract_list_field(raw_response, "Contraindications")
        specialty_recommendations = self._extract_list_field(raw_response, "Specialty Recommendations")
        
        # Enhance with knowledge base
        enhanced_diagnosis = await self._enhance_with_knowledge_base(
            primary_diagnosis, differential_diagnoses, patient_data, symptoms, vital_signs
        )
        
        # Apply agent-specific validation
        validated_diagnosis = await self._validate_diagnosis(
            enhanced_diagnosis, confidence_score
        )
        
        return AgentDiagnosis(
            agent_specialization=self.specialization,
            primary_diagnosis=validated_diagnosis.get("primary_diagnosis", primary_diagnosis or "Unable to determine"),
            differential_diagnoses=validated_diagnosis.get("differential_diagnoses", differential_diagnoses),
            confidence_score=validated_diagnosis.get("confidence_score", confidence_score),
            reasoning_chain=reasoning_chain + enhanced_diagnosis.get("additional_reasoning", []),
            recommended_actions=recommended_actions + specialty_recommendations,
            risk_factors=risk_factors + enhanced_diagnosis.get("additional_risks", []),
            contraindications=contraindications + enhanced_diagnosis.get("additional_contraindications", []),
            processing_time_ms=0.0  # Will be set by caller
        )
    
    async def _enhance_with_knowledge_base(
        self,
        primary_diagnosis: str,
        differential_diagnoses: List[str],
        patient_data: Dict[str, Any],
        symptoms: List[str],
        vital_signs: Dict[str, float]
    ) -> Dict[str, Any]:
        """Enhance diagnosis with agent's knowledge base"""
        
        enhancements = {
            "additional_reasoning": [],
            "additional_risks": [],
            "additional_contraindications": []
        }
        
        # Check if diagnosis is in knowledge base
        if primary_diagnosis:
            for condition, details in self.knowledge_base["conditions"].items():
                if condition.lower() in primary_diagnosis.lower():
                    enhancements["additional_reasoning"].append(
                        f"Condition {condition} is within specialty expertise"
                    )
                    break
        
        # Check for medication considerations
        age = patient_data.get("age", 0)
        if age > 65:
            enhancements["additional_risks"].append("Advanced age - increased medication sensitivity")
        
        if age < 18:
            enhancements["additional_risks"].append("Pediatric considerations required")
        
        # Check vital signs for specialty-specific concerns
        if self.specialization == AgentSpecialization.CARDIOLOGY:
            hr = vital_signs.get("heart_rate", 0)
            if hr > 100:
                enhancements["additional_reasoning"].append("Tachycardia noted - cardiac evaluation indicated")
            elif hr < 60:
                enhancements["additional_reasoning"].append("Bradycardia noted - cardiac evaluation indicated")
        
        elif self.specialization == AgentSpecialization.PULMONOLOGY:
            o2_sat = vital_signs.get("oxygen_saturation", 100)
            if o2_sat < 95:
                enhancements["additional_reasoning"].append("Hypoxemia present - respiratory evaluation urgent")
        
        return enhancements
    
    async def _validate_diagnosis(
        self,
        enhanced_diagnosis: Dict[str, Any],
        confidence_score: float
    ) -> Dict[str, Any]:
        """Apply agent-specific validation and safety checks"""
        
        validated = enhanced_diagnosis.copy()
        
        # Apply confidence threshold
        if confidence_score < self.capabilities.confidence_threshold:
            validated["confidence_score"] = max(confidence_score * 0.8, 0.1)
            if "additional_reasoning" not in validated:
                validated["additional_reasoning"] = []
            validated["additional_reasoning"].append(
                f"Confidence below specialty threshold ({self.capabilities.confidence_threshold})"
            )
        else:
            validated["confidence_score"] = confidence_score
        
        # Emergency agent should have higher confidence for critical cases
        if self.specialization == AgentSpecialization.EMERGENCY:
            if any(indicator in str(enhanced_diagnosis).lower() 
                   for indicator in self.capabilities.emergency_indicators):
                validated["confidence_score"] = min(validated.get("confidence_score", 0.5) + 0.1, 1.0)
        
        return validated
    
    def _create_low_relevance_diagnosis(self) -> AgentDiagnosis:
        """Create diagnosis for cases with low relevance to this specialty"""
        
        return AgentDiagnosis(
            agent_specialization=self.specialization,
            primary_diagnosis=f"Outside {self.specialization.value.replace('_', ' ')} specialty scope",
            differential_diagnoses=["Refer to appropriate specialty"],
            confidence_score=0.2,
            reasoning_chain=[
                f"Case has low relevance to {self.specialization.value.replace('_', ' ')}",
                "Recommend evaluation by appropriate specialist"
            ],
            recommended_actions=[
                f"Consult appropriate specialist",
                "Continue general medical evaluation"
            ],
            risk_factors=["Delayed diagnosis if appropriate specialty not consulted"],
            contraindications=["Avoid specialty-specific treatments without proper evaluation"],
            processing_time_ms=0.0
        )
    
    def _create_error_diagnosis(self, error_message: str) -> AgentDiagnosis:
        """Create diagnosis for error cases"""
        
        return AgentDiagnosis(
            agent_specialization=self.specialization,
            primary_diagnosis="Unable to complete analysis - system error",
            differential_diagnoses=["Manual evaluation required"],
            confidence_score=0.1,
            reasoning_chain=[
                f"Agent processing error: {error_message}",
                "Fallback diagnosis generated"
            ],
            recommended_actions=[
                "Manual physician evaluation required",
                "System error review needed"
            ],
            risk_factors=["Delayed diagnosis due to system error"],
            contraindications=["Do not rely on this assessment for treatment decisions"],
            processing_time_ms=0.0
        )
    
    def _extract_field(self, text: str, field_name: str) -> Optional[str]:
        """Extract single field from agent response"""
        import re
        
        pattern = rf"{field_name}:\s*(.+?)(?:\n|$)"
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else None
    
    def _extract_list_field(self, text: str, field_name: str) -> List[str]:
        """Extract list field from agent response"""
        import re
        
        pattern = rf"{field_name}:\s*(.+?)(?:\n\n|\n[A-Z]|$)"
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        
        if not match:
            return []
        
        content = match.group(1).strip()
        items = re.split(r'[,;\n]\s*', content)
        return [item.strip('- ').strip() for item in items if item.strip()]
    
    def _extract_confidence(self, text: str) -> float:
        """Extract confidence score from agent response"""
        import re
        
        pattern = r"Confidence Score:\s*([0-9]*\.?[0-9]+)"
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            try:
                confidence = float(match.group(1))
                return min(max(confidence, 0.0), 1.0)
            except ValueError:
                pass
        
        return 0.5  # Default confidence
    
    async def _update_performance_metrics(self, diagnosis: AgentDiagnosis):
        """Update agent performance metrics"""
        
        self.performance_metrics.total_diagnoses += 1
        
        if diagnosis.confidence_score >= self.capabilities.confidence_threshold:
            self.performance_metrics.successful_diagnoses += 1
        
        # Update running averages
        total = self.performance_metrics.total_diagnoses
        self.performance_metrics.average_confidence = (
            (self.performance_metrics.average_confidence * (total - 1) + diagnosis.confidence_score) / total
        )
        
        self.performance_metrics.average_processing_time_ms = (
            (self.performance_metrics.average_processing_time_ms * (total - 1) + diagnosis.processing_time_ms) / total
        )
        
        self.performance_metrics.accuracy_rate = (
            self.performance_metrics.successful_diagnoses / total
        )
        
        # Check for emergency detection
        if any(indicator in diagnosis.primary_diagnosis.lower() 
               for indicator in self.capabilities.emergency_indicators):
            # Emergency detected - this would be verified in real implementation
            self.performance_metrics.emergency_detection_rate = (
                self.performance_metrics.emergency_detection_rate * (total - 1) + 1.0
            ) / total
        
        self.performance_metrics.last_updated = datetime.now(timezone.utc)
        
        logger.info(
            f"Updated metrics for {self.specialization.value}",
            total_diagnoses=self.performance_metrics.total_diagnoses,
            accuracy_rate=self.performance_metrics.accuracy_rate,
            avg_confidence=self.performance_metrics.average_confidence
        )
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report for this agent"""
        
        return {
            "agent_info": {
                "specialization": self.specialization.value,
                "medical_specialty": self.capabilities.medical_specialty.value,
                "confidence_threshold": self.capabilities.confidence_threshold
            },
            "performance_metrics": asdict(self.performance_metrics),
            "capabilities": {
                "expertise_areas": self.capabilities.expertise_areas,
                "primary_conditions": self.capabilities.primary_conditions,
                "emergency_indicators": self.capabilities.emergency_indicators
            },
            "knowledge_base_stats": {
                "conditions_count": len(self.knowledge_base["conditions"]),
                "medications_count": len(self.knowledge_base["medications"]),
                "procedures_count": len(self.knowledge_base["procedures"])
            }
        }

# Factory function for creating specialized agents
def create_medical_agent(specialization: AgentSpecialization) -> MedicalSpecializedAgent:
    """Factory function to create specialized medical agents"""
    
    return MedicalSpecializedAgent(specialization)

# Create all standard medical agents
def create_all_medical_agents() -> Dict[AgentSpecialization, MedicalSpecializedAgent]:
    """Create all standard medical agents for the HEMA3N system"""
    
    agents = {}
    
    for specialization in AgentSpecialization:
        try:
            agent = create_medical_agent(specialization)
            agents[specialization] = agent
            logger.info(f"Created {specialization.value} agent")
        except Exception as e:
            logger.error(f"Failed to create {specialization.value} agent: {e}")
    
    return agents

# Example usage and testing
async def test_medical_agent():
    """Test a medical agent with sample patient data"""
    
    # Create cardiology agent
    cardiology_agent = create_medical_agent(AgentSpecialization.CARDIOLOGY)
    
    # Sample patient data
    patient_data = {"age": 65, "gender": "male", "weight": 80}
    symptoms = ["chest pain", "shortness of breath", "diaphoresis"]
    vital_signs = {"heart_rate": 110, "blood_pressure_systolic": 160, "oxygen_saturation": 94}
    medical_history = ["hypertension", "diabetes", "smoking"]
    
    # Process diagnosis
    try:
        diagnosis = await cardiology_agent.process_diagnosis(
            patient_data, symptoms, vital_signs, medical_history
        )
        
        print(f"Cardiology Agent Diagnosis:")
        print(f"Primary: {diagnosis.primary_diagnosis}")
        print(f"Confidence: {diagnosis.confidence_score:.2f}")
        print(f"Actions: {', '.join(diagnosis.recommended_actions[:3])}")
        
        # Get performance report
        report = cardiology_agent.get_performance_report()
        print(f"Agent Performance: {report['performance_metrics']['accuracy_rate']:.2f}")
        
        return diagnosis
        
    except Exception as e:
        print(f"Agent test failed: {e}")
        return None

if __name__ == "__main__":
    # Test medical agents
    asyncio.run(test_medical_agent())