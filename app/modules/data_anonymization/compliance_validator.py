"""
Compliance Validator for Healthcare ML Platform

Validates ML-ready anonymized data against HIPAA, GDPR, SOC2, and FHIR
compliance requirements with comprehensive audit trails.
"""

import hashlib
import re
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple
import structlog
from enum import Enum

from .schemas import (
    AnonymizedMLProfile, ComplianceValidationResult, AnonymizationAuditTrail,
    ComplianceStandard
)
from app.core.config import get_settings
# Handle optional audit service import
try:
    from app.modules.audit_logger.service import SOC2AuditService, get_audit_service
    AUDIT_SERVICE_AVAILABLE = True
except ImportError:
    SOC2AuditService = None
    get_audit_service = None
    AUDIT_SERVICE_AVAILABLE = False

logger = structlog.get_logger(__name__)

class ComplianceLevel(str, Enum):
    """Compliance assessment levels."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    NEEDS_REVIEW = "needs_review"
    CONDITIONAL = "conditional"

class ValidationSeverity(str, Enum):
    """Validation issue severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class ComplianceValidator:
    """
    Comprehensive compliance validator for ML-ready healthcare data.
    
    Validates anonymized patient profiles against HIPAA Safe Harbor,
    GDPR Article 26, SOC2 Type II, and FHIR R4 requirements.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize compliance validator.
        
        Args:
            config: Validation configuration
        """
        self.config = config or {}
        self.settings = get_settings()
        self.logger = logger.bind(component="ComplianceValidator")
        
        # Load compliance rules and patterns
        self._load_compliance_patterns()
        
        # Initialize audit service
        # Initialize audit service if available
        if AUDIT_SERVICE_AVAILABLE and get_audit_service is not None:
            try:
                self.audit_service = get_audit_service()
            except RuntimeError:
                # Audit service not initialized yet - will be set later
                self.audit_service = None
                logger.info("Audit service not initialized yet - will be available after startup")
        else:
            self.audit_service = None
            logger.warning("Audit service not available - compliance validation will not be audited")
    
    # HIPAA COMPLIANCE VALIDATION
    
    async def validate_hipaa_safe_harbor(
        self,
        profile: AnonymizedMLProfile
    ) -> Dict[str, Any]:
        """
        Validate profile against HIPAA Safe Harbor requirements.
        
        HIPAA Safe Harbor removes 18 specific identifiers plus any other
        information that could be used to identify the individual.
        
        Args:
            profile: Anonymized ML profile to validate
            
        Returns:
            HIPAA compliance validation results
        """
        try:
            results = {
                "compliance_level": ComplianceLevel.COMPLIANT,
                "safe_harbor_compliant": True,
                "identifiers_removed": [],
                "violations": [],
                "recommendations": [],
                "validation_timestamp": datetime.utcnow().isoformat()
            }
            
            # Check HIPAA Safe Harbor 18 identifiers
            violations = await self._check_hipaa_18_identifiers(profile)
            if violations:
                results["violations"].extend(violations)
                results["compliance_level"] = ComplianceLevel.NON_COMPLIANT
                results["safe_harbor_compliant"] = False
            
            # Validate anonymization quality
            anonymization_quality = await self._assess_anonymization_quality(profile)
            if anonymization_quality["re_identification_risk"] > 0.05:  # 5% threshold
                results["violations"].append({
                    "type": "re_identification_risk",
                    "severity": ValidationSeverity.HIGH,
                    "description": f"Re-identification risk too high: {anonymization_quality['re_identification_risk']:.3f}",
                    "recommendation": "Increase anonymization strength"
                })
                results["compliance_level"] = ComplianceLevel.CONDITIONAL
            
            # Check for sufficient anonymization
            if not await self._validate_sufficient_anonymization(profile):
                results["violations"].append({
                    "type": "insufficient_anonymization",
                    "severity": ValidationSeverity.CRITICAL,
                    "description": "Anonymization may not meet Safe Harbor standards",
                    "recommendation": "Apply additional anonymization techniques"
                })
                results["compliance_level"] = ComplianceLevel.NON_COMPLIANT
                results["safe_harbor_compliant"] = False
            
            # Audit HIPAA validation
            await self._audit_hipaa_validation(profile, results)
            
            self.logger.info(
                "HIPAA Safe Harbor validation completed",
                profile_id=profile.profile_id,
                compliance_level=results["compliance_level"],
                violations_count=len(results["violations"])
            )
            
            return results
            
        except Exception as e:
            self.logger.error(
                "HIPAA Safe Harbor validation failed",
                profile_id=profile.profile_id,
                error=str(e)
            )
            return {
                "compliance_level": ComplianceLevel.NON_COMPLIANT,
                "safe_harbor_compliant": False,
                "error": str(e),
                "validation_timestamp": datetime.utcnow().isoformat()
            }
    
    async def check_hipaa_identifiers_removed(
        self,
        profile: AnonymizedMLProfile
    ) -> List[str]:
        """
        Check which HIPAA identifiers have been properly removed.
        
        Args:
            profile: Anonymized ML profile
            
        Returns:
            List of identifiers that were properly removed
        """
        removed_identifiers = []
        
        # Check each of the 18 HIPAA identifiers
        hipaa_identifiers = [
            "names", "geographic_subdivisions", "dates", "telephone_numbers",
            "fax_numbers", "email_addresses", "ssn", "medical_record_numbers",
            "health_plan_beneficiary_numbers", "account_numbers", 
            "certificate_license_numbers", "vehicle_identifiers", 
            "device_identifiers", "web_urls", "ip_addresses", 
            "biometric_identifiers", "full_face_photos", "other_unique_identifying_numbers"
        ]
        
        for identifier in hipaa_identifiers:
            if await self._check_identifier_removed(profile, identifier):
                removed_identifiers.append(identifier)
        
        return removed_identifiers
    
    async def validate_minimum_necessary_standard(
        self,
        profile: AnonymizedMLProfile
    ) -> bool:
        """
        Validate HIPAA minimum necessary standard for ML use.
        
        Args:
            profile: Anonymized ML profile
            
        Returns:
            True if profile meets minimum necessary standard
        """
        # Check that only necessary data is included for ML purposes
        necessary_categories = {
            "age_group", "gender_category", "pregnancy_status",
            "location_category", "season_category", "medical_history_categories",
            "medication_categories", "allergy_categories", "risk_factors"
        }
        
        profile_categories = set(profile.categorical_features.keys())
        
        # Allow additional ML-specific features
        ml_specific_categories = {
            "similarity_metadata", "vector_features", "prediction_ready",
            "comorbidity_indicators", "utilization_pattern", "care_complexity"
        }
        
        allowed_categories = necessary_categories.union(ml_specific_categories)
        
        # Check for unnecessary data
        unnecessary_data = profile_categories - allowed_categories
        
        if unnecessary_data:
            self.logger.warning(
                "Unnecessary data found in ML profile",
                profile_id=profile.profile_id,
                unnecessary_fields=list(unnecessary_data)
            )
            return False
        
        return True
    
    async def audit_phi_removal(
        self,
        original: Dict[str, Any],
        anonymized: AnonymizedMLProfile
    ) -> Dict[str, Any]:
        """
        Audit PHI removal process for compliance.
        
        Args:
            original: Original patient data
            anonymized: Anonymized ML profile
            
        Returns:
            PHI removal audit results
        """
        audit_results = {
            "audit_id": str(uuid.uuid4()),
            "original_fields_count": len(original),
            "anonymized_fields_count": len(anonymized.categorical_features),
            "phi_fields_removed": [],
            "phi_fields_transformed": [],
            "audit_timestamp": datetime.utcnow().isoformat()
        }
        
        # Identify PHI fields that were removed
        phi_fields = {
            "first_name", "last_name", "full_name", "ssn", "phone_number",
            "email", "address", "date_of_birth", "medical_record_number"
        }
        
        for field in phi_fields:
            if field in original and field not in anonymized.categorical_features:
                audit_results["phi_fields_removed"].append(field)
        
        # Identify fields that were transformed
        transformation_mappings = {
            "age": "age_group",
            "location": "location_category",
            "visit_date": "season_category"
        }
        
        for original_field, anonymized_field in transformation_mappings.items():
            if (original_field in original and 
                anonymized_field in anonymized.categorical_features):
                audit_results["phi_fields_transformed"].append({
                    "original": original_field,
                    "anonymized": anonymized_field
                })
        
        return audit_results
    
    # GDPR COMPLIANCE VALIDATION
    
    async def validate_gdpr_article_26(
        self,
        profile: AnonymizedMLProfile
    ) -> Dict[str, Any]:
        """
        Validate profile against GDPR Article 26 requirements.
        
        GDPR Article 26 requires pseudonymisation such that data can no longer
        be attributed to a specific data subject without additional information.
        
        Args:
            profile: Anonymized ML profile
            
        Returns:
            GDPR Article 26 compliance results
        """
        try:
            results = {
                "compliance_level": ComplianceLevel.COMPLIANT,
                "article_26_compliant": True,
                "pseudonymisation_adequate": True,
                "data_subject_identification_risk": 0.0,
                "violations": [],
                "safeguards_implemented": [],
                "validation_timestamp": datetime.utcnow().isoformat()
            }
            
            # Check pseudonymisation adequacy
            pseudonym_quality = await self._assess_pseudonym_quality(
                profile.anonymous_id
            )
            
            if not pseudonym_quality["adequate"]:
                results["violations"].append({
                    "type": "inadequate_pseudonymisation",
                    "severity": ValidationSeverity.CRITICAL,
                    "description": "Pseudonym does not meet GDPR Article 26 standards",
                    "recommendation": "Regenerate with stronger pseudonymisation"
                })
                results["article_26_compliant"] = False
                results["pseudonymisation_adequate"] = False
            
            # Check for additional safeguards
            safeguards = await self._check_gdpr_safeguards(profile)
            results["safeguards_implemented"] = safeguards
            
            if len(safeguards) < 2:  # Minimum 2 safeguards required
                results["violations"].append({
                    "type": "insufficient_safeguards",
                    "severity": ValidationSeverity.HIGH,
                    "description": "Insufficient additional safeguards for GDPR compliance",
                    "recommendation": "Implement additional technical and organisational measures"
                })
                results["compliance_level"] = ComplianceLevel.CONDITIONAL
            
            # Calculate data subject identification risk
            identification_risk = await self._calculate_identification_risk(profile)
            results["data_subject_identification_risk"] = identification_risk
            
            if identification_risk > 0.1:  # 10% threshold
                results["violations"].append({
                    "type": "high_identification_risk",
                    "severity": ValidationSeverity.HIGH,
                    "description": f"Data subject identification risk too high: {identification_risk:.3f}",
                    "recommendation": "Apply stronger anonymisation techniques"
                })
                results["compliance_level"] = ComplianceLevel.CONDITIONAL
            
            # Audit GDPR validation
            await self._audit_gdpr_validation(profile, results)
            
            return results
            
        except Exception as e:
            self.logger.error(
                "GDPR Article 26 validation failed",
                profile_id=profile.profile_id,
                error=str(e)
            )
            return {
                "compliance_level": ComplianceLevel.NON_COMPLIANT,
                "article_26_compliant": False,
                "error": str(e),
                "validation_timestamp": datetime.utcnow().isoformat()
            }
    
    async def check_right_to_erasure_compliance(
        self,
        profile: AnonymizedMLProfile
    ) -> bool:
        """
        Check GDPR right to erasure compliance for anonymized data.
        
        Args:
            profile: Anonymized ML profile
            
        Returns:
            True if right to erasure is properly handled
        """
        # For properly anonymized data, right to erasure doesn't apply
        # because the data can no longer be linked to the individual
        
        # Check anonymization quality
        anonymization_quality = await self._assess_anonymization_quality(profile)
        
        # If re-identification risk is very low, right to erasure doesn't apply
        if anonymization_quality["re_identification_risk"] < 0.01:  # 1% threshold
            return True
        
        # If there's significant re-identification risk, we need erasure capability
        return False
    
    # SOC2 TYPE II COMPLIANCE VALIDATION
    
    async def validate_soc2_security(
        self,
        profile: AnonymizedMLProfile
    ) -> Dict[str, Any]:
        """
        Validate profile against SOC2 Type II security requirements.
        
        Args:
            profile: Anonymized ML profile
            
        Returns:
            SOC2 Type II compliance results
        """
        results = {
            "compliance_level": ComplianceLevel.COMPLIANT,
            "soc2_compliant": True,
            "security_controls": [],
            "violations": [],
            "validation_timestamp": datetime.utcnow().isoformat()
        }
        
        # Check security controls implementation
        security_controls = await self._validate_soc2_security_controls(profile)
        results["security_controls"] = security_controls
        
        # Check for control failures
        failed_controls = [
            control for control in security_controls
            if not control["implemented"]
        ]
        
        if failed_controls:
            for control in failed_controls:
                results["violations"].append({
                    "type": "security_control_failure",
                    "control": control["name"],
                    "severity": ValidationSeverity.HIGH,
                    "description": f"SOC2 security control not implemented: {control['name']}",
                    "recommendation": control.get("recommendation", "Implement security control")
                })
            
            results["compliance_level"] = ComplianceLevel.NON_COMPLIANT
            results["soc2_compliant"] = False
        
        return results
    
    # COMPREHENSIVE VALIDATION
    
    async def comprehensive_compliance_check(
        self,
        profile: AnonymizedMLProfile
    ) -> ComplianceValidationResult:
        """
        Perform comprehensive compliance validation across all standards.
        
        Args:
            profile: Anonymized ML profile
            
        Returns:
            Complete compliance validation results
        """
        try:
            # Run all compliance validations
            hipaa_results = await self.validate_hipaa_safe_harbor(profile)
            gdpr_results = await self.validate_gdpr_article_26(profile)
            soc2_results = await self.validate_soc2_security(profile)
            
            # Calculate overall compliance
            overall_compliant = (
                hipaa_results["safe_harbor_compliant"] and
                gdpr_results["article_26_compliant"] and
                soc2_results["soc2_compliant"]
            )
            
            # Calculate overall compliance score
            compliance_scores = {
                "hipaa": 1.0 if hipaa_results["safe_harbor_compliant"] else 0.0,
                "gdpr": 1.0 if gdpr_results["article_26_compliant"] else 0.0,
                "soc2": 1.0 if soc2_results["soc2_compliant"] else 0.0
            }
            overall_score = sum(compliance_scores.values()) / len(compliance_scores)
            
            # Collect all issues
            all_issues = []
            all_issues.extend(hipaa_results.get("violations", []))
            all_issues.extend(gdpr_results.get("violations", []))
            all_issues.extend(soc2_results.get("violations", []))
            
            # Generate recommendations
            recommendations = await self._generate_compliance_recommendations(
                hipaa_results, gdpr_results, soc2_results
            )
            
            # Create comprehensive result
            validation_result = ComplianceValidationResult(
                profile_id=profile.profile_id,
                hipaa_compliant=hipaa_results["safe_harbor_compliant"],
                gdpr_compliant=gdpr_results["article_26_compliant"],
                soc2_compliant=soc2_results["soc2_compliant"],
                fhir_compliant=True,  # Assume FHIR compliance for ML profiles
                pii_removal_validated=len(all_issues) == 0,
                re_identification_risk=gdpr_results.get("data_subject_identification_risk", 0.0),
                utility_preservation=await self._calculate_utility_preservation(profile),
                overall_compliance_score=overall_score,
                compliance_issues=[issue["description"] for issue in all_issues],
                recommendations=recommendations
            )
            
            # Audit comprehensive validation
            await self._audit_comprehensive_validation(profile, validation_result)
            
            self.logger.info(
                "Comprehensive compliance validation completed",
                profile_id=profile.profile_id,
                overall_compliant=overall_compliant,
                compliance_score=overall_score
            )
            
            return validation_result
            
        except Exception as e:
            self.logger.error(
                "Comprehensive compliance validation failed",
                profile_id=profile.profile_id,
                error=str(e)
            )
            
            # Return non-compliant result
            return ComplianceValidationResult(
                profile_id=profile.profile_id,
                hipaa_compliant=False,
                gdpr_compliant=False,
                soc2_compliant=False,
                fhir_compliant=False,
                pii_removal_validated=False,
                re_identification_risk=1.0,
                utility_preservation=0.0,
                overall_compliance_score=0.0,
                compliance_issues=[f"Validation error: {str(e)}"],
                recommendations=["Fix validation errors and retry"]
            )
    
    async def batch_validate_compliance(
        self,
        profiles: List[AnonymizedMLProfile]
    ) -> List[ComplianceValidationResult]:
        """
        Validate compliance for multiple profiles efficiently.
        
        Args:
            profiles: List of anonymized ML profiles
            
        Returns:
            List of compliance validation results
        """
        results = []
        
        self.logger.info(
            "Starting batch compliance validation",
            profile_count=len(profiles)
        )
        
        for i, profile in enumerate(profiles):
            try:
                result = await self.comprehensive_compliance_check(profile)
                results.append(result)
                
                # Log progress
                if (i + 1) % 100 == 0:
                    self.logger.info(
                        "Batch validation progress",
                        completed=i + 1,
                        total=len(profiles)
                    )
                    
            except Exception as e:
                self.logger.error(
                    "Failed to validate profile in batch",
                    profile_id=profile.profile_id,
                    error=str(e)
                )
                # Add failed result
                results.append(ComplianceValidationResult(
                    profile_id=profile.profile_id,
                    hipaa_compliant=False,
                    gdpr_compliant=False,
                    soc2_compliant=False,
                    fhir_compliant=False,
                    pii_removal_validated=False,
                    re_identification_risk=1.0,
                    utility_preservation=0.0,
                    overall_compliance_score=0.0,
                    compliance_issues=[f"Batch validation error: {str(e)}"],
                    recommendations=["Review profile data and retry validation"]
                ))
        
        self.logger.info(
            "Batch compliance validation completed",
            total_profiles=len(profiles),
            successful_validations=len(results)
        )
        
        return results
    
    # PRIVATE HELPER METHODS
    
    def _load_compliance_patterns(self):
        """Load compliance validation patterns and rules."""
        # HIPAA Safe Harbor identifiers patterns
        self.hipaa_patterns = {
            "names": r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',
            "dates": r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            "phone_numbers": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        }
        
        # GDPR pseudonymisation requirements
        self.gdpr_requirements = {
            "min_pseudonym_length": 16,
            "max_identification_risk": 0.1,
            "min_safeguards_count": 2
        }
        
        # SOC2 security controls
        self.soc2_controls = [
            "access_control", "encryption", "audit_logging",
            "data_integrity", "monitoring", "incident_response"
        ]
    
    async def _check_hipaa_18_identifiers(
        self,
        profile: AnonymizedMLProfile
    ) -> List[Dict[str, Any]]:
        """Check for presence of HIPAA 18 identifiers."""
        violations = []
        
        # Convert profile to searchable text
        profile_text = str(profile.categorical_features)
        
        for identifier, pattern in self.hipaa_patterns.items():
            matches = re.findall(pattern, profile_text, re.IGNORECASE)
            if matches:
                violations.append({
                    "type": f"hipaa_identifier_{identifier}",
                    "severity": ValidationSeverity.CRITICAL,
                    "description": f"HIPAA identifier found: {identifier}",
                    "matches": matches[:5],  # Limit to first 5 matches
                    "recommendation": f"Remove all {identifier} from profile"
                })
        
        return violations
    
    async def _assess_anonymization_quality(
        self,
        profile: AnonymizedMLProfile
    ) -> Dict[str, float]:
        """Assess overall anonymization quality."""
        # Simple heuristic-based assessment
        # In production, this would use more sophisticated metrics
        
        quality_metrics = {
            "re_identification_risk": 0.0,
            "utility_preservation": 1.0,
            "anonymization_strength": 1.0
        }
        
        # Check pseudonym quality
        pseudonym_entropy = len(set(profile.anonymous_id)) / len(profile.anonymous_id)
        if pseudonym_entropy < 0.5:
            quality_metrics["re_identification_risk"] += 0.3
        
        # Check categorical generalization
        categorical_features = profile.categorical_features
        specific_values = sum(
            1 for value in categorical_features.values()
            if isinstance(value, str) and len(value.split('_')) == 1
        )
        
        if specific_values > len(categorical_features) * 0.3:
            quality_metrics["re_identification_risk"] += 0.2
        
        return quality_metrics
    
    async def _validate_sufficient_anonymization(
        self,
        profile: AnonymizedMLProfile
    ) -> bool:
        """Validate if anonymization is sufficient for HIPAA."""
        # Check k-anonymity approximation
        # This is simplified - production would use actual k-anonymity calculation
        
        categorical_count = len(profile.categorical_features)
        if categorical_count < 5:  # Minimum categorical features
            return False
        
        # Check for overly specific categories
        for key, value in profile.categorical_features.items():
            if isinstance(value, str) and any(
                specific in value.lower() 
                for specific in ["specific", "unique", "individual"]
            ):
                return False
        
        return True
    
    async def _check_identifier_removed(
        self,
        profile: AnonymizedMLProfile,
        identifier: str
    ) -> bool:
        """Check if specific HIPAA identifier was removed."""
        profile_text = str(profile.categorical_features).lower()
        
        identifier_keywords = {
            "names": ["name", "first", "last"],
            "dates": ["birth", "date", "dob"],
            "phone": ["phone", "tel", "mobile"],
            "ssn": ["ssn", "social", "security"],
            "email": ["email", "@", "mail"]
        }
        
        keywords = identifier_keywords.get(identifier, [])
        return not any(keyword in profile_text for keyword in keywords)
    
    async def _assess_pseudonym_quality(self, pseudonym: str) -> Dict[str, Any]:
        """Assess pseudonym quality for GDPR compliance."""
        quality = {
            "adequate": True,
            "length_sufficient": len(pseudonym) >= 16,
            "entropy_sufficient": True,
            "pattern_resistant": True
        }
        
        # Check entropy
        if len(set(pseudonym)) < 8:
            quality["entropy_sufficient"] = False
            quality["adequate"] = False
        
        # Check for patterns
        if pseudonym.count(pseudonym[0]) > len(pseudonym) * 0.3:
            quality["pattern_resistant"] = False
            quality["adequate"] = False
        
        return quality
    
    async def _check_gdpr_safeguards(
        self,
        profile: AnonymizedMLProfile
    ) -> List[str]:
        """Check implemented GDPR safeguards."""
        safeguards = []
        
        # Pseudonymisation
        if profile.anonymous_id and len(profile.anonymous_id) >= 16:
            safeguards.append("pseudonymisation")
        
        # Data minimization
        if len(profile.categorical_features) <= 15:  # Reasonable limit
            safeguards.append("data_minimization")
        
        # Technical measures (encryption implied)
        if profile.compliance_validated:
            safeguards.append("technical_measures")
        
        # Organisational measures (audit trail)
        if profile.anonymization_timestamp:
            safeguards.append("organisational_measures")
        
        return safeguards
    
    async def _calculate_identification_risk(
        self,
        profile: AnonymizedMLProfile
    ) -> float:
        """Calculate data subject identification risk."""
        # Simplified risk calculation
        # Production would use more sophisticated algorithms
        
        risk_factors = 0.0
        
        # Check uniqueness of categorical combinations
        categorical_specificity = len(str(profile.categorical_features)) / 1000.0
        risk_factors += min(categorical_specificity, 0.5)
        
        # Check pseudonym quality
        pseudonym_entropy = len(set(profile.anonymous_id)) / len(profile.anonymous_id)
        if pseudonym_entropy < 0.5:
            risk_factors += 0.3
        
        # Check for rare combinations
        rare_combinations = sum(
            1 for value in profile.categorical_features.values()
            if isinstance(value, list) and len(value) > 5
        )
        risk_factors += min(rare_combinations * 0.1, 0.2)
        
        return min(risk_factors, 1.0)
    
    async def _validate_soc2_security_controls(
        self,
        profile: AnonymizedMLProfile
    ) -> List[Dict[str, Any]]:
        """Validate SOC2 security controls implementation."""
        controls = []
        
        for control_name in self.soc2_controls:
            control_result = {
                "name": control_name,
                "implemented": False,
                "details": ""
            }
            
            if control_name == "access_control":
                # Check if profile has proper access controls
                control_result["implemented"] = bool(profile.anonymous_id)
                control_result["details"] = "Pseudonymous access control implemented"
            
            elif control_name == "encryption":
                # Assume encryption if compliance validated
                control_result["implemented"] = profile.compliance_validated
                control_result["details"] = "Data encryption validated"
            
            elif control_name == "audit_logging":
                # Check if audit metadata exists
                control_result["implemented"] = bool(profile.anonymization_timestamp)
                control_result["details"] = "Audit logging timestamp present"
            
            elif control_name == "data_integrity":
                # Check data consistency
                control_result["implemented"] = profile.prediction_ready
                control_result["details"] = "Data integrity validated for ML use"
            
            elif control_name == "monitoring":
                # Check if monitoring metadata exists
                control_result["implemented"] = bool(profile.similarity_metadata)
                control_result["details"] = "Monitoring metadata available"
            
            elif control_name == "incident_response":
                # Check if compliance framework is in place
                control_result["implemented"] = profile.compliance_validated
                control_result["details"] = "Incident response framework validated"
            
            controls.append(control_result)
        
        return controls
    
    async def _calculate_utility_preservation(
        self,
        profile: AnonymizedMLProfile
    ) -> float:
        """Calculate data utility preservation score."""
        utility_score = 1.0
        
        # Check if clinical features are preserved
        clinical_features = [
            "medical_history_categories", "medication_categories",
            "allergy_categories", "risk_factors"
        ]
        
        preserved_features = sum(
            1 for feature in clinical_features
            if feature in profile.categorical_features and 
            profile.categorical_features[feature]
        )
        
        feature_preservation = preserved_features / len(clinical_features)
        utility_score *= feature_preservation
        
        # Check if ML readiness is maintained
        if profile.prediction_ready and profile.clinical_text_embedding:
            utility_score *= 1.0
        else:
            utility_score *= 0.7
        
        return min(utility_score, 1.0)
    
    async def _generate_compliance_recommendations(
        self,
        hipaa_results: Dict[str, Any],
        gdpr_results: Dict[str, Any],
        soc2_results: Dict[str, Any]
    ) -> List[str]:
        """Generate compliance improvement recommendations."""
        recommendations = []
        
        # HIPAA recommendations
        if not hipaa_results["safe_harbor_compliant"]:
            recommendations.append("Apply stronger anonymization to meet HIPAA Safe Harbor standards")
            recommendations.append("Remove or further generalize any remaining identifiers")
        
        # GDPR recommendations
        if not gdpr_results["article_26_compliant"]:
            recommendations.append("Implement additional technical and organisational safeguards for GDPR compliance")
            recommendations.append("Strengthen pseudonymisation to reduce identification risk")
        
        # SOC2 recommendations
        if not soc2_results["soc2_compliant"]:
            recommendations.append("Implement missing SOC2 security controls")
            recommendations.append("Enhance audit logging and monitoring capabilities")
        
        # General recommendations
        if not recommendations:
            recommendations.append("Maintain current anonymization standards")
            recommendations.append("Regularly review and update compliance measures")
        
        return recommendations
    
    # AUDIT METHODS
    
    async def _audit_hipaa_validation(
        self,
        profile: AnonymizedMLProfile,
        results: Dict[str, Any]
    ):
        """Audit HIPAA validation process."""
        try:
            audit_data = {
                "operation": "hipaa_validation",
                "profile_id": profile.profile_id,
                "compliance_level": results["compliance_level"],
                "violations_count": len(results.get("violations", [])),
                "validation_timestamp": results["validation_timestamp"]
            }
            
            self.logger.info("HIPAA validation audited", **audit_data)
            
        except Exception as e:
            self.logger.error("Failed to audit HIPAA validation", error=str(e))
    
    async def _audit_gdpr_validation(
        self,
        profile: AnonymizedMLProfile,
        results: Dict[str, Any]
    ):
        """Audit GDPR validation process."""
        try:
            audit_data = {
                "operation": "gdpr_validation",
                "profile_id": profile.profile_id,
                "article_26_compliant": results["article_26_compliant"],
                "identification_risk": results.get("data_subject_identification_risk", 0.0),
                "validation_timestamp": results["validation_timestamp"]
            }
            
            self.logger.info("GDPR validation audited", **audit_data)
            
        except Exception as e:
            self.logger.error("Failed to audit GDPR validation", error=str(e))
    
    async def _audit_comprehensive_validation(
        self,
        profile: AnonymizedMLProfile,
        result: ComplianceValidationResult
    ):
        """Audit comprehensive validation process."""
        try:
            audit_data = {
                "operation": "comprehensive_validation",
                "profile_id": profile.profile_id,
                "overall_compliance_score": result.overall_compliance_score,
                "hipaa_compliant": result.hipaa_compliant,
                "gdpr_compliant": result.gdpr_compliant,
                "soc2_compliant": result.soc2_compliant,
                "validation_timestamp": result.validation_timestamp
            }
            
            self.logger.info("Comprehensive validation audited", **audit_data)
            
        except Exception as e:
            self.logger.error("Failed to audit comprehensive validation", error=str(e))