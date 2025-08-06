"""
Core authentication utilities for FastAPI dependencies.
Provides get_current_user and require_roles functions for the clinical workflows module.
"""

from typing import List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.database_unified import get_db, User
from app.core.security import security_manager

logger = structlog.get_logger()
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verify and decode JWT token
        payload = security_manager.verify_token(credentials.credentials)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
    except Exception as e:
        logger.warning("Token verification failed", error=str(e))
        raise credentials_exception
    
    # Get user from database
    try:
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if user is None:
            raise credentials_exception
            
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive",
                headers={"WWW-Authenticate": "Bearer"}
            )
            
        return user
        
    except Exception as e:
        logger.error("Database error during user lookup", error=str(e))
        raise credentials_exception

def require_roles(allowed_roles: List[str]):
    """
    Dependency factory that requires user to have one of the specified roles.
    
    Args:
        allowed_roles: List of role names that are allowed access
        
    Returns:
        FastAPI dependency function
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        """Check if current user has required role."""
        user_roles = []
        
        # Handle both single role and multiple roles
        if hasattr(current_user, 'roles') and current_user.roles:
            # If user has multiple roles (relationship)
            user_roles = [role.name for role in current_user.roles]
        elif hasattr(current_user, 'role') and current_user.role:
            # If user has single role (string field)
            user_roles = [current_user.role]
        
        # Check if user has any of the allowed roles
        if not any(role in allowed_roles for role in user_roles):
            logger.warning(
                "Access denied - insufficient permissions",
                user_id=str(current_user.id),
                user_roles=user_roles,
                required_roles=allowed_roles
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        logger.info(
            "Access granted",
            user_id=str(current_user.id),
            user_roles=user_roles,
            required_roles=allowed_roles
        )
        
        return current_user
    
    return role_checker

# Convenience functions for common role requirements
def require_physician(current_user: User = Depends(require_roles(["physician", "admin"]))) -> User:
    """Require physician or admin role."""
    return current_user

def require_nurse(current_user: User = Depends(require_roles(["nurse", "physician", "admin"]))) -> User:
    """Require nurse, physician, or admin role."""
    return current_user

def require_admin(current_user: User = Depends(require_roles(["admin"]))) -> User:
    """Require admin role."""
    return current_user

def require_clinical_staff(current_user: User = Depends(require_roles(["physician", "nurse", "clinical_admin", "admin"]))) -> User:
    """Require any clinical staff role."""
    return current_user

def require_permissions(permissions: List[str]):
    """
    Dependency factory that requires user to have specified permissions.
    
    Args:
        permissions: List of permission names that are required
        
    Returns:
        FastAPI dependency function
    """
    def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        """Check if current user has required permissions."""
        user_permissions = []
        
        # Handle permissions based on roles
        if hasattr(current_user, 'roles') and current_user.roles:
            # If user has multiple roles (relationship)
            for role in current_user.roles:
                if hasattr(role, 'permissions'):
                    user_permissions.extend([perm.name for perm in role.permissions])
        elif hasattr(current_user, 'role') and current_user.role:
            # Basic role-based permissions mapping
            role_permissions = {
                'admin': ['read', 'write', 'delete', 'create', 'update'],
                'physician': ['read', 'write', 'create', 'update'],
                'nurse': ['read', 'write', 'update'],
                'user': ['read']
            }
            user_permissions = role_permissions.get(current_user.role, [])
        
        # Check if user has all required permissions
        missing_permissions = [perm for perm in permissions if perm not in user_permissions]
        if missing_permissions:
            logger.warning(
                "Access denied - missing permissions",
                user_id=str(current_user.id),
                user_permissions=user_permissions,
                required_permissions=permissions,
                missing_permissions=missing_permissions
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Access denied. Missing permissions: {', '.join(missing_permissions)}",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        logger.info(
            "Access granted with permissions",
            user_id=str(current_user.id),
            user_permissions=user_permissions,
            required_permissions=permissions
        )
        
        return current_user
    
    return permission_checker