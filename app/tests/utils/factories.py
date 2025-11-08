"""
Test data factories for consistent, deterministic test data generation.

Replaces random data generation with controlled factories.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
import uuid


class TestDataFactory:
    """
    Factory for generating consistent test data.

    Uses deterministic patterns instead of random data for reproducibility.
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize factory with optional seed for reproducibility.

        Args:
            seed: Seed for any random operations (not currently used, but reserved)
        """
        self.seed = seed
        self._counter = 0

    def _next_id(self) -> int:
        """Generate next sequential ID."""
        self._counter += 1
        return self._counter

    def user_data(
        self,
        username: Optional[str] = None,
        email: Optional[str] = None,
        role: str = "patient",
        **overrides
    ) -> Dict[str, Any]:
        """
        Generate test user data.

        Args:
            username: Custom username (auto-generated if None)
            email: Custom email (auto-generated if None)
            role: User role
            **overrides: Additional fields to override

        Returns:
            Dictionary with user data
        """
        user_id = self._next_id()
        base_data = {
            "id": str(uuid.UUID(int=user_id)),
            "username": username or f"testuser_{user_id}",
            "email": email or f"testuser_{user_id}@example.com",
            "full_name": f"Test User {user_id}",
            "role": role,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
        }
        base_data.update(overrides)
        return base_data

    def patient_data(
        self,
        patient_id: Optional[str] = None,
        **overrides
    ) -> Dict[str, Any]:
        """Generate test patient data."""
        pid = patient_id or self._next_id()
        base_data = {
            "id": str(pid),
            "first_name": f"Patient{pid}",
            "last_name": f"Test{pid}",
            "date_of_birth": "1980-01-01",
            "gender": "unknown",
            "mrn": f"MRN{str(pid).zfill(8)}",
            "ssn_encrypted": None,
        }
        base_data.update(overrides)
        return base_data

    def immunization_data(
        self,
        patient_id: Optional[str] = None,
        vaccine_code: str = "COVID19",
        **overrides
    ) -> Dict[str, Any]:
        """Generate test immunization data."""
        imm_id = self._next_id()
        base_data = {
            "id": str(imm_id),
            "patient_id": patient_id or "test_patient_1",
            "vaccine_code": vaccine_code,
            "vaccine_name": f"{vaccine_code} Vaccine",
            "administered_date": datetime.now(timezone.utc).isoformat(),
            "dose_number": 1,
            "series_doses": 2,
            "lot_number": f"LOT{str(imm_id).zfill(6)}",
            "site": "left_arm",
            "route": "intramuscular",
        }
        base_data.update(overrides)
        return base_data

    def fhir_patient_resource(
        self,
        patient_id: Optional[str] = None,
        **overrides
    ) -> Dict[str, Any]:
        """Generate FHIR R4 compliant patient resource."""
        pid = patient_id or str(self._next_id())
        base_data = {
            "resourceType": "Patient",
            "id": pid,
            "identifier": [
                {
                    "system": "http://hospital.example.org",
                    "value": f"MRN{pid.zfill(8)}"
                }
            ],
            "name": [
                {
                    "use": "official",
                    "family": f"Test{pid}",
                    "given": [f"Patient{pid}"]
                }
            ],
            "gender": "unknown",
            "birthDate": "1980-01-01",
            "active": True,
        }
        base_data.update(overrides)
        return base_data

    def fhir_immunization_resource(
        self,
        patient_id: str,
        vaccine_code: str = "207",
        **overrides
    ) -> Dict[str, Any]:
        """Generate FHIR R4 compliant immunization resource."""
        imm_id = self._next_id()
        base_data = {
            "resourceType": "Immunization",
            "id": str(imm_id),
            "status": "completed",
            "vaccineCode": {
                "coding": [
                    {
                        "system": "http://hl7.org/fhir/sid/cvx",
                        "code": vaccine_code,
                        "display": "COVID-19 vaccine"
                    }
                ]
            },
            "patient": {
                "reference": f"Patient/{patient_id}"
            },
            "occurrenceDateTime": datetime.now(timezone.utc).isoformat(),
            "primarySource": True,
        }
        base_data.update(overrides)
        return base_data

    def audit_log_data(
        self,
        user_id: str,
        action: str = "test_action",
        **overrides
    ) -> Dict[str, Any]:
        """Generate audit log data."""
        log_id = self._next_id()
        base_data = {
            "id": str(log_id),
            "event_type": "test.event",
            "user_id": user_id,
            "action": action,
            "outcome": "success",
            "timestamp": datetime.now(timezone.utc),
            "event_data": {},
        }
        base_data.update(overrides)
        return base_data

    def oauth2_token_response(
        self,
        access_token: Optional[str] = None,
        **overrides
    ) -> Dict[str, Any]:
        """Generate OAuth2 token response."""
        token_id = self._next_id()
        base_data = {
            "access_token": access_token or f"token_{token_id}",
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": "read write",
        }
        base_data.update(overrides)
        return base_data

    def api_error_response(
        self,
        status_code: int = 400,
        error: str = "test_error",
        **overrides
    ) -> Dict[str, Any]:
        """Generate API error response."""
        base_data = {
            "status_code": status_code,
            "error": error,
            "message": f"Test error: {error}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        base_data.update(overrides)
        return base_data

    def document_metadata(
        self,
        document_id: Optional[str] = None,
        patient_id: Optional[str] = None,
        **overrides
    ) -> Dict[str, Any]:
        """Generate document metadata."""
        doc_id = document_id or str(self._next_id())
        base_data = {
            "id": doc_id,
            "patient_id": patient_id or "test_patient_1",
            "document_type": "clinical_note",
            "title": f"Test Document {doc_id}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "file_size": 1024,
            "mime_type": "application/pdf",
            "classification": "medical_record",
        }
        base_data.update(overrides)
        return base_data

    def performance_metrics(
        self,
        response_time: float = 100.0,
        **overrides
    ) -> Dict[str, Any]:
        """Generate performance metrics data."""
        base_data = {
            "response_time_ms": response_time,
            "cpu_percent": 25.0,
            "memory_mb": 512.0,
            "throughput_rps": 100.0,
            "error_rate": 0.0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        base_data.update(overrides)
        return base_data

    def reset(self):
        """Reset the factory counter."""
        self._counter = 0


# Global factory instance for convenience
default_factory = TestDataFactory()


# Convenience functions using default factory
def create_user(**kwargs) -> Dict[str, Any]:
    """Create user data using default factory."""
    return default_factory.user_data(**kwargs)


def create_patient(**kwargs) -> Dict[str, Any]:
    """Create patient data using default factory."""
    return default_factory.patient_data(**kwargs)


def create_immunization(**kwargs) -> Dict[str, Any]:
    """Create immunization data using default factory."""
    return default_factory.immunization_data(**kwargs)


def create_fhir_patient(**kwargs) -> Dict[str, Any]:
    """Create FHIR patient resource using default factory."""
    return default_factory.fhir_patient_resource(**kwargs)


def create_fhir_immunization(patient_id: str, **kwargs) -> Dict[str, Any]:
    """Create FHIR immunization resource using default factory."""
    return default_factory.fhir_immunization_resource(patient_id, **kwargs)
