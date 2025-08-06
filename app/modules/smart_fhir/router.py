#!/usr/bin/env python3
"""
SMART on FHIR Router Implementation
OAuth2/OpenID Connect endpoints for FHIR authentication.

This module provides the REST API endpoints for SMART on FHIR authentication,
including authorization, token exchange, and metadata endpoints.

Endpoints:
- GET /.well-known/smart-configuration - SMART authorization server metadata
- GET /.well-known/jwks.json - JSON Web Key Set
- GET /auth - Authorization endpoint
- POST /token - Token exchange endpoint
- POST /revoke - Token revocation endpoint
- GET /userinfo - User information endpoint (OpenID Connect)
- POST /register - Dynamic client registration
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode, urlparse
import structlog

from fastapi import APIRouter, HTTPException, Depends, Query, Request, Response, Form
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database_unified import get_async_session
from app.core.security import get_current_user_with_permissions
from app.modules.smart_fhir.smart_auth import (
    SMARTAuthService, SMARTAuthorizationRequest, SMARTAccessToken,
    SMARTClient, SMARTScope, SMARTGrantType
)

logger = structlog.get_logger()

# Pydantic models for request/response

class TokenRequest(BaseModel):
    """OAuth2 token request"""
    grant_type: str
    code: Optional[str] = None
    redirect_uri: Optional[str] = None
    client_id: str
    client_secret: Optional[str] = None
    code_verifier: Optional[str] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None

class ClientRegistrationRequest(BaseModel):
    """Dynamic client registration request"""
    client_name: str
    client_type: str = "public"  # public or confidential
    redirect_uris: List[str]
    scopes: List[str]
    launch_uri: Optional[str] = None
    jwks_uri: Optional[str] = None

class ClientRegistrationResponse(BaseModel):
    """Dynamic client registration response"""
    client_id: str
    client_name: str
    client_type: str
    redirect_uris: List[str]
    scopes: List[str]
    client_secret: Optional[str] = None
    registration_access_token: Optional[str] = None
    registration_client_uri: Optional[str] = None

# Router setup
router = APIRouter(prefix="/smart", tags=["SMART on FHIR"])
security = HTTPBearer()

async def get_smart_service(
    db: AsyncSession = Depends(get_async_session)
) -> SMARTAuthService:
    """Dependency injection for SMART service"""
    return SMARTAuthService(db)

# SMART Configuration and Metadata Endpoints

@router.get("/.well-known/smart-configuration")
async def get_smart_configuration(
    service: SMARTAuthService = Depends(get_smart_service)
):
    """
    SMART authorization server metadata endpoint.
    
    This endpoint provides metadata about the SMART authorization server,
    including supported capabilities, endpoints, and security features.
    """
    
    try:
        metadata = await service.get_authorization_metadata()
        
        logger.info("SMART_CONFIG - Configuration metadata requested")
        
        return metadata
        
    except Exception as e:
        logger.error("SMART_CONFIG - Failed to get configuration",
                    error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve SMART configuration"
        )

@router.get("/.well-known/jwks.json")
async def get_jwks(
    service: SMARTAuthService = Depends(get_smart_service)
):
    """
    JSON Web Key Set (JWKS) endpoint.
    
    Provides the public keys used to verify JWT tokens issued by this
    authorization server.
    """
    
    try:
        jwks = await service.get_jwks()
        
        logger.info("SMART_JWKS - JWKS requested")
        
        return jwks
        
    except Exception as e:
        logger.error("SMART_JWKS - Failed to get JWKS",
                    error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve JWKS"
        )

# Authorization Endpoints

@router.get("/auth")
async def authorize(
    request: Request,
    response_type: str = Query(..., description="OAuth2 response type"),
    client_id: str = Query(..., description="Client identifier"),
    redirect_uri: str = Query(..., description="Redirect URI"),
    scope: str = Query("", description="Requested scopes"),
    state: str = Query(..., description="State parameter for CSRF protection"),
    aud: str = Query(..., description="FHIR server base URL"),
    launch: Optional[str] = Query(None, description="Launch context token"),
    code_challenge: Optional[str] = Query(None, description="PKCE code challenge"),
    code_challenge_method: Optional[str] = Query(None, description="PKCE method"),
    nonce: Optional[str] = Query(None, description="OpenID Connect nonce"),
    service: SMARTAuthService = Depends(get_smart_service)
):
    """
    OAuth2 authorization endpoint.
    
    Initiates the authorization flow by validating the request parameters
    and presenting a consent screen to the user (or redirecting to login).
    """
    
    try:
        # Create authorization request from parameters
        params = dict(request.query_params)
        auth_request = await service.create_authorization_request(params)
        
        logger.info("SMART_AUTH - Authorization request received",
                   client_id=client_id,
                   scope=scope,
                   has_launch_context=bool(launch))
        
        # For demo purposes, we'll auto-approve the request
        # In production, this would show a consent screen
        
        # Simulate user authentication and consent
        # This would normally be handled by your authentication system
        user_id = "demo-user-123"  # Would come from authenticated session
        
        # Extract launch context if provided
        launch_context = None
        if launch:
            # In a real implementation, you would decode the launch token
            # and extract patient/encounter context
            launch_context = {
                "patient": "Patient/123",
                "encounter": "Encounter/456"
            }
        
        # Create authorization code
        code = await service.create_authorization_code(
            auth_request, user_id, launch_context
        )
        
        # Build redirect URL with authorization code
        redirect_params = {
            "code": code,
            "state": state
        }
        
        redirect_url = f"{redirect_uri}?{urlencode(redirect_params)}"
        
        logger.info("SMART_AUTH - Authorization approved, redirecting",
                   client_id=client_id,
                   user_id=user_id,
                   redirect_uri=redirect_uri)
        
        return RedirectResponse(url=redirect_url)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("SMART_AUTH - Authorization failed",
                    client_id=client_id,
                    error=str(e))
        
        # Redirect to client with error
        error_params = {
            "error": "server_error",
            "error_description": "Authorization request failed",
            "state": state
        }
        error_url = f"{redirect_uri}?{urlencode(error_params)}"
        
        return RedirectResponse(url=error_url)

@router.get("/auth/consent")
async def show_consent_form(
    request: Request,
    client_id: str = Query(...),
    scope: str = Query(""),
    service: SMARTAuthService = Depends(get_smart_service)
):
    """
    Display consent form for user authorization.
    
    This endpoint would show a consent screen where users can review
    the requested permissions and approve or deny the request.
    """
    
    try:
        # Validate client
        client = await service.validate_client(client_id)
        if not client:
            raise HTTPException(status_code=400, detail="Invalid client")
        
        # Parse requested scopes
        requested_scopes = scope.split() if scope else []
        
        # Generate consent form HTML
        scope_descriptions = {
            SMARTScope.PATIENT_READ_ALL.value: "Read all patient data",
            SMARTScope.PATIENT_WRITE_ALL.value: "Write all patient data",
            SMARTScope.USER_READ_ALL.value: "Read data based on your role",
            SMARTScope.USER_WRITE_ALL.value: "Write data based on your role",
            SMARTScope.LAUNCH_PATIENT.value: "Access patient context",
            SMARTScope.LAUNCH_ENCOUNTER.value: "Access encounter context",
            SMARTScope.OPENID.value: "Verify your identity",
            SMARTScope.PROFILE.value: "Access your profile information"
        }
        
        scope_list = ""
        for scope_item in requested_scopes:
            description = scope_descriptions.get(scope_item, scope_item)
            scope_list += f"<li>{description} ({scope_item})</li>"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authorization Request</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .container {{ max-width: 600px; margin: 0 auto; }}
                .app-info {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
                .permissions {{ margin: 20px 0; }}
                .permissions ul {{ padding-left: 20px; }}
                .buttons {{ margin-top: 30px; }}
                .btn {{ padding: 12px 30px; margin: 0 10px; border: none; border-radius: 5px; cursor: pointer; }}
                .btn-approve {{ background: #28a745; color: white; }}
                .btn-deny {{ background: #dc3545; color: white; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Authorization Request</h1>
                
                <div class="app-info">
                    <h3>{client.client_name}</h3>
                    <p>This application is requesting permission to access your health information.</p>
                </div>
                
                <div class="permissions">
                    <h4>Requested Permissions:</h4>
                    <ul>
                        {scope_list}
                    </ul>
                </div>
                
                <div class="buttons">
                    <button class="btn btn-approve" onclick="approve()">Allow</button>
                    <button class="btn btn-deny" onclick="deny()">Deny</button>
                </div>
            </div>
            
            <script>
                function approve() {{
                    // Submit approval - in real implementation, this would POST to approval endpoint
                    alert("Authorization approved (demo)");
                }}
                
                function deny() {{
                    // Submit denial
                    alert("Authorization denied (demo)");
                }}
            </script>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error("SMART_CONSENT - Failed to show consent form",
                    client_id=client_id,
                    error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to display consent form"
        )

# Token Endpoints

@router.post("/token")
async def token_endpoint(
    grant_type: str = Form(...),
    code: Optional[str] = Form(None),
    redirect_uri: Optional[str] = Form(None),
    client_id: str = Form(...),
    client_secret: Optional[str] = Form(None),
    code_verifier: Optional[str] = Form(None),
    refresh_token: Optional[str] = Form(None),
    scope: Optional[str] = Form(None),
    service: SMARTAuthService = Depends(get_smart_service)
):
    """
    OAuth2 token endpoint.
    
    Exchanges authorization codes for access tokens, or refreshes
    existing tokens.
    """
    
    try:
        logger.info("SMART_TOKEN - Token request received",
                   grant_type=grant_type,
                   client_id=client_id,
                   has_code=bool(code),
                   has_refresh_token=bool(refresh_token))
        
        if grant_type == SMARTGrantType.AUTHORIZATION_CODE.value:
            # Authorization code grant
            if not code:
                raise HTTPException(
                    status_code=400,
                    detail="Missing authorization code"
                )
            
            token_response = await service.exchange_authorization_code(
                code=code,
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                code_verifier=code_verifier
            )
            
            logger.info("SMART_TOKEN - Access token issued",
                       client_id=client_id,
                       has_patient_context=bool(token_response.patient),
                       scopes=token_response.scope)
            
            return token_response.to_dict()
            
        elif grant_type == SMARTGrantType.REFRESH_TOKEN.value:
            # Refresh token grant
            if not refresh_token:
                raise HTTPException(
                    status_code=400,
                    detail="Missing refresh token"
                )
            
            # TODO: Implement refresh token exchange
            raise HTTPException(
                status_code=501,
                detail="Refresh token grant not yet implemented"
            )
            
        elif grant_type == SMARTGrantType.CLIENT_CREDENTIALS.value:
            # Client credentials grant (for backend services)
            # TODO: Implement client credentials grant
            raise HTTPException(
                status_code=501,
                detail="Client credentials grant not yet implemented"
            )
            
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported grant type: {grant_type}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("SMART_TOKEN - Token request failed",
                    grant_type=grant_type,
                    client_id=client_id,
                    error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Token request failed"
        )

@router.post("/revoke")
async def revoke_token(
    token: str = Form(...),
    client_id: str = Form(...),
    client_secret: Optional[str] = Form(None),
    service: SMARTAuthService = Depends(get_smart_service)
):
    """
    Token revocation endpoint.
    
    Revokes access tokens or refresh tokens.
    """
    
    try:
        success = await service.revoke_token(
            token=token,
            client_id=client_id,
            client_secret=client_secret
        )
        
        if success:
            logger.info("SMART_REVOKE - Token revoked successfully",
                       client_id=client_id)
            return {"revoked": True}
        else:
            logger.warning("SMART_REVOKE - Token revocation failed",
                          client_id=client_id)
            return {"revoked": False}
            
    except Exception as e:
        logger.error("SMART_REVOKE - Token revocation error",
                    client_id=client_id,
                    error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Token revocation failed"
        )

# User Info Endpoint (OpenID Connect)

@router.get("/userinfo")
async def get_user_info(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    service: SMARTAuthService = Depends(get_smart_service)
):
    """
    OpenID Connect UserInfo endpoint.
    
    Returns user profile information for the authenticated user.
    """
    
    try:
        # Validate access token
        token_data = await service.validate_access_token(credentials.credentials)
        if not token_data:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired access token"
            )
        
        # Check if profile scope is present
        if "profile" not in token_data["scopes"]:
            raise HTTPException(
                status_code=403,
                detail="Insufficient scope for user information"
            )
        
        # Build user info response
        user_info = {
            "sub": token_data["user_id"],
            "name": f"User {token_data['user_id']}",
            "given_name": token_data["user_id"],
            "family_name": "User",
            "preferred_username": token_data["user_id"]
        }
        
        # Add FHIR user reference if requested
        if "fhirUser" in token_data["scopes"]:
            user_info["fhirUser"] = token_data["fhir_user"]
        
        logger.info("SMART_USERINFO - User info requested",
                   user_id=token_data["user_id"],
                   client_id=token_data["client_id"])
        
        return user_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("SMART_USERINFO - Failed to get user info",
                    error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user information"
        )

# Client Registration Endpoint

@router.post("/register")
async def register_client(
    registration_request: ClientRegistrationRequest,
    service: SMARTAuthService = Depends(get_smart_service)
):
    """
    Dynamic client registration endpoint.
    
    Allows clients to register themselves with the authorization server.
    """
    
    try:
        # Generate client ID
        import secrets
        client_id = f"smart-client-{secrets.token_hex(8)}"
        
        # Generate client secret for confidential clients
        client_secret = None
        if registration_request.client_type == "confidential":
            client_secret = secrets.token_urlsafe(32)
        
        # Create client
        client = SMARTClient(
            client_id=client_id,
            client_name=registration_request.client_name,
            client_type=registration_request.client_type,
            client_secret=client_secret,
            redirect_uris=registration_request.redirect_uris,
            scopes=registration_request.scopes,
            launch_uri=registration_request.launch_uri,
            jwks_uri=registration_request.jwks_uri
        )
        
        # Store client (in production, store in database)
        service.clients[client_id] = client
        
        # Create response
        response = ClientRegistrationResponse(
            client_id=client_id,
            client_name=registration_request.client_name,
            client_type=registration_request.client_type,
            redirect_uris=registration_request.redirect_uris,
            scopes=registration_request.scopes,
            client_secret=client_secret
        )
        
        logger.info("SMART_REGISTER - Client registered",
                   client_id=client_id,
                   client_name=registration_request.client_name,
                   client_type=registration_request.client_type)
        
        return response
        
    except Exception as e:
        logger.error("SMART_REGISTER - Client registration failed",
                    client_name=registration_request.client_name,
                    error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Client registration failed"
        )

# Introspection Endpoint (RFC 7662)

@router.post("/introspect")
async def introspect_token(
    token: str = Form(...),
    client_id: str = Form(...),
    client_secret: Optional[str] = Form(None),
    service: SMARTAuthService = Depends(get_smart_service)
):
    """
    Token introspection endpoint.
    
    Allows clients to query information about access tokens.
    """
    
    try:
        # Validate client
        client = await service.validate_client(client_id, client_secret)
        if not client:
            raise HTTPException(
                status_code=401,
                detail="Invalid client credentials"
            )
        
        # Validate token
        token_data = await service.validate_access_token(token)
        
        if token_data:
            # Token is active
            response = {
                "active": True,
                "client_id": token_data["client_id"],
                "scope": " ".join(token_data["scopes"]),
                "sub": token_data["user_id"],
                "exp": int((token_data.get("expires_at", datetime.now())).timestamp()),
                "iat": int((token_data.get("created_at", datetime.now())).timestamp())
            }
            
            # Add context information
            if token_data.get("patient"):
                response["patient"] = token_data["patient"]
            if token_data.get("encounter"):
                response["encounter"] = token_data["encounter"]
            if token_data.get("fhir_user"):
                response["fhirUser"] = token_data["fhir_user"]
                
        else:
            # Token is inactive
            response = {"active": False}
        
        logger.info("SMART_INTROSPECT - Token introspected",
                   client_id=client_id,
                   active=response["active"])
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("SMART_INTROSPECT - Token introspection failed",
                    client_id=client_id,
                    error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Token introspection failed"
        )

# Export router
__all__ = ["router"]