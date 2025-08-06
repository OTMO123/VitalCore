#!/usr/bin/env python3
"""
SMART on FHIR Module
OAuth2/OpenID Connect authentication for FHIR applications.

This module provides SMART on FHIR authentication capabilities including:
- OAuth2 authorization server
- OpenID Connect identity provider
- JWT token management
- FHIR-specific scopes and contexts
- Patient and provider launch contexts

Key Components:
- smart_auth.py: Core authentication service and token management
- router.py: REST API endpoints for OAuth2/OIDC flows

Standards Compliance:
- OAuth 2.0 (RFC 6749)
- OpenID Connect 1.0
- SMART App Launch Framework
- FHIR R4 Security Implementation Guide
"""

from .smart_auth import (
    SMARTAuthService,
    SMARTClient,
    SMARTAuthorizationRequest,
    SMARTAccessToken,
    SMARTScope
)
from .router import router

__all__ = [
    "SMARTAuthService",
    "SMARTClient", 
    "SMARTAuthorizationRequest",
    "SMARTAccessToken",
    "SMARTScope",
    "router"
]