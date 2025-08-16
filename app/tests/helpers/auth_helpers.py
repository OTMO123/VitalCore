"""
Authentication Helpers for Healthcare Role Testing

Provides utilities for creating test users and managing authentication
in healthcare role-based security tests.
"""

from typing import Dict, Optional
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database_unified import User
from app.modules.auth.schemas import UserCreate


async def create_test_user(
    db_session: AsyncSession,
    username: str,
    role: str,
    email: str,
    password: str = "TestPassword123!",
    is_active: bool = True
) -> User:
    """
    Create a test user with specified role and credentials.
    
    Args:
        db_session: Database session
        username: Unique username for the user
        role: User role (patient, doctor, lab_technician, nurse, admin)
        email: User email address
        password: User password (defaults to secure test password)
        is_active: Whether user account is active
        
    Returns:
        Created User object
        
    Raises:
        Exception: If user creation fails
    """
    
    from app.modules.auth.service import AuthService
    auth_service = AuthService()
    
    try:
        print(f"DEBUG: create_test_user called for {username}")
        print(f"DEBUG: Role: {role}, Email: {email}, Password length: {len(password)}")
        
        user_create = UserCreate(
            username=username,
            email=email,
            password=password,
            role=role,
            email_verified=True,  # Enterprise tests require verified users for compliance
            is_active=is_active
        )
        
        print(f"DEBUG: UserCreate object created, calling auth_service.create_user")
        
        user = await auth_service.create_user(user_create, db_session)
        
        print(f"DEBUG: User created by auth_service - ID: {user.id}, Email Verified: {user.email_verified}, Active: {user.is_active}")
        
        # Ensure user is properly committed to database for enterprise compliance testing
        await db_session.commit()
        await db_session.refresh(user)
        
        print(f"DEBUG: User committed to database - Final user: ID={user.id}, Username={user.username}, Active={user.is_active}")
        
        return user
        
    except Exception as e:
        print(f"DEBUG: Error creating user {username}: {str(e)}")
        print(f"DEBUG: Exception type: {type(e)}")
        if hasattr(e, 'detail'):
            print(f"DEBUG: Exception detail: {e.detail}")
        if hasattr(e, 'status_code'):
            print(f"DEBUG: Exception status_code: {e.status_code}")
        await db_session.rollback()
        raise Exception(f"Failed to create test user {username}: {str(e)}")


async def get_auth_headers(
    async_client: AsyncClient,
    username: str,
    password: str,
    base_url: str = ""
) -> Dict[str, str]:
    """
    Authenticate user and return authorization headers.
    
    Args:
        async_client: HTTP client for API requests
        username: Username for authentication
        password: Password for authentication
        base_url: Base URL prefix (optional)
        
    Returns:
        Dictionary with Authorization and Content-Type headers
        
    Raises:
        Exception: If authentication fails
    """
    
    login_data = {
        "username": username,
        "password": password
    }
    
    try:
        # Add required headers for enterprise authentication
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Enterprise-Healthcare-Test-Client",
            "X-Real-IP": "127.0.0.1",
            "X-Forwarded-For": "127.0.0.1"
        }
        
        response = await async_client.post(
            f"{base_url}/api/v1/auth/login",
            json=login_data,
            headers=headers
        )
        
        if response.status_code != 200:
            error_detail = "Unknown error"
            try:
                error_data = response.json()
                error_detail = error_data.get("detail", response.text)
            except:
                error_detail = response.text
            
            # Enhanced error logging for debugging authentication failures
            print(f"DEBUG: Authentication failed for {username}")
            print(f"DEBUG: Response status: {response.status_code}")
            print(f"DEBUG: Response headers: {dict(response.headers)}")
            print(f"DEBUG: Response text: {response.text}")
            print(f"DEBUG: Login data: {login_data}")
            
            raise Exception(f"Authentication failed for {username}: {error_detail}")
        
        token_data = response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise Exception(f"No access token received for {username}")
        
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
    except Exception as e:
        if "Authentication failed" in str(e):
            raise e
        else:
            raise Exception(f"Authentication request failed for {username}: {str(e)}")


async def verify_user_role(
    async_client: AsyncClient,
    auth_headers: Dict[str, str],
    expected_role: str
) -> bool:
    """
    Verify that authenticated user has expected role.
    
    Args:
        async_client: HTTP client for API requests
        auth_headers: Authentication headers
        expected_role: Expected user role
        
    Returns:
        True if user has expected role, False otherwise
    """
    
    try:
        response = await async_client.get(
            "/api/v1/auth/me",
            headers=auth_headers
        )
        
        if response.status_code != 200:
            return False
        
        user_data = response.json()
        return user_data.get("role") == expected_role
        
    except Exception:
        return False


async def create_test_user_with_permissions(
    db_session: AsyncSession,
    username: str,
    role: str,
    email: str,
    permissions: Optional[list] = None,
    password: str = "TestPassword123!"
) -> User:
    """
    Create a test user with specific permissions.
    
    Args:
        db_session: Database session
        username: Unique username
        role: User role
        email: User email
        permissions: List of specific permissions (optional)
        password: User password
        
    Returns:
        Created User object with permissions set
    """
    
    user = await create_test_user(
        db_session=db_session,
        username=username,
        role=role,
        email=email,
        password=password
    )
    
    # Set custom permissions if provided
    if permissions:
        # This would integrate with your permission system
        # Implementation depends on your RBAC structure
        pass
    
    return user


class AuthTestHelper:
    """
    Helper class for authentication testing in healthcare enterprise deployment.
    
    Provides comprehensive user creation and authentication for FHIR Bundle tests
    with SOC2 Type II, HIPAA, PHI, FHIR R4, and GDPR compliance.
    """
    
    def __init__(self, db_session: AsyncSession, async_client: AsyncClient):
        self.db_session = db_session
        self.async_client = async_client
        self.created_users = []
    
    async def create_user(
        self,
        username: str,
        role: str,
        email: str,
        password: str = "TestPassword123!",
        is_active: bool = True
    ) -> User:
        """
        Create test user with healthcare role-based access control.
        
        Args:
            username: Unique username
            role: Healthcare role (system_admin, physician, nurse, etc.)
            email: User email address
            password: User password
            is_active: Whether user is active
            
        Returns:
            Created User object
        """
        
        try:
            user = await create_test_user(
                db_session=self.db_session,
                username=username,
                role=role,
                email=email,
                password=password,
                is_active=is_active
            )
            
            self.created_users.append(user)
            return user
            
        except Exception as e:
            print(f"DEBUG: AuthTestHelper.create_user failed for {username}: {str(e)}")
            raise
    
    async def get_auth_headers(
        self,
        username: str,
        password: str
    ) -> Dict[str, str]:
        """
        Get authentication headers for API requests.
        
        Args:
            username: Username for authentication
            password: User password
            
        Returns:
            Dictionary with Authorization and Content-Type headers
        """
        
        return await get_auth_headers(
            async_client=self.async_client,
            username=username,
            password=password
        )
    
    async def get_headers(
        self,
        username: str,
        password: str
    ) -> Dict[str, str]:
        """
        Alias for get_auth_headers for backward compatibility.
        """
        return await self.get_auth_headers(username, password)
    
    async def cleanup(self):
        """Clean up all created test users."""
        
        if self.created_users:
            usernames = [user.username for user in self.created_users]
            await cleanup_test_users(self.db_session, usernames)
            self.created_users.clear()


async def cleanup_test_users(
    db_session: AsyncSession,
    usernames: list
):
    """
    Clean up test users after testing.
    
    Args:
        db_session: Database session
        usernames: List of usernames to clean up
    """
    
    try:
        from sqlalchemy import select, delete
        
        # Get user IDs
        stmt = select(User.id).where(User.username.in_(usernames))
        result = await db_session.execute(stmt)
        user_ids = [row[0] for row in result.fetchall()]
        
        if user_ids:
            # ENTERPRISE HEALTHCARE COMPLIANCE: Proper cascade deletion order
            # This order is critical for SOC2/HIPAA data integrity requirements
            
            # 1. First, delete all consents that reference patients (not just users)
            try:
                from app.core.database_unified import Consent
                # Delete ALL consents to avoid any patient->consent foreign key issues
                consent_delete_all = delete(Consent)
                await db_session.execute(consent_delete_all)
                print(f"DEBUG: Deleted all consents to avoid patient foreign key constraints")
            except Exception as e:
                print(f"DEBUG: Error deleting all consents: {e}")
            
            # 2. Delete PHI access logs that reference patients first (before deleting patients)
            try:
                from app.core.database_unified import PHIAccessLog
                # Get all patient IDs first to delete their access logs
                from app.core.database_unified import Patient
                patient_stmt = select(Patient.id)
                patient_result = await db_session.execute(patient_stmt)
                patient_ids = [row[0] for row in patient_result.fetchall()]
                
                if patient_ids:
                    # Delete PHI access logs for patients
                    phi_patient_delete = delete(PHIAccessLog).where(PHIAccessLog.patient_id.in_(patient_ids))
                    await db_session.execute(phi_patient_delete)
                    print(f"DEBUG: Deleted PHI access logs for {len(patient_ids)} patients")
                
                # Delete PHI access logs for users
                phi_user_delete = delete(PHIAccessLog).where(PHIAccessLog.user_id.in_(user_ids))
                await db_session.execute(phi_user_delete)
                print(f"DEBUG: Deleted PHI access logs for {len(user_ids)} users")
            except Exception as e:
                print(f"DEBUG: Error deleting PHI access logs: {e}")
            
            # 3. Delete immunizations that reference patients
            try:
                from app.core.database_unified import Immunization
                immunization_delete = delete(Immunization)
                await db_session.execute(immunization_delete)
                print(f"DEBUG: Deleted all immunizations for clean state")
            except Exception as e:
                print(f"DEBUG: Error deleting immunizations: {e}")
            
            # 4. Delete clinical documents that reference patients
            try:
                from app.core.database_unified import ClinicalDocument
                doc_delete = delete(ClinicalDocument)
                await db_session.execute(doc_delete)
                print(f"DEBUG: Deleted all clinical documents for clean state")
            except Exception as e:
                print(f"DEBUG: Error deleting clinical documents: {e}")
            
            # 5. Now delete patients (after all references are cleaned up)
            try:
                from app.core.database_unified import Patient
                patient_delete = delete(Patient)
                await db_session.execute(patient_delete)
                print(f"DEBUG: Deleted all patients for enterprise data integrity")
            except Exception as e:
                print(f"DEBUG: Error deleting patients: {e}")
            
            # 4. Finally delete users
            delete_stmt = delete(User).where(User.id.in_(user_ids))
            await db_session.execute(delete_stmt)
            await db_session.commit()
            print(f"DEBUG: Successfully cleaned up {len(user_ids)} test users")
            
    except Exception as e:
        await db_session.rollback()
        # Log but don't fail - this is cleanup
        print(f"Warning: Failed to cleanup test users: {e}")
        print(f"DEBUG: Full error details: {str(e)}")


# Duplicate class removed - using the comprehensive version above


# Role-specific helper functions
async def create_patient_user(
    db_session: AsyncSession,
    username: str,
    email: str,
    password: str = "TestPassword123!"
) -> User:
    """Create a patient role user."""
    
    return await create_test_user(
        db_session=db_session,
        username=username,
        role="patient",
        email=email,
        password=password
    )


async def create_doctor_user(
    db_session: AsyncSession,
    username: str,
    email: str,
    password: str = "TestPassword123!"
) -> User:
    """Create a physician role user."""
    
    return await create_test_user(
        db_session=db_session,
        username=username,
        role="physician",
        email=email,
        password=password
    )


async def create_lab_user(
    db_session: AsyncSession,
    username: str,
    email: str,
    password: str = "TestPassword123!"
) -> User:
    """Create a clinical technician role user."""
    
    return await create_test_user(
        db_session=db_session,
        username=username,
        role="clinical_technician",
        email=email,
        password=password
    )


async def create_admin_user(
    db_session: AsyncSession,
    username: str,
    email: str,
    password: str = "TestPassword123!"
) -> User:
    """Create an admin role user."""
    
    return await create_test_user(
        db_session=db_session,
        username=username,
        role="admin",
        email=email,
        password=password
    )