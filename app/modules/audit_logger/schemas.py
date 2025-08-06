"""
SOC2-Compliant Audit Logging Schemas

Comprehensive event definitions for SOC2 Type II compliance:
- User authentication and authorization events
- Data access and modification tracking
- System configuration changes
- API interactions and integrations
- Security events and violations
- Administrative actions

All events support immutable audit trails with cryptographic integrity.
"""

from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from enum import Enum
import ipaddress

from app.core.event_bus_advanced import BaseEvent, EventPriority

# ============================================
# SOC2 AUDIT EVENT CATEGORIES
# ============================================

class SOC2Category(str, Enum):
    """SOC2 audit categories for compliance reporting."""
    SECURITY = "security"
    AVAILABILITY = "availability"
    PROCESSING_INTEGRITY = "processing_integrity"
    CONFIDENTIALITY = "confidentiality"
    PRIVACY = "privacy"

class AccessType(str, Enum):
    """Types of access for SOC2 tracking."""
    LOGIN = "login"
    LOGOUT = "logout"
    DATA_ACCESS = "data_access"
    DATA_EXPORT = "data_export"
    SYSTEM_ACCESS = "system_access"
    ADMIN_ACCESS = "admin_access"
    API_ACCESS = "api_access"

class DataOperation(str, Enum):
    """Data operations for audit tracking."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXPORT = "export"
    IMPORT = "import"
    BACKUP = "backup"
    RESTORE = "restore"

class SecurityEventType(str, Enum):
    """Security event types."""
    AUTHENTICATION_SUCCESS = "authentication_success"
    AUTHENTICATION_FAILURE = "authentication_failure"
    AUTHORIZATION_SUCCESS = "authorization_success"
    AUTHORIZATION_FAILURE = "authorization_failure"
    PASSWORD_CHANGE = "password_change"
    ACCOUNT_LOCKED = "account_locked"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    SECURITY_VIOLATION = "security_violation"
    PRIVILEGED_ACCESS = "privileged_access"

# ============================================
# BASE AUDIT EVENT
# ============================================

class AuditEvent(BaseEvent):
    """Base audit event with SOC2 compliance fields."""
    
    # SOC2 specific fields
    soc2_category: SOC2Category = Field(..., description="SOC2 compliance category")
    user_id: Optional[str] = Field(None, description="User identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    request_id: Optional[str] = Field(None, description="Request identifier")
    
    # Client information
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")
    geographic_location: Optional[Dict[str, Any]] = Field(None, description="Geographic info")
    device_fingerprint: Optional[str] = Field(None, description="Device fingerprint")
    
    # Resource information
    resource_type: Optional[str] = Field(None, description="Resource type")
    resource_id: Optional[str] = Field(None, description="Resource identifier")
    resource_name: Optional[str] = Field(None, description="Resource name")
    
    # Operation details
    operation: Optional[str] = Field(None, description="Operation performed")
    outcome: str = Field(..., description="Operation outcome (success/failure/error)")
    risk_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Risk assessment score")
    
    # Compliance metadata
    data_classification: Optional[str] = Field(None, description="Data classification level")
    compliance_tags: List[str] = Field(default_factory=list, description="Compliance tags")
    retention_period_days: int = Field(default=2555, description="Retention period (7 years default)")
    
    # Error information
    error_code: Optional[str] = Field(None, description="Error code if applicable")
    error_message: Optional[str] = Field(None, description="Error message")
    
    @field_validator("ip_address")
    @classmethod
    def validate_ip_address(cls, v):
        if v is not None:
            try:
                ipaddress.ip_address(v)
            except ValueError:
                raise ValueError("Invalid IP address format")
        return v
    
    @field_validator("outcome")
    @classmethod
    def validate_outcome(cls, v):
        allowed_outcomes = ["success", "failure", "error", "denied", "partial"]
        if v not in allowed_outcomes:
            raise ValueError(f"Outcome must be one of {allowed_outcomes}")
        return v
    
    def __init__(self, **data):
        # Set default event type if not provided
        if "event_type" not in data:
            data["event_type"] = self.__class__.__name__
        
        # Set default aggregate info for audit events
        if "aggregate_type" not in data:
            data["aggregate_type"] = "audit_log"
        if "aggregate_id" not in data:
            data["aggregate_id"] = data.get("user_id", "system")
        
        # Set high priority for security events
        if "priority" not in data and data.get("soc2_category") == SOC2Category.SECURITY:
            data["priority"] = EventPriority.HIGH
        
        super().__init__(**data)

# ============================================
# AUTHENTICATION & AUTHORIZATION EVENTS
# ============================================

class UserLoginEvent(AuditEvent):
    """User login attempt event."""
    
    soc2_category: SOC2Category = SOC2Category.SECURITY
    username: str = Field(..., description="Username or email")
    login_method: str = Field(..., description="Login method (password/mfa/sso)")
    mfa_enabled: bool = Field(default=False, description="MFA enabled for user")
    account_status: str = Field(..., description="Account status")
    failed_attempts: int = Field(default=0, description="Failed login attempts")
    
class UserLogoutEvent(AuditEvent):
    """User logout event."""
    
    soc2_category: SOC2Category = SOC2Category.SECURITY
    logout_reason: str = Field(..., description="Logout reason (user/timeout/admin)")
    session_duration_seconds: Optional[int] = Field(None, description="Session duration")

class PasswordChangeEvent(AuditEvent):
    """Password change event."""
    
    soc2_category: SOC2Category = SOC2Category.SECURITY
    changed_by_user: bool = Field(..., description="Changed by user or admin")
    password_strength_score: Optional[float] = Field(None, description="Password strength")
    force_change: bool = Field(default=False, description="Forced password change")

class PermissionChangeEvent(AuditEvent):
    """Permission or role change event."""
    
    soc2_category: SOC2Category = SOC2Category.SECURITY
    target_user_id: str = Field(..., description="User whose permissions changed")
    permission_type: str = Field(..., description="Permission type")
    old_permissions: List[str] = Field(default_factory=list, description="Previous permissions")
    new_permissions: List[str] = Field(default_factory=list, description="New permissions")
    changed_by_user_id: str = Field(..., description="User who made the change")

# ============================================
# DATA ACCESS EVENTS
# ============================================

class DataAccessEvent(AuditEvent):
    """Data access tracking event."""
    
    soc2_category: SOC2Category = SOC2Category.CONFIDENTIALITY
    access_type: AccessType = Field(..., description="Type of access")
    data_operation: DataOperation = Field(..., description="Data operation performed")
    record_count: Optional[int] = Field(None, description="Number of records accessed")
    query_parameters: Optional[Dict[str, Any]] = Field(None, description="Query parameters")
    data_sensitivity_level: str = Field(..., description="Data sensitivity classification")
    access_granted: bool = Field(..., description="Whether access was granted")
    access_denied_reason: Optional[str] = Field(None, description="Reason for access denial")

class DataExportEvent(AuditEvent):
    """Data export event."""
    
    soc2_category: SOC2Category = SOC2Category.PRIVACY
    export_format: str = Field(..., description="Export format (csv/json/pdf)")
    export_size_bytes: Optional[int] = Field(None, description="Export file size")
    export_location: Optional[str] = Field(None, description="Export destination")
    encryption_used: bool = Field(..., description="Whether export is encrypted")
    export_purpose: str = Field(..., description="Purpose of export")
    approval_required: bool = Field(default=False, description="Required approval")
    approved_by: Optional[str] = Field(None, description="Approver user ID")

class DataModificationEvent(AuditEvent):
    """Data modification tracking."""
    
    soc2_category: SOC2Category = SOC2Category.PROCESSING_INTEGRITY
    modification_type: DataOperation = Field(..., description="Type of modification")
    fields_modified: List[str] = Field(default_factory=list, description="Modified fields")
    old_values: Optional[Dict[str, Any]] = Field(None, description="Previous values")
    new_values: Optional[Dict[str, Any]] = Field(None, description="New values")
    modification_reason: Optional[str] = Field(None, description="Reason for modification")
    approval_workflow: Optional[str] = Field(None, description="Approval workflow used")

# ============================================
# SYSTEM EVENTS
# ============================================

class SystemConfigurationEvent(AuditEvent):
    """System configuration change event."""
    
    soc2_category: SOC2Category = SOC2Category.SECURITY
    config_section: str = Field(..., description="Configuration section")
    config_key: str = Field(..., description="Configuration key")
    old_value: Optional[str] = Field(None, description="Previous value")
    new_value: Optional[str] = Field(None, description="New value")
    change_reason: str = Field(..., description="Reason for change")
    rollback_possible: bool = Field(..., description="Whether change can be rolled back")

class SystemMaintenanceEvent(AuditEvent):
    """System maintenance event."""
    
    soc2_category: SOC2Category = SOC2Category.AVAILABILITY
    maintenance_type: str = Field(..., description="Type of maintenance")
    maintenance_window: str = Field(..., description="Maintenance window")
    affected_services: List[str] = Field(default_factory=list, description="Affected services")
    downtime_duration_seconds: Optional[int] = Field(None, description="Downtime duration")
    maintenance_status: str = Field(..., description="Maintenance status")

class BackupEvent(AuditEvent):
    """Backup operation event."""
    
    soc2_category: SOC2Category = SOC2Category.AVAILABILITY
    backup_type: str = Field(..., description="Backup type (full/incremental)")
    backup_size_bytes: Optional[int] = Field(None, description="Backup size")
    backup_location: str = Field(..., description="Backup location")
    encryption_used: bool = Field(..., description="Backup encryption")
    verification_status: str = Field(..., description="Backup verification status")
    retention_policy: str = Field(..., description="Backup retention policy")

# ============================================
# API & INTEGRATION EVENTS
# ============================================

class APIRequestEvent(AuditEvent):
    """API request audit event."""
    
    soc2_category: SOC2Category = SOC2Category.SECURITY
    api_endpoint: str = Field(..., description="API endpoint")
    http_method: str = Field(..., description="HTTP method")
    request_size_bytes: Optional[int] = Field(None, description="Request size")
    response_size_bytes: Optional[int] = Field(None, description="Response size")
    response_status_code: int = Field(..., description="HTTP response status")
    response_time_ms: Optional[int] = Field(None, description="Response time")
    api_key_used: Optional[str] = Field(None, description="API key identifier")
    rate_limit_status: Optional[Dict[str, Any]] = Field(None, description="Rate limit info")

class IntegrationEvent(AuditEvent):
    """External integration event."""
    
    soc2_category: SOC2Category = SOC2Category.SECURITY
    integration_name: str = Field(..., description="Integration system name")
    integration_type: str = Field(..., description="Integration type")
    data_direction: str = Field(..., description="Data flow direction (inbound/outbound)")
    data_types: List[str] = Field(default_factory=list, description="Types of data")
    authentication_method: str = Field(..., description="Authentication method")
    encryption_in_transit: bool = Field(..., description="Data encrypted in transit")

# ============================================
# SECURITY EVENTS
# ============================================

class SecurityViolationEvent(AuditEvent):
    """Security violation event."""
    
    soc2_category: SOC2Category = SOC2Category.SECURITY
    violation_type: SecurityEventType = Field(..., description="Type of violation")
    severity_level: str = Field(..., description="Severity level")
    detection_method: str = Field(..., description="How violation was detected")
    automated_response: Optional[str] = Field(None, description="Automated response taken")
    investigation_required: bool = Field(..., description="Requires investigation")
    false_positive_probability: Optional[float] = Field(None, description="False positive probability")

class PrivilegedAccessEvent(AuditEvent):
    """Privileged access event."""
    
    soc2_category: SOC2Category = SOC2Category.SECURITY
    privilege_type: str = Field(..., description="Type of privilege")
    privilege_level: str = Field(..., description="Privilege level")
    access_method: str = Field(..., description="Access method")
    justification: str = Field(..., description="Justification for access")
    approval_required: bool = Field(..., description="Required approval")
    approved_by: Optional[str] = Field(None, description="Approver")
    session_monitored: bool = Field(..., description="Session monitored")

class IncidentEvent(AuditEvent):
    """Security incident event."""
    
    soc2_category: SOC2Category = SOC2Category.SECURITY
    incident_id: str = Field(..., description="Incident identifier")
    incident_type: str = Field(..., description="Incident type")
    severity: str = Field(..., description="Incident severity")
    affected_systems: List[str] = Field(default_factory=list, description="Affected systems")
    incident_status: str = Field(..., description="Incident status")
    assigned_investigator: Optional[str] = Field(None, description="Assigned investigator")
    estimated_impact: Optional[str] = Field(None, description="Estimated impact")

# ============================================
# COMPLIANCE REPORTING SCHEMAS
# ============================================

class ComplianceReport(BaseModel):
    """Compliance report schema."""
    
    report_id: str = Field(..., description="Report identifier")
    report_type: str = Field(..., description="Type of compliance report")
    reporting_period_start: datetime = Field(..., description="Report period start")
    reporting_period_end: datetime = Field(..., description="Report period end")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generated_by: str = Field(..., description="Report generator")
    
    # Report sections
    summary: Dict[str, Any] = Field(default_factory=dict, description="Report summary")
    findings: List[Dict[str, Any]] = Field(default_factory=list, description="Audit findings")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Compliance metrics")
    
    # Metadata
    total_events_analyzed: int = Field(..., description="Total events in report")
    data_sources: List[str] = Field(default_factory=list, description="Data sources")
    export_format: str = Field(..., description="Export format")
    encryption_used: bool = Field(default=True, description="Report encryption")

class AuditLogQuery(BaseModel):
    """Audit log query parameters."""
    
    # Time range
    start_date: Optional[datetime] = Field(None, description="Query start date")
    end_date: Optional[datetime] = Field(None, description="Query end date")
    
    # Filters
    user_id: Optional[str] = Field(None, description="Filter by user")
    event_types: Optional[List[str]] = Field(None, description="Filter by event types")
    soc2_categories: Optional[List[SOC2Category]] = Field(None, description="Filter by SOC2 category")
    outcomes: Optional[List[str]] = Field(None, description="Filter by outcome")
    ip_address: Optional[str] = Field(None, description="Filter by IP address")
    resource_type: Optional[str] = Field(None, description="Filter by resource type")
    
    # Advanced filters
    risk_score_min: Optional[float] = Field(None, description="Minimum risk score")
    compliance_tags: Optional[List[str]] = Field(None, description="Filter by compliance tags")
    
    # Query options
    limit: int = Field(default=1000, le=10000, description="Maximum results")
    offset: int = Field(default=0, description="Result offset")
    sort_by: str = Field(default="timestamp", description="Sort field")
    sort_order: str = Field(default="desc", description="Sort order")
    
    # Export options
    export_format: Optional[str] = Field(None, description="Export format")
    include_raw_data: bool = Field(default=False, description="Include raw event data")

class AuditLogIntegrityReport(BaseModel):
    """Audit log integrity verification report."""
    
    verification_id: str = Field(..., description="Verification run ID")
    start_time: datetime = Field(..., description="Verification start time")
    end_time: datetime = Field(..., description="Verification end time")
    total_events_checked: int = Field(..., description="Total events verified")
    
    # Results
    valid_events: int = Field(..., description="Valid events count")
    invalid_events: int = Field(..., description="Invalid events count")
    missing_events: int = Field(..., description="Missing events count")
    integrity_violations: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Overall status
    integrity_status: str = Field(..., description="Overall integrity status")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    
    @field_validator("integrity_status")
    @classmethod
    def validate_integrity_status(cls, v):
        allowed_statuses = ["clean", "compromised", "suspicious", "unknown"]
        if v not in allowed_statuses:
            raise ValueError(f"Status must be one of {allowed_statuses}")
        return v

# ============================================
# SIEM EXPORT SCHEMAS
# ============================================

class SIEMExportConfig(BaseModel):
    """SIEM export configuration."""
    
    export_name: str = Field(..., description="Export configuration name")
    siem_system: str = Field(..., description="Target SIEM system")
    export_format: str = Field(..., description="Export format (CEF/JSON/CSV)")
    
    # Filtering
    event_types: List[str] = Field(default_factory=list, description="Event types to export")
    soc2_categories: List[SOC2Category] = Field(default_factory=list, description="SOC2 categories")
    minimum_risk_score: Optional[float] = Field(None, description="Minimum risk score")
    
    # Schedule
    export_frequency: str = Field(..., description="Export frequency (realtime/hourly/daily)")
    batch_size: int = Field(default=1000, description="Batch size for exports")
    
    # Destination
    destination_url: Optional[str] = Field(None, description="Destination URL")
    authentication: Dict[str, Any] = Field(default_factory=dict, description="Auth config")
    encryption_required: bool = Field(default=True, description="Require encryption")
    
    # Metadata
    created_by: str = Field(..., description="Creator user ID")
    last_export: Optional[datetime] = Field(None, description="Last export time")
    export_count: int = Field(default=0, description="Total exports performed")

class SIEMEvent(BaseModel):
    """SIEM-formatted event."""
    
    # CEF header fields
    version: str = Field(default="CEF:0", description="CEF version")
    device_vendor: str = Field(default="YourCompany", description="Device vendor")
    device_product: str = Field(default="IRISAPISystem", description="Device product")
    device_version: str = Field(default="1.0", description="Device version")
    signature_id: str = Field(..., description="Event signature ID")
    name: str = Field(..., description="Event name")
    severity: int = Field(..., ge=0, le=10, description="Severity level")
    
    # Extension fields
    extensions: Dict[str, Any] = Field(default_factory=dict, description="CEF extensions")
    
    # Raw event data
    raw_event: Optional[Dict[str, Any]] = Field(None, description="Original event data")
    
    def to_cef(self) -> str:
        """Convert to CEF format."""
        header = f"{self.version}|{self.device_vendor}|{self.device_product}|{self.device_version}|{self.signature_id}|{self.name}|{self.severity}"
        
        if self.extensions:
            ext_string = " ".join(f"{k}={v}" for k, v in self.extensions.items())
            return f"{header}|{ext_string}"
        
        return header