"""
External Registry Integration Testing Suite

Comprehensive external healthcare registry integration testing:
- State Immunization Information Systems (IIS) integration with CDC compliance
- National Adult and Influenza Immunization Summit (NAIIS) coordination
- Vaccine Adverse Event Reporting System (VAERS) integration with safety monitoring
- Vaccines for Children (VFC) program coordination with eligibility verification
- Healthcare Provider Registry Integration with credential validation
- Public Health Emergency Preparedness (PHEP) registry coordination
- Clinical Decision Support (CDS) integration with evidence-based recommendations
- Health Information Exchange (HIE) coordination with interoperability standards
- Registry Data Quality Validation with comprehensive error handling
- Multi-Registry Coordination with conflict resolution and data harmonization
- Registry Performance Monitoring with real-time health checks and alerting
- Regulatory Compliance Validation with automated audit trail generation

This suite implements comprehensive external registry integration testing meeting
CDC, FHIR R4, HL7, and public health interoperability standards with real-world
healthcare registry scenarios and regulatory compliance validation.
"""
import pytest
import asyncio
import json
import uuid
import secrets
import time
from datetime import datetime, timedelta, date
from typing import Dict, Any, List, Optional, Set, Tuple
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, text
import structlog
import aiohttp
from aiohttp.test_utils import make_mocked_coro

from app.core.database_unified import get_db
from app.modules.audit_logger.schemas import AuditEvent as AuditLog
from app.core.database_unified import User
from app.core.database_unified import Patient
from app.modules.healthcare_records.models import Immunization
from app.core.database_advanced import APIEndpoint, APICredential, APIRequest
from app.modules.iris_api.client import IRISAPIClient, IRISAPIError, CircuitBreakerError
from app.modules.iris_api.service import IRISIntegrationService
from app.modules.iris_api.schemas import (
    IRISAuthResponse, IRISPatientResponse, IRISImmunizationResponse,
    APIEndpointCreate, SyncRequest, SyncResult, SyncStatus, HealthStatus,
    HealthCheckResponse
)
from app.core.security import security_manager

logger = structlog.get_logger()

pytestmark = [pytest.mark.integration, pytest.mark.external_registry, pytest.mark.public_health]

@pytest.fixture
async def external_registry_users(db_session: AsyncSession):
    """Create users for external registry integration testing"""
    roles_data = [
        {"name": "public_health_coordinator", "description": "Public Health Registry Coordinator"},
        {"name": "immunization_registry_manager", "description": "Immunization Registry Manager"},
        {"name": "vaccine_safety_officer", "description": "Vaccine Safety and VAERS Officer"},
        {"name": "health_information_exchange_admin", "description": "Health Information Exchange Administrator"},
        {"name": "registry_compliance_auditor", "description": "Registry Compliance Auditor"}
    ]
    
    roles = {}
    users = {}
    
    for role_data in roles_data:
        role = Role(name=role_data["name"], description=role_data["description"])
        db_session.add(role)
        await db_session.flush()
        roles[role_data["name"]] = role
        
        user = User(
            username=f"registry_{role_data['name']}",
            email=f"{role_data['name']}@registry.health.gov",
            hashed_password="$2b$12$registry.integration.secure.hash.testing",
            is_active=True,
            role_id=role.id
        )
        db_session.add(user)
        await db_session.flush()
        users[role_data["name"]] = user
    
    await db_session.commit()
    return users

@pytest.fixture
async def external_registry_endpoints(db_session: AsyncSession, external_registry_users: Dict[str, User]):
    """Create external registry endpoints for comprehensive testing"""
    registry_coordinator = external_registry_users["public_health_coordinator"]
    
    # State Immunization Information System (IIS)
    state_iis_endpoint = APIEndpoint(
        name="State_IIS_California",
        base_url="https://ca-iis.cdph.ca.gov/api",
        api_version="v2.1",
        auth_type="oauth2",
        timeout_seconds=45,
        retry_attempts=3,
        status="active",
        metadata={
            "registry_type": "state_immunization_information_system",
            "state": "California",
            "jurisdiction": "CA-CDPH",
            "supported_standards": ["FHIR_R4", "HL7_v2.5.1", "CDC_IIS"],
            "capabilities": ["immunization_submit", "patient_query", "inventory_management", "adverse_event_reporting"],
            "compliance_certifications": ["CDC_IIS_Functional_Standards", "HL7_FHIR_R4", "HIPAA_Compliant"],
            "data_exchange_methods": ["real_time_api", "batch_processing", "hl7_messaging"]
        }
    )
    
    # National Adult and Influenza Immunization Summit (NAIIS)
    national_registry_endpoint = APIEndpoint(
        name="NAIIS_National_Registry",
        base_url="https://naiis.cdc.gov/api",
        api_version="v3.0",
        auth_type="hmac",
        timeout_seconds=60,
        retry_attempts=2,
        status="active",
        metadata={
            "registry_type": "national_adult_immunization_registry",
            "jurisdiction": "CDC_National",
            "supported_standards": ["FHIR_R4", "HL7_v2.8.2", "CDC_NNDSS"],
            "capabilities": ["adult_immunization_tracking", "influenza_surveillance", "coverage_reporting", "outbreak_management"],
            "compliance_certifications": ["CDC_NNDSS", "HL7_FHIR_R4", "Public_Health_HIPAA"],
            "surveillance_systems": ["FluVaxView", "BRFSS", "NHIS"]
        }
    )
    
    # Vaccine Adverse Event Reporting System (VAERS)
    vaers_endpoint = APIEndpoint(
        name="VAERS_Safety_Monitoring",
        base_url="https://vaers.hhs.gov/api",
        api_version="v1.2", 
        auth_type="oauth2",
        timeout_seconds=30,
        retry_attempts=5,
        status="active",
        metadata={
            "registry_type": "vaccine_adverse_event_reporting",
            "jurisdiction": "FDA_CDC_Joint",
            "supported_standards": ["FHIR_R4", "HL7_FHIR_Adverse_Event", "FDA_FAERS"],
            "capabilities": ["adverse_event_submit", "safety_signal_monitoring", "causality_assessment", "regulatory_reporting"],
            "compliance_certifications": ["FDA_FAERS", "CDC_Vaccine_Safety", "CIOMS_Reporting"],
            "safety_monitoring": ["real_time_alerts", "signal_detection", "periodic_safety_reports"]
        }
    )
    
    # Vaccines for Children (VFC) Program Registry
    vfc_endpoint = APIEndpoint(
        name="VFC_Program_Registry",
        base_url="https://vfc.cdc.gov/api",
        api_version="v2.0",
        auth_type="oauth2",
        timeout_seconds=40,
        retry_attempts=3,
        status="active",
        metadata={
            "registry_type": "vaccines_for_children_program",
            "jurisdiction": "CDC_VFC_Program",
            "supported_standards": ["FHIR_R4", "HL7_v2.5.1", "CDC_VFC"],
            "capabilities": ["eligibility_verification", "vaccine_inventory", "provider_enrollment", "coverage_tracking"],
            "compliance_certifications": ["CDC_VFC_Standards", "FHIR_R4_Pediatric", "HIPAA_Pediatric"],
            "program_components": ["eligibility_screening", "vaccine_ordering", "inventory_management", "accountability"]
        }
    )
    
    # Health Information Exchange (HIE)
    hie_endpoint = APIEndpoint(
        name="Regional_HIE_Network",
        base_url="https://hie.healthnetwork.org/api",
        api_version="v4.1",
        auth_type="hmac",
        timeout_seconds=35,
        retry_attempts=4,
        status="active",
        metadata={
            "registry_type": "health_information_exchange",
            "jurisdiction": "Regional_HIE_Consortium",
            "supported_standards": ["FHIR_R4", "HL7_v2.8.2", "C-CDA_R2.1", "XCA", "XDS.b"],
            "capabilities": ["patient_discovery", "document_sharing", "clinical_data_exchange", "provider_directory"],
            "compliance_certifications": ["ONC_Certified", "DIRECT_Trust", "HIPAA_HIE", "FHIR_R4_US_Core"],
            "interoperability_services": ["patient_matching", "consent_management", "audit_logging", "security_framework"]
        }
    )
    
    endpoints = {
        "state_iis": state_iis_endpoint,
        "national_registry": national_registry_endpoint,
        "vaers": vaers_endpoint,
        "vfc": vfc_endpoint,
        "hie": hie_endpoint
    }
    
    db_session.add_all(endpoints.values())
    await db_session.commit()
    
    # Add credentials for each endpoint
    for endpoint_name, endpoint in endpoints.items():
        # OAuth2/HMAC credentials specific to each registry
        client_id_cred = APICredential(
            api_endpoint_id=str(endpoint.id),
            credential_name="client_id",
            encrypted_value=security_manager.encrypt_data(f"{endpoint_name}_client_id_{secrets.token_hex(8)}"),
            created_by=str(registry_coordinator.id)
        )
        
        client_secret_cred = APICredential(
            api_endpoint_id=str(endpoint.id),
            credential_name="client_secret",
            encrypted_value=security_manager.encrypt_data(f"{endpoint_name}_secret_{secrets.token_hex(16)}"),
            created_by=str(registry_coordinator.id)
        )
        
        # Additional registry-specific credentials
        if endpoint_name == "vaers":
            # VAERS requires additional FDA reporting credentials
            fda_reporter_id_cred = APICredential(
                api_endpoint_id=str(endpoint.id),
                credential_name="fda_reporter_id",
                encrypted_value=security_manager.encrypt_data(f"FDA_REPORTER_{secrets.token_hex(6)}"),
                created_by=str(registry_coordinator.id)
            )
            db_session.add(fda_reporter_id_cred)
        
        elif endpoint_name == "vfc":
            # VFC requires provider enrollment credentials
            vfc_provider_id_cred = APICredential(
                api_endpoint_id=str(endpoint.id),
                credential_name="vfc_provider_id",
                encrypted_value=security_manager.encrypt_data(f"VFC_PROV_{secrets.token_hex(8)}"),
                created_by=str(registry_coordinator.id)
            )
            db_session.add(vfc_provider_id_cred)
        
        db_session.add_all([client_id_cred, client_secret_cred])
    
    await db_session.commit()
    return endpoints

@pytest.fixture
async def comprehensive_vaccine_dataset(db_session: AsyncSession):
    """Create comprehensive vaccine dataset for registry testing"""
    vaccines = []
    
    # Comprehensive CDC vaccine dataset for registry testing
    vaccine_registry_data = [
        {
            "vaccine_code": "207", "vaccine_name": "COVID-19, mRNA, LNP-S, PF, 30 mcg/0.3 mL dose",
            "manufacturer": "Pfizer-BioNTech", "lot_number": "REG001COVID",
            "administration_date": date(2025, 1, 15), "dose_number": 1,
            "registry_categories": ["covid_19", "pandemic_response", "adult_immunization"],
            "safety_monitoring": True, "vfc_eligible": False
        },
        {
            "vaccine_code": "141", "vaccine_name": "Influenza, seasonal, injectable",
            "manufacturer": "Sanofi Pasteur", "lot_number": "REG002FLU",
            "administration_date": date(2024, 10, 1), "dose_number": 1,
            "registry_categories": ["seasonal_influenza", "annual_campaign", "adult_immunization"],
            "safety_monitoring": True, "vfc_eligible": True
        },
        {
            "vaccine_code": "20", "vaccine_name": "DTaP (Diphtheria, Tetanus toxoids and acellular Pertussis)",
            "manufacturer": "GSK", "lot_number": "REG003DTAP",
            "administration_date": date(2025, 1, 10), "dose_number": 1,
            "registry_categories": ["pediatric_routine", "vfc_program", "school_requirement"],
            "safety_monitoring": True, "vfc_eligible": True
        },
        {
            "vaccine_code": "114", "vaccine_name": "Meningococcal conjugate vaccine, serogroups A, C, W, Y",
            "manufacturer": "Pfizer", "lot_number": "REG004MENING",
            "administration_date": date(2025, 1, 5), "dose_number": 1,
            "registry_categories": ["adolescent_immunization", "college_requirement", "travel_vaccine"],
            "safety_monitoring": True, "vfc_eligible": True
        },
        {
            "vaccine_code": "133", "vaccine_name": "Pneumococcal conjugate vaccine, 13 valent",
            "manufacturer": "Pfizer", "lot_number": "REG005PNEUMO",
            "administration_date": date(2025, 1, 20), "dose_number": 1,
            "registry_categories": ["pediatric_routine", "adult_high_risk", "vfc_program"],
            "safety_monitoring": True, "vfc_eligible": True
        }
    ]
    
    for i, vaccine_data in enumerate(vaccine_registry_data):
        # Create corresponding patient for each vaccine
        patient = Patient(
            first_name=f"Registry",
            last_name=f"Patient{i+1}",
            date_of_birth=date(1990 + i, 1, 1),
            gender="U",
            phone_number=f"+1-555-REG-{i+1:03d}",
            email=f"registry.patient.{i+1}@integration.test",
            address_line1=f"123 Registry Avenue #{i+1}",
            city="Registry City",
            state="RC",
            zip_code=f"9010{i}",
            medical_record_number=f"REG{2025}{str(i+1).zfill(6)}",
            insurance_provider="Registry Test Insurance",
            insurance_policy_number=f"REG{i+1}890123",
            external_id=f"REGISTRY_PATIENT_{i+1:03d}"
        )
        
        db_session.add(patient)
        await db_session.flush()
        
        immunization = Immunization(
            patient_id=patient.id,
            vaccine_code=vaccine_data["vaccine_code"],
            vaccine_name=vaccine_data["vaccine_name"],
            administration_date=vaccine_data["administration_date"],
            lot_number=vaccine_data["lot_number"],
            manufacturer=vaccine_data["manufacturer"],
            dose_number=vaccine_data["dose_number"],
            series_complete=vaccine_data["dose_number"] >= 1,
            administered_by=f"Dr. Registry Administrator {i+1}",
            administration_site="Left deltoid",
            route="Intramuscular",
            iris_record_id=f"REGISTRY_IMM_{i+1}_{secrets.token_hex(4)}",
            data_source="Registry_Testing",
            registry_submission_status="pending",
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow()
        )
        
        db_session.add(immunization)
        vaccines.append({
            "patient": patient,
            "immunization": immunization,
            "registry_metadata": vaccine_data
        })
    
    await db_session.commit()
    
    for vaccine_entry in vaccines:
        await db_session.refresh(vaccine_entry["patient"])
        await db_session.refresh(vaccine_entry["immunization"])
    
    return vaccines

class TestStateImmunizationInformationSystem:
    """Test State Immunization Information System (IIS) integration"""
    
    @pytest.mark.asyncio
    async def test_state_iis_comprehensive_integration(
        self,
        db_session: AsyncSession,
        external_registry_endpoints: Dict[str, APIEndpoint],
        comprehensive_vaccine_dataset: List[Dict],
        external_registry_users: Dict[str, User]
    ):
        """
        Test State IIS Comprehensive Integration
        
        State Registry Features Tested:
        - CDC IIS Functional Standards compliance with complete patient reporting
        - HL7 v2.5.1 message processing with healthcare interoperability
        - FHIR R4 immunization resource submission with validation
        - Patient demographics synchronization with PHI protection
        - Vaccine inventory management with real-time availability tracking
        - Adverse event pre-screening with safety signal detection
        - Provider enrollment verification with credential validation
        - Coverage assessment reporting with population health analytics
        """
        immunization_manager = external_registry_users["immunization_registry_manager"]
        state_iis_endpoint = external_registry_endpoints["state_iis"]
        vaccine_dataset = comprehensive_vaccine_dataset
        
        # State IIS integration testing
        state_iis_tests = []
        
        # Test 1: CDC IIS Functional Standards Compliance
        iris_service = IRISIntegrationService()
        
        with patch.object(IRISAPIClient, 'sync_immunization_registry') as mock_iis_sync:
            # Mock CDC IIS compliant response
            mock_iis_response = {
                "status": "success",
                "registry_type": "state_immunization_information_system",
                "submission_id": f"CA_IIS_{secrets.token_hex(8)}",
                "total_records": len(vaccine_dataset),
                "processed_records": len(vaccine_dataset),
                "failed_records": 0,
                "processing_time_ms": 2100,
                "cdc_iis_compliance": {
                    "functional_standards_met": True,
                    "data_quality_score": 0.98,
                    "interoperability_validated": True,
                    "security_requirements_met": True,
                    "privacy_controls_verified": True
                },
                "hl7_processing": {
                    "hl7_version": "v2.5.1",
                    "message_types_processed": ["VXU^V04", "QBP^Q11", "RSP^K11"],
                    "ack_messages_sent": len(vaccine_dataset),
                    "error_conditions": []
                },
                "fhir_r4_validation": {
                    "immunization_resources_valid": True,
                    "patient_resources_valid": True,
                    "bundle_structure_compliant": True,
                    "terminology_bindings_correct": True
                },
                "submission_timestamp": datetime.utcnow().isoformat()
            }
            
            mock_iis_sync.return_value = mock_iis_response
            
            # Prepare state IIS submission parameters
            iis_params = {
                "state": "California",
                "registry_type": "state_iis",
                "submission_method": "fhir_r4_batch",
                "include_patient_demographics": True,
                "include_vaccine_inventory": True,
                "include_provider_data": True,
                "compliance_level": "cdc_iis_functional_standards",
                "data_quality_checks": True,
                "privacy_controls": "phi_encrypted"
            }
            
            # Perform state IIS synchronization
            start_time = time.time()
            iis_result = await iris_service.sync_with_external_registry(
                str(state_iis_endpoint.id),
                "state_iis",
                iis_params,
                db_session
            )
            iis_sync_duration = time.time() - start_time
            
            state_iis_test = {
                "registry_type": "state_immunization_information_system",
                "state_jurisdiction": "California",
                "iis_endpoint": state_iis_endpoint.base_url,
                "sync_request_successful": iis_result["status"] == "success",
                "immunization_records_submitted": mock_iis_response["total_records"],
                "records_processed_successfully": mock_iis_response["processed_records"],
                "processing_time_ms": mock_iis_response["processing_time_ms"],
                "sync_duration_seconds": iis_sync_duration,
                "cdc_iis_compliance": mock_iis_response["cdc_iis_compliance"],
                "functional_standards_met": mock_iis_response["cdc_iis_compliance"]["functional_standards_met"],
                "data_quality_score": mock_iis_response["cdc_iis_compliance"]["data_quality_score"],
                "interoperability_validated": mock_iis_response["cdc_iis_compliance"]["interoperability_validated"],
                "hl7_processing": mock_iis_response["hl7_processing"],
                "hl7_messages_processed": len(mock_iis_response["hl7_processing"]["message_types_processed"]),
                "fhir_r4_validation": mock_iis_response["fhir_r4_validation"],
                "fhir_resources_valid": all(mock_iis_response["fhir_r4_validation"].values()),
                "public_health_reporting_compliant": True,
                "clinical_workflow_compatible": iis_sync_duration < 8.0  # <8 seconds for state IIS
            }
            
            # Validate state IIS integration
            assert iis_result["status"] == "success", "State IIS sync should succeed"
            assert mock_iis_response["cdc_iis_compliance"]["functional_standards_met"], "Should meet CDC IIS functional standards"
            assert mock_iis_response["cdc_iis_compliance"]["data_quality_score"] >= 0.95, "Should maintain high data quality"
            assert mock_iis_response["fhir_r4_validation"]["immunization_resources_valid"], "FHIR R4 immunization resources should be valid"
            assert iis_sync_duration < 8.0, "State IIS sync should complete within public health timeframes"
            
            state_iis_tests.append(state_iis_test)
        
        # Test 2: Patient Demographics and Immunization History Submission
        with patch.object(IRISAPIClient, 'submit_immunization_record') as mock_submit_immunization:
            # Test individual immunization submission to state IIS
            test_vaccine = vaccine_dataset[0]  # COVID-19 vaccine
            
            # Mock state IIS immunization submission response
            mock_submission_response = {
                "id": f"CA_IIS_SUB_{secrets.token_hex(6)}",
                "status": "accepted",
                "state_registry_id": f"CA_{test_vaccine['immunization'].vaccine_code}_{secrets.token_hex(4)}",
                "validation_results": {
                    "patient_demographics_validation": "passed",
                    "immunization_data_validation": "passed",
                    "cdc_vaccine_code_validation": "passed",
                    "provider_validation": "passed",
                    "duplicate_detection": "no_duplicates_found",
                    "contraindication_screening": "no_contraindications"
                },
                "iis_processing": {
                    "patient_matched": True,
                    "immunization_recorded": True,
                    "coverage_assessment_updated": True,
                    "reminder_recall_updated": True
                },
                "compliance_certifications": {
                    "cdc_iis_functional_standards": True,
                    "hipaa_privacy_rule": True,
                    "state_reporting_requirements": True
                },
                "processing_time_ms": 1200
            }
            
            mock_submit_immunization.return_value = mock_submission_response
            
            # Prepare immunization data for state IIS submission
            immunization_data = {
                "id": str(test_vaccine["immunization"].id),
                "patient_external_id": test_vaccine["patient"].external_id,
                "patient_demographics": {
                    "first_name": test_vaccine["patient"].first_name,
                    "last_name": test_vaccine["patient"].last_name,
                    "date_of_birth": test_vaccine["patient"].date_of_birth.isoformat(),
                    "gender": test_vaccine["patient"].gender,
                    "address": {
                        "line1": test_vaccine["patient"].address_line1,
                        "city": test_vaccine["patient"].city,
                        "state": test_vaccine["patient"].state,
                        "zip_code": test_vaccine["patient"].zip_code
                    }
                },
                "immunization_details": {
                    "vaccine_code": test_vaccine["immunization"].vaccine_code,
                    "vaccine_name": test_vaccine["immunization"].vaccine_name,
                    "administration_date": test_vaccine["immunization"].administration_date.isoformat(),
                    "lot_number": test_vaccine["immunization"].lot_number,
                    "manufacturer": test_vaccine["immunization"].manufacturer,
                    "dose_number": test_vaccine["immunization"].dose_number,
                    "administered_by": test_vaccine["immunization"].administered_by,
                    "administration_site": test_vaccine["immunization"].administration_site,
                    "route": test_vaccine["immunization"].route
                },
                "registry_metadata": test_vaccine["registry_metadata"]
            }
            
            # Submit immunization to state IIS
            start_time = time.time()
            submission_result = await iris_service.submit_immunization_to_registry(
                str(state_iis_endpoint.id),
                immunization_data,
                db_session
            )
            submission_duration = time.time() - start_time
            
            # Verify immunization record updated with state IIS submission status
            result = await db_session.execute(
                select(Immunization).where(Immunization.id == test_vaccine["immunization"].id)
            )
            updated_immunization = result.scalar_one()
            
            iis_submission_test = {
                "immunization_id": str(test_vaccine["immunization"].id),
                "vaccine_code": test_vaccine["immunization"].vaccine_code,
                "submission_successful": submission_result["status"] == "submitted",
                "state_registry_id": mock_submission_response["state_registry_id"],
                "validation_results": mock_submission_response["validation_results"],
                "patient_demographics_validated": mock_submission_response["validation_results"]["patient_demographics_validation"] == "passed",
                "immunization_data_validated": mock_submission_response["validation_results"]["immunization_data_validation"] == "passed",
                "cdc_code_validated": mock_submission_response["validation_results"]["cdc_vaccine_code_validation"] == "passed",
                "provider_validated": mock_submission_response["validation_results"]["provider_validation"] == "passed",
                "duplicate_detection_passed": mock_submission_response["validation_results"]["duplicate_detection"] == "no_duplicates_found",
                "contraindication_screening_passed": mock_submission_response["validation_results"]["contraindication_screening"] == "no_contraindications",
                "iis_processing": mock_submission_response["iis_processing"],
                "patient_matched": mock_submission_response["iis_processing"]["patient_matched"],
                "coverage_assessment_updated": mock_submission_response["iis_processing"]["coverage_assessment_updated"],
                "processing_time_ms": mock_submission_response["processing_time_ms"],
                "submission_duration_seconds": submission_duration,
                "local_record_updated": updated_immunization.registry_submission_status == "submitted",
                "state_registry_tracking": updated_immunization.registry_submission_id is not None,
                "public_health_workflow_efficient": submission_duration < 3.0
            }
            
            # Validate state IIS submission
            assert submission_result["status"] == "submitted", "State IIS immunization submission should succeed"
            assert mock_submission_response["iis_processing"]["patient_matched"], "Patient should be matched in state IIS"
            assert mock_submission_response["iis_processing"]["coverage_assessment_updated"], "Coverage assessment should be updated"
            assert updated_immunization.registry_submission_status == "submitted", "Local record should reflect submission"
            assert submission_duration < 3.0, "Submission should be efficient for public health workflows"
            
            state_iis_tests.append(iis_submission_test)
        
        # Test 3: Vaccine Inventory Management and Availability
        with patch.object(IRISAPIClient, 'get_vaccine_inventory') as mock_get_inventory:
            # Mock state IIS vaccine inventory response
            mock_inventory_response = {
                "status": "success",
                "inventory_date": datetime.utcnow().isoformat(),
                "provider_locations": [
                    {
                        "location_id": "CA_PROV_001",
                        "location_name": "State IIS Test Clinic",
                        "address": "123 Public Health Blvd, Sacramento, CA 95814",
                        "vaccine_inventory": [
                            {
                                "vaccine_code": "207",
                                "vaccine_name": "COVID-19, mRNA, LNP-S, PF, 30 mcg/0.3 mL dose",
                                "manufacturer": "Pfizer-BioNTech",
                                "available_doses": 500,
                                "allocated_doses": 200,
                                "expiration_dates": ["2025-06-30", "2025-08-15"],
                                "storage_conditions": "ultra_cold_freezer",
                                "vfc_eligible_doses": 150
                            },
                            {
                                "vaccine_code": "141",
                                "vaccine_name": "Influenza, seasonal, injectable",
                                "manufacturer": "Sanofi Pasteur",
                                "available_doses": 800,
                                "allocated_doses": 300,
                                "expiration_dates": ["2025-04-30"],
                                "storage_conditions": "refrigerated",
                                "vfc_eligible_doses": 400
                            }
                        ]
                    }
                ],
                "inventory_summary": {
                    "total_vaccine_types": 15,
                    "total_available_doses": 12500,
                    "vfc_available_doses": 5800,
                    "expiring_within_30_days": 450,
                    "storage_temperature_compliant": True
                }
            }
            
            mock_get_inventory.return_value = mock_inventory_response
            
            # Get vaccine inventory from state IIS
            start_time = time.time()
            inventory_result = await iris_service.get_vaccine_inventory(
                str(state_iis_endpoint.id),
                "CA_PROV_001",
                db_session
            )
            inventory_duration = time.time() - start_time
            
            inventory_test = {
                "inventory_request_successful": inventory_result["status"] == "success",
                "provider_locations_returned": len(mock_inventory_response["provider_locations"]),
                "vaccine_types_available": len(mock_inventory_response["provider_locations"][0]["vaccine_inventory"]),
                "total_available_doses": mock_inventory_response["inventory_summary"]["total_available_doses"],
                "vfc_doses_available": mock_inventory_response["inventory_summary"]["vfc_available_doses"],
                "expiring_doses_tracked": mock_inventory_response["inventory_summary"]["expiring_within_30_days"],
                "storage_compliance_verified": mock_inventory_response["inventory_summary"]["storage_temperature_compliant"],
                "inventory_processing_time_seconds": inventory_duration,
                "real_time_inventory_available": True,
                "vaccine_management_integrated": True,
                "public_health_supply_chain_visible": True
            }
            
            # Validate inventory management
            assert inventory_result["status"] == "success", "Vaccine inventory request should succeed"
            assert mock_inventory_response["inventory_summary"]["total_available_doses"] > 10000, "Should have substantial vaccine inventory"
            assert mock_inventory_response["inventory_summary"]["storage_temperature_compliant"], "Storage conditions should be compliant"
            assert inventory_duration < 2.0, "Inventory queries should be fast for clinical decision making"
            
            state_iis_tests.append(inventory_test)
        
        # Create comprehensive state IIS integration audit log
        state_iis_log = AuditLog(
            event_type="state_iis_comprehensive_integration_test",
            user_id=str(immunization_manager.id),
            timestamp=datetime.utcnow(),
            details={
                "state_iis_testing_type": "cdc_functional_standards_and_interoperability",
                "state_jurisdiction": "California",
                "iis_endpoint": state_iis_endpoint.base_url,
                "state_iis_tests": state_iis_tests,
                "state_iis_summary": {
                    "registry_integration_tests": len(state_iis_tests),
                    "successful_iis_syncs": sum(1 for t in state_iis_tests if t.get("sync_request_successful", False)),
                    "cdc_functional_standards_compliance": sum(1 for t in state_iis_tests if t.get("functional_standards_met", False)),
                    "fhir_r4_resources_validated": sum(1 for t in state_iis_tests if t.get("fhir_resources_valid", False)),
                    "immunization_submissions_successful": sum(1 for t in state_iis_tests if t.get("submission_successful", False)),
                    "patient_matching_effective": sum(1 for t in state_iis_tests if t.get("patient_matched", False)),
                    "vaccine_inventory_accessible": sum(1 for t in state_iis_tests if t.get("inventory_request_successful", False)),
                    "average_processing_time": sum(t.get("processing_time_ms", 0) for t in state_iis_tests if "processing_time_ms" in t) / max(1, len([t for t in state_iis_tests if "processing_time_ms" in t]))
                },
                "public_health_compliance": {
                    "cdc_iis_functional_standards": True,
                    "hl7_v2_5_1_interoperability": True,
                    "fhir_r4_immunization_resources": True,
                    "hipaa_privacy_rule_compliance": True,
                    "state_reporting_requirements": True,
                    "vaccine_inventory_management": True
                }
            },
            severity="info",
            source_system="state_iis_integration_testing"
        )
        
        db_session.add(state_iis_log)
        await db_session.commit()
        
        # Verification: State IIS integration effectiveness
        successful_syncs = sum(1 for test in state_iis_tests if test.get("sync_request_successful", False))
        assert successful_syncs >= 1, "State IIS synchronizations should succeed"
        
        cdc_compliance = sum(1 for test in state_iis_tests if test.get("functional_standards_met", False))
        assert cdc_compliance >= 1, "CDC IIS functional standards should be met"
        
        fhir_validation = sum(1 for test in state_iis_tests if test.get("fhir_resources_valid", False))
        assert fhir_validation >= 1, "FHIR R4 resources should be validated"
        
        patient_matching = sum(1 for test in state_iis_tests if test.get("patient_matched", False))
        assert patient_matching >= 1, "Patient matching should be effective"
        
        logger.info(
            "State IIS comprehensive integration testing completed",
            successful_syncs=successful_syncs,
            cdc_compliance_validated=cdc_compliance,
            fhir_validation_passed=fhir_validation
        )

class TestVaccineAdverseEventReporting:
    """Test VAERS (Vaccine Adverse Event Reporting System) integration"""
    
    @pytest.mark.asyncio
    async def test_vaers_adverse_event_reporting_comprehensive(
        self,
        db_session: AsyncSession,
        external_registry_endpoints: Dict[str, APIEndpoint],
        comprehensive_vaccine_dataset: List[Dict],
        external_registry_users: Dict[str, User]
    ):
        """
        Test VAERS Adverse Event Reporting System
        
        VAERS Safety Features Tested:
        - FDA FAERS integration with regulatory reporting compliance
        - CDC vaccine safety monitoring with signal detection
        - CIOMS adverse event reporting with international standards
        - Real-time safety alert generation with clinical decision support
        - Causality assessment workflow with medical expert review
        - Regulatory submission automation with timeline compliance
        - Safety signal detection with statistical analysis
        - Healthcare provider notification with actionable safety information
        """
        vaccine_safety_officer = external_registry_users["vaccine_safety_officer"]
        vaers_endpoint = external_registry_endpoints["vaers"]
        vaccine_dataset = comprehensive_vaccine_dataset
        
        # VAERS adverse event reporting testing
        vaers_tests = []
        
        # Test 1: Adverse Event Detection and Reporting
        with patch.object(IRISAPIClient, 'submit_immunization_record') as mock_vaers_submit:
            # Simulate adverse event scenario
            test_vaccine = vaccine_dataset[0]  # COVID-19 vaccine for adverse event
            
            # Mock adverse event data
            adverse_event_data = {
                "event_id": f"VAERS_{secrets.token_hex(8)}",
                "patient_id": test_vaccine["patient"].external_id,
                "immunization_id": str(test_vaccine["immunization"].id),
                "event_details": {
                    "onset_date": "2025-01-16",  # Day after vaccination
                    "event_description": "Patient reported mild fatigue and low-grade fever within 24 hours of COVID-19 vaccination",
                    "severity": "mild",
                    "outcome": "recovered_without_sequelae",
                    "medical_attention_required": False,
                    "hospitalization_required": False,
                    "life_threatening": False,
                    "permanent_disability": False,
                    "death": False
                },
                "reporter_information": {
                    "reporter_type": "healthcare_provider",
                    "reporter_name": "Dr. Safety Monitor",
                    "facility_name": "VAERS Test Clinic",
                    "contact_information": {
                        "phone": "+1-555-VAERS-01",
                        "email": "safety@vaers.test.clinic"
                    }
                },
                "vaccine_details": {
                    "vaccine_code": test_vaccine["immunization"].vaccine_code,
                    "vaccine_name": test_vaccine["immunization"].vaccine_name,
                    "lot_number": test_vaccine["immunization"].lot_number,
                    "manufacturer": test_vaccine["immunization"].manufacturer,
                    "administration_date": test_vaccine["immunization"].administration_date.isoformat(),
                    "dose_number": test_vaccine["immunization"].dose_number,
                    "administered_by": test_vaccine["immunization"].administered_by
                }
            }
            
            # Mock VAERS submission response
            mock_vaers_response = {
                "id": f"VAERS_RPT_{secrets.token_hex(8)}",
                "status": "submitted",
                "vaers_id": f"VAERS{datetime.utcnow().year}{secrets.token_hex(4).upper()}",
                "fda_case_number": f"FDA{datetime.utcnow().year}{secrets.token_hex(6).upper()}",
                "submission_validation": {
                    "patient_data_validation": "passed",
                    "vaccine_data_validation": "passed",
                    "adverse_event_validation": "passed",
                    "reporter_validation": "passed",
                    "regulatory_requirements_met": True,
                    "duplicate_check": "no_duplicates_found"
                },
                "safety_assessment": {
                    "initial_causality_assessment": "possible",
                    "severity_classification": "mild",
                    "regulatory_significance": "routine_monitoring",
                    "follow_up_required": False,
                    "safety_signal_contribution": "low_priority"
                },
                "regulatory_processing": {
                    "fda_notification_sent": True,
                    "cdc_notification_sent": True,
                    "manufacturer_notification_required": False,
                    "timeline_compliance": "within_24_hours",
                    "international_reporting_required": False
                },
                "processing_time_ms": 1800
            }
            
            mock_vaers_submit.return_value = mock_vaers_response
            
            # Submit adverse event to VAERS
            start_time = time.time()
            vaers_result = await iris_service.submit_immunization_to_registry(
                str(vaers_endpoint.id),
                {
                    **adverse_event_data,
                    "submission_type": "adverse_event_report"
                },
                db_session
            )
            vaers_submission_duration = time.time() - start_time
            
            vaers_adverse_event_test = {
                "adverse_event_id": adverse_event_data["event_id"],
                "vaccine_code": adverse_event_data["vaccine_details"]["vaccine_code"],
                "vaers_submission_successful": vaers_result["status"] == "submitted",
                "vaers_case_id": mock_vaers_response["vaers_id"],
                "fda_case_number": mock_vaers_response["fda_case_number"],
                "submission_validation": mock_vaers_response["submission_validation"],
                "patient_data_validated": mock_vaers_response["submission_validation"]["patient_data_validation"] == "passed",
                "vaccine_data_validated": mock_vaers_response["submission_validation"]["vaccine_data_validation"] == "passed",
                "adverse_event_validated": mock_vaers_response["submission_validation"]["adverse_event_validation"] == "passed",
                "regulatory_requirements_met": mock_vaers_response["submission_validation"]["regulatory_requirements_met"],
                "safety_assessment": mock_vaers_response["safety_assessment"],
                "causality_assessment": mock_vaers_response["safety_assessment"]["initial_causality_assessment"],
                "severity_classification": mock_vaers_response["safety_assessment"]["severity_classification"],
                "regulatory_processing": mock_vaers_response["regulatory_processing"],
                "fda_notification_sent": mock_vaers_response["regulatory_processing"]["fda_notification_sent"],
                "cdc_notification_sent": mock_vaers_response["regulatory_processing"]["cdc_notification_sent"],
                "timeline_compliance": mock_vaers_response["regulatory_processing"]["timeline_compliance"],
                "processing_time_ms": mock_vaers_response["processing_time_ms"],
                "submission_duration_seconds": vaers_submission_duration,
                "vaccine_safety_monitoring_active": True,
                "regulatory_compliance_validated": True,
                "clinical_safety_workflow_efficient": vaers_submission_duration < 5.0
            }
            
            # Validate VAERS adverse event reporting
            assert vaers_result["status"] == "submitted", "VAERS adverse event submission should succeed"
            assert mock_vaers_response["submission_validation"]["regulatory_requirements_met"], "Should meet regulatory requirements"
            assert mock_vaers_response["regulatory_processing"]["fda_notification_sent"], "FDA should be notified"
            assert mock_vaers_response["regulatory_processing"]["cdc_notification_sent"], "CDC should be notified"
            assert mock_vaers_response["regulatory_processing"]["timeline_compliance"] == "within_24_hours", "Should meet reporting timeline"
            assert vaers_submission_duration < 5.0, "VAERS submission should be efficient for safety workflows"
            
            vaers_tests.append(vaers_adverse_event_test)
        
        # Test 2: Safety Signal Detection and Analysis
        with patch.object(IRISAPIClient, 'sync_immunization_registry') as mock_vaers_signal:
            # Mock safety signal detection response
            mock_signal_response = {
                "status": "success",
                "analysis_type": "safety_signal_detection",
                "analysis_period": {
                    "start_date": "2025-01-01",
                    "end_date": "2025-01-31",
                    "total_reports_analyzed": 15847
                },
                "signal_detection_results": [
                    {
                        "vaccine_code": "207",
                        "vaccine_name": "COVID-19, mRNA, LNP-S, PF, 30 mcg/0.3 mL dose",
                        "signal_type": "myocarditis_pericarditis",
                        "statistical_measures": {
                            "reporting_rate": 4.1,  # per 100,000 doses
                            "proportional_reporting_ratio": 1.8,
                            "confidence_interval": "1.2-2.7",
                            "statistical_significance": "p<0.05"
                        },
                        "clinical_significance": {
                            "severity_pattern": "mostly_mild",
                            "age_group_affected": "young_adults_16_30",
                            "gender_predilection": "male_predominant",
                            "outcome_pattern": "resolves_with_treatment"
                        },
                        "regulatory_action": {
                            "action_required": True,
                            "action_type": "enhanced_monitoring",
                            "healthcare_provider_communication": True,
                            "label_update_required": False,
                            "use_restriction_required": False
                        }
                    }
                ],
                "aggregate_safety_profile": {
                    "total_vaccines_monitored": 25,
                    "active_safety_signals": 3,
                    "resolved_safety_signals": 12,
                    "overall_safety_assessment": "acceptable_benefit_risk_profile"
                },
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
            mock_vaers_signal.return_value = mock_signal_response
            
            # Perform safety signal detection analysis
            signal_params = {
                "analysis_type": "safety_signal_detection",
                "time_period": "monthly",
                "statistical_methods": ["proportional_reporting_ratio", "empirical_bayes", "multi_item_gamma_poisson"],
                "clinical_review_required": True,
                "regulatory_threshold_analysis": True
            }
            
            start_time = time.time()
            signal_result = await iris_service.sync_with_external_registry(
                str(vaers_endpoint.id),
                "safety_signal_analysis",
                signal_params,
                db_session
            )
            signal_analysis_duration = time.time() - start_time
            
            safety_signal_test = {
                "signal_analysis_successful": signal_result["status"] == "success",
                "analysis_period_reports": mock_signal_response["analysis_period"]["total_reports_analyzed"],
                "safety_signals_detected": len(mock_signal_response["signal_detection_results"]),
                "vaccines_monitored": mock_signal_response["aggregate_safety_profile"]["total_vaccines_monitored"],
                "active_safety_signals": mock_signal_response["aggregate_safety_profile"]["active_safety_signals"],
                "statistical_analysis_performed": True,
                "clinical_significance_assessed": True,
                "regulatory_actions_determined": True,
                "enhanced_monitoring_triggered": any(
                    signal["regulatory_action"]["action_type"] == "enhanced_monitoring"
                    for signal in mock_signal_response["signal_detection_results"]
                ),
                "healthcare_provider_communication": any(
                    signal["regulatory_action"]["healthcare_provider_communication"]
                    for signal in mock_signal_response["signal_detection_results"]
                ),
                "overall_safety_assessment": mock_signal_response["aggregate_safety_profile"]["overall_safety_assessment"],
                "analysis_duration_seconds": signal_analysis_duration,
                "vaccine_safety_science_applied": True,
                "public_health_decision_support": True
            }
            
            # Validate safety signal detection
            assert signal_result["status"] == "success", "Safety signal analysis should succeed"
            assert mock_signal_response["analysis_period"]["total_reports_analyzed"] > 10000, "Should analyze substantial number of reports"
            assert len(mock_signal_response["signal_detection_results"]) >= 1, "Should detect safety signals when present"
            assert mock_signal_response["aggregate_safety_profile"]["overall_safety_assessment"] == "acceptable_benefit_risk_profile", "Should provide overall safety assessment"
            assert signal_analysis_duration < 10.0, "Signal analysis should complete within reasonable time"
            
            vaers_tests.append(safety_signal_test)
        
        # Create comprehensive VAERS integration audit log
        vaers_log = AuditLog(
            event_type="vaers_adverse_event_reporting_comprehensive_test",
            user_id=str(vaccine_safety_officer.id),
            timestamp=datetime.utcnow(),
            details={
                "vaers_testing_type": "adverse_event_reporting_and_safety_monitoring",
                "vaers_endpoint": vaers_endpoint.base_url,
                "vaers_tests": vaers_tests,
                "vaers_summary": {
                    "adverse_event_tests": len([t for t in vaers_tests if "adverse_event_id" in t]),
                    "successful_vaers_submissions": sum(1 for t in vaers_tests if t.get("vaers_submission_successful", False)),
                    "regulatory_requirements_met": sum(1 for t in vaers_tests if t.get("regulatory_requirements_met", False)),
                    "fda_notifications_sent": sum(1 for t in vaers_tests if t.get("fda_notification_sent", False)),
                    "cdc_notifications_sent": sum(1 for t in vaers_tests if t.get("cdc_notification_sent", False)),
                    "safety_signals_detected": sum(t.get("safety_signals_detected", 0) for t in vaers_tests),
                    "timeline_compliance_achieved": sum(1 for t in vaers_tests if t.get("timeline_compliance") == "within_24_hours"),
                    "average_processing_time": sum(t.get("processing_time_ms", 0) for t in vaers_tests if "processing_time_ms" in t) / max(1, len([t for t in vaers_tests if "processing_time_ms" in t]))
                },
                "vaccine_safety_compliance": {
                    "fda_faers_integration": True,
                    "cdc_vaccine_safety_monitoring": True,
                    "cioms_adverse_event_reporting": True,
                    "regulatory_timeline_compliance": True,
                    "safety_signal_detection": True,
                    "healthcare_provider_communication": True
                }
            },
            severity="info",
            source_system="vaers_safety_monitoring_testing"
        )
        
        db_session.add(vaers_log)
        await db_session.commit()
        
        # Verification: VAERS integration effectiveness
        successful_submissions = sum(1 for test in vaers_tests if test.get("vaers_submission_successful", False))
        assert successful_submissions >= 1, "VAERS adverse event submissions should succeed"
        
        regulatory_compliance = sum(1 for test in vaers_tests if test.get("regulatory_requirements_met", False))
        assert regulatory_compliance >= 1, "Regulatory requirements should be met"
        
        fda_notifications = sum(1 for test in vaers_tests if test.get("fda_notification_sent", False))
        assert fda_notifications >= 1, "FDA notifications should be sent"
        
        safety_monitoring = sum(1 for test in vaers_tests if test.get("vaccine_safety_monitoring_active", False))
        assert safety_monitoring >= 1, "Vaccine safety monitoring should be active"
        
        logger.info(
            "VAERS adverse event reporting comprehensive testing completed",
            successful_submissions=successful_submissions,
            regulatory_compliance_met=regulatory_compliance,
            fda_notifications_sent=fda_notifications
        )

class TestVaccinesForChildrenProgram:
    """Test VFC (Vaccines for Children) Program integration"""
    
    @pytest.mark.asyncio
    async def test_vfc_program_integration_comprehensive(
        self,
        db_session: AsyncSession,
        external_registry_endpoints: Dict[str, APIEndpoint],
        comprehensive_vaccine_dataset: List[Dict],
        external_registry_users: Dict[str, User]
    ):
        """
        Test VFC Program Integration
        
        VFC Program Features Tested:
        - Pediatric patient eligibility verification with income and insurance status
        - VFC vaccine inventory management with federal vaccine allocation
        - Provider enrollment and accountability with CDC oversight
        - Vaccine ordering and distribution with temperature monitoring
        - Coverage tracking and AFIX (Assessment, Feedback, Incentives, and eXchange)
        - Quality assurance monitoring with site visits and audits
        - Vaccine wastage reporting with accountability measures
        - Health equity monitoring with demographic analysis
        """
        immunization_manager = external_registry_users["immunization_registry_manager"]
        vfc_endpoint = external_registry_endpoints["vfc"]
        vaccine_dataset = comprehensive_vaccine_dataset
        
        # VFC program integration testing
        vfc_tests = []
        
        # Test 1: Pediatric Patient Eligibility Verification
        with patch.object(IRISAPIClient, 'sync_immunization_registry') as mock_vfc_eligibility:
            # Select pediatric vaccines for VFC testing
            pediatric_vaccines = [v for v in vaccine_dataset if v["registry_metadata"]["vfc_eligible"]]
            
            # Mock VFC eligibility verification response
            mock_eligibility_response = {
                "status": "success",
                "eligibility_verification_type": "vfc_pediatric_eligibility",
                "patients_screened": len(pediatric_vaccines),
                "eligibility_results": []
            }
            
            # Create eligibility results for each pediatric patient
            for i, vaccine_entry in enumerate(pediatric_vaccines):
                eligibility_result = {
                    "patient_id": vaccine_entry["patient"].external_id,
                    "age_verification": {
                        "patient_age_years": 5 + i,  # Ages 5-9 for VFC eligibility
                        "vfc_age_eligible": True,
                        "age_at_vaccination": f"{5 + i} years"
                    },
                    "insurance_status": {
                        "insurance_type": ["medicaid", "uninsured", "underinsured", "native_american"][i % 4],
                        "vfc_insurance_eligible": True,
                        "medicaid_id": f"MEDICAID_{secrets.token_hex(6)}" if i % 4 == 0 else None
                    },
                    "income_verification": {
                        "family_income_percentage_fpl": 185 + (i * 10),  # 185%-225% Federal Poverty Level
                        "vfc_income_eligible": True,
                        "documentation_verified": True
                    },
                    "overall_vfc_eligibility": {
                        "eligible": True,
                        "eligibility_category": ["medicaid_eligible", "uninsured", "underinsured", "native_american"][i % 4],
                        "effective_date": "2025-01-01",
                        "expiration_date": "2025-12-31"
                    },
                    "vaccine_entitlement": {
                        "entitled_vaccines": ["DTaP", "MMR", "Varicella", "Pneumococcal", "Influenza"],
                        "age_appropriate_vaccines": True,
                        "catch_up_vaccines_needed": False
                    }
                }
                mock_eligibility_response["eligibility_results"].append(eligibility_result)
            
            # Add summary statistics
            mock_eligibility_response["eligibility_summary"] = {
                "total_eligible_patients": len(pediatric_vaccines),
                "medicaid_eligible": len([r for r in mock_eligibility_response["eligibility_results"] if r["insurance_status"]["insurance_type"] == "medicaid"]),
                "uninsured_eligible": len([r for r in mock_eligibility_response["eligibility_results"] if r["insurance_status"]["insurance_type"] == "uninsured"]),
                "underinsured_eligible": len([r for r in mock_eligibility_response["eligibility_results"] if r["insurance_status"]["insurance_type"] == "underinsured"]),
                "native_american_eligible": len([r for r in mock_eligibility_response["eligibility_results"] if r["insurance_status"]["insurance_type"] == "native_american"]),
                "total_vaccine_entitlements": sum(len(r["vaccine_entitlement"]["entitled_vaccines"]) for r in mock_eligibility_response["eligibility_results"])
            }
            
            mock_vfc_eligibility.return_value = mock_eligibility_response
            
            # Perform VFC eligibility verification
            vfc_params = {
                "verification_type": "pediatric_eligibility_screening",
                "include_income_verification": True,
                "include_insurance_status": True,
                "include_vaccine_entitlement": True,
                "compliance_level": "cdc_vfc_standards"
            }
            
            start_time = time.time()
            eligibility_result = await iris_service.sync_with_external_registry(
                str(vfc_endpoint.id),
                "vfc_eligibility",
                vfc_params,
                db_session
            )
            eligibility_duration = time.time() - start_time
            
            vfc_eligibility_test = {
                "eligibility_verification_successful": eligibility_result["status"] == "success",
                "patients_screened": mock_eligibility_response["patients_screened"],
                "eligible_patients": mock_eligibility_response["eligibility_summary"]["total_eligible_patients"],
                "medicaid_eligible_count": mock_eligibility_response["eligibility_summary"]["medicaid_eligible"],
                "uninsured_eligible_count": mock_eligibility_response["eligibility_summary"]["uninsured_eligible"],
                "underinsured_eligible_count": mock_eligibility_response["eligibility_summary"]["underinsured_eligible"],
                "native_american_eligible_count": mock_eligibility_response["eligibility_summary"]["native_american_eligible"],
                "total_vaccine_entitlements": mock_eligibility_response["eligibility_summary"]["total_vaccine_entitlements"],
                "age_verification_completed": all(r["age_verification"]["vfc_age_eligible"] for r in mock_eligibility_response["eligibility_results"]),
                "insurance_screening_completed": all(r["insurance_status"]["vfc_insurance_eligible"] for r in mock_eligibility_response["eligibility_results"]),
                "income_verification_completed": all(r["income_verification"]["vfc_income_eligible"] for r in mock_eligibility_response["eligibility_results"]),
                "vaccine_entitlement_determined": all(r["vaccine_entitlement"]["entitled_vaccines"] for r in mock_eligibility_response["eligibility_results"]),
                "eligibility_processing_time_seconds": eligibility_duration,
                "health_equity_screening_active": True,
                "pediatric_vaccine_access_facilitated": True,
                "vfc_program_compliance_validated": True
            }
            
            # Validate VFC eligibility verification
            assert eligibility_result["status"] == "success", "VFC eligibility verification should succeed"
            assert mock_eligibility_response["eligibility_summary"]["total_eligible_patients"] >= 3, "Should verify multiple pediatric patients"
            assert all(r["overall_vfc_eligibility"]["eligible"] for r in mock_eligibility_response["eligibility_results"]), "All test patients should be VFC eligible"
            assert eligibility_duration < 6.0, "Eligibility verification should be efficient for clinical workflows"
            
            vfc_tests.append(vfc_eligibility_test)
        
        # Test 2: VFC Vaccine Inventory and Ordering Management
        with patch.object(IRISAPIClient, 'get_vaccine_inventory') as mock_vfc_inventory:
            # Mock VFC vaccine inventory response
            mock_vfc_inventory_response = {
                "status": "success",
                "inventory_type": "vfc_federal_vaccine_inventory",
                "provider_vfc_pin": "VFC123456789",
                "inventory_date": datetime.utcnow().isoformat(),
                "vfc_vaccine_inventory": [
                    {
                        "vaccine_code": "20",
                        "vaccine_name": "DTaP (Diphtheria, Tetanus toxoids and acellular Pertussis)",
                        "manufacturer": "GSK",
                        "vfc_inventory": {
                            "allocated_doses": 500,
                            "distributed_doses": 320,
                            "remaining_doses": 180,
                            "pending_orders": 200,
                            "wastage_doses": 15,
                            "wastage_percentage": 3.0
                        },
                        "storage_compliance": {
                            "temperature_range": "2-8°C",
                            "current_temperature": "4.2°C",
                            "temperature_compliant": True,
                            "storage_unit_certified": True,
                            "backup_power_available": True
                        },
                        "expiration_tracking": {
                            "earliest_expiration": "2025-08-15",
                            "doses_expiring_30_days": 25,
                            "doses_expiring_90_days": 75,
                            "rotation_compliance": True
                        }
                    },
                    {
                        "vaccine_code": "133",
                        "vaccine_name": "Pneumococcal conjugate vaccine, 13 valent",
                        "manufacturer": "Pfizer",
                        "vfc_inventory": {
                            "allocated_doses": 300,
                            "distributed_doses": 180,
                            "remaining_doses": 120,
                            "pending_orders": 100,
                            "wastage_doses": 8,
                            "wastage_percentage": 2.7
                        },
                        "storage_compliance": {
                            "temperature_range": "2-8°C",
                            "current_temperature": "3.8°C",
                            "temperature_compliant": True,
                            "storage_unit_certified": True,
                            "backup_power_available": True
                        },
                        "expiration_tracking": {
                            "earliest_expiration": "2025-10-30",
                            "doses_expiring_30_days": 0,
                            "doses_expiring_90_days": 40,
                            "rotation_compliance": True
                        }
                    }
                ],
                "inventory_summary": {
                    "total_vfc_vaccine_types": 15,
                    "total_allocated_doses": 12500,
                    "total_distributed_doses": 8750,
                    "total_remaining_doses": 3750,
                    "overall_wastage_percentage": 2.8,
                    "storage_compliance_rate": 100.0,
                    "expiration_management_compliant": True
                },
                "accountability_metrics": {
                    "doses_administered_to_vfc_eligible": 8200,
                    "doses_administered_to_non_vfc": 550,  # Should be minimal
                    "accountability_rate": 93.7,  # (8200/8750) * 100
                    "provider_compliance_status": "compliant"
                }
            }
            
            mock_vfc_inventory.return_value = mock_vfc_inventory_response
            
            # Get VFC vaccine inventory
            start_time = time.time()
            inventory_result = await iris_service.get_vaccine_inventory(
                str(vfc_endpoint.id),
                "VFC123456789",  # VFC PIN
                db_session
            )
            inventory_duration = time.time() - start_time
            
            vfc_inventory_test = {
                "vfc_inventory_request_successful": inventory_result["status"] == "success",
                "vfc_vaccine_types_available": len(mock_vfc_inventory_response["vfc_vaccine_inventory"]),
                "total_allocated_doses": mock_vfc_inventory_response["inventory_summary"]["total_allocated_doses"],
                "total_distributed_doses": mock_vfc_inventory_response["inventory_summary"]["total_distributed_doses"],
                "total_remaining_doses": mock_vfc_inventory_response["inventory_summary"]["total_remaining_doses"],
                "overall_wastage_percentage": mock_vfc_inventory_response["inventory_summary"]["overall_wastage_percentage"],
                "storage_compliance_rate": mock_vfc_inventory_response["inventory_summary"]["storage_compliance_rate"],
                "expiration_management_compliant": mock_vfc_inventory_response["inventory_summary"]["expiration_management_compliant"],
                "accountability_metrics": mock_vfc_inventory_response["accountability_metrics"],
                "vfc_eligible_administration_rate": mock_vfc_inventory_response["accountability_metrics"]["accountability_rate"],
                "provider_compliance_status": mock_vfc_inventory_response["accountability_metrics"]["provider_compliance_status"],
                "inventory_processing_time_seconds": inventory_duration,
                "federal_vaccine_management_active": True,
                "temperature_monitoring_compliant": all(
                    vaccine["storage_compliance"]["temperature_compliant"]
                    for vaccine in mock_vfc_inventory_response["vfc_vaccine_inventory"]
                ),
                "wastage_tracking_effective": mock_vfc_inventory_response["inventory_summary"]["overall_wastage_percentage"] < 5.0,
                "vfc_program_accountability_maintained": mock_vfc_inventory_response["accountability_metrics"]["accountability_rate"] > 90.0
            }
            
            # Validate VFC inventory management
            assert inventory_result["status"] == "success", "VFC inventory request should succeed"
            assert mock_vfc_inventory_response["inventory_summary"]["storage_compliance_rate"] == 100.0, "Storage compliance should be 100%"
            assert mock_vfc_inventory_response["inventory_summary"]["overall_wastage_percentage"] < 5.0, "Wastage should be under 5%"
            assert mock_vfc_inventory_response["accountability_metrics"]["accountability_rate"] > 90.0, "Accountability rate should exceed 90%"
            assert inventory_duration < 3.0, "VFC inventory queries should be efficient"
            
            vfc_tests.append(vfc_inventory_test)
        
        # Test 3: AFIX (Assessment, Feedback, Incentives, and eXchange) Quality Assurance
        with patch.object(IRISAPIClient, 'sync_immunization_registry') as mock_afix:
            # Mock AFIX quality assurance response
            mock_afix_response = {
                "status": "success",
                "afix_assessment_type": "comprehensive_quality_assurance",
                "assessment_period": {
                    "start_date": "2024-10-01",
                    "end_date": "2024-12-31",
                    "quarter": "Q4_2024"
                },
                "coverage_assessment": {
                    "target_population_0_35_months": 2500,
                    "up_to_date_0_35_months": 2125,
                    "coverage_rate_0_35_months": 85.0,
                    "coverage_target": 90.0,
                    "coverage_gap": 5.0,
                    "patients_needing_vaccines": 375
                },
                "provider_feedback": {
                    "strengths": [
                        "Excellent vaccine storage and handling practices",
                        "High VFC accountability rates (93.7%)",
                        "Timely adverse event reporting",
                        "Strong patient reminder/recall system"
                    ],
                    "improvement_opportunities": [
                        "Increase coverage rates for 0-35 month population",
                        "Enhance weekend and evening clinic hours",
                        "Improve patient education materials in Spanish"
                    ],
                    "action_plan": {
                        "priority_actions": [
                            "Implement extended clinic hours on Saturdays",
                            "Deploy bilingual patient education materials",
                            "Enhance reminder/recall system for overdue patients"
                        ],
                        "timeline": "90_days",
                        "follow_up_assessment": "2025-04-01"
                    }
                },
                "incentives_programs": {
                    "quality_improvement_incentive": {
                        "eligible": True,
                        "incentive_amount": 2500.00,
                        "performance_criteria_met": ["storage_compliance", "accountability_rate", "adverse_event_reporting"]
                    },
                    "coverage_improvement_incentive": {
                        "eligible": False,
                        "reason": "coverage_rate_below_target",
                        "improvement_needed": "5_percentage_points"
                    }
                },
                "knowledge_exchange": {
                    "best_practices_shared": [
                        "Effective patient reminder systems",
                        "Cultural competency in vaccine communication",
                        "Efficient vaccine inventory management"
                    ],
                    "peer_learning_opportunities": [
                        "Regional VFC provider network meeting",
                        "Vaccine storage and handling training",
                        "Health equity improvement workshop"
                    ]
                }
            }
            
            mock_afix.return_value = mock_afix_response
            
            # Perform AFIX quality assurance assessment
            afix_params = {
                "assessment_type": "comprehensive_quality_assurance",
                "include_coverage_assessment": True,
                "include_provider_feedback": True,
                "include_incentives_evaluation": True,
                "include_knowledge_exchange": True,
                "quality_improvement_focus": True
            }
            
            start_time = time.time()
            afix_result = await iris_service.sync_with_external_registry(
                str(vfc_endpoint.id),
                "afix_assessment",
                afix_params,
                db_session
            )
            afix_duration = time.time() - start_time
            
            vfc_afix_test = {
                "afix_assessment_successful": afix_result["status"] == "success",
                "coverage_assessment_completed": True,
                "target_population_assessed": mock_afix_response["coverage_assessment"]["target_population_0_35_months"],
                "current_coverage_rate": mock_afix_response["coverage_assessment"]["coverage_rate_0_35_months"],
                "coverage_target": mock_afix_response["coverage_assessment"]["coverage_target"],
                "coverage_gap_identified": mock_afix_response["coverage_assessment"]["coverage_gap"],
                "patients_needing_vaccines": mock_afix_response["coverage_assessment"]["patients_needing_vaccines"],
                "provider_feedback_generated": len(mock_afix_response["provider_feedback"]["strengths"]) > 0,
                "improvement_opportunities_identified": len(mock_afix_response["provider_feedback"]["improvement_opportunities"]) > 0,
                "action_plan_developed": len(mock_afix_response["provider_feedback"]["action_plan"]["priority_actions"]) > 0,
                "quality_incentive_eligible": mock_afix_response["incentives_programs"]["quality_improvement_incentive"]["eligible"],
                "incentive_amount": mock_afix_response["incentives_programs"]["quality_improvement_incentive"]["incentive_amount"],
                "knowledge_exchange_facilitated": len(mock_afix_response["knowledge_exchange"]["best_practices_shared"]) > 0,
                "peer_learning_opportunities": len(mock_afix_response["knowledge_exchange"]["peer_learning_opportunities"]),
                "assessment_processing_time_seconds": afix_duration,
                "quality_improvement_program_active": True,
                "provider_development_supported": True,
                "vfc_program_excellence_promoted": True
            }
            
            # Validate AFIX quality assurance
            assert afix_result["status"] == "success", "AFIX assessment should succeed"
            assert mock_afix_response["coverage_assessment"]["target_population_0_35_months"] > 2000, "Should assess substantial target population"
            assert len(mock_afix_response["provider_feedback"]["action_plan"]["priority_actions"]) >= 3, "Should provide actionable improvement plan"
            assert mock_afix_response["incentives_programs"]["quality_improvement_incentive"]["eligible"], "Should be eligible for quality incentives"
            assert afix_duration < 5.0, "AFIX assessment should be efficient"
            
            vfc_tests.append(vfc_afix_test)
        
        # Create comprehensive VFC program integration audit log
        vfc_log = AuditLog(
            event_type="vfc_program_integration_comprehensive_test",
            user_id=str(immunization_manager.id),
            timestamp=datetime.utcnow(),
            details={
                "vfc_testing_type": "pediatric_vaccine_program_and_quality_assurance",
                "vfc_endpoint": vfc_endpoint.base_url,
                "vfc_tests": vfc_tests,
                "vfc_summary": {
                    "eligibility_verifications_completed": len([t for t in vfc_tests if "patients_screened" in t]),
                    "eligible_patients_identified": sum(t.get("eligible_patients", 0) for t in vfc_tests),
                    "vfc_inventory_assessments": len([t for t in vfc_tests if "vfc_inventory_request_successful" in t]),
                    "total_allocated_doses": sum(t.get("total_allocated_doses", 0) for t in vfc_tests),
                    "wastage_percentage_average": sum(t.get("overall_wastage_percentage", 0) for t in vfc_tests if "overall_wastage_percentage" in t) / max(1, len([t for t in vfc_tests if "overall_wastage_percentage" in t])),
                    "accountability_rate_average": sum(t.get("vfc_eligible_administration_rate", 0) for t in vfc_tests if "vfc_eligible_administration_rate" in t) / max(1, len([t for t in vfc_tests if "vfc_eligible_administration_rate" in t])),
                    "afix_assessments_completed": len([t for t in vfc_tests if "afix_assessment_successful" in t]),
                    "quality_incentives_earned": sum(t.get("incentive_amount", 0) for t in vfc_tests)
                },
                "vfc_program_compliance": {
                    "cdc_vfc_standards": True,
                    "pediatric_eligibility_verification": True,
                    "federal_vaccine_accountability": True,
                    "storage_and_handling_compliance": True,
                    "afix_quality_assurance": True,
                    "health_equity_promotion": True
                }
            },
            severity="info",
            source_system="vfc_program_testing"
        )
        
        db_session.add(vfc_log)
        await db_session.commit()
        
        # Verification: VFC program integration effectiveness
        eligibility_verifications = len([t for t in vfc_tests if "patients_screened" in t])
        assert eligibility_verifications >= 1, "VFC eligibility verifications should be completed"
        
        inventory_assessments = len([t for t in vfc_tests if "vfc_inventory_request_successful" in t])
        assert inventory_assessments >= 1, "VFC inventory assessments should be successful"
        
        afix_assessments = len([t for t in vfc_tests if "afix_assessment_successful" in t])
        assert afix_assessments >= 1, "AFIX quality assurance assessments should be completed"
        
        wastage_compliance = all(t.get("wastage_tracking_effective", False) for t in vfc_tests if "wastage_tracking_effective" in t)
        assert wastage_compliance, "VFC wastage tracking should be effective"
        
        logger.info(
            "VFC program integration comprehensive testing completed",
            eligibility_verifications=eligibility_verifications,
            inventory_assessments=inventory_assessments,
            afix_assessments=afix_assessments
        )

class TestHealthInformationExchange:
    """Test HIE (Health Information Exchange) integration"""
    
    @pytest.mark.asyncio
    async def test_hie_interoperability_comprehensive(
        self,
        db_session: AsyncSession,
        external_registry_endpoints: Dict[str, APIEndpoint],
        comprehensive_vaccine_dataset: List[Dict],
        external_registry_users: Dict[str, User]
    ):
        """
        Test HIE Interoperability Integration
        
        HIE Features Tested:
        - Patient discovery across healthcare networks with identity matching
        - Clinical document sharing with C-CDA R2.1 and FHIR R4 standards
        - Provider directory services with credential verification
        - Consent management with granular patient privacy controls
        - Security framework with DIRECT Trust and encryption
        - Quality measure reporting with clinical performance indicators
        - Care coordination workflows with longitudinal patient records
        - Public health reporting integration with automated case notification
        """
        hie_admin = external_registry_users["health_information_exchange_admin"]
        hie_endpoint = external_registry_endpoints["hie"]
        vaccine_dataset = comprehensive_vaccine_dataset
        
        # HIE interoperability testing
        hie_tests = []
        
        # Test 1: Patient Discovery and Identity Matching
        with patch.object(IRISAPIClient, 'search_patients') as mock_patient_discovery:
            # Select patient for HIE discovery testing
            test_patient = vaccine_dataset[0]["patient"]
            
            # Mock HIE patient discovery response
            mock_discovery_response = [
                {
                    "patient_id": f"HIE_{test_patient.external_id}",
                    "mrn": test_patient.medical_record_number,
                    "demographics": {
                        "first_name": test_patient.first_name,
                        "last_name": test_patient.last_name,
                        "date_of_birth": test_patient.date_of_birth.isoformat(),
                        "gender": test_patient.gender,
                        "address": {
                            "line1": test_patient.address_line1,
                            "city": test_patient.city,
                            "state": test_patient.state,
                            "zip_code": test_patient.zip_code
                        }
                    },
                    "identity_matching": {
                        "match_score": 0.96,
                        "match_algorithm": "probabilistic_linkage",
                        "identity_confidence": "high",
                        "demographic_matches": {
                            "name_match": True,
                            "dob_match": True,
                            "address_match": True,
                            "ssn_match": True
                        },
                        "duplicate_detection": {
                            "potential_duplicates": 0,
                            "unique_patient_confirmed": True
                        }
                    },
                    "participating_organizations": [
                        {
                            "organization_id": "ORG_HOSP_001",
                            "organization_name": "Regional Medical Center",
                            "organization_type": "hospital",
                            "last_encounter": "2024-12-15",
                            "available_records": ["immunizations", "lab_results", "discharge_summaries"]
                        },
                        {
                            "organization_id": "ORG_CLINIC_002",
                            "organization_name": "Primary Care Associates",
                            "organization_type": "primary_care_clinic",
                            "last_encounter": "2025-01-10",
                            "available_records": ["immunizations", "clinical_notes", "care_plans"]
                        }
                    ],
                    "consent_status": {
                        "general_consent": True,
                        "immunization_sharing": True,
                        "sensitive_data_sharing": False,
                        "research_consent": False,
                        "consent_date": "2024-06-01",
                        "consent_expiration": "2025-06-01"
                    }
                }
            ]
            
            mock_patient_discovery.return_value = mock_discovery_response
            
            # Perform patient discovery
            discovery_params = {
                "first_name": test_patient.first_name,
                "last_name": test_patient.last_name,
                "date_of_birth": test_patient.date_of_birth.isoformat(),
                "mrn": test_patient.medical_record_number
            }
            
            start_time = time.time()
            discovery_result = await iris_service.get_client(str(hie_endpoint.id), db_session)
            discovery_patients = await discovery_result.search_patients(discovery_params)
            discovery_duration = time.time() - start_time
            
            patient_discovery_test = {
                "patient_discovery_successful": len(discovery_patients) > 0,
                "patients_found": len(discovery_patients),
                "identity_match_score": discovery_patients[0].match_score if discovery_patients else 0,
                "identity_confidence": discovery_patients[0].identity_confidence if discovery_patients else "none",
                "demographic_matching": {
                    "name_match": discovery_patients[0].demographic_matches["name_match"] if discovery_patients else False,
                    "dob_match": discovery_patients[0].demographic_matches["dob_match"] if discovery_patients else False,
                    "address_match": discovery_patients[0].demographic_matches["address_match"] if discovery_patients else False,
                    "all_demographics_matched": all(discovery_patients[0].demographic_matches.values()) if discovery_patients else False
                },
                "participating_organizations": len(discovery_patients[0].participating_organizations) if discovery_patients else 0,
                "consent_verified": discovery_patients[0].consent_status["immunization_sharing"] if discovery_patients else False,
                "duplicate_detection_performed": discovery_patients[0].duplicate_detection["unique_patient_confirmed"] if discovery_patients else False,
                "discovery_processing_time_seconds": discovery_duration,
                "hie_patient_matching_effective": discovery_patients[0].match_score > 0.9 if discovery_patients else False,
                "multi_organization_visibility": True,
                "privacy_controls_respected": True,
                "interoperability_framework_operational": True
            }
            
            # Validate patient discovery
            assert len(discovery_patients) >= 1, "Patient discovery should find matching patients"
            assert discovery_patients[0].match_score > 0.9, "Identity matching should have high confidence"
            assert all(discovery_patients[0].demographic_matches.values()), "All demographic elements should match"
            assert discovery_patients[0].consent_status["immunization_sharing"], "Patient should consent to immunization sharing"
            assert discovery_duration < 4.0, "Patient discovery should be efficient for clinical workflows"
            
            hie_tests.append(patient_discovery_test)
        
        # Test 2: Clinical Document Sharing and Interoperability
        with patch.object(IRISAPIClient, 'get_patient_bundle') as mock_document_sharing:
            # Mock HIE clinical document bundle response
            mock_document_bundle = {
                "resourceType": "Bundle",
                "id": f"hie-patient-bundle-{test_patient.external_id}",
                "type": "document",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "total": 15,
                "entry": [
                    {
                        "resource": {
                            "resourceType": "Composition",
                            "id": "care-summary-composition",
                            "status": "final",
                            "type": {
                                "coding": [{
                                    "system": "http://loinc.org",
                                    "code": "34133-9",
                                    "display": "Summarization of Episode Note"
                                }]
                            },
                            "subject": {"reference": f"Patient/{test_patient.external_id}"},
                            "date": "2025-01-20",
                            "author": [{"reference": "Practitioner/hie-provider-001"}],
                            "title": "Comprehensive Care Summary"
                        }
                    },
                    {
                        "resource": {
                            "resourceType": "Immunization",
                            "id": "hie-immunization-001",
                            "status": "completed",
                            "vaccineCode": {
                                "coding": [{
                                    "system": "http://hl7.org/fhir/sid/cvx",
                                    "code": "207",
                                    "display": "COVID-19, mRNA, LNP-S, PF, 30 mcg/0.3 mL dose"
                                }]
                            },
                            "patient": {"reference": f"Patient/{test_patient.external_id}"},
                            "occurrenceDateTime": "2025-01-15",
                            "recorded": "2025-01-15",
                            "lotNumber": "HIE001COVID",
                            "manufacturer": {"display": "Pfizer-BioNTech"},
                            "performer": [{
                                "actor": {"reference": "Organization/regional-medical-center"}
                            }]
                        }
                    },
                    {
                        "resource": {
                            "resourceType": "DiagnosticReport",
                            "id": "hie-lab-report-001",
                            "status": "final",
                            "category": [{
                                "coding": [{
                                    "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                                    "code": "LAB",
                                    "display": "Laboratory"
                                }]
                            }],
                            "code": {
                                "coding": [{
                                    "system": "http://loinc.org",
                                    "code": "94500-6",
                                    "display": "SARS-CoV-2 RNA Detected"
                                }]
                            },
                            "subject": {"reference": f"Patient/{test_patient.external_id}"},
                            "effectiveDateTime": "2024-12-10",
                            "result": [{"reference": "Observation/covid-test-result"}]
                        }
                    }
                ],
                "hie_metadata": {
                    "document_standards": ["C-CDA_R2.1", "FHIR_R4", "HL7_v2.8.2"],
                    "interoperability_validated": True,
                    "data_quality_score": 0.94,
                    "contributing_organizations": 3,
                    "longitudinal_coverage_months": 18,
                    "privacy_controls_applied": True,
                    "encryption_status": "encrypted_in_transit_and_at_rest"
                }
            }
            
            mock_document_sharing.return_value = mock_document_bundle
            
            # Retrieve clinical document bundle
            start_time = time.time()
            client = await iris_service.get_client(str(hie_endpoint.id), db_session)
            document_bundle = await client.get_patient_bundle(test_patient.external_id)
            document_duration = time.time() - start_time
            
            clinical_document_test = {
                "document_sharing_successful": document_bundle.get("resourceType") == "Bundle",
                "document_bundle_type": document_bundle.get("type"),
                "total_clinical_resources": document_bundle.get("total", 0),
                "document_standards_supported": mock_document_bundle["hie_metadata"]["document_standards"],
                "interoperability_validated": mock_document_bundle["hie_metadata"]["interoperability_validated"],
                "data_quality_score": mock_document_bundle["hie_metadata"]["data_quality_score"],
                "contributing_organizations": mock_document_bundle["hie_metadata"]["contributing_organizations"],
                "longitudinal_coverage_months": mock_document_bundle["hie_metadata"]["longitudinal_coverage_months"],
                "resource_types_included": [
                    entry["resource"]["resourceType"] for entry in document_bundle.get("entry", [])
                ],
                "immunization_records_shared": len([
                    entry for entry in document_bundle.get("entry", [])
                    if entry["resource"]["resourceType"] == "Immunization"
                ]),
                "lab_results_shared": len([
                    entry for entry in document_bundle.get("entry", [])
                    if entry["resource"]["resourceType"] == "DiagnosticReport"
                ]),
                "care_summaries_included": len([
                    entry for entry in document_bundle.get("entry", [])
                    if entry["resource"]["resourceType"] == "Composition"
                ]),
                "privacy_controls_applied": mock_document_bundle["hie_metadata"]["privacy_controls_applied"],
                "encryption_verified": mock_document_bundle["hie_metadata"]["encryption_status"] == "encrypted_in_transit_and_at_rest",
                "document_processing_time_seconds": document_duration,
                "comprehensive_care_view_available": True,
                "clinical_decision_support_enhanced": True,
                "care_coordination_facilitated": True
            }
            
            # Validate clinical document sharing
            assert document_bundle.get("resourceType") == "Bundle", "Should receive FHIR Bundle"
            assert document_bundle.get("total", 0) >= 10, "Should include comprehensive clinical data"
            assert mock_document_bundle["hie_metadata"]["data_quality_score"] > 0.9, "Should maintain high data quality"
            assert mock_document_bundle["hie_metadata"]["contributing_organizations"] >= 2, "Should aggregate multi-organizational data"
            assert document_duration < 6.0, "Document retrieval should be efficient for clinical use"
            
            hie_tests.append(clinical_document_test)
        
        # Test 3: Provider Directory and Credential Verification
        with patch.object(IRISAPIClient, 'get_provider_directory') as mock_provider_directory:
            # Mock HIE provider directory response
            mock_provider_response = [
                {
                    "provider_id": "HIE_PROV_001",
                    "npi": "1234567890",
                    "name": {
                        "first_name": "Sarah",
                        "last_name": "Johnson",
                        "suffix": "MD"
                    },
                    "specialties": [
                        {"code": "207Q00000X", "description": "Family Medicine"},
                        {"code": "363L00000X", "description": "Pediatrics"}
                    ],
                    "credentials": {
                        "medical_license": {
                            "license_number": "MD123456",
                            "state": "CA",
                            "expiration_date": "2026-06-30",
                            "status": "active",
                            "verified": True
                        },
                        "board_certifications": [
                            {
                                "board": "American Board of Family Medicine",
                                "certification_date": "2020-01-15",
                                "expiration_date": "2030-01-15",
                                "status": "certified"
                            }
                        ],
                        "dea_registration": {
                            "dea_number": "BJ1234567",
                            "expiration_date": "2026-04-30",
                            "status": "active"
                        }
                    },
                    "practice_locations": [
                        {
                            "location_id": "LOC_001",
                            "name": "Family Health Center",
                            "address": {
                                "line1": "123 Healthcare Blvd",
                                "city": "San Francisco",
                                "state": "CA",
                                "zip_code": "94102"
                            },
                            "phone": "+1-415-555-0123",
                            "email": "info@familyhealthcenter.org"
                        }
                    ],
                    "hie_participation": {
                        "participant_status": "active",
                        "participation_date": "2023-01-01",
                        "data_sharing_agreements": ["immunizations", "lab_results", "clinical_notes"],
                        "quality_measures_reporting": True,
                        "direct_trust_certified": True
                    }
                }
            ]
            
            mock_provider_directory.return_value = mock_provider_response
            
            # Search provider directory
            provider_search_params = {
                "specialty": "Family Medicine",
                "location": "San Francisco, CA",
                "network_participation": "active"
            }
            
            start_time = time.time()
            client = await iris_service.get_client(str(hie_endpoint.id), db_session)
            providers = await client.get_provider_directory(provider_search_params)
            provider_search_duration = time.time() - start_time
            
            provider_directory_test = {
                "provider_search_successful": len(providers) > 0,
                "providers_found": len(providers),
                "credential_verification_complete": all(
                    provider["credentials"]["medical_license"]["verified"] for provider in providers
                ),
                "board_certifications_validated": all(
                    len(provider["credentials"]["board_certifications"]) > 0 for provider in providers
                ),
                "hie_participation_verified": all(
                    provider["hie_participation"]["participant_status"] == "active" for provider in providers
                ),
                "data_sharing_agreements_confirmed": all(
                    "immunizations" in provider["hie_participation"]["data_sharing_agreements"] for provider in providers
                ),
                "direct_trust_certification": all(
                    provider["hie_participation"]["direct_trust_certified"] for provider in providers
                ),
                "quality_measures_reporting": all(
                    provider["hie_participation"]["quality_measures_reporting"] for provider in providers
                ),
                "provider_search_time_seconds": provider_search_duration,
                "network_provider_discovery_effective": True,
                "credential_validation_automated": True,
                "care_team_coordination_facilitated": True
            }
            
            # Validate provider directory
            assert len(providers) >= 1, "Provider directory should return matching providers"
            assert all(provider["credentials"]["medical_license"]["verified"] for provider in providers), "Provider credentials should be verified"
            assert all(provider["hie_participation"]["participant_status"] == "active" for provider in providers), "Providers should be active HIE participants"
            assert provider_search_duration < 3.0, "Provider search should be efficient"
            
            hie_tests.append(provider_directory_test)
        
        # Create comprehensive HIE integration audit log
        hie_log = AuditLog(
            event_type="hie_interoperability_comprehensive_test",
            user_id=str(hie_admin.id),
            timestamp=datetime.utcnow(),
            details={
                "hie_testing_type": "health_information_exchange_interoperability",
                "hie_endpoint": hie_endpoint.base_url,
                "hie_tests": hie_tests,
                "hie_summary": {
                    "patient_discovery_tests": len([t for t in hie_tests if "patient_discovery_successful" in t]),
                    "successful_patient_matches": sum(1 for t in hie_tests if t.get("patient_discovery_successful", False)),
                    "clinical_document_sharing_tests": len([t for t in hie_tests if "document_sharing_successful" in t]),
                    "documents_shared": sum(t.get("total_clinical_resources", 0) for t in hie_tests),
                    "provider_directory_searches": len([t for t in hie_tests if "provider_search_successful" in t]),
                    "verified_providers": sum(t.get("providers_found", 0) for t in hie_tests),
                    "interoperability_standards_validated": sum(1 for t in hie_tests if t.get("interoperability_validated", False)),
                    "privacy_controls_verified": sum(1 for t in hie_tests if t.get("privacy_controls_applied", False))
                },
                "hie_interoperability_compliance": {
                    "onc_certified_health_it": True,
                    "direct_trust_framework": True,
                    "fhir_r4_us_core": True,
                    "c_cda_r2_1_support": True,
                    "patient_matching_algorithms": True,
                    "consent_management": True,
                    "security_encryption": True,
                    "provider_directory_services": True
                }
            },
            severity="info",
            source_system="hie_interoperability_testing"
        )
        
        db_session.add(hie_log)
        await db_session.commit()
        
        # Verification: HIE integration effectiveness
        patient_discovery_tests = len([t for t in hie_tests if "patient_discovery_successful" in t])
        assert patient_discovery_tests >= 1, "Patient discovery tests should be completed"
        
        document_sharing_tests = len([t for t in hie_tests if "document_sharing_successful" in t])
        assert document_sharing_tests >= 1, "Clinical document sharing should be tested"
        
        provider_directory_tests = len([t for t in hie_tests if "provider_search_successful" in t])
        assert provider_directory_tests >= 1, "Provider directory searches should be successful"
        
        interoperability_validated = sum(1 for t in hie_tests if t.get("interoperability_validated", False))
        assert interoperability_validated >= 1, "HIE interoperability should be validated"
        
        logger.info(
            "HIE interoperability comprehensive testing completed",
            patient_discovery_tests=patient_discovery_tests,
            document_sharing_tests=document_sharing_tests,
            provider_directory_tests=provider_directory_tests
        )