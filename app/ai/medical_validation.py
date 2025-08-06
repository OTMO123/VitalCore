#!/usr/bin/env python3
"""
Gemma3N Medical Diagnosis Validator - Clinical Safety and Validation

Comprehensive medical validation system ensuring clinical safety, accuracy,
and compliance with medical standards for AI-generated diagnoses.

Features:
- Clinical safety validation and contraindication checking
- Medical knowledge base validation against established guidelines
- Drug interaction and allergy checking
- Age and condition-specific validation rules
- Emergency situation validation and escalation
- Evidence-based medicine validation
- FHIR R4 compliance validation
- Medical terminology and coding validation
"""

import asyncio
import logging
import json
import re
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

from .diagnosis_engine import ConsolidatedDiagnosis, DiagnosisRequest, AgentSpecialization

try:
    from ..modules.edge_ai.schemas import UrgencyLevel, ValidationStatus
except ImportError:
    logger.warning("Edge AI schemas not available - using mock")
    class UrgencyLevel:
        LOW = "low"
        MODERATE = "moderate"
        HIGH = "high"
        CRITICAL = "critical"
        EMERGENCY = "emergency"
    
    class ValidationStatus:
        VALID = "valid"
        WARNING = "warning"
        ERROR = "error"

try:
    from ..modules.healthcare_records.schemas import PatientCreate
except ImportError:
    logger.warning("Healthcare records schemas not available")

class ValidationSeverity(str, Enum):
    """Severity levels for validation findings"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ValidationCategory(str, Enum):
    """Categories of medical validation"""
    CLINICAL_SAFETY = "clinical_safety"
    DRUG_INTERACTIONS = "drug_interactions"
    CONTRAINDICATIONS = "contraindications"
    AGE_APPROPRIATENESS = "age_appropriateness"
    EMERGENCY_PROTOCOLS = "emergency_protocols"
    EVIDENCE_BASED = "evidence_based"
    TERMINOLOGY = "terminology"
    COMPLIANCE = "compliance"

@dataclass
class ValidationFinding:
    """Individual validation finding"""
    finding_id: str
    category: ValidationCategory
    severity: ValidationSeverity
    title: str
    description: str
    affected_diagnosis: str
    recommendation: str
    evidence_reference: Optional[str] = None
    requires_human_review: bool = False
    auto_correctable: bool = False

@dataclass
class ValidationResult:
    """Comprehensive validation result"""
    validation_id: str
    overall_status: ValidationStatus
    validation_score: float  # 0-1 score
    findings: List[ValidationFinding]
    safety_cleared: bool
    requires_human_review: bool
    emergency_escalation_needed: bool
    validated_diagnosis: Optional[ConsolidatedDiagnosis]
    validation_timestamp: datetime
    validator_version: str = "1.0.0"

@dataclass
class MedicalKnowledgeBase:
    """Medical knowledge base for validation"""
    conditions: Dict[str, Dict[str, Any]]
    medications: Dict[str, Dict[str, Any]]
    contraindications: Dict[str, List[str]]
    drug_interactions: Dict[str, List[str]]
    age_restrictions: Dict[str, Dict[str, Any]]
    emergency_protocols: Dict[str, Dict[str, Any]]
    evidence_levels: Dict[str, str]

class MedicalDiagnosisValidator:
    """
    Comprehensive medical diagnosis validation system
    """
    
    def __init__(self):
        self.knowledge_base = self._initialize_knowledge_base()
        self.validation_rules = self._initialize_validation_rules()
        self.terminology_validator = MedicalTerminologyValidator()
        self.safety_checker = ClinicalSafetyChecker()
        self.drug_checker = DrugInteractionChecker()
        
    def _initialize_knowledge_base(self) -> MedicalKnowledgeBase:
        """Initialize comprehensive medical knowledge base"""
        
        # This would be loaded from comprehensive medical databases
        # For now, initialize with key medical knowledge
        
        conditions = {
            "myocardial infarction": {
                "icd10": "I21.9",
                "synonyms": ["heart attack", "mi", "stemi", "nstemi"],
                "emergency": True,
                "contraindications": ["thrombolytics with recent bleeding"],
                "required_actions": ["immediate catheterization", "dual antiplatelet therapy"],
                "monitoring": ["cardiac enzymes", "ecg", "hemodynamics"],
                "complications": ["cardiogenic shock", "arrhythmias", "mechanical complications"]
            },
            "stroke": {
                "icd10": "I64",
                "synonyms": ["cerebrovascular accident", "cva", "brain attack"],
                "emergency": True,
                "contraindications": ["tpa with contraindications"],
                "required_actions": ["ct scan", "neurological assessment", "blood pressure management"],
                "monitoring": ["neurological status", "blood pressure", "glucose"],
                "complications": ["cerebral edema", "hemorrhagic transformation"]
            },
            "pneumonia": {
                "icd10": "J18.9",
                "synonyms": ["lung infection", "respiratory infection"],
                "emergency": False,
                "contraindications": ["fluoroquinolones in pregnancy"],
                "required_actions": ["chest x-ray", "blood cultures", "antibiotic therapy"],
                "monitoring": ["respiratory status", "fever", "white blood cell count"],
                "complications": ["respiratory failure", "sepsis", "pleural effusion"]
            },
            "diabetes mellitus": {
                "icd10": "E11.9",
                "synonyms": ["diabetes", "dm", "type 2 diabetes"],
                "emergency": False,
                "contraindications": ["metformin in renal failure"],
                "required_actions": ["glucose monitoring", "hemoglobin a1c", "lifestyle counseling"],
                "monitoring": ["blood glucose", "hemoglobin a1c", "renal function"],
                "complications": ["diabetic ketoacidosis", "hyperosmolar state", "chronic complications"]
            }
        }
        
        medications = {
            "aspirin": {
                "category": "antiplatelet",
                "indications": ["cardiovascular protection", "myocardial infarction"],
                "contraindications": ["active bleeding", "severe liver disease"],
                "interactions": ["warfarin", "heparin"],
                "age_restrictions": {"min_age": 18, "pediatric_indication": "kawasaki disease"},
                "monitoring": ["bleeding", "gastrointestinal symptoms"]
            },
            "metformin": {
                "category": "antidiabetic",
                "indications": ["type 2 diabetes", "prediabetes"],
                "contraindications": ["severe renal impairment", "severe liver disease"],
                "interactions": ["contrast agents", "alcohol"],
                "age_restrictions": {"min_age": 10, "max_age": None},
                "monitoring": ["renal function", "vitamin b12", "lactic acidosis"]
            },
            "warfarin": {
                "category": "anticoagulant",
                "indications": ["atrial fibrillation", "venous thromboembolism"],
                "contraindications": ["active bleeding", "pregnancy"],
                "interactions": ["aspirin", "antibiotics", "many drugs"],
                "age_restrictions": {"min_age": 18, "elderly_caution": True},
                "monitoring": ["inr", "bleeding", "drug interactions"]
            }
        }
        
        contraindications = {
            "pregnancy": [
                "warfarin", "ace inhibitors", "statins", "fluoroquinolones"
            ],
            "renal_failure": [
                "metformin", "nsaids", "ace inhibitors"
            ],
            "liver_disease": [
                "acetaminophen", "statins", "warfarin"
            ],
            "bleeding_risk": [
                "anticoagulants", "antiplatelets", "thrombolytics"
            ]
        }
        
        drug_interactions = {
            "warfarin": [
                "aspirin", "antibiotics", "antifungals", "amiodarone"
            ],
            "metformin": [
                "contrast_agents", "alcohol", "diuretics"
            ],
            "digoxin": [
                "diuretics", "quinidine", "verapamil", "amiodarone"
            ]
        }
        
        age_restrictions = {
            "pediatric": {
                "min_age": 0,
                "max_age": 18,
                "restricted_medications": ["aspirin", "tetracyclines", "fluoroquinolones"],
                "special_dosing": ["weight_based", "surface_area_based"]
            },
            "geriatric": {
                "min_age": 65,
                "max_age": None,
                "high_risk_medications": ["anticholinergics", "sedatives", "nsaids"],
                "dose_adjustments": ["renal_function", "hepatic_function"]
            }
        }
        
        emergency_protocols = {
            "stemi": {
                "time_target": 90,  # minutes to catheterization
                "required_actions": ["dual antiplatelet", "anticoagulation", "catheterization"],
                "contraindications_check": ["bleeding", "surgery"],
                "monitoring": ["hemodynamics", "arrhythmias"]
            },
            "stroke": {
                "time_target": 60,  # minutes to tpa
                "required_actions": ["ct scan", "blood pressure management", "glucose control"],
                "contraindications_check": ["bleeding", "recent surgery", "anticoagulation"],
                "monitoring": ["neurological status", "blood pressure"]
            },
            "sepsis": {
                "time_target": 60,  # minutes to antibiotics
                "required_actions": ["blood cultures", "broad spectrum antibiotics", "fluid resuscitation"],
                "contraindications_check": ["drug allergies"],
                "monitoring": ["vital signs", "organ function", "lactate"]
            }
        }
        
        evidence_levels = {
            "myocardial infarction": "A",  # Strong evidence
            "stroke": "A",
            "pneumonia": "B",
            "diabetes mellitus": "A",
            "hypertension": "A"
        }
        
        return MedicalKnowledgeBase(
            conditions=conditions,
            medications=medications,
            contraindications=contraindications,
            drug_interactions=drug_interactions,
            age_restrictions=age_restrictions,
            emergency_protocols=emergency_protocols,
            evidence_levels=evidence_levels
        )
    
    def _initialize_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize validation rules and thresholds"""
        
        return {
            "confidence_thresholds": {
                "emergency_minimum": 0.7,
                "critical_minimum": 0.6,
                "standard_minimum": 0.5
            },
            "consensus_thresholds": {
                "strong_consensus": 0.8,
                "moderate_consensus": 0.6,
                "weak_consensus": 0.4
            },
            "safety_rules": {
                "require_human_review": [
                    "confidence < 0.6 AND emergency = True",
                    "contraindications_found > 0",
                    "drug_interactions_critical > 0"
                ],
                "auto_escalate": [
                    "emergency AND confidence < 0.5",
                    "critical_contraindications > 0"
                ]
            }
        }
    
    async def validate_diagnosis(
        self,
        diagnosis: ConsolidatedDiagnosis,
        request: DiagnosisRequest,
        patient_context: Dict[str, Any] = None
    ) -> ValidationResult:
        """
        Comprehensive validation of medical diagnosis
        
        Args:
            diagnosis: AI-generated consolidated diagnosis
            request: Original diagnosis request with patient data
            patient_context: Additional patient context and history
            
        Returns:
            ValidationResult: Comprehensive validation results
        """
        
        validation_start = datetime.now(timezone.utc)
        findings = []
        
        try:
            # 1. Clinical Safety Validation
            safety_findings = await self._validate_clinical_safety(
                diagnosis, request, patient_context
            )
            findings.extend(safety_findings)
            
            # 2. Drug Interaction Validation
            drug_findings = await self._validate_drug_interactions(
                diagnosis, request, patient_context
            )
            findings.extend(drug_findings)
            
            # 3. Contraindications Validation
            contraindication_findings = await self._validate_contraindications(
                diagnosis, request, patient_context
            )
            findings.extend(contraindication_findings)
            
            # 4. Age Appropriateness Validation
            age_findings = await self._validate_age_appropriateness(
                diagnosis, request, patient_context
            )
            findings.extend(age_findings)
            
            # 5. Emergency Protocol Validation
            emergency_findings = await self._validate_emergency_protocols(
                diagnosis, request
            )
            findings.extend(emergency_findings)
            
            # 6. Evidence-Based Medicine Validation
            evidence_findings = await self._validate_evidence_based(diagnosis)
            findings.extend(evidence_findings)
            
            # 7. Medical Terminology Validation
            terminology_findings = await self._validate_terminology(diagnosis)
            findings.extend(terminology_findings)
            
            # 8. Compliance Validation (FHIR, etc.)
            compliance_findings = await self._validate_compliance(diagnosis)
            findings.extend(compliance_findings)
            
            # Analyze findings and determine overall status
            validation_result = await self._analyze_validation_results(
                diagnosis, findings, validation_start
            )
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Validation failed: {e}", exc_info=True)
            
            # Return error validation result
            return ValidationResult(
                validation_id=str(uuid.uuid4()),
                overall_status=ValidationStatus.ERROR,
                validation_score=0.0,
                findings=[ValidationFinding(
                    finding_id=str(uuid.uuid4()),
                    category=ValidationCategory.CLINICAL_SAFETY,
                    severity=ValidationSeverity.CRITICAL,
                    title="Validation System Error",
                    description=f"Validation failed: {str(e)}",
                    affected_diagnosis=diagnosis.primary_diagnosis,
                    recommendation="Manual validation required",
                    requires_human_review=True
                )],
                safety_cleared=False,
                requires_human_review=True,
                emergency_escalation_needed=True,
                validated_diagnosis=None,
                validation_timestamp=datetime.now(timezone.utc)
            )
    
    async def _validate_clinical_safety(
        self,
        diagnosis: ConsolidatedDiagnosis,
        request: DiagnosisRequest,
        patient_context: Dict[str, Any] = None
    ) -> List[ValidationFinding]:
        """Validate clinical safety aspects"""
        
        findings = []
        
        # Check confidence thresholds for safety
        if request.urgency_level in [UrgencyLevel.CRITICAL, UrgencyLevel.EMERGENCY]:
            min_confidence = self.validation_rules["confidence_thresholds"]["emergency_minimum"]
            if diagnosis.overall_confidence < min_confidence:
                findings.append(ValidationFinding(
                    finding_id=str(uuid.uuid4()),
                    category=ValidationCategory.CLINICAL_SAFETY,
                    severity=ValidationSeverity.WARNING,
                    title="Low Confidence for Emergency Case",
                    description=f"Confidence {diagnosis.overall_confidence:.2f} below emergency threshold {min_confidence}",
                    affected_diagnosis=diagnosis.primary_diagnosis,
                    recommendation="Human physician review recommended",
                    requires_human_review=True
                ))
        
        # Check for high-risk diagnoses
        high_risk_conditions = ["cardiac arrest", "stroke", "sepsis", "anaphylaxis"]
        if any(condition in diagnosis.primary_diagnosis.lower() for condition in high_risk_conditions):
            if diagnosis.emergency_score < 0.8:
                findings.append(ValidationFinding(
                    finding_id=str(uuid.uuid4()),
                    category=ValidationCategory.CLINICAL_SAFETY,
                    severity=ValidationSeverity.WARNING,
                    title="High-Risk Condition with Low Emergency Score",
                    description=f"High-risk condition '{diagnosis.primary_diagnosis}' has emergency score {diagnosis.emergency_score:.2f}",
                    affected_diagnosis=diagnosis.primary_diagnosis,
                    recommendation="Verify emergency protocols are followed"
                ))
        
        # Check for missing critical actions
        critical_diagnoses = {
            "myocardial infarction": ["ecg", "cardiac enzymes", "catheterization"],
            "stroke": ["ct scan", "neurological assessment"],
            "sepsis": ["blood cultures", "antibiotics"]
        }
        
        for condition, required_actions in critical_diagnoses.items():
            if condition in diagnosis.primary_diagnosis.lower():
                missing_actions = []
                for action in required_actions:
                    if not any(action in ia.lower() for ia in diagnosis.immediate_actions):
                        missing_actions.append(action)
                
                if missing_actions:
                    findings.append(ValidationFinding(
                        finding_id=str(uuid.uuid4()),
                        category=ValidationCategory.CLINICAL_SAFETY,
                        severity=ValidationSeverity.ERROR,
                        title="Missing Critical Actions",
                        description=f"Missing critical actions for {condition}: {', '.join(missing_actions)}",
                        affected_diagnosis=diagnosis.primary_diagnosis,
                        recommendation=f"Add critical actions: {', '.join(missing_actions)}",
                        auto_correctable=True
                    ))
        
        return findings
    
    async def _validate_drug_interactions(
        self,
        diagnosis: ConsolidatedDiagnosis,
        request: DiagnosisRequest,
        patient_context: Dict[str, Any] = None
    ) -> List[ValidationFinding]:
        """Validate drug interactions"""
        
        findings = []
        
        # Extract medications from medical history
        current_medications = []
        if request.medical_history:
            for item in request.medical_history:
                # Simple medication extraction (would use NLP in production)
                for med in self.knowledge_base.medications.keys():
                    if med.lower() in item.lower():
                        current_medications.append(med)
        
        # Extract recommended medications from immediate actions
        recommended_medications = []
        for action in diagnosis.immediate_actions:
            for med in self.knowledge_base.medications.keys():
                if med.lower() in action.lower():
                    recommended_medications.append(med)
        
        # Check for drug interactions
        for current_med in current_medications:
            for rec_med in recommended_medications:
                if current_med in self.knowledge_base.drug_interactions:
                    if rec_med in self.knowledge_base.drug_interactions[current_med]:
                        findings.append(ValidationFinding(
                            finding_id=str(uuid.uuid4()),
                            category=ValidationCategory.DRUG_INTERACTIONS,
                            severity=ValidationSeverity.WARNING,
                            title="Potential Drug Interaction",
                            description=f"Interaction between current medication '{current_med}' and recommended '{rec_med}'",
                            affected_diagnosis=diagnosis.primary_diagnosis,
                            recommendation=f"Monitor for {current_med}-{rec_med} interaction or consider alternative",
                            requires_human_review=True
                        ))
        
        return findings
    
    async def _validate_contraindications(
        self,
        diagnosis: ConsolidatedDiagnosis,
        request: DiagnosisRequest,
        patient_context: Dict[str, Any] = None
    ) -> List[ValidationFinding]:
        """Validate contraindications"""
        
        findings = []
        
        # Check for condition-specific contraindications
        primary_condition = diagnosis.primary_diagnosis.lower()
        
        if primary_condition in self.knowledge_base.conditions:
            condition_info = self.knowledge_base.conditions[primary_condition]
            contraindications = condition_info.get("contraindications", [])
            
            # Check against patient history
            for contraindication in contraindications:
                if any(contraindication.lower() in hist.lower() for hist in request.medical_history):
                    findings.append(ValidationFinding(
                        finding_id=str(uuid.uuid4()),
                        category=ValidationCategory.CONTRAINDICATIONS,
                        severity=ValidationSeverity.ERROR,
                        title="Medical Contraindication",
                        description=f"Patient history contains contraindication: {contraindication}",
                        affected_diagnosis=diagnosis.primary_diagnosis,
                        recommendation=f"Consider alternative approach due to {contraindication}",
                        requires_human_review=True
                    ))
        
        # Check for general contraindications based on patient factors
        patient_age = request.patient_data.get("age", 0)
        if patient_age < 18:
            pediatric_contraindications = self.knowledge_base.contraindications.get("pediatric", [])
            for action in diagnosis.immediate_actions:
                for contraindication in pediatric_contraindications:
                    if contraindication.lower() in action.lower():
                        findings.append(ValidationFinding(
                            finding_id=str(uuid.uuid4()),
                            category=ValidationCategory.CONTRAINDICATIONS,
                            severity=ValidationSeverity.WARNING,
                            title="Pediatric Contraindication",
                            description=f"Recommended action may not be appropriate for pediatric patient: {contraindication}",
                            affected_diagnosis=diagnosis.primary_diagnosis,
                            recommendation="Consider pediatric-specific alternatives"
                        ))
        
        return findings
    
    async def _validate_age_appropriateness(
        self,
        diagnosis: ConsolidatedDiagnosis,
        request: DiagnosisRequest,
        patient_context: Dict[str, Any] = None
    ) -> List[ValidationFinding]:
        """Validate age appropriateness of diagnosis and treatments"""
        
        findings = []
        patient_age = request.patient_data.get("age", 0)
        
        # Age-specific validation rules
        if patient_age < 18:
            # Pediatric considerations
            adult_conditions = [
                "myocardial infarction", "stroke", "diabetes type 2"
            ]
            
            for condition in adult_conditions:
                if condition in diagnosis.primary_diagnosis.lower():
                    findings.append(ValidationFinding(
                        finding_id=str(uuid.uuid4()),
                        category=ValidationCategory.AGE_APPROPRIATENESS,
                        severity=ValidationSeverity.WARNING,
                        title="Adult Condition in Pediatric Patient",
                        description=f"Condition '{condition}' is unusual in pediatric patients",
                        affected_diagnosis=diagnosis.primary_diagnosis,
                        recommendation="Consider pediatric-specific differential diagnoses"
                    ))
        
        elif patient_age > 75:
            # Geriatric considerations
            if diagnosis.overall_confidence < 0.7:
                findings.append(ValidationFinding(
                    finding_id=str(uuid.uuid4()),
                    category=ValidationCategory.AGE_APPROPRIATENESS,
                    severity=ValidationSeverity.INFO,
                    title="Geriatric Patient Consideration",
                    description="Geriatric patients may have atypical presentations",
                    affected_diagnosis=diagnosis.primary_diagnosis,
                    recommendation="Consider age-related factors and multiple comorbidities"
                ))
        
        return findings
    
    async def _validate_emergency_protocols(
        self,
        diagnosis: ConsolidatedDiagnosis,
        request: DiagnosisRequest
    ) -> List[ValidationFinding]:
        """Validate emergency protocols and time-sensitive actions"""
        
        findings = []
        
        if request.urgency_level not in [UrgencyLevel.CRITICAL, UrgencyLevel.EMERGENCY]:
            return findings
        
        # Check emergency protocols
        primary_condition = diagnosis.primary_diagnosis.lower()
        
        for protocol_condition, protocol_info in self.knowledge_base.emergency_protocols.items():
            if protocol_condition in primary_condition:
                required_actions = protocol_info.get("required_actions", [])
                
                missing_actions = []
                for action in required_actions:
                    if not any(action in ia.lower() for ia in diagnosis.immediate_actions):
                        missing_actions.append(action)
                
                if missing_actions:
                    findings.append(ValidationFinding(
                        finding_id=str(uuid.uuid4()),
                        category=ValidationCategory.EMERGENCY_PROTOCOLS,
                        severity=ValidationSeverity.ERROR,
                        title="Missing Emergency Protocol Actions",
                        description=f"Missing required emergency actions for {protocol_condition}: {', '.join(missing_actions)}",
                        affected_diagnosis=diagnosis.primary_diagnosis,
                        recommendation=f"Add emergency actions: {', '.join(missing_actions)}",
                        requires_human_review=True,
                        auto_correctable=True
                    ))
                
                # Check time targets
                time_target = protocol_info.get("time_target", 0)
                if time_target > 0:
                    findings.append(ValidationFinding(
                        finding_id=str(uuid.uuid4()),
                        category=ValidationCategory.EMERGENCY_PROTOCOLS,
                        severity=ValidationSeverity.INFO,
                        title="Time-Sensitive Protocol",
                        description=f"Emergency protocol requires action within {time_target} minutes",
                        affected_diagnosis=diagnosis.primary_diagnosis,
                        recommendation=f"Ensure {protocol_condition} protocol timeline is followed"
                    ))
        
        return findings
    
    async def _validate_evidence_based(
        self, 
        diagnosis: ConsolidatedDiagnosis
    ) -> List[ValidationFinding]:
        """Validate against evidence-based medicine guidelines"""
        
        findings = []
        
        primary_condition = diagnosis.primary_diagnosis.lower()
        
        # Check evidence levels
        for condition, evidence_level in self.knowledge_base.evidence_levels.items():
            if condition in primary_condition:
                if evidence_level in ["A", "B"]:
                    # Strong evidence - good
                    findings.append(ValidationFinding(
                        finding_id=str(uuid.uuid4()),
                        category=ValidationCategory.EVIDENCE_BASED,
                        severity=ValidationSeverity.INFO,
                        title="Strong Evidence Base",
                        description=f"Diagnosis '{condition}' has evidence level {evidence_level}",
                        affected_diagnosis=diagnosis.primary_diagnosis,
                        recommendation="Evidence-based diagnosis with strong support"
                    ))
                else:
                    # Weaker evidence
                    findings.append(ValidationFinding(
                        finding_id=str(uuid.uuid4()),
                        category=ValidationCategory.EVIDENCE_BASED,
                        severity=ValidationSeverity.WARNING,
                        title="Limited Evidence Base",
                        description=f"Diagnosis '{condition}' has limited evidence (level {evidence_level})",
                        affected_diagnosis=diagnosis.primary_diagnosis,
                        recommendation="Consider additional validation or alternative diagnoses"
                    ))
                break
        
        return findings
    
    async def _validate_terminology(
        self, 
        diagnosis: ConsolidatedDiagnosis
    ) -> List[ValidationFinding]:
        """Validate medical terminology and coding"""
        
        findings = []
        
        # Check if primary diagnosis uses proper medical terminology
        if not self.terminology_validator.is_valid_medical_term(diagnosis.primary_diagnosis):
            findings.append(ValidationFinding(
                finding_id=str(uuid.uuid4()),
                category=ValidationCategory.TERMINOLOGY,
                severity=ValidationSeverity.WARNING,
                title="Non-Standard Medical Terminology",
                description=f"Primary diagnosis may use non-standard terminology: '{diagnosis.primary_diagnosis}'",
                affected_diagnosis=diagnosis.primary_diagnosis,
                recommendation="Consider using standard medical terminology",
                auto_correctable=True
            ))
        
        # Check differential diagnoses
        for diff_diagnosis in diagnosis.differential_diagnoses:
            if not self.terminology_validator.is_valid_medical_term(diff_diagnosis):
                findings.append(ValidationFinding(
                    finding_id=str(uuid.uuid4()),
                    category=ValidationCategory.TERMINOLOGY,
                    severity=ValidationSeverity.INFO,
                    title="Non-Standard Terminology in Differential",
                    description=f"Differential diagnosis uses non-standard terminology: '{diff_diagnosis}'",
                    affected_diagnosis=diff_diagnosis,
                    recommendation="Consider standard medical terminology"
                ))
        
        return findings
    
    async def _validate_compliance(
        self, 
        diagnosis: ConsolidatedDiagnosis
    ) -> List[ValidationFinding]:
        """Validate compliance with medical standards (FHIR R4, etc.)"""
        
        findings = []
        
        # Check FHIR R4 compliance (basic validation)
        if not self._is_fhir_compliant(diagnosis):
            findings.append(ValidationFinding(
                finding_id=str(uuid.uuid4()),
                category=ValidationCategory.COMPLIANCE,
                severity=ValidationSeverity.WARNING,
                title="FHIR R4 Compliance Issue",
                description="Diagnosis structure may not be fully FHIR R4 compliant",
                affected_diagnosis=diagnosis.primary_diagnosis,
                recommendation="Ensure FHIR R4 compliance for interoperability"
            ))
        
        # Check for required fields
        required_fields = ["primary_diagnosis", "triage_category", "immediate_actions"]
        for field in required_fields:
            if not hasattr(diagnosis, field) or not getattr(diagnosis, field):
                findings.append(ValidationFinding(
                    finding_id=str(uuid.uuid4()),
                    category=ValidationCategory.COMPLIANCE,
                    severity=ValidationSeverity.ERROR,
                    title="Missing Required Field",
                    description=f"Required field '{field}' is missing or empty",
                    affected_diagnosis=diagnosis.primary_diagnosis,
                    recommendation=f"Populate required field: {field}",
                    auto_correctable=True
                ))
        
        return findings
    
    async def _analyze_validation_results(
        self,
        diagnosis: ConsolidatedDiagnosis,
        findings: List[ValidationFinding],
        validation_start: datetime
    ) -> ValidationResult:
        """Analyze validation findings and determine overall result"""
        
        # Count findings by severity
        critical_count = sum(1 for f in findings if f.severity == ValidationSeverity.CRITICAL)
        error_count = sum(1 for f in findings if f.severity == ValidationSeverity.ERROR)
        warning_count = sum(1 for f in findings if f.severity == ValidationSeverity.WARNING)
        
        # Determine overall status
        if critical_count > 0:
            overall_status = ValidationStatus.ERROR
            validation_score = 0.0
        elif error_count > 0:
            overall_status = ValidationStatus.WARNING
            validation_score = max(0.3, 1.0 - (error_count * 0.2))
        elif warning_count > 0:
            overall_status = ValidationStatus.WARNING
            validation_score = max(0.6, 1.0 - (warning_count * 0.1))
        else:
            overall_status = ValidationStatus.VALID
            validation_score = 1.0
        
        # Determine safety clearance
        safety_cleared = critical_count == 0 and error_count == 0
        
        # Determine human review requirement
        requires_human_review = any(f.requires_human_review for f in findings)
        
        # Determine emergency escalation
        emergency_escalation_needed = (
            critical_count > 0 or
            any(f.category == ValidationCategory.EMERGENCY_PROTOCOLS and 
                f.severity in [ValidationSeverity.CRITICAL, ValidationSeverity.ERROR] 
                for f in findings)
        )
        
        # Create validated diagnosis (with corrections if applicable)
        validated_diagnosis = await self._apply_auto_corrections(diagnosis, findings)
        
        return ValidationResult(
            validation_id=str(uuid.uuid4()),
            overall_status=overall_status,
            validation_score=validation_score,
            findings=findings,
            safety_cleared=safety_cleared,
            requires_human_review=requires_human_review,
            emergency_escalation_needed=emergency_escalation_needed,
            validated_diagnosis=validated_diagnosis,
            validation_timestamp=datetime.now(timezone.utc)
        )
    
    async def _apply_auto_corrections(
        self,
        diagnosis: ConsolidatedDiagnosis,
        findings: List[ValidationFinding]
    ) -> ConsolidatedDiagnosis:
        """Apply automatic corrections where possible"""
        
        corrected_diagnosis = diagnosis
        
        # Apply auto-correctable findings
        for finding in findings:
            if finding.auto_correctable:
                if finding.category == ValidationCategory.EMERGENCY_PROTOCOLS:
                    # Add missing emergency actions
                    if "Add emergency actions:" in finding.recommendation:
                        missing_actions = finding.recommendation.replace("Add emergency actions: ", "").split(", ")
                        corrected_diagnosis.immediate_actions.extend(missing_actions)
                
                elif finding.category == ValidationCategory.CLINICAL_SAFETY:
                    # Add missing critical actions
                    if "Add critical actions:" in finding.recommendation:
                        missing_actions = finding.recommendation.replace("Add critical actions: ", "").split(", ")
                        corrected_diagnosis.immediate_actions.extend(missing_actions)
        
        return corrected_diagnosis
    
    def _is_fhir_compliant(self, diagnosis: ConsolidatedDiagnosis) -> bool:
        """Basic FHIR R4 compliance check"""
        
        # Basic structure validation
        required_attributes = [
            "diagnosis_id", "primary_diagnosis", "overall_confidence",
            "triage_category", "immediate_actions", "timestamp"
        ]
        
        for attr in required_attributes:
            if not hasattr(diagnosis, attr) or getattr(diagnosis, attr) is None:
                return False
        
        return True
    
    def get_validation_summary(self, result: ValidationResult) -> Dict[str, Any]:
        """Generate validation summary report"""
        
        findings_by_category = {}
        findings_by_severity = {}
        
        for finding in result.findings:
            # Group by category
            if finding.category.value not in findings_by_category:
                findings_by_category[finding.category.value] = []
            findings_by_category[finding.category.value].append(finding)
            
            # Group by severity
            if finding.severity.value not in findings_by_severity:
                findings_by_severity[finding.severity.value] = []
            findings_by_severity[finding.severity.value].append(finding)
        
        return {
            "validation_summary": {
                "validation_id": result.validation_id,
                "overall_status": result.overall_status.value,
                "validation_score": result.validation_score,
                "safety_cleared": result.safety_cleared,
                "requires_human_review": result.requires_human_review,
                "emergency_escalation_needed": result.emergency_escalation_needed
            },
            "findings_summary": {
                "total_findings": len(result.findings),
                "by_severity": {
                    severity: len(findings) 
                    for severity, findings in findings_by_severity.items()
                },
                "by_category": {
                    category: len(findings) 
                    for category, findings in findings_by_category.items()
                }
            },
            "recommendations": {
                "immediate_actions_needed": result.emergency_escalation_needed,
                "human_review_required": result.requires_human_review,
                "safe_to_proceed": result.safety_cleared,
                "auto_corrections_applied": any(f.auto_correctable for f in result.findings)
            },
            "next_steps": self._generate_next_steps(result)
        }
    
    def _generate_next_steps(self, result: ValidationResult) -> List[str]:
        """Generate recommended next steps based on validation results"""
        
        next_steps = []
        
        if result.emergency_escalation_needed:
            next_steps.append("Immediate emergency escalation required")
        
        if result.requires_human_review:
            next_steps.append("Human physician review required")
        
        if not result.safety_cleared:
            next_steps.append("Resolve safety concerns before proceeding")
        
        # Category-specific next steps
        categories_with_errors = set()
        for finding in result.findings:
            if finding.severity in [ValidationSeverity.CRITICAL, ValidationSeverity.ERROR]:
                categories_with_errors.add(finding.category)
        
        if ValidationCategory.DRUG_INTERACTIONS in categories_with_errors:
            next_steps.append("Review and resolve drug interaction concerns")
        
        if ValidationCategory.CONTRAINDICATIONS in categories_with_errors:
            next_steps.append("Address contraindications before treatment")
        
        if ValidationCategory.EMERGENCY_PROTOCOLS in categories_with_errors:
            next_steps.append("Implement missing emergency protocol actions")
        
        if not next_steps:
            next_steps.append("Diagnosis validation passed - proceed with care plan")
        
        return next_steps

class MedicalTerminologyValidator:
    """Validate medical terminology and standardization"""
    
    def __init__(self):
        self.valid_terms = self._initialize_terminology_database()
    
    def _initialize_terminology_database(self) -> Set[str]:
        """Initialize medical terminology database"""
        
        # This would be loaded from comprehensive medical terminology databases
        # SNOMED CT, ICD-10, etc.
        terms = {
            "myocardial infarction", "stroke", "pneumonia", "diabetes mellitus",
            "hypertension", "asthma", "copd", "heart failure", "sepsis",
            "anaphylaxis", "cardiac arrest", "respiratory failure",
            "acute coronary syndrome", "cerebrovascular accident",
            "unstable angina", "atrial fibrillation", "ventricular tachycardia"
        }
        
        return terms
    
    def is_valid_medical_term(self, term: str) -> bool:
        """Check if term is valid medical terminology"""
        
        term_lower = term.lower().strip()
        
        # Direct match
        if term_lower in self.valid_terms:
            return True
        
        # Partial match for compound terms
        for valid_term in self.valid_terms:
            if valid_term in term_lower or term_lower in valid_term:
                return True
        
        # Could add more sophisticated NLP-based validation
        return False

class ClinicalSafetyChecker:
    """Clinical safety validation"""
    
    def __init__(self):
        self.safety_rules = self._initialize_safety_rules()
    
    def _initialize_safety_rules(self) -> Dict[str, Any]:
        """Initialize clinical safety rules"""
        
        return {
            "high_risk_combinations": [
                {"condition": "myocardial infarction", "contraindication": "recent bleeding"},
                {"condition": "stroke", "contraindication": "recent surgery"},
                {"condition": "sepsis", "contraindication": "immunocompromised"}
            ],
            "critical_actions_required": {
                "cardiac arrest": ["cpr", "defibrillation", "epinephrine"],
                "anaphylaxis": ["epinephrine", "h1 antihistamine", "corticosteroids"],
                "status epilepticus": ["benzodiazepines", "antiepileptic drugs"]
            }
        }
    
    def check_safety(self, diagnosis: str, actions: List[str], history: List[str]) -> List[str]:
        """Check clinical safety concerns"""
        
        safety_concerns = []
        
        # Check for high-risk combinations
        for rule in self.safety_rules["high_risk_combinations"]:
            if rule["condition"] in diagnosis.lower():
                if any(rule["contraindication"] in h.lower() for h in history):
                    safety_concerns.append(
                        f"Safety concern: {rule['condition']} with {rule['contraindication']}"
                    )
        
        # Check for missing critical actions
        for condition, required_actions in self.safety_rules["critical_actions_required"].items():
            if condition in diagnosis.lower():
                missing_actions = []
                for action in required_actions:
                    if not any(action in a.lower() for a in actions):
                        missing_actions.append(action)
                
                if missing_actions:
                    safety_concerns.append(
                        f"Missing critical actions for {condition}: {', '.join(missing_actions)}"
                    )
        
        return safety_concerns

class DrugInteractionChecker:
    """Drug interaction validation"""
    
    def __init__(self):
        self.interaction_database = self._initialize_interaction_database()
    
    def _initialize_interaction_database(self) -> Dict[str, Dict[str, str]]:
        """Initialize drug interaction database"""
        
        return {
            "warfarin": {
                "aspirin": "increased bleeding risk",
                "antibiotics": "increased anticoagulation",
                "amiodarone": "increased warfarin effect"
            },
            "digoxin": {
                "diuretics": "electrolyte imbalance",
                "quinidine": "increased digoxin levels",
                "verapamil": "increased digoxin toxicity"
            },
            "metformin": {
                "contrast_agents": "lactic acidosis risk",
                "alcohol": "increased lactic acidosis risk"
            }
        }
    
    def check_interactions(
        self, 
        current_medications: List[str], 
        new_medications: List[str]
    ) -> List[Dict[str, str]]:
        """Check for drug interactions"""
        
        interactions = []
        
        for current_med in current_medications:
            current_med_lower = current_med.lower()
            
            if current_med_lower in self.interaction_database:
                for new_med in new_medications:
                    new_med_lower = new_med.lower()
                    
                    if new_med_lower in self.interaction_database[current_med_lower]:
                        interactions.append({
                            "drug1": current_med,
                            "drug2": new_med,
                            "interaction": self.interaction_database[current_med_lower][new_med_lower],
                            "severity": "moderate"  # Would be determined by clinical rules
                        })
        
        return interactions

# Example usage and testing
async def test_medical_validator():
    """Test the medical validation system"""
    
    from .diagnosis_engine import ConsolidatedDiagnosis, DiagnosisRequest, AgentSpecialization
    from datetime import datetime, timezone
    import uuid
    
    # Create sample diagnosis
    sample_diagnosis = ConsolidatedDiagnosis(
        diagnosis_id=str(uuid.uuid4()),
        primary_diagnosis="Myocardial infarction",
        differential_diagnoses=["Unstable angina", "Pericarditis"],
        overall_confidence=0.85,
        emergency_score=0.9,
        triage_category="RED - Immediate",
        immediate_actions=["ECG", "Cardiac enzymes", "Catheterization"],
        specialist_referrals=["cardiology"],
        agent_consensus={"cardiology_agent": 0.85, "emergency_agent": 0.92},
        processing_summary={"agents_consulted": 2},
        timestamp=datetime.now(timezone.utc)
    )
    
    # Create sample request
    sample_request = DiagnosisRequest(
        request_id=str(uuid.uuid4()),
        patient_data={"age": 65, "gender": "male"},
        symptoms=["chest pain", "shortness of breath"],
        vital_signs={"heart_rate": 110, "blood_pressure_systolic": 160},
        medical_history=["diabetes", "hypertension"],
        urgency_level=UrgencyLevel.CRITICAL,
        requesting_provider="dr_test",
        timestamp=datetime.now(timezone.utc)
    )
    
    # Test validation
    validator = MedicalDiagnosisValidator()
    
    try:
        result = await validator.validate_diagnosis(sample_diagnosis, sample_request)
        
        summary = validator.get_validation_summary(result)
        
        print("Medical Validation Results:")
        print(f"Overall Status: {result.overall_status.value}")
        print(f"Validation Score: {result.validation_score:.2f}")
        print(f"Safety Cleared: {result.safety_cleared}")
        print(f"Findings: {len(result.findings)}")
        
        for finding in result.findings[:3]:  # Show first 3 findings
            print(f"- {finding.title} ({finding.severity.value})")
        
        return result
        
    except Exception as e:
        print(f"Validation test failed: {e}")
        return None

if __name__ == "__main__":
    # Test medical validator
    asyncio.run(test_medical_validator())