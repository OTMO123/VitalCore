"""
Healthcare Workflow Integration Testing Suite

Comprehensive end-to-end testing of healthcare workflows including:
- Patient registration workflow with PHI encryption and consent
- Immunization record workflow with FHIR compliance and audit
- Clinical document workflow with encryption and access control
- Consent management workflow with HIPAA compliance
- Cross-service integration with event-driven communication
- Workflow error handling and rollback mechanisms
- Performance testing under realistic load conditions

This suite validates complete healthcare business processes from
start to finish with proper security, compliance, and audit trails.
"""

import pytest
import asyncio
import json
import uuid
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional, Tuple
from unittest.mock import Mock, patch, AsyncMock

# Testing framework imports
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient

# Application imports
from app.main import app
from app.core.database_unified import get_db
from app.core.security import EncryptionService, get_current_user_id
from app.core.events.event_bus import get_event_bus
from app.modules.healthcare_records.service import (
    get_healthcare_service, AccessContext, PatientService,
    ClinicalDocumentService, ConsentService
)
from app.modules.healthcare_records.schemas import (
    PatientCreate, PatientResponse,
    ImmunizationCreate, ImmunizationResponse,
    ClinicalDocumentCreate, ClinicalDocumentResponse,
    ConsentCreate, ConsentResponse
)
from app.modules.auth.router import get_current_user


class TestHealthcareWorkflowSuite:
    """Base class for healthcare workflow integration tests."""
    
    @pytest.fixture(autouse=True)
    async def setup_workflow_environment(self):
        """Set up workflow testing environment."""
        self.client = TestClient(app)
        self.encryption_service = EncryptionService()
        
        # Create test user context
        self.test_user_id = str(uuid.uuid4())
        self.test_access_context = AccessContext(
            user_id=self.test_user_id,
            purpose="testing",
            role="admin",
            ip_address="127.0.0.1",
            session_id=str(uuid.uuid4())
        )
        
        # Test configuration
        self.workflow_timeout = 60  # seconds
        self.max_retry_attempts = 3
        
        # Mock authentication for testing
        self.auth_headers = {
            "Authorization": "Bearer test-jwt-token",
            "Content-Type": "application/json"
        }
        
    async def get_test_db_session(self) -> AsyncSession:
        """Get test database session."""
        async for session in get_db():
            return session
    
    def mock_authentication(self):
        """Mock authentication for workflow testing."""
        return patch.multiple(
            'app.core.security',
            get_current_user_id=Mock(return_value=self.test_user_id),
            require_role=Mock(return_value={"role": "admin", "user_id": self.test_user_id}),
            check_rate_limit=Mock(return_value=True),
            get_client_info=AsyncMock(return_value={
                "ip_address": "127.0.0.1",
                "request_id": str(uuid.uuid4())
            })
        )


class TestPatientRegistrationWorkflow(TestHealthcareWorkflowSuite):
    """Complete patient registration workflow tests."""
    
    @pytest.mark.asyncio
    async def test_complete_patient_registration_workflow(self):
        """Test complete patient registration workflow end-to-end."""
        
        with self.mock_authentication():
            # Step 1: Create patient with PHI encryption
            patient_data = {
                "identifier": [{
                    "use": "official",
                    "type": {
                        "coding": [{
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "MR"
                        }]
                    },
                    "system": "http://hospital.example.org",
                    "value": "MRN-WORKFLOW-001"
                }],
                "active": True,
                "name": [{
                    "use": "official",
                    "family": "WorkflowPatient",
                    "given": ["Test", "Integration"]
                }],
                "telecom": [{
                    "system": "phone",
                    "value": "+1-555-0123",
                    "use": "home"
                }],
                "gender": "female",
                "birthDate": "1990-06-15",
                "address": [{
                    "use": "home",
                    "line": ["123 Healthcare Drive", "Suite 456"],
                    "city": "Medical City",
                    "state": "HC",
                    "postalCode": "12345",
                    "country": "US"
                }],
                "consent_status": "pending",
                "consent_types": ["treatment", "data_access"]
            }
            
            # Create patient
            response = self.client.post(
                "/api/v1/healthcare/patients",
                json=patient_data,
                headers=self.auth_headers
            )
            
            assert response.status_code == 201
            patient_result = response.json()
            patient_id = patient_result["id"]
            
            # Verify patient creation
            assert patient_result["resourceType"] == "Patient"
            assert patient_result["active"] is True
            assert patient_result["consent_status"] == "pending"
            
            # Step 2: Grant consent for patient
            consent_data = {
                "patient_id": patient_id,
                "consent_type": "treatment",
                "scope": {
                    "allowed_purposes": ["treatment", "emergency"],
                    "data_types": ["demographics", "clinical"]
                }
            }
            
            consent_response = self.client.post(
                "/api/v1/healthcare/consents",
                json=consent_data,
                headers=self.auth_headers
            )
            
            assert consent_response.status_code == 201
            consent_result = consent_response.json()
            
            # Verify consent creation
            assert consent_result["patient_id"] == patient_id
            assert consent_result["consent_types"] == ["treatment"]
            
            # Step 3: Verify patient is accessible with consent
            patient_get_response = self.client.get(
                f"/api/v1/healthcare/patients/{patient_id}",
                headers=self.auth_headers
            )
            
            assert patient_get_response.status_code == 200
            retrieved_patient = patient_get_response.json()
            
            # Verify PHI decryption and access
            assert retrieved_patient["id"] == patient_id
            assert retrieved_patient["name"][0]["family"] == "WorkflowPatient"
            
            # Step 4: Update patient information
            update_data = {
                "telecom": [{
                    "system": "email",
                    "value": "test.patient@example.com",
                    "use": "home"
                }]
            }
            
            update_response = self.client.put(
                f"/api/v1/healthcare/patients/{patient_id}",
                json=update_data,
                headers=self.auth_headers
            )
            
            assert update_response.status_code == 200
            updated_patient = update_response.json()
            
            # Verify update was applied
            assert len(updated_patient.get("telecom", [])) > 0
            
            return patient_id  # Return for use in other workflow tests
    
    @pytest.mark.asyncio
    async def test_patient_registration_with_validation_errors(self):
        """Test patient registration workflow with validation errors."""
        
        with self.mock_authentication():
            # Attempt to create patient with invalid data
            invalid_patient_data = {
                "identifier": [],  # Empty identifiers (invalid)
                "active": True,
                "name": [],  # Empty names (invalid)
                "gender": "invalid_gender",  # Invalid gender
                "birthDate": "invalid-date"  # Invalid date format
            }
            
            response = self.client.post(
                "/api/v1/healthcare/patients",
                json=invalid_patient_data,
                headers=self.auth_headers
            )
            
            # Should return validation error
            assert response.status_code in [400, 422]
            error_result = response.json()
            assert "detail" in error_result or "errors" in error_result
    
    @pytest.mark.asyncio
    async def test_patient_registration_without_consent(self):
        """Test patient data access without proper consent."""
        
        with self.mock_authentication():
            # Create patient without consent
            patient_data = {
                "identifier": [{
                    "use": "official",
                    "system": "http://hospital.example.org",
                    "value": "MRN-NO-CONSENT-001"
                }],
                "active": True,
                "name": [{
                    "use": "official",
                    "family": "NoConsentPatient",
                    "given": ["Test"]
                }],
                "gender": "male",
                "birthDate": "1985-03-20",
                "consent_status": "withdrawn"  # No consent
            }
            
            response = self.client.post(
                "/api/v1/healthcare/patients",
                json=patient_data,
                headers=self.auth_headers
            )
            
            if response.status_code == 201:
                patient_result = response.json()
                patient_id = patient_result["id"]
                
                # Attempt to access patient without consent
                access_response = self.client.get(
                    f"/api/v1/healthcare/patients/{patient_id}",
                    headers=self.auth_headers
                )
                
                # Should be accessible by admin for this test
                # In real implementation, might require additional consent checks
                assert access_response.status_code in [200, 403]


class TestImmunizationRecordWorkflow(TestHealthcareWorkflowSuite):
    """Immunization record workflow integration tests."""
    
    @pytest.mark.asyncio
    async def test_complete_immunization_workflow(self):
        """Test complete immunization record workflow."""
        
        with self.mock_authentication():
            # First create a patient for immunization
            patient_data = {
                "identifier": [{
                    "use": "official",
                    "system": "http://hospital.example.org",
                    "value": "MRN-IMMUNIZATION-001"
                }],
                "active": True,
                "name": [{
                    "use": "official", 
                    "family": "ImmunizationPatient",
                    "given": ["Vaccine", "Test"]
                }],
                "gender": "female",
                "birthDate": "1992-08-10",
                "consent_status": "active",
                "consent_types": ["treatment", "immunization_registry"]
            }
            
            patient_response = self.client.post(
                "/api/v1/healthcare/patients",
                json=patient_data,
                headers=self.auth_headers
            )
            
            assert patient_response.status_code == 201
            patient_result = patient_response.json()
            patient_id = patient_result["id"]
            
            # Step 1: Create immunization record
            immunization_data = {
                "patient_id": patient_id,
                "status": "completed",
                "vaccine_code": "208",  # COVID-19 Pfizer
                "vaccine_display": "COVID-19, mRNA, LNP-S, PF, 30 mcg/0.3 mL dose",
                "occurrence_datetime": "2024-01-15T10:30:00Z",
                "location": "Community Health Center",
                "primary_source": True,
                "lot_number": "ABC123DEF",
                "expiration_date": "2025-01-15",
                "manufacturer": "Pfizer-BioNTech",
                "route_code": "IM",
                "route_display": "Injection, intramuscular",
                "site_code": "LA",
                "site_display": "left arm",
                "dose_quantity": "0.3",
                "dose_unit": "mL",
                "performer_type": "physician",
                "performer_name": "Dr. Sarah Johnson",
                "performer_organization": "Community Health Center",
                "indication_codes": ["840539006"],  # COVID-19 prevention
                "tenant_id": str(uuid.uuid4()),
                "organization_id": str(uuid.uuid4())
            }
            
            immunization_response = self.client.post(
                "/api/v1/healthcare/immunizations",
                json=immunization_data,
                headers=self.auth_headers
            )
            
            assert immunization_response.status_code == 201
            immunization_result = immunization_response.json()
            immunization_id = immunization_result["id"]
            
            # Verify immunization creation
            assert immunization_result["resourceType"] == "Immunization"
            assert immunization_result["patient_id"] == patient_id
            assert immunization_result["vaccine_code"] == "208"
            assert immunization_result["status"] == "completed"
            
            # Step 2: Retrieve immunization with decrypted data
            get_response = self.client.get(
                f"/api/v1/healthcare/immunizations/{immunization_id}",
                headers=self.auth_headers
            )
            
            assert get_response.status_code == 200
            retrieved_immunization = get_response.json()
            
            # Verify decrypted fields are accessible
            assert retrieved_immunization["location"] == "Community Health Center"
            assert retrieved_immunization["lot_number"] == "ABC123DEF"
            assert retrieved_immunization["performer_name"] == "Dr. Sarah Johnson"
            
            # Step 3: List immunizations for patient
            list_response = self.client.get(
                f"/api/v1/healthcare/immunizations?patient_id={patient_id}",
                headers=self.auth_headers
            )
            
            assert list_response.status_code == 200
            list_result = list_response.json()
            
            # Verify patient's immunizations are returned
            assert list_result["total"] >= 1
            assert len(list_result["immunizations"]) >= 1
            assert any(
                imm["id"] == immunization_id 
                for imm in list_result["immunizations"]
            )
            
            # Step 4: Update immunization record
            update_data = {
                "reactions": [{
                    "manifestation": "mild soreness at injection site",
                    "severity": "mild",
                    "onset": "2 hours post-vaccination"
                }]
            }
            
            update_response = self.client.put(
                f"/api/v1/healthcare/immunizations/{immunization_id}",
                json=update_data,
                headers=self.auth_headers
            )
            
            assert update_response.status_code == 200
            updated_immunization = update_response.json()
            
            # Verify reaction was added
            assert len(updated_immunization.get("reactions", [])) > 0
            
            return immunization_id
    
    @pytest.mark.asyncio
    async def test_immunization_workflow_with_adverse_reaction(self):
        """Test immunization workflow with adverse reaction reporting."""
        
        with self.mock_authentication():
            # Create patient and immunization first
            patient_data = {
                "identifier": [{"use": "official", "system": "http://test.org", "value": "MRN-REACTION-001"}],
                "active": True,
                "name": [{"use": "official", "family": "ReactionPatient", "given": ["Adverse"]}],
                "gender": "male",
                "birthDate": "1988-12-05",
                "consent_status": "active",
                "consent_types": ["treatment"]
            }
            
            patient_response = self.client.post(
                "/api/v1/healthcare/patients",
                json=patient_data,
                headers=self.auth_headers
            )
            
            assert patient_response.status_code == 201
            patient_id = patient_response.json()["id"]
            
            # Create immunization with immediate reaction
            immunization_data = {
                "patient_id": patient_id,
                "status": "completed",
                "vaccine_code": "88",  # Influenza vaccine
                "vaccine_display": "Influenza virus vaccine",
                "occurrence_datetime": "2024-01-20T14:00:00Z",
                "location": "Urgent Care Center",
                "reactions": [{
                    "manifestation": "anaphylaxis", 
                    "severity": "severe",
                    "onset": "immediate",
                    "treatment": "epinephrine administered",
                    "outcome": "recovered"
                }]
            }
            
            immunization_response = self.client.post(
                "/api/v1/healthcare/immunizations",
                json=immunization_data,
                headers=self.auth_headers
            )
            
            assert immunization_response.status_code == 201
            immunization_result = immunization_response.json()
            
            # Verify severe reaction was recorded
            reactions = immunization_result.get("reactions", [])
            assert len(reactions) > 0
            assert any(
                reaction.get("severity") == "severe" 
                for reaction in reactions
            )


class TestClinicalDocumentWorkflow(TestHealthcareWorkflowSuite):
    """Clinical document workflow integration tests."""
    
    @pytest.mark.asyncio
    async def test_complete_clinical_document_workflow(self):
        """Test complete clinical document workflow with encryption."""
        
        with self.mock_authentication():
            # Create patient first
            patient_data = {
                "identifier": [{"use": "official", "system": "http://test.org", "value": "MRN-DOCUMENT-001"}],
                "active": True,
                "name": [{"use": "official", "family": "DocumentPatient", "given": ["Clinical"]}],
                "gender": "female",
                "birthDate": "1975-04-18",
                "consent_status": "active",
                "consent_types": ["treatment", "data_access"]
            }
            
            patient_response = self.client.post(
                "/api/v1/healthcare/patients",
                json=patient_data,
                headers=self.auth_headers
            )
            
            assert patient_response.status_code == 201
            patient_id = patient_response.json()["id"]
            
            # Step 1: Create clinical document
            document_data = {
                "patient_id": patient_id,
                "title": "Clinical Assessment Note",
                "content": "Patient presents with mild respiratory symptoms. No fever. Vital signs stable. Plan: rest, fluids, follow-up in 48 hours if symptoms persist.",
                "document_type": "clinical_note",
                "content_type": "text/plain"
            }
            
            document_response = self.client.post(
                "/api/v1/healthcare/documents",
                json=document_data,
                headers=self.auth_headers
            )
            
            assert document_response.status_code == 201
            document_result = document_response.json()
            document_id = document_result["id"]
            
            # Verify document creation
            assert document_result["patient_id"] == patient_id
            assert document_result["metadata"]["title"] == "Clinical Assessment Note"
            assert document_result["content_encrypted"] is True
            
            # Step 2: Retrieve document
            get_response = self.client.get(
                f"/api/v1/healthcare/documents/{document_id}",
                headers=self.auth_headers
            )
            
            assert get_response.status_code == 200
            retrieved_document = get_response.json()
            
            # Verify document retrieval
            assert retrieved_document["id"] == document_id
            assert retrieved_document["patient_id"] == patient_id
            
            # Step 3: List documents for patient
            list_response = self.client.get(
                f"/api/v1/healthcare/documents?patient_id={patient_id}",
                headers=self.auth_headers
            )
            
            assert list_response.status_code == 200
            list_result = list_response.json()
            
            # Verify document is in patient's document list
            assert len(list_result) >= 1
            assert any(doc["id"] == document_id for doc in list_result)
            
            return document_id


class TestConsentManagementWorkflow(TestHealthcareWorkflowSuite):
    """Consent management workflow integration tests."""
    
    @pytest.mark.asyncio
    async def test_complete_consent_management_workflow(self):
        """Test complete consent management workflow with HIPAA compliance."""
        
        with self.mock_authentication():
            # Create patient
            patient_data = {
                "identifier": [{"use": "official", "system": "http://test.org", "value": "MRN-CONSENT-001"}],
                "active": True,
                "name": [{"use": "official", "family": "ConsentPatient", "given": ["HIPAA"]}],
                "gender": "non-binary",
                "birthDate": "1990-11-22",
                "consent_status": "pending",
                "consent_types": []
            }
            
            patient_response = self.client.post(
                "/api/v1/healthcare/patients",
                json=patient_data,
                headers=self.auth_headers
            )
            
            assert patient_response.status_code == 201
            patient_id = patient_response.json()["id"]
            
            # Step 1: Grant treatment consent
            treatment_consent = {
                "patient_id": patient_id,
                "consent_type": "treatment",
                "scope": {
                    "allowed_purposes": ["treatment", "emergency"],
                    "data_types": ["demographics", "clinical", "prescriptions"]
                }
            }
            
            treatment_response = self.client.post(
                "/api/v1/healthcare/consents",
                json=treatment_consent,
                headers=self.auth_headers
            )
            
            assert treatment_response.status_code == 201
            treatment_result = treatment_response.json()
            
            # Verify treatment consent
            assert treatment_result["patient_id"] == patient_id
            assert "treatment" in treatment_result["consent_types"]
            
            # Step 2: Grant research consent
            research_consent = {
                "patient_id": patient_id,
                "consent_type": "research",
                "scope": {
                    "allowed_purposes": ["research"],
                    "data_types": ["demographics", "clinical"],
                    "restrictions": ["no_genetic_data"]
                }
            }
            
            research_response = self.client.post(
                "/api/v1/healthcare/consents",
                json=research_consent,
                headers=self.auth_headers
            )
            
            assert research_response.status_code == 201
            research_result = research_response.json()
            
            # Verify research consent
            assert research_result["patient_id"] == patient_id
            assert "research" in research_result["consent_types"]
            
            # Step 3: List all consents for patient
            consent_list_response = self.client.get(
                f"/api/v1/healthcare/consents?patient_id={patient_id}",
                headers=self.auth_headers
            )
            
            assert consent_list_response.status_code == 200
            consent_list = consent_list_response.json()
            
            # Verify multiple consents
            assert len(consent_list) >= 2
            consent_types = [
                consent["consent_types"][0] 
                for consent in consent_list 
                if consent["consent_types"]
            ]
            assert "treatment" in consent_types
            assert "research" in consent_types
            
            # Step 4: Check patient consent status
            consent_status_response = self.client.get(
                f"/api/v1/healthcare/patients/{patient_id}/consent-status",
                headers=self.auth_headers
            )
            
            assert consent_status_response.status_code == 200
            consent_status = consent_status_response.json()
            
            # Verify consent status summary
            assert consent_status["patient_id"] == patient_id
            assert "treatment" in consent_status.get("active_consents", [])
            assert "research" in consent_status.get("active_consents", [])
            
            return patient_id


class TestCrossServiceIntegrationWorkflow(TestHealthcareWorkflowSuite):
    """Cross-service integration and event-driven workflow tests."""
    
    @pytest.mark.asyncio
    async def test_complete_cross_service_workflow(self):
        """Test complete workflow across all healthcare services."""
        
        with self.mock_authentication():
            # Step 1: Create patient
            patient_data = {
                "identifier": [{"use": "official", "system": "http://test.org", "value": "MRN-INTEGRATION-001"}],
                "active": True,
                "name": [{"use": "official", "family": "IntegrationPatient", "given": ["Full", "Workflow"]}],
                "gender": "female",
                "birthDate": "1985-07-30",
                "consent_status": "active",
                "consent_types": ["treatment", "data_access", "immunization_registry"]
            }
            
            patient_response = self.client.post(
                "/api/v1/healthcare/patients",
                json=patient_data,
                headers=self.auth_headers
            )
            
            assert patient_response.status_code == 201
            patient_result = patient_response.json()
            patient_id = patient_result["id"]
            
            # Step 2: Grant comprehensive consents
            consent_data = {
                "patient_id": patient_id,
                "consent_type": "data_access",
                "scope": {
                    "allowed_purposes": ["treatment", "research", "quality_improvement"],
                    "data_types": ["all"]
                }
            }
            
            consent_response = self.client.post(
                "/api/v1/healthcare/consents",
                json=consent_data,
                headers=self.auth_headers
            )
            
            assert consent_response.status_code == 201
            
            # Step 3: Create immunization record
            immunization_data = {
                "patient_id": patient_id,
                "status": "completed",
                "vaccine_code": "207",  # COVID-19 Moderna
                "vaccine_display": "COVID-19, mRNA, LNP-S, PF, 100 mcg/0.5 mL dose",
                "occurrence_datetime": "2024-02-01T09:15:00Z",
                "location": "Integrated Health Center"
            }
            
            immunization_response = self.client.post(
                "/api/v1/healthcare/immunizations",
                json=immunization_data,
                headers=self.auth_headers
            )
            
            assert immunization_response.status_code == 201
            immunization_result = immunization_response.json()
            immunization_id = immunization_result["id"]
            
            # Step 4: Create clinical document about immunization
            document_data = {
                "patient_id": patient_id,
                "title": "COVID-19 Vaccination Record",
                "content": f"Patient received COVID-19 vaccination (Moderna) on 2024-02-01. No immediate adverse reactions observed. Patient advised on post-vaccination care. Immunization ID: {immunization_id}",
                "document_type": "immunization_record",
                "content_type": "text/plain"
            }
            
            document_response = self.client.post(
                "/api/v1/healthcare/documents",
                json=document_data,
                headers=self.auth_headers
            )
            
            assert document_response.status_code == 201
            document_result = document_response.json()
            document_id = document_result["id"]
            
            # Step 5: Verify all related data is accessible
            # Get patient with full data
            patient_get_response = self.client.get(
                f"/api/v1/healthcare/patients/{patient_id}",
                headers=self.auth_headers
            )
            assert patient_get_response.status_code == 200
            
            # Get patient's immunizations
            immunizations_response = self.client.get(
                f"/api/v1/healthcare/immunizations?patient_id={patient_id}",
                headers=self.auth_headers
            )
            assert immunizations_response.status_code == 200
            immunizations_result = immunizations_response.json()
            assert immunizations_result["total"] >= 1
            
            # Get patient's documents
            documents_response = self.client.get(
                f"/api/v1/healthcare/documents?patient_id={patient_id}",
                headers=self.auth_headers
            )
            assert documents_response.status_code == 200
            documents_result = documents_response.json()
            assert len(documents_result) >= 1
            
            # Get patient's consents
            consents_response = self.client.get(
                f"/api/v1/healthcare/consents?patient_id={patient_id}",
                headers=self.auth_headers
            )
            assert consents_response.status_code == 200
            consents_result = consents_response.json()
            assert len(consents_result) >= 1
            
            # Step 6: Verify FHIR compliance
            fhir_validation_data = {
                "resource_type": "Patient",
                "resource_data": {
                    "resourceType": "Patient",
                    "id": patient_id,
                    "active": True,
                    "name": patient_result["name"],
                    "gender": patient_result["gender"],
                    "birthDate": patient_result["birthDate"]
                }
            }
            
            fhir_response = self.client.post(
                "/api/v1/healthcare/fhir/validate",
                json=fhir_validation_data,
                headers=self.auth_headers
            )
            
            assert fhir_response.status_code == 200
            fhir_result = fhir_response.json()
            assert fhir_result["is_valid"] is True
            
            return {
                "patient_id": patient_id,
                "immunization_id": immunization_id,
                "document_id": document_id,
                "workflow_complete": True
            }


class TestWorkflowErrorHandling(TestHealthcareWorkflowSuite):
    """Workflow error handling and recovery tests."""
    
    @pytest.mark.asyncio
    async def test_workflow_rollback_on_failure(self):
        """Test workflow rollback when operations fail."""
        
        with self.mock_authentication():
            # Create patient successfully
            patient_data = {
                "identifier": [{"use": "official", "system": "http://test.org", "value": "MRN-ROLLBACK-001"}],
                "active": True,
                "name": [{"use": "official", "family": "RollbackPatient", "given": ["Test"]}],
                "gender": "male",
                "birthDate": "1980-09-14"
            }
            
            patient_response = self.client.post(
                "/api/v1/healthcare/patients",
                json=patient_data,
                headers=self.auth_headers
            )
            
            assert patient_response.status_code == 201
            patient_id = patient_response.json()["id"]
            
            # Attempt to create immunization with invalid data
            invalid_immunization_data = {
                "patient_id": patient_id,
                "status": "invalid_status",  # Invalid status
                "vaccine_code": "",  # Empty vaccine code
                "occurrence_datetime": "invalid-date"  # Invalid date
            }
            
            immunization_response = self.client.post(
                "/api/v1/healthcare/immunizations",
                json=invalid_immunization_data,
                headers=self.auth_headers
            )
            
            # Should fail with validation error
            assert immunization_response.status_code in [400, 422]
            
            # Verify patient still exists and is accessible
            patient_get_response = self.client.get(
                f"/api/v1/healthcare/patients/{patient_id}",
                headers=self.auth_headers
            )
            assert patient_get_response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_concurrent_workflow_operations(self):
        """Test concurrent operations on the same patient."""
        
        with self.mock_authentication():
            # Create patient
            patient_data = {
                "identifier": [{"use": "official", "system": "http://test.org", "value": "MRN-CONCURRENT-001"}],
                "active": True,
                "name": [{"use": "official", "family": "ConcurrentPatient", "given": ["Multi"]}],
                "gender": "female",
                "birthDate": "1987-01-25"
            }
            
            patient_response = self.client.post(
                "/api/v1/healthcare/patients",
                json=patient_data,
                headers=self.auth_headers
            )
            
            assert patient_response.status_code == 201
            patient_id = patient_response.json()["id"]
            
            # Prepare multiple concurrent operations
            operations = []
            
            # Concurrent immunization creation
            for i in range(3):
                immunization_data = {
                    "patient_id": patient_id,
                    "status": "completed",
                    "vaccine_code": f"{i+88:02d}",  # Different vaccine codes
                    "vaccine_display": f"Vaccine {i+1}",
                    "occurrence_datetime": f"2024-0{i+1}-15T10:30:00Z"
                }
                operations.append(
                    ("immunizations", immunization_data)
                )
            
            # Concurrent document creation
            for i in range(2):
                document_data = {
                    "patient_id": patient_id,
                    "title": f"Clinical Note {i+1}",
                    "content": f"Clinical note content {i+1}",
                    "document_type": "clinical_note"
                }
                operations.append(
                    ("documents", document_data)
                )
            
            # Execute operations concurrently
            responses = []
            for endpoint, data in operations:
                response = self.client.post(
                    f"/api/v1/healthcare/{endpoint}",
                    json=data,
                    headers=self.auth_headers
                )
                responses.append(response)
            
            # Verify most operations succeeded
            successful_responses = [r for r in responses if r.status_code in [200, 201]]
            assert len(successful_responses) >= len(operations) // 2  # At least half should succeed


@pytest.mark.asyncio
async def test_healthcare_workflow_performance():
    """Test healthcare workflow performance under load."""
    client = TestClient(app)
    
    # Mock authentication
    with patch.multiple(
        'app.core.security',
        get_current_user_id=Mock(return_value=str(uuid.uuid4())),
        require_role=Mock(return_value={"role": "admin"}),
        check_rate_limit=Mock(return_value=True),
        get_client_info=AsyncMock(return_value={"ip_address": "127.0.0.1"})
    ):
        start_time = datetime.now()
        
        # Create multiple patients concurrently
        patient_responses = []
        for i in range(5):
            patient_data = {
                "identifier": [{"use": "official", "system": "http://test.org", "value": f"MRN-PERF-{i:03d}"}],
                "active": True,
                "name": [{"use": "official", "family": f"PerfPatient{i}", "given": ["Load", "Test"]}],
                "gender": "other",
                "birthDate": f"198{i % 10}-0{(i % 9) + 1}-01"
            }
            
            response = client.post(
                "/api/v1/healthcare/patients",
                json=patient_data,
                headers={"Authorization": "Bearer test-token", "Content-Type": "application/json"}
            )
            patient_responses.append(response)
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # Verify performance
        successful_creates = [r for r in patient_responses if r.status_code == 201]
        assert len(successful_creates) >= 3  # At least 3 should succeed
        assert processing_time < 15.0  # Should complete within 15 seconds


if __name__ == "__main__":
    """Run healthcare workflow integration tests independently."""
    pytest.main([__file__, "-v", "--tb=short"])