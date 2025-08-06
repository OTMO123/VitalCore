"""
FHIR Security Labels Manager for Healthcare Platform V2.0

Advanced security label management for FHIR resources with automated classification,
dynamic labeling, and compliance validation for healthcare AI systems.
"""

import asyncio
import logging
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass

# FHIR imports
from fhir.resources import Resource, Patient, Observation, DiagnosticReport
from fhir.resources.meta import Meta
from fhir.resources.coding import Coding

# Internal imports
from .schemas import (
    SecurityLabel, SecurityClassification, SecurityLabelCategory,
    FHIRSecurityConfig, SecurityLabelRequest, SecurityAuditEvent
)
from ..audit_logger.service import AuditLogService
from ...core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

@dataclass
class ClassificationRule:
    """Security classification rule."""
    rule_id: str
    rule_name: str
    resource_types: List[str]
    conditions: Dict[str, Any]
    classification: SecurityClassification
    security_labels: List[str]
    priority: int
    active: bool = True

@dataclass
class LabelingContext:
    """Context for security labeling decisions."""
    resource_type: str
    resource_id: str
    data_elements: List[str]
    clinical_context: Dict[str, Any]
    patient_demographics: Dict[str, Any]
    organizational_policy: Dict[str, Any]
    regulatory_requirements: List[str]

class SecurityLabelManager:
    """
    Advanced security label manager for FHIR resources.
    
    Provides automated classification, dynamic labeling, and compliance
    validation for healthcare data with ML-enhanced sensitivity detection.
    """
    
    def __init__(self, config: FHIRSecurityConfig):
        self.config = config
        self.logger = logger.bind(component="SecurityLabelManager")
        
        # Core services
        self.audit_service = AuditLogService()
        
        # Security label definitions
        self.standard_labels = self._initialize_standard_labels()
        self.classification_rules = self._initialize_classification_rules()
        
        # Sensitivity detection patterns
        self.sensitivity_patterns = self._initialize_sensitivity_patterns()
        
        # Caching for performance
        self.label_cache: Dict[str, List[SecurityLabel]] = {}
        self.classification_cache: Dict[str, SecurityClassification] = {}
        
        self.logger.info("SecurityLabelManager initialized successfully")
    
    def _initialize_standard_labels(self) -> Dict[str, SecurityLabel]:
        """Initialize standard FHIR security labels."""
        return {
            # Confidentiality labels
            "unrestricted": SecurityLabel(
                system="http://terminology.hl7.org/CodeSystem/v3-Confidentiality",
                code="U",
                display="unrestricted",
                category=SecurityLabelCategory.CONFIDENTIALITY,
                classification=SecurityClassification.PUBLIC,
                handling_caveats=[],
                access_restrictions=[]
            ),
            "low": SecurityLabel(
                system="http://terminology.hl7.org/CodeSystem/v3-Confidentiality",
                code="L",
                display="low",
                category=SecurityLabelCategory.CONFIDENTIALITY,
                classification=SecurityClassification.INTERNAL,
                handling_caveats=["internal_use_only"],
                access_restrictions=["authenticated_users"]
            ),
            "normal": SecurityLabel(
                system="http://terminology.hl7.org/CodeSystem/v3-Confidentiality",
                code="N",
                display="normal",
                category=SecurityLabelCategory.CONFIDENTIALITY,
                classification=SecurityClassification.CONFIDENTIAL,
                handling_caveats=["encrypt_at_rest", "audit_access"],
                access_restrictions=["authorized_users_only", "purpose_limitation"]
            ),
            "restricted": SecurityLabel(
                system="http://terminology.hl7.org/CodeSystem/v3-Confidentiality",
                code="R",
                display="restricted",
                category=SecurityLabelCategory.CONFIDENTIALITY,
                classification=SecurityClassification.RESTRICTED,
                handling_caveats=["encrypt_at_rest", "audit_access", "require_consent", "dual_authorization"],
                access_restrictions=["specialized_authorization", "purpose_limitation", "time_limited_access"]
            ),
            "very_restricted": SecurityLabel(
                system="http://terminology.hl7.org/CodeSystem/v3-Confidentiality",
                code="V",
                display="very restricted",
                category=SecurityLabelCategory.CONFIDENTIALITY,
                classification=SecurityClassification.TOP_SECRET,
                handling_caveats=["encrypt_at_rest", "audit_access", "require_consent", "dual_authorization", "special_handling"],
                access_restrictions=["highest_authorization", "purpose_limitation", "time_limited_access", "supervisor_approval"]
            ),
            
            # Compartment labels
            "psychiatry": SecurityLabel(
                system="http://terminology.hl7.org/CodeSystem/v3-ActCode",
                code="PSY",
                display="psychiatry",
                category=SecurityLabelCategory.COMPARTMENT,
                classification=SecurityClassification.RESTRICTED,
                handling_caveats=["specialized_consent", "mental_health_protections"],
                access_restrictions=["psychiatrist_authorization", "mental_health_clearance"]
            ),
            "substance_abuse": SecurityLabel(
                system="http://terminology.hl7.org/CodeSystem/v3-ActCode",
                code="SUD",
                display="substance use disorder",
                category=SecurityLabelCategory.COMPARTMENT,
                classification=SecurityClassification.RESTRICTED,
                handling_caveats=["specialized_consent", "substance_abuse_protections"],
                access_restrictions=["addiction_specialist_authorization", "42_cfr_compliance"]
            ),
            "genetic": SecurityLabel(
                system="http://terminology.hl7.org/CodeSystem/v3-ActCode",
                code="GENETIC",
                display="genetic information",
                category=SecurityLabelCategory.COMPARTMENT,
                classification=SecurityClassification.TOP_SECRET,
                handling_caveats=["genetic_counselor_required", "anti_discrimination_protections"],
                access_restrictions=["genetic_authorization", "no_insurance_discrimination", "family_notification_protocols"]
            ),
            "hiv": SecurityLabel(
                system="http://terminology.hl7.org/CodeSystem/v3-ActCode",
                code="HIV",
                display="HIV status",
                category=SecurityLabelCategory.COMPARTMENT,
                classification=SecurityClassification.RESTRICTED,
                handling_caveats=["hiv_specific_consent", "anti_discrimination_protections"],
                access_restrictions=["infectious_disease_authorization", "partner_notification_protocols"]
            ),
            
            # Purpose labels
            "treatment": SecurityLabel(
                system="http://terminology.hl7.org/CodeSystem/v3-ActReason",
                code="TREAT",
                display="treatment",
                category=SecurityLabelCategory.PURPOSE,
                classification=SecurityClassification.CONFIDENTIAL,
                handling_caveats=["clinical_use_only"],
                access_restrictions=["treating_provider_access"]
            ),
            "research": SecurityLabel(
                system="http://terminology.hl7.org/CodeSystem/v3-ActReason",
                code="RESEARCH",
                display="research",
                category=SecurityLabelCategory.PURPOSE,
                classification=SecurityClassification.CONFIDENTIAL,
                handling_caveats=["irb_approval_required", "anonymization_required"],
                access_restrictions=["research_authorization", "approved_study_only"]
            ),
            "quality": SecurityLabel(
                system="http://terminology.hl7.org/CodeSystem/v3-ActReason",
                code="QUAL",
                display="quality assurance",
                category=SecurityLabelCategory.PURPOSE,
                classification=SecurityClassification.INTERNAL,
                handling_caveats=["quality_improvement_only"],
                access_restrictions=["quality_team_access"]
            ),
            
            # Handling labels
            "no_redisclosure": SecurityLabel(
                system="http://terminology.hl7.org/CodeSystem/v3-ActCode",
                code="NODSCLCD",
                display="no disclosure without consent",
                category=SecurityLabelCategory.HANDLING,
                classification=SecurityClassification.RESTRICTED,
                handling_caveats=["explicit_consent_required"],
                access_restrictions=["no_external_sharing"]
            ),
            "encrypt": SecurityLabel(
                system="http://terminology.hl7.org/CodeSystem/v3-ObservationValue",
                code="ENCRYPT",
                display="encrypt",
                category=SecurityLabelCategory.HANDLING,
                classification=SecurityClassification.CONFIDENTIAL,
                handling_caveats=["encryption_required"],
                access_restrictions=["encrypted_transmission_only"]
            )
        }
    
    def _initialize_classification_rules(self) -> List[ClassificationRule]:
        """Initialize automated classification rules."""
        return [
            # High-sensitivity resource types
            ClassificationRule(
                rule_id="genetic_data",
                rule_name="Genetic Information Classification",
                resource_types=["Observation", "DiagnosticReport"],
                conditions={
                    "category_codes": ["genetics", "genomics"],
                    "component_codes": ["LA6114-0", "LA6115-7"],  # LOINC genetic codes
                    "value_patterns": ["chromosome", "allele", "mutation", "variant"]
                },
                classification=SecurityClassification.TOP_SECRET,
                security_labels=["genetic", "very_restricted", "no_redisclosure"],
                priority=1
            ),
            ClassificationRule(
                rule_id="mental_health",
                rule_name="Mental Health Classification",
                resource_types=["Observation", "Condition", "Procedure"],
                conditions={
                    "category_codes": ["psychiatry", "psychology", "mental-health"],
                    "snomed_codes": ["74732009", "192080009", "35489007"],  # Mental health SNOMED
                    "icd10_codes": ["F20", "F31", "F32", "F33", "F84"]
                },
                classification=SecurityClassification.RESTRICTED,
                security_labels=["psychiatry", "restricted", "specialized_consent"],
                priority=2
            ),
            ClassificationRule(
                rule_id="substance_abuse",
                rule_name="Substance Abuse Classification",
                resource_types=["Observation", "Condition", "Procedure"],
                conditions={
                    "category_codes": ["substance-abuse", "addiction"],
                    "snomed_codes": ["191816009", "26416006", "228388006"],
                    "icd10_codes": ["F10", "F11", "F12", "F13", "F14", "F15", "F16", "F17", "F18", "F19"]
                },
                classification=SecurityClassification.RESTRICTED,
                security_labels=["substance_abuse", "restricted", "42_cfr_compliance"],
                priority=2
            ),
            ClassificationRule(
                rule_id="hiv_status",
                rule_name="HIV Status Classification",
                resource_types=["Observation", "Condition", "DiagnosticReport"],
                conditions={
                    "loinc_codes": ["33747-0", "75622-1", "25835-0"],  # HIV tests
                    "snomed_codes": ["86406008", "165816005"],  # HIV status
                    "value_patterns": ["HIV", "human immunodeficiency virus"]
                },
                classification=SecurityClassification.RESTRICTED,
                security_labels=["hiv", "restricted", "anti_discrimination"],
                priority=2
            ),
            ClassificationRule(
                rule_id="pediatric_data",
                rule_name="Pediatric Data Classification",
                resource_types=["Patient", "Observation", "Condition"],
                conditions={
                    "age_range": {"min": 0, "max": 18},
                    "category_codes": ["pediatric", "neonatal"],
                    "special_populations": ["minor", "adolescent"]
                },
                classification=SecurityClassification.RESTRICTED,
                security_labels=["pediatric", "restricted", "parental_consent"],
                priority=3
            ),
            ClassificationRule(
                rule_id="reproductive_health",
                rule_name="Reproductive Health Classification",
                resource_types=["Observation", "Procedure", "Condition"],
                conditions={
                    "category_codes": ["reproductive-health", "pregnancy", "contraception"],
                    "snomed_codes": ["169564007", "118185001", "182855006"],
                    "procedure_codes": ["59400", "59510", "59514"]  # CPT pregnancy codes
                },
                classification=SecurityClassification.RESTRICTED,
                security_labels=["reproductive_health", "restricted", "specialized_consent"],
                priority=3
            ),
            # Standard sensitivity rules
            ClassificationRule(
                rule_id="clinical_data",
                rule_name="Standard Clinical Data",
                resource_types=["Observation", "Condition", "Procedure"],
                conditions={
                    "default_clinical": True
                },
                classification=SecurityClassification.CONFIDENTIAL,
                security_labels=["normal", "treatment"],
                priority=5
            ),
            ClassificationRule(
                rule_id="administrative_data",
                rule_name="Administrative Data",
                resource_types=["Appointment", "Schedule", "Coverage"],
                conditions={
                    "administrative": True
                },
                classification=SecurityClassification.INTERNAL,
                security_labels=["low", "administrative"],
                priority=6
            )
        ]
    
    def _initialize_sensitivity_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns for sensitive data detection."""
        return {
            "genetic_keywords": [
                "chromosome", "allele", "mutation", "variant", "gene", "genomic",
                "hereditary", "inherited", "familial", "carrier", "genotype",
                "DNA", "RNA", "nucleotide", "sequence", "polymorphism"
            ],
            "mental_health_keywords": [
                "depression", "anxiety", "bipolar", "schizophrenia", "psychosis",
                "suicide", "self-harm", "psychiatric", "therapy", "counseling",
                "antidepressant", "antipsychotic", "mood disorder", "PTSD"
            ],
            "substance_abuse_keywords": [
                "alcohol", "drug", "substance", "addiction", "dependency",
                "withdrawal", "detox", "rehabilitation", "methadone", "suboxone",
                "cocaine", "heroin", "marijuana", "opioid", "abuse"
            ],
            "reproductive_keywords": [
                "pregnancy", "contraception", "abortion", "fertility", "reproductive",
                "menstrual", "ovulation", "conception", "prenatal", "obstetric",
                "gynecologic", "birth control", "family planning"
            ],
            "sensitive_identifiers": [
                "SSN", "social security", "passport", "license", "credit card",
                "bank account", "financial", "emergency contact", "next of kin"
            ]
        }
    
    async def classify_resource_sensitivity(
        self, 
        resource: Resource, 
        context: LabelingContext
    ) -> Tuple[SecurityClassification, List[str]]:
        """
        Classify resource sensitivity level using ML-enhanced analysis.
        
        Args:
            resource: FHIR resource to classify
            context: Classification context
            
        Returns:
            Tuple of (classification, applied_rule_ids)
        """
        try:
            # Check cache first
            cache_key = f"{resource.resource_type}_{getattr(resource, 'id', 'unknown')}"
            if cache_key in self.classification_cache:
                cached_classification = self.classification_cache[cache_key]
                return cached_classification, ["cached"]
            
            applied_rules = []
            highest_classification = SecurityClassification.PUBLIC
            
            # Apply classification rules
            for rule in sorted(self.classification_rules, key=lambda r: r.priority):
                if not rule.active:
                    continue
                
                if resource.resource_type in rule.resource_types:
                    if await self._evaluate_classification_rule(resource, rule, context):
                        applied_rules.append(rule.rule_id)
                        
                        # Update to highest classification
                        if self._get_classification_level(rule.classification) > self._get_classification_level(highest_classification):
                            highest_classification = rule.classification
            
            # ML-enhanced sensitivity detection
            ml_classification = await self._ml_sensitivity_analysis(resource, context)
            if self._get_classification_level(ml_classification) > self._get_classification_level(highest_classification):
                highest_classification = ml_classification
                applied_rules.append("ml_enhanced")
            
            # Content-based sensitivity detection
            content_classification = await self._analyze_content_sensitivity(resource)
            if self._get_classification_level(content_classification) > self._get_classification_level(highest_classification):
                highest_classification = content_classification
                applied_rules.append("content_analysis")
            
            # Cache result
            self.classification_cache[cache_key] = highest_classification
            
            self.logger.info(
                "Resource sensitivity classified",
                resource_type=resource.resource_type,
                resource_id=getattr(resource, 'id', 'unknown'),
                classification=highest_classification.value,
                applied_rules=applied_rules
            )
            
            return highest_classification, applied_rules
            
        except Exception as e:
            self.logger.error(f"Failed to classify resource sensitivity: {str(e)}")
            # Default to highest security for safety
            return SecurityClassification.RESTRICTED, ["error_default"]
    
    async def apply_security_labels(
        self, 
        resource: Resource, 
        classification: SecurityClassification,
        additional_labels: List[str] = None
    ) -> List[SecurityLabel]:
        """
        Apply appropriate security labels to a FHIR resource.
        
        Args:
            resource: FHIR resource to label
            classification: Security classification level
            additional_labels: Additional label names to apply
            
        Returns:
            List of applied security labels
        """
        try:
            applied_labels = []
            
            # Get base confidentiality label
            confidentiality_label = await self._get_confidentiality_label(classification)
            if confidentiality_label:
                applied_labels.append(confidentiality_label)
            
            # Get resource-specific labels
            resource_labels = await self._get_resource_specific_labels(resource, classification)
            applied_labels.extend(resource_labels)
            
            # Add additional labels if specified
            if additional_labels:
                for label_name in additional_labels:
                    if label_name in self.standard_labels:
                        applied_labels.append(self.standard_labels[label_name])
            
            # Apply purpose-based labels
            purpose_labels = await self._get_purpose_labels(resource)
            applied_labels.extend(purpose_labels)
            
            # Apply handling instruction labels
            handling_labels = await self._get_handling_labels(classification)
            applied_labels.extend(handling_labels)
            
            # Apply labels to resource metadata
            if not resource.meta:
                resource.meta = Meta()
            
            if not resource.meta.security:
                resource.meta.security = []
            
            # Convert to FHIR Coding objects and add to resource
            for label in applied_labels:
                coding = Coding(
                    system=label.system,
                    code=label.code,
                    display=label.display
                )
                resource.meta.security.append(coding)
            
            # Audit labeling action
            await self._audit_security_labeling(resource, applied_labels, classification)
            
            self.logger.info(
                "Security labels applied",
                resource_type=resource.resource_type,
                resource_id=getattr(resource, 'id', 'unknown'),
                label_count=len(applied_labels),
                classification=classification.value
            )
            
            return applied_labels
            
        except Exception as e:
            self.logger.error(f"Failed to apply security labels: {str(e)}")
            raise
    
    async def validate_label_compliance(
        self, 
        resource: Resource, 
        required_standards: List[str] = None
    ) -> Dict[str, Any]:
        """
        Validate security label compliance with regulatory standards.
        
        Args:
            resource: FHIR resource to validate
            required_standards: List of required compliance standards
            
        Returns:
            Validation result dictionary
        """
        try:
            if not required_standards:
                required_standards = ["HIPAA", "FHIR_R4", "SOC2"]
            
            validation_result = {
                "compliant": True,
                "violations": [],
                "warnings": [],
                "recommendations": [],
                "compliance_score": 1.0
            }
            
            # Check if resource has security labels
            if not resource.meta or not resource.meta.security:
                validation_result["compliant"] = False
                validation_result["violations"].append("Missing required security labels")
                validation_result["compliance_score"] -= 0.5
                validation_result["recommendations"].append("Apply appropriate security labels")
            
            # Validate label completeness
            if resource.meta and resource.meta.security:
                label_validation = await self._validate_label_completeness(resource)
                if not label_validation["complete"]:
                    validation_result["warnings"].extend(label_validation["missing_categories"])
                    validation_result["compliance_score"] -= 0.2
            
            # HIPAA compliance validation
            if "HIPAA" in required_standards:
                hipaa_validation = await self._validate_hipaa_compliance(resource)
                if not hipaa_validation["compliant"]:
                    validation_result["compliant"] = False
                    validation_result["violations"].extend(hipaa_validation["violations"])
                    validation_result["compliance_score"] -= 0.3
            
            # FHIR R4 compliance validation
            if "FHIR_R4" in required_standards:
                fhir_validation = await self._validate_fhir_compliance(resource)
                if not fhir_validation["compliant"]:
                    validation_result["violations"].extend(fhir_validation["violations"])
                    validation_result["compliance_score"] -= 0.2
            
            # SOC2 compliance validation
            if "SOC2" in required_standards:
                soc2_validation = await self._validate_soc2_compliance(resource)
                if not soc2_validation["compliant"]:
                    validation_result["violations"].extend(soc2_validation["violations"])
                    validation_result["compliance_score"] -= 0.2
            
            # Ensure compliance score doesn't go below 0
            validation_result["compliance_score"] = max(0.0, validation_result["compliance_score"])
            
            self.logger.info(
                "Label compliance validated",
                resource_type=resource.resource_type,
                compliant=validation_result["compliant"],
                compliance_score=validation_result["compliance_score"],
                violations_count=len(validation_result["violations"])
            )
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Failed to validate label compliance: {str(e)}")
            raise
    
    async def get_dynamic_labels(
        self, 
        resource: Resource, 
        user_context: Dict[str, Any],
        access_purpose: str
    ) -> List[SecurityLabel]:
        """
        Generate dynamic security labels based on context.
        
        Args:
            resource: FHIR resource
            user_context: User access context
            access_purpose: Purpose of access
            
        Returns:
            List of dynamic security labels
        """
        try:
            dynamic_labels = []
            
            # Time-based labels
            current_hour = datetime.utcnow().hour
            if not (8 <= current_hour <= 17):  # Outside business hours
                after_hours_label = SecurityLabel(
                    system="http://healthcare-platform.org/security-labels",
                    code="AFTER_HOURS",
                    display="After Hours Access",
                    category=SecurityLabelCategory.HANDLING,
                    classification=SecurityClassification.RESTRICTED,
                    handling_caveats=["supervisor_notification", "enhanced_audit"],
                    access_restrictions=["emergency_justification_required"]
                )
                dynamic_labels.append(after_hours_label)
            
            # Location-based labels
            user_location = user_context.get("geographic_location")
            if user_location and user_location != "primary_facility":
                remote_access_label = SecurityLabel(
                    system="http://healthcare-platform.org/security-labels",
                    code="REMOTE_ACCESS",
                    display="Remote Access",
                    category=SecurityLabelCategory.HANDLING,
                    classification=SecurityClassification.CONFIDENTIAL,
                    handling_caveats=["secure_connection_required", "enhanced_authentication"],
                    access_restrictions=["vpn_required"]
                )
                dynamic_labels.append(remote_access_label)
            
            # Purpose-based dynamic labels
            if access_purpose == "emergency":
                emergency_label = SecurityLabel(
                    system="http://healthcare-platform.org/security-labels",
                    code="EMERGENCY_ACCESS",
                    display="Emergency Access",
                    category=SecurityLabelCategory.PURPOSE,
                    classification=SecurityClassification.CONFIDENTIAL,
                    handling_caveats=["break_glass_audit", "supervisor_review"],
                    access_restrictions=["clinical_justification_required"]
                )
                dynamic_labels.append(emergency_label)
            
            # User role-based labels
            user_role = user_context.get("user_role")
            if user_role in ["student", "intern", "resident"]:
                trainee_label = SecurityLabel(
                    system="http://healthcare-platform.org/security-labels",
                    code="TRAINEE_ACCESS",
                    display="Trainee Access",
                    category=SecurityLabelCategory.HANDLING,
                    classification=SecurityClassification.CONFIDENTIAL,
                    handling_caveats=["supervisor_oversight", "educational_purpose"],
                    access_restrictions=["attending_supervision_required"]
                )
                dynamic_labels.append(trainee_label)
            
            self.logger.info(
                "Dynamic labels generated",
                resource_type=resource.resource_type,
                user_role=user_role,
                access_purpose=access_purpose,
                dynamic_labels_count=len(dynamic_labels)
            )
            
            return dynamic_labels
            
        except Exception as e:
            self.logger.error(f"Failed to generate dynamic labels: {str(e)}")
            return []
    
    # Helper methods
    
    async def _evaluate_classification_rule(
        self, 
        resource: Resource, 
        rule: ClassificationRule, 
        context: LabelingContext
    ) -> bool:
        """Evaluate if a classification rule applies to a resource."""
        try:
            conditions = rule.conditions
            
            # Check category codes
            if "category_codes" in conditions:
                if hasattr(resource, 'category') and resource.category:
                    resource_categories = []
                    for category in resource.category:
                        if category.coding:
                            resource_categories.extend([coding.code for coding in category.coding])
                    
                    if any(code in resource_categories for code in conditions["category_codes"]):
                        return True
            
            # Check SNOMED codes
            if "snomed_codes" in conditions:
                if hasattr(resource, 'code') and resource.code and resource.code.coding:
                    resource_codes = [coding.code for coding in resource.code.coding 
                                    if coding.system and "snomed" in coding.system.lower()]
                    
                    if any(code in resource_codes for code in conditions["snomed_codes"]):
                        return True
            
            # Check LOINC codes
            if "loinc_codes" in conditions:
                if hasattr(resource, 'code') and resource.code and resource.code.coding:
                    resource_codes = [coding.code for coding in resource.code.coding 
                                    if coding.system and "loinc" in coding.system.lower()]
                    
                    if any(code in resource_codes for code in conditions["loinc_codes"]):
                        return True
            
            # Check ICD-10 codes
            if "icd10_codes" in conditions:
                if hasattr(resource, 'code') and resource.code and resource.code.coding:
                    resource_codes = [coding.code for coding in resource.code.coding 
                                    if coding.system and "icd" in coding.system.lower()]
                    
                    if any(icd_code in code for code in resource_codes for icd_code in conditions["icd10_codes"]):
                        return True
            
            # Check value patterns
            if "value_patterns" in conditions:
                resource_text = json.dumps(resource.dict()).lower()
                if any(pattern.lower() in resource_text for pattern in conditions["value_patterns"]):
                    return True
            
            # Check age range for patients
            if "age_range" in conditions and resource.resource_type == "Patient":
                if hasattr(resource, 'birthDate') and resource.birthDate:
                    age = (datetime.now().date() - resource.birthDate).days // 365
                    age_range = conditions["age_range"]
                    if age_range["min"] <= age <= age_range["max"]:
                        return True
            
            # Check default conditions
            if conditions.get("default_clinical", False) and resource.resource_type in ["Observation", "Condition", "Procedure"]:
                return True
            
            if conditions.get("administrative", False) and resource.resource_type in ["Appointment", "Schedule", "Coverage"]:
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to evaluate classification rule: {str(e)}")
            return False
    
    async def _ml_sensitivity_analysis(
        self, 
        resource: Resource, 
        context: LabelingContext
    ) -> SecurityClassification:
        """Perform ML-enhanced sensitivity analysis."""
        # Placeholder for ML model implementation
        # In production, this would use trained models for sensitivity detection
        
        try:
            # Extract text content from resource
            resource_text = json.dumps(resource.dict()).lower()
            
            # Check for sensitive keywords
            genetic_score = sum(1 for keyword in self.sensitivity_patterns["genetic_keywords"] 
                              if keyword.lower() in resource_text)
            mental_health_score = sum(1 for keyword in self.sensitivity_patterns["mental_health_keywords"] 
                                    if keyword.lower() in resource_text)
            substance_abuse_score = sum(1 for keyword in self.sensitivity_patterns["substance_abuse_keywords"] 
                                      if keyword.lower() in resource_text)
            
            # Determine classification based on scores
            if genetic_score >= 2:
                return SecurityClassification.TOP_SECRET
            elif mental_health_score >= 2 or substance_abuse_score >= 2:
                return SecurityClassification.RESTRICTED
            elif genetic_score >= 1 or mental_health_score >= 1 or substance_abuse_score >= 1:
                return SecurityClassification.CONFIDENTIAL
            else:
                return SecurityClassification.INTERNAL
                
        except Exception as e:
            self.logger.error(f"ML sensitivity analysis failed: {str(e)}")
            return SecurityClassification.CONFIDENTIAL
    
    async def _analyze_content_sensitivity(self, resource: Resource) -> SecurityClassification:
        """Analyze resource content for sensitive information."""
        try:
            resource_text = json.dumps(resource.dict()).lower()
            
            # Check for sensitive identifiers
            sensitive_id_count = sum(1 for pattern in self.sensitivity_patterns["sensitive_identifiers"] 
                                   if pattern.lower() in resource_text)
            
            if sensitive_id_count >= 2:
                return SecurityClassification.RESTRICTED
            elif sensitive_id_count >= 1:
                return SecurityClassification.CONFIDENTIAL
            else:
                return SecurityClassification.INTERNAL
                
        except Exception as e:
            self.logger.error(f"Content sensitivity analysis failed: {str(e)}")
            return SecurityClassification.CONFIDENTIAL
    
    def _get_classification_level(self, classification: SecurityClassification) -> int:
        """Get numeric level for classification comparison."""
        levels = {
            SecurityClassification.PUBLIC: 1,
            SecurityClassification.INTERNAL: 2,
            SecurityClassification.CONFIDENTIAL: 3,
            SecurityClassification.RESTRICTED: 4,
            SecurityClassification.TOP_SECRET: 5
        }
        return levels.get(classification, 3)
    
    async def _get_confidentiality_label(self, classification: SecurityClassification) -> Optional[SecurityLabel]:
        """Get appropriate confidentiality label for classification."""
        mapping = {
            SecurityClassification.PUBLIC: "unrestricted",
            SecurityClassification.INTERNAL: "low",
            SecurityClassification.CONFIDENTIAL: "normal",
            SecurityClassification.RESTRICTED: "restricted",
            SecurityClassification.TOP_SECRET: "very_restricted"
        }
        
        label_name = mapping.get(classification)
        return self.standard_labels.get(label_name) if label_name else None
    
    async def _get_resource_specific_labels(
        self, 
        resource: Resource, 
        classification: SecurityClassification
    ) -> List[SecurityLabel]:
        """Get resource-specific security labels."""
        labels = []
        
        # Add compartment labels based on content analysis
        if classification in [SecurityClassification.RESTRICTED, SecurityClassification.TOP_SECRET]:
            resource_text = json.dumps(resource.dict()).lower()
            
            # Check for specific compartments
            if any(keyword in resource_text for keyword in ["psychiatric", "mental", "depression", "anxiety"]):
                labels.append(self.standard_labels["psychiatry"])
            
            if any(keyword in resource_text for keyword in ["genetic", "chromosome", "dna", "gene"]):
                labels.append(self.standard_labels["genetic"])
            
            if any(keyword in resource_text for keyword in ["substance", "addiction", "drug", "alcohol"]):
                labels.append(self.standard_labels["substance_abuse"])
            
            if any(keyword in resource_text for keyword in ["hiv", "aids", "human immunodeficiency"]):
                labels.append(self.standard_labels["hiv"])
        
        return labels
    
    async def _get_purpose_labels(self, resource: Resource) -> List[SecurityLabel]:
        """Get purpose-based labels."""
        # Default to treatment purpose for clinical resources
        if resource.resource_type in ["Observation", "Condition", "Procedure", "DiagnosticReport"]:
            return [self.standard_labels["treatment"]]
        
        return []
    
    async def _get_handling_labels(self, classification: SecurityClassification) -> List[SecurityLabel]:
        """Get handling instruction labels."""
        labels = []
        
        if classification in [SecurityClassification.RESTRICTED, SecurityClassification.TOP_SECRET]:
            labels.append(self.standard_labels["no_redisclosure"])
        
        if classification in [SecurityClassification.CONFIDENTIAL, SecurityClassification.RESTRICTED, SecurityClassification.TOP_SECRET]:
            labels.append(self.standard_labels["encrypt"])
        
        return labels
    
    async def _audit_security_labeling(
        self, 
        resource: Resource, 
        labels: List[SecurityLabel], 
        classification: SecurityClassification
    ):
        """Audit security labeling actions."""
        try:
            audit_event = SecurityAuditEvent(
                event_type="security_labeling",
                severity="info",
                event_details={
                    "resource_type": resource.resource_type,
                    "resource_id": getattr(resource, 'id', 'unknown'),
                    "classification": classification.value,
                    "labels_applied": [label.code for label in labels],
                    "label_count": len(labels)
                },
                outcome="success"
            )
            
            await self.audit_service.log_security_event(audit_event.dict())
            
        except Exception as e:
            self.logger.error(f"Failed to audit security labeling: {str(e)}")
    
    async def _validate_label_completeness(self, resource: Resource) -> Dict[str, Any]:
        """Validate completeness of security labels."""
        required_categories = [SecurityLabelCategory.CONFIDENTIALITY]
        present_categories = set()
        
        if resource.meta and resource.meta.security:
            for coding in resource.meta.security:
                # Determine category based on system and code
                if "Confidentiality" in coding.system:
                    present_categories.add(SecurityLabelCategory.CONFIDENTIALITY)
                elif "ActCode" in coding.system:
                    present_categories.add(SecurityLabelCategory.COMPARTMENT)
                elif "ActReason" in coding.system:
                    present_categories.add(SecurityLabelCategory.PURPOSE)
        
        missing_categories = [cat.value for cat in required_categories if cat not in present_categories]
        
        return {
            "complete": len(missing_categories) == 0,
            "missing_categories": missing_categories,
            "present_categories": [cat.value for cat in present_categories]
        }
    
    async def _validate_hipaa_compliance(self, resource: Resource) -> Dict[str, Any]:
        """Validate HIPAA compliance for security labels."""
        violations = []
        
        # Check for minimum required security
        if not resource.meta or not resource.meta.security:
            violations.append("HIPAA requires minimum security labeling for PHI")
        
        # Check for audit requirements
        has_audit_label = False
        if resource.meta and resource.meta.security:
            for coding in resource.meta.security:
                if "audit" in coding.display.lower():
                    has_audit_label = True
                    break
        
        if not has_audit_label:
            violations.append("HIPAA requires audit trail labeling for PHI access")
        
        return {
            "compliant": len(violations) == 0,
            "violations": violations
        }
    
    async def _validate_fhir_compliance(self, resource: Resource) -> Dict[str, Any]:
        """Validate FHIR R4 compliance for security labels."""
        violations = []
        
        if resource.meta and resource.meta.security:
            for coding in resource.meta.security:
                # Validate required fields
                if not coding.system:
                    violations.append("FHIR security labels require system URI")
                if not coding.code:
                    violations.append("FHIR security labels require code")
                
                # Validate system URIs are proper
                if coding.system and not coding.system.startswith("http"):
                    violations.append("FHIR security label systems must be valid URIs")
        
        return {
            "compliant": len(violations) == 0,
            "violations": violations
        }
    
    async def _validate_soc2_compliance(self, resource: Resource) -> Dict[str, Any]:
        """Validate SOC2 compliance for security labels."""
        violations = []
        
        # SOC2 requires data classification
        if not resource.meta or not resource.meta.security:
            violations.append("SOC2 requires data classification labels")
        
        # Check for encryption requirements
        has_encryption_indicator = False
        if resource.meta and resource.meta.security:
            for coding in resource.meta.security:
                if "encrypt" in coding.code.lower() or "encrypt" in coding.display.lower():
                    has_encryption_indicator = True
                    break
        
        # High sensitivity data should have encryption labels
        if not has_encryption_indicator:
            # This is a warning rather than violation for flexibility
            pass
        
        return {
            "compliant": len(violations) == 0,
            "violations": violations
        }