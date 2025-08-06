from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from enum import Enum

class HealthStatus(str, Enum):
    """Health status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

class SyncStatus(str, Enum):
    """Synchronization status."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"

# ============================================
# IRIS API REQUEST/RESPONSE SCHEMAS
# ============================================

class IRISAuthRequest(BaseModel):
    """IRIS API authentication request."""
    client_id: str = Field(..., description="IRIS client ID")
    client_secret: str = Field(..., description="IRIS client secret")
    scope: Optional[str] = Field(default="read write", description="Requested scopes")

class IRISAuthResponse(BaseModel):
    """IRIS API authentication response."""
    access_token: str = Field(..., description="Access token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiry in seconds")
    scope: Optional[str] = Field(None, description="Granted scopes")
    refresh_token: Optional[str] = Field(None, description="Refresh token")

class IRISPatientRequest(BaseModel):
    """Request schema for patient data from IRIS."""
    patient_id: Optional[str] = Field(None, description="IRIS patient ID")
    mrn: Optional[str] = Field(None, description="Medical record number")
    last_sync_date: Optional[datetime] = Field(None, description="Last synchronization date")
    include_immunizations: bool = Field(default=True, description="Include immunization records")
    include_demographics: bool = Field(default=True, description="Include demographic data")

class IRISPatientResponse(BaseModel):
    """Patient data response from IRIS API."""
    patient_id: str = Field(..., description="IRIS patient ID")
    mrn: Optional[str] = Field(None, description="Medical record number")
    demographics: Optional[Dict[str, Any]] = Field(None, description="Patient demographics")
    immunizations: Optional[List[Dict[str, Any]]] = Field(None, description="Immunization records")
    last_updated: datetime = Field(..., description="Last update timestamp")
    data_version: Optional[str] = Field(None, description="Data version")

class IRISImmunizationRequest(BaseModel):
    """Request schema for immunization data."""
    patient_id: str = Field(..., description="Patient ID")
    vaccine_code: Optional[str] = Field(None, description="Vaccine code filter")
    start_date: Optional[date] = Field(None, description="Start date filter")
    end_date: Optional[date] = Field(None, description="End date filter")

class IRISImmunizationResponse(BaseModel):
    """Immunization record response from IRIS."""
    immunization_id: str = Field(..., description="IRIS immunization ID")
    patient_id: str = Field(..., description="Patient ID")
    vaccine_code: str = Field(..., description="Vaccine code")
    vaccine_name: str = Field(..., description="Vaccine name")
    administration_date: date = Field(..., description="Administration date")
    lot_number: Optional[str] = Field(None, description="Vaccine lot number")
    manufacturer: Optional[str] = Field(None, description="Manufacturer")
    dose_number: Optional[int] = Field(None, description="Dose number in series")
    series_complete: bool = Field(default=False, description="Series completion status")
    administered_by: Optional[str] = Field(None, description="Healthcare provider")
    administration_site: Optional[str] = Field(None, description="Administration site")
    route: Optional[str] = Field(None, description="Administration route")

# ============================================
# API INTEGRATION SCHEMAS
# ============================================

class APIEndpointCreate(BaseModel):
    """Schema for creating API endpoints."""
    name: str = Field(..., min_length=1, max_length=255, description="Endpoint name")
    base_url: str = Field(..., description="Base URL")
    api_version: Optional[str] = Field(None, description="API version")
    auth_type: str = Field(..., description="Authentication type")
    timeout_seconds: int = Field(default=30, ge=1, le=300, description="Timeout")
    retry_attempts: int = Field(default=3, ge=0, le=10, description="Retry attempts")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadata")
    
    @field_validator("auth_type")
    @classmethod
    def validate_auth_type(cls, v):
        allowed_types = ["oauth2", "hmac", "jwt", "api_key", "basic"]
        if v not in allowed_types:
            raise ValueError(f"Auth type must be one of {allowed_types}")
        return v

class APIEndpointResponse(BaseModel):
    """API endpoint response schema."""
    id: str
    name: str
    base_url: str
    api_version: Optional[str]
    status: str
    auth_type: str
    timeout_seconds: int
    retry_attempts: int
    last_health_check_at: Optional[datetime]
    last_health_check_status: Optional[bool]
    metadata: Dict[str, Any]
    created_at: datetime
    
    class Config:
        from_attributes = True

class APICredentialCreate(BaseModel):
    """Schema for creating API credentials."""
    credential_name: str = Field(..., description="Credential name")
    credential_value: str = Field(..., description="Credential value (will be encrypted)")
    expires_at: Optional[datetime] = Field(None, description="Expiration date")

class APICredentialResponse(BaseModel):
    """API credential response schema (excludes sensitive data)."""
    id: str
    credential_name: str
    expires_at: Optional[datetime]
    last_rotated_at: datetime
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class APIRequestCreate(BaseModel):
    """Schema for creating API requests."""
    endpoint_path: str = Field(..., description="API endpoint path")
    method: str = Field(..., description="HTTP method")
    headers: Optional[Dict[str, str]] = Field(default_factory=dict, description="Request headers")
    body: Optional[Dict[str, Any]] = Field(None, description="Request body")
    
    @field_validator("method")
    @classmethod
    def validate_method(cls, v):
        allowed_methods = ["GET", "POST", "PUT", "PATCH", "DELETE"]
        if v.upper() not in allowed_methods:
            raise ValueError(f"Method must be one of {allowed_methods}")
        return v.upper()

class APIRequestResponse(BaseModel):
    """API request response schema."""
    id: str
    correlation_id: str
    method: str
    endpoint_path: str
    status: str
    response_status_code: Optional[int]
    total_duration_ms: Optional[int]
    attempt_count: int
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# ============================================
# HEALTH CHECK SCHEMAS
# ============================================

class HealthCheckRequest(BaseModel):
    """Health check request schema."""
    endpoint_id: Optional[str] = Field(None, description="Specific endpoint to check")
    timeout_seconds: int = Field(default=10, ge=1, le=60, description="Health check timeout")

class HealthCheckResponse(BaseModel):
    """Health check response schema."""
    endpoint_id: str
    endpoint_name: str
    status: HealthStatus
    response_time_ms: Optional[int]
    last_check_at: datetime
    error_message: Optional[str]
    metadata: Dict[str, Any]

class SystemHealthResponse(BaseModel):
    """Overall system health response."""
    overall_status: HealthStatus
    endpoints: List[HealthCheckResponse]
    checked_at: datetime
    summary: Dict[str, Any]

# ============================================
# SYNCHRONIZATION SCHEMAS
# ============================================

class SyncRequest(BaseModel):
    """Data synchronization request."""
    patient_ids: Optional[List[str]] = Field(None, description="Specific patient IDs to sync")
    sync_type: str = Field(default="incremental", description="Sync type")
    force_full_sync: bool = Field(default=False, description="Force full synchronization")
    include_deleted: bool = Field(default=False, description="Include deleted records")
    
    @field_validator("sync_type")
    @classmethod
    def validate_sync_type(cls, v):
        allowed_types = ["incremental", "full", "patient_specific"]
        if v not in allowed_types:
            raise ValueError(f"Sync type must be one of {allowed_types}")
        return v

class SyncResult(BaseModel):
    """Synchronization result."""
    sync_id: str
    status: SyncStatus
    patients_processed: int
    patients_updated: int
    patients_failed: int
    immunizations_processed: int
    immunizations_updated: int
    errors: List[str]
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]

class SyncStatusResponse(BaseModel):
    """Sync status response."""
    sync_id: str
    status: SyncStatus
    progress_percentage: float
    current_operation: Optional[str]
    estimated_completion: Optional[datetime]
    results: Optional[SyncResult]

# ============================================
# ERROR SCHEMAS
# ============================================

class APIError(BaseModel):
    """Standard API error response."""
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    correlation_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ValidationError(BaseModel):
    """Validation error details."""
    field: str
    message: str
    value: Optional[Any] = None

class APIValidationError(APIError):
    """API validation error with field details."""
    validation_errors: List[ValidationError] = Field(default_factory=list)