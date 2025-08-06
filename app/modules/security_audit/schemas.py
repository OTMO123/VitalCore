"""
Security & Audit Dashboard Schemas
Pydantic models for SOC2 Type 2 compliance reporting
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ComplianceStatus(str, Enum):
    """Compliance status indicators."""
    COMPLIANT = "COMPLIANT"
    AT_RISK = "AT_RISK"
    NON_COMPLIANT = "NON_COMPLIANT"


class AlertStatus(str, Enum):
    """Alert status tracking."""
    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    ESCALATED = "ESCALATED"


class AuditLogEntryResponse(BaseModel):
    """Individual audit log entry for dashboard display."""
    id: str
    event_type: str
    user_id: Optional[str]
    action: str
    outcome: str
    timestamp: datetime
    risk_level: str
    phi_involved: bool
    ip_address: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[str]


class DashboardSummary(BaseModel):
    """Summary metrics for audit dashboard."""
    total_events: int = Field(..., description="Total audit events in time period")
    critical_events: int = Field(..., description="Critical security events")
    failed_authentications: int = Field(..., description="Failed login attempts")
    phi_access_events: int = Field(..., description="PHI access events")
    security_score: float = Field(..., ge=0, le=100, description="Overall security score")
    compliance_status: ComplianceStatus = Field(..., description="Current compliance status")


class AlertsSummary(BaseModel):
    """Summary of security alerts."""
    active_alerts: int = Field(..., description="Currently active alerts")
    resolved_today: int = Field(..., description="Alerts resolved today")
    escalated: int = Field(..., description="Escalated alerts")


class TimeSeriesDataPoint(BaseModel):
    """Time series data point for charts."""
    timestamp: str
    total_events: int
    critical_events: int


class AuditDashboardResponse(BaseModel):
    """Main audit dashboard response."""
    summary: DashboardSummary
    recent_events: List[AuditLogEntryResponse]
    time_series: List[TimeSeriesDataPoint]
    alerts_summary: AlertsSummary


class AuthenticationMetrics(BaseModel):
    """Authentication-related security metrics."""
    successful_logins: int
    failed_logins: int
    unique_users: int
    unique_ips: int
    success_rate: float = Field(..., ge=0, le=100)


class PHIAccessMetrics(BaseModel):
    """PHI access security metrics."""
    total_access_events: int
    unique_users: int
    critical_events: int
    compliance_score: float = Field(..., ge=0, le=100)


class SystemSecurityMetrics(BaseModel):
    """System security metrics."""
    critical_events: int
    high_risk_events: int
    failed_operations: int
    avg_response_time: float
    overall_health: str


class SecurityMetricsResponse(BaseModel):
    """Comprehensive security metrics response."""
    authentication: AuthenticationMetrics
    phi_access: PHIAccessMetrics
    system_security: SystemSecurityMetrics
    generated_at: datetime


class ComplianceFinding(BaseModel):
    """Individual compliance finding."""
    control: str = Field(..., description="Control objective (e.g., CC7.2)")
    issue: str = Field(..., description="Description of the finding")
    severity: AlertSeverity = Field(..., description="Severity of the finding")
    recommendation: Optional[str] = Field(None, description="Recommended remediation")


class ComplianceReportResponse(BaseModel):
    """Compliance report response."""
    report_type: str = Field(..., description="Type of compliance report")
    period_start: datetime
    period_end: datetime
    integrity_status: str = Field(..., description="Audit log integrity status")
    compliance_score: float = Field(..., ge=0, le=100)
    findings: List[ComplianceFinding]
    recommendations: List[str]
    generated_by: str
    generated_at: datetime


class RealTimeAlertResponse(BaseModel):
    """Real-time security alert."""
    id: str
    severity: AlertSeverity
    title: str
    description: str
    event_type: str
    user_id: Optional[str]
    ip_address: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[str]
    phi_involved: bool
    timestamp: datetime
    status: AlertStatus = AlertStatus.ACTIVE


class ThreatIntelligenceResponse(BaseModel):
    """Threat intelligence data."""
    threat_level: str
    indicators: List[Dict[str, Any]]
    recommendations: List[str]
    last_updated: datetime


class IntegrityError(BaseModel):
    """Integrity verification error."""
    entry_id: str
    error_type: str
    description: str


class ChainBreak(BaseModel):
    """Audit chain break information."""
    entry_id: str
    expected_previous: str
    actual_previous: str


class IntegrityVerificationResponse(BaseModel):
    """Audit log integrity verification response."""
    status: str = Field(..., description="Overall integrity status")
    entries_checked: int
    integrity_errors: List[IntegrityError]
    signature_errors: List[str]
    chain_breaks: List[ChainBreak]
    verification_timestamp: datetime
    verified_by: str


class AuditSearchRequest(BaseModel):
    """Audit log search request."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    user_id: Optional[str] = None
    event_type: Optional[str] = None
    risk_level: Optional[AlertSeverity] = None
    phi_involved: Optional[bool] = None
    outcome: Optional[str] = None
    ip_address: Optional[str] = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)


class AuditSearchResponse(BaseModel):
    """Audit log search response."""
    results: List[AuditLogEntryResponse]
    total_count: int
    has_more: bool
    query_time_ms: float


class ComplianceControlStatus(BaseModel):
    """Status of individual compliance control."""
    control_id: str
    control_name: str
    status: ComplianceStatus
    last_tested: datetime
    findings_count: int
    score: float


class SOC2ComplianceResponse(BaseModel):
    """SOC2 Type 2 compliance status response."""
    overall_status: ComplianceStatus
    overall_score: float
    controls: List[ComplianceControlStatus]
    period_start: datetime
    period_end: datetime
    assessment_date: datetime


class SecurityPostureResponse(BaseModel):
    """Overall security posture assessment."""
    posture_score: float = Field(..., ge=0, le=100)
    risk_level: str
    top_risks: List[str]
    recommendations: List[str]
    last_assessment: datetime
    next_assessment: datetime


class AuditRetentionPolicy(BaseModel):
    """Audit log retention policy."""
    category: str
    retention_days: int
    archive_after_days: int
    purge_after_days: int
    legal_hold: bool


class AuditRetentionResponse(BaseModel):
    """Audit retention policy response."""
    policies: List[AuditRetentionPolicy]
    total_audit_entries: int
    storage_used_mb: float
    projected_growth_mb: float
    next_purge_date: Optional[datetime]


# Request/Response models for audit log management
class AuditLogCreateRequest(BaseModel):
    """Request to create audit log entry."""
    event_type: str
    category: str
    risk_level: AlertSeverity
    action: str
    outcome: str = "success"
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    additional_data: Dict[str, Any] = {}
    phi_involved: bool = False


class BatchAuditRequest(BaseModel):
    """Batch audit log creation request."""
    events: List[AuditLogCreateRequest]
    batch_id: Optional[str] = None


class AuditExportRequest(BaseModel):
    """Audit log export request."""
    format: str = Field(..., regex="^(csv|json|pdf)$")
    start_date: datetime
    end_date: datetime
    filters: Optional[AuditSearchRequest] = None
    include_phi: bool = False
    encryption_required: bool = True


class AuditExportResponse(BaseModel):
    """Audit log export response."""
    export_id: str
    status: str
    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    estimated_size_mb: float