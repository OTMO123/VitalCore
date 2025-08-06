"""
Dashboard API Schemas

Optimized data structures for dashboard performance with minimal API calls.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class DashboardMetric(BaseModel):
    """Individual dashboard metric."""
    name: str
    value: int | float | str
    change: Optional[str] = None  # e.g. "+12 this week"
    change_type: Optional[str] = None  # "increase", "decrease", "neutral"
    trend: Optional[List[float]] = None  # Historical data points
    status: Optional[str] = None  # "healthy", "warning", "critical"
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class SystemHealthSummary(BaseModel):
    """Aggregated system health data."""
    overall_status: str  # "healthy", "degraded", "unhealthy"
    overall_percentage: float
    components: Dict[str, Dict[str, Any]]  # component_name -> {status, details}
    last_check: datetime


class IRISIntegrationSummary(BaseModel):
    """IRIS API integration status summary."""
    status: str  # "healthy", "degraded", "unhealthy"
    endpoints_total: int
    endpoints_healthy: int
    avg_response_time: float
    syncs_today: int
    success_rate: float
    last_sync: Optional[datetime] = None


class SecuritySummary(BaseModel):
    """Security events and audit summary."""
    security_events_today: int  # Actually last 7 days for better visibility
    failed_logins_24h: int      # Actually last 7 days for better visibility  
    phi_access_events: int      # Last 7 days for better visibility
    admin_actions: int          # Last 7 days for better visibility
    total_audit_events_24h: int # Actually last 7 days for better visibility
    critical_alerts: int
    compliance_score: float


class DashboardStats(BaseModel):
    """Complete dashboard statistics in one API call."""
    
    # Core metrics
    total_patients: int
    total_patients_change: Optional[str] = None
    
    system_uptime_percentage: float
    system_uptime_period: str = "Last 30 days"
    
    compliance_score: float
    compliance_details: Dict[str, float]  # HIPAA, SOC2, etc.
    
    security_events_today: int
    
    # Detailed breakdowns
    security_summary: SecuritySummary
    system_health: SystemHealthSummary
    iris_integration: IRISIntegrationSummary
    
    # Timestamps
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    refresh_interval_seconds: int = 30


class DashboardActivity(BaseModel):
    """Recent dashboard activity item."""
    id: str
    title: str
    description: str
    severity: str  # "info", "warning", "error", "critical"
    category: str  # "security", "phi", "admin", "system", "compliance"
    timestamp: datetime
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    status: Optional[str] = None  # "resolved", "pending", "investigating"


class DashboardActivities(BaseModel):
    """Recent activities for dashboard."""
    activities: List[DashboardActivity]
    total_count: int
    categories: Dict[str, int]  # category -> count
    severity_counts: Dict[str, int]  # severity -> count
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class DashboardAlert(BaseModel):
    """System alert for dashboard."""
    id: str
    title: str
    message: str
    severity: str  # "info", "warning", "error", "critical"
    category: str
    created_at: datetime
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    auto_resolve: bool = False
    metadata: Optional[Dict[str, Any]] = None


class DashboardAlerts(BaseModel):
    """System alerts for dashboard."""
    alerts: List[DashboardAlert]
    critical_count: int
    warning_count: int
    info_count: int
    unacknowledged_count: int
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class BulkRefreshRequest(BaseModel):
    """Request for bulk dashboard data refresh."""
    include_stats: bool = True
    include_activities: bool = True
    include_alerts: bool = True
    activity_limit: int = Field(default=50, ge=1, le=200)
    activity_categories: Optional[List[str]] = None
    time_range_hours: int = Field(default=24, ge=1, le=168)  # 1 hour to 1 week


class BulkDashboardResponse(BaseModel):
    """Complete dashboard data in single response."""
    stats: Optional[DashboardStats] = None
    activities: Optional[DashboardActivities] = None
    alerts: Optional[DashboardAlerts] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    cache_expires_at: Optional[datetime] = None


class PerformanceMetrics(BaseModel):
    """Dashboard performance metrics."""
    api_response_time_ms: float
    database_query_time_ms: float
    cache_hit_rate: float
    concurrent_users: int
    requests_per_minute: float
    error_rate: float
    last_measured: datetime = Field(default_factory=datetime.utcnow)


class DashboardHealth(BaseModel):
    """Dashboard-specific health check."""
    status: str  # "healthy", "degraded", "unhealthy"
    database_connected: bool
    redis_connected: bool
    event_bus_connected: bool
    external_apis_healthy: bool
    performance_metrics: PerformanceMetrics
    service_versions: Dict[str, str]
    uptime_seconds: int
    last_restart: datetime
    health_check_timestamp: datetime = Field(default_factory=datetime.utcnow)