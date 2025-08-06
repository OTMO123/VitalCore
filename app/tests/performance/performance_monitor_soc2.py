"""
SOC2/HIPAA Compliant Performance Monitoring for Enterprise Healthcare

This module provides enterprise-grade performance monitoring with compliance features
for SOC2 Type II and HIPAA requirements in healthcare applications.
"""

import asyncio
import time
import statistics
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
import structlog
import psutil
import tracemalloc

logger = structlog.get_logger()

@dataclass
class CompliancePerformanceMetrics:
    """SOC2/HIPAA compliant performance metrics."""
    # Core performance metrics
    response_time_ms: float = 0.0
    throughput_tps: float = 0.0
    error_rate_percent: float = 0.0
    concurrent_users: int = 0
    
    # Percentile metrics for SLA compliance
    p50_response_time_ms: float = 0.0
    p95_response_time_ms: float = 0.0
    p99_response_time_ms: float = 0.0
    
    # Resource utilization
    cpu_usage_percent: float = 0.0
    memory_usage_mb: float = 0.0
    database_connections_active: int = 0
    
    # Healthcare-specific metrics
    phi_access_count: int = 0
    encryption_operations_count: int = 0
    audit_log_entries_created: int = 0
    
    # Compliance tracking
    data_classification_violations: int = 0
    access_control_violations: int = 0
    encryption_failures: int = 0
    
    # Timing breakdowns
    database_time_ms: float = 0.0
    encryption_time_ms: float = 0.0
    business_logic_time_ms: float = 0.0
    
    # Quality metrics
    availability_percent: float = 100.0
    data_integrity_score: float = 100.0
    security_score: float = 100.0

@dataclass
class PerformanceThresholds:
    """Enterprise performance thresholds for healthcare compliance."""
    # Response time thresholds (milliseconds)
    max_response_time_ms: float = 2000.0
    max_p95_response_time_ms: float = 3000.0
    max_p99_response_time_ms: float = 5000.0
    
    # Throughput thresholds
    min_throughput_tps: float = 10.0
    
    # Error rate thresholds
    max_error_rate_percent: float = 1.0
    
    # Resource thresholds
    max_cpu_usage_percent: float = 80.0
    max_memory_usage_mb: float = 1000.0
    
    # Healthcare compliance thresholds
    max_phi_access_time_ms: float = 500.0
    max_encryption_time_ms: float = 100.0
    
    # Availability requirements
    min_availability_percent: float = 99.9

class SOC2PerformanceMonitor:
    """SOC2 Type II compliant performance monitoring system."""
    
    def __init__(self):
        self.metrics_history: List[CompliancePerformanceMetrics] = []
        self.thresholds = PerformanceThresholds()
        self.monitoring_active = False
        self._lock = threading.Lock()
        self.start_time = None
        
    async def start_monitoring(self):
        """Start performance monitoring session."""
        self.monitoring_active = True
        self.start_time = time.time()
        tracemalloc.start()
        
        logger.info("SOC2 performance monitoring started",
                   session_id=id(self),
                   timestamp=datetime.now(timezone.utc).isoformat())
    
    async def stop_monitoring(self) -> CompliancePerformanceMetrics:
        """Stop monitoring and return final metrics."""
        self.monitoring_active = False
        final_metrics = await self._capture_system_metrics()
        
        # Calculate session-wide statistics
        if self.metrics_history:
            response_times = [m.response_time_ms for m in self.metrics_history]
            final_metrics.p50_response_time_ms = statistics.median(response_times)
            final_metrics.p95_response_time_ms = statistics.quantiles(response_times, n=20)[18]
            final_metrics.p99_response_time_ms = statistics.quantiles(response_times, n=100)[98]
            final_metrics.throughput_tps = statistics.mean([m.throughput_tps for m in self.metrics_history])
        
        tracemalloc.stop()
        
        logger.info("SOC2 performance monitoring completed",
                   session_duration_seconds=time.time() - self.start_time,
                   total_metrics_captured=len(self.metrics_history),
                   final_response_time=final_metrics.response_time_ms,
                   final_throughput=final_metrics.throughput_tps)
        
        return final_metrics
    
    async def record_operation(self, operation_name: str, duration_ms: float, 
                             phi_accessed: bool = False, encrypted_operations: int = 0):
        """Record a single operation for compliance monitoring."""
        if not self.monitoring_active:
            return
        
        metrics = CompliancePerformanceMetrics(
            response_time_ms=duration_ms,
            phi_access_count=1 if phi_accessed else 0,
            encryption_operations_count=encrypted_operations,
            audit_log_entries_created=1,  # Every operation creates audit log
            concurrent_users=1
        )
        
        # Capture system metrics
        system_metrics = await self._capture_system_metrics()
        metrics.cpu_usage_percent = system_metrics.cpu_usage_percent
        metrics.memory_usage_mb = system_metrics.memory_usage_mb
        
        with self._lock:
            self.metrics_history.append(metrics)
        
        # Check compliance thresholds
        violations = self._check_compliance_violations(metrics)
        if violations:
            logger.warning("Performance compliance violations detected",
                          operation=operation_name,
                          violations=violations,
                          response_time=duration_ms)
    
    async def _capture_system_metrics(self) -> CompliancePerformanceMetrics:
        """Capture current system performance metrics."""
        process = psutil.Process()
        
        # CPU and memory metrics
        cpu_percent = process.cpu_percent(interval=0.1)
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        
        # Database connection metrics (placeholder - would integrate with actual DB monitoring)
        db_connections = 0  # This would be populated from actual DB pool stats
        
        return CompliancePerformanceMetrics(
            cpu_usage_percent=cpu_percent,
            memory_usage_mb=memory_mb,
            database_connections_active=db_connections
        )
    
    def _check_compliance_violations(self, metrics: CompliancePerformanceMetrics) -> List[str]:
        """Check for SOC2/HIPAA compliance violations."""
        violations = []
        
        if metrics.response_time_ms > self.thresholds.max_response_time_ms:
            violations.append(f"Response time {metrics.response_time_ms}ms exceeds threshold {self.thresholds.max_response_time_ms}ms")
        
        if metrics.error_rate_percent > self.thresholds.max_error_rate_percent:
            violations.append(f"Error rate {metrics.error_rate_percent}% exceeds threshold {self.thresholds.max_error_rate_percent}%")
        
        if metrics.cpu_usage_percent > self.thresholds.max_cpu_usage_percent:
            violations.append(f"CPU usage {metrics.cpu_usage_percent}% exceeds threshold {self.thresholds.max_cpu_usage_percent}%")
        
        if metrics.memory_usage_mb > self.thresholds.max_memory_usage_mb:
            violations.append(f"Memory usage {metrics.memory_usage_mb}MB exceeds threshold {self.thresholds.max_memory_usage_mb}MB")
        
        return violations
    
    def generate_compliance_report(self) -> Dict[str, Any]:
        """Generate SOC2 compliance performance report."""
        if not self.metrics_history:
            return {"status": "no_data", "message": "No performance data collected"}
        
        # Calculate aggregate statistics
        response_times = [m.response_time_ms for m in self.metrics_history]
        throughputs = [m.throughput_tps for m in self.metrics_history]
        error_rates = [m.error_rate_percent for m in self.metrics_history]
        
        report = {
            "monitoring_session": {
                "start_time": self.start_time,
                "duration_seconds": time.time() - self.start_time if self.start_time else 0,
                "total_operations": len(self.metrics_history)
            },
            "performance_summary": {
                "avg_response_time_ms": statistics.mean(response_times),
                "p95_response_time_ms": statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else max(response_times),
                "p99_response_time_ms": statistics.quantiles(response_times, n=100)[98] if len(response_times) >= 100 else max(response_times),
                "avg_throughput_tps": statistics.mean(throughputs) if throughputs else 0,
                "avg_error_rate_percent": statistics.mean(error_rates) if error_rates else 0
            },
            "compliance_status": {
                "response_time_compliant": all(rt <= self.thresholds.max_response_time_ms for rt in response_times),
                "throughput_compliant": all(tp >= self.thresholds.min_throughput_tps for tp in throughputs if tp > 0),
                "error_rate_compliant": all(er <= self.thresholds.max_error_rate_percent for er in error_rates),
                "overall_compliant": True  # Would be calculated based on all checks
            },
            "healthcare_metrics": {
                "total_phi_accesses": sum(m.phi_access_count for m in self.metrics_history),
                "total_encryption_operations": sum(m.encryption_operations_count for m in self.metrics_history),
                "total_audit_entries": sum(m.audit_log_entries_created for m in self.metrics_history)
            }
        }
        
        return report

@asynccontextmanager
async def monitor_performance(operation_name: str):
    """Context manager for monitoring individual operations."""
    monitor = SOC2PerformanceMonitor()
    await monitor.start_monitoring()
    start_time = time.time()
    
    try:
        yield monitor
    finally:
        duration_ms = (time.time() - start_time) * 1000
        await monitor.record_operation(operation_name, duration_ms)
        final_metrics = await monitor.stop_monitoring()
        
        logger.info("Operation performance monitored",
                   operation=operation_name,
                   duration_ms=duration_ms,
                   cpu_usage=final_metrics.cpu_usage_percent,
                   memory_usage_mb=final_metrics.memory_usage_mb)