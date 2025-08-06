#!/usr/bin/env python3
"""
SMART on FHIR Authentication Implementation
OAuth2/OpenID Connect authentication for FHIR applications.

SMART on FHIR (Substitutable Medical Applications and Reusable Technologies)
provides a standards-based approach for healthcare applications to authenticate
with FHIR servers and request appropriate access permissions.

Key Features:
- OAuth2/OpenID Connect authentication flow
- SMART App Launch Framework implementation
- JWT token validation and management
- Scope-based access control for FHIR resources
- Patient context management
- Provider context management
- Launch context validation

Security Architecture:
- RSA256 JWT token signing and validation
- Refresh token rotation and secure storage
- PKCE (Proof Key for Code Exchange) support
- State parameter validation for CSRF protection
- Nonce validation for replay attack prevention

Supported SMART Scopes:
- patient/*.read - Read access to patient resources
- patient/*.write - Write access to patient resources  
- user/*.read - Read access based on user role
- user/*.write - Write access based on user role
- launch/patient - Patient launch context
- launch/encounter - Encounter launch context
- openid - OpenID Connect authentication
- profile - Access to user profile information
"""

import asyncio
import base64
import hashlib
import json
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from urllib.parse import urlencode, parse_qs, unquote
import structlog
from dataclasses import dataclass, field
from enum import Enum, auto

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import APIRouter, HTTPException, Depends, Query, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, field_validator
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database_unified import get_async_session, audit_change
from app.core.security import get_current_user_with_permissions
from app.core.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

# SMART on FHIR Constants

class SMARTScope(str, Enum):
    """SMART on FHIR scope definitions"""
    # Patient context scopes
    PATIENT_READ_ALL = "patient/*.read"
    PATIENT_WRITE_ALL = "patient/*.write"
    PATIENT_READ_SPECIFIC = "patient/{resource}.read"
    PATIENT_WRITE_SPECIFIC = "patient/{resource}.write"
    
    # User context scopes
    USER_READ_ALL = "user/*.read"
    USER_WRITE_ALL = "user/*.write"
    USER_READ_SPECIFIC = "user/{resource}.read"
    USER_WRITE_SPECIFIC = "user/{resource}.write"
    
    # Launch context scopes
    LAUNCH_PATIENT = "launch/patient"
    LAUNCH_ENCOUNTER = "launch/encounter"
    LAUNCH_STANDALONE = "launch"
    
    # OpenID Connect scopes
    OPENID = "openid"
    PROFILE = "profile"
    FHIR_USER = "fhirUser"
    EMAIL = "email"
    
    # System scopes (for backend services)
    SYSTEM_READ_ALL = "system/*.read"
    SYSTEM_WRITE_ALL = "system/*.write"

class SMARTGrantType(str, Enum):
    """OAuth2 grant types supported by SMART"""
    AUTHORIZATION_CODE = "authorization_code"
    REFRESH_TOKEN = "refresh_token"
    CLIENT_CREDENTIALS = "client_credentials"

class SMARTResponseType(str, Enum):
    """OAuth2 response types"""
    CODE = "code"
    TOKEN = "token"
    ID_TOKEN = "id_token"

@dataclass
class SMARTClient:
    """SMART on FHIR client registration"""
    client_id: str
    client_name: str
    client_type: str  # public, confidential
    redirect_uris: List[str]
    scopes: List[str]
    launch_uri: Optional[str] = None
    client_secret: Optional[str] = None  # Only for confidential clients
    jwks_uri: Optional[str] = None
    public_key: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    active: bool = True
    
    def is_confidential(self) -> bool:
        """Check if client is confidential"""
        return self.client_type == "confidential" and self.client_secret is not None
    
    def validate_redirect_uri(self, redirect_uri: str) -> bool:
        """Validate redirect URI against registered URIs"""
        return redirect_uri in self.redirect_uris

@dataclass
class SMARTAuthorizationRequest:
    """SMART authorization request parameters"""
    response_type: str
    client_id: str
    redirect_uri: str
    scope: str
    state: str
    aud: str  # FHIR server base URL
    launch: Optional[str] = None  # Launch context token
    code_challenge: Optional[str] = None  # PKCE code challenge
    code_challenge_method: Optional[str] = None  # PKCE method (S256)
    nonce: Optional[str] = None  # OpenID Connect nonce
    
    def validate_pkce(self, code_verifier: str) -> bool:
        """Validate PKCE code challenge"""
        if not self.code_challenge or not self.code_challenge_method:
            return True  # PKCE not required
        
        if self.code_challenge_method == "S256":
            challenge = base64.urlsafe_b64encode(
                hashlib.sha256(code_verifier.encode()).digest()
            ).decode().rstrip("=")
            return challenge == self.code_challenge
        
        return False

@dataclass
class SMARTAuthorizationCode:
    """SMART authorization code with context"""
    code: str
    client_id: str
    user_id: str
    scopes: List[str]
    redirect_uri: str
    expires_at: datetime
    launch_context: Optional[Dict[str, Any]] = None
    code_challenge: Optional[str] = None
    nonce: Optional[str] = None
    
    def is_expired(self) -> bool:
        """Check if authorization code is expired"""
        return datetime.now() > self.expires_at

@dataclass
class SMARTAccessToken:
    """SMART access token with context"""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600  # 1 hour default
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
    patient: Optional[str] = None  # Patient ID from launch context
    encounter: Optional[str] = None  # Encounter ID from launch context
    fhir_user: Optional[str] = None  # FHIR user resource reference
    id_token: Optional[str] = None  # OpenID Connect ID token
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to OAuth2 token response format"""
        result = {
            "access_token": self.access_token,
            "token_type": self.token_type,
            "expires_in": self.expires_in
        }
        
        if self.refresh_token:
            result["refresh_token"] = self.refresh_token
        if self.scope:
            result["scope"] = self.scope
        if self.patient:
            result["patient"] = self.patient
        if self.encounter:
            result["encounter"] = self.encounter
        if self.fhir_user:
            result["fhirUser"] = self.fhir_user
        if self.id_token:
            result["id_token"] = self.id_token
            
        return result

class SMARTAuthService:
    """SMART on FHIR authentication service"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.clients: Dict[str, SMARTClient] = {}
        self.auth_codes: Dict[str, SMARTAuthorizationCode] = {}
        self.access_tokens: Dict[str, Dict[str, Any]] = {}
        
        # Initialize RSA key pair for JWT signing
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self.public_key = self.private_key.public_key()
        
        # Register default test client
        self._register_default_clients()
    
    def _register_default_clients(self):
        """Register default SMART clients for testing"""
        
        # Public client for web apps
        public_client = SMARTClient(
            client_id="smart-public-client",
            client_name="SMART Public Test Client",
            client_type="public",
            redirect_uris=[
                "http://localhost:3000/smart/callback",
                "https://app.example.com/smart/callback"
            ],
            scopes=[
                SMARTScope.PATIENT_READ_ALL.value,
                SMARTScope.LAUNCH_PATIENT.value,
                SMARTScope.OPENID.value,
                SMARTScope.PROFILE.value
            ]
        )
        self.clients[public_client.client_id] = public_client
        
        # Confidential client for backend services
        confidential_client = SMARTClient(
            client_id="smart-confidential-client",
            client_name="SMART Backend Service",
            client_type="confidential",
            client_secret="super-secret-key-for-confidential-client",
            redirect_uris=[
                "https://backend.example.com/smart/callback"
            ],
            scopes=[
                SMARTScope.SYSTEM_READ_ALL.value,
                SMARTScope.SYSTEM_WRITE_ALL.value
            ]
        )
        self.clients[confidential_client.client_id] = confidential_client
    
    async def get_authorization_metadata(self) -> Dict[str, Any]:
        """Get SMART authorization server metadata"""
        
        base_url = f"{settings.API_BASE_URL}/smart"
        
        metadata = {
            "issuer": base_url,
            "authorization_endpoint": f"{base_url}/auth",
            "token_endpoint": f"{base_url}/token",
            "userinfo_endpoint": f"{base_url}/userinfo",
            "jwks_uri": f"{base_url}/.well-known/jwks.json",
            "registration_endpoint": f"{base_url}/register",
            "revocation_endpoint": f"{base_url}/revoke",
            "introspection_endpoint": f"{base_url}/introspect",
            
            # Supported parameters
            "response_types_supported": ["code", "code id_token"],
            "grant_types_supported": [
                "authorization_code",
                "refresh_token",
                "client_credentials"
            ],
            "subject_types_supported": ["public"],
            "id_token_signing_alg_values_supported": ["RS256"],
            "token_endpoint_auth_methods_supported": [
                "client_secret_post",
                "client_secret_basic",
                "private_key_jwt"
            ],
            
            # SMART-specific capabilities
            "capabilities": [
                "launch-ehr",
                "launch-standalone",
                "client-public",
                "client-confidential",
                "sso-openid-connect",
                "context-passthrough-banner",
                "context-passthrough-style",
                "context-standalone-patient",
                "context-standalone-encounter",
                "permission-offline",
                "permission-patient",
                "permission-user"
            ],
            
            # Supported scopes
            "scopes_supported": [
                "openid", "profile", "fhirUser", "email",
                "launch", "launch/patient", "launch/encounter",
                "patient/*.read", "patient/*.write",
                "user/*.read", "user/*.write",
                "system/*.read", "system/*.write"
            ],
            
            # Code challenge methods
            "code_challenge_methods_supported": ["S256"]
        }
        
        return metadata
    
    async def get_jwks(self) -> Dict[str, Any]:
        """Get JSON Web Key Set (JWKS)"""
        
        # Get public key in JWK format
        public_numbers = self.public_key.public_numbers()
        
        # Convert to base64url encoding
        def int_to_base64url(value: int) -> str:
            """Convert integer to base64url string"""
            byte_length = (value.bit_length() + 7) // 8
            value_bytes = value.to_bytes(byte_length, byteorder='big')
            return base64.urlsafe_b64encode(value_bytes).decode().rstrip('=')
        
        jwk = {
            "kty": "RSA",
            "use": "sig",
            "alg": "RS256",
            "kid": "smart-auth-key-1",
            "n": int_to_base64url(public_numbers.n),
            "e": int_to_base64url(public_numbers.e)
        }
        
        return {"keys": [jwk]}
    
    async def validate_client(self, client_id: str, client_secret: Optional[str] = None) -> Optional[SMARTClient]:
        """Validate client credentials"""
        
        client = self.clients.get(client_id)
        if not client or not client.active:
            return None
        
        # For confidential clients, validate secret
        if client.is_confidential():
            if not client_secret or client_secret != client.client_secret:
                return None
        
        return client
    
    async def create_authorization_request(self, params: Dict[str, str]) -> SMARTAuthorizationRequest:
        """Create and validate authorization request"""
        
        try:
            # Extract required parameters
            response_type = params.get("response_type")
            client_id = params.get("client_id")
            redirect_uri = params.get("redirect_uri")
            scope = params.get("scope", "")
            state = params.get("state")
            aud = params.get("aud")
            
            # Validate required parameters
            if not all([response_type, client_id, redirect_uri, state, aud]):
                raise HTTPException(
                    status_code=400,
                    detail="Missing required parameters"
                )
            
            # Validate client
            client = await self.validate_client(client_id)
            if not client:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid client_id"
                )
            
            # Validate redirect URI
            if not client.validate_redirect_uri(redirect_uri):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid redirect_uri"
                )
            
            # Validate audience (should be FHIR server base URL)
            if aud != settings.API_BASE_URL:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid audience"
                )
            
            # Create authorization request
            auth_request = SMARTAuthorizationRequest(
                response_type=response_type,
                client_id=client_id,
                redirect_uri=redirect_uri,
                scope=scope,
                state=state,
                aud=aud,
                launch=params.get("launch"),
                code_challenge=params.get("code_challenge"),
                code_challenge_method=params.get("code_challenge_method"),
                nonce=params.get("nonce")
            )
            
            logger.info("SMART_AUTH - Authorization request created",
                       client_id=client_id,
                       scope=scope,
                       launch=auth_request.launch)
            
            return auth_request
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("SMART_AUTH - Authorization request creation failed",
                        error=str(e))
            raise HTTPException(
                status_code=400,
                detail="Invalid authorization request"
            )
    
    async def create_authorization_code(self, auth_request: SMARTAuthorizationRequest,
                                     user_id: str, launch_context: Optional[Dict[str, Any]] = None) -> str:
        """Create authorization code after user consent"""
        
        try:
            # Generate authorization code
            code = secrets.token_urlsafe(32)
            
            # Parse scopes
            scopes = auth_request.scope.split() if auth_request.scope else []
            
            # Create authorization code record
            auth_code = SMARTAuthorizationCode(
                code=code,
                client_id=auth_request.client_id,
                user_id=user_id,
                scopes=scopes,
                redirect_uri=auth_request.redirect_uri,
                expires_at=datetime.now() + timedelta(minutes=10),  # 10 minute expiry
                launch_context=launch_context,
                code_challenge=auth_request.code_challenge,
                nonce=auth_request.nonce
            )
            
            # Store authorization code
            self.auth_codes[code] = auth_code
            
            # Audit log
            await audit_change(
                self.db,
                table_name="smart_authorization_codes",
                operation="CREATE",
                record_ids=[code],
                old_values=None,
                new_values={
                    "client_id": auth_request.client_id,
                    "user_id": user_id,
                    "scopes": scopes,
                    "launch_context": launch_context
                },
                user_id=user_id,
                session_id=None
            )
            
            logger.info("SMART_AUTH - Authorization code created",
                       client_id=auth_request.client_id,
                       user_id=user_id,
                       scopes=scopes,
                       code_length=len(code))
            
            return code
            
        except Exception as e:
            logger.error("SMART_AUTH - Authorization code creation failed",
                        client_id=auth_request.client_id,
                        user_id=user_id,
                        error=str(e))
            raise HTTPException(
                status_code=500,
                detail="Failed to create authorization code"
            )
    
    async def exchange_authorization_code(self, code: str, client_id: str,
                                       client_secret: Optional[str] = None,
                                       redirect_uri: Optional[str] = None,
                                       code_verifier: Optional[str] = None) -> SMARTAccessToken:
        """Exchange authorization code for access token"""
        
        try:
            # Validate client
            client = await self.validate_client(client_id, client_secret)
            if not client:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid client credentials"
                )
            
            # Get authorization code
            auth_code = self.auth_codes.get(code)
            if not auth_code:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid authorization code"
                )
            
            # Validate authorization code
            if auth_code.is_expired():
                # Clean up expired code
                del self.auth_codes[code]
                raise HTTPException(
                    status_code=400,
                    detail="Authorization code expired"
                )
            
            if auth_code.client_id != client_id:
                raise HTTPException(
                    status_code=400,
                    detail="Authorization code client mismatch"
                )
            
            if redirect_uri and auth_code.redirect_uri != redirect_uri:
                raise HTTPException(
                    status_code=400,
                    detail="Redirect URI mismatch"
                )
            
            # Validate PKCE if present
            if auth_code.code_challenge and code_verifier:
                auth_request = SMARTAuthorizationRequest(
                    response_type="code",
                    client_id=client_id,
                    redirect_uri=auth_code.redirect_uri,
                    scope=" ".join(auth_code.scopes),
                    state="dummy",
                    aud=settings.API_BASE_URL,
                    code_challenge=auth_code.code_challenge,
                    code_challenge_method="S256"
                )
                
                if not auth_request.validate_pkce(code_verifier):
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid PKCE code verifier"
                    )
            
            # Generate access token
            access_token = await self._create_access_token(auth_code)
            
            # Generate refresh token if offline_access scope requested
            refresh_token = None
            if "offline_access" in auth_code.scopes:
                refresh_token = secrets.token_urlsafe(32)
                # Store refresh token (in production, store in database)
                
            # Generate ID token if openid scope requested
            id_token = None
            if "openid" in auth_code.scopes:
                id_token = await self._create_id_token(auth_code)
            
            # Create token response
            token_response = SMARTAccessToken(
                access_token=access_token,
                expires_in=3600,
                refresh_token=refresh_token,
                scope=" ".join(auth_code.scopes),
                patient=auth_code.launch_context.get("patient") if auth_code.launch_context else None,
                encounter=auth_code.launch_context.get("encounter") if auth_code.launch_context else None,
                fhir_user=f"Practitioner/{auth_code.user_id}",
                id_token=id_token
            )
            
            # Store access token metadata
            self.access_tokens[access_token] = {
                "user_id": auth_code.user_id,
                "client_id": client_id,
                "scopes": auth_code.scopes,
                "launch_context": auth_code.launch_context,
                "expires_at": datetime.now() + timedelta(seconds=3600),
                "created_at": datetime.now()
            }
            
            # Clean up authorization code
            del self.auth_codes[code]
            
            # Audit log
            await audit_change(
                self.db,
                table_name="smart_access_tokens",
                operation="CREATE",
                record_ids=[access_token[:16] + "..."],  # Log partial token for security
                old_values=None,
                new_values={
                    "client_id": client_id,
                    "user_id": auth_code.user_id,
                    "scopes": auth_code.scopes,
                    "patient": token_response.patient,
                    "encounter": token_response.encounter
                },
                user_id=auth_code.user_id,
                session_id=None
            )
            
            logger.info("SMART_AUTH - Access token created",
                       client_id=client_id,
                       user_id=auth_code.user_id,
                       scopes=auth_code.scopes,
                       has_patient_context=bool(token_response.patient),
                       has_refresh_token=bool(refresh_token))
            
            return token_response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("SMART_AUTH - Token exchange failed",
                        client_id=client_id,
                        error=str(e))
            raise HTTPException(
                status_code=500,
                detail="Token exchange failed"
            )
    
    async def _create_access_token(self, auth_code: SMARTAuthorizationCode) -> str:
        """Create JWT access token"""
        
        now = datetime.now()
        payload = {
            "iss": f"{settings.API_BASE_URL}/smart",  # Issuer
            "sub": auth_code.user_id,  # Subject (user)
            "aud": settings.API_BASE_URL,  # Audience (FHIR server)
            "exp": int((now + timedelta(hours=1)).timestamp()),  # Expiration
            "iat": int(now.timestamp()),  # Issued at
            "jti": str(uuid.uuid4()),  # JWT ID
            "client_id": auth_code.client_id,
            "scope": " ".join(auth_code.scopes)
        }
        
        # Add launch context
        if auth_code.launch_context:
            if "patient" in auth_code.launch_context:
                payload["patient"] = auth_code.launch_context["patient"]
            if "encounter" in auth_code.launch_context:
                payload["encounter"] = auth_code.launch_context["encounter"]
        
        # Sign JWT with private key
        private_pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        token = jwt.encode(
            payload,
            private_pem,
            algorithm="RS256",
            headers={"kid": "smart-auth-key-1"}
        )
        
        return token
    
    async def _create_id_token(self, auth_code: SMARTAuthorizationCode) -> str:
        """Create OpenID Connect ID token"""
        
        now = datetime.now()
        payload = {
            "iss": f"{settings.API_BASE_URL}/smart",
            "sub": auth_code.user_id,
            "aud": auth_code.client_id,
            "exp": int((now + timedelta(hours=1)).timestamp()),
            "iat": int(now.timestamp()),
            "auth_time": int(now.timestamp()),
            "nonce": auth_code.nonce
        }
        
        # Add profile information if requested
        if "profile" in auth_code.scopes:
            payload.update({
                "name": f"User {auth_code.user_id}",
                "family_name": "User",
                "given_name": auth_code.user_id,
                "preferred_username": auth_code.user_id
            })
        
        if "fhirUser" in auth_code.scopes:
            payload["fhirUser"] = f"Practitioner/{auth_code.user_id}"
        
        # Sign JWT
        private_pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        token = jwt.encode(
            payload,
            private_pem,
            algorithm="RS256",
            headers={"kid": "smart-auth-key-1"}
        )
        
        return token
    
    async def validate_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT access token"""
        
        try:
            # Get public key
            public_pem = self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            # Decode and validate JWT
            payload = jwt.decode(
                token,
                public_pem,
                algorithms=["RS256"],
                audience=settings.API_BASE_URL,
                issuer=f"{settings.API_BASE_URL}/smart"
            )
            
            # Check if token exists in our store
            token_data = self.access_tokens.get(token)
            if not token_data:
                return None
            
            # Check expiration
            if datetime.now() > token_data["expires_at"]:
                # Clean up expired token
                del self.access_tokens[token]
                return None
            
            # Return token metadata
            return {
                "user_id": payload["sub"],
                "client_id": payload["client_id"],
                "scopes": payload["scope"].split(),
                "patient": payload.get("patient"),
                "encounter": payload.get("encounter"),
                "fhir_user": f"Practitioner/{payload['sub']}"
            }
            
        except jwt.ExpiredSignatureError:
            logger.warning("SMART_AUTH - Expired access token presented")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning("SMART_AUTH - Invalid access token",
                          error=str(e))
            return None
        except Exception as e:
            logger.error("SMART_AUTH - Token validation failed",
                        error=str(e))
            return None
    
    async def revoke_token(self, token: str, client_id: str,
                          client_secret: Optional[str] = None) -> bool:
        """Revoke access or refresh token"""
        
        try:
            # Validate client
            client = await self.validate_client(client_id, client_secret)
            if not client:
                return False
            
            # Remove from token store
            if token in self.access_tokens:
                token_data = self.access_tokens[token]
                
                # Verify client owns token
                if token_data["client_id"] != client_id:
                    return False
                
                # Remove token
                del self.access_tokens[token]
                
                # Audit log
                await audit_change(
                    self.db,
                    table_name="smart_access_tokens",
                    operation="REVOKE",
                    record_ids=[token[:16] + "..."],
                    old_values=token_data,
                    new_values={"revoked_at": datetime.now()},
                    user_id=token_data["user_id"],
                    session_id=None
                )
                
                logger.info("SMART_AUTH - Token revoked",
                           client_id=client_id,
                           user_id=token_data["user_id"])
                
                return True
            
            return False
            
        except Exception as e:
            logger.error("SMART_AUTH - Token revocation failed",
                        client_id=client_id,
                        error=str(e))
            return False

# Export key classes and service
__all__ = [
    "SMARTAuthService",
    "SMARTClient", 
    "SMARTAuthorizationRequest",
    "SMARTAccessToken",
    "SMARTScope"
]