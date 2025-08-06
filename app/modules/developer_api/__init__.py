"""
Developer API Platform for Healthcare Platform V2.0

Comprehensive API platform enabling external developers to integrate with
the AI-ready healthcare ecosystem. Provides secure access to MCP/A2A capabilities,
medical AI agents, and healthcare data with full compliance support.
"""

from .api_gateway import APIGateway
from .sdk_generator import SDKGenerator
from .rate_limiter import RateLimiter
from .authentication import DeveloperAuth, APIKeyManager
from .webhook_manager import WebhookManager
from .schemas import (
    DeveloperProject, APIKey, WebhookEndpoint, APIRequest, APIResponse,
    SDKConfiguration, RateLimitConfig, DeveloperTier
)
from .models import (
    DeveloperAccount, DeveloperProject as DeveloperProjectModel,
    APIKeyModel, WebhookEndpointModel, APIUsageLog
)

# Export main classes for easy import
__all__ = [
    "APIGateway",
    "SDKGenerator", 
    "RateLimiter",
    "DeveloperAuth",
    "APIKeyManager",
    "WebhookManager",
    "DeveloperProject",
    "APIKey",
    "WebhookEndpoint",
    "APIRequest",
    "APIResponse",
    "SDKConfiguration",
    "RateLimitConfig",
    "DeveloperTier",
    "DeveloperAccount",
    "DeveloperProjectModel",
    "APIKeyModel",
    "WebhookEndpointModel",
    "APIUsageLog"
]

# Module version for SDK generation
__version__ = "2.0.0"