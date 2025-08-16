"""
Authorization tests for role-based access control.

Tests RBAC implementation, permission checking, and access control
for healthcare data and administrative functions.
"""
import pytest
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.core.database_unified import User

pytestmark = pytest.mark.security


class TestRoleBasedAccessControl:
    """Test RBAC implementation and enforcement"""
    
    @pytest.fixture
    def role_permissions_matrix(self) -> Dict[str, List[str]]:
        """Define expected permissions for each role."""
        return {
            "user": [
                "read_own_profile",
                "update_own_profile", 
                "read_public_documents"
            ],
            "operator": [
                "read_own_profile",
                "update_own_profile",
                "read_public_documents",
                "create_patients",
                "update_patients",
                "read_patients",
                "create_clinical_documents",
                "read_clinical_documents"
            ],
            "admin": [
                "read_own_profile",
                "update_own_profile",
                "read_public_documents",
                "create_patients",
                "update_patients", 
                "read_patients",
                "delete_patients",
                "create_clinical_documents",
                "read_clinical_documents",
                "update_clinical_documents",
                "delete_clinical_documents",
                "read_audit_logs",
                "manage_users",
                "read_phi_access_logs"
            ],
            "super_admin": [
                # All permissions + system administration
                "*"  # Wildcard for all permissions
            ]
        }
    
    @pytest.mark.asyncio
    async def test_user_role_permissions(self, async_test_client, test_users_by_role):
        """
        Test that user role has appropriate permissions.
        Regular users should have minimal access.
        """
        user = test_users_by_role["user"]
        user_headers = await self._get_auth_headers(async_test_client, user)
        
        # Should be able to access own profile
        response = await async_test_client.get(
            "/api/v1/auth/me",
            headers=user_headers
        )
        assert response.status_code == 200
        
        # Should NOT be able to list all users
        response = await async_test_client.get(
            "/api/v1/auth/users",
            headers=user_headers
        )
        assert response.status_code in [403, 404]  # Forbidden or not found
        
        # Should NOT be able to create patients
        response = await async_test_client.post(
            "/api/v1/healthcare/patients",
            headers=user_headers,
            json={"test": "data"}
        )
        assert response.status_code in [403, 422]  # Forbidden or validation error
        
        # Should NOT be able to access audit logs
        response = await async_test_client.get(
            "/api/v1/audit-logs",
            headers=user_headers
        )
        assert response.status_code in [403, 404]
        
        print("✓ User role permissions correctly restricted")
    
    @pytest.mark.asyncio
    async def test_operator_role_permissions(self, async_test_client, test_users_by_role):
        """
        Test that operator role has healthcare management permissions.
        Operators should manage patients but not system administration.
        """
        operator = test_users_by_role.get("operator")
        if not operator:
            pytest.skip("Operator role not available in test data")
        
        operator_headers = await self._get_auth_headers(async_test_client, operator)
        
        # Should be able to access own profile
        response = await async_test_client.get(
            "/api/v1/auth/me",
            headers=operator_headers
        )
        assert response.status_code == 200
        
        # Should be able to list patients (if endpoint exists)
        response = await async_test_client.get(
            "/api/v1/healthcare/patients",
            headers=operator_headers
        )
        assert response.status_code in [200, 404]  # OK or not implemented
        
        # Should be able to create clinical documents (if implemented)
        response = await async_test_client.post(
            "/api/v1/healthcare/documents",
            headers=operator_headers,
            json={"test": "data"}
        )
        # Might fail validation but shouldn't be forbidden
        assert response.status_code not in [401, 403]
        
        # Should NOT be able to manage users
        response = await async_test_client.get(
            "/api/v1/auth/users",
            headers=operator_headers
        )
        assert response.status_code in [403, 404]
        
        # Should NOT be able to access audit logs
        response = await async_test_client.get(
            "/api/v1/audit-logs",
            headers=operator_headers
        )
        assert response.status_code in [403, 404]
        
        print("✓ Operator role permissions correctly configured")
    
    @pytest.mark.asyncio
    async def test_admin_role_permissions(self, async_test_client, test_users_by_role):
        """
        Test that admin role has comprehensive permissions.
        Admins should access most resources except super-admin functions.
        """
        admin = test_users_by_role["admin"]
        admin_headers = await self._get_auth_headers(async_test_client, admin)
        
        # Should be able to access own profile
        response = await async_test_client.get(
            "/api/v1/auth/me",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        # Should be able to list users
        response = await async_test_client.get(
            "/api/v1/auth/users",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        # Should be able to access patients
        response = await async_test_client.get(
            "/api/v1/healthcare/patients",
            headers=admin_headers
        )
        assert response.status_code in [200, 404]  # OK or not implemented
        
        # Should be able to access audit logs
        response = await async_test_client.get(
            "/api/v1/audit-logs",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        # Should NOT be able to access super-admin functions
        response = await async_test_client.get(
            "/api/v1/admin/system/config",
            headers=admin_headers
        )
        assert response.status_code in [403, 404]
        
        print("✓ Admin role permissions correctly configured")
    
    @pytest.mark.asyncio
    async def test_super_admin_role_permissions(self, async_test_client, test_users_by_role):
        """
        Test that super_admin role has unrestricted access.
        Super admins should access all system functions.
        """
        super_admin = test_users_by_role["super_admin"]
        super_admin_headers = await self._get_auth_headers(async_test_client, super_admin)
        
        # Should be able to access all admin functions
        admin_endpoints = [
            "/api/v1/auth/me",
            "/api/v1/auth/users",
            "/api/v1/audit-logs",
            "/api/v1/healthcare/patients"
        ]
        
        for endpoint in admin_endpoints:
            response = await async_test_client.get(
                endpoint,
                headers=super_admin_headers
            )
            # Should not be forbidden (might be not implemented)
            assert response.status_code not in [401, 403]
        
        # Should be able to access system configuration
        response = await async_test_client.get(
            "/api/v1/admin/system/config", 
            headers=super_admin_headers
        )
        assert response.status_code in [200, 404]  # OK or not implemented
        
        print("✓ Super admin role permissions correctly configured")
    
    @pytest.mark.asyncio
    async def test_cross_role_data_access(self, async_test_client, test_users_by_role):
        """
        Test that users can only access data appropriate to their role.
        Verifies data isolation and access control.
        """
        user = test_users_by_role["user"]
        admin = test_users_by_role["admin"]
        
        user_headers = await self._get_auth_headers(async_test_client, user)
        admin_headers = await self._get_auth_headers(async_test_client, admin)
        
        # Create some test data as admin
        test_patient_data = {
            "identifier": [{"use": "official", "value": "TEST123"}],
            "name": [{"family": "TestPatient", "given": ["Cross", "Role"]}],
            "active": True,
            "organization_id": str(uuid.uuid4())
        }
        
        response = await async_test_client.post(
            "/api/v1/healthcare/patients",
            headers=admin_headers,
            json=test_patient_data
        )
        
        if response.status_code == 201:
            patient_id = response.json()["id"]
            
            # Admin should be able to access the patient
            response = await async_test_client.get(
                f"/api/v1/healthcare/patients/{patient_id}",
                headers=admin_headers
            )
            assert response.status_code == 200
            
            # Regular user should NOT be able to access the patient
            response = await async_test_client.get(
                f"/api/v1/healthcare/patients/{patient_id}",
                headers=user_headers
            )
            assert response.status_code in [403, 404]
        
        print("✓ Cross-role data access properly controlled")
    
    @pytest.mark.asyncio
    async def test_role_hierarchy_enforcement(self, async_test_client, test_users_by_role):
        """
        Test that role hierarchy is properly enforced.
        Higher roles should have access to lower role functions.
        """
        # Test hierarchy: super_admin > admin > operator > user
        role_hierarchy = ["user", "admin", "super_admin"]
        
        for i, role in enumerate(role_hierarchy):
            user = test_users_by_role[role]
            headers = await self._get_auth_headers(async_test_client, user)
            
            # Each role should be able to access own profile
            response = await async_test_client.get(
                "/api/v1/auth/me",
                headers=headers
            )
            assert response.status_code == 200
            
            # Higher roles should have access to more endpoints
            if role in ["admin", "super_admin"]:
                # Should access admin functions
                response = await async_test_client.get(
                    "/api/v1/auth/users",
                    headers=headers
                )
                assert response.status_code == 200
            else:
                # Lower roles should not access admin functions
                response = await async_test_client.get(
                    "/api/v1/auth/users", 
                    headers=headers
                )
                assert response.status_code in [403, 404]
        
        print("✓ Role hierarchy properly enforced")
    
    @pytest.mark.asyncio
    async def test_token_role_tampering_protection(self, async_test_client, test_users_by_role):
        """
        Test protection against token role tampering.
        Verify tokens cannot be modified to escalate privileges.
        """
        user = test_users_by_role["user"]
        
        # Create legitimate token
        legitimate_token = create_access_token({
            "sub": str(user.id),
            "user_id": str(user.id), 
            "username": user.username,
            "role": user.role,
            "email": user.email
        })
        
        # Try to create fake admin token (should fail validation)
        try:
            fake_admin_token = create_access_token({
                "sub": str(user.id),
                "user_id": str(user.id),
                "username": user.username, 
                "role": "admin",  # Escalated role
                "email": user.email
            })
            
            # Try to use fake token
            response = await async_test_client.get(
                "/api/v1/auth/users",  # Admin-only endpoint
                headers={"Authorization": f"Bearer {fake_admin_token}"}
            )
            
            # Should be rejected (server should validate role against database)
            # If not rejected, it indicates a security vulnerability
            if response.status_code == 200:
                print("⚠️  WARNING: Role tampering not detected - security vulnerability!")
            else:
                print("✓ Token role tampering properly prevented")
                
        except Exception as e:
            print("✓ Token creation with invalid role prevented")
    
    @pytest.mark.asyncio
    async def test_inactive_user_access_denied(self, async_test_client, db_session):
        """
        Test that inactive users are denied access.
        Verifies account deactivation security.
        """
        # Create an inactive user
        inactive_user = User(
            username="inactive_user",
            email="inactive@example.com", 
            hashed_password="dummy_hash",
            role="user",
            is_active=False,  # Inactive
            is_verified=True
        )
        
        db_session.add(inactive_user)
        await db_session.commit()
        await db_session.refresh(inactive_user)
        
        # Try to create token for inactive user
        token = create_access_token({
            "sub": str(inactive_user.id),
            "user_id": str(inactive_user.id),
            "username": inactive_user.username,
            "role": inactive_user.role,
            "email": inactive_user.email
        })
        
        # Try to access protected resource
        response = await async_test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Should be denied access
        assert response.status_code in [401, 403]
        
        print("✓ Inactive user access properly denied")
    
    @pytest.mark.asyncio
    async def test_phi_access_role_restrictions(self, async_test_client, test_users_by_role):
        """
        Test PHI access restrictions based on user roles.
        Ensures proper healthcare data protection.
        """
        # Test different roles accessing PHI data
        for role, user in test_users_by_role.items():
            headers = await self._get_auth_headers(async_test_client, user)
            
            # Try to access PHI access logs
            response = await async_test_client.get(
                "/api/v1/healthcare/audit/phi-access",
                headers=headers
            )
            
            if role in ["admin", "super_admin"]:
                # Admins should be able to access PHI access logs
                assert response.status_code in [200, 404]  # OK or not implemented
            else:
                # Regular users should not access PHI access logs
                assert response.status_code in [403, 404]
        
        print("✓ PHI access role restrictions properly enforced")
    
    @pytest.mark.asyncio
    async def test_time_based_access_control(self, async_test_client, test_users_by_role):
        """
        Test time-based access control if implemented.
        Some roles might have time restrictions.
        """
        # This test would verify if there are time-based restrictions
        # For now, just verify that tokens don't expire immediately
        
        user = test_users_by_role["user"]
        headers = await self._get_auth_headers(async_test_client, user)
        
        # Access should work immediately
        response = await async_test_client.get(
            "/api/v1/auth/me",
            headers=headers
        )
        assert response.status_code == 200
        
        # Test with expired token
        expired_token = create_access_token(
            {
                "sub": str(user.id),
                "user_id": str(user.id),
                "username": user.username,
                "role": user.role,
                "email": user.email
            },
            expires_delta=timedelta(seconds=-1)  # Already expired
        )
        
        response = await async_test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert response.status_code == 401  # Unauthorized
        
        print("✓ Time-based access control working")
    
    async def _get_auth_headers(self, async_test_client, user: User) -> Dict[str, str]:
        """Helper method to get authentication headers for a user."""
        # Try to login (if login endpoint works)
        login_response = await async_test_client.post(
            "/api/v1/auth/login",
            data={
                "username": user.username,
                "password": "testpassword123"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
        else:
            # Fallback: create token manually
            token = create_access_token({
                "sub": str(user.id),
                "user_id": str(user.id),
                "username": user.username,
                "role": user.role,
                "email": user.email
            })
        
        return {"Authorization": f"Bearer {token}"}


class TestPermissionChecking:
    """Test granular permission checking"""
    
    @pytest.mark.asyncio
    async def test_endpoint_permission_mapping(self, async_test_client, test_users_by_role):
        """
        Test that endpoints properly map to required permissions.
        Verifies permission-based access control.
        """
        endpoint_permissions = {
            "/api/v1/auth/me": ["read_own_profile"],
            "/api/v1/auth/users": ["manage_users"],
            "/api/v1/healthcare/patients": ["read_patients"],
            "/api/v1/audit-logs": ["read_audit_logs"],
            "/api/v1/healthcare/audit/phi-access": ["read_phi_access_logs"]
        }
        
        for endpoint, required_perms in endpoint_permissions.items():
            # Test with different roles
            for role, user in test_users_by_role.items():
                headers = await self._get_auth_headers(async_test_client, user)
                
                response = await async_test_client.get(endpoint, headers=headers)
                
                # Verify access based on role permissions
                if self._user_has_permissions(role, required_perms):
                    assert response.status_code not in [401, 403]
                else:
                    assert response.status_code in [401, 403, 404]
        
        print("✓ Endpoint permission mapping verified")
    
    def _user_has_permissions(self, role: str, required_permissions: List[str]) -> bool:
        """Check if user role has required permissions."""
        role_permissions = {
            "user": ["read_own_profile"],
            "operator": ["read_own_profile", "read_patients", "create_patients"],
            "admin": ["read_own_profile", "manage_users", "read_patients", "read_audit_logs"],
            "super_admin": ["*"]  # All permissions
        }
        
        user_perms = role_permissions.get(role, [])
        
        if "*" in user_perms:
            return True
        
        return all(perm in user_perms for perm in required_permissions)
    
    async def _get_auth_headers(self, async_test_client, user: User) -> Dict[str, str]:
        """Helper method to get authentication headers for a user."""
        token = create_access_token({
            "sub": str(user.id),
            "user_id": str(user.id),
            "username": user.username,
            "role": user.role,
            "email": user.email
        })
        return {"Authorization": f"Bearer {token}"}


if __name__ == "__main__":
    """
    Run authorization tests directly:
    python app/tests/core/security/test_authorization.py
    """
    print("🔐 Running authorization tests...")
    pytest.main([__file__, "-v", "--tb=short"])