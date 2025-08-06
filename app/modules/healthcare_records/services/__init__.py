"""
Healthcare Records Services Package

Service layer implementations for healthcare records domain.
Provides business logic encapsulation with PHI encryption and audit logging.
"""

from .immunization_service import ImmunizationService
from .patient_service import PatientService

__all__ = ["ImmunizationService", "PatientService"]