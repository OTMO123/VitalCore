"""
SOC2 Type 2 Compliant Circuit Breaker for Critical Security Components

This module ensures continuous security monitoring and audit logging
even during system failures, meeting SOC2 availability and monitoring requirements.
"""

import asyncio
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class CircuitState(Enum):
    """Circuit breaker states for SOC2 monitoring"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failures detected, circuit open
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """SOC2-compliant circuit breaker configuration"""
    failure_threshold: int = 5          # SOC2: Quick failure detection
    success_threshold: int = 3          # SOC2: Conservative recovery
    timeout_seconds: int = 30           # SOC2: Fast recovery attempt
    monitoring_window_seconds: int = 60 # SOC2: Monitoring window


@dataclass
class CircuitBreakerMetrics:
    """SOC2 audit metrics for circuit breaker"""
    component_name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    circuit_opens: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    current_state: CircuitState = CircuitState.CLOSED
    uptime_percentage: float = 100.0


class SOC2CircuitBreakerException(Exception):
    """Exception raised when circuit breaker is open"""
    def __init__(self, component_name: str, failure_count: int):
        self.component_name = component_name
        self.failure_count = failure_count
        super().__init__(f"Circuit breaker OPEN for {component_name} after {failure_count} failures")


class SOC2CircuitBreaker:
    """
    SOC2 Type 2 compliant circuit breaker for critical security components.
    
    Ensures continuous monitoring and audit logging capabilities
    with automated failover and recovery mechanisms.
    """
    
    def __init__(
        self, 
        component_name: str,
        config: Optional[CircuitBreakerConfig] = None,
        backup_handler: Optional[Callable] = None
    ):
        self.component_name = component_name
        self.config = config or CircuitBreakerConfig()
        self.backup_handler = backup_handler
        
        # Circuit breaker state
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.last_request_time: Optional[float] = None
        
        # SOC2 metrics tracking
        self.metrics = CircuitBreakerMetrics(component_name=component_name)
        
        # SOC2 audit logging
        self._log_circuit_breaker_initialization()
    
    def _log_circuit_breaker_initialization(self):
        """SOC2 Audit: Log circuit breaker initialization"""
        logger.info(
            "SOC2 Circuit Breaker Initialized",
            component=self.component_name,
            failure_threshold=self.config.failure_threshold,
            success_threshold=self.config.success_threshold,
            timeout_seconds=self.config.timeout_seconds,
            soc2_control="CC7.2",  # SOC2 System Monitoring
            event_type="circuit_breaker_init"
        )
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        SOC2 Requirements:
        - Track all requests for availability metrics
        - Provide automatic failover for critical security functions
        - Maintain audit trail of all circuit breaker events
        """
        request_start_time = time.time()
        self.last_request_time = request_start_time
        self.metrics.total_requests += 1
        
        # SOC2: Check if circuit should be closed
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to_half_open()
            else:
                await self._handle_circuit_open()
                raise SOC2CircuitBreakerException(self.component_name, self.failure_count)
        
        try:
            # Execute the function
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            
            # SOC2: Record successful operation
            await self._record_success(request_start_time)
            return result
            
        except Exception as e:
            # SOC2: Record failure and check circuit state
            await self._record_failure(e, request_start_time)
            
            # If we have a backup handler for critical security functions
            if self.backup_handler and self._is_critical_security_function():
                logger.warning(
                    "SOC2 Critical Security Function Failed - Executing Backup",
                    component=self.component_name,
                    error=str(e),
                    backup_handler_active=True,
                    soc2_control="CC6.1"  # SOC2 Logical Access Controls
                )
                return await self.backup_handler(*args, **kwargs)
            
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True
        
        time_since_failure = time.time() - self.last_failure_time
        return time_since_failure >= self.config.timeout_seconds
    
    def _transition_to_half_open(self):
        """Transition circuit to half-open state for testing"""
        self.state = CircuitState.HALF_OPEN
        logger.info(
            "SOC2 Circuit Breaker Transition to HALF_OPEN",
            component=self.component_name,
            previous_state="OPEN",
            failure_count=self.failure_count,
            soc2_control="CC7.2",
            event_type="circuit_state_change"
        )
    
    async def _handle_circuit_open(self):
        """Handle circuit breaker open state - SOC2 logging and alerting"""
        logger.error(
            "SOC2 Circuit Breaker OPEN - Service Unavailable",
            component=self.component_name,
            failure_count=self.failure_count,
            time_since_last_failure=time.time() - (self.last_failure_time or 0),
            soc2_control="A1.2",  # SOC2 Availability Controls
            event_type="circuit_open",
            requires_immediate_attention=True
        )
        
        # SOC2: Update availability metrics
        self._update_availability_metrics()
    
    async def _record_success(self, request_start_time: float):
        """Record successful operation for SOC2 metrics"""
        response_time = time.time() - request_start_time
        
        self.metrics.successful_requests += 1
        self.metrics.last_success_time = datetime.utcnow()
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self._close_circuit()
        
        # SOC2: Log successful operation
        logger.debug(
            "SOC2 Circuit Breaker Success",
            component=self.component_name,
            response_time_ms=round(response_time * 1000, 2),
            state=self.state.value,
            success_count=self.success_count,
            soc2_control="CC7.2"
        )
    
    async def _record_failure(self, error: Exception, request_start_time: float):
        """Record failed operation for SOC2 metrics"""
        response_time = time.time() - request_start_time
        
        self.failure_count += 1
        self.last_failure_time = time.time()
        self.metrics.failed_requests += 1
        self.metrics.last_failure_time = datetime.utcnow()
        
        # SOC2: Critical security component failure logging
        logger.error(
            "SOC2 Circuit Breaker Failure",
            component=self.component_name,
            error_type=type(error).__name__,
            error_message=str(error),
            failure_count=self.failure_count,
            response_time_ms=round(response_time * 1000, 2),
            state=self.state.value,
            soc2_control="CC7.2",
            event_type="component_failure"
        )
        
        # Check if we should open the circuit
        if self.failure_count >= self.config.failure_threshold:
            await self._open_circuit()
    
    async def _open_circuit(self):
        """Open circuit breaker - critical SOC2 event"""
        previous_state = self.state
        self.state = CircuitState.OPEN
        self.metrics.circuit_opens += 1
        
        logger.critical(
            "SOC2 CRITICAL: Circuit Breaker OPENED",
            component=self.component_name,
            previous_state=previous_state.value,
            failure_count=self.failure_count,
            failure_threshold=self.config.failure_threshold,
            soc2_control="A1.2",  # SOC2 Availability
            event_type="circuit_opened",
            requires_immediate_response=True,
            escalation_required=self._is_critical_security_function()
        )
        
        # SOC2: Update availability metrics
        self._update_availability_metrics()
    
    def _close_circuit(self):
        """Close circuit breaker - recovery event"""
        previous_state = self.state
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        
        logger.info(
            "SOC2 Circuit Breaker CLOSED - Service Recovered",
            component=self.component_name,
            previous_state=previous_state.value,
            recovery_time_seconds=time.time() - (self.last_failure_time or 0),
            soc2_control="A1.2",
            event_type="circuit_closed"
        )
    
    def _is_critical_security_function(self) -> bool:
        """Determine if this component is critical for SOC2 security"""
        critical_components = [
            "audit_logger",
            "security_monitor", 
            "access_control",
            "phi_access_logger",
            "security_event_processor"
        ]
        return self.component_name.lower() in critical_components
    
    def _update_availability_metrics(self):
        """Update SOC2 availability metrics"""
        if self.metrics.total_requests > 0:
            self.metrics.uptime_percentage = (
                self.metrics.successful_requests / self.metrics.total_requests
            ) * 100
    
    def get_soc2_metrics(self) -> CircuitBreakerMetrics:
        """Get SOC2 compliance metrics for this component"""
        self._update_availability_metrics()
        self.metrics.current_state = self.state
        return self.metrics
    
    def reset(self):
        """Manual reset for SOC2 incident response"""
        logger.warning(
            "SOC2 Circuit Breaker Manual Reset",
            component=self.component_name,
            previous_state=self.state.value,
            failure_count=self.failure_count,
            soc2_control="CC8.1",  # SOC2 Change Management
            event_type="manual_reset",
            operator_action=True
        )
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0


class SOC2CircuitBreakerRegistry:
    """
    SOC2 compliant registry for managing all circuit breakers.
    
    Provides centralized monitoring and reporting for SOC2 audits.
    """
    
    def __init__(self):
        self._breakers: Dict[str, SOC2CircuitBreaker] = {}
        self._critical_components = set()
    
    def register_breaker(
        self, 
        component_name: str, 
        config: Optional[CircuitBreakerConfig] = None,
        backup_handler: Optional[Callable] = None,
        is_critical: bool = False
    ) -> SOC2CircuitBreaker:
        """Register a new circuit breaker for SOC2 monitoring"""
        
        breaker = SOC2CircuitBreaker(
            component_name=component_name,
            config=config,
            backup_handler=backup_handler
        )
        
        self._breakers[component_name] = breaker
        
        if is_critical:
            self._critical_components.add(component_name)
        
        logger.info(
            "SOC2 Circuit Breaker Registered",
            component=component_name,
            is_critical=is_critical,
            total_breakers=len(self._breakers),
            soc2_control="CC7.2"
        )
        
        return breaker
    
    def get_breaker(self, component_name: str) -> Optional[SOC2CircuitBreaker]:
        """Get circuit breaker for component"""
        return self._breakers.get(component_name)
    
    def get_soc2_availability_report(self) -> Dict[str, Any]:
        """Generate SOC2 availability report for all components"""
        report = {
            "report_timestamp": datetime.utcnow().isoformat(),
            "total_components": len(self._breakers),
            "critical_components": len(self._critical_components),
            "component_metrics": {},
            "overall_availability": 0.0,
            "critical_component_availability": 0.0,
            "soc2_compliance_status": "compliant"
        }
        
        total_availability = 0.0
        critical_availability = 0.0
        critical_count = 0
        
        for name, breaker in self._breakers.items():
            metrics = breaker.get_soc2_metrics()
            report["component_metrics"][name] = {
                "uptime_percentage": metrics.uptime_percentage,
                "total_requests": metrics.total_requests,
                "failed_requests": metrics.failed_requests,
                "circuit_opens": metrics.circuit_opens,
                "current_state": metrics.current_state.value,
                "is_critical": name in self._critical_components
            }
            
            total_availability += metrics.uptime_percentage
            
            if name in self._critical_components:
                critical_availability += metrics.uptime_percentage
                critical_count += 1
        
        if self._breakers:
            report["overall_availability"] = total_availability / len(self._breakers)
        
        if critical_count > 0:
            report["critical_component_availability"] = critical_availability / critical_count
            
            # SOC2 Critical: If critical components below 99.9% uptime
            if report["critical_component_availability"] < 99.9:
                report["soc2_compliance_status"] = "non_compliant"
                report["compliance_issues"] = [
                    f"Critical component availability ({report['critical_component_availability']:.2f}%) below SOC2 requirement (99.9%)"
                ]
        
        return report


# Global SOC2 circuit breaker registry
soc2_breaker_registry = SOC2CircuitBreakerRegistry()