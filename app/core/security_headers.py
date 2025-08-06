"""
Security Headers Middleware for SOC2 Compliance
Implements comprehensive security headers including CSP, HSTS, and HIPAA-compliant headers.
"""

import re
from typing import Dict, List, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
import structlog

logger = structlog.get_logger()

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive security headers middleware for SOC2 Type 2 compliance.
    
    Implements:
    - Content Security Policy (CSP) with nonce support
    - HTTP Strict Transport Security (HSTS)
    - X-Content-Type-Options
    - Referrer Policy
    - Permissions Policy
    - Cross-Origin security headers
    - HIPAA-compliant security headers
    """
    
    def __init__(
        self,
        app,
        enforce_https: bool = True,
        development_mode: bool = False,
        allowed_origins: Optional[List[str]] = None,
        enable_csp_reporting: bool = True
    ):
        super().__init__(app)
        self.enforce_https = enforce_https
        self.development_mode = development_mode
        self.allowed_origins = allowed_origins or []
        self.enable_csp_reporting = enable_csp_reporting
        
        # Generate nonce for CSP (would be per-request in production)
        self.nonce_pattern = re.compile(r'nonce-[a-zA-Z0-9+/=]+')
        
    def generate_nonce(self) -> str:
        """Generate a unique nonce for CSP."""
        import secrets
        import base64
        return base64.b64encode(secrets.token_bytes(16)).decode('utf-8')
    
    def get_content_security_policy(self, request: Request, nonce: str) -> str:
        """
        Generate Content Security Policy header based on environment and request.
        
        Production CSP is strict for SOC2 compliance.
        Development CSP allows localhost and dev tools.
        Special handling for Swagger UI documentation.
        """
        
        # Check if this is a docs request
        is_docs_request = request.url.path in ["/docs", "/redoc", "/openapi.json"]
        
        # Base CSP directives for healthcare application
        base_csp = {
            "default-src": ["'self'"],
            "script-src": [
                "'self'",
                f"'nonce-{nonce}'",
                # Allow specific trusted CDNs for production
                "https://cdn.jsdelivr.net",
                "https://unpkg.com"
            ],
            "style-src": [
                "'self'",
                "'unsafe-inline'",  # Required for Material-UI and styled-components
                "https://fonts.googleapis.com",
                "https://cdn.jsdelivr.net"
            ],
            "font-src": [
                "'self'",
                "https://fonts.gstatic.com",
                "https://cdn.jsdelivr.net",
                "data:"
            ],
            "img-src": [
                "'self'",
                "data:",
                "blob:",
                "https:",  # Allow HTTPS images for healthcare content
            ],
            "connect-src": [
                "'self'",
                # API endpoints
                "https://api.iris.healthcare.gov",
                "https://iris-api.hhs.gov"
            ],
            "frame-ancestors": ["'none'"],  # Prevent clickjacking
            "base-uri": ["'self'"],
            "form-action": ["'self'"],
            "object-src": ["'none'"],
            "media-src": ["'self'", "data:", "blob:"],
            "worker-src": ["'self'", "blob:"],
            "manifest-src": ["'self'"],
            "upgrade-insecure-requests": [],  # Force HTTPS
        }
        
        # Special handling for Swagger UI documentation
        if is_docs_request:
            # Swagger UI requires unsafe-inline for scripts and styles
            # Remove nonce for docs endpoints as unsafe-inline is ignored when nonce is present
            base_csp["script-src"] = [
                "'self'",
                "'unsafe-inline'",
                "'unsafe-eval'",  # Required for Swagger UI
                "https://cdn.jsdelivr.net",
                "https://unpkg.com"
            ]
            base_csp["style-src"].append("'unsafe-inline'")
            logger.info("CSP relaxed for Swagger UI documentation", 
                       path=request.url.path, 
                       nonce_removed=True)
        
        # Development mode adjustments
        if self.development_mode:
            # Allow localhost for development
            dev_sources = [
                "http://localhost:*",
                "http://127.0.0.1:*",
                "ws://localhost:*",
                "ws://127.0.0.1:*",
                "'unsafe-eval'"  # Allow eval for dev tools
            ]
            
            base_csp["script-src"].extend(dev_sources)
            base_csp["connect-src"].extend(dev_sources)
            base_csp["style-src"].extend(dev_sources)
            
            # Remove upgrade-insecure-requests for development
            del base_csp["upgrade-insecure-requests"]
            
            logger.info("CSP configured for development mode", 
                       allowed_localhost=True, 
                       unsafe_eval=True)
        
        # Add reporting endpoint if enabled
        if self.enable_csp_reporting:
            base_csp["report-uri"] = ["/api/v1/security/csp-report"]
            base_csp["report-to"] = ["csp-endpoint"]
        
        # Convert to CSP header string
        csp_parts = []
        for directive, sources in base_csp.items():
            if sources:
                csp_parts.append(f"{directive} {' '.join(sources)}")
            else:
                csp_parts.append(directive)
        
        return "; ".join(csp_parts)
    
    def get_permissions_policy(self) -> str:
        """
        Generate Permissions Policy header for healthcare application.
        Restrictive policy for SOC2 compliance.
        """
        policies = {
            "camera": "self",
            "microphone": "self", 
            "geolocation": "none",
            "payment": "none",
            "usb": "none",
            "magnetometer": "none",
            "gyroscope": "none",
            "accelerometer": "none",
            "ambient-light-sensor": "none",
            "autoplay": "self",
            "encrypted-media": "self",
            "fullscreen": "self",
            "picture-in-picture": "none",
            "screen-wake-lock": "none",
            "web-share": "self"
        }
        
        return ", ".join([f"{feature}=({value})" for feature, value in policies.items()])
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and add security headers to response."""
        
        # Generate unique nonce for this request
        nonce = self.generate_nonce()
        
        # Store nonce in request state for use in templates
        request.state.csp_nonce = nonce
        
        # Process the request
        response: StarletteResponse = await call_next(request)
        
        # Add comprehensive security headers
        security_headers = self.get_security_headers(request, nonce)
        
        for header_name, header_value in security_headers.items():
            response.headers[header_name] = header_value
        
        # Log security header application for audit trail
        logger.info(
            "Security headers applied",
            path=request.url.path,
            method=request.method,
            headers_applied=list(security_headers.keys()),
            csp_nonce=nonce[:8] + "...",  # Log partial nonce for debugging
            client_ip=request.client.host if request.client else "unknown"
        )
        
        return response
    
    def get_security_headers(self, request: Request, nonce: str) -> Dict[str, str]:
        """Get all security headers for the response."""
        
        headers = {
            # Content Security Policy
            "Content-Security-Policy": self.get_content_security_policy(request, nonce),
            
            # Prevent MIME type sniffing
            "X-Content-Type-Options": "nosniff",
            
            # Referrer Policy for privacy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Permissions Policy
            "Permissions-Policy": self.get_permissions_policy(),
            
            # Cross-Origin Policies
            "Cross-Origin-Embedder-Policy": "require-corp",
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Resource-Policy": "same-origin",
            
            # Security headers
            "X-Frame-Options": "DENY",  # Backup for older browsers
            "X-XSS-Protection": "1; mode=block",  # Legacy XSS protection
            "X-Permitted-Cross-Domain-Policies": "none",
            
            # Cache control for sensitive data
            "Cache-Control": "no-store, no-cache, must-revalidate, private",
            "Pragma": "no-cache",
            "Expires": "0",
            
            # HIPAA compliance headers
            "X-Healthcare-Data": "protected",
            "X-PHI-Protection": "enabled",
        }
        
        # Add HSTS only for HTTPS or if enforced
        if request.url.scheme == "https" or self.enforce_https:
            headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        # Add CSP reporting headers if enabled
        if self.enable_csp_reporting:
            headers["Report-To"] = '''{"group":"csp-endpoint","max_age":10886400,"endpoints":[{"url":"/api/v1/security/csp-report"}]}'''
        
        # Development mode adjustments
        if self.development_mode:
            # Relax some headers for development
            headers["Cross-Origin-Embedder-Policy"] = "unsafe-none"
            headers["Cache-Control"] = "no-cache"
            
            logger.debug("Security headers relaxed for development mode")
        
        return headers


def get_security_headers_middleware(
    enforce_https: bool = True,
    development_mode: bool = False,
    allowed_origins: Optional[List[str]] = None,
    enable_csp_reporting: bool = True
) -> SecurityHeadersMiddleware:
    """
    Factory function to create SecurityHeadersMiddleware with configuration.
    
    Args:
        enforce_https: Whether to enforce HTTPS redirects and HSTS
        development_mode: Enable development-friendly CSP settings
        allowed_origins: List of allowed origins for CORS
        enable_csp_reporting: Enable CSP violation reporting
    
    Returns:
        Configured SecurityHeadersMiddleware instance
    """
    
    def middleware_factory(app):
        return SecurityHeadersMiddleware(
            app,
            enforce_https=enforce_https,
            development_mode=development_mode,
            allowed_origins=allowed_origins,
            enable_csp_reporting=enable_csp_reporting
        )
    
    return middleware_factory