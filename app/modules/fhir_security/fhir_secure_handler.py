"""
FHIR Secure Handler for Healthcare Platform V2.0

Enterprise-grade FHIR R4 security implementation with security labels,
consent management, audit trails, and multimodal healthcare data protection.
"""

import asyncio
import logging
import uuid
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum

# FHIR and healthcare imports
from fhir.resources import Patient, Observation, DiagnosticReport, Procedure
from fhir.resources.bundle import Bundle
from fhir.resources.auditEvent import AuditEvent
from fhir.resources.provenance import Provenance
from fhir.resources.consent import Consent
from fhir.resources.meta import Meta
from fhir.resources.coding import Coding
from fhir.resources.codeableConcept import CodeableConcept

# Security and cryptography
import cryptography
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption

# Internal imports
from ..security.encryption import EncryptionService
from ..audit_logger.service import AuditLogService
from ...core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class SecurityClassification(str, Enum):
    """FHIR security classification levels."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    TOP_SECRET = "top_secret"

class ConsentStatus(str, Enum):
    """Consent status values."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PROPOSED = "proposed"
    REJECTED = "rejected"
    ENTERED_IN_ERROR = "entered-in-error"

class AccessCategory(str, Enum):
    """Access category classifications."""
    TREATMENT = "treatment"
    PAYMENT = "payment"
    OPERATIONS = "operations"
    RESEARCH = "research"
    EMERGENCY = "emergency"
    DISCLOSURE = "disclosure"

@dataclass
class FHIRSecurityConfig:
    """Configuration for FHIR security implementation."""
    
    # Security settings
    enable_security_labels: bool = True
    require_consent_validation: bool = True
    enable_encryption: bool = True
    enable_digital_signatures: bool = True
    
    # Audit settings
    audit_all_access: bool = True
    audit_retention_days: int = 2555  # 7 years for HIPAA
    enable_detailed_logging: bool = True
    
    # Consent settings
    default_consent_period_days: int = 365
    require_explicit_consent: bool = True
    granular_consent_enabled: bool = True
    
    # Multimodal settings
    secure_multimodal_data: bool = True
    encrypt_imaging_data: bool = True
    anonymize_audio_transcripts: bool = True
    genetic_data_special_handling: bool = True
    
    # Performance settings
    cache_consent_decisions: bool = True
    cache_ttl_minutes: int = 60
    batch_audit_events: bool = True

@dataclass
class SecurityLabel:
    """FHIR security label implementation."""
    
    system: str
    code: str
    display: str
    classification: SecurityClassification
    handling_caveats: List[str]
    access_restrictions: List[str]
    retention_period: Optional[timedelta] = None
    
    def to_fhir_coding(self) -> Coding:
        """Convert to FHIR Coding resource."""
        return Coding(
            system=self.system,
            code=self.code,
            display=self.display
        )

@dataclass
class ConsentPolicy:
    """Consent policy configuration."""
    
    policy_id: str
    policy_name: str
    purpose_codes: List[str]
    data_categories: List[str]
    access_categories: List[AccessCategory]
    retention_period: timedelta
    geographical_restrictions: List[str]
    requires_explicit_consent: bool = True
    allows_data_sharing: bool = False
    allows_research_use: bool = False

@dataclass
class ResourceAccess:
    """Resource access tracking."""
    
    resource_type: str
    resource_id: str
    access_type: str  # read, write, delete, etc.
    access_timestamp: datetime
    user_id: str
    user_role: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

@dataclass
class UserContext:
    """User context for access control."""
    
    user_id: str
    user_role: str
    organization_id: str
    access_scopes: List[str]
    security_clearance: SecurityClassification
    consent_agreements: List[str]
    session_id: str

@dataclass
class LabeledResource:
    """FHIR resource with security labels."""
    
    resource: Any  # FHIR resource
    security_labels: List[SecurityLabel]
    encryption_metadata: Optional[Dict[str, Any]] = None
    digital_signature: Optional[str] = None
    access_log: List[ResourceAccess] = None

@dataclass
class ConsentContext:
    """Consent context for data access."""
    
    patient_id: str
    consent_id: str
    consent_status: ConsentStatus
    granted_purposes: List[str]
    granted_data_categories: List[str]
    restrictions: List[str]
    expiry_date: datetime
    last_verified: datetime

@dataclass
class ComplianceResult:
    """Compliance validation result."""
    
    compliant: bool
    compliance_score: float
    violations: List[str]
    recommendations: List[str]
    compliance_standards: List[str]
    validation_timestamp: datetime

@dataclass
class EncryptedResource:
    """Encrypted FHIR resource."""
    
    resource_id: str
    resource_type: str
    encrypted_data: bytes
    encryption_algorithm: str
    key_id: str
    initialization_vector: bytes
    authentication_tag: bytes

@dataclass
class SignedResource:
    """Digitally signed FHIR resource."""
    
    resource: Any
    signature: str
    signature_algorithm: str
    certificate_chain: List[str]
    signing_timestamp: datetime

@dataclass
class AccessDecision:
    """Access control decision."""
    
    decision: str  # allow, deny, conditional
    reasoning: str
    required_conditions: List[str]
    access_level: str
    security_warnings: List[str]
    decision_timestamp: datetime

class FHIRSecureHandler:
    """
    Enterprise FHIR security handler implementing comprehensive security controls.
    
    Provides security labels, consent management, encryption, digital signatures,
    and audit capabilities for FHIR R4 resources in healthcare AI systems.
    """
    
    def __init__(self, config: FHIRSecurityConfig):
        self.config = config
        self.logger = logger.bind(component="FHIRSecureHandler")
        
        # Initialize security services
        self.encryption_service = EncryptionService()
        self.audit_service = AuditLogService()
        
        # Security label management
        self.security_labels = self._initialize_security_labels()
        
        # Consent and access control caches
        self.consent_cache: Dict[str, ConsentContext] = {}
        self.access_decision_cache: Dict[str, AccessDecision] = {}
        
        # Cryptographic keys for signing
        self.signing_key = self._initialize_signing_key()
        self.verification_keys: Dict[str, Any] = {}
        
        self.logger.info("FHIRSecureHandler initialized successfully")

    def _initialize_security_labels(self) -> Dict[str, SecurityLabel]:
        """Initialize standard FHIR security labels."""
        return {
            "public": SecurityLabel(
                system="http://terminology.hl7.org/CodeSystem/v3-Confidentiality",
                code="U",
                display="unrestricted",
                classification=SecurityClassification.PUBLIC,
                handling_caveats=[],
                access_restrictions=[]
            ),
            "confidential": SecurityLabel(
                system="http://terminology.hl7.org/CodeSystem/v3-Confidentiality", 
                code="R",
                display="restricted",
                classification=SecurityClassification.CONFIDENTIAL,
                handling_caveats=["encrypt_at_rest", "audit_access"],
                access_restrictions=["authorized_users_only"]
            ),
            "sensitive": SecurityLabel(
                system="http://terminology.hl7.org/CodeSystem/v3-ActCode",
                code="PSY",
                display="psychiatry",
                classification=SecurityClassification.RESTRICTED,
                handling_caveats=["encrypt_at_rest", "audit_access", "require_consent"],
                access_restrictions=["specialized_authorization", "purpose_limitation"]
            ),
            "genetic": SecurityLabel(
                system="http://terminology.hl7.org/CodeSystem/v3-ActCode",
                code="GENETIC",
                display="genetic information",
                classification=SecurityClassification.TOP_SECRET,
                handling_caveats=["encrypt_at_rest", "audit_access", "require_consent", "special_handling"],
                access_restrictions=["genetic_counselor_approval", "purpose_limitation", "no_discrimination_use"]
            )
        }

    def _initialize_signing_key(self) -> rsa.RSAPrivateKey:
        """Initialize RSA key for digital signatures."""
        try:
            # In production, load from secure key management system
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            return private_key
        except Exception as e:
            self.logger.error(f"Failed to initialize signing key: {str(e)}")
            raise

    async def apply_fhir_security_labels(
        self, 
        resource: Any, 
        sensitivity_level: str
    ) -> LabeledResource:
        """
        Apply FHIR security labels to healthcare resources.
        
        Args:
            resource: FHIR resource to label
            sensitivity_level: Sensitivity classification level
            
        Returns:
            LabeledResource with applied security labels
        """
        try:
            # Determine appropriate security labels
            labels = await self._determine_security_labels(resource, sensitivity_level)
            
            # Apply security labels to resource metadata
            if not resource.meta:
                resource.meta = Meta()
            
            if not resource.meta.security:
                resource.meta.security = []
            
            # Add security label codings
            for label in labels:
                security_coding = label.to_fhir_coding()
                resource.meta.security.append(security_coding)
            
            # Create labeled resource
            labeled_resource = LabeledResource(
                resource=resource,
                security_labels=labels,
                access_log=[]
            )
            
            # Apply encryption if required
            if self.config.enable_encryption and any(
                "encrypt_at_rest" in label.handling_caveats for label in labels
            ):
                labeled_resource.encryption_metadata = await self._encrypt_resource_elements(
                    resource, labels
                )
            
            # Apply digital signature if required
            if self.config.enable_digital_signatures:
                labeled_resource.digital_signature = await self._sign_resource(resource)
            
            self.logger.info(
                "FHIR security labels applied",
                resource_type=resource.resource_type,
                resource_id=getattr(resource, 'id', 'unknown'),
                label_count=len(labels),
                sensitivity_level=sensitivity_level
            )
            
            return labeled_resource
            
        except Exception as e:
            self.logger.error(
                "Failed to apply FHIR security labels",
                resource_type=getattr(resource, 'resource_type', 'unknown'),
                sensitivity_level=sensitivity_level,
                error=str(e)
            )
            raise

    async def implement_fhir_consent_management(
        self, 
        patient_id: str, 
        consent_policies: List[ConsentPolicy]
    ) -> ConsentContext:
        """
        Implement FHIR-compliant consent management.
        
        Args:
            patient_id: Patient identifier
            consent_policies: List of applicable consent policies
            
        Returns:
            ConsentContext with validated consent information
        """
        try:
            # Check cache first
            cache_key = f"consent_{patient_id}"
            if self.config.cache_consent_decisions and cache_key in self.consent_cache:
                cached_consent = self.consent_cache[cache_key]
                if (datetime.utcnow() - cached_consent.last_verified).total_seconds() < self.config.cache_ttl_minutes * 60:
                    return cached_consent
            
            # Create FHIR Consent resource
            consent_resource = await self._create_fhir_consent_resource(
                patient_id, consent_policies
            )
            
            # Validate consent policies
            validation_result = await self._validate_consent_policies(
                patient_id, consent_policies
            )
            
            if not validation_result["valid"]:
                raise ValueError(f"Invalid consent policies: {validation_result['errors']}")
            
            # Aggregate consent information
            granted_purposes = []
            granted_data_categories = []
            restrictions = []
            
            for policy in consent_policies:
                granted_purposes.extend(policy.purpose_codes)
                granted_data_categories.extend(policy.data_categories)
                if policy.geographical_restrictions:
                    restrictions.extend(policy.geographical_restrictions)
            
            # Calculate consent expiry
            min_retention = min(policy.retention_period for policy in consent_policies)
            expiry_date = datetime.utcnow() + min_retention
            
            # Create consent context
            consent_context = ConsentContext(
                patient_id=patient_id,
                consent_id=consent_resource.id,
                consent_status=ConsentStatus.ACTIVE,
                granted_purposes=list(set(granted_purposes)),
                granted_data_categories=list(set(granted_data_categories)),
                restrictions=list(set(restrictions)),
                expiry_date=expiry_date,
                last_verified=datetime.utcnow()
            )
            
            # Cache consent decision
            if self.config.cache_consent_decisions:
                self.consent_cache[cache_key] = consent_context
            
            # Audit consent establishment
            await self._audit_consent_management(
                patient_id, consent_context, "consent_established"
            )
            
            self.logger.info(
                "FHIR consent management implemented",
                patient_id=patient_id,
                consent_id=consent_context.consent_id,
                granted_purposes_count=len(consent_context.granted_purposes),
                expiry_date=consent_context.expiry_date.isoformat()
            )
            
            return consent_context
            
        except Exception as e:
            self.logger.error(
                "Failed to implement FHIR consent management",
                patient_id=patient_id,
                policy_count=len(consent_policies),
                error=str(e)
            )
            raise

    async def audit_fhir_resource_access(
        self, 
        resource_access: ResourceAccess, 
        user_context: UserContext
    ) -> str:
        """
        Audit FHIR resource access with comprehensive logging.
        
        Args:
            resource_access: Resource access information
            user_context: User context for the access
            
        Returns:
            Audit event ID
        """
        try:
            # Create FHIR AuditEvent resource
            audit_event = AuditEvent(
                type=Coding(
                    system="http://dicom.nema.org/resources/ontology/DCM",
                    code="110100", 
                    display="Application Activity"
                ),
                subtype=[
                    Coding(
                        system="http://hl7.org/fhir/restful-interaction",
                        code=resource_access.access_type,
                        display=resource_access.access_type.title()
                    )
                ],
                action="E",  # Execute
                recorded=resource_access.access_timestamp,
                outcome="0",  # Success
                purposeOfEvent=[
                    CodeableConcept(
                        coding=[
                            Coding(
                                system="http://terminology.hl7.org/CodeSystem/v3-ActReason",
                                code="TREAT",
                                display="Treatment"
                            )
                        ]
                    )
                ]
            )
            
            # Add agent (user) information
            audit_event.agent = [{
                "type": CodeableConcept(
                    coding=[
                        Coding(
                            system="http://terminology.hl7.org/CodeSystem/extra-security-role-type",
                            code="humanuser",
                            display="Human User"
                        )
                    ]
                ),
                "who": {
                    "identifier": {
                        "value": user_context.user_id
                    }
                },
                "role": [
                    CodeableConcept(
                        coding=[
                            Coding(
                                system="http://terminology.hl7.org/CodeSystem/v3-RoleCode",
                                code=user_context.user_role,
                                display=user_context.user_role
                            )
                        ]
                    )
                ],
                "requestor": True
            }]
            
            # Add source information
            audit_event.source = {
                "site": "Healthcare Platform V2.0",
                "observer": {
                    "display": "FHIR Security Handler"
                },
                "type": [
                    Coding(
                        system="http://terminology.hl7.org/CodeSystem/security-source-type",
                        code="4",
                        display="Application Server"
                    )
                ]
            }
            
            # Add entity (resource) information
            audit_event.entity = [{
                "what": {
                    "reference": f"{resource_access.resource_type}/{resource_access.resource_id}"
                },
                "type": Coding(
                    system="http://terminology.hl7.org/CodeSystem/audit-entity-type",
                    code="2",
                    display="System Object"
                ),
                "role": Coding(
                    system="http://terminology.hl7.org/CodeSystem/object-role",
                    code="1",
                    display="Patient"
                )
            }]
            
            # Store audit event
            audit_event_id = str(uuid.uuid4())
            audit_event.id = audit_event_id
            
            # Enhanced audit logging
            audit_details = {
                "audit_event_id": audit_event_id,
                "resource_type": resource_access.resource_type,
                "resource_id": resource_access.resource_id,
                "access_type": resource_access.access_type,
                "user_id": user_context.user_id,
                "user_role": user_context.user_role,
                "organization_id": user_context.organization_id,
                "security_clearance": user_context.security_clearance.value,
                "session_id": user_context.session_id,
                "ip_address": resource_access.ip_address,
                "user_agent": resource_access.user_agent,
                "access_timestamp": resource_access.access_timestamp.isoformat(),
                "compliance_framework": "HIPAA_SOC2_FHIR"
            }
            
            # Log to audit service
            await self.audit_service.log_audit_event(
                operation="fhir_resource_access",
                details=audit_details,
                user_id=user_context.user_id,
                resource_type=resource_access.resource_type,
                security_classification=user_context.security_clearance.value
            )
            
            self.logger.info(
                "FHIR resource access audited",
                audit_event_id=audit_event_id,
                resource_type=resource_access.resource_type,
                access_type=resource_access.access_type,
                user_id=user_context.user_id
            )
            
            return audit_event_id
            
        except Exception as e:
            self.logger.error(
                "Failed to audit FHIR resource access",
                resource_type=resource_access.resource_type,
                user_id=user_context.user_id,
                error=str(e)
            )
            raise

    async def encrypt_fhir_elements(
        self, 
        resource: Any, 
        encryption_rules: Dict[str, Any]
    ) -> EncryptedResource:
        """
        Encrypt sensitive FHIR resource elements.
        
        Args:
            resource: FHIR resource to encrypt
            encryption_rules: Element-specific encryption rules
            
        Returns:
            EncryptedResource with encrypted sensitive data
        """
        try:
            # Identify sensitive elements
            sensitive_elements = await self._identify_sensitive_elements(resource, encryption_rules)
            
            # Create encryption context
            encryption_key = await self.encryption_service.generate_encryption_key()
            iv = await self.encryption_service.generate_iv()
            
            # Encrypt sensitive elements
            encrypted_data = {}
            for element_path, element_value in sensitive_elements.items():
                encrypted_value = await self.encryption_service.encrypt_data(
                    json.dumps(element_value).encode(),
                    encryption_key,
                    iv
                )
                encrypted_data[element_path] = encrypted_value
            
            # Create encrypted resource representation
            resource_dict = resource.dict()
            
            # Replace sensitive elements with encryption placeholders
            for element_path in sensitive_elements.keys():
                self._set_nested_value(resource_dict, element_path, "[ENCRYPTED]")
            
            # Generate authentication tag
            auth_tag = await self._generate_authentication_tag(encrypted_data, encryption_key)
            
            encrypted_resource = EncryptedResource(
                resource_id=getattr(resource, 'id', str(uuid.uuid4())),
                resource_type=resource.resource_type,
                encrypted_data=json.dumps(encrypted_data).encode(),
                encryption_algorithm="AES-256-GCM",
                key_id=await self.encryption_service.get_key_id(encryption_key),
                initialization_vector=iv,
                authentication_tag=auth_tag
            )
            
            self.logger.info(
                "FHIR elements encrypted",
                resource_type=resource.resource_type,
                encrypted_elements_count=len(sensitive_elements),
                encryption_algorithm=encrypted_resource.encryption_algorithm
            )
            
            return encrypted_resource
            
        except Exception as e:
            self.logger.error(
                "Failed to encrypt FHIR elements",
                resource_type=getattr(resource, 'resource_type', 'unknown'),
                error=str(e)
            )
            raise

    async def implement_fhir_provenance(
        self, 
        resource: Any, 
        action: str, 
        agent: Dict[str, Any]
    ) -> str:
        """
        Implement FHIR provenance tracking for resource changes.
        
        Args:
            resource: FHIR resource being tracked
            action: Action performed on resource
            agent: Agent performing the action
            
        Returns:
            Provenance record ID
        """
        try:
            # Create FHIR Provenance resource
            provenance = Provenance(
                target=[{
                    "reference": f"{resource.resource_type}/{getattr(resource, 'id', str(uuid.uuid4()))}"
                }],
                occurredDateTime=datetime.utcnow(),
                recorded=datetime.utcnow(),
                activity=CodeableConcept(
                    coding=[
                        Coding(
                            system="http://terminology.hl7.org/CodeSystem/v3-DataOperation",
                            code=action.upper(),
                            display=action.title()
                        )
                    ]
                ),
                agent=[{
                    "type": CodeableConcept(
                        coding=[
                            Coding(
                                system="http://terminology.hl7.org/CodeSystem/provenance-participant-type",
                                code="author",
                                display="Author"
                            )
                        ]
                    ),
                    "who": {
                        "identifier": {
                            "value": agent.get("id", "unknown")
                        },
                        "display": agent.get("name", "Unknown Agent")
                    },
                    "role": [
                        CodeableConcept(
                            coding=[
                                Coding(
                                    system="http://terminology.hl7.org/CodeSystem/v3-RoleCode",
                                    code=agent.get("role", "UNKNOWN"),
                                    display=agent.get("role_display", "Unknown Role")
                                )
                            ]
                        )
                    ]
                }]
            )
            
            # Add signature for integrity
            provenance_id = str(uuid.uuid4())
            provenance.id = provenance_id
            
            # Generate digital signature for provenance
            signature_data = await self._generate_provenance_signature(provenance, agent)
            
            # Add signature extension
            provenance.signature = [{
                "type": [
                    Coding(
                        system="urn:iso-astm:E1762-95:2013",
                        code="1.2.840.10065.1.12.1.1",
                        display="Author's Signature"
                    )
                ],
                "when": datetime.utcnow(),
                "who": {
                    "reference": f"Practitioner/{agent.get('id', 'unknown')}"
                },
                "data": signature_data
            }]
            
            # Store provenance record
            await self._store_provenance_record(provenance)
            
            self.logger.info(
                "FHIR provenance implemented",
                provenance_id=provenance_id,
                resource_type=resource.resource_type,
                action=action,
                agent_id=agent.get("id", "unknown")
            )
            
            return provenance_id
            
        except Exception as e:
            self.logger.error(
                "Failed to implement FHIR provenance",
                resource_type=getattr(resource, 'resource_type', 'unknown'),
                action=action,
                error=str(e)
            )
            raise

    async def validate_fhir_security_compliance(
        self, 
        resource: Any, 
        policy: Dict[str, Any]
    ) -> ComplianceResult:
        """
        Validate FHIR resource security compliance.
        
        Args:
            resource: FHIR resource to validate
            policy: Security policy to validate against
            
        Returns:
            ComplianceResult with validation details
        """
        try:
            violations = []
            recommendations = []
            compliance_score = 1.0
            
            # Validate security labels
            if not resource.meta or not resource.meta.security:
                violations.append("Missing required security labels")
                compliance_score -= 0.3
                recommendations.append("Apply appropriate security labels")
            
            # Validate consent requirements
            if policy.get("require_consent", True):
                consent_validation = await self._validate_consent_compliance(resource, policy)
                if not consent_validation["compliant"]:
                    violations.extend(consent_validation["violations"])
                    compliance_score -= 0.4
                    recommendations.extend(consent_validation["recommendations"])
            
            # Validate encryption requirements
            if policy.get("require_encryption", False):
                encryption_validation = await self._validate_encryption_compliance(resource, policy)
                if not encryption_validation["compliant"]:
                    violations.extend(encryption_validation["violations"])
                    compliance_score -= 0.3
                    recommendations.extend(encryption_validation["recommendations"])
            
            # Validate audit requirements
            audit_validation = await self._validate_audit_compliance(resource, policy)
            if not audit_validation["compliant"]:
                violations.extend(audit_validation["violations"])
                compliance_score -= 0.2
                recommendations.extend(audit_validation["recommendations"])
            
            # Validate data minimization
            minimization_validation = await self._validate_data_minimization(resource, policy)
            if not minimization_validation["compliant"]:
                violations.extend(minimization_validation["violations"])
                compliance_score -= 0.1
                recommendations.extend(minimization_validation["recommendations"])
            
            compliance_result = ComplianceResult(
                compliant=len(violations) == 0,
                compliance_score=max(0.0, compliance_score),
                violations=violations,
                recommendations=recommendations,
                compliance_standards=["HIPAA", "FHIR R4", "SOC2", "GDPR"],
                validation_timestamp=datetime.utcnow()
            )
            
            self.logger.info(
                "FHIR security compliance validated",
                resource_type=resource.resource_type,
                compliant=compliance_result.compliant,
                compliance_score=compliance_result.compliance_score,
                violations_count=len(violations)
            )
            
            return compliance_result
            
        except Exception as e:
            self.logger.error(
                "Failed to validate FHIR security compliance",
                resource_type=getattr(resource, 'resource_type', 'unknown'),
                error=str(e)
            )
            raise

    async def implement_fhir_digital_signatures(
        self, 
        resource: Any, 
        signing_key: Any
    ) -> SignedResource:
        """
        Implement FHIR digital signatures for resource integrity.
        
        Args:
            resource: FHIR resource to sign
            signing_key: Private key for signing
            
        Returns:
            SignedResource with digital signature
        """
        try:
            # Canonicalize resource for signing
            canonical_resource = await self._canonicalize_fhir_resource(resource)
            
            # Generate digital signature
            signature = await self._generate_digital_signature(canonical_resource, signing_key)
            
            # Create certificate chain
            certificate_chain = await self._get_certificate_chain(signing_key)
            
            signed_resource = SignedResource(
                resource=resource,
                signature=signature,
                signature_algorithm="RS256",
                certificate_chain=certificate_chain,
                signing_timestamp=datetime.utcnow()
            )
            
            # Add signature to resource metadata
            if not resource.meta:
                resource.meta = Meta()
            
            # Add signature extension
            resource.meta.extension = resource.meta.extension or []
            resource.meta.extension.append({
                "url": "http://hl7.org/fhir/StructureDefinition/signature",
                "valueSignature": {
                    "type": [
                        Coding(
                            system="urn:iso-astm:E1762-95:2013",
                            code="1.2.840.10065.1.12.1.1",
                            display="Author's Signature"
                        )
                    ],
                    "when": signed_resource.signing_timestamp,
                    "data": signature
                }
            })
            
            self.logger.info(
                "FHIR digital signature implemented",
                resource_type=resource.resource_type,
                signature_algorithm=signed_resource.signature_algorithm,
                signing_timestamp=signed_resource.signing_timestamp.isoformat()
            )
            
            return signed_resource
            
        except Exception as e:
            self.logger.error(
                "Failed to implement FHIR digital signature",
                resource_type=getattr(resource, 'resource_type', 'unknown'),
                error=str(e)
            )
            raise

    async def manage_fhir_access_control(
        self, 
        resource_request: Dict[str, Any], 
        user_permissions: Dict[str, Any]
    ) -> AccessDecision:
        """
        Manage FHIR resource access control with comprehensive authorization.
        
        Args:
            resource_request: Resource access request
            user_permissions: User permission context
            
        Returns:
            AccessDecision with authorization result
        """
        try:
            # Extract request details
            resource_type = resource_request.get("resource_type")
            resource_id = resource_request.get("resource_id")
            access_type = resource_request.get("access_type", "read")
            user_id = user_permissions.get("user_id")
            user_role = user_permissions.get("user_role")
            
            # Check cache for previous decisions
            cache_key = f"access_{user_id}_{resource_type}_{access_type}"
            if cache_key in self.access_decision_cache:
                cached_decision = self.access_decision_cache[cache_key]
                if (datetime.utcnow() - cached_decision.decision_timestamp).total_seconds() < 300:  # 5 minutes
                    return cached_decision
            
            # Initialize decision
            decision = "deny"
            reasoning = "Access denied by default"
            required_conditions = []
            security_warnings = []
            
            # Role-based access control
            rbac_result = await self._evaluate_rbac(user_permissions, resource_request)
            if not rbac_result["allowed"]:
                reasoning = f"Insufficient role permissions: {rbac_result['reason']}"
            else:
                decision = "conditional"
                reasoning = "Role permissions validated"
                required_conditions.extend(rbac_result.get("conditions", []))
            
            # Attribute-based access control (ABAC)
            if decision != "deny":
                abac_result = await self._evaluate_abac(user_permissions, resource_request)
                if not abac_result["allowed"]:
                    decision = "deny"
                    reasoning = f"Attribute-based access denied: {abac_result['reason']}"
                else:
                    required_conditions.extend(abac_result.get("conditions", []))
            
            # Consent-based access control
            if decision != "deny":
                consent_result = await self._evaluate_consent_access(user_permissions, resource_request)
                if not consent_result["allowed"]:
                    decision = "deny"
                    reasoning = f"Consent requirements not met: {consent_result['reason']}"
                else:
                    required_conditions.extend(consent_result.get("conditions", []))
            
            # Purpose limitation validation
            if decision != "deny":
                purpose_result = await self._evaluate_purpose_limitation(user_permissions, resource_request)
                if not purpose_result["allowed"]:
                    decision = "deny"
                    reasoning = f"Purpose limitation violation: {purpose_result['reason']}"
                else:
                    security_warnings.extend(purpose_result.get("warnings", []))
            
            # Final decision processing
            if decision == "conditional" and not required_conditions:
                decision = "allow"
                reasoning = "All access conditions satisfied"
            
            access_decision = AccessDecision(
                decision=decision,
                reasoning=reasoning,
                required_conditions=required_conditions,
                access_level="full" if decision == "allow" else "restricted",
                security_warnings=security_warnings,
                decision_timestamp=datetime.utcnow()
            )
            
            # Cache decision
            self.access_decision_cache[cache_key] = access_decision
            
            # Audit access decision
            await self._audit_access_decision(resource_request, user_permissions, access_decision)
            
            self.logger.info(
                "FHIR access control decision made",
                resource_type=resource_type,
                user_id=user_id,
                access_type=access_type,
                decision=decision,
                conditions_count=len(required_conditions)
            )
            
            return access_decision
            
        except Exception as e:
            self.logger.error(
                "Failed to manage FHIR access control",
                resource_type=resource_request.get("resource_type", "unknown"),
                user_id=user_permissions.get("user_id", "unknown"),
                error=str(e)
            )
            raise

    # Helper methods for FHIR security implementation
    
    async def _determine_security_labels(
        self, 
        resource: Any, 
        sensitivity_level: str
    ) -> List[SecurityLabel]:
        """Determine appropriate security labels for resource."""
        labels = []
        
        # Base classification
        if sensitivity_level in self.security_labels:
            labels.append(self.security_labels[sensitivity_level])
        
        # Resource-specific labels
        if hasattr(resource, 'resourceType'):
            if resource.resourceType == "Observation":
                # Check for sensitive observation types
                if hasattr(resource, 'category') and resource.category:
                    for category in resource.category:
                        if category.coding:
                            for coding in category.coding:
                                if coding.code in ["vital-signs", "survey"]:
                                    labels.append(self.security_labels["confidential"])
                                elif coding.code in ["genetics", "psychiatry"]:
                                    labels.append(self.security_labels["sensitive"])
        
        return labels or [self.security_labels["confidential"]]

    async def _encrypt_resource_elements(
        self, 
        resource: Any, 
        labels: List[SecurityLabel]
    ) -> Dict[str, Any]:
        """Encrypt sensitive resource elements."""
        encryption_metadata = {
            "encrypted_elements": [],
            "encryption_key_id": "key_001",
            "algorithm": "AES-256-GCM",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Placeholder for element-specific encryption logic
        # In production, would encrypt based on security labels
        
        return encryption_metadata

    async def _sign_resource(self, resource: Any) -> str:
        """Generate digital signature for resource."""
        try:
            # Create canonical representation
            resource_json = json.dumps(resource.dict(), sort_keys=True)
            resource_bytes = resource_json.encode('utf-8')
            
            # Generate signature
            signature = self.signing_key.sign(
                resource_bytes,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            # Return base64 encoded signature
            import base64
            return base64.b64encode(signature).decode('utf-8')
            
        except Exception as e:
            self.logger.error(f"Failed to sign resource: {str(e)}")
            return ""

    # Additional helper methods would continue here...
    # (Placeholder implementations for brevity)