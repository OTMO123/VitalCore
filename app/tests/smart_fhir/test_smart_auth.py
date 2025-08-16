#!/usr/bin/env python3
"""
Tests for SMART on FHIR Authentication
Comprehensive test suite for OAuth2/OpenID Connect authentication.
"""

import asyncio
import json
import pytest
import jwt
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from urllib.parse import parse_qs, urlparse

from app.modules.smart_fhir.smart_auth import (
    SMARTAuthService, SMARTClient, SMARTAuthorizationRequest,
    SMARTAccessToken, SMARTScope, SMARTGrantType
)

class TestSMARTClient:
    """Test SMART client functionality"""
    
    def test_smart_client_creation(self):
        """Test SMART client creation and validation"""
        client = SMARTClient(
            client_id="test-client",
            client_name="Test Client",
            client_type="public",
            redirect_uris=["http://localhost:3000/callback"],
            scopes=[SMARTScope.PATIENT_READ_ALL.value]
        )
        
        assert client.client_id == "test-client"
        assert client.client_name == "Test Client"
        assert not client.is_confidential()
        assert client.validate_redirect_uri("http://localhost:3000/callback")
        assert not client.validate_redirect_uri("http://evil.com/callback")
    
    def test_confidential_client(self):
        """Test confidential client functionality"""
        client = SMARTClient(
            client_id="confidential-client",
            client_name="Confidential Client",
            client_type="confidential",
            client_secret="super-secret",
            redirect_uris=["https://app.example.com/callback"],
            scopes=[SMARTScope.SYSTEM_READ_ALL.value]
        )
        
        assert client.is_confidential()
        assert client.client_secret == "super-secret"

class TestSMARTAuthorizationRequest:
    """Test SMART authorization request handling"""
    
    def test_authorization_request_creation(self):
        """Test authorization request creation"""
        auth_request = SMARTAuthorizationRequest(
            response_type="code",
            client_id="test-client",
            redirect_uri="http://localhost:3000/callback",
            scope="patient/*.read launch/patient openid",
            state="random-state-123",
            aud="https://fhir.example.com",
            launch="launch-token-456",
            code_challenge="challenge-hash",
            code_challenge_method="S256",
            nonce="nonce-789"
        )
        
        assert auth_request.response_type == "code"
        assert auth_request.client_id == "test-client"
        assert auth_request.launch == "launch-token-456"
        assert auth_request.code_challenge == "challenge-hash"
    
    def test_pkce_validation(self):
        """Test PKCE code challenge validation"""
        import base64
        import hashlib
        
        # Generate PKCE parameters
        code_verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).decode().rstrip("=")
        
        auth_request = SMARTAuthorizationRequest(
            response_type="code",
            client_id="test-client",
            redirect_uri="http://localhost:3000/callback",
            scope="patient/*.read",
            state="state",
            aud="https://fhir.example.com",
            code_challenge=code_challenge,
            code_challenge_method="S256"
        )
        
        # Valid verifier should pass
        assert auth_request.validate_pkce(code_verifier)
        
        # Invalid verifier should fail
        assert not auth_request.validate_pkce("invalid-verifier")

class TestSMARTAuthService:
    """Test SMART authentication service"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return AsyncMock()
    
    @pytest.fixture
    def auth_service(self, mock_db_session):
        """Create SMART auth service for testing"""
        with patch('app.core.config.get_settings') as mock_settings:
            mock_settings.return_value.API_BASE_URL = "https://fhir.example.com"
            return SMARTAuthService(mock_db_session)
    
    @pytest.mark.asyncio
    async def test_get_authorization_metadata(self, auth_service):
        """Test authorization server metadata endpoint"""
        metadata = await auth_service.get_authorization_metadata()
        
        assert metadata["issuer"] == "https://fhir.example.com/smart"
        assert "authorization_endpoint" in metadata
        assert "token_endpoint" in metadata
        assert "jwks_uri" in metadata
        assert "patient/*.read" in metadata["scopes_supported"]
        assert "launch-ehr" in metadata["capabilities"]
    
    @pytest.mark.asyncio
    async def test_get_jwks(self, auth_service):
        """Test JWKS endpoint"""
        jwks = await auth_service.get_jwks()
        
        assert "keys" in jwks
        assert len(jwks["keys"]) > 0
        
        key = jwks["keys"][0]
        assert key["kty"] == "RSA"
        assert key["use"] == "sig"
        assert key["alg"] == "RS256"
        assert "n" in key  # RSA modulus
        assert "e" in key  # RSA exponent
    
    @pytest.mark.asyncio
    async def test_validate_client(self, auth_service):
        """Test client validation"""
        # Test valid public client
        client = await auth_service.validate_client("smart-public-client")
        assert client is not None
        assert client.client_id == "smart-public-client"
        
        # Test valid confidential client with correct secret
        client = await auth_service.validate_client(
            "smart-confidential-client",
            "super-secret-key-for-confidential-client"
        )
        assert client is not None
        
        # Test confidential client with wrong secret
        client = await auth_service.validate_client(
            "smart-confidential-client",
            "wrong-secret"
        )
        assert client is None
        
        # Test invalid client ID
        client = await auth_service.validate_client("nonexistent-client")
        assert client is None
    
    @pytest.mark.asyncio
    async def test_create_authorization_request(self, auth_service):
        """Test authorization request creation and validation"""
        params = {
            "response_type": "code",
            "client_id": "smart-public-client",
            "redirect_uri": "http://localhost:3000/smart/callback",
            "scope": "patient/*.read launch/patient openid",
            "state": "random-state-123",
            "aud": "https://fhir.example.com",
            "launch": "launch-token-456"
        }
        
        auth_request = await auth_service.create_authorization_request(params)
        
        assert auth_request.response_type == "code"
        assert auth_request.client_id == "smart-public-client"
        assert auth_request.launch == "launch-token-456"
    
    @pytest.mark.asyncio
    async def test_create_authorization_request_validation_errors(self, auth_service):
        """Test authorization request validation errors"""
        # Missing required parameters
        with pytest.raises(Exception):
            await auth_service.create_authorization_request({})
        
        # Invalid client ID
        with pytest.raises(Exception):
            await auth_service.create_authorization_request({
                "response_type": "code",
                "client_id": "invalid-client",
                "redirect_uri": "http://localhost:3000/callback",
                "scope": "patient/*.read",
                "state": "state",
                "aud": "https://fhir.example.com"
            })
        
        # Invalid redirect URI
        with pytest.raises(Exception):
            await auth_service.create_authorization_request({
                "response_type": "code",
                "client_id": "smart-public-client",
                "redirect_uri": "http://evil.com/callback",
                "scope": "patient/*.read",
                "state": "state",
                "aud": "https://fhir.example.com"
            })
    
    @pytest.mark.asyncio
    async def test_authorization_code_flow(self, auth_service):
        """Test complete authorization code flow"""
        # Create authorization request
        params = {
            "response_type": "code",
            "client_id": "smart-public-client",
            "redirect_uri": "http://localhost:3000/smart/callback",
            "scope": "patient/*.read launch/patient openid profile",
            "state": "random-state-123",
            "aud": "https://fhir.example.com"
        }
        
        auth_request = await auth_service.create_authorization_request(params)
        
        # Create authorization code
        user_id = "test-user-123"
        launch_context = {"patient": "Patient/123"}
        
        code = await auth_service.create_authorization_code(
            auth_request, user_id, launch_context
        )
        
        assert code is not None
        assert len(code) > 10  # Should be a decent length
        
        # Exchange authorization code for token
        token_response = await auth_service.exchange_authorization_code(
            code=code,
            client_id="smart-public-client",
            redirect_uri="http://localhost:3000/smart/callback"
        )
        
        assert token_response.access_token is not None
        assert token_response.token_type == "Bearer"
        assert token_response.patient == "Patient/123"
        assert token_response.scope == "patient/*.read launch/patient openid profile"
        assert token_response.id_token is not None  # OpenID Connect ID token
    
    @pytest.mark.asyncio
    async def test_access_token_validation(self, auth_service):
        """Test access token validation"""
        # Create and exchange authorization code first
        params = {
            "response_type": "code",
            "client_id": "smart-public-client",
            "redirect_uri": "http://localhost:3000/smart/callback",
            "scope": "patient/*.read launch/patient",
            "state": "state",
            "aud": "https://fhir.example.com"
        }
        
        auth_request = await auth_service.create_authorization_request(params)
        code = await auth_service.create_authorization_code(
            auth_request, "test-user", {"patient": "Patient/123"}
        )
        token_response = await auth_service.exchange_authorization_code(
            code, "smart-public-client", 
            redirect_uri="http://localhost:3000/smart/callback"
        )
        
        # Validate the access token
        token_data = await auth_service.validate_access_token(token_response.access_token)
        
        assert token_data is not None
        assert token_data["user_id"] == "test-user"
        assert token_data["client_id"] == "smart-public-client"
        assert "patient/*.read" in token_data["scopes"]
        assert token_data["patient"] == "Patient/123"
    
    @pytest.mark.asyncio
    async def test_token_revocation(self, auth_service):
        """Test access token revocation"""
        # Create access token first
        params = {
            "response_type": "code",
            "client_id": "smart-public-client",
            "redirect_uri": "http://localhost:3000/smart/callback",
            "scope": "patient/*.read",
            "state": "state",
            "aud": "https://fhir.example.com"
        }
        
        auth_request = await auth_service.create_authorization_request(params)
        code = await auth_service.create_authorization_code(auth_request, "test-user")
        token_response = await auth_service.exchange_authorization_code(
            code, "smart-public-client",
            redirect_uri="http://localhost:3000/smart/callback"
        )
        
        # Token should be valid initially
        token_data = await auth_service.validate_access_token(token_response.access_token)
        assert token_data is not None
        
        # Revoke token
        success = await auth_service.revoke_token(
            token_response.access_token,
            "smart-public-client"
        )
        assert success
        
        # Token should be invalid after revocation
        token_data = await auth_service.validate_access_token(token_response.access_token)
        assert token_data is None
    
    @pytest.mark.asyncio
    async def test_jwt_token_structure(self, auth_service):
        """Test JWT access token structure and claims"""
        # Create access token
        params = {
            "response_type": "code",
            "client_id": "smart-public-client",
            "redirect_uri": "http://localhost:3000/smart/callback",
            "scope": "patient/*.read launch/patient",
            "state": "state",
            "aud": "https://fhir.example.com"
        }
        
        auth_request = await auth_service.create_authorization_request(params)
        code = await auth_service.create_authorization_code(
            auth_request, "test-user", {"patient": "Patient/123"}
        )
        token_response = await auth_service.exchange_authorization_code(
            code, "smart-public-client",
            redirect_uri="http://localhost:3000/smart/callback"
        )
        
        # Decode JWT without verification to check structure
        payload = jwt.decode(token_response.access_token, options={"verify_signature": False})
        
        assert payload["iss"] == "https://fhir.example.com/smart"
        assert payload["sub"] == "test-user"
        assert payload["aud"] == "https://fhir.example.com"
        assert payload["client_id"] == "smart-public-client"
        assert payload["scope"] == "patient/*.read launch/patient"
        assert payload["patient"] == "Patient/123"
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload
    
    @pytest.mark.asyncio
    async def test_id_token_creation(self, auth_service):
        """Test OpenID Connect ID token creation"""
        # Create authorization request with openid scope
        params = {
            "response_type": "code",
            "client_id": "smart-public-client",
            "redirect_uri": "http://localhost:3000/smart/callback",
            "scope": "openid profile fhirUser",
            "state": "state",
            "aud": "https://fhir.example.com",
            "nonce": "test-nonce-123"
        }
        
        auth_request = await auth_service.create_authorization_request(params)
        code = await auth_service.create_authorization_code(auth_request, "test-user")
        token_response = await auth_service.exchange_authorization_code(
            code, "smart-public-client",
            redirect_uri="http://localhost:3000/smart/callback"
        )
        
        # Should have ID token
        assert token_response.id_token is not None
        
        # Decode ID token to check claims
        id_payload = jwt.decode(token_response.id_token, options={"verify_signature": False})
        
        assert id_payload["iss"] == "https://fhir.example.com/smart"
        assert id_payload["sub"] == "test-user"
        assert id_payload["aud"] == "smart-public-client"
        assert id_payload["nonce"] == "test-nonce-123"
        assert "name" in id_payload  # Profile information
        assert "fhirUser" in id_payload  # FHIR user reference
        assert id_payload["fhirUser"] == "Practitioner/test-user"

class TestSMARTAccessToken:
    """Test SMART access token functionality"""
    
    def test_access_token_to_dict(self):
        """Test access token dictionary conversion"""
        token = SMARTAccessToken(
            access_token="access-token-123",
            expires_in=3600,
            refresh_token="refresh-token-456",
            scope="patient/*.read launch/patient",
            patient="Patient/123",
            fhir_user="Practitioner/456",
            id_token="id-token-789"
        )
        
        token_dict = token.to_dict()
        
        assert token_dict["access_token"] == "access-token-123"
        assert token_dict["token_type"] == "Bearer"
        assert token_dict["expires_in"] == 3600
        assert token_dict["refresh_token"] == "refresh-token-456"
        assert token_dict["scope"] == "patient/*.read launch/patient"
        assert token_dict["patient"] == "Patient/123"
        assert token_dict["fhirUser"] == "Practitioner/456"
        assert token_dict["id_token"] == "id-token-789"

# Integration Tests

class TestSMARTIntegration:
    """Integration tests for SMART on FHIR flow"""
    
    @pytest.mark.asyncio
    async def test_full_smart_launch_flow(self):
        """Test complete SMART launch flow simulation"""
        with patch('app.core.config.get_settings') as mock_settings:
            mock_settings.return_value.API_BASE_URL = "https://fhir.example.com"
            
            mock_db = AsyncMock()
            auth_service = SMARTAuthService(mock_db)
            
            # Step 1: Get authorization metadata
            metadata = await auth_service.get_authorization_metadata()
            assert "authorization_endpoint" in metadata
            
            # Step 2: Create authorization request
            auth_params = {
                "response_type": "code",
                "client_id": "smart-public-client",
                "redirect_uri": "http://localhost:3000/smart/callback",
                "scope": "patient/*.read launch/patient openid profile",
                "state": "random-state-123",
                "aud": "https://fhir.example.com",
                "launch": "launch-context-token"
            }
            
            auth_request = await auth_service.create_authorization_request(auth_params)
            
            # Step 3: User authentication and consent (simulated)
            user_id = "practitioner-123"
            launch_context = {
                "patient": "Patient/456",
                "encounter": "Encounter/789"
            }
            
            # Step 4: Create authorization code
            auth_code = await auth_service.create_authorization_code(
                auth_request, user_id, launch_context
            )
            
            # Step 5: Exchange code for tokens
            token_response = await auth_service.exchange_authorization_code(
                code=auth_code,
                client_id="smart-public-client",
                redirect_uri="http://localhost:3000/smart/callback"
            )
            
            # Verify token response
            assert token_response.access_token is not None
            assert token_response.patient == "Patient/456"
            assert token_response.encounter == "Encounter/789"
            assert token_response.fhir_user == "Practitioner/practitioner-123"
            assert token_response.id_token is not None
            
            # Step 6: Validate access token
            token_data = await auth_service.validate_access_token(token_response.access_token)
            assert token_data["user_id"] == user_id
            assert token_data["patient"] == "Patient/456"
            assert token_data["encounter"] == "Encounter/789"
    
    @pytest.mark.asyncio
    async def test_pkce_flow(self):
        """Test SMART flow with PKCE (Proof Key for Code Exchange)"""
        import base64
        import hashlib
        import secrets
        
        with patch('app.core.config.get_settings') as mock_settings:
            mock_settings.return_value.API_BASE_URL = "https://fhir.example.com"
            
            mock_db = AsyncMock()
            auth_service = SMARTAuthService(mock_db)
            
            # Generate PKCE parameters
            code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode().rstrip('=')
            code_challenge = base64.urlsafe_b64encode(
                hashlib.sha256(code_verifier.encode()).digest()
            ).decode().rstrip('=')
            
            # Authorization request with PKCE
            auth_params = {
                "response_type": "code",
                "client_id": "smart-public-client",
                "redirect_uri": "http://localhost:3000/smart/callback",
                "scope": "patient/*.read",
                "state": "state-123",
                "aud": "https://fhir.example.com",
                "code_challenge": code_challenge,
                "code_challenge_method": "S256"
            }
            
            auth_request = await auth_service.create_authorization_request(auth_params)
            auth_code = await auth_service.create_authorization_code(auth_request, "user-123")
            
            # Token exchange with code verifier
            token_response = await auth_service.exchange_authorization_code(
                code=auth_code,
                client_id="smart-public-client",
                redirect_uri="http://localhost:3000/smart/callback",
                code_verifier=code_verifier
            )
            
            assert token_response.access_token is not None
            
            # Verify token is valid
            token_data = await auth_service.validate_access_token(token_response.access_token)
            assert token_data is not None