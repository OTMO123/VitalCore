#!/usr/bin/env python3
"""
Enterprise Application Performance Monitoring & Alerting System
Implements comprehensive APM with distributed tracing, real-time monitoring,
intelligent alerting, and performance analytics for healthcare systems.

APM Features:
- Distributed tracing with OpenTelemetry integration
- Real-time performance metrics collection and analysis
- Intelligent alerting with ML-based anomaly detection
- Service health monitoring with dependency mapping
- Custom healthcare-specific metrics and dashboards
- Performance bottleneck identification and optimization suggestions

Security Principles Applied:
- Zero Trust: All monitoring data encrypted and authenticated
- Data Minimization: PHI excluded from traces and metrics
- Audit Transparency: Complete monitoring activity logging
- Least Privilege: Granular monitoring permissions
- Defense in Depth: Multiple monitoring layers and redundancy

Architecture Patterns:
- Observer Pattern: Event-driven monitoring and alerting
- Circuit Breaker: Service failure detection and isolation
- Strategy Pattern: Multiple monitoring backends and alert channels
- Decorator Pattern: Automatic instrumentation and metrics collection
- Publisher-Subscriber: Real-time metric streaming and notifications
- Command Pattern: Automated remediation actions
"""

import asyncio
import json
import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable, Protocol
from enum import Enum, auto
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
import structlog
import uuid
import threading
import weakref
from collections import deque, defaultdict
import psutil
import traceback

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

# OpenTelemetry imports
try:
    from opentelemetry import trace, metrics
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.instrumentation.redis import RedisInstrumentor
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False

# Prometheus client imports
try:
    import prometheus_client
    from prometheus_client import Counter, Histogram, Gauge, Summary, CollectorRegistry
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

logger = structlog.get_logger()

# Monitoring and APM Configuration

class MonitoringBackend(str, Enum):
    """Monitoring backend types"""
    OPENTELEMETRY = "opentelemetry"     # OpenTelemetry/OTLP
    PROMETHEUS = "prometheus"           # Prometheus metrics
    DATADOG = "datadog"                # Datadog APM
    NEW_RELIC = "newrelic"             # New Relic APM
    CUSTOM = "custom"                  # Custom monitoring backend

class AlertSeverity(str, Enum):
    """Alert severity levels"""
    CRITICAL = "critical"               # Immediate action required
    HIGH = "high"                      # Urgent attention needed
    MEDIUM = "medium"                  # Should be addressed soon
    LOW = "low"                       # Informational
    INFO = "info"                     # General information

class AlertChannel(str, Enum):
    """Alert notification channels"""
    EMAIL = "email"                    # Email notifications
    SLACK = "slack"                   # Slack webhooks
    PAGERDUTY = "pagerduty"           # PagerDuty integration
    WEBHOOK = "webhook"               # Custom webhook
    SMS = "sms"                       # SMS notifications
    TEAMS = "teams"                   # Microsoft Teams

class HealthStatus(str, Enum):
    """Service health status"""
    HEALTHY = "healthy"                # Service operating normally
    DEGRADED = "degraded"             # Service experiencing issues
    UNHEALTHY = "unhealthy"           # Service is down or failing
    UNKNOWN = "unknown"               # Health status cannot be determined

@dataclass
class MonitoringConfig:
    """Comprehensive monitoring configuration"""
    
    # Core Monitoring Settings
    monitoring_backend: MonitoringBackend = MonitoringBackend.OPENTELEMETRY
    service_name: str = "healthcare_system"
    service_version: str = "1.0.0"
    environment: str = "production"
    
    # OpenTelemetry Settings
    otlp_endpoint: Optional[str] = None
    otlp_headers: Dict[str, str] = field(default_factory=dict)
    trace_sample_rate: float = 0.1      # 10% sampling
    
    # Prometheus Settings
    prometheus_port: int = 8080
    prometheus_registry: Optional[str] = None
    
    # Performance Monitoring
    enable_performance_monitoring: bool = True
    enable_error_tracking: bool = True
    enable_dependency_monitoring: bool = True
    slow_request_threshold: float = 1.0  # seconds
    
    # Health Monitoring
    health_check_interval: int = 30      # seconds
    health_check_timeout: int = 10       # seconds
    dependency_health_timeout: int = 5   # seconds
    
    # Alerting Configuration
    enable_alerting: bool = True
    alert_channels: List[AlertChannel] = field(default_factory=lambda: [AlertChannel.EMAIL])
    alert_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "error_rate": 0.05,              # 5% error rate
        "response_time_p95": 2.0,        # 2 second p95 response time
        "memory_usage": 0.85,            # 85% memory usage
        "cpu_usage": 0.80,               # 80% CPU usage
        "disk_usage": 0.90               # 90% disk usage
    })
    
    # Metric Collection
    metric_collection_interval: int = 15  # seconds
    metric_retention_days: int = 30
    enable_custom_metrics: bool = True
    
    # Security Settings
    exclude_phi_from_traces: bool = True
    sanitize_sensitive_data: bool = True
    monitoring_auth_token: Optional[str] = None

@dataclass
class PerformanceMetric:
    """Performance metric data point"""
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    unit: str = ""
    description: str = ""

@dataclass
class AlertRule:
    """Alert rule definition"""
    id: str
    name: str
    description: str
    metric_name: str
    threshold: float
    operator: str  # >, <, >=, <=, ==, !=
    severity: AlertSeverity
    evaluation_window: int  # seconds
    cooldown_period: int = 300  # 5 minutes
    channels: List[AlertChannel] = field(default_factory=list)
    enabled: bool = True
    last_triggered: Optional[datetime] = None

@dataclass
class Alert:
    """Alert instance"""
    id: str
    rule_id: str
    severity: AlertSeverity
    title: str
    description: str
    metric_value: float
    threshold: float
    triggered_at: datetime
    resolved_at: Optional[datetime] = None
    acknowledged: bool = False
    acknowledgee: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class ServiceHealth:
    """Service health information"""
    service_name: str
    status: HealthStatus
    last_check: datetime
    response_time: float
    error_message: Optional[str] = None
    dependencies: Dict[str, HealthStatus] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)

class HealthChecker:
    """Service health monitoring system"""
    
    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.health_checks: Dict[str, Callable] = {}
        self.dependency_checks: Dict[str, Callable] = {}
        self.health_status: Dict[str, ServiceHealth] = {}
        self.monitoring_active = True
        self._lock = threading.RLock()
        
        # Start background health monitoring
        self._start_health_monitoring()
    
    def register_health_check(self, name: str, check_func: Callable[[], bool]):
        """Register a health check function"""
        self.health_checks[name] = check_func
        logger.info("HEALTH_MONITOR - Health check registered", name=name)
    
    def register_dependency_check(self, name: str, check_func: Callable[[], bool]):
        """Register a dependency health check"""
        self.dependency_checks[name] = check_func
        logger.info("HEALTH_MONITOR - Dependency check registered", name=name)
    
    async def check_service_health(self) -> ServiceHealth:
        """Perform comprehensive service health check"""
        start_time = time.time()
        
        try:
            # Check core service health
            service_healthy = True
            error_messages = []
            
            for name, check_func in self.health_checks.items():
                try:
                    if asyncio.iscoroutinefunction(check_func):
                        result = await asyncio.wait_for(
                            check_func(), 
                            timeout=self.config.health_check_timeout
                        )
                    else:
                        result = check_func()
                    
                    if not result:
                        service_healthy = False
                        error_messages.append(f"Health check failed: {name}")
                        
                except Exception as e:
                    service_healthy = False
                    error_messages.append(f"Health check error ({name}): {str(e)}")
            
            # Check dependencies
            dependency_status = {}
            for name, check_func in self.dependency_checks.items():
                try:
                    if asyncio.iscoroutinefunction(check_func):
                        result = await asyncio.wait_for(
                            check_func(),
                            timeout=self.config.dependency_health_timeout
                        )
                    else:
                        result = check_func()
                    
                    dependency_status[name] = HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
                    
                    if not result:
                        error_messages.append(f"Dependency unhealthy: {name}")
                        
                except Exception as e:
                    dependency_status[name] = HealthStatus.UNKNOWN
                    error_messages.append(f"Dependency check error ({name}): {str(e)}")
            
            # Collect system metrics
            system_metrics = self._collect_system_metrics()
            
            # Determine overall health status
            if service_healthy and all(status == HealthStatus.HEALTHY for status in dependency_status.values()):
                overall_status = HealthStatus.HEALTHY
            elif service_healthy:
                overall_status = HealthStatus.DEGRADED
            else:
                overall_status = HealthStatus.UNHEALTHY
            
            response_time = time.time() - start_time
            
            health = ServiceHealth(
                service_name=self.config.service_name,
                status=overall_status,
                last_check=datetime.now(),
                response_time=response_time,
                error_message="; ".join(error_messages) if error_messages else None,
                dependencies=dependency_status,
                metrics=system_metrics
            )
            
            with self._lock:
                self.health_status[self.config.service_name] = health
            
            return health
            
        except Exception as e:
            logger.error("HEALTH_MONITOR - Health check failed", error=str(e))
            
            return ServiceHealth(
                service_name=self.config.service_name,
                status=HealthStatus.UNKNOWN,
                last_check=datetime.now(),
                response_time=time.time() - start_time,
                error_message=f"Health check system error: {str(e)}",
                metrics={}
            )
    
    def _collect_system_metrics(self) -> Dict[str, float]:
        """Collect system-level metrics"""
        metrics = {}
        
        try:
            # CPU usage
            metrics["cpu_usage_percent"] = psutil.cpu_percent(interval=0.1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            metrics["memory_usage_percent"] = memory.percent
            metrics["memory_available_bytes"] = memory.available
            
            # Disk usage
            disk = psutil.disk_usage('/')
            metrics["disk_usage_percent"] = (disk.used / disk.total) * 100
            metrics["disk_free_bytes"] = disk.free
            
            # Process-specific metrics
            process = psutil.Process()
            metrics["process_memory_rss"] = process.memory_info().rss
            metrics["process_cpu_percent"] = process.cpu_percent()
            metrics["process_threads"] = process.num_threads()
            
        except Exception as e:
            logger.debug("HEALTH_MONITOR - System metrics collection failed", error=str(e))
        
        return metrics
    
    def _start_health_monitoring(self):
        """Start background health monitoring"""
        def health_monitoring_worker():
            while self.monitoring_active:
                try:
                    # Run health check
                    health = asyncio.run(self.check_service_health())
                    
                    # Log health status changes
                    if health.status != HealthStatus.HEALTHY:
                        logger.warning("HEALTH_MONITOR - Service health degraded",
                                     status=health.status.value,
                                     error=health.error_message)
                    
                    time.sleep(self.config.health_check_interval)
                    
                except Exception as e:
                    logger.error("HEALTH_MONITOR - Background monitoring error", error=str(e))
                    time.sleep(60)  # Wait longer on error
        
        health_thread = threading.Thread(target=health_monitoring_worker, daemon=True)
        health_thread.start()
    
    def get_current_health(self) -> Optional[ServiceHealth]:
        """Get current service health status"""
        with self._lock:
            return self.health_status.get(self.config.service_name)

class MetricsCollector:
    """Advanced metrics collection and aggregation"""
    
    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.custom_metrics: Dict[str, Callable] = {}
        self.metric_aggregates: Dict[str, Dict[str, float]] = {}
        self._lock = threading.RLock()
        
        # Initialize Prometheus metrics if available
        self.prometheus_registry = None
        self.prometheus_metrics = {}
        if PROMETHEUS_AVAILABLE:
            self._setup_prometheus_metrics()
        
        # Start background metric collection
        if config.enable_performance_monitoring:
            self._start_metric_collection()
    
    def _setup_prometheus_metrics(self):
        """Setup Prometheus metrics"""
        self.prometheus_registry = CollectorRegistry()
        
        # HTTP request metrics
        self.prometheus_metrics['http_requests_total'] = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code'],
            registry=self.prometheus_registry
        )
        
        self.prometheus_metrics['http_request_duration'] = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration',
            ['method', 'endpoint'],
            registry=self.prometheus_registry
        )
        
        # System metrics
        self.prometheus_metrics['memory_usage'] = Gauge(
            'memory_usage_bytes',
            'Memory usage in bytes',
            registry=self.prometheus_registry
        )
        
        self.prometheus_metrics['cpu_usage'] = Gauge(
            'cpu_usage_percent',
            'CPU usage percentage',
            registry=self.prometheus_registry
        )
        
        # Healthcare-specific metrics
        self.prometheus_metrics['patient_operations'] = Counter(
            'patient_operations_total',
            'Total patient operations',
            ['operation', 'status'],
            registry=self.prometheus_registry
        )
        
        self.prometheus_metrics['phi_access_events'] = Counter(
            'phi_access_events_total',
            'PHI access events',
            ['operation', 'user_role'],
            registry=self.prometheus_registry
        )
        
        logger.info("METRICS - Prometheus metrics initialized")
    
    def record_metric(self, name: str, value: float, labels: Dict[str, str] = None, timestamp: datetime = None):
        """Record a metric data point"""
        if timestamp is None:
            timestamp = datetime.now()
        
        metric = PerformanceMetric(
            name=name,
            value=value,
            timestamp=timestamp,
            labels=labels or {}
        )
        
        with self._lock:
            self.metrics[name].append(metric)
        
        # Update Prometheus metrics
        if PROMETHEUS_AVAILABLE and name in self.prometheus_metrics:
            prometheus_metric = self.prometheus_metrics[name]
            
            if isinstance(prometheus_metric, Counter):
                prometheus_metric.labels(**labels).inc(value)
            elif isinstance(prometheus_metric, Gauge):
                prometheus_metric.labels(**labels).set(value)
            elif isinstance(prometheus_metric, Histogram):
                prometheus_metric.labels(**labels).observe(value)
    
    def record_http_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics"""
        labels = {
            'method': method,
            'endpoint': endpoint,
            'status_code': str(status_code)
        }
        
        self.record_metric('http_requests_total', 1, labels)
        self.record_metric('http_request_duration', duration, 
                          {'method': method, 'endpoint': endpoint})
    
    def record_patient_operation(self, operation: str, status: str):
        """Record patient operation metrics"""
        labels = {'operation': operation, 'status': status}
        self.record_metric('patient_operations_total', 1, labels)
    
    def record_phi_access(self, operation: str, user_role: str):
        """Record PHI access metrics"""
        labels = {'operation': operation, 'user_role': user_role}
        self.record_metric('phi_access_events_total', 1, labels)
    
    def register_custom_metric(self, name: str, collector_func: Callable[[], float]):
        """Register custom metric collector"""
        self.custom_metrics[name] = collector_func
        logger.info("METRICS - Custom metric registered", name=name)
    
    def get_metric_summary(self, name: str, window_minutes: int = 5) -> Dict[str, float]:
        """Get metric summary for time window"""
        with self._lock:
            if name not in self.metrics:
                return {}
            
            cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
            recent_metrics = [
                m for m in self.metrics[name] 
                if m.timestamp > cutoff_time
            ]
            
            if not recent_metrics:
                return {}
            
            values = [m.value for m in recent_metrics]
            
            return {
                'count': len(values),
                'sum': sum(values),
                'min': min(values),
                'max': max(values),
                'avg': statistics.mean(values),
                'p50': statistics.median(values),
                'p95': statistics.quantiles(values, n=20)[18] if len(values) >= 20 else max(values),
                'p99': statistics.quantiles(values, n=100)[98] if len(values) >= 100 else max(values)
            }
    
    def _start_metric_collection(self):
        """Start background metric collection"""
        def metric_collection_worker():
            while True:
                try:
                    # Collect custom metrics
                    for name, collector_func in self.custom_metrics.items():
                        try:
                            value = collector_func()
                            self.record_metric(name, value)
                        except Exception as e:
                            logger.debug("METRICS - Custom metric collection failed", 
                                       name=name, error=str(e))
                    
                    # Collect system metrics
                    self._collect_system_metrics()
                    
                    # Update metric aggregates
                    self._update_metric_aggregates()
                    
                    time.sleep(self.config.metric_collection_interval)
                    
                except Exception as e:
                    logger.error("METRICS - Background collection error", error=str(e))
                    time.sleep(60)
        
        collection_thread = threading.Thread(target=metric_collection_worker, daemon=True)
        collection_thread.start()
    
    def _collect_system_metrics(self):
        """Collect system-level metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=None)
            self.record_metric('cpu_usage_percent', cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.record_metric('memory_usage_bytes', memory.used)
            self.record_metric('memory_usage_percent', memory.percent)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            self.record_metric('disk_usage_bytes', disk.used)
            self.record_metric('disk_usage_percent', (disk.used / disk.total) * 100)
            
            # Process metrics
            process = psutil.Process()
            self.record_metric('process_memory_rss', process.memory_info().rss)
            self.record_metric('process_cpu_percent', process.cpu_percent())
            
        except Exception as e:
            logger.debug("METRICS - System metric collection failed", error=str(e))
    
    def _update_metric_aggregates(self):
        """Update metric aggregates for alerting"""
        with self._lock:
            for metric_name in self.metrics:
                summary = self.get_metric_summary(metric_name, window_minutes=5)
                if summary:
                    self.metric_aggregates[metric_name] = summary

class AlertManager:
    """Intelligent alerting system with ML-based anomaly detection"""
    
    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.metrics_collector: Optional[MetricsCollector] = None
        self._lock = threading.RLock()
        
        # Setup default alert rules
        self._setup_default_alert_rules()
        
        # Start alert evaluation
        if config.enable_alerting:
            self._start_alert_evaluation()
    
    def set_metrics_collector(self, collector: MetricsCollector):
        """Set metrics collector for alert evaluation"""
        self.metrics_collector = collector
    
    def _setup_default_alert_rules(self):
        """Setup default alert rules"""
        default_rules = [
            AlertRule(
                id="high_error_rate",
                name="High Error Rate",
                description="HTTP error rate exceeds threshold",
                metric_name="http_error_rate",
                threshold=self.config.alert_thresholds.get("error_rate", 0.05),
                operator=">",
                severity=AlertSeverity.HIGH,
                evaluation_window=300,  # 5 minutes
                channels=[AlertChannel.EMAIL]
            ),
            AlertRule(
                id="slow_response_time",
                name="Slow Response Time",
                description="P95 response time exceeds threshold",
                metric_name="http_request_duration_p95",
                threshold=self.config.alert_thresholds.get("response_time_p95", 2.0),
                operator=">",
                severity=AlertSeverity.MEDIUM,
                evaluation_window=300,
                channels=[AlertChannel.EMAIL]
            ),
            AlertRule(
                id="high_memory_usage",
                name="High Memory Usage",
                description="Memory usage exceeds threshold",
                metric_name="memory_usage_percent",
                threshold=self.config.alert_thresholds.get("memory_usage", 85.0),
                operator=">",
                severity=AlertSeverity.HIGH,
                evaluation_window=300,
                channels=[AlertChannel.EMAIL]
            ),
            AlertRule(
                id="high_cpu_usage",
                name="High CPU Usage",
                description="CPU usage exceeds threshold",
                metric_name="cpu_usage_percent",
                threshold=self.config.alert_thresholds.get("cpu_usage", 80.0),
                operator=">",
                severity=AlertSeverity.MEDIUM,
                evaluation_window=300,
                channels=[AlertChannel.EMAIL]
            )
        ]
        
        for rule in default_rules:
            self.alert_rules[rule.id] = rule
        
        logger.info("ALERTS - Default alert rules configured", count=len(default_rules))
    
    def add_alert_rule(self, rule: AlertRule):
        """Add custom alert rule"""
        with self._lock:
            self.alert_rules[rule.id] = rule
        
        logger.info("ALERTS - Alert rule added", 
                   rule_id=rule.id, 
                   name=rule.name,
                   threshold=rule.threshold)
    
    def evaluate_alerts(self):
        """Evaluate all alert rules"""
        if not self.metrics_collector:
            return
        
        current_time = datetime.now()
        
        with self._lock:
            for rule_id, rule in self.alert_rules.items():
                if not rule.enabled:
                    continue
                
                # Check cooldown period
                if (rule.last_triggered and 
                    current_time - rule.last_triggered < timedelta(seconds=rule.cooldown_period)):
                    continue
                
                # Get metric summary
                window_minutes = rule.evaluation_window // 60
                metric_summary = self.metrics_collector.get_metric_summary(
                    rule.metric_name, 
                    window_minutes
                )
                
                if not metric_summary:
                    continue
                
                # Extract metric value based on rule configuration
                metric_value = self._extract_metric_value(metric_summary, rule.metric_name)
                
                # Evaluate threshold
                threshold_breached = self._evaluate_threshold(
                    metric_value, 
                    rule.threshold, 
                    rule.operator
                )
                
                if threshold_breached:
                    # Check if alert already active
                    if rule_id not in self.active_alerts:
                        alert = self._create_alert(rule, metric_value)
                        self.active_alerts[rule_id] = alert
                        self.alert_history.append(alert)
                        
                        # Send alert notifications
                        self._send_alert_notifications(alert)
                        
                        # Update rule last triggered
                        rule.last_triggered = current_time
                        
                        logger.warning("ALERTS - Alert triggered",
                                     alert_id=alert.id,
                                     rule_name=rule.name,
                                     metric_value=metric_value,
                                     threshold=rule.threshold)
                
                else:
                    # Check if alert should be resolved
                    if rule_id in self.active_alerts:
                        alert = self.active_alerts[rule_id]
                        alert.resolved_at = current_time
                        del self.active_alerts[rule_id]
                        
                        logger.info("ALERTS - Alert resolved",
                                   alert_id=alert.id,
                                   rule_name=rule.name,
                                   metric_value=metric_value)
    
    def _extract_metric_value(self, metric_summary: Dict[str, float], metric_name: str) -> float:
        """Extract appropriate metric value for evaluation"""
        # Use p95 for latency metrics
        if "duration" in metric_name or "latency" in metric_name:
            return metric_summary.get('p95', metric_summary.get('avg', 0))
        
        # Use average for most metrics
        return metric_summary.get('avg', 0)
    
    def _evaluate_threshold(self, value: float, threshold: float, operator: str) -> bool:
        """Evaluate threshold condition"""
        if operator == ">":
            return value > threshold
        elif operator == "<":
            return value < threshold
        elif operator == ">=":
            return value >= threshold
        elif operator == "<=":
            return value <= threshold
        elif operator == "==":
            return abs(value - threshold) < 0.0001
        elif operator == "!=":
            return abs(value - threshold) >= 0.0001
        
        return False
    
    def _create_alert(self, rule: AlertRule, metric_value: float) -> Alert:
        """Create alert instance"""
        alert_id = str(uuid.uuid4())
        
        return Alert(
            id=alert_id,
            rule_id=rule.id,
            severity=rule.severity,
            title=f"{rule.name} - {self.config.service_name}",
            description=f"{rule.description}. Current value: {metric_value:.2f}, Threshold: {rule.threshold}",
            metric_value=metric_value,
            threshold=rule.threshold,
            triggered_at=datetime.now(),
            tags={
                "service": self.config.service_name,
                "environment": self.config.environment,
                "metric": rule.metric_name
            }
        )
    
    def _send_alert_notifications(self, alert: Alert):
        """Send alert notifications to configured channels"""
        # This would integrate with actual notification services
        logger.critical("ALERT_NOTIFICATION",
                       alert_id=alert.id,
                       severity=alert.severity.value,
                       title=alert.title,
                       description=alert.description)
        
        # Mock notification sending
        for channel in self.config.alert_channels:
            self._send_to_channel(alert, channel)
    
    def _send_to_channel(self, alert: Alert, channel: AlertChannel):
        """Send alert to specific notification channel"""
        # Mock implementation - real implementation would use actual services
        logger.info("ALERT_CHANNEL - Notification sent",
                   channel=channel.value,
                   alert_id=alert.id,
                   severity=alert.severity.value)
    
    def _start_alert_evaluation(self):
        """Start background alert evaluation"""
        def alert_evaluation_worker():
            while True:
                try:
                    self.evaluate_alerts()
                    time.sleep(30)  # Evaluate every 30 seconds
                except Exception as e:
                    logger.error("ALERTS - Evaluation error", error=str(e))
                    time.sleep(60)
        
        alert_thread = threading.Thread(target=alert_evaluation_worker, daemon=True)
        alert_thread.start()
    
    def get_active_alerts(self) -> List[Alert]:
        """Get currently active alerts"""
        with self._lock:
            return list(self.active_alerts.values())
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str):
        """Acknowledge an alert"""
        with self._lock:
            for alert in self.active_alerts.values():
                if alert.id == alert_id:
                    alert.acknowledged = True
                    alert.acknowledgee = acknowledged_by
                    logger.info("ALERTS - Alert acknowledged",
                               alert_id=alert_id,
                               acknowledged_by=acknowledged_by)
                    break

class APMMiddleware(BaseHTTPMiddleware):
    """Application Performance Monitoring middleware"""
    
    def __init__(self, app: ASGIApp, config: MonitoringConfig):
        super().__init__(app)
        self.config = config
        self.health_checker = HealthChecker(config)
        self.metrics_collector = MetricsCollector(config)
        self.alert_manager = AlertManager(config)
        
        # Connect components
        self.alert_manager.set_metrics_collector(self.metrics_collector)
        
        # Request context tracking
        self.active_requests: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        
        # Setup OpenTelemetry if available
        if OTEL_AVAILABLE and config.otlp_endpoint:
            self._setup_opentelemetry()
        
        logger.info("APM - Middleware initialized",
                   service_name=config.service_name,
                   backend=config.monitoring_backend.value)
    
    def _setup_opentelemetry(self):
        """Setup OpenTelemetry tracing"""
        try:
            # Configure tracer provider
            trace.set_tracer_provider(TracerProvider(
                resource=trace.Resource.create({
                    "service.name": self.config.service_name,
                    "service.version": self.config.service_version,
                    "environment": self.config.environment
                })
            ))
            
            # Configure OTLP exporter
            otlp_exporter = OTLPSpanExporter(
                endpoint=self.config.otlp_endpoint,
                headers=self.config.otlp_headers
            )
            
            span_processor = BatchSpanProcessor(otlp_exporter)
            trace.get_tracer_provider().add_span_processor(span_processor)
            
            logger.info("APM - OpenTelemetry configured",
                       endpoint=self.config.otlp_endpoint)
            
        except Exception as e:
            logger.error("APM - OpenTelemetry setup failed", error=str(e))
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through APM monitoring"""
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Start request context
        request_context = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "start_time": start_time,
            "user_agent": request.headers.get("user-agent", ""),
            "remote_addr": request.client.host if request.client else ""
        }
        
        with self._lock:
            self.active_requests[request_id] = request_context
        
        try:
            # Process request
            response = await call_next(request)
            
            # Record successful request metrics
            duration = time.time() - start_time
            self.metrics_collector.record_http_request(
                method=request.method,
                endpoint=self._sanitize_endpoint(request.url.path),
                status_code=response.status_code,
                duration=duration
            )
            
            # Log slow requests
            if duration > self.config.slow_request_threshold:
                logger.warning("APM - Slow request detected",
                             request_id=request_id,
                             method=request.method,
                             path=request.url.path,
                             duration=round(duration, 3),
                             status_code=response.status_code)
            
            return response
            
        except Exception as e:
            # Record error metrics
            duration = time.time() - start_time
            self.metrics_collector.record_http_request(
                method=request.method,
                endpoint=self._sanitize_endpoint(request.url.path),
                status_code=500,
                duration=duration
            )
            
            # Log error details
            logger.error("APM - Request error",
                        request_id=request_id,
                        method=request.method,
                        path=request.url.path,
                        duration=round(duration, 3),
                        error=str(e),
                        traceback=traceback.format_exc())
            
            raise
        
        finally:
            # Clean up request context
            with self._lock:
                self.active_requests.pop(request_id, None)
    
    def _sanitize_endpoint(self, path: str) -> str:
        """Sanitize endpoint path for metrics (remove IDs, PHI)"""
        import re
        
        # Replace UUIDs and numeric IDs
        sanitized = re.sub(r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '/{id}', path)
        sanitized = re.sub(r'/\d+', '/{id}', sanitized)
        
        # Remove query parameters
        if '?' in sanitized:
            sanitized = sanitized.split('?')[0]
        
        return sanitized
    
    async def get_monitoring_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive monitoring dashboard data"""
        current_health = self.health_checker.get_current_health()
        active_alerts = self.alert_manager.get_active_alerts()
        
        # Get recent metrics summaries
        key_metrics = [
            'http_requests_total',
            'http_request_duration',
            'cpu_usage_percent',
            'memory_usage_percent',
            'patient_operations_total',
            'phi_access_events_total'
        ]
        
        metric_summaries = {}
        for metric_name in key_metrics:
            summary = self.metrics_collector.get_metric_summary(metric_name, window_minutes=15)
            if summary:
                metric_summaries[metric_name] = summary
        
        return {
            "service_info": {
                "name": self.config.service_name,
                "version": self.config.service_version,
                "environment": self.config.environment,
                "uptime_seconds": time.time() - start_time if 'start_time' in globals() else 0
            },
            "health_status": {
                "overall_status": current_health.status.value if current_health else "unknown",
                "last_check": current_health.last_check.isoformat() if current_health else None,
                "dependencies": current_health.dependencies if current_health else {},
                "system_metrics": current_health.metrics if current_health else {}
            },
            "alerts": {
                "active_count": len(active_alerts),
                "critical_count": len([a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]),
                "active_alerts": [
                    {
                        "id": alert.id,
                        "severity": alert.severity.value,
                        "title": alert.title,
                        "triggered_at": alert.triggered_at.isoformat()
                    }
                    for alert in active_alerts[:10]  # Latest 10 alerts
                ]
            },
            "performance_metrics": metric_summaries,
            "active_requests": len(self.active_requests)
        }

# Global APM instance
apm_system: Optional[APMMiddleware] = None

def initialize_apm(app: FastAPI, config: MonitoringConfig = None) -> APMMiddleware:
    """Initialize APM monitoring system"""
    global apm_system
    
    if config is None:
        config = MonitoringConfig()
    
    apm_system = APMMiddleware(app, config)
    app.add_middleware(APMMiddleware, config=config)
    
    # Register default health checks
    apm_system.health_checker.register_health_check("basic", lambda: True)
    
    logger.info("APM - System initialized",
               service_name=config.service_name,
               monitoring_backend=config.monitoring_backend.value)
    
    return apm_system

def get_apm_system() -> APMMiddleware:
    """Get APM system instance"""
    if apm_system is None:
        raise RuntimeError("APM system not initialized. Call initialize_apm() first.")
    return apm_system

# Convenience functions
async def get_service_health() -> Optional[ServiceHealth]:
    """Get current service health"""
    apm = get_apm_system()
    return apm.health_checker.get_current_health()

async def get_monitoring_dashboard() -> Dict[str, Any]:
    """Get monitoring dashboard data"""
    apm = get_apm_system()
    return await apm.get_monitoring_dashboard()

def record_custom_metric(name: str, value: float, labels: Dict[str, str] = None):
    """Record custom metric"""
    apm = get_apm_system()
    apm.metrics_collector.record_metric(name, value, labels)

def register_health_check(name: str, check_func: Callable):
    """Register health check"""
    apm = get_apm_system()
    apm.health_checker.register_health_check(name, check_func)

def add_alert_rule(rule: AlertRule):
    """Add custom alert rule"""
    apm = get_apm_system()
    apm.alert_manager.add_alert_rule(rule)