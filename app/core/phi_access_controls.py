#!/usr/bin/env python3
"""
Enhanced PHI Access Controls with Field-Level Audit Tracking
Implements HIPAA minimum necessary rule with granular field-level access monitoring.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
import structlog
import uuid

logger = structlog.get_logger()

class PHIFieldType(Enum):
    """PHI field classification"""
    DIRECT_IDENTIFIER = "direct_identifier"  # Name, SSN, etc.
    QUASI_IDENTIFIER = "quasi_identifier"   # DOB, ZIP, etc.
    CLINICAL_DATA = "clinical_data"          # Diagnosis, treatment
    ADMINISTRATIVE = "administrative"        # Insurance, billing
    SENSITIVE_CLINICAL = "sensitive_clinical" # Mental health, substance abuse

class AccessPurpose(Enum):
    """Access purpose for minimum necessary rule"""
    TREATMENT = "treatment"
    PAYMENT = "payment"
    OPERATIONS = "healthcare_operations"
    RESEARCH = "research"
    LEGAL = "legal_requirement"
    PATIENT_REQUEST = "patient_request"
    EMERGENCY = "emergency"

class ConsentType(Enum):
    """Patient consent types"""
    GENERAL_TREATMENT = "general_treatment"
    RESEARCH_PARTICIPATION = "research_participation"
    MARKETING = "marketing"
    PSYCHOTHERAPY_NOTES = "psychotherapy_notes"
    SUBSTANCE_ABUSE = "substance_abuse"
    MENTAL_HEALTH = "mental_health"
    DATA_SHARING = "data_sharing"

@dataclass
class PHIFieldDefinition:
    """Definition of PHI field with access controls"""
    field_name: str
    field_type: PHIFieldType
    sensitivity_level: int  # 1-5, 5 being most sensitive
    required_roles: Set[str]
    required_consent: Set[ConsentType]
    audit_required: bool
    retention_days: int
    minimum_necessary_purposes: Set[AccessPurpose]

@dataclass
class PHIAccessRequest:
    """PHI access request with justification"""
    request_id: str
    user_id: str
    patient_id: str
    requested_fields: List[str]
    purpose: AccessPurpose
    justification: str
    timestamp: datetime
    ip_address: str
    session_id: str
    approved: bool
    approval_reason: str

@dataclass
class PHIFieldAccess:
    """Individual field access audit record"""
    access_id: str
    request_id: str
    user_id: str
    patient_id: str
    field_name: str
    field_type: PHIFieldType
    field_value_hash: str  # SHA-256 hash of accessed value
    access_timestamp: datetime
    purpose: AccessPurpose
    justification: str
    minimum_necessary_verified: bool
    consent_verified: bool
    retention_expires: datetime

class PHIAccessController:
    """Enhanced PHI access control with field-level granularity"""
    
    def __init__(self):
        self.phi_field_definitions = {}
        self.access_requests = {}
        self.field_accesses = []
        self.consent_cache = {}  # Cache patient consents
        self.role_permissions = {}
        self._setup_phi_field_definitions()
        self._setup_role_permissions()
    
    def _setup_phi_field_definitions(self):
        """Define PHI fields with access controls"""
        
        # Direct identifiers - highest sensitivity
        self.phi_field_definitions.update({
            "first_name": PHIFieldDefinition(
                field_name="first_name",
                field_type=PHIFieldType.DIRECT_IDENTIFIER,
                sensitivity_level=4,
                required_roles={"doctor", "nurse", "admin"},
                required_consent={ConsentType.GENERAL_TREATMENT},
                audit_required=True,
                retention_days=2555,  # 7 years
                minimum_necessary_purposes={AccessPurpose.TREATMENT, AccessPurpose.PAYMENT, AccessPurpose.OPERATIONS}
            ),
            "last_name": PHIFieldDefinition(
                field_name="last_name",
                field_type=PHIFieldType.DIRECT_IDENTIFIER,
                sensitivity_level=4,
                required_roles={"doctor", "nurse", "admin"},
                required_consent={ConsentType.GENERAL_TREATMENT},
                audit_required=True,
                retention_days=2555,
                minimum_necessary_purposes={AccessPurpose.TREATMENT, AccessPurpose.PAYMENT, AccessPurpose.OPERATIONS}
            ),
            "ssn": PHIFieldDefinition(
                field_name="ssn",
                field_type=PHIFieldType.DIRECT_IDENTIFIER,
                sensitivity_level=5,
                required_roles={"admin", "billing"},
                required_consent={ConsentType.GENERAL_TREATMENT},
                audit_required=True,
                retention_days=2555,
                minimum_necessary_purposes={AccessPurpose.PAYMENT, AccessPurpose.OPERATIONS}
            ),
            "email": PHIFieldDefinition(
                field_name="email",
                field_type=PHIFieldType.DIRECT_IDENTIFIER,
                sensitivity_level=3,
                required_roles={"doctor", "nurse", "admin", "patient"},
                required_consent={ConsentType.GENERAL_TREATMENT},
                audit_required=True,
                retention_days=2555,
                minimum_necessary_purposes={AccessPurpose.TREATMENT, AccessPurpose.PAYMENT, AccessPurpose.OPERATIONS}
            ),
        })
        
        # Quasi-identifiers
        self.phi_field_definitions.update({
            "date_of_birth": PHIFieldDefinition(
                field_name="date_of_birth",
                field_type=PHIFieldType.QUASI_IDENTIFIER,
                sensitivity_level=3,
                required_roles={"doctor", "nurse", "admin", "lab_technician"},
                required_consent={ConsentType.GENERAL_TREATMENT},
                audit_required=True,
                retention_days=2555,
                minimum_necessary_purposes={AccessPurpose.TREATMENT, AccessPurpose.PAYMENT, AccessPurpose.OPERATIONS}
            ),
            "address": PHIFieldDefinition(
                field_name="address",
                field_type=PHIFieldType.QUASI_IDENTIFIER,
                sensitivity_level=3,
                required_roles={"doctor", "nurse", "admin"},
                required_consent={ConsentType.GENERAL_TREATMENT},
                audit_required=True,
                retention_days=2555,
                minimum_necessary_purposes={AccessPurpose.TREATMENT, AccessPurpose.PAYMENT, AccessPurpose.OPERATIONS}
            ),
            "phone": PHIFieldDefinition(
                field_name="phone",
                field_type=PHIFieldType.QUASI_IDENTIFIER,
                sensitivity_level=3,
                required_roles={"doctor", "nurse", "admin"},
                required_consent={ConsentType.GENERAL_TREATMENT},
                audit_required=True,
                retention_days=2555,
                minimum_necessary_purposes={AccessPurpose.TREATMENT, AccessPurpose.PAYMENT, AccessPurpose.OPERATIONS}
            ),
        })
        
        # Clinical data
        self.phi_field_definitions.update({
            "diagnosis": PHIFieldDefinition(
                field_name="diagnosis",
                field_type=PHIFieldType.CLINICAL_DATA,
                sensitivity_level=4,
                required_roles={"doctor", "nurse"},
                required_consent={ConsentType.GENERAL_TREATMENT},
                audit_required=True,
                retention_days=2555,
                minimum_necessary_purposes={AccessPurpose.TREATMENT, AccessPurpose.OPERATIONS}
            ),
            "medication": PHIFieldDefinition(
                field_name="medication",
                field_type=PHIFieldType.CLINICAL_DATA,
                sensitivity_level=4,
                required_roles={"doctor", "nurse", "pharmacist"},
                required_consent={ConsentType.GENERAL_TREATMENT},
                audit_required=True,
                retention_days=2555,
                minimum_necessary_purposes={AccessPurpose.TREATMENT}
            ),
            "lab_results": PHIFieldDefinition(
                field_name="lab_results",
                field_type=PHIFieldType.CLINICAL_DATA,
                sensitivity_level=3,
                required_roles={"doctor", "nurse", "lab_technician"},
                required_consent={ConsentType.GENERAL_TREATMENT},
                audit_required=True,
                retention_days=2555,
                minimum_necessary_purposes={AccessPurpose.TREATMENT, AccessPurpose.OPERATIONS}
            ),
        })
        
        # Sensitive clinical data
        self.phi_field_definitions.update({
            "mental_health_notes": PHIFieldDefinition(
                field_name="mental_health_notes",
                field_type=PHIFieldType.SENSITIVE_CLINICAL,
                sensitivity_level=5,
                required_roles={"psychiatrist", "psychologist"},
                required_consent={ConsentType.MENTAL_HEALTH, ConsentType.PSYCHOTHERAPY_NOTES},
                audit_required=True,
                retention_days=2555,
                minimum_necessary_purposes={AccessPurpose.TREATMENT}
            ),
            "substance_abuse_history": PHIFieldDefinition(
                field_name="substance_abuse_history",
                field_type=PHIFieldType.SENSITIVE_CLINICAL,
                sensitivity_level=5,
                required_roles={"doctor", "substance_abuse_counselor"},
                required_consent={ConsentType.SUBSTANCE_ABUSE},
                audit_required=True,
                retention_days=2555,
                minimum_necessary_purposes={AccessPurpose.TREATMENT}
            ),
        })
        
        # Administrative data
        self.phi_field_definitions.update({
            "insurance_id": PHIFieldDefinition(
                field_name="insurance_id",
                field_type=PHIFieldType.ADMINISTRATIVE,
                sensitivity_level=3,
                required_roles={"admin", "billing", "doctor"},
                required_consent={ConsentType.GENERAL_TREATMENT},
                audit_required=True,
                retention_days=2555,
                minimum_necessary_purposes={AccessPurpose.PAYMENT, AccessPurpose.OPERATIONS}
            ),
            "billing_information": PHIFieldDefinition(
                field_name="billing_information",
                field_type=PHIFieldType.ADMINISTRATIVE,
                sensitivity_level=3,
                required_roles={"admin", "billing"},
                required_consent={ConsentType.GENERAL_TREATMENT},
                audit_required=True,
                retention_days=2555,
                minimum_necessary_purposes={AccessPurpose.PAYMENT, AccessPurpose.OPERATIONS}
            ),
        })
    
    def _setup_role_permissions(self):
        """Setup role-based permissions for PHI access"""
        
        self.role_permissions = {
            "patient": {
                "can_access_own_data": True,
                "can_access_others_data": False,
                "allowed_purposes": {AccessPurpose.PATIENT_REQUEST},
                "field_restrictions": set()  # Patients can access all their own fields
            },
            "doctor": {
                "can_access_own_data": True,
                "can_access_others_data": True,
                "allowed_purposes": {AccessPurpose.TREATMENT, AccessPurpose.OPERATIONS},
                "field_restrictions": set()  # Doctors can access most fields
            },
            "nurse": {
                "can_access_own_data": True,
                "can_access_others_data": True,
                "allowed_purposes": {AccessPurpose.TREATMENT, AccessPurpose.OPERATIONS},
                "field_restrictions": {"ssn", "billing_information"}  # Limited admin access
            },
            "lab_technician": {
                "can_access_own_data": True,
                "can_access_others_data": True,
                "allowed_purposes": {AccessPurpose.TREATMENT},
                "field_restrictions": {"ssn", "billing_information", "mental_health_notes", "substance_abuse_history"}
            },
            "admin": {
                "can_access_own_data": True,
                "can_access_others_data": True,
                "allowed_purposes": {AccessPurpose.PAYMENT, AccessPurpose.OPERATIONS, AccessPurpose.LEGAL},
                "field_restrictions": {"mental_health_notes", "substance_abuse_history"}  # Admin can't access sensitive clinical
            },
            "billing": {
                "can_access_own_data": True,
                "can_access_others_data": True,
                "allowed_purposes": {AccessPurpose.PAYMENT, AccessPurpose.OPERATIONS},
                "field_restrictions": {"diagnosis", "medication", "lab_results", "mental_health_notes", "substance_abuse_history"}
            },
        }
    
    async def request_phi_access(self, user_id: str, user_role: str, patient_id: str, 
                                requested_fields: List[str], purpose: AccessPurpose, 
                                justification: str, ip_address: str, session_id: str) -> PHIAccessRequest:
        """Request access to PHI fields with minimum necessary validation"""
        
        request_id = str(uuid.uuid4())
        
        # Create access request
        access_request = PHIAccessRequest(
            request_id=request_id,
            user_id=user_id,
            patient_id=patient_id,
            requested_fields=requested_fields,
            purpose=purpose,
            justification=justification,
            timestamp=datetime.utcnow(),
            ip_address=ip_address,
            session_id=session_id,
            approved=False,
            approval_reason=""
        )
        
        # Validate access request
        approval_result = await self._validate_phi_access_request(user_role, access_request)
        access_request.approved = approval_result["approved"]
        access_request.approval_reason = approval_result["reason"]
        
        # Store request
        self.access_requests[request_id] = access_request
        
        # Log the access request
        logger.info("PHI_ACCESS - Access request created",
                   request_id=request_id,
                   user_id=user_id,
                   patient_id=patient_id,
                   fields_requested=len(requested_fields),
                   purpose=purpose.value,
                   approved=access_request.approved)
        
        if not access_request.approved:
            logger.warning("PHI_ACCESS - Access request denied",
                          request_id=request_id,
                          reason=access_request.approval_reason)
        
        return access_request
    
    async def _validate_phi_access_request(self, user_role: str, request: PHIAccessRequest) -> Dict[str, Any]:
        """Validate PHI access request against HIPAA minimum necessary rule"""
        
        # Check role permissions
        if user_role not in self.role_permissions:
            return {"approved": False, "reason": f"Unknown role: {user_role}"}
        
        role_perms = self.role_permissions[user_role]
        
        # Check if purpose is allowed for role
        if request.purpose not in role_perms["allowed_purposes"]:
            return {"approved": False, "reason": f"Purpose {request.purpose.value} not allowed for role {user_role}"}
        
        # Check field-level permissions
        denied_fields = []
        for field in request.requested_fields:
            # Check if field is defined
            if field not in self.phi_field_definitions:
                denied_fields.append(f"{field}: undefined PHI field")
                continue
            
            field_def = self.phi_field_definitions[field]
            
            # Check role restrictions
            if field in role_perms["field_restrictions"]:
                denied_fields.append(f"{field}: restricted for role {user_role}")
                continue
            
            # Check if role is authorized for this field
            if user_role not in field_def.required_roles:
                denied_fields.append(f"{field}: role {user_role} not authorized")
                continue
            
            # Check if purpose is valid for this field
            if request.purpose not in field_def.minimum_necessary_purposes:
                denied_fields.append(f"{field}: purpose {request.purpose.value} not necessary")
                continue
        
        if denied_fields:
            return {"approved": False, "reason": f"Field access denied: {'; '.join(denied_fields)}"}
        
        # Check patient consent (simplified - in production, query actual consent records)
        consent_check = await self._check_patient_consent(request.patient_id, request.requested_fields, request.purpose)
        if not consent_check["valid"]:
            return {"approved": False, "reason": f"Insufficient patient consent: {consent_check['reason']}"}
        
        # Validate justification
        if not request.justification or len(request.justification.strip()) < 10:
            return {"approved": False, "reason": "Insufficient justification provided"}
        
        return {"approved": True, "reason": "Access approved - all requirements met"}
    
    async def _check_patient_consent(self, patient_id: str, fields: List[str], purpose: AccessPurpose) -> Dict[str, Any]:
        """Check if patient has provided necessary consent for field access"""
        
        # In production, this would query actual patient consent records
        # For now, assume general treatment consent exists
        
        required_consents = set()
        for field in fields:
            if field in self.phi_field_definitions:
                field_def = self.phi_field_definitions[field]
                required_consents.update(field_def.required_consent)
        
        # Simulate consent validation
        # In production, query actual consent database
        patient_consents = self.consent_cache.get(patient_id, {ConsentType.GENERAL_TREATMENT})
        
        missing_consents = required_consents - patient_consents
        if missing_consents:
            return {
                "valid": False,
                "reason": f"Missing consent for: {[c.value for c in missing_consents]}"
            }
        
        return {"valid": True, "reason": "All required consents present"}
    
    async def access_phi_fields(self, request_id: str, field_values: Dict[str, Any]) -> List[PHIFieldAccess]:
        """Record actual PHI field access with audit trail"""
        
        if request_id not in self.access_requests:
            raise ValueError(f"Access request {request_id} not found")
        
        request = self.access_requests[request_id]
        
        if not request.approved:
            raise ValueError(f"Access request {request_id} not approved")
        
        field_accesses = []
        
        for field_name, field_value in field_values.items():
            if field_name not in request.requested_fields:
                logger.warning("PHI_ACCESS - Attempt to access non-requested field",
                              request_id=request_id,
                              field=field_name)
                continue
            
            # Create field access record
            access_id = str(uuid.uuid4())
            field_def = self.phi_field_definitions.get(field_name)
            
            # Hash the field value for audit purposes (don't store actual value)
            import hashlib
            field_value_str = str(field_value) if field_value is not None else ""
            field_value_hash = hashlib.sha256(field_value_str.encode()).hexdigest()
            
            field_access = PHIFieldAccess(
                access_id=access_id,
                request_id=request_id,
                user_id=request.user_id,
                patient_id=request.patient_id,
                field_name=field_name,
                field_type=field_def.field_type if field_def else PHIFieldType.CLINICAL_DATA,
                field_value_hash=field_value_hash,
                access_timestamp=datetime.utcnow(),
                purpose=request.purpose,
                justification=request.justification,
                minimum_necessary_verified=True,  # Verified during request approval
                consent_verified=True,  # Verified during request approval
                retention_expires=datetime.utcnow() + timedelta(days=field_def.retention_days if field_def else 2555)
            )
            
            field_accesses.append(field_access)
            self.field_accesses.append(field_access)
            
            # Log field access
            logger.info("PHI_ACCESS - Field accessed",
                       access_id=access_id,
                       request_id=request_id,
                       user_id=request.user_id,
                       patient_id=request.patient_id,
                       field=field_name,
                       field_type=field_def.field_type.value if field_def else "unknown",
                       purpose=request.purpose.value)
        
        return field_accesses
    
    async def audit_phi_access_patterns(self, hours: int = 24) -> Dict[str, Any]:
        """Analyze PHI access patterns for anomalies"""
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_accesses = [a for a in self.field_accesses if a.access_timestamp > cutoff_time]
        
        analysis = {
            "analysis_period_hours": hours,
            "total_field_accesses": len(recent_accesses),
            "unique_users": len(set(a.user_id for a in recent_accesses)),
            "unique_patients": len(set(a.patient_id for a in recent_accesses)),
            "field_type_breakdown": {},
            "purpose_breakdown": {},
            "high_sensitivity_accesses": 0,
            "anomalies_detected": []
        }
        
        # Analyze field type access
        for access in recent_accesses:
            field_type = access.field_type.value
            analysis["field_type_breakdown"][field_type] = analysis["field_type_breakdown"].get(field_type, 0) + 1
            
            purpose = access.purpose.value
            analysis["purpose_breakdown"][purpose] = analysis["purpose_breakdown"].get(purpose, 0) + 1
            
            # Count high sensitivity accesses
            field_def = self.phi_field_definitions.get(access.field_name)
            if field_def and field_def.sensitivity_level >= 4:
                analysis["high_sensitivity_accesses"] += 1
        
        # Detect anomalies
        # 1. Unusual access patterns by user
        user_access_counts = {}
        for access in recent_accesses:
            user_access_counts[access.user_id] = user_access_counts.get(access.user_id, 0) + 1
        
        # Flag users with unusually high access
        avg_access = sum(user_access_counts.values()) / len(user_access_counts) if user_access_counts else 0
        for user_id, count in user_access_counts.items():
            if count > avg_access * 3 and count > 50:  # 3x average and >50 accesses
                analysis["anomalies_detected"].append({
                    "type": "high_access_volume",
                    "user_id": user_id,
                    "access_count": count,
                    "average": avg_access
                })
        
        # 2. After-hours access to sensitive data
        for access in recent_accesses:
            access_hour = access.access_timestamp.hour
            field_def = self.phi_field_definitions.get(access.field_name)
            
            if field_def and field_def.sensitivity_level >= 4 and (access_hour < 6 or access_hour > 22):
                analysis["anomalies_detected"].append({
                    "type": "after_hours_sensitive_access",
                    "user_id": access.user_id,
                    "patient_id": access.patient_id,
                    "field": access.field_name,
                    "timestamp": access.access_timestamp.isoformat()
                })
        
        return analysis
    
    async def generate_phi_access_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate comprehensive PHI access report for compliance"""
        
        accesses_in_period = [
            a for a in self.field_accesses 
            if start_date <= a.access_timestamp <= end_date
        ]
        
        report = {
            "report_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": (end_date - start_date).days
            },
            "summary": {
                "total_field_accesses": len(accesses_in_period),
                "unique_users": len(set(a.user_id for a in accesses_in_period)),
                "unique_patients": len(set(a.patient_id for a in accesses_in_period)),
                "field_types_accessed": len(set(a.field_type for a in accesses_in_period))
            },
            "compliance_metrics": {
                "minimum_necessary_compliance": len([a for a in accesses_in_period if a.minimum_necessary_verified]) / len(accesses_in_period) * 100 if accesses_in_period else 0,
                "consent_compliance": len([a for a in accesses_in_period if a.consent_verified]) / len(accesses_in_period) * 100 if accesses_in_period else 0,
                "audit_trail_complete": 100.0  # All accesses are audited by design
            },
            "detailed_breakdown": {
                "by_field_type": {},
                "by_purpose": {},
                "by_sensitivity_level": {}
            },
            "high_risk_accesses": []
        }
        
        # Detailed breakdowns
        for access in accesses_in_period:
            # By field type
            field_type = access.field_type.value
            if field_type not in report["detailed_breakdown"]["by_field_type"]:
                report["detailed_breakdown"]["by_field_type"][field_type] = 0
            report["detailed_breakdown"]["by_field_type"][field_type] += 1
            
            # By purpose
            purpose = access.purpose.value
            if purpose not in report["detailed_breakdown"]["by_purpose"]:
                report["detailed_breakdown"]["by_purpose"][purpose] = 0
            report["detailed_breakdown"]["by_purpose"][purpose] += 1
            
            # By sensitivity level
            field_def = self.phi_field_definitions.get(access.field_name)
            sensitivity = field_def.sensitivity_level if field_def else 1
            sensitivity_key = f"level_{sensitivity}"
            if sensitivity_key not in report["detailed_breakdown"]["by_sensitivity_level"]:
                report["detailed_breakdown"]["by_sensitivity_level"][sensitivity_key] = 0
            report["detailed_breakdown"]["by_sensitivity_level"][sensitivity_key] += 1
            
            # Identify high-risk accesses
            if field_def and field_def.sensitivity_level >= 4:
                report["high_risk_accesses"].append({
                    "access_id": access.access_id,
                    "user_id": access.user_id,
                    "patient_id": access.patient_id,
                    "field": access.field_name,
                    "sensitivity_level": field_def.sensitivity_level,
                    "timestamp": access.access_timestamp.isoformat(),
                    "purpose": access.purpose.value
                })
        
        return report

# Global PHI access controller
phi_access_controller = PHIAccessController()

async def request_phi_access(user_id: str, user_role: str, patient_id: str, 
                            requested_fields: List[str], purpose: AccessPurpose, 
                            justification: str, ip_address: str, session_id: str) -> PHIAccessRequest:
    """Request PHI access with enhanced controls"""
    return await phi_access_controller.request_phi_access(
        user_id, user_role, patient_id, requested_fields, purpose, justification, ip_address, session_id
    )

async def access_phi_fields(request_id: str, field_values: Dict[str, Any]) -> List[PHIFieldAccess]:
    """Access PHI fields with audit trail"""
    return await phi_access_controller.access_phi_fields(request_id, field_values)

async def audit_phi_access_patterns(hours: int = 24) -> Dict[str, Any]:
    """Audit PHI access patterns"""
    return await phi_access_controller.audit_phi_access_patterns(hours)

async def generate_phi_access_report(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Generate PHI access compliance report"""
    return await phi_access_controller.generate_phi_access_report(start_date, end_date)