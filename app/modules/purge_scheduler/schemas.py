"""
Intelligent Purge Scheduler Schemas

Comprehensive data retention and purge management with:
- Configurable retention policies per data type
- Override conditions (legal holds, investigations)
- Cascade deletion with dependency tracking
- Emergency suspension mechanisms
- Compliance-aware scheduling
"""

from pydantic import BaseModel, Field, validator, root_validator
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
from enum import Enum
import uuid

# ============================================
# PURGE ENUMS AND TYPES
# ============================================

class PurgeStrategy(str, Enum):
    """Purge execution strategies."""
    HARD_DELETE = "hard_delete"
    SOFT_DELETE = "soft_delete"
    ARCHIVE = "archive"
    ANONYMIZE = "anonymize"

class RetentionTrigger(str, Enum):
    """Retention policy triggers."""
    TIME_BASED = "time_based"
    EVENT_BASED = "event_based"
    SIZE_BASED = "size_based"
    CUSTOM = "custom"

class OverrideReason(str, Enum):
    """Retention override reasons."""
    LEGAL_HOLD = "legal_hold"
    ACTIVE_INVESTIGATION = "active_investigation"
    COMPLIANCE_AUDIT = "compliance_audit"
    USER_REQUEST = "user_request"
    SYSTEM_DEPENDENCY = "system_dependency"
    REGULATORY_REQUIREMENT = "regulatory_requirement"

class PurgeStatus(str, Enum):
    """Purge execution status."""
    SCHEDULED = "scheduled"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    OVERRIDDEN = "overridden"
    SUSPENDED = "suspended"

class DataClassification(str, Enum):
    """Data classification levels."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    PHI = "phi"
    PII = "pii"

# ============================================
# RETENTION POLICY SCHEMAS
# ============================================

class RetentionRule(BaseModel):
    """Individual retention rule configuration."""
    
    rule_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Descriptive name for the rule")
    description: Optional[str] = Field(None, description="Detailed description")
    
    # Trigger configuration
    trigger_type: RetentionTrigger = Field(..., description="What triggers retention")
    retention_period_days: int = Field(..., ge=1, description="Days to retain data")
    
    # Scope configuration
    table_name: str = Field(..., description="Target table name")
    filter_conditions: Optional[Dict[str, Any]] = Field(None, description="SQL filter conditions")
    data_classification: Optional[DataClassification] = Field(None, description="Data classification filter")
    
    # Execution configuration
    purge_strategy: PurgeStrategy = Field(default=PurgeStrategy.SOFT_DELETE)
    archive_location: Optional[str] = Field(None, description="Archive destination")
    anonymization_config: Optional[Dict[str, Any]] = Field(None, description="Anonymization rules")
    
    # Dependencies
    dependent_tables: List[str] = Field(default_factory=list, description="Tables that depend on this data")
    cascade_delete: bool = Field(default=False, description="Delete dependent records")
    
    # Override handling
    allow_overrides: bool = Field(default=True, description="Allow retention overrides")
    override_approval_required: bool = Field(default=True, description="Require approval for overrides")
    
    # Compliance
    compliance_tags: List[str] = Field(default_factory=list, description="Compliance requirements")
    regulatory_basis: Optional[str] = Field(None, description="Legal/regulatory basis")
    
    @validator("archive_location")
    def validate_archive_location(cls, v, values):
        if values.get("purge_strategy") == PurgeStrategy.ARCHIVE and not v:
            raise ValueError("Archive location required for archive strategy")
        return v
    
    @validator("anonymization_config")
    def validate_anonymization_config(cls, v, values):
        if values.get("purge_strategy") == PurgeStrategy.ANONYMIZE and not v:
            raise ValueError("Anonymization config required for anonymize strategy")
        return v

class RetentionPolicy(BaseModel):
    """Complete retention policy with multiple rules."""
    
    policy_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Policy name")
    description: Optional[str] = Field(None, description="Policy description")
    version: int = Field(default=1, description="Policy version")
    
    # Rules
    rules: List[RetentionRule] = Field(..., min_items=1, description="Retention rules")
    
    # Scheduling
    schedule_expression: str = Field(default="0 2 * * *", description="Cron expression for execution")
    timezone: str = Field(default="UTC", description="Timezone for scheduling")
    execution_window_hours: int = Field(default=4, ge=1, le=12, description="Max execution window")
    
    # Execution configuration
    batch_size: int = Field(default=1000, ge=1, le=10000, description="Records per batch")
    max_concurrent_batches: int = Field(default=5, ge=1, le=20, description="Concurrent batches")
    dry_run_first: bool = Field(default=True, description="Always do dry run first")
    
    # Safety mechanisms
    max_records_per_execution: Optional[int] = Field(None, description="Safety limit on records processed")
    confirmation_required: bool = Field(default=True, description="Require manual confirmation")
    emergency_suspension_enabled: bool = Field(default=True, description="Allow emergency suspension")
    
    # Monitoring
    enable_notifications: bool = Field(default=True, description="Send execution notifications")
    notification_recipients: List[str] = Field(default_factory=list, description="Email recipients")
    
    # Metadata
    created_by: str = Field(..., description="Creator user ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: Optional[str] = Field(None, description="Last updater user ID")
    updated_at: Optional[datetime] = Field(None, description="Last update time")
    is_active: bool = Field(default=True, description="Policy is active")
    
    @validator("rules")
    def validate_rules_uniqueness(cls, v):
        table_names = [rule.table_name for rule in v]
        if len(table_names) != len(set(table_names)):
            raise ValueError("Multiple rules for the same table not allowed in single policy")
        return v

# ============================================
# OVERRIDE SCHEMAS
# ============================================

class RetentionOverride(BaseModel):
    """Retention override for specific records."""
    
    override_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    table_name: str = Field(..., description="Target table")
    record_id: str = Field(..., description="Record identifier")
    
    # Override details
    reason: OverrideReason = Field(..., description="Override reason")
    description: str = Field(..., description="Detailed explanation")
    override_until: Optional[datetime] = Field(None, description="Override expiry date")
    indefinite: bool = Field(default=False, description="Indefinite override")
    
    # Approval workflow
    requested_by: str = Field(..., description="Requester user ID")
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    approval_required: bool = Field(default=True, description="Requires approval")
    approved_by: Optional[str] = Field(None, description="Approver user ID")
    approved_at: Optional[datetime] = Field(None, description="Approval timestamp")
    approval_notes: Optional[str] = Field(None, description="Approval notes")
    
    # Legal/compliance
    legal_reference: Optional[str] = Field(None, description="Legal case/reference number")
    compliance_requirement: Optional[str] = Field(None, description="Compliance requirement")
    
    # Status
    status: str = Field(default="pending", description="Override status")
    is_active: bool = Field(default=True, description="Override is active")
    
    @root_validator
    def validate_override_duration(cls, values):
        if values.get("indefinite") and values.get("override_until"):
            raise ValueError("Cannot have both indefinite flag and expiry date")
        if not values.get("indefinite") and not values.get("override_until"):
            raise ValueError("Must specify either indefinite flag or expiry date")
        return values

class BulkOverrideRequest(BaseModel):
    """Bulk override request for multiple records."""
    
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    table_name: str = Field(..., description="Target table")
    filter_criteria: Dict[str, Any] = Field(..., description="Filter for bulk selection")
    
    # Override details
    reason: OverrideReason = Field(..., description="Override reason")
    description: str = Field(..., description="Detailed explanation")
    override_until: Optional[datetime] = Field(None, description="Override expiry date")
    indefinite: bool = Field(default=False, description="Indefinite override")
    
    # Approval
    requested_by: str = Field(..., description="Requester user ID")
    max_records: int = Field(default=1000, ge=1, le=10000, description="Maximum records to override")
    
    # Processing
    estimated_count: Optional[int] = Field(None, description="Estimated records affected")
    actual_count: Optional[int] = Field(None, description="Actual records processed")
    status: str = Field(default="pending", description="Request status")

# ============================================
# EXECUTION SCHEMAS
# ============================================

class PurgeExecution(BaseModel):
    """Purge execution record."""
    
    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    policy_id: str = Field(..., description="Source retention policy")
    rule_id: str = Field(..., description="Specific rule being executed")
    
    # Execution metadata
    execution_type: str = Field(..., description="Execution type (scheduled/manual/dry_run)")
    scheduled_at: datetime = Field(..., description="Scheduled execution time")
    started_at: Optional[datetime] = Field(None, description="Actual start time")
    completed_at: Optional[datetime] = Field(None, description="Completion time")
    
    # Status tracking
    status: PurgeStatus = Field(default=PurgeStatus.SCHEDULED)
    progress_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    current_batch: int = Field(default=0, description="Current batch number")
    total_batches: Optional[int] = Field(None, description="Total batches to process")
    
    # Results
    records_identified: int = Field(default=0, description="Records identified for purge")
    records_processed: int = Field(default=0, description="Records successfully processed")
    records_failed: int = Field(default=0, description="Records that failed processing")
    records_skipped: int = Field(default=0, description="Records skipped due to overrides")
    
    # Error handling
    error_message: Optional[str] = Field(None, description="Error description if failed")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Detailed error information")
    retry_count: int = Field(default=0, description="Number of retries attempted")
    
    # Configuration
    execution_config: Dict[str, Any] = Field(default_factory=dict, description="Execution parameters")
    dry_run: bool = Field(default=False, description="Dry run execution")
    
    # Approval and confirmation
    requires_confirmation: bool = Field(default=True, description="Requires manual confirmation")
    confirmed_by: Optional[str] = Field(None, description="User who confirmed execution")
    confirmed_at: Optional[datetime] = Field(None, description="Confirmation timestamp")
    
    # Monitoring
    executed_by: Optional[str] = Field(None, description="User who triggered execution")
    monitoring_url: Optional[str] = Field(None, description="Monitoring dashboard URL")

class PurgeBatch(BaseModel):
    """Individual purge batch within an execution."""
    
    batch_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    execution_id: str = Field(..., description="Parent execution ID")
    batch_number: int = Field(..., description="Batch sequence number")
    
    # Batch data
    record_ids: List[str] = Field(..., description="Record IDs in this batch")
    batch_size: int = Field(..., description="Number of records in batch")
    
    # Processing
    started_at: Optional[datetime] = Field(None, description="Batch start time")
    completed_at: Optional[datetime] = Field(None, description="Batch completion time")
    status: PurgeStatus = Field(default=PurgeStatus.SCHEDULED)
    
    # Results
    successful_records: List[str] = Field(default_factory=list, description="Successfully processed")
    failed_records: List[str] = Field(default_factory=list, description="Failed to process")
    skipped_records: List[str] = Field(default_factory=list, description="Skipped due to overrides")
    
    # Error tracking
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Individual record errors")
    retry_attempts: int = Field(default=0, description="Retry attempts for this batch")

# ============================================
# REPORTING SCHEMAS
# ============================================

class PurgeReport(BaseModel):
    """Comprehensive purge execution report."""
    
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    report_type: str = Field(..., description="Report type")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generated_by: str = Field(..., description="Report generator")
    
    # Report period
    period_start: datetime = Field(..., description="Report period start")
    period_end: datetime = Field(..., description="Report period end")
    
    # Summary statistics
    total_executions: int = Field(default=0, description="Total executions in period")
    successful_executions: int = Field(default=0, description="Successful executions")
    failed_executions: int = Field(default=0, description="Failed executions")
    total_records_purged: int = Field(default=0, description="Total records purged")
    
    # Breakdown by policy
    policy_statistics: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="Statistics per policy"
    )
    
    # Breakdown by table
    table_statistics: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="Statistics per table"
    )
    
    # Override statistics
    override_statistics: Dict[str, int] = Field(
        default_factory=dict, description="Override usage statistics"
    )
    
    # Compliance metrics
    compliance_metrics: Dict[str, Any] = Field(
        default_factory=dict, description="Compliance-related metrics"
    )
    
    # Performance metrics
    performance_metrics: Dict[str, Any] = Field(
        default_factory=dict, description="Performance statistics"
    )
    
    # Issues and recommendations
    issues_identified: List[str] = Field(default_factory=list, description="Issues found")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")

class RetentionDashboard(BaseModel):
    """Dashboard data for retention management."""
    
    dashboard_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Active policies
    active_policies: int = Field(default=0, description="Number of active policies")
    total_rules: int = Field(default=0, description="Total retention rules")
    
    # Upcoming executions
    next_24h_executions: int = Field(default=0, description="Executions in next 24 hours")
    next_week_executions: int = Field(default=0, description="Executions in next week")
    
    # Current overrides
    active_overrides: int = Field(default=0, description="Active retention overrides")
    pending_approvals: int = Field(default=0, description="Pending override approvals")
    expiring_overrides: int = Field(default=0, description="Overrides expiring soon")
    
    # Recent activity
    recent_executions: List[Dict[str, Any]] = Field(
        default_factory=list, description="Recent executions"
    )
    recent_overrides: List[Dict[str, Any]] = Field(
        default_factory=list, description="Recent overrides"
    )
    
    # Alerts and warnings
    alerts: List[Dict[str, str]] = Field(default_factory=list, description="Active alerts")
    warnings: List[Dict[str, str]] = Field(default_factory=list, description="Active warnings")
    
    # Storage metrics
    data_growth_rate: Optional[float] = Field(None, description="Data growth rate per day")
    projected_purge_volume: Optional[int] = Field(None, description="Projected records to purge")
    
    # Compliance status
    compliance_status: Dict[str, str] = Field(
        default_factory=dict, description="Compliance status by requirement"
    )

# ============================================
# CONFIGURATION SCHEMAS
# ============================================

class PurgeSchedulerConfig(BaseModel):
    """Global purge scheduler configuration."""
    
    config_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    version: int = Field(default=1, description="Configuration version")
    
    # Global settings
    enabled: bool = Field(default=True, description="Purge scheduler enabled")
    maintenance_mode: bool = Field(default=False, description="Maintenance mode")
    
    # Execution limits
    max_concurrent_executions: int = Field(default=3, ge=1, le=10, description="Max concurrent executions")
    max_records_per_hour: int = Field(default=100000, description="Max records processed per hour")
    execution_timeout_hours: int = Field(default=12, description="Max execution time")
    
    # Safety mechanisms
    emergency_suspension_enabled: bool = Field(default=True, description="Emergency suspension enabled")
    automatic_dry_run: bool = Field(default=True, description="Always dry run first")
    confirmation_timeout_hours: int = Field(default=24, description="Confirmation timeout")
    
    # Monitoring
    health_check_interval_minutes: int = Field(default=5, description="Health check interval")
    metrics_retention_days: int = Field(default=90, description="Metrics retention period")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Notifications
    notification_channels: List[str] = Field(
        default_factory=list, description="Notification channels"
    )
    alert_thresholds: Dict[str, float] = Field(
        default_factory=dict, description="Alert thresholds"
    )
    
    # Integration settings
    database_pool_size: int = Field(default=10, description="Database connection pool size")
    redis_url: Optional[str] = Field(None, description="Redis URL for caching")
    
    # Compliance
    audit_all_operations: bool = Field(default=True, description="Audit all operations")
    require_dual_approval: bool = Field(default=False, description="Require dual approval")
    
    # Metadata
    updated_by: str = Field(..., description="Last updater")
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# ============================================
# API REQUEST/RESPONSE SCHEMAS
# ============================================

class CreatePolicyRequest(BaseModel):
    """Request to create new retention policy."""
    name: str = Field(..., description="Policy name")
    description: Optional[str] = Field(None, description="Policy description")
    rules: List[RetentionRule] = Field(..., min_items=1, description="Retention rules")
    schedule_expression: str = Field(default="0 2 * * *", description="Cron expression")
    notification_recipients: List[str] = Field(default_factory=list, description="Email recipients")

class PolicyResponse(BaseModel):
    """Retention policy response."""
    policy: RetentionPolicy
    status: str = Field(default="active", description="Policy status")
    next_execution: Optional[datetime] = Field(None, description="Next scheduled execution")
    last_execution: Optional[Dict[str, Any]] = Field(None, description="Last execution info")

class ExecutionRequest(BaseModel):
    """Manual execution request."""
    policy_id: str = Field(..., description="Policy to execute")
    rule_ids: Optional[List[str]] = Field(None, description="Specific rules to execute")
    dry_run: bool = Field(default=True, description="Dry run execution")
    force: bool = Field(default=False, description="Force execution without confirmation")
    batch_size: Optional[int] = Field(None, description="Override batch size")

class OverrideRequest(BaseModel):
    """Retention override request."""
    table_name: str = Field(..., description="Target table")
    record_id: str = Field(..., description="Record ID")
    reason: OverrideReason = Field(..., description="Override reason")
    description: str = Field(..., description="Detailed explanation")
    override_until: Optional[datetime] = Field(None, description="Override expiry")
    indefinite: bool = Field(default=False, description="Indefinite override")
    legal_reference: Optional[str] = Field(None, description="Legal reference")

class SystemStatusResponse(BaseModel):
    """System status response."""
    status: str = Field(..., description="Overall system status")
    scheduler_running: bool = Field(..., description="Scheduler is running")
    active_executions: int = Field(..., description="Currently active executions")
    pending_executions: int = Field(..., description="Pending executions")
    emergency_suspended: bool = Field(..., description="Emergency suspension active")
    last_health_check: datetime = Field(..., description="Last health check time")
    version: str = Field(..., description="System version")
    uptime_seconds: int = Field(..., description="System uptime")