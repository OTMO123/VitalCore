"""
Healthcare Records Bounded Context

This module implements the Healthcare Records bounded context as defined in the
DDD Context Map. It manages PHI/PII data for patients, clinical documents,
and ensures FHIR R4 compliance.

Key Aggregates:
- Patient: Encrypted PHI/PII management with consent tracking
- ClinicalDocument: FHIR-compliant document handling with access controls

Domain Events:
- PHI.Accessed
- Patient.ConsentUpdated  
- ClinicalDocument.Created
- Patient.Created
- PHI.Encrypted
"""

from .schemas import (
    PatientCreate,
    PatientUpdate, 
    PatientResponse,
    ClinicalDocumentCreate,
    ClinicalDocumentResponse,
    ConsentRequest,
    ConsentResponse,
    PHIAccessRequest
)

from .service import (
    HealthcareRecordsService,
    PatientService,
    ClinicalDocumentService,
    ConsentService,
    PHIAccessAuditService
)

__all__ = [
    "PatientCreate",
    "PatientUpdate",
    "PatientResponse", 
    "ClinicalDocumentCreate",
    "ClinicalDocumentResponse",
    "ConsentRequest",
    "ConsentResponse",
    "PHIAccessRequest",
    "HealthcareRecordsService",
    "PatientService",
    "ClinicalDocumentService", 
    "ConsentService",
    "PHIAccessAuditService",
]