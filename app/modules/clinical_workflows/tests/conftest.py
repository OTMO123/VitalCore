"""
Clinical Workflows Test Configuration and Fixtures

Comprehensive test setup for enterprise-grade testing with role-based scenarios.
Includes fixtures for different user roles: physicians, nurses, administrators, etc.
"""

import pytest
import asyncio
from datetime import datetime, date, timedelta
from uuid import uuid4, UUID
from typing import Dict, Any, List, Optional
from unittest.mock import AsyncMock, Mock, MagicMock

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.core.database_unified import Base, DataClassification
from app.core.security import security_manager, create_access_token
from app.core.database_unified import User
from app.modules.clinical_workflows.models import (
    ClinicalWorkflow, ClinicalWorkflowStep, ClinicalEncounter, ClinicalWorkflowAudit
)
from app.modules.auth.schemas import UserRole
from app.modules.clinical_workflows.schemas import (
    WorkflowType, WorkflowStatus, WorkflowPriority, EncounterClass, StepStatus
)
from app.modules.clinical_workflows.service import ClinicalWorkflowService
from app.modules.clinical_workflows.security import ClinicalWorkflowSecurity


# ======================== DATABASE FIXTURES ========================

@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine with isolated SQLite."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False  # Set to True for SQL debugging
    )
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(test_engine):
    """Create isolated database session for each test."""
    SessionLocal = sessionmaker(bind=test_engine)
    session = SessionLocal()
    
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def clean_db(db_session):
    """Clean database state between tests."""
    # Clear all tables
    for table in reversed(Base.metadata.sorted_tables):
        db_session.execute(table.delete())
    db_session.commit()
    return db_session


# ======================== USER ROLE FIXTURES ========================

@pytest.fixture
def physician_role():
    """Physician role for clinical workflows."""
    return Role(
        id=uuid4(),
        name="physician",
        description="Licensed physician with full clinical access",
        permissions=[
            "create_workflow", "view_workflow", "update_workflow", "complete_workflow",
            "create_encounter", "view_phi", "decrypt_phi", "clinical_documentation"
        ]
    )


@pytest.fixture
def nurse_role():
    """Nurse role with clinical documentation access."""
    return Role(
        id=uuid4(),
        name="nurse",
        description="Registered nurse with clinical documentation access",
        permissions=[
            "create_workflow", "view_workflow", "update_workflow",
            "create_encounter", "view_phi", "clinical_documentation"
        ]
    )


@pytest.fixture
def clinical_admin_role():
    """Clinical administrator role with analytics access."""
    return Role(
        id=uuid4(),
        name="clinical_admin",
        description="Clinical administrator with analytics access",
        permissions=[
            "view_workflow", "view_analytics", "generate_reports",
            "manage_workflows", "view_audit_logs"
        ]
    )


@pytest.fixture
def ai_researcher_role():
    """AI researcher role for data collection."""
    return Role(
        id=uuid4(),
        name="ai_researcher",
        description="AI researcher with anonymized data access",
        permissions=[
            "collect_ai_training_data", "view_anonymized_data",
            "research_access", "data_analysis"
        ]
    )


@pytest.fixture
def patient_role():
    """Patient role with limited access."""
    return Role(
        id=uuid4(),
        name="patient",
        description="Patient with access to own records",
        permissions=["view_own_records", "consent_management"]
    )


@pytest.fixture
def unauthorized_user_role():
    """Unauthorized user role for security testing."""
    return Role(
        id=uuid4(),
        name="unauthorized",
        description="User without clinical access",
        permissions=["basic_access"]
    )


# ======================== USER FIXTURES BY ROLE ========================

@pytest.fixture
def physician_user(physician_role):
    """Create physician user for testing."""
    return User(
        id=uuid4(),
        email="dr.smith@hospital.com",
        username="dr_smith",
        first_name="John",
        last_name="Smith",
        is_active=True,
        roles=[physician_role],
        department="Emergency Medicine",
        license_number="MD123456",
        specialization="Emergency Medicine"
    )


@pytest.fixture
def nurse_user(nurse_role):
    """Create nurse user for testing."""
    return User(
        id=uuid4(),
        email="nurse.johnson@hospital.com",
        username="nurse_johnson",
        first_name="Sarah",
        last_name="Johnson",
        is_active=True,
        roles=[nurse_role],
        department="Emergency Medicine",
        license_number="RN789012"
    )


@pytest.fixture
def clinical_admin_user(clinical_admin_role):
    """Create clinical administrator user for testing."""
    return User(
        id=uuid4(),
        email="admin.wilson@hospital.com",
        username="admin_wilson",
        first_name="Michael",
        last_name="Wilson",
        is_active=True,
        roles=[clinical_admin_role],
        department="Clinical Administration"
    )


@pytest.fixture
def ai_researcher_user(ai_researcher_role):
    """Create AI researcher user for testing."""
    return User(
        id=uuid4(),
        email="researcher.chen@ailab.com",
        username="ai_researcher",
        first_name="Lisa",
        last_name="Chen",
        is_active=True,
        roles=[ai_researcher_role],
        department="AI Research"
    )


@pytest.fixture
def patient_user(patient_role):
    """Create patient user for testing."""
    return User(
        id=uuid4(),
        email="patient.brown@email.com",
        username="patient_brown",
        first_name="Robert",
        last_name="Brown",
        is_active=True,
        roles=[patient_role]
    )


@pytest.fixture
def unauthorized_user(unauthorized_user_role):
    """Create unauthorized user for security testing."""
    return User(
        id=uuid4(),
        email="unauthorized@test.com",
        username="unauthorized",
        first_name="Test",
        last_name="User",
        is_active=True,
        roles=[unauthorized_user_role]
    )


# ======================== AUTHENTICATION FIXTURES ========================

@pytest.fixture
def physician_token(physician_user):
    """Create JWT token for physician user."""
    return create_access_token(
        data={"sub": str(physician_user.id), "email": physician_user.email},
        expires_delta=timedelta(hours=1)
    )


@pytest.fixture
def nurse_token(nurse_user):
    """Create JWT token for nurse user."""
    return create_access_token(
        data={"sub": str(nurse_user.id), "email": nurse_user.email},
        expires_delta=timedelta(hours=1)
    )


@pytest.fixture
def admin_token(clinical_admin_user):
    """Create JWT token for clinical admin user."""
    return create_access_token(
        data={"sub": str(clinical_admin_user.id), "email": clinical_admin_user.email},
        expires_delta=timedelta(hours=1)
    )


@pytest.fixture
def ai_researcher_token(ai_researcher_user):
    """Create JWT token for AI researcher user."""
    return create_access_token(
        data={"sub": str(ai_researcher_user.id), "email": ai_researcher_user.email},
        expires_delta=timedelta(hours=1)
    )


@pytest.fixture
def unauthorized_token(unauthorized_user):
    """Create JWT token for unauthorized user."""
    return create_access_token(
        data={"sub": str(unauthorized_user.id), "email": unauthorized_user.email},
        expires_delta=timedelta(hours=1)
    )


# ======================== SERVICE MOCKS ========================

@pytest.fixture
def mock_encryption_service():
    """Mock encryption service for testing."""
    service = AsyncMock()
    service.encrypt.return_value = "encrypted_test_data_hash"
    service.decrypt.return_value = "decrypted_test_data"
    return service


@pytest.fixture
def mock_audit_service():
    """Mock audit service for testing."""
    service = AsyncMock()
    service.log_event = AsyncMock()
    service.log_phi_access = AsyncMock()
    return service


@pytest.fixture
def mock_event_bus():
    """Mock event bus for testing."""
    bus = AsyncMock()
    bus.publish = AsyncMock()
    bus.subscribe = AsyncMock()
    return bus


@pytest_asyncio.fixture
async def healthcare_event_bus(test_engine):
    """
    Healthcare Event Bus fixture for clinical workflows testing.
    
    Provides real enterprise healthcare event bus for proper SOC2/HIPAA compliance testing.
    """
    try:
        from app.core.events.event_bus import initialize_event_bus, shutdown_event_bus
        from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
        import structlog
        
        logger = structlog.get_logger()
        
        # Create session factory from test engine
        session_factory = async_sessionmaker(
            test_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False
        )
        
        logger.info("Initializing healthcare event bus for clinical workflows tests")
        event_bus = await initialize_event_bus(session_factory)
        
        yield event_bus
        
        logger.info("Shutting down healthcare event bus for clinical workflows tests")
        await shutdown_event_bus()
        
    except Exception as e:
        # Fallback to comprehensive mock for tests that can't initialize the real event bus
        from unittest.mock import AsyncMock
        mock_bus = AsyncMock()
        mock_bus.publish_patient_created = AsyncMock(return_value=True)
        mock_bus.publish_patient_updated = AsyncMock(return_value=True)
        mock_bus.publish_phi_access = AsyncMock(return_value=True)
        mock_bus.publish_event = AsyncMock(return_value=True)
        mock_bus.publish_workflow_created = AsyncMock(return_value=True)
        mock_bus.publish_workflow_completed = AsyncMock(return_value=True)
        mock_bus.subscribe = AsyncMock()
        mock_bus.unsubscribe = AsyncMock()
        yield mock_bus


@pytest.fixture
def clinical_security(mock_encryption_service, mock_audit_service):
    """Create clinical security instance with mocked dependencies."""
    return ClinicalWorkflowSecurity(mock_encryption_service, mock_audit_service)


@pytest.fixture
def clinical_workflow_service(mock_encryption_service, mock_audit_service, mock_event_bus):
    """Create clinical workflow service with mocked dependencies."""
    return ClinicalWorkflowService(
        encryption_service=mock_encryption_service,
        audit_service=mock_audit_service,
        event_bus=mock_event_bus
    )


# ======================== TEST DATA FIXTURES ========================

@pytest.fixture
def patient_id():
    """Standard patient ID for testing."""
    return uuid4()


@pytest.fixture
def valid_workflow_data(patient_id, physician_user):
    """Valid workflow creation data."""
    return {
        "patient_id": patient_id,
        "provider_id": physician_user.id,
        "workflow_type": WorkflowType.ENCOUNTER,
        "priority": WorkflowPriority.ROUTINE,
        "chief_complaint": "Patient reports chest pain and shortness of breath",
        "history_present_illness": "Chest pain started 2 hours ago, radiating to left arm",
        "location": "Emergency Department",
        "department": "Emergency Medicine",
        "estimated_duration_minutes": 90,
        "allergies": ["Penicillin", "Latex"],
        "current_medications": ["Lisinopril 10mg daily", "Metformin 500mg BID"]
    }


@pytest.fixture
def valid_vital_signs():
    """Valid vital signs data."""
    return {
        "systolic_bp": 140,
        "diastolic_bp": 90,
        "heart_rate": 95,
        "respiratory_rate": 18,
        "temperature": 98.6,
        "oxygen_saturation": 98,
        "weight_kg": 75.0,
        "height_cm": 175.0,
        "pain_score": 7
    }


@pytest.fixture
def valid_soap_note():
    """Valid SOAP note data."""
    return {
        "subjective": "Patient reports severe chest pain, 8/10 intensity, radiating to left arm",
        "objective": "Patient appears uncomfortable, diaphoretic. VS: BP 140/90, HR 95, RR 18, O2 98%",
        "assessment": "Chest pain, rule out acute coronary syndrome. Possible angina.",
        "plan": "EKG, cardiac enzymes, chest X-ray. Monitor in ED. Cardiology consult."
    }


@pytest.fixture
def valid_clinical_codes():
    """Valid clinical codes for testing."""
    return [
        {
            "code": "R06.02",
            "display": "Shortness of breath",
            "system": "http://hl7.org/fhir/sid/icd-10-cm",
            "version": "2024"
        },
        {
            "code": "R50.9",
            "display": "Fever, unspecified",
            "system": "http://hl7.org/fhir/sid/icd-10-cm"
        }
    ]


@pytest.fixture
def edge_case_data():
    """Edge case data for boundary testing."""
    return {
        "max_blood_pressure": {"systolic_bp": 300, "diastolic_bp": 200},
        "min_heart_rate": {"heart_rate": 20},
        "max_pain_score": {"pain_score": 10},
        "min_temperature": {"temperature": 80.0},
        "max_oxygen_saturation": {"oxygen_saturation": 100},
        "empty_strings": {"chief_complaint": "", "notes": ""},
        "null_values": {"allergies": None, "medications": None},
        "max_text_length": {"chief_complaint": "a" * 10000}
    }


@pytest.fixture
def malicious_data():
    """Malicious data for security testing."""
    return {
        "sql_injection": {
            "chief_complaint": "'; DROP TABLE clinical_workflows; --",
            "notes": "admin'; UPDATE users SET role='admin' WHERE id=1; --"
        },
        "xss_injection": {
            "chief_complaint": "<script>alert('XSS')</script>",
            "notes": "<img src=x onerror=alert('XSS')>"
        },
        "path_traversal": {
            "notes": "../../../etc/passwd",
            "assessment": "..\\..\\..\\windows\\system32\\config\\sam"
        },
        "large_payload": {
            "chief_complaint": "A" * 1000000,  # 1MB of data
            "notes": "B" * 1000000
        }
    }


# ======================== WORKFLOW STATE FIXTURES ========================

@pytest.fixture
def active_workflow(db_session, patient_id, physician_user):
    """Create an active workflow for testing."""
    workflow = ClinicalWorkflow(
        patient_id=patient_id,
        provider_id=physician_user.id,
        workflow_type=WorkflowType.ENCOUNTER.value,
        status=WorkflowStatus.ACTIVE.value,
        priority=WorkflowPriority.ROUTINE.value,
        chief_complaint_encrypted="encrypted_complaint",
        workflow_start_time=datetime.utcnow(),
        created_by=physician_user.id,
        data_classification=DataClassification.PHI.value
    )
    db_session.add(workflow)
    db_session.commit()
    return workflow


@pytest.fixture
def completed_workflow(db_session, patient_id, physician_user):
    """Create a completed workflow for testing."""
    workflow = ClinicalWorkflow(
        patient_id=patient_id,
        provider_id=physician_user.id,
        workflow_type=WorkflowType.ENCOUNTER.value,
        status=WorkflowStatus.COMPLETED.value,
        priority=WorkflowPriority.ROUTINE.value,
        chief_complaint_encrypted="encrypted_complaint",
        workflow_start_time=datetime.utcnow() - timedelta(hours=2),
        workflow_end_time=datetime.utcnow(),
        completion_percentage=100,
        actual_duration_minutes=120,
        created_by=physician_user.id,
        data_classification=DataClassification.PHI.value
    )
    db_session.add(workflow)
    db_session.commit()
    return workflow


@pytest.fixture
def emergency_workflow(db_session, patient_id, physician_user):
    """Create an emergency workflow for testing."""
    workflow = ClinicalWorkflow(
        patient_id=patient_id,
        provider_id=physician_user.id,
        workflow_type=WorkflowType.EMERGENCY.value,
        status=WorkflowStatus.ACTIVE.value,
        priority=WorkflowPriority.EMERGENCY.value,
        chief_complaint_encrypted="encrypted_emergency_complaint",
        workflow_start_time=datetime.utcnow(),
        risk_score=95,
        created_by=physician_user.id,
        data_classification=DataClassification.PHI.value
    )
    db_session.add(workflow)
    db_session.commit()
    return workflow


# ======================== PERFORMANCE TESTING FIXTURES ========================

@pytest.fixture
def performance_benchmark():
    """Performance benchmarking fixture."""
    def benchmark(func, *args, **kwargs):
        import time
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        return result, execution_time
    return benchmark


@pytest.fixture
def concurrent_users():
    """Generate concurrent user scenarios."""
    def create_user_scenario(role_type: str, count: int):
        users = []
        for i in range(count):
            user_id = uuid4()
            users.append({
                "id": user_id,
                "role": role_type,
                "email": f"{role_type}_{i}@test.com",
                "token": create_access_token(data={"sub": str(user_id)})
            })
        return users
    return create_user_scenario


# ======================== COMPLIANCE TESTING FIXTURES ========================

@pytest.fixture
def hipaa_test_scenario():
    """HIPAA compliance testing scenario."""
    return {
        "phi_fields": [
            "chief_complaint", "history_present_illness", "allergies",
            "current_medications", "assessment", "plan", "progress_notes"
        ],
        "access_purposes": [
            "treatment", "payment", "healthcare_operations",
            "research", "emergency", "patient_request"
        ],
        "audit_requirements": [
            "user_identification", "access_timestamp", "phi_fields_accessed",
            "access_purpose", "patient_identification"
        ]
    }


@pytest.fixture
def soc2_test_scenario():
    """SOC2 compliance testing scenario."""
    return {
        "security_controls": [
            "encryption_at_rest", "encryption_in_transit", "access_controls",
            "audit_logging", "data_retention", "incident_response"
        ],
        "availability_controls": [
            "system_monitoring", "backup_procedures", "disaster_recovery"
        ],
        "processing_integrity": [
            "data_validation", "error_handling", "transaction_completeness"
        ]
    }


@pytest.fixture
def fhir_r4_test_scenario():
    """FHIR R4 compliance testing scenario."""
    return {
        "encounter_classes": ["AMB", "EMER", "IMP", "OBSENC", "SS"],
        "encounter_statuses": ["planned", "arrived", "triaged", "in-progress", "finished"],
        "required_fields": ["encounter_class", "encounter_status", "encounter_datetime"],
        "optional_fields": ["location", "service_provider", "participant"]
    }


# ======================== API CLIENT FIXTURES ========================

@pytest.fixture
async def async_client():
    """Async HTTP client for API testing."""
    from app.main import app
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def client():
    """Synchronous HTTP client for API testing."""
    from app.main import app
    return TestClient(app)


# ======================== HELPER FUNCTIONS ========================

@pytest.fixture
def assert_phi_encrypted():
    """Helper to assert PHI fields are encrypted."""
    def check_encryption(data: Dict[str, Any], phi_fields: List[str]):
        for field in phi_fields:
            encrypted_field = f"{field}_encrypted"
            if encrypted_field in data:
                assert data[encrypted_field] is not None
                assert data[encrypted_field] != ""
                # Ensure original field is not present in plaintext
                assert field not in data or data[field] is None
    return check_encryption


@pytest.fixture
def assert_audit_logged():
    """Helper to assert audit events are logged."""
    def check_audit(mock_audit_service, event_type: str, user_id: str):
        mock_audit_service.log_event.assert_called()
        call_args = mock_audit_service.log_event.call_args
        assert call_args[1]["event_type"] == event_type
        assert call_args[1]["user_id"] == user_id
    return check_audit


@pytest.fixture
def role_based_headers():
    """Generate headers for different user roles."""
    def create_headers(token: str) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    return create_headers


# ======================== ASYNCIO CONFIGURATION ========================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async testing."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ======================== PYTEST MARKERS ========================

# Register custom markers
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.security = pytest.mark.security
pytest.mark.performance = pytest.mark.performance
pytest.mark.e2e = pytest.mark.e2e
pytest.mark.chaos = pytest.mark.chaos
pytest.mark.physician = pytest.mark.physician
pytest.mark.nurse = pytest.mark.nurse
pytest.mark.admin = pytest.mark.admin
pytest.mark.patient = pytest.mark.patient
pytest.mark.ai_researcher = pytest.mark.ai_researcher
pytest.mark.unauthorized = pytest.mark.unauthorized

# ======================== USER ROLE FIXTURES ========================

@pytest.fixture
def admin_user_data():
    """Test data for admin user."""
    return {
        "email": "admin@test.com",
        "username": "admin",
        "password": "admin123",
        "role": UserRole.ADMIN,
        "is_active": True
    }

@pytest.fixture
def physician_user_data():
    """Test data for physician user."""
    return {
        "email": "physician@test.com", 
        "username": "physician",
        "password": "physician123",
        "role": UserRole.USER,  # Physicians are typically USER role with specific permissions
        "is_active": True
    }

@pytest.fixture
def nurse_user_data():
    """Test data for nurse user."""
    return {
        "email": "nurse@test.com",
        "username": "nurse", 
        "password": "nurse123",
        "role": UserRole.OPERATOR,
        "is_active": True
    }
