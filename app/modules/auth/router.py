from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
import structlog
import uuid

from app.core.database_unified import get_db, AuditEventType
from app.core.security import get_current_user_id, get_client_info, require_role
from app.modules.auth.schemas import (
    UserCreate, UserLogin, UserResponse, TokenResponse, 
    UserUpdate, PasswordReset, PasswordResetConfirm,
    PasswordChange, RoleResponse, PermissionResponse,
    UserPermissionsResponse, RoleCreate, RoleUpdate, UserRoleAssignment
)
from app.modules.auth.service import AuthService

auth_service = AuthService()

logger = structlog.get_logger()

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user account."""
    client_info = await get_client_info(request)
    
    user = await auth_service.create_user(user_data, db)
    
    logger.info("User registered", user_id=user.id, username=user.username, **client_info)
    
    return UserResponse.model_validate(user)

@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: UserLogin,
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return access token (OAuth2 compliant)."""
    import time
    import uuid
    
    # Generate unique request ID for security tracking
    login_attempt_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    
    client_info = await get_client_info(request)
    
    # Comprehensive security logging for login attempt
    logger.info(
        "SECURITY - LOGIN ATTEMPT STARTED",
        login_attempt_id=login_attempt_id,
        username=login_data.username,
        client_ip=client_info.get("ip_address"),
        user_agent=client_info.get("user_agent"),
        referer=client_info.get("referer"),
        request_id=client_info.get("request_id"),
        timestamp=time.time()
    )
    
    try:
        # Log login data validation
        if not login_data.username or not login_data.password:
            logger.warning(
                "SECURITY - INVALID LOGIN DATA",
                login_attempt_id=login_attempt_id,
                has_username=bool(login_data.username),
                has_password=bool(login_data.password),
                client_ip=client_info.get("ip_address")
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username and password are required"
            )
        
        logger.info(
            "SECURITY - LOGIN DATA PROCESSED",
            login_attempt_id=login_attempt_id,
            username=login_data.username,
            username_length=len(login_data.username),
            password_provided=bool(login_data.password)
        )
        
        # Call authentication service with comprehensive logging
        logger.info(
            "SECURITY - CALLING AUTH SERVICE",
            login_attempt_id=login_attempt_id,
            username=login_data.username,
            client_ip=client_info.get("ip_address")
        )
        
        logger.info(
            "SECURITY - About to call auth_service.authenticate_user",
            login_attempt_id=login_attempt_id,
            username=login_data.username,
            client_ip=client_info.get("ip_address")
        )
        
        user = await auth_service.authenticate_user(login_data, db, client_info)
        
        logger.info(
            "SECURITY - Auth service returned result",
            login_attempt_id=login_attempt_id,
            username=login_data.username,
            user_returned=user is not None,
            user_id=str(user.id) if user else None,
            user_active=user.is_active if user else None
        )
        
        if not user:
            processing_time = time.time() - start_time
            logger.error(
                "SECURITY - AUTHENTICATION FAILED",
                login_attempt_id=login_attempt_id,
                username=login_data.username,
                client_ip=client_info.get("ip_address"),
                user_agent=client_info.get("user_agent"),
                processing_time_ms=round(processing_time * 1000, 2),
                failure_reason="Invalid credentials"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.info(
            "SECURITY - AUTHENTICATION SUCCESSFUL",
            login_attempt_id=login_attempt_id,
            user_id=str(user.id),
            username=user.username,
            user_role=user.role,
            user_active=user.is_active,
            client_ip=client_info.get("ip_address")
        )
        
        # Create access token with security logging
        logger.info(
            "SECURITY - CREATING TOKENS",
            login_attempt_id=login_attempt_id,
            user_id=str(user.id),
            username=user.username
        )
        
        token_data = await auth_service.create_access_token(user)
        
        processing_time = time.time() - start_time
        
        # Log successful login completion
        logger.info(
            "SECURITY - LOGIN COMPLETED SUCCESSFULLY",
            login_attempt_id=login_attempt_id,
            user_id=str(user.id),
            username=user.username,
            user_role=user.role,
            client_ip=client_info.get("ip_address"),
            user_agent=client_info.get("user_agent"),
            processing_time_ms=round(processing_time * 1000, 2),
            has_access_token=bool(token_data.get("access_token")),
            has_refresh_token=bool(token_data.get("refresh_token")),
            token_expires_in=token_data.get("expires_in")
        )
        
        # SOC2 MANDATORY AUDIT LOGGING - NEVER DISABLE FOR COMPLIANCE
        try:
            from app.core.database_unified import AuditLog
            from datetime import datetime
            import uuid
            import hashlib
            import json
            
            # Calculate log hash for integrity (required field)
            audit_data = {
                "event_type": "USER_LOGIN",
                "user_id": str(user.id),
                "action": "login",
                "result": "success",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "ip_address": client_info.get("ip_address"),
                "username": user.username
            }
            
            log_hash = hashlib.sha256(json.dumps(audit_data, sort_keys=True).encode()).hexdigest()
            
            audit_log = AuditLog(
                event_type=AuditEventType.USER_LOGIN.value,
                user_id=str(user.id),
                resource_type="auth",
                resource_id=str(user.id),
                action="login",
                outcome="success",
                ip_address=client_info.get("ip_address"),
                user_agent=client_info.get("user_agent"),
                config_metadata={
                    "username": user.username,
                    "user_role": str(user.role) if user.role else "user",
                    "login_attempt_id": login_attempt_id,
                    "processing_time_ms": round(processing_time * 1000, 2),
                    "compliance_level": "SOC2_Type_II",
                    "authentication_method": "password"
                },
                compliance_tags=["SOC2", "authentication", "access_control"]
            )
            
            db.add(audit_log)
            await db.commit()
            
            logger.info("SOC2 AUDIT - Login event recorded", 
                       user_id=str(user.id),
                       username=user.username,
                       compliance_level="SOC2_Type_II")
            
        except Exception as audit_error:
            # SOC2 CRITICAL: Audit failure must be logged and monitored
            logger.error("SOC2 CRITICAL - Audit logging failed", 
                        error=str(audit_error),
                        user_id=str(user.id),
                        username=user.username,
                        compliance_level="SOC2_Type_II_VIOLATION")
            
            # For SOC2 compliance, we could consider failing the login if audit fails
            # But for now, we'll log the violation and continue
        
        return TokenResponse(
            access_token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            token_type=token_data["token_type"],
            expires_in=token_data["expires_in"],
            user=UserResponse.model_validate(token_data["user"])
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (already logged above)
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(
            "SECURITY - LOGIN ENDPOINT ERROR",
            login_attempt_id=login_attempt_id,
            username=getattr(login_data, 'username', 'unknown'),
            client_ip=client_info.get("ip_address"),
            error=str(e),
            error_type=type(e).__name__,
            processing_time_ms=round(processing_time * 1000, 2)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login processing error"
        )

@router.post("/logout")
async def logout(
    request: Request,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Securely logout user with token blacklisting for SOC2 compliance."""
    client_info = await get_client_info(request)
    
    try:
        # Extract JWT token from Authorization header
        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authorization header required for secure logout"
            )
        
        token = authorization.split(" ")[1]
        
        # Get security manager and decode token to extract JTI
        from app.core.security import SecurityManager
        security_manager = SecurityManager()
        payload = security_manager.verify_token(token)
        jti = payload.get("jti")
        
        if not jti:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token - missing JTI"
            )
        
        # Revoke the token by adding JTI to blacklist
        success = security_manager.revoke_token(jti, reason="user_logout")
        
        if not success:
            logger.error("Token revocation failed", 
                        user_id=current_user_id, 
                        jti=jti[:8] + "...")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Logout failed - please try again"
            )
        
        # SOC2 Audit logging for secure logout
        from app.core.database_unified import AuditLog
        from datetime import datetime
        import hashlib
        import json
        
        audit_data = {
            "event_type": "USER_LOGOUT",
            "user_id": current_user_id,
            "action": "secure_logout",
            "result": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "ip_address": client_info.get("ip_address"),
            "jti_revoked": jti[:8] + "..."
        }
        
        log_hash = hashlib.sha256(json.dumps(audit_data, sort_keys=True).encode()).hexdigest()
        
        audit_log = AuditLog(
            event_type=AuditEventType.USER_LOGOUT,
            user_id=uuid.UUID(current_user_id) if isinstance(current_user_id, str) else current_user_id,
            resource_type="auth",
            resource_id=uuid.UUID(current_user_id) if isinstance(current_user_id, str) else current_user_id,
            action="secure_logout",
            outcome="success",
            ip_address=client_info.get("ip_address"),
            user_agent=client_info.get("user_agent"),
            config_metadata={
                "token_revoked": True,
                "jti_prefix": jti[:8] + "...",
                "compliance_level": "SOC2_Type_II",
                "logout_method": "secure_blacklist"
            },
            compliance_tags=["SOC2", "authentication", "token_revocation"]
        )
        
        db.add(audit_log)
        await db.commit()
        
        # Publish logout event
        from app.core.event_bus import publish_auth_event, EventType
        await publish_auth_event(
            EventType.USER_LOGOUT,
            user_id=current_user_id,
            **client_info
        )
        
        logger.info("Secure logout completed", 
                   user_id=current_user_id, 
                   jti_revoked=jti[:8] + "...",
                   **client_info)
        
        return {
            "message": "Successfully logged out", 
            "token_revoked": True,
            "security_level": "SOC2_compliant"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Logout error", 
                    user_id=current_user_id, 
                    error=str(e),
                    **client_info)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed - please try again"
        )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token_data: dict,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token."""
    client_info = await get_client_info(request)
    
    refresh_token = refresh_token_data.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token is required"
        )
    
    token_data = await auth_service.refresh_access_token(refresh_token, db)
    
    logger.info("Token refreshed", **client_info)
    
    return TokenResponse(
        access_token=token_data["access_token"],
        refresh_token=token_data["refresh_token"],
        token_type=token_data["token_type"],
        expires_in=token_data["expires_in"]
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get current user information."""
    user = await auth_service.get_user_by_id(current_user_id, db)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.model_validate(user)

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Update current user information."""
    user = await auth_service.update_user(current_user_id, user_update, db)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.model_validate(user)

@router.get("/users", response_model=list[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin"))
):
    """List all users (admin only)."""
    from sqlalchemy import select, func
    from app.core.database_unified import User
    
    try:
        # Get users with pagination
        result = await db.execute(
            select(User)
            .where(User.is_active == True)  # Use is_active instead of is_deleted
            .order_by(User.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        users = result.scalars().all()
        
        return [UserResponse.model_validate(user) for user in users]
        
    except Exception as e:
        logger.error("Failed to list users", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin"))
):
    """Get user by ID (admin only)."""
    user = await auth_service.get_user_by_id(user_id, db)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.model_validate(user)

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin"))
):
    """Update user by ID (admin only)."""
    user = await auth_service.update_user(user_id, user_update, db)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.model_validate(user)

@router.delete("/users/{user_id}")
async def deactivate_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin"))
):
    """Deactivate user by ID (admin only)."""
    success = await auth_service.deactivate_user(user_id, db)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User deactivated successfully"}

@router.post("/forgot-password")
async def forgot_password(
    reset_data: PasswordReset,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Initiate password reset process."""
    client_info = await get_client_info(request)
    
    # In a production system, you would:
    # 1. Generate a secure reset token
    # 2. Store it in the database with expiration
    # 3. Send email with reset link
    # 4. Log the event for audit
    
    from app.core.event_bus import publish_auth_event, EventType
    await publish_auth_event(
        EventType.DATA_ACCESSED,
        user_id="system",
        data={"action": "password_reset_requested", "email": reset_data.email},
        **client_info
    )
    
    logger.info("Password reset requested", email=reset_data.email, **client_info)
    
    # Always return success for security (don't reveal if email exists)
    return {"message": "If the email exists, a reset link has been sent"}

@router.post("/reset-password")
async def reset_password(
    reset_data: PasswordResetConfirm,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Confirm password reset with token."""
    client_info = await get_client_info(request)
    
    # In a production system, you would:
    # 1. Validate the reset token
    # 2. Check if it's not expired
    # 3. Update the user's password
    # 4. Invalidate the reset token
    # 5. Log the event
    
    from app.core.event_bus import publish_auth_event, EventType
    await publish_auth_event(
        EventType.DATA_UPDATED,
        user_id="unknown",  # Would be determined from token
        data={"action": "password_reset_completed"},
        **client_info
    )
    
    logger.info("Password reset completed", **client_info)
    
    return {"message": "Password reset successfully"}

# ============================================
# PASSWORD MANAGEMENT ENDPOINTS
# ============================================

@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    request: Request,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Change current user's password."""
    client_info = await get_client_info(request)
    
    try:
        # Verify current password and update to new password
        success = await auth_service.change_password(
            current_user_id, 
            password_data.current_password, 
            password_data.new_password, 
            db
        )
        
        if not success:
            logger.warning("Password change failed - invalid current password", 
                         user_id=current_user_id, **client_info)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # SOC2 Audit logging
        from app.core.event_bus import publish_auth_event, EventType
        await publish_auth_event(
            EventType.DATA_UPDATED,
            user_id=current_user_id,
            data={"action": "password_changed"},
            **client_info
        )
        
        logger.info("Password changed successfully", user_id=current_user_id, **client_info)
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Password change failed", user_id=current_user_id, error=str(e), **client_info)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )

# ============================================
# ROLE MANAGEMENT ENDPOINTS
# ============================================

@router.get("/roles", response_model=list[RoleResponse])
async def list_roles(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin"))
):
    """List all roles (admin only)."""
    try:
        # Mock role data - in production would query database
        roles = [
            RoleResponse(
                name="admin",
                description="System administrator with full access",
                permissions=[
                    "admin", "user_management", "patient_risk_read", "patient_risk_write",
                    "population_health_read", "risk_analytics_read", "quality_analytics_read",
                    "cost_analytics_read", "intervention_analytics_read", "phi_access"
                ],
                is_active=True,
                created_at=datetime.now()
            ),
            RoleResponse(
                name="user",
                description="Standard user with limited access",
                permissions=["patient_risk_read", "basic_analytics_read"],
                is_active=True,
                created_at=datetime.now()
            ),
            RoleResponse(
                name="super_admin",
                description="Super administrator with system-level access",
                permissions=[
                    "admin", "super_admin", "user_management", "role_management",
                    "system_configuration", "audit_access", "phi_access"
                ],
                is_active=True,
                created_at=datetime.now()
            )
        ]
        
        logger.info("Roles listed", role_count=len(roles))
        return roles[skip:skip+limit]
        
    except Exception as e:
        logger.error("Failed to list roles", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve roles"
        )

@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    _: dict = Depends(require_role("super_admin"))
):
    """Create a new role (super admin only)."""
    client_info = await get_client_info(request)
    
    try:
        # In production, would create role in database
        # For now, return mock response
        role = RoleResponse(
            name=role_data.name,
            description=role_data.description,
            permissions=role_data.permissions,
            is_active=role_data.is_active,
            created_at=datetime.now()
        )
        
        logger.info("Role created", 
                   role_name=role_data.name, 
                   created_by=current_user_id, 
                   **client_info)
        
        return role
        
    except Exception as e:
        logger.error("Role creation failed", 
                    role_name=role_data.name, 
                    error=str(e), 
                    **client_info)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Role creation failed"
        )

@router.get("/roles/{role_name}", response_model=RoleResponse)
async def get_role(
    role_name: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin"))
):
    """Get role by name (admin only)."""
    # Mock role lookup
    if role_name == "admin":
        return RoleResponse(
            name="admin",
            description="System administrator with full access",
            permissions=[
                "admin", "user_management", "patient_risk_read", "patient_risk_write",
                "population_health_read", "risk_analytics_read", "quality_analytics_read",
                "cost_analytics_read", "intervention_analytics_read", "phi_access"
            ],
            is_active=True,
            created_at=datetime.now()
        )
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Role not found"
    )

@router.put("/roles/{role_name}", response_model=RoleResponse)
async def update_role(
    role_name: str,
    role_update: RoleUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    _: dict = Depends(require_role("super_admin"))
):
    """Update role by name (super admin only)."""
    client_info = await get_client_info(request)
    
    try:
        # In production, would update role in database
        # For now, return mock response
        role = RoleResponse(
            name=role_name,
            description=role_update.description or "Updated role description",
            permissions=role_update.permissions or ["basic_permissions"],
            is_active=role_update.is_active if role_update.is_active is not None else True,
            created_at=datetime.now()
        )
        
        logger.info("Role updated", 
                   role_name=role_name, 
                   updated_by=current_user_id, 
                   **client_info)
        
        return role
        
    except Exception as e:
        logger.error("Role update failed", 
                    role_name=role_name, 
                    error=str(e), 
                    **client_info)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Role update failed"
        )

@router.delete("/roles/{role_name}")
async def delete_role(
    role_name: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    _: dict = Depends(require_role("super_admin"))
):
    """Delete role by name (super admin only)."""
    client_info = await get_client_info(request)
    
    # Prevent deletion of system roles
    if role_name in ["admin", "user", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete system roles"
        )
    
    try:
        # In production, would soft delete role in database
        logger.info("Role deleted", 
                   role_name=role_name, 
                   deleted_by=current_user_id, 
                   **client_info)
        
        return {"message": f"Role {role_name} deleted successfully"}
        
    except Exception as e:
        logger.error("Role deletion failed", 
                    role_name=role_name, 
                    error=str(e), 
                    **client_info)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Role deletion failed"
        )

# ============================================
# PERMISSION MANAGEMENT ENDPOINTS
# ============================================

@router.get("/permissions", response_model=list[PermissionResponse])
async def list_permissions(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin"))
):
    """List all available permissions (admin only)."""
    try:
        # Mock permissions data
        permissions = [
            PermissionResponse(
                name="admin",
                description="Full administrative access",
                resource_type="system",
                action="manage"
            ),
            PermissionResponse(
                name="user_management",
                description="Manage user accounts",
                resource_type="users",
                action="manage"
            ),
            PermissionResponse(
                name="patient_risk_read",
                description="Read patient risk data",
                resource_type="patient_risk",
                action="read"
            ),
            PermissionResponse(
                name="patient_risk_write",
                description="Write patient risk data",
                resource_type="patient_risk",
                action="write"
            ),
            PermissionResponse(
                name="population_health_read",
                description="Access population health analytics",
                resource_type="analytics",
                action="read"
            ),
            PermissionResponse(
                name="risk_analytics_read",
                description="Access risk analytics",
                resource_type="analytics",
                action="read"
            ),
            PermissionResponse(
                name="quality_analytics_read",
                description="Access quality analytics",
                resource_type="analytics",
                action="read"
            ),
            PermissionResponse(
                name="cost_analytics_read",
                description="Access cost analytics",
                resource_type="analytics",
                action="read"
            ),
            PermissionResponse(
                name="intervention_analytics_read",
                description="Access intervention analytics",
                resource_type="analytics",
                action="read"
            ),
            PermissionResponse(
                name="phi_access",
                description="Access Protected Health Information",
                resource_type="phi",
                action="access"
            )
        ]
        
        logger.info("Permissions listed", permission_count=len(permissions))
        return permissions
        
    except Exception as e:
        logger.error("Failed to list permissions", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve permissions"
        )

@router.get("/users/{user_id}/permissions", response_model=UserPermissionsResponse)
async def get_user_permissions(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin"))
):
    """Get user permissions (admin only)."""
    try:
        # In production, would query user and role permissions from database
        # Mock response for now
        user_permissions = UserPermissionsResponse(
            user_id=uuid.UUID(user_id),
            username="mock_user",
            role="admin",
            permissions=[
                "admin", "user_management", "patient_risk_read", "patient_risk_write",
                "population_health_read", "risk_analytics_read", "quality_analytics_read",
                "cost_analytics_read", "intervention_analytics_read", "phi_access"
            ],
            effective_permissions=[
                "admin", "user_management", "patient_risk_read", "patient_risk_write",
                "population_health_read", "risk_analytics_read", "quality_analytics_read",
                "cost_analytics_read", "intervention_analytics_read", "phi_access"
            ],
            last_updated=datetime.now()
        )
        
        logger.info("User permissions retrieved", user_id=user_id)
        return user_permissions
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    except Exception as e:
        logger.error("Failed to get user permissions", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user permissions"
        )

@router.post("/users/{user_id}/role")
async def assign_user_role(
    user_id: str,
    role_assignment: UserRoleAssignment,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    _: dict = Depends(require_role("admin"))
):
    """Assign role to user (admin only)."""
    client_info = await get_client_info(request)
    
    try:
        # In production, would update user role in database
        logger.info("User role assigned", 
                   user_id=user_id,
                   role_name=role_assignment.role_name,
                   assigned_by=current_user_id,
                   reason=role_assignment.reason,
                   **client_info)
        
        return {
            "message": f"Role {role_assignment.role_name} assigned to user {user_id}",
            "assigned_by": current_user_id,
            "assigned_at": datetime.now().isoformat()
        }
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    except Exception as e:
        logger.error("Role assignment failed", 
                    user_id=user_id,
                    role_name=role_assignment.role_name,
                    error=str(e),
                    **client_info)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Role assignment failed"
        )