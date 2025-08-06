"""
FHIR Security Module for Healthcare Platform V2.0

Enhanced FHIR R4 compliance with security labels, consent management,
access control, and advanced privacy controls for healthcare AI systems.
"""

from .schemas import (
    SecurityLabel, SecurityClassification, ConsentPolicy, ConsentContext,
    ProvenanceRecord, AccessDecision, ComplianceResult, FHIRSecurityConfig,
    SecurityAuditEvent, BreachNotification, SecurityReport
)
from .fhir_secure_handler import FHIRSecureHandler
from .security_labels import SecurityLabelManager
from .consent_manager import ConsentManager  
from .provenance_tracker import ProvenanceTracker
from .router import router

__all__ = [
    # Schemas
    "SecurityLabel", "SecurityClassification", "ConsentPolicy", "ConsentContext",
    "ProvenanceRecord", "AccessDecision", "ComplianceResult", "FHIRSecurityConfig",
    "SecurityAuditEvent", "BreachNotification", "SecurityReport",
    
    # Core components
    "FHIRSecureHandler", "SecurityLabelManager", "ConsentManager", "ProvenanceTracker",
    
    # API router
    "router"
]