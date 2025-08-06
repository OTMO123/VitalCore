"""
Developer API Schemas for Healthcare Platform V2.0

Pydantic models for the Developer API platform with comprehensive validation,
security controls, and compliance features for external integrations.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, field_validator, EmailStr, ConfigDict
from enum import Enum
import uuid

class DeveloperTier(str, Enum):
    """Developer account tiers with different capabilities."""
    STARTER = "starter"           # Basic tier - limited requests
    PROFESSIONAL = "professional" # Mid tier - more requests, webhooks
    ENTERPRISE = "enterprise"     # Full tier - unlimited, custom features
    RESEARCH = "research"         # Academic/research institutions
    HEALTHCARE = "healthcare"     # Healthcare organizations - special compliance

class APIScope(str, Enum):
    """API access scopes for granular permission control."""
    READ_BASIC = "read:basic"                    # Basic read operations
    READ_MEDICAL = "read:medical"                # Medical data access (requires HIPAA)
    WRITE_BASIC = "write:basic"                  # Basic write operations
    WRITE_MEDICAL = "write:medical"              # Medical data writing
    MCP_COMMUNICATE = "mcp:communicate"          # MCP agent communication
    A2A_COLLABORATE = "a2a:collaborate"          # A2A collaboration
    AI_INFERENCE = "ai:inference"                # AI model inference
    FHIR_ACCESS = "fhir:access"                  # FHIR resource access
    ADMIN_MANAGE = "admin:manage"                # Admin operations
    WEBHOOK_MANAGE = "webhook:manage"            # Webhook management
    ANONYMIZE_DATA = "anonymize:data"            # Data anonymization
    EDGE_DEPLOY = "edge:deploy"                  # Edge AI deployment

class APIVersion(str, Enum):
    """Supported API versions."""
    V1_0 = "v1.0"
    V2_0 = "v2.0"
    BETA = "beta"

class RateLimitConfig(BaseModel):
    """Rate limiting configuration for API access."""
    
    requests_per_minute: int = Field(default=100, description="Requests per minute limit")
    requests_per_hour: int = Field(default=1000, description="Requests per hour limit") 
    requests_per_day: int = Field(default=10000, description="Requests per day limit")
    burst_limit: int = Field(default=10, description="Burst request limit")
    
    # Special limits for different operations
    ai_inference_per_hour: int = Field(default=100, description="AI inference calls per hour")
    collaboration_per_day: int = Field(default=50, description="A2A collaborations per day")
    fhir_operations_per_hour: int = Field(default=500, description="FHIR operations per hour")
    
    # Compliance limits
    phi_access_per_day: int = Field(default=100, description="PHI access operations per day")
    
    @field_validator('requests_per_minute', 'requests_per_hour', 'requests_per_day', 'burst_limit', 'ai_inference_per_hour', 'collaboration_per_day', 'fhir_operations_per_hour', 'phi_access_per_day')
    @classmethod
    def validate_positive(cls, v):
        """Ensure all limits are positive."""
        if isinstance(v, int) and v <= 0:
            raise ValueError('Rate limits must be positive integers')
        return v

class DeveloperProject(BaseModel):
    """Developer project configuration and metadata."""
    
    # Project identification
    project_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique project identifier")
    project_name: str = Field(..., min_length=3, max_length=100, description="Project name")
    description: str = Field(..., min_length=10, max_length=1000, description="Project description")
    
    # Project categorization
    category: str = Field(..., description="Project category (startup, research, healthcare, etc.)")
    use_case: str = Field(..., description="Primary use case for the API")
    target_audience: str = Field(..., description="Target audience for the application")
    
    # Technical configuration
    api_version: APIVersion = Field(default=APIVersion.V2_0, description="API version to use")
    scopes: List[APIScope] = Field(default=[], description="Required API scopes")
    webhook_url: Optional[str] = Field(default=None, description="Webhook endpoint URL")
    
    # Compliance requirements
    handles_phi: bool = Field(default=False, description="Whether project handles PHI")
    hipaa_compliant: bool = Field(default=False, description="HIPAA compliance certification")
    gdpr_compliant: bool = Field(default=False, description="GDPR compliance certification")
    research_purpose: bool = Field(default=False, description="Used for research purposes")
    
    # Development stage
    development_stage: str = Field(default="development", description="Current development stage")
    production_ready: bool = Field(default=False, description="Ready for production use")
    
    # Rate limiting
    rate_limits: RateLimitConfig = Field(default_factory=RateLimitConfig, description="Rate limiting configuration")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Project creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    @field_validator('scopes')
    @classmethod
    def validate_scopes_compliance(cls, v, info):
        """Validate scope requirements based on compliance flags."""
        if info.data:
            handles_phi = info.data.get('handles_phi', False)
            hipaa_compliant = info.data.get('hipaa_compliant', False)
            
            # If handling PHI, must be HIPAA compliant
            if handles_phi and not hipaa_compliant:
                raise ValueError('Projects handling PHI must be HIPAA compliant')
            
            # Medical scopes require HIPAA compliance
            medical_scopes = [APIScope.READ_MEDICAL, APIScope.WRITE_MEDICAL, APIScope.FHIR_ACCESS]
            if any(scope in v for scope in medical_scopes) and not hipaa_compliant:
                raise ValueError('Medical API scopes require HIPAA compliance')
        
        return v

class APIKey(BaseModel):
    """API key configuration and metadata."""
    
    # Key identification
    key_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique key identifier")
    key_name: str = Field(..., description="Human-readable key name")
    key_prefix: str = Field(..., description="Public key prefix for identification")
    
    # Associated project and developer
    project_id: str = Field(..., description="Associated project ID")
    developer_id: str = Field(..., description="Associated developer ID")
    
    # Key configuration
    scopes: List[APIScope] = Field(default=[], description="API scopes granted to this key")
    environment: str = Field(default="development", description="Target environment")
    
    # Security settings
    ip_restrictions: List[str] = Field(default=[], description="Allowed IP addresses/ranges")
    user_agent_restrictions: List[str] = Field(default=[], description="Allowed user agents")
    webhook_secret: Optional[str] = Field(default=None, description="Webhook verification secret")
    
    # Status and lifecycle
    is_active: bool = Field(default=True, description="Whether key is active")
    expires_at: Optional[datetime] = Field(default=None, description="Key expiration time")
    last_used_at: Optional[datetime] = Field(default=None, description="Last usage timestamp")
    
    # Usage tracking
    total_requests: int = Field(default=0, description="Total requests made with this key")
    monthly_requests: int = Field(default=0, description="Requests this month")
    
    # Compliance tracking
    phi_access_count: int = Field(default=0, description="PHI access operations count")
    last_phi_access: Optional[datetime] = Field(default=None, description="Last PHI access timestamp")
    
    # Rate limiting (can override project defaults)
    custom_rate_limits: Optional[RateLimitConfig] = Field(default=None, description="Custom rate limits")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Key creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

class WebhookEndpoint(BaseModel):
    """Webhook endpoint configuration."""
    
    # Webhook identification
    webhook_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique webhook identifier")
    project_id: str = Field(..., description="Associated project ID")
    
    # Endpoint configuration
    url: str = Field(..., description="Webhook endpoint URL")
    secret: str = Field(..., description="Webhook verification secret")
    
    # Event configuration
    events: List[str] = Field(default=[], description="Subscribed event types")
    filter_conditions: Dict[str, Any] = Field(default={}, description="Event filtering conditions")
    
    # Delivery settings
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    retry_delay_seconds: int = Field(default=60, description="Delay between retries")
    timeout_seconds: int = Field(default=30, description="Request timeout")
    
    # Status and health
    is_active: bool = Field(default=True, description="Whether webhook is active")
    last_delivery_at: Optional[datetime] = Field(default=None, description="Last successful delivery")
    failure_count: int = Field(default=0, description="Recent failure count")
    
    # Security
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")
    allowed_ips: List[str] = Field(default=[], description="IP address restrictions")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Webhook creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

class APIRequest(BaseModel):
    """API request structure for standardized handling."""
    
    # Request identification
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique request identifier")
    
    # Authentication
    api_key: str = Field(..., description="API key for authentication")
    project_id: Optional[str] = Field(default=None, description="Project ID (derived from key)")
    
    # Request details
    method: str = Field(..., description="HTTP method")
    endpoint: str = Field(..., description="API endpoint")
    version: APIVersion = Field(default=APIVersion.V2_0, description="API version")
    
    # Request data
    headers: Dict[str, str] = Field(default={}, description="Request headers")
    query_params: Dict[str, Any] = Field(default={}, description="Query parameters")
    body: Optional[Dict[str, Any]] = Field(default=None, description="Request body")
    
    # Client information
    client_ip: str = Field(..., description="Client IP address")
    user_agent: str = Field(default="", description="Client user agent")
    
    # Processing context
    scopes_required: List[APIScope] = Field(default=[], description="Required scopes for this request")
    phi_involved: bool = Field(default=False, description="Whether request involves PHI")
    
    # Timing
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Request timestamp")

class APIResponse(BaseModel):
    """API response structure with compliance tracking."""
    
    # Response identification
    request_id: str = Field(..., description="Associated request ID")
    response_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique response identifier")
    
    # Response status
    status_code: int = Field(..., description="HTTP status code")
    success: bool = Field(..., description="Whether request was successful")
    
    # Response data
    data: Optional[Dict[str, Any]] = Field(default=None, description="Response data")
    error: Optional[Dict[str, Any]] = Field(default=None, description="Error information")
    
    # Metadata
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    cache_hit: bool = Field(default=False, description="Whether response was cached")
    
    # Compliance tracking
    phi_included: bool = Field(default=False, description="Whether response includes PHI")
    audit_logged: bool = Field(default=True, description="Whether request was audit logged")
    
    # Pagination (for list endpoints)
    pagination: Optional[Dict[str, Any]] = Field(default=None, description="Pagination metadata")
    
    # Rate limiting information
    rate_limit_remaining: int = Field(default=0, description="Remaining requests in current window")
    rate_limit_reset: Optional[datetime] = Field(default=None, description="When rate limit resets")
    
    # Timestamp
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")

class SDKConfiguration(BaseModel):
    """Configuration for SDK generation."""
    
    # SDK metadata
    sdk_name: str = Field(..., description="SDK package name")
    version: str = Field(default="1.0.0", description="SDK version")
    language: str = Field(..., description="Target programming language")
    
    # API configuration
    api_version: APIVersion = Field(default=APIVersion.V2_0, description="Target API version")
    base_url: str = Field(..., description="API base URL")
    
    # Authentication
    auth_method: str = Field(default="api_key", description="Authentication method")
    
    # SDK features
    include_models: bool = Field(default=True, description="Include data models")
    include_async: bool = Field(default=True, description="Include async support")
    include_webhooks: bool = Field(default=True, description="Include webhook utilities")
    include_examples: bool = Field(default=True, description="Include code examples")
    
    # Documentation
    include_docs: bool = Field(default=True, description="Include documentation")
    doc_format: str = Field(default="markdown", description="Documentation format")
    
    # Customization
    custom_headers: Dict[str, str] = Field(default={}, description="Custom default headers")
    timeout_seconds: int = Field(default=30, description="Default request timeout")
    retry_config: Dict[str, Any] = Field(default={}, description="Retry configuration")
    
    # Compliance features
    phi_handling: bool = Field(default=False, description="Include PHI handling utilities")
    audit_logging: bool = Field(default=True, description="Include audit logging")
    
    # Generation settings
    output_directory: str = Field(default="./sdk", description="Output directory for generated SDK")
    package_registry: Optional[str] = Field(default=None, description="Package registry for publishing")

class DeveloperAccount(BaseModel):
    """Developer account information and settings."""
    
    # Account identification
    developer_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique developer identifier")
    email: EmailStr = Field(..., description="Developer email address")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    
    # Personal information
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    company: Optional[str] = Field(default=None, description="Company/organization")
    title: Optional[str] = Field(default=None, description="Job title")
    
    # Account settings
    tier: DeveloperTier = Field(default=DeveloperTier.STARTER, description="Account tier")
    timezone: str = Field(default="UTC", description="Developer timezone")
    
    # Compliance certifications
    hipaa_certified: bool = Field(default=False, description="HIPAA certification status")
    gdpr_acknowledged: bool = Field(default=False, description="GDPR acknowledgment")
    terms_accepted_at: Optional[datetime] = Field(default=None, description="Terms acceptance timestamp")
    
    # Contact preferences
    notifications_email: bool = Field(default=True, description="Email notifications enabled")
    marketing_emails: bool = Field(default=False, description="Marketing emails enabled")
    
    # Usage tracking
    total_projects: int = Field(default=0, description="Total number of projects")
    active_api_keys: int = Field(default=0, description="Number of active API keys")
    monthly_requests: int = Field(default=0, description="Monthly API requests")
    
    # Account status
    is_active: bool = Field(default=True, description="Account active status")
    is_verified: bool = Field(default=False, description="Email verification status")
    last_login_at: Optional[datetime] = Field(default=None, description="Last login timestamp")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Account creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

class APIUsageMetrics(BaseModel):
    """API usage metrics and analytics."""
    
    # Time period
    period_start: datetime = Field(..., description="Metrics period start")
    period_end: datetime = Field(..., description="Metrics period end")
    
    # Request metrics
    total_requests: int = Field(default=0, description="Total requests in period")
    successful_requests: int = Field(default=0, description="Successful requests")
    failed_requests: int = Field(default=0, description="Failed requests")
    
    # Response time metrics
    avg_response_time_ms: float = Field(default=0.0, description="Average response time")
    p95_response_time_ms: float = Field(default=0.0, description="95th percentile response time")
    p99_response_time_ms: float = Field(default=0.0, description="99th percentile response time")
    
    # Endpoint usage
    endpoint_usage: Dict[str, int] = Field(default={}, description="Usage by endpoint")
    error_breakdown: Dict[str, int] = Field(default={}, description="Error count by type")
    
    # Geographic distribution
    country_breakdown: Dict[str, int] = Field(default={}, description="Requests by country")
    
    # AI-specific metrics
    ai_inference_calls: int = Field(default=0, description="AI inference calls")
    a2a_collaborations: int = Field(default=0, description="A2A collaborations initiated")
    mcp_messages: int = Field(default=0, description="MCP messages processed")
    
    # Compliance metrics
    phi_accesses: int = Field(default=0, description="PHI access operations")
    audit_events_generated: int = Field(default=0, description="Audit events generated")
    
    # Rate limiting
    rate_limit_hits: int = Field(default=0, description="Rate limit violations")
    throttled_requests: int = Field(default=0, description="Throttled requests")

class WebhookDelivery(BaseModel):
    """Webhook delivery attempt tracking."""
    
    # Delivery identification
    delivery_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique delivery identifier")
    webhook_id: str = Field(..., description="Associated webhook ID")
    
    # Event information
    event_type: str = Field(..., description="Event type being delivered")
    event_data: Dict[str, Any] = Field(..., description="Event payload data")
    
    # Delivery attempt
    attempt_number: int = Field(default=1, description="Delivery attempt number")
    status: str = Field(..., description="Delivery status (success, failed, pending)")
    
    # Response information
    http_status: Optional[int] = Field(default=None, description="HTTP response status")
    response_body: Optional[str] = Field(default=None, description="Response body")
    response_headers: Dict[str, str] = Field(default={}, description="Response headers")
    
    # Timing
    sent_at: datetime = Field(default_factory=datetime.utcnow, description="Delivery attempt timestamp")
    response_time_ms: Optional[float] = Field(default=None, description="Response time")
    
    # Error information
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    will_retry: bool = Field(default=False, description="Whether delivery will be retried")
    next_retry_at: Optional[datetime] = Field(default=None, description="Next retry timestamp")

class DeveloperPortalSettings(BaseModel):
    """Settings for the developer portal interface."""
    
    # Portal configuration
    portal_url: str = Field(..., description="Developer portal URL")
    api_docs_url: str = Field(..., description="API documentation URL")
    support_email: EmailStr = Field(..., description="Support contact email")
    
    # Registration settings
    auto_approve_accounts: bool = Field(default=False, description="Auto-approve new accounts")
    require_email_verification: bool = Field(default=True, description="Require email verification")
    default_tier: DeveloperTier = Field(default=DeveloperTier.STARTER, description="Default account tier")
    
    # API key settings
    max_keys_per_project: int = Field(default=5, description="Maximum API keys per project")
    key_expiry_days: int = Field(default=365, description="Default API key expiry in days")
    
    # Rate limiting defaults
    default_rate_limits: RateLimitConfig = Field(default_factory=RateLimitConfig, description="Default rate limits")
    
    # Webhook settings
    webhook_timeout_seconds: int = Field(default=30, description="Default webhook timeout")
    max_webhook_retries: int = Field(default=3, description="Maximum webhook retry attempts")
    
    # SDK generation
    supported_languages: List[str] = Field(default=["python", "javascript", "java", "go"], description="Supported SDK languages")
    sdk_repository_url: str = Field(..., description="SDK repository URL")
    
    # Compliance settings
    require_hipaa_for_medical: bool = Field(default=True, description="Require HIPAA compliance for medical scopes")
    audit_all_requests: bool = Field(default=True, description="Audit all API requests")
    
    # Monitoring settings
    alert_threshold_error_rate: float = Field(default=0.05, description="Error rate alert threshold (5%)")
    alert_threshold_response_time: float = Field(default=5000.0, description="Response time alert threshold (5s)")
    
    # Metadata
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last settings update")