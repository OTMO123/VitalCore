"""
Healthcare Role Testing Configuration and Fixtures

Provides test fixtures and utilities for healthcare role-based security testing.
Ensures proper test isolation and HIPAA-compliant test data handling.
"""

import pytest
import pytest_asyncio
import asyncio
import uuid
from typing import Dict, List, Optional, AsyncGenerator
from httpx import AsyncClient
import httpx
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

from app.core.database_unified import Base, get_db, User, Patient
from app.core.config import get_settings
from app.main import app
from app.modules.auth.schemas import UserCreate
from app.modules.healthcare_records.schemas import PatientCreate


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Removed test_db_engine fixture - using unified database instead


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create isolated database session for each test using unified database."""
    from app.core.database_unified import get_session_factory
    
    session_factory = await get_session_factory()
    
    async with session_factory() as session:
        yield session
        await session.rollback()  # Ensure test isolation


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for testing."""
    
    # Create transport that routes to our FastAPI app  
    transport = httpx.ASGITransport(app=app)
    
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def test_users(db_session: AsyncSession) -> Dict[str, User]:
    """Create standard test users for role-based testing."""
    
    users = {}
    
    # Create test users for different roles
    user_configs = [
        {
            "username": "test_admin",
            "email": "admin@test.com", 
            "role": "admin",
            "password": "AdminPassword123!"
        },
        {
            "username": "test_doctor",
            "email": "doctor@test.com",
            "role": "doctor", 
            "password": "DoctorPassword123!"
        },
        {
            "username": "test_patient",
            "email": "patient@test.com",
            "role": "patient",
            "password": "PatientPassword123!"
        },
        {
            "username": "test_lab_tech",
            "email": "lab@test.com",
            "role": "lab_technician",
            "password": "LabPassword123!"
        },
        {
            "username": "test_nurse",
            "email": "nurse@test.com",
            "role": "nurse", 
            "password": "NursePassword123!"
        }
    ]
    
    for config in user_configs:
        from app.modules.auth.service import auth_service
        
        user_create = UserCreate(
            username=config["username"],
            email=config["email"],
            password=config["password"],
            role=config["role"]
        )
        
        user = await auth_service.create_user(user_create, db_session)
        users[config["role"]] = user
    
    await db_session.commit()
    return users


@pytest.fixture 
@pytest.mark.asyncio
async def test_patients(db_session: AsyncSession, test_users: Dict[str, User]) -> List[Patient]:
    """Create test patients with proper consent and assignments."""
    
    patients = []
    
    # Create diverse test patients
    patient_configs = [
        {
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1990-01-01",
            "gender": "male",
            "consent_types": ["treatment", "data_sharing"]
        },
        {
            "first_name": "Jane", 
            "last_name": "Smith",
            "date_of_birth": "1985-05-15",
            "gender": "female",
            "consent_types": ["treatment", "research"]
        },
        {
            "first_name": "Bob",
            "last_name": "Johnson", 
            "date_of_birth": "1975-12-31",
            "gender": "male",
            "consent_types": ["treatment"]
        }
    ]
    
    from app.modules.healthcare_records.service import get_healthcare_service
    from app.modules.healthcare_records.service import AccessContext
    
    service = await get_healthcare_service(session=db_session)
    
    for config in patient_configs:
        # Create access context for patient creation
        context = AccessContext(
            user_id=str(test_users["admin"].id),
            purpose="testing",
            role="admin",
            ip_address="127.0.0.1",
            session_id="test_session"
        )
        
        patient_create = PatientCreate(
            first_name=config["first_name"],
            last_name=config["last_name"],
            date_of_birth=config["date_of_birth"],
            gender=config["gender"]
        )
        
        patient = await service.patient_service.create_patient(
            patient_data=patient_create,
            context=context
        )
        
        # Set up consent
        patient.consent_status = {
            "status": "active",
            "types": config["consent_types"],
            "granted_date": datetime.now().isoformat(),
            "expiry_date": (datetime.now() + timedelta(days=365)).isoformat()
        }
        
        patients.append(patient)
    
    await db_session.commit()
    return patients


@pytest.fixture
async def patient_assignments(
    db_session: AsyncSession, 
    test_users: Dict[str, User], 
    test_patients: List[Patient]
) -> Dict[str, List[str]]:
    """Create patient assignments for testing role-based access."""
    
    assignments = {
        "doctor": [],
        "nurse": [],
        "lab_technician": []
    }
    
    # Assign first patient to doctor
    if len(test_patients) > 0:
        assignments["doctor"].append(str(test_patients[0].id))
    
    # Assign second patient to nurse
    if len(test_patients) > 1:
        assignments["nurse"].append(str(test_patients[1].id))
    
    # Lab tech gets access to lab orders for all patients
    assignments["lab_technician"] = [str(p.id) for p in test_patients]
    
    return assignments


class HealthcareTestHelper:
    """Helper class for healthcare role testing utilities."""
    
    @staticmethod
    async def create_test_user(
        db_session: AsyncSession,
        username: str,
        role: str,
        email: str,
        password: str = "TestPassword123!"
    ) -> User:
        """Create a test user with specified role."""
        
        from app.modules.auth.service import auth_service
        
        user_create = UserCreate(
            username=username,
            email=email,
            password=password,
            role=role
        )
        
        user = await auth_service.create_user(user_create, db_session)
        await db_session.commit()
        return user
    
    @staticmethod
    async def get_auth_headers(
        async_client: AsyncClient,
        username: str,
        password: str
    ) -> Dict[str, str]:
        """Get authentication headers for API requests."""
        
        login_data = {
            "username": username,
            "password": password
        }
        
        response = await async_client.post(
            "/api/v1/auth/login",
            json=login_data
        )
        
        if response.status_code != 200:
            raise Exception(f"Authentication failed for {username}: {response.text}")
        
        token_data = response.json()
        return {
            "Authorization": f"Bearer {token_data['access_token']}",
            "Content-Type": "application/json"
        }
    
    @staticmethod
    async def create_test_patient(
        async_client: AsyncClient,
        auth_headers: Dict[str, str],
        patient_data: Optional[Dict] = None
    ) -> Dict:
        """Create a test patient with proper FHIR compliance."""
        
        if patient_data is None:
            patient_data = {
                "first_name": f"Test_{uuid.uuid4().hex[:8]}",
                "last_name": f"Patient_{uuid.uuid4().hex[:8]}",
                "date_of_birth": "1990-01-01",
                "gender": "male"
            }
        
        response = await async_client.post(
            "/api/v1/healthcare/patients",
            json=patient_data,
            headers=auth_headers
        )
        
        if response.status_code != 201:
            raise Exception(f"Patient creation failed: {response.text}")
        
        return response.json()
    
    @staticmethod
    async def verify_audit_log_entry(
        async_client: AsyncClient,
        auth_headers: Dict[str, str],
        event_type: str,
        user_id: str,
        resource_id: Optional[str] = None
    ) -> bool:
        """Verify that an audit log entry exists for compliance checking."""
        
        params = {
            "event_type": event_type,
            "user_id": user_id
        }
        
        if resource_id:
            params["resource_id"] = resource_id
        
        response = await async_client.get(
            "/api/v1/audit/logs",
            params=params,
            headers=auth_headers
        )
        
        if response.status_code != 200:
            return False
        
        audit_data = response.json()
        return len(audit_data.get("audit_logs", [])) > 0
    
    @staticmethod
    def assert_hipaa_compliance_headers(response_headers: Dict[str, str]):
        """Assert that response headers meet HIPAA compliance requirements."""
        
        # Check for security headers
        assert "x-content-type-options" in response_headers
        assert "referrer-policy" in response_headers
        assert "permissions-policy" in response_headers
        
        # Check Content Security Policy
        assert "content-security-policy" in response_headers
        csp = response_headers["content-security-policy"]
        assert "frame-ancestors 'none'" in csp
        assert "object-src 'none'" in csp
    
    @staticmethod
    def assert_fhir_r4_compliance(patient_data: Dict):
        """Assert that patient data meets FHIR R4 compliance requirements."""
        
        # Required FHIR Patient resource fields
        assert patient_data.get("resourceType") == "Patient"
        assert "id" in patient_data
        assert "active" in patient_data
        
        # Name structure compliance
        if "name" in patient_data:
            names = patient_data["name"]
            assert isinstance(names, list)
            if len(names) > 0:
                name = names[0]
                assert "use" in name
                assert name["use"] in ["usual", "official", "temp", "nickname", "anonymous", "old", "maiden"]
    
    @staticmethod
    async def cleanup_test_data(
        db_session: AsyncSession,
        user_ids: List[str] = None,
        patient_ids: List[str] = None
    ):
        """Clean up test data after test completion."""
        
        try:
            # Clean up patients
            if patient_ids:
                from sqlalchemy import delete
                stmt = delete(Patient).where(Patient.id.in_(patient_ids))
                await db_session.execute(stmt)
            
            # Clean up users  
            if user_ids:
                from sqlalchemy import delete
                stmt = delete(User).where(User.id.in_(user_ids))
                await db_session.execute(stmt)
            
            await db_session.commit()
            
        except Exception as e:
            await db_session.rollback()
            # Log cleanup failure but don't fail the test
            print(f"Test cleanup warning: {e}")


@pytest.fixture
def healthcare_test_helper():
    """Provide healthcare testing helper utilities."""
    return HealthcareTestHelper


# Pytest markers for organizing healthcare role tests
pytest.mark.patient_role = pytest.mark.patient_role
pytest.mark.doctor_role = pytest.mark.doctor_role  
pytest.mark.lab_role = pytest.mark.lab_role
pytest.mark.nurse_role = pytest.mark.nurse_role
pytest.mark.admin_role = pytest.mark.admin_role
pytest.mark.security = pytest.mark.security
pytest.mark.compliance = pytest.mark.compliance
pytest.mark.hipaa = pytest.mark.hipaa
pytest.mark.fhir = pytest.mark.fhir
pytest.mark.integration = pytest.mark.integration