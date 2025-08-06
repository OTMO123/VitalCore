from datetime import datetime, timedelta, timezone
from typing import Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException, status
import structlog
import uuid

from app.core.database_unified import User
from app.core.security import security_manager
from app.core.event_bus import EventType, publish_auth_event
from app.modules.auth.schemas import UserCreate, UserLogin, UserUpdate

logger = structlog.get_logger()

class AuthService:
    """Authentication service for user management and JWT tokens."""
    
    def __init__(self):
        self.security = security_manager
    
    async def create_user(self, user_data: UserCreate, db: AsyncSession) -> User:
        """Create a new user account."""
        try:
            # Check if user already exists
            existing_user = await self.get_user_by_username(user_data.username.lower(), db)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already registered"
                )
            
            existing_email = await self.get_user_by_email(user_data.email.lower(), db)
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            
            # Create new user
            hashed_password = self.security.hash_password(user_data.password)
            
            user = User(
                username=user_data.username.lower(),
                email=user_data.email.lower(),
                password_hash=hashed_password,
                role=user_data.role,
                is_active=user_data.is_active if user_data.is_active is not None else True,
                email_verified=user_data.email_verified if user_data.email_verified is not None else False
            )
            
            db.add(user)
            await db.commit()
            await db.refresh(user)
            
            # Publish user creation event
            await publish_auth_event(
                EventType.USER_LOGIN_SUCCESS,
                user_id=str(user.id),
                data={"action": "user_created", "username": user.username, "role": user.role}
            )
            
            logger.info("User created successfully", user_id=user.id, username=user.username)
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to create user", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user account"
            )
    
    async def authenticate_user(self, login_data: UserLogin, db: AsyncSession, client_info: dict) -> Optional[User]:
        """Authenticate user credentials with comprehensive security logging."""
        import time
        import uuid
        
        auth_attempt_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        logger.info(
            "AUTH SERVICE - AUTHENTICATION STARTED",
            auth_attempt_id=auth_attempt_id,
            username=login_data.username,
            client_ip=client_info.get("ip_address"),
            user_agent=client_info.get("user_agent"),
            timestamp=time.time()
        )
        
        try:
            # Log database lookup attempt
            logger.info(
                "AUTH SERVICE - USER LOOKUP",
                auth_attempt_id=auth_attempt_id,
                username=login_data.username,
                lookup_method="username_first"
            )
            
            # Find user by username or email
            user = await self.get_user_by_username(login_data.username, db)
            if not user:
                logger.info(
                    "AUTH SERVICE - FALLBACK EMAIL LOOKUP",
                    auth_attempt_id=auth_attempt_id,
                    username=login_data.username,
                    lookup_method="email_fallback"
                )
                user = await self.get_user_by_email(login_data.username, db)
            
            if not user:
                processing_time = time.time() - start_time
                logger.warning(
                    "AUTH SERVICE - USER NOT FOUND",
                    auth_attempt_id=auth_attempt_id,
                    username=login_data.username,
                    client_ip=client_info.get("ip_address"),
                    processing_time_ms=round(processing_time * 1000, 2)
                )
                await publish_auth_event(
                    EventType.USER_LOGIN_FAILURE,
                    user_id="unknown",
                    outcome="failure",
                    data={"reason": "user_not_found", "username": login_data.username},
                    **client_info
                )
                return None
            
            logger.info(
                "AUTH SERVICE - USER FOUND",
                auth_attempt_id=auth_attempt_id,
                user_id=str(user.id),
                username=user.username,
                user_role=user.role,
                user_active=user.is_active,
                email_verified=user.email_verified,
                failed_attempts=user.failed_login_attempts,
                locked_until=user.locked_until.isoformat() if user.locked_until else None
            )
            
            # Check if user is locked
            if user.locked_until and user.locked_until > datetime.now(timezone.utc).replace(tzinfo=None):
                processing_time = time.time() - start_time
                logger.warning(
                    "AUTH SERVICE - ACCOUNT LOCKED",
                    auth_attempt_id=auth_attempt_id,
                    user_id=str(user.id),
                    username=user.username,
                    locked_until=user.locked_until.isoformat(),
                    client_ip=client_info.get("ip_address"),
                    processing_time_ms=round(processing_time * 1000, 2)
                )
                await publish_auth_event(
                    EventType.USER_LOGIN_FAILURE,
                    user_id=str(user.id),
                    outcome="failure",
                    data={"reason": "account_locked", "locked_until": user.locked_until.isoformat()},
                    **client_info
                )
                return None
            
            # Log password verification attempt
            logger.info(
                "AUTH SERVICE - VERIFYING PASSWORD",
                auth_attempt_id=auth_attempt_id,
                user_id=str(user.id),
                username=user.username,
                failed_attempts_before=user.failed_login_attempts
            )
            
            # Verify password with enhanced logging
            logger.info(
                "AUTH_SERVICE - Starting password verification",
                auth_attempt_id=auth_attempt_id,
                user_id=str(user.id),
                username=user.username,
                password_provided=bool(login_data.password),
                password_hash_exists=bool(user.password_hash),
                password_hash_format=user.password_hash[:10] + "..." if user.password_hash else None
            )
            
            password_valid = self.security.verify_password(login_data.password, user.password_hash)
            
            logger.info(
                "AUTH_SERVICE - Password verification result",
                auth_attempt_id=auth_attempt_id,
                user_id=str(user.id),
                username=user.username,
                password_valid=password_valid
            )
            
            if not password_valid:
                # Increment failed attempts
                user.failed_login_attempts += 1
                
                # Lock account after 5 failed attempts
                will_lock = user.failed_login_attempts >= 5
                if will_lock:
                    user.locked_until = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=30)
                
                await db.commit()
                
                processing_time = time.time() - start_time
                logger.warning(
                    "AUTH SERVICE - INVALID PASSWORD",
                    auth_attempt_id=auth_attempt_id,
                    user_id=str(user.id),
                    username=user.username,
                    failed_attempts=user.failed_login_attempts,
                    account_locked=will_lock,
                    locked_until=user.locked_until.isoformat() if user.locked_until else None,
                    client_ip=client_info.get("ip_address"),
                    processing_time_ms=round(processing_time * 1000, 2)
                )
                
                await publish_auth_event(
                    EventType.USER_LOGIN_FAILURE,
                    user_id=str(user.id),
                    outcome="failure",
                    data={
                        "reason": "invalid_password",
                        "failed_attempts": user.failed_login_attempts,
                        "locked": user.locked_until is not None
                    },
                    **client_info
                )
                return None
            
            # Check if user is active
            if not user.is_active:
                processing_time = time.time() - start_time
                logger.warning(
                    "AUTH SERVICE - ACCOUNT INACTIVE",
                    auth_attempt_id=auth_attempt_id,
                    user_id=str(user.id),
                    username=user.username,
                    client_ip=client_info.get("ip_address"),
                    processing_time_ms=round(processing_time * 1000, 2)
                )
                await publish_auth_event(
                    EventType.USER_LOGIN_FAILURE,
                    user_id=str(user.id),
                    outcome="failure",
                    data={"reason": "account_inactive"},
                    **client_info
                )
                return None
            
            # Successful login - reset failed attempts
            logger.info(
                "AUTH SERVICE - UPDATING USER LOGIN STATE",
                auth_attempt_id=auth_attempt_id,
                user_id=str(user.id),
                username=user.username,
                resetting_failed_attempts=user.failed_login_attempts > 0
            )
            
            user.failed_login_attempts = 0
            user.locked_until = None
            user.last_login_at = datetime.now(timezone.utc).replace(tzinfo=None)
            await db.commit()
            
            processing_time = time.time() - start_time
            
            await publish_auth_event(
                EventType.USER_LOGIN_SUCCESS,
                user_id=str(user.id),
                data={"username": user.username, "role": user.role},
                **client_info
            )
            
            logger.info(
                "AUTH SERVICE - AUTHENTICATION SUCCESSFUL",
                auth_attempt_id=auth_attempt_id,
                user_id=str(user.id),
                username=user.username,
                user_role=user.role,
                client_ip=client_info.get("ip_address"),
                processing_time_ms=round(processing_time * 1000, 2)
            )
            return user
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(
                "AUTH SERVICE - CRITICAL ERROR",
                auth_attempt_id=auth_attempt_id,
                username=login_data.username,
                client_ip=client_info.get("ip_address"),
                error=str(e),
                error_type=type(e).__name__,
                processing_time_ms=round(processing_time * 1000, 2)
            )
            await publish_auth_event(
                EventType.ERROR_OCCURRED,
                user_id="unknown",
                outcome="error",
                data={"error": str(e), "action": "authenticate_user", "auth_attempt_id": auth_attempt_id}
            )
            return None
    
    async def create_access_token(self, user: User) -> dict:
        """Create access token for authenticated user."""
        try:
            token_data = {
                "user_id": str(user.id),
                "username": user.username,
                "role": str(user.role) if user.role else "user",
                "email": user.email
            }
            
            access_token = self.security.create_access_token(token_data)
            refresh_token = self.security.create_refresh_token(token_data)
            
            await publish_auth_event(
                EventType.TOKEN_CREATED,
                user_id=str(user.id),
                data={"token_type": "access", "expires_in": self.security.settings.ACCESS_TOKEN_EXPIRE_MINUTES}
            )
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": self.security.settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "user": user
            }
            
        except Exception as e:
            logger.error("Failed to create access token", error=str(e), user_id=user.id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create access token"
            )
    
    async def get_user_by_id(self, user_id: Union[int, str, uuid.UUID], db: AsyncSession) -> Optional[User]:
        """Get user by ID."""
        try:
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("Failed to get user by ID", error=str(e), user_id=user_id)
            return None
    
    async def get_user_by_username(self, username: str, db: AsyncSession) -> Optional[User]:
        """Get user by username."""
        import time
        start_time = time.time()
        
        try:
            logger.info("AUTH_SERVICE - Starting user lookup by username", 
                       username=username, 
                       lookup_method="username")
            
            result = await db.execute(
                select(User).where(User.username == username.lower())
            )
            user = result.scalar_one_or_none()
            
            lookup_time = time.time() - start_time
            
            if user:
                logger.info("AUTH_SERVICE - User found by username", 
                           username=username,
                           user_id=str(user.id),
                           user_role=user.role,
                           is_active=user.is_active,
                           email_verified=user.email_verified,
                           failed_attempts=user.failed_login_attempts,
                           lookup_time_ms=round(lookup_time * 1000, 2))
            else:
                logger.warning("AUTH_SERVICE - User NOT found by username", 
                              username=username,
                              lookup_time_ms=round(lookup_time * 1000, 2))
            
            return user
            
        except Exception as e:
            error_time = time.time() - start_time
            logger.error("AUTH_SERVICE - Failed to get user by username", 
                        error=str(e), 
                        error_type=type(e).__name__,
                        username=username,
                        lookup_time_ms=round(error_time * 1000, 2))
            return None
    
    async def get_user_by_email(self, email: str, db: AsyncSession) -> Optional[User]:
        """Get user by email."""
        try:
            result = await db.execute(
                select(User).where(User.email == email.lower())
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("Failed to get user by email", error=str(e), email=email)
            return None
    
    async def update_user(self, user_id: Union[int, str, uuid.UUID], user_update: UserUpdate, db: AsyncSession) -> Optional[User]:
        """Update user information."""
        try:
            user = await self.get_user_by_id(user_id, db)
            if not user:
                return None
            
            update_data = user_update.dict(exclude_unset=True)
            
            if update_data:
                await db.execute(
                    update(User)
                    .where(User.id == user_id)
                    .values(**update_data, updated_at=datetime.utcnow())
                )
                await db.commit()
                await db.refresh(user)
                
                await publish_auth_event(
                    EventType.DATA_UPDATED,
                    user_id=str(user.id),
                    data={"updated_fields": list(update_data.keys())}
                )
            
            return user
            
        except Exception as e:
            logger.error("Failed to update user", error=str(e), user_id=user_id)
            return None
    
    async def deactivate_user(self, user_id: Union[int, str, uuid.UUID], db: AsyncSession) -> bool:
        """Deactivate user account."""
        try:
            result = await db.execute(
                update(User)
                .where(User.id == user_id)
                .values(is_active=False, updated_at=datetime.utcnow())
            )
            
            if result.rowcount > 0:
                await db.commit()
                await publish_auth_event(
                    EventType.DATA_UPDATED,
                    user_id=str(user_id),
                    data={"action": "user_deactivated"}
                )
                return True
            
            return False
            
        except Exception as e:
            logger.error("Failed to deactivate user", error=str(e), user_id=user_id)
            return False
    
    async def refresh_access_token(self, refresh_token: str, db: AsyncSession) -> dict:
        """Refresh access token using valid refresh token."""
        try:
            # Verify refresh token
            payload = self.security.verify_token(refresh_token)
            
            # Check token type
            if payload.get("token_type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            # Get user
            user_id = payload.get("sub")
            user = await self.get_user_by_id(user_id, db)
            
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive"
                )
            
            # Create new tokens
            token_data = {
                "user_id": str(user.id),
                "username": user.username,
                "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
                "email": user.email
            }
            
            new_access_token = self.security.create_access_token(token_data)
            new_refresh_token = self.security.create_refresh_token(token_data)
            
            # Revoke old refresh token
            old_jti = payload.get("jti")
            if old_jti:
                self.security.revoke_token(old_jti, "token_refresh")
            
            await publish_auth_event(
                EventType.TOKEN_CREATED,
                user_id=str(user.id),
                data={"action": "token_refreshed"}
            )
            
            return {
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer",
                "expires_in": self.security.settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to refresh token", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not refresh token"
            )
    
    async def change_password(self, user_id: Union[int, str, uuid.UUID], current_password: str, new_password: str, db: AsyncSession) -> bool:
        """Change user password after verifying current password."""
        try:
            # Get user
            user = await self.get_user_by_id(user_id, db)
            if not user:
                logger.warning("Password change attempted for non-existent user", user_id=user_id)
                return False
            
            # Verify current password
            if not self.security.verify_password(current_password, user.password_hash):
                logger.warning("Password change failed - incorrect current password", 
                             user_id=user_id, username=user.username)
                
                await publish_auth_event(
                    EventType.USER_LOGIN_FAILURE,
                    user_id=str(user.id),
                    outcome="failure",
                    data={"action": "password_change_failed", "reason": "incorrect_current_password"}
                )
                return False
            
            # Update password
            new_password_hash = self.security.hash_password(new_password)
            await db.execute(
                update(User)
                .where(User.id == user_id)
                .values(password_hash=new_password_hash, updated_at=datetime.utcnow())
            )
            await db.commit()
            
            # Log successful password change
            await publish_auth_event(
                EventType.DATA_UPDATED,
                user_id=str(user.id),
                data={"action": "password_changed", "username": user.username}
            )
            
            logger.info("Password changed successfully", user_id=user_id, username=user.username)
            return True
            
        except Exception as e:
            logger.error("Failed to change password", error=str(e), user_id=user_id)
            return False

# Global service instance
auth_service = AuthService()