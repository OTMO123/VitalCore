"""
FHIR Consent Manager for Healthcare Platform V2.0

Advanced consent management system with granular permissions, dynamic validation,
and automated compliance tracking for healthcare AI systems.
"""

import asyncio
import logging
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple

# FHIR imports
from fhir.resources.consent import Consent
from fhir.resources.patient import Patient
from fhir.resources.organization import Organization
from fhir.resources.coding import Coding
from fhir.resources.codeableConcept import CodeableConcept

# Internal imports
from .schemas import (
    ConsentPolicy, ConsentContext, ConsentStatus, AccessCategory,
    FHIRSecurityConfig, ConsentRequest, SecurityAuditEvent
)
from ..audit_logger.service import AuditLogService
from ...core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class ConsentManager:
    """
    Advanced FHIR consent management system.
    
    Provides granular consent tracking, dynamic validation, automated compliance
    monitoring, and consent lifecycle management for healthcare AI platforms.
    """
    
    def __init__(self, config: FHIRSecurityConfig):
        self.config = config
        self.logger = logger.bind(component="ConsentManager")
        
        # Core services
        self.audit_service = AuditLogService()
        
        # Consent storage and caching
        self.active_consents: Dict[str, ConsentContext] = {}
        self.consent_policies: Dict[str, ConsentPolicy] = {}
        self.consent_history: Dict[str, List[ConsentContext]] = {}
        
        # Initialize default policies
        self._initialize_default_policies()
        
        # Consent validation cache
        self.validation_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = timedelta(minutes=self.config.cache_ttl_minutes)
        
        self.logger.info("ConsentManager initialized successfully")
    
    def _initialize_default_policies(self):
        """Initialize default consent policies."""
        
        # Treatment consent policy
        treatment_policy = ConsentPolicy(
            policy_name="Standard Treatment Consent",
            purpose_codes=["TREAT", "HOPERAT"],
            data_categories=["clinical", "demographics", "vital_signs"],
            access_categories=[AccessCategory.TREATMENT, AccessCategory.OPERATIONS],
            retention_period_days=2555,  # 7 years
            requires_explicit_consent=True,
            allows_data_sharing=False,
            allows_research_use=False
        )
        
        # Research consent policy
        research_policy = ConsentPolicy(
            policy_name="Research Participation Consent",
            purpose_codes=["RESEARCH", "HRESCH"],
            data_categories=["clinical", "demographics", "imaging", "genetics"],
            access_categories=[AccessCategory.RESEARCH],
            retention_period_days=3650,  # 10 years
            requires_explicit_consent=True,
            allows_data_sharing=True,
            allows_research_use=True,
            allows_commercial_use=False,
            minimum_age_requirement=18
        )
        
        # Emergency consent policy
        emergency_policy = ConsentPolicy(
            policy_name="Emergency Treatment Consent",
            purpose_codes=["ETREAT", "EMERGENCY"],
            data_categories=["clinical", "demographics", "vital_signs", "allergies"],
            access_categories=[AccessCategory.TREATMENT, AccessCategory.EMERGENCY],
            retention_period_days=365,
            requires_explicit_consent=False,  # Emergency exception
            allows_data_sharing=False,
            allows_research_use=False
        )
        
        # Quality improvement consent policy
        quality_policy = ConsentPolicy(
            policy_name="Quality Improvement Consent",
            purpose_codes=["QUAL", "HMARKT"],
            data_categories=["clinical", "outcomes", "safety"],
            access_categories=[AccessCategory.OPERATIONS],
            retention_period_days=1825,  # 5 years
            requires_explicit_consent=True,
            allows_data_sharing=False,
            allows_research_use=False
        )
        
        # Payment/billing consent policy
        payment_policy = ConsentPolicy(
            policy_name="Payment and Billing Consent",
            purpose_codes=["HPAYMT", "TREAT"],
            data_categories=["demographics", "insurance", "billing"],
            access_categories=[AccessCategory.PAYMENT, AccessCategory.OPERATIONS],
            retention_period_days=2190,  # 6 years
            requires_explicit_consent=True,
            allows_data_sharing=True,  # With insurance/billing entities
            allows_research_use=False
        )
        
        self.consent_policies = {
            "treatment": treatment_policy,
            "research": research_policy,
            "emergency": emergency_policy,
            "quality": quality_policy,
            "payment": payment_policy
        }
    
    async def create_consent_record(
        self, 
        patient_id: str,
        consent_policies: List[str],
        granular_permissions: Dict[str, Any] = None,
        consent_method: str = "digital_signature",
        witness_info: Dict[str, Any] = None
    ) -> ConsentContext:
        """
        Create a new consent record with specified policies.
        
        Args:
            patient_id: Patient identifier
            consent_policies: List of consent policy IDs
            granular_permissions: Specific permissions and restrictions
            consent_method: Method of consent capture
            witness_info: Witness information if required
            
        Returns:
            ConsentContext with consent details
        """
        try:
            consent_id = str(uuid.uuid4())
            
            # Validate policies exist
            for policy_id in consent_policies:
                if policy_id not in self.consent_policies:
                    raise ValueError(f"Unknown consent policy: {policy_id}")
            
            # Aggregate permissions from policies
            aggregated_permissions = await self._aggregate_policy_permissions(consent_policies)
            
            # Apply granular permissions if provided
            if granular_permissions:
                aggregated_permissions = await self._apply_granular_permissions(
                    aggregated_permissions, granular_permissions
                )
            
            # Determine consent expiry
            expiry_date = await self._calculate_consent_expiry(consent_policies)
            
            # Create FHIR Consent resource
            fhir_consent = await self._create_fhir_consent_resource(
                patient_id, consent_id, consent_policies, aggregated_permissions
            )
            
            # Create consent context
            consent_context = ConsentContext(
                context_id=str(uuid.uuid4()),
                patient_id=patient_id,
                consent_id=consent_id,
                consent_status=ConsentStatus.ACTIVE,
                granted_purposes=aggregated_permissions["purposes"],
                granted_data_categories=aggregated_permissions["data_categories"],
                granted_access_types=aggregated_permissions["access_types"],
                restrictions=aggregated_permissions.get("restrictions", []),
                conditions=aggregated_permissions.get("conditions", []),
                consent_date=datetime.utcnow(),
                expiry_date=expiry_date,
                verification_method=consent_method,
                witness_information=witness_info
            )
            
            # Store consent
            self.active_consents[patient_id] = consent_context
            
            # Initialize history
            if patient_id not in self.consent_history:
                self.consent_history[patient_id] = []
            self.consent_history[patient_id].append(consent_context)
            
            # Audit consent creation
            await self._audit_consent_action(
                "consent_created", patient_id, consent_context, 
                {"policies": consent_policies, "method": consent_method}
            )
            
            self.logger.info(
                "Consent record created",
                patient_id=patient_id,
                consent_id=consent_id,
                policies_count=len(consent_policies),
                expiry_date=expiry_date.isoformat()
            )
            
            return consent_context
            
        except Exception as e:
            self.logger.error(f"Failed to create consent record: {str(e)}")
            raise
    
    async def validate_consent_for_access(
        self, 
        patient_id: str,
        access_purpose: str,
        data_categories: List[str],
        requesting_user: str,
        access_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Validate consent for specific data access request.
        
        Args:
            patient_id: Patient identifier
            access_purpose: Purpose of data access
            data_categories: Categories of data being accessed
            requesting_user: User requesting access
            access_context: Additional access context
            
        Returns:
            Validation result with permission details
        """
        try:
            # Check validation cache
            cache_key = f"{patient_id}_{access_purpose}_{hash(tuple(data_categories))}"
            if cache_key in self.validation_cache:
                cached_result = self.validation_cache[cache_key]
                if datetime.utcnow() - cached_result["timestamp"] < self.cache_ttl:
                    return cached_result["result"]
            
            validation_result = {
                "consent_valid": False,
                "access_permitted": False,
                "consent_status": "not_found",
                "permitted_data_categories": [],
                "restrictions": [],
                "conditions": [],
                "expiry_date": None,
                "reason": "No valid consent found"
            }
            
            # Get active consent
            if patient_id not in self.active_consents:
                validation_result["reason"] = "No active consent record found"
                return validation_result
            
            consent_context = self.active_consents[patient_id]
            
            # Check consent status
            if consent_context.consent_status != ConsentStatus.ACTIVE:
                validation_result["consent_status"] = consent_context.consent_status.value
                validation_result["reason"] = f"Consent status is {consent_context.consent_status.value}"
                return validation_result
            
            # Check expiry
            if datetime.utcnow() > consent_context.expiry_date:
                validation_result["consent_status"] = "expired"
                validation_result["reason"] = "Consent has expired"
                await self._expire_consent(patient_id)
                return validation_result
            
            # Validate purpose
            purpose_permitted = await self._validate_purpose_permission(
                consent_context, access_purpose
            )
            
            if not purpose_permitted["permitted"]:
                validation_result["reason"] = f"Purpose '{access_purpose}' not permitted"
                return validation_result
            
            # Validate data categories
            data_permission = await self._validate_data_category_permissions(
                consent_context, data_categories
            )
            
            if not data_permission["permitted_categories"]:
                validation_result["reason"] = "No requested data categories are permitted"
                return validation_result
            
            # Check restrictions
            restriction_check = await self._check_access_restrictions(
                consent_context, requesting_user, access_context or {}
            )
            
            if restriction_check["blocked"]:
                validation_result["reason"] = f"Access blocked by restrictions: {restriction_check['reasons']}"
                return validation_result
            
            # All validations passed
            validation_result.update({
                "consent_valid": True,
                "access_permitted": True,
                "consent_status": "active",
                "permitted_data_categories": data_permission["permitted_categories"],
                "denied_data_categories": data_permission["denied_categories"],
                "restrictions": consent_context.restrictions,
                "conditions": consent_context.conditions + restriction_check.get("additional_conditions", []),
                "expiry_date": consent_context.expiry_date.isoformat(),
                "reason": "Access permitted under active consent"
            })
            
            # Cache result
            self.validation_cache[cache_key] = {
                "result": validation_result,
                "timestamp": datetime.utcnow()
            }
            
            # Audit consent validation
            await self._audit_consent_action(
                "consent_validated", patient_id, consent_context,
                {
                    "access_purpose": access_purpose,
                    "requesting_user": requesting_user,
                    "validation_result": validation_result["access_permitted"]
                }
            )
            
            self.logger.info(
                "Consent validation completed",
                patient_id=patient_id,
                access_purpose=access_purpose,
                access_permitted=validation_result["access_permitted"],
                permitted_categories=len(validation_result["permitted_data_categories"])
            )
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Failed to validate consent: {str(e)}")
            return {
                "consent_valid": False,
                "access_permitted": False,
                "reason": f"Validation error: {str(e)}"
            }
    
    async def withdraw_consent(
        self, 
        patient_id: str,
        withdrawal_scope: str = "all",
        withdrawal_reason: str = None,
        effective_date: datetime = None
    ) -> Dict[str, Any]:
        """
        Process consent withdrawal request.
        
        Args:
            patient_id: Patient identifier
            withdrawal_scope: Scope of withdrawal ("all", "research", "specific")
            withdrawal_reason: Reason for withdrawal
            effective_date: When withdrawal becomes effective
            
        Returns:
            Withdrawal processing result
        """
        try:
            if patient_id not in self.active_consents:
                raise ValueError(f"No active consent found for patient {patient_id}")
            
            consent_context = self.active_consents[patient_id]
            
            if not effective_date:
                effective_date = datetime.utcnow()
            
            # Process withdrawal based on scope
            if withdrawal_scope == "all":
                # Complete withdrawal
                consent_context.consent_status = ConsentStatus.INACTIVE
                consent_context.withdrawal_date = effective_date
                consent_context.withdrawal_reason = withdrawal_reason
                
                # Remove from active consents
                del self.active_consents[patient_id]
                
            elif withdrawal_scope == "research":
                # Withdraw only research permissions
                consent_context.granted_purposes = [
                    purpose for purpose in consent_context.granted_purposes
                    if purpose not in ["RESEARCH", "HRESCH"]
                ]
                consent_context.restrictions.append("no_research_use")
                
            else:
                # Specific withdrawal would require more granular handling
                raise NotImplementedError("Specific withdrawal scope not yet implemented")
            
            # Update consent history
            self.consent_history[patient_id].append(consent_context)
            
            # Create withdrawal audit record
            await self._audit_consent_action(
                "consent_withdrawn", patient_id, consent_context,
                {
                    "withdrawal_scope": withdrawal_scope,
                    "withdrawal_reason": withdrawal_reason,
                    "effective_date": effective_date.isoformat()
                }
            )
            
            # Clear validation cache for this patient
            keys_to_remove = [key for key in self.validation_cache.keys() if key.startswith(patient_id)]
            for key in keys_to_remove:
                del self.validation_cache[key]
            
            withdrawal_result = {
                "withdrawal_processed": True,
                "withdrawal_scope": withdrawal_scope,
                "effective_date": effective_date.isoformat(),
                "remaining_permissions": consent_context.granted_purposes if withdrawal_scope != "all" else [],
                "grace_period_hours": self.config.consent_withdrawal_grace_period_hours
            }
            
            self.logger.info(
                "Consent withdrawal processed",
                patient_id=patient_id,
                withdrawal_scope=withdrawal_scope,
                effective_date=effective_date.isoformat()
            )
            
            return withdrawal_result
            
        except Exception as e:
            self.logger.error(f"Failed to process consent withdrawal: {str(e)}")
            raise
    
    async def update_consent_permissions(
        self, 
        patient_id: str,
        permission_updates: Dict[str, Any],
        update_reason: str
    ) -> ConsentContext:
        """
        Update consent permissions for existing consent.
        
        Args:
            patient_id: Patient identifier
            permission_updates: Updated permissions
            update_reason: Reason for update
            
        Returns:
            Updated consent context
        """
        try:
            if patient_id not in self.active_consents:
                raise ValueError(f"No active consent found for patient {patient_id}")
            
            consent_context = self.active_consents[patient_id]
            
            # Create backup of current consent
            backup_consent = ConsentContext(**consent_context.dict())
            
            # Apply updates
            if "granted_purposes" in permission_updates:
                consent_context.granted_purposes = permission_updates["granted_purposes"]
            
            if "granted_data_categories" in permission_updates:
                consent_context.granted_data_categories = permission_updates["granted_data_categories"]
            
            if "restrictions" in permission_updates:
                consent_context.restrictions.extend(permission_updates["restrictions"])
            
            if "conditions" in permission_updates:
                consent_context.conditions.extend(permission_updates["conditions"])
            
            # Update verification timestamp
            consent_context.last_verified = datetime.utcnow()
            
            # Store updated consent
            self.active_consents[patient_id] = consent_context
            self.consent_history[patient_id].append(consent_context)
            
            # Clear validation cache
            keys_to_remove = [key for key in self.validation_cache.keys() if key.startswith(patient_id)]
            for key in keys_to_remove:
                del self.validation_cache[key]
            
            # Audit update
            await self._audit_consent_action(
                "consent_updated", patient_id, consent_context,
                {
                    "permission_updates": permission_updates,
                    "update_reason": update_reason,
                    "previous_consent": backup_consent.dict()
                }
            )
            
            self.logger.info(
                "Consent permissions updated",
                patient_id=patient_id,
                update_reason=update_reason
            )
            
            return consent_context
            
        except Exception as e:
            self.logger.error(f"Failed to update consent permissions: {str(e)}")
            raise
    
    async def get_consent_status(self, patient_id: str) -> Dict[str, Any]:
        """
        Get comprehensive consent status for a patient.
        
        Args:
            patient_id: Patient identifier
            
        Returns:
            Comprehensive consent status
        """
        try:
            status = {
                "patient_id": patient_id,
                "has_active_consent": False,
                "consent_status": "not_found",
                "active_permissions": {},
                "restrictions": [],
                "expiry_date": None,
                "last_verified": None,
                "consent_history_count": 0
            }
            
            # Check active consent
            if patient_id in self.active_consents:
                consent_context = self.active_consents[patient_id]
                
                status.update({
                    "has_active_consent": True,
                    "consent_status": consent_context.consent_status.value,
                    "active_permissions": {
                        "purposes": consent_context.granted_purposes,
                        "data_categories": consent_context.granted_data_categories,
                        "access_types": [at.value for at in consent_context.granted_access_types]
                    },
                    "restrictions": consent_context.restrictions,
                    "conditions": consent_context.conditions,
                    "expiry_date": consent_context.expiry_date.isoformat(),
                    "last_verified": consent_context.last_verified.isoformat(),
                    "verification_method": consent_context.verification_method
                })
            
            # Add history information
            if patient_id in self.consent_history:
                status["consent_history_count"] = len(self.consent_history[patient_id])
                
                # Add recent history summary
                recent_history = self.consent_history[patient_id][-3:]  # Last 3 entries
                status["recent_history"] = [
                    {
                        "consent_date": ctx.consent_date.isoformat(),
                        "status": ctx.consent_status.value,
                        "withdrawal_date": ctx.withdrawal_date.isoformat() if ctx.withdrawal_date else None
                    }
                    for ctx in recent_history
                ]
            
            return status
            
        except Exception as e:
            self.logger.error(f"Failed to get consent status: {str(e)}")
            raise
    
    async def check_consent_expiry(self) -> Dict[str, List[str]]:
        """
        Check for expiring or expired consents.
        
        Returns:
            Dictionary with expiring and expired consent lists
        """
        try:
            now = datetime.utcnow()
            expiring_soon = []  # Within 30 days
            expired = []
            
            for patient_id, consent_context in self.active_consents.items():
                days_until_expiry = (consent_context.expiry_date - now).days
                
                if days_until_expiry < 0:
                    expired.append(patient_id)
                elif days_until_expiry <= 30:
                    expiring_soon.append(patient_id)
            
            # Process expired consents
            for patient_id in expired:
                await self._expire_consent(patient_id)
            
            self.logger.info(
                "Consent expiry check completed",
                expiring_soon_count=len(expiring_soon),
                expired_count=len(expired)
            )
            
            return {
                "expiring_soon": expiring_soon,
                "expired": expired
            }
            
        except Exception as e:
            self.logger.error(f"Failed to check consent expiry: {str(e)}")
            return {"expiring_soon": [], "expired": []}
    
    # Helper methods
    
    async def _aggregate_policy_permissions(self, policy_ids: List[str]) -> Dict[str, Any]:
        """Aggregate permissions from multiple policies."""
        aggregated = {
            "purposes": [],
            "data_categories": [],
            "access_categories": [],
            "access_types": [],
            "restrictions": [],
            "conditions": []
        }
        
        for policy_id in policy_ids:
            policy = self.consent_policies[policy_id]
            
            aggregated["purposes"].extend(policy.purpose_codes)
            aggregated["data_categories"].extend(policy.data_categories)
            aggregated["access_categories"].extend([cat.value for cat in policy.access_categories])
            
            # Convert access categories to access types
            if AccessCategory.TREATMENT in policy.access_categories:
                aggregated["access_types"].extend(["read", "write", "update"])
            if AccessCategory.RESEARCH in policy.access_categories:
                aggregated["access_types"].extend(["read", "search"])
            if AccessCategory.EMERGENCY in policy.access_categories:
                aggregated["access_types"].extend(["read", "write", "create"])
            
            # Add policy-specific restrictions
            if not policy.allows_data_sharing:
                aggregated["restrictions"].append("no_external_sharing")
            if not policy.allows_research_use:
                aggregated["restrictions"].append("no_research_use")
            if not policy.allows_commercial_use:
                aggregated["restrictions"].append("no_commercial_use")
            
            # Add age restrictions
            if policy.minimum_age_requirement:
                aggregated["conditions"].append(f"minimum_age_{policy.minimum_age_requirement}")
        
        # Remove duplicates
        for key in aggregated:
            aggregated[key] = list(set(aggregated[key]))
        
        return aggregated
    
    async def _apply_granular_permissions(
        self, 
        base_permissions: Dict[str, Any], 
        granular_permissions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply granular permission overrides."""
        result = base_permissions.copy()
        
        # Apply restrictions (additive)
        if "additional_restrictions" in granular_permissions:
            result["restrictions"].extend(granular_permissions["additional_restrictions"])
        
        # Apply conditions (additive)
        if "additional_conditions" in granular_permissions:
            result["conditions"].extend(granular_permissions["additional_conditions"])
        
        # Remove specific permissions if specified
        if "remove_purposes" in granular_permissions:
            for purpose in granular_permissions["remove_purposes"]:
                if purpose in result["purposes"]:
                    result["purposes"].remove(purpose)
        
        if "remove_data_categories" in granular_permissions:
            for category in granular_permissions["remove_data_categories"]:
                if category in result["data_categories"]:
                    result["data_categories"].remove(category)
        
        return result
    
    async def _calculate_consent_expiry(self, policy_ids: List[str]) -> datetime:
        """Calculate consent expiry based on policies."""
        min_retention = min(
            self.consent_policies[policy_id].retention_period_days 
            for policy_id in policy_ids
        )
        
        return datetime.utcnow() + timedelta(days=min_retention)
    
    async def _create_fhir_consent_resource(
        self, 
        patient_id: str, 
        consent_id: str, 
        policy_ids: List[str],
        permissions: Dict[str, Any]
    ) -> Consent:
        """Create FHIR Consent resource."""
        
        consent = Consent(
            id=consent_id,
            status="active",
            scope=CodeableConcept(
                coding=[
                    Coding(
                        system="http://terminology.hl7.org/CodeSystem/consentscope",
                        code="patient-privacy",
                        display="Privacy Consent"
                    )
                ]
            ),
            category=[
                CodeableConcept(
                    coding=[
                        Coding(
                            system="http://terminology.hl7.org/CodeSystem/consentcategorycodes",
                            code="infa",
                            display="Information Access"
                        )
                    ]
                )
            ],
            patient={
                "reference": f"Patient/{patient_id}"
            },
            dateTime=datetime.utcnow(),
            performer=[
                {
                    "reference": f"Patient/{patient_id}"
                }
            ],
            policyRule=CodeableConcept(
                coding=[
                    Coding(
                        system="http://terminology.hl7.org/CodeSystem/consentpolicycodes",
                        code="cric",
                        display="Common Rule Informed Consent"
                    )
                ]
            )
        )
        
        # Add purpose provisions
        consent.provision = {
            "type": "permit",
            "purpose": []
        }
        
        for purpose in permissions["purposes"]:
            consent.provision["purpose"].append(
                Coding(
                    system="http://terminology.hl7.org/CodeSystem/v3-ActReason",
                    code=purpose
                )
            )
        
        return consent
    
    async def _validate_purpose_permission(
        self, 
        consent_context: ConsentContext, 
        access_purpose: str
    ) -> Dict[str, Any]:
        """Validate if purpose is permitted under consent."""
        
        # Direct purpose match
        if access_purpose in consent_context.granted_purposes:
            return {"permitted": True, "reason": "Direct purpose match"}
        
        # Purpose hierarchy matching
        purpose_hierarchy = {
            "TREAT": ["HOPERAT", "CAREMGT"],
            "RESEARCH": ["HRESCH", "CLINTRCH"],
            "QUAL": ["HMARKT", "HOPERAT"]
        }
        
        for granted_purpose in consent_context.granted_purposes:
            if granted_purpose in purpose_hierarchy:
                if access_purpose in purpose_hierarchy[granted_purpose]:
                    return {"permitted": True, "reason": f"Hierarchical match under {granted_purpose}"}
        
        return {"permitted": False, "reason": f"Purpose {access_purpose} not permitted"}
    
    async def _validate_data_category_permissions(
        self, 
        consent_context: ConsentContext, 
        requested_categories: List[str]
    ) -> Dict[str, Any]:
        """Validate data category permissions."""
        
        permitted_categories = []
        denied_categories = []
        
        for category in requested_categories:
            if category in consent_context.granted_data_categories:
                permitted_categories.append(category)
            else:
                denied_categories.append(category)
        
        return {
            "permitted_categories": permitted_categories,
            "denied_categories": denied_categories
        }
    
    async def _check_access_restrictions(
        self, 
        consent_context: ConsentContext, 
        requesting_user: str,
        access_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check access restrictions and conditions."""
        
        blocked_reasons = []
        additional_conditions = []
        
        # Check time-based restrictions
        current_hour = datetime.utcnow().hour
        if "business_hours_only" in consent_context.restrictions:
            if not (8 <= current_hour <= 17):
                blocked_reasons.append("Access restricted to business hours")
        
        # Check location restrictions
        user_location = access_context.get("user_location")
        if "facility_only" in consent_context.restrictions:
            if user_location != "primary_facility":
                blocked_reasons.append("Access restricted to primary facility")
        
        # Check emergency access
        if "emergency_only" in consent_context.restrictions:
            if not access_context.get("emergency_access", False):
                blocked_reasons.append("Access restricted to emergency situations")
        
        # Add conditional requirements
        if "supervisor_approval" in consent_context.conditions:
            additional_conditions.append("Supervisor approval required")
        
        if "audit_notification" in consent_context.conditions:
            additional_conditions.append("Enhanced audit logging required")
        
        return {
            "blocked": len(blocked_reasons) > 0,
            "reasons": blocked_reasons,
            "additional_conditions": additional_conditions
        }
    
    async def _expire_consent(self, patient_id: str):
        """Process consent expiry."""
        if patient_id in self.active_consents:
            consent_context = self.active_consents[patient_id]
            consent_context.consent_status = ConsentStatus.INACTIVE
            
            # Move to history
            self.consent_history[patient_id].append(consent_context)
            del self.active_consents[patient_id]
            
            # Audit expiry
            await self._audit_consent_action(
                "consent_expired", patient_id, consent_context, {}
            )
    
    async def _audit_consent_action(
        self, 
        action: str, 
        patient_id: str, 
        consent_context: ConsentContext,
        additional_data: Dict[str, Any]
    ):
        """Audit consent management actions."""
        try:
            audit_event = SecurityAuditEvent(
                event_type="consent_management",
                event_subtype=action,
                severity="info",
                event_details={
                    "patient_id": patient_id,
                    "consent_id": consent_context.consent_id,
                    "action": action,
                    "consent_status": consent_context.consent_status.value,
                    **additional_data
                },
                outcome="success"
            )
            
            await self.audit_service.log_security_event(audit_event.dict())
            
        except Exception as e:
            self.logger.error(f"Failed to audit consent action: {str(e)}")