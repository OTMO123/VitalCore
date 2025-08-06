"""
Clinical Workflows Module

Healthcare workflow management with SOC2 Type II compliance, HIPAA protection,
and FHIR R4 compliance. Designed for clinical decision support and workflow automation.

Features:
- Clinical encounters (SOAP notes, ICD-10, CPT codes)
- Care plans & protocols
- Clinical decision support
- Provider-to-provider communication
- Patient timeline aggregation
- Quality measure tracking
- AI data collection for Gemma 3n training

Security:
- SOC2 Type II audit trails
- HIPAA PHI protection
- FHIR R4 compliance
- Provider authentication
- Patient consent verification
"""

from .router import router, public_router
from .schemas import *
from .service import ClinicalWorkflowService

__all__ = [
    "router",
    "public_router", 
    "ClinicalWorkflowService",
]