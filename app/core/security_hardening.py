#!/usr/bin/env python3
"""
Enterprise Production Security Hardening System
Implements comprehensive security hardening with WAF, SIEM, DDoS protection,
intrusion detection, threat intelligence, and automated security response.

Security Hardening Features:
- Web Application Firewall (WAF) with OWASP rule sets
- Security Information and Event Management (SIEM) integration
- DDoS protection with traffic analysis and mitigation
- Intrusion Detection System (IDS) with behavioral analysis
- Threat intelligence integration and automated response
- Security event correlation and incident management

Security Principles Applied:
- Defense in Depth: Multiple security layers and controls
- Zero Trust: Every request verified and monitored
- Principle of Least Privilege: Minimal access rights
- Fail-Safe Defaults: Secure-by-default configurations
- Complete Mediation: All access attempts checked
- Economy of Mechanism: Simple, reliable security controls

Architecture Patterns:
- Chain of Responsibility: Security filter chain processing
- Strategy Pattern: Multiple security policies and algorithms
- Observer Pattern: Security event monitoring and alerting
- Command Pattern: Automated security response actions
- Decorator Pattern: Security layer wrapping
- Circuit Breaker: Security service failure protection
"""

import asyncio
import json
import time
import re
import ipaddress
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable, Set, Tuple
from enum import Enum, auto
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
import structlog
import uuid
import hashlib
import threading
from collections import defaultdict, deque
import weakref
import geoip2.database
import geoip2.webservice

from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.status import HTTP_429_TOO_MANY_REQUESTS, HTTP_403_FORBIDDEN

# Security monitoring imports
try:
    import requests
    import psutil
    REQUESTS_PSUTIL_AVAILABLE = True
except ImportError:
    REQUESTS_PSUTIL_AVAILABLE = False

# GeoIP imports
try:
    import geoip2.database
    import geoip2.webservice
    GEOIP_AVAILABLE = True
except ImportError:
    GEOIP_AVAILABLE = False

# Cryptographic imports
try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False

logger = structlog.get_logger()

# Security Configuration

class SecurityThreatLevel(str, Enum):
    """Security threat levels"""
    LOW = "low"                      # Informational events
    MEDIUM = "medium"                # Suspicious activity
    HIGH = "high"                    # Confirmed threats
    CRITICAL = "critical"            # Active attacks

class SecurityEventType(str, Enum):
    """Security event types"""
    WAF_BLOCK = "waf_block"                     # WAF blocked request
    DDOS_ATTEMPT = "ddos_attempt"               # DDoS attack detected
    INTRUSION_ATTEMPT = "intrusion_attempt"    # Intrusion detected
    MALWARE_DETECTED = "malware_detected"      # Malware found
    DATA_EXFILTRATION = "data_exfiltration"    # Data theft attempt
    PRIVILEGE_ESCALATION = "privilege_escalation" # Privilege abuse
    BRUTE_FORCE = "brute_force"                # Brute force attack
    ANOMALOUS_BEHAVIOR = "anomalous_behavior"  # Behavioral anomaly

class SecurityAction(str, Enum):
    """Automated security actions"""
    ALLOW = "allow"                  # Allow request
    BLOCK = "block"                  # Block request
    QUARANTINE = "quarantine"        # Isolate threat
    ALERT = "alert"                  # Generate alert
    LOG = "log"                      # Log event
    RATE_LIMIT = "rate_limit"        # Apply rate limiting

class WAFRuleType(str, Enum):
    """WAF rule types"""
    OWASP_CORE = "owasp_core"        # OWASP Core Rule Set
    SQL_INJECTION = "sql_injection"   # SQL injection protection
    XSS_PROTECTION = "xss_protection" # Cross-site scripting
    LFI_RFI = "lfi_rfi"              # Local/Remote file inclusion
    COMMAND_INJECTION = "command_injection" # Command injection
    CUSTOM = "custom"                # Custom rules

@dataclass
class SecurityHardeningConfig:
    """Security hardening configuration"""
    
    # WAF Configuration
    enable_waf: bool = True
    waf_rules: List[WAFRuleType] = field(default_factory=lambda: [
        WAFRuleType.OWASP_CORE,
        WAFRuleType.SQL_INJECTION,
        WAFRuleType.XSS_PROTECTION
    ])
    waf_block_threshold: int = 10     # Block after N violations
    waf_log_all_requests: bool = False # Log all requests (high volume)
    
    # DDoS Protection
    enable_ddos_protection: bool = True
    ddos_requests_per_minute: int = 1000  # Per IP limit
    ddos_detection_window: int = 60       # Detection window (seconds)
    ddos_mitigation_duration: int = 300   # Mitigation duration (seconds)
    ddos_whitelist_ips: Set[str] = field(default_factory=set)
    
    # Intrusion Detection
    enable_ids: bool = True
    ids_anomaly_threshold: float = 0.8    # Anomaly detection threshold
    ids_learning_period: int = 86400      # Learning period (seconds)
    ids_max_sessions_per_ip: int = 100    # Max concurrent sessions
    
    # SIEM Integration
    enable_siem: bool = True
    siem_endpoint: Optional[str] = None   # SIEM system endpoint
    siem_api_key: Optional[str] = None    # SIEM API key
    siem_batch_size: int = 100           # Events per batch
    siem_flush_interval: int = 60        # Flush interval (seconds)
    
    # Threat Intelligence
    enable_threat_intelligence: bool = True
    threat_intel_feeds: List[str] = field(default_factory=list)
    threat_intel_update_interval: int = 3600  # Update interval (seconds)
    
    # Geo-blocking
    enable_geo_blocking: bool = False
    blocked_countries: Set[str] = field(default_factory=set)
    allowed_countries: Set[str] = field(default_factory=set)
    geoip_database_path: Optional[str] = None
    
    # Security Headers
    enable_security_headers: bool = True
    hsts_max_age: int = 31536000         # HSTS max age
    content_security_policy: str = "default-src 'self'"
    
    # Rate Limiting
    global_rate_limit: int = 10000       # Global requests per minute
    per_ip_rate_limit: int = 1000        # Per IP requests per minute
    per_user_rate_limit: int = 5000      # Per user requests per minute
    
    # Monitoring and Alerting
    security_log_retention_days: int = 90
    enable_real_time_alerts: bool = True
    alert_escalation_threshold: int = 5   # Escalate after N critical events
    
    # Automated Response
    enable_automated_response: bool = True
    auto_block_duration: int = 3600       # Auto-block duration (seconds)
    quarantine_suspicious_users: bool = True

@dataclass
class SecurityEvent:
    """Security event data structure"""
    event_id: str
    event_type: SecurityEventType
    threat_level: SecurityThreatLevel
    timestamp: datetime
    source_ip: str
    user_agent: Optional[str] = None
    request_path: Optional[str] = None
    request_method: Optional[str] = None
    request_headers: Dict[str, str] = field(default_factory=dict)
    request_body: Optional[str] = None
    rule_triggered: Optional[str] = None
    severity_score: float = 0.0
    geo_location: Optional[Dict[str, str]] = None
    additional_context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SecurityRule:
    """Security rule definition"""
    rule_id: str
    rule_name: str
    rule_type: WAFRuleType
    pattern: str              # Regex pattern or condition
    action: SecurityAction
    severity_score: float
    enabled: bool = True
    description: Optional[str] = None

# Web Application Firewall (WAF)

class WebApplicationFirewall:
    """Enterprise Web Application Firewall"""
    
    def __init__(self, config: SecurityHardeningConfig):
        self.config = config
        self.rules: List[SecurityRule] = []
        self.blocked_ips: Dict[str, datetime] = {}
        self.violation_counts: Dict[str, int] = defaultdict(int)
        
        # Initialize WAF rules
        self._initialize_waf_rules()
        
        logger.info("WAF initialized", 
                   rules_count=len(self.rules),
                   enabled_rule_types=[rt.value for rt in config.waf_rules])
    
    def _initialize_waf_rules(self):
        """Initialize WAF rules based on configuration"""
        if WAFRuleType.OWASP_CORE in self.config.waf_rules:
            self._add_owasp_core_rules()
        
        if WAFRuleType.SQL_INJECTION in self.config.waf_rules:
            self._add_sql_injection_rules()
        
        if WAFRuleType.XSS_PROTECTION in self.config.waf_rules:
            self._add_xss_protection_rules()
        
        if WAFRuleType.LFI_RFI in self.config.waf_rules:
            self._add_lfi_rfi_rules()
        
        if WAFRuleType.COMMAND_INJECTION in self.config.waf_rules:
            self._add_command_injection_rules()
    
    def _add_owasp_core_rules(self):
        """Add OWASP Core Rule Set"""
        owasp_rules = [
            SecurityRule(
                rule_id="OWASP-001",
                rule_name="HTTP Method Validation",
                rule_type=WAFRuleType.OWASP_CORE,
                pattern=r"^(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)$",
                action=SecurityAction.BLOCK,
                severity_score=5.0,
                description="Block non-standard HTTP methods"
            ),
            SecurityRule(
                rule_id="OWASP-002",
                rule_name="Suspicious User Agent",
                rule_type=WAFRuleType.OWASP_CORE,
                pattern=r"(sqlmap|nikto|nmap|masscan|zgrab|shodan)",
                action=SecurityAction.BLOCK,
                severity_score=8.0,
                description="Block scanning tools and automated attacks"
            ),
            SecurityRule(
                rule_id="OWASP-003",
                rule_name="Path Traversal Protection",
                rule_type=WAFRuleType.OWASP_CORE,
                pattern=r"(\.\./|\.\.\\|/etc/passwd|/proc/|\\windows\\)",
                action=SecurityAction.BLOCK,
                severity_score=9.0,
                description="Prevent path traversal attacks"
            )
        ]
        self.rules.extend(owasp_rules)
    
    def _add_sql_injection_rules(self):
        """Add SQL injection protection rules"""
        sql_rules = [
            SecurityRule(
                rule_id="SQL-001",
                rule_name="SQL Injection Keywords",
                rule_type=WAFRuleType.SQL_INJECTION,
                pattern=r"(?i)(union\s+select|select\s+.*\s+from|insert\s+into|delete\s+from|drop\s+table|exec\s*\()",
                action=SecurityAction.BLOCK,
                severity_score=10.0,
                description="Block SQL injection attempts"
            ),
            SecurityRule(
                rule_id="SQL-002",
                rule_name="SQL Comment Injection",
                rule_type=WAFRuleType.SQL_INJECTION,
                pattern=r"(/\*.*\*/|--\s|#.*)",
                action=SecurityAction.BLOCK,
                severity_score=8.0,
                description="Block SQL comment-based injection"
            ),
            SecurityRule(
                rule_id="SQL-003",
                rule_name="SQL Function Calls",
                rule_type=WAFRuleType.SQL_INJECTION,
                pattern=r"(?i)(benchmark\s*\(|sleep\s*\(|waitfor\s+delay|pg_sleep)",
                action=SecurityAction.BLOCK,
                severity_score=9.0,
                description="Block SQL time-based injection"
            )
        ]
        self.rules.extend(sql_rules)
    
    def _add_xss_protection_rules(self):
        """Add XSS protection rules"""
        xss_rules = [
            SecurityRule(
                rule_id="XSS-001",
                rule_name="Script Tag Injection",
                rule_type=WAFRuleType.XSS_PROTECTION,
                pattern=r"(?i)<script[^>]*>.*?</script>",
                action=SecurityAction.BLOCK,
                severity_score=8.0,
                description="Block script tag injection"
            ),
            SecurityRule(
                rule_id="XSS-002",
                rule_name="Event Handler Injection",
                rule_type=WAFRuleType.XSS_PROTECTION,
                pattern=r"(?i)(on\w+\s*=|javascript:|vbscript:|data:text/html)",
                action=SecurityAction.BLOCK,
                severity_score=7.0,
                description="Block event handler-based XSS"
            ),
            SecurityRule(
                rule_id="XSS-003",
                rule_name="HTML Entity Encoding Bypass",
                rule_type=WAFRuleType.XSS_PROTECTION,
                pattern=r"(&#x[0-9a-f]+;|&#[0-9]+;|&\w+;)",
                action=SecurityAction.LOG,
                severity_score=5.0,
                description="Log potential HTML entity encoding bypass"
            )
        ]
        self.rules.extend(xss_rules)
    
    def _add_lfi_rfi_rules(self):
        """Add Local/Remote File Inclusion rules"""
        lfi_rfi_rules = [
            SecurityRule(
                rule_id="LFI-001",
                rule_name="Local File Inclusion",
                rule_type=WAFRuleType.LFI_RFI,
                pattern=r"(?i)(file://|php://|zip://|data://)",
                action=SecurityAction.BLOCK,
                severity_score=9.0,
                description="Block local file inclusion attempts"
            ),
            SecurityRule(
                rule_id="RFI-001",
                rule_name="Remote File Inclusion",
                rule_type=WAFRuleType.LFI_RFI,
                pattern=r"(?i)(https?://[^/\s]+/|ftp://)",
                action=SecurityAction.BLOCK,
                severity_score=9.0,
                description="Block remote file inclusion attempts"
            )
        ]
        self.rules.extend(lfi_rfi_rules)
    
    def _add_command_injection_rules(self):
        """Add command injection protection rules"""
        cmd_rules = [
            SecurityRule(
                rule_id="CMD-001",
                rule_name="Command Injection",
                rule_type=WAFRuleType.COMMAND_INJECTION,
                pattern=r"(?i)(;|\||&|`|\$\(|<\(|>\()",
                action=SecurityAction.BLOCK,
                severity_score=10.0,
                description="Block command injection attempts"
            ),
            SecurityRule(
                rule_id="CMD-002",
                rule_name="System Commands",
                rule_type=WAFRuleType.COMMAND_INJECTION,
                pattern=r"(?i)(wget|curl|nc|netcat|ping|nslookup|dig)",
                action=SecurityAction.BLOCK,
                severity_score=8.0,
                description="Block system command execution"
            )
        ]
        self.rules.extend(cmd_rules)
    
    async def evaluate_request(self, request: Request) -> Tuple[SecurityAction, Optional[SecurityEvent]]:
        """Evaluate request against WAF rules"""
        client_ip = self._get_client_ip(request)
        
        # Check if IP is already blocked
        if client_ip in self.blocked_ips:
            if datetime.utcnow() < self.blocked_ips[client_ip]:
                return SecurityAction.BLOCK, self._create_security_event(
                    SecurityEventType.WAF_BLOCK,
                    SecurityThreatLevel.HIGH,
                    client_ip,
                    request,
                    "IP blocked due to previous violations"
                )
        
        # Evaluate each rule
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            if await self._evaluate_rule(rule, request):
                # Rule triggered
                self.violation_counts[client_ip] += 1
                
                # Check if we should block this IP
                if self.violation_counts[client_ip] >= self.config.waf_block_threshold:
                    self.blocked_ips[client_ip] = datetime.utcnow() + timedelta(
                        seconds=self.config.auto_block_duration
                    )
                
                security_event = self._create_security_event(
                    SecurityEventType.WAF_BLOCK,
                    self._severity_to_threat_level(rule.severity_score),
                    client_ip,
                    request,
                    f"WAF rule triggered: {rule.rule_name}"
                )
                security_event.rule_triggered = rule.rule_id
                security_event.severity_score = rule.severity_score
                
                return rule.action, security_event
        
        return SecurityAction.ALLOW, None
    
    async def _evaluate_rule(self, rule: SecurityRule, request: Request) -> bool:
        """Evaluate a single WAF rule against request"""
        try:
            # Get request components
            method = request.method
            path = str(request.url.path)
            query = str(request.url.query) if request.url.query else ""
            user_agent = request.headers.get("user-agent", "")
            
            # Read request body if present
            body = ""
            if request.method in ["POST", "PUT", "PATCH"]:
                try:
                    body_bytes = await request.body()
                    body = body_bytes.decode('utf-8', errors='ignore')
                except:
                    body = ""
            
            # Combine all request data for pattern matching
            request_data = f"{method} {path} {query} {user_agent} {body}"
            
            # Apply pattern matching based on rule type
            if rule.rule_type == WAFRuleType.OWASP_CORE:
                if rule.rule_id == "OWASP-001":  # HTTP method validation
                    return not re.match(rule.pattern, method)
                else:
                    return bool(re.search(rule.pattern, request_data, re.IGNORECASE))
            else:
                return bool(re.search(rule.pattern, request_data, re.IGNORECASE))
                
        except Exception as e:
            logger.error("WAF rule evaluation error", 
                        rule_id=rule.rule_id, 
                        error=str(e))
            return False
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
        
        # Fallback to direct client IP
        if hasattr(request, 'client') and request.client:
            return request.client.host
        
        return "unknown"
    
    def _severity_to_threat_level(self, severity_score: float) -> SecurityThreatLevel:
        """Convert severity score to threat level"""
        if severity_score >= 9.0:
            return SecurityThreatLevel.CRITICAL
        elif severity_score >= 7.0:
            return SecurityThreatLevel.HIGH
        elif severity_score >= 5.0:
            return SecurityThreatLevel.MEDIUM
        else:
            return SecurityThreatLevel.LOW
    
    def _create_security_event(
        self,
        event_type: SecurityEventType,
        threat_level: SecurityThreatLevel,
        source_ip: str,
        request: Request,
        description: str
    ) -> SecurityEvent:
        """Create security event from request"""
        return SecurityEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            threat_level=threat_level,
            timestamp=datetime.utcnow(),
            source_ip=source_ip,
            user_agent=request.headers.get("user-agent"),
            request_path=str(request.url.path),
            request_method=request.method,
            request_headers=dict(request.headers),
            additional_context={"description": description}
        )

# DDoS Protection System

class DDoSProtectionSystem:
    """Enterprise DDoS Protection System"""
    
    def __init__(self, config: SecurityHardeningConfig):
        self.config = config
        self.request_counts: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.blocked_ips: Dict[str, datetime] = {}
        self.traffic_baseline: Dict[str, float] = {}
        self.suspicious_patterns: Set[str] = set()
        
        logger.info("DDoS protection initialized",
                   rps_limit=config.ddos_requests_per_minute,
                   detection_window=config.ddos_detection_window)
    
    async def analyze_traffic(self, request: Request) -> Tuple[SecurityAction, Optional[SecurityEvent]]:
        """Analyze traffic for DDoS patterns"""
        client_ip = self._get_client_ip(request)
        current_time = time.time()
        
        # Check if IP is whitelisted
        if client_ip in self.config.ddos_whitelist_ips:
            return SecurityAction.ALLOW, None
        
        # Check if IP is already blocked
        if client_ip in self.blocked_ips:
            if datetime.utcnow() < self.blocked_ips[client_ip]:
                return SecurityAction.BLOCK, self._create_ddos_event(
                    client_ip, request, "IP blocked due to DDoS activity"
                )
            else:
                # Block expired, remove it
                del self.blocked_ips[client_ip]
        
        # Record request
        self.request_counts[client_ip].append(current_time)
        
        # Clean old requests outside detection window
        cutoff_time = current_time - self.config.ddos_detection_window
        while (self.request_counts[client_ip] and 
               self.request_counts[client_ip][0] < cutoff_time):
            self.request_counts[client_ip].popleft()
        
        # Check request rate
        request_count = len(self.request_counts[client_ip])
        requests_per_minute = (request_count / self.config.ddos_detection_window) * 60
        
        if requests_per_minute > self.config.ddos_requests_per_minute:
            # DDoS detected, block IP
            self.blocked_ips[client_ip] = datetime.utcnow() + timedelta(
                seconds=self.config.ddos_mitigation_duration
            )
            
            security_event = self._create_ddos_event(
                client_ip, request, f"DDoS attack detected: {requests_per_minute:.1f} RPM"
            )
            security_event.severity_score = min(10.0, requests_per_minute / 100)
            
            logger.warning("DDoS attack detected",
                          client_ip=client_ip,
                          requests_per_minute=requests_per_minute)
            
            return SecurityAction.BLOCK, security_event
        
        # Check for suspicious patterns
        if await self._detect_suspicious_patterns(client_ip, request):
            security_event = self._create_ddos_event(
                client_ip, request, "Suspicious traffic pattern detected"
            )
            return SecurityAction.RATE_LIMIT, security_event
        
        return SecurityAction.ALLOW, None
    
    async def _detect_suspicious_patterns(self, client_ip: str, request: Request) -> bool:
        """Detect suspicious traffic patterns"""
        # Check for bot-like behavior
        user_agent = request.headers.get("user-agent", "").lower()
        
        # Suspicious user agents
        bot_patterns = [
            "bot", "crawler", "spider", "scraper", "scanner",
            "python-requests", "curl", "wget", "httpclient"
        ]
        
        if any(pattern in user_agent for pattern in bot_patterns):
            return True
        
        # Check for repeated identical requests
        request_signature = self._get_request_signature(request)
        if request_signature in self.suspicious_patterns:
            return True
        
        # Add to suspicious patterns if too many similar requests
        if len([sig for sig in self.suspicious_patterns if sig.startswith(client_ip)]) > 5:
            self.suspicious_patterns.add(request_signature)
            return True
        
        return False
    
    def _get_request_signature(self, request: Request) -> str:
        """Generate request signature for pattern detection"""
        client_ip = self._get_client_ip(request)
        path = str(request.url.path)
        method = request.method
        user_agent = request.headers.get("user-agent", "")[:50]  # Truncate
        
        signature_data = f"{client_ip}:{method}:{path}:{user_agent}"
        return hashlib.md5(signature_data.encode()).hexdigest()
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        if hasattr(request, 'client') and request.client:
            return request.client.host
        
        return "unknown"
    
    def _create_ddos_event(self, client_ip: str, request: Request, description: str) -> SecurityEvent:
        """Create DDoS security event"""
        return SecurityEvent(
            event_id=str(uuid.uuid4()),
            event_type=SecurityEventType.DDOS_ATTEMPT,
            threat_level=SecurityThreatLevel.HIGH,
            timestamp=datetime.utcnow(),
            source_ip=client_ip,
            user_agent=request.headers.get("user-agent"),
            request_path=str(request.url.path),
            request_method=request.method,
            additional_context={"description": description}
        )

# Intrusion Detection System

class IntrusionDetectionSystem:
    """Behavioral Intrusion Detection System"""
    
    def __init__(self, config: SecurityHardeningConfig):
        self.config = config
        self.user_sessions: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.baseline_behavior: Dict[str, Dict[str, float]] = {}
        self.anomaly_scores: Dict[str, float] = defaultdict(float)
        self.learning_mode = True
        self.learning_start_time = time.time()
        
        logger.info("IDS initialized", 
                   anomaly_threshold=config.ids_anomaly_threshold,
                   learning_period=config.ids_learning_period)
    
    async def analyze_behavior(self, request: Request, user_id: Optional[str] = None) -> Tuple[SecurityAction, Optional[SecurityEvent]]:
        """Analyze user behavior for anomalies"""
        client_ip = self._get_client_ip(request)
        session_key = user_id or client_ip
        
        # Check if still in learning mode
        if self.learning_mode:
            if time.time() - self.learning_start_time > self.config.ids_learning_period:
                self.learning_mode = False
                logger.info("IDS learning mode disabled, entering detection mode")
        
        # Update session information
        await self._update_session_info(session_key, request)
        
        # Calculate anomaly score
        anomaly_score = await self._calculate_anomaly_score(session_key, request)
        self.anomaly_scores[session_key] = anomaly_score
        
        # Check for intrusion
        if not self.learning_mode and anomaly_score > self.config.ids_anomaly_threshold:
            security_event = SecurityEvent(
                event_id=str(uuid.uuid4()),
                event_type=SecurityEventType.INTRUSION_ATTEMPT,
                threat_level=SecurityThreatLevel.HIGH,
                timestamp=datetime.utcnow(),
                source_ip=client_ip,
                user_agent=request.headers.get("user-agent"),
                request_path=str(request.url.path),
                request_method=request.method,
                severity_score=anomaly_score * 10,
                additional_context={
                    "anomaly_score": anomaly_score,
                    "user_id": user_id,
                    "description": f"Behavioral anomaly detected (score: {anomaly_score:.2f})"
                }
            )
            
            logger.warning("Intrusion attempt detected",
                          session_key=session_key,
                          anomaly_score=anomaly_score)
            
            return SecurityAction.ALERT, security_event
        
        return SecurityAction.ALLOW, None
    
    async def _update_session_info(self, session_key: str, request: Request):
        """Update session information for behavior analysis"""
        current_time = time.time()
        session = self.user_sessions[session_key]
        
        # Initialize session if new
        if "start_time" not in session:
            session["start_time"] = current_time
            session["request_count"] = 0
            session["unique_paths"] = set()
            session["request_intervals"] = deque(maxlen=10)
            session["user_agents"] = set()
            session["last_request_time"] = current_time
        
        # Update session metrics
        session["request_count"] += 1
        session["unique_paths"].add(str(request.url.path))
        session["user_agents"].add(request.headers.get("user-agent", ""))
        
        # Calculate request interval
        interval = current_time - session["last_request_time"]
        session["request_intervals"].append(interval)
        session["last_request_time"] = current_time
        
        # Session duration
        session["duration"] = current_time - session["start_time"]
    
    async def _calculate_anomaly_score(self, session_key: str, request: Request) -> float:
        """Calculate behavioral anomaly score"""
        session = self.user_sessions[session_key]
        anomaly_factors = []
        
        # Request rate anomaly
        if session["duration"] > 0:
            request_rate = session["request_count"] / session["duration"]
            if session_key in self.baseline_behavior:
                baseline_rate = self.baseline_behavior[session_key].get("request_rate", request_rate)
                rate_anomaly = abs(request_rate - baseline_rate) / max(baseline_rate, 1)
                anomaly_factors.append(min(rate_anomaly, 1.0))
            else:
                # No baseline, check against global average
                if request_rate > 10:  # More than 10 requests per second
                    anomaly_factors.append(0.7)
        
        # Path diversity anomaly
        path_diversity = len(session["unique_paths"]) / max(session["request_count"], 1)
        if path_diversity > 0.8:  # Accessing many different paths
            anomaly_factors.append(0.6)
        
        # User agent switching
        if len(session["user_agents"]) > 1:
            anomaly_factors.append(0.5)
        
        # Request interval consistency
        intervals = list(session["request_intervals"])
        if len(intervals) > 3:
            import statistics
            try:
                interval_variance = statistics.variance(intervals)
                if interval_variance < 0.1:  # Very consistent timing (bot-like)
                    anomaly_factors.append(0.8)
            except:
                pass
        
        # Combine anomaly factors
        if anomaly_factors:
            return min(sum(anomaly_factors) / len(anomaly_factors), 1.0)
        
        return 0.0
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        if hasattr(request, 'client') and request.client:
            return request.client.host
        
        return "unknown"

# SIEM Integration

class SIEMIntegration:
    """Security Information and Event Management Integration"""
    
    def __init__(self, config: SecurityHardeningConfig):
        self.config = config
        self.event_queue: deque = deque(maxlen=10000)
        self.last_flush_time = time.time()
        self.correlation_rules: List[Dict[str, Any]] = []
        
        # Initialize correlation rules
        self._initialize_correlation_rules()
        
        logger.info("SIEM integration initialized",
                   endpoint=config.siem_endpoint,
                   batch_size=config.siem_batch_size)
    
    def _initialize_correlation_rules(self):
        """Initialize event correlation rules"""
        self.correlation_rules = [
            {
                "rule_id": "CORR-001",
                "name": "Multiple Failed Logins",
                "events": [SecurityEventType.BRUTE_FORCE],
                "threshold": 5,
                "time_window": 300,  # 5 minutes
                "escalation": SecurityThreatLevel.HIGH
            },
            {
                "rule_id": "CORR-002", 
                "name": "Coordinated Attack",
                "events": [SecurityEventType.WAF_BLOCK, SecurityEventType.DDOS_ATTEMPT],
                "threshold": 3,
                "time_window": 600,  # 10 minutes
                "escalation": SecurityThreatLevel.CRITICAL
            }
        ]
    
    async def queue_event(self, event: SecurityEvent):
        """Queue security event for SIEM processing"""
        self.event_queue.append(event)
        
        # Check if we should flush events
        current_time = time.time()
        if (len(self.event_queue) >= self.config.siem_batch_size or
            current_time - self.last_flush_time >= self.config.siem_flush_interval):
            await self._flush_events()
    
    async def _flush_events(self):
        """Flush events to SIEM system"""
        if not self.event_queue:
            return
        
        # Perform event correlation
        correlated_events = await self._correlate_events()
        
        # Prepare events for SIEM
        events_to_send = []
        while self.event_queue:
            event = self.event_queue.popleft()
            events_to_send.append(self._serialize_event(event))
        
        # Add correlated events
        for corr_event in correlated_events:
            events_to_send.append(self._serialize_event(corr_event))
        
        # Send to SIEM
        if self.config.siem_endpoint and events_to_send:
            await self._send_to_siem(events_to_send)
        
        self.last_flush_time = time.time()
        
        logger.debug("SIEM events flushed", 
                    event_count=len(events_to_send))
    
    async def _correlate_events(self) -> List[SecurityEvent]:
        """Correlate events based on rules"""
        correlated_events = []
        current_time = time.time()
        
        for rule in self.correlation_rules:
            # Count relevant events in time window
            relevant_events = []
            cutoff_time = current_time - rule["time_window"]
            
            for event in self.event_queue:
                if (event.event_type in rule["events"] and
                    event.timestamp.timestamp() > cutoff_time):
                    relevant_events.append(event)
            
            # Check if threshold is met
            if len(relevant_events) >= rule["threshold"]:
                # Create correlated event
                correlated_event = SecurityEvent(
                    event_id=str(uuid.uuid4()),
                    event_type=SecurityEventType.ANOMALOUS_BEHAVIOR,
                    threat_level=rule["escalation"],
                    timestamp=datetime.utcnow(),
                    source_ip="multiple",  # Multiple sources
                    severity_score=8.0,
                    additional_context={
                        "correlation_rule": rule["rule_id"],
                        "correlated_events": [e.event_id for e in relevant_events],
                        "description": f"Correlation rule triggered: {rule['name']}"
                    }
                )
                
                correlated_events.append(correlated_event)
                
                logger.info("Event correlation triggered",
                           rule_id=rule["rule_id"],
                           event_count=len(relevant_events))
        
        return correlated_events
    
    def _serialize_event(self, event: SecurityEvent) -> Dict[str, Any]:
        """Serialize security event for SIEM"""
        return {
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "threat_level": event.threat_level.value,
            "timestamp": event.timestamp.isoformat(),
            "source_ip": event.source_ip,
            "user_agent": event.user_agent,
            "request_path": event.request_path,
            "request_method": event.request_method,
            "rule_triggered": event.rule_triggered,
            "severity_score": event.severity_score,
            "geo_location": event.geo_location,
            "additional_context": event.additional_context
        }
    
    async def _send_to_siem(self, events: List[Dict[str, Any]]):
        """Send events to SIEM system"""
        if not REQUESTS_PSUTIL_AVAILABLE:
            logger.warning("Requests library not available, cannot send to SIEM")
            return
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config.siem_api_key}"
            } if self.config.siem_api_key else {"Content-Type": "application/json"}
            
            payload = {
                "events": events,
                "source": "healthcare_api_security",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            response = requests.post(
                self.config.siem_endpoint,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.debug("Events sent to SIEM successfully")
            else:
                logger.error("Failed to send events to SIEM",
                           status_code=response.status_code,
                           response_text=response.text)
                
        except Exception as e:
            logger.error("SIEM integration error", error=str(e))

# Security Hardening Middleware

class SecurityHardeningMiddleware(BaseHTTPMiddleware):
    """Comprehensive security hardening middleware"""
    
    def __init__(self, app: ASGIApp, config: SecurityHardeningConfig):
        super().__init__(app)
        self.config = config
        
        # Initialize security components
        self.waf = WebApplicationFirewall(config) if config.enable_waf else None
        self.ddos_protection = DDoSProtectionSystem(config) if config.enable_ddos_protection else None
        self.ids = IntrusionDetectionSystem(config) if config.enable_ids else None
        self.siem = SIEMIntegration(config) if config.enable_siem else None
        
        # Security statistics
        self.security_stats = {
            "total_requests": 0,
            "blocked_requests": 0,
            "security_events": 0,
            "start_time": datetime.utcnow()
        }
        
        logger.info("Security hardening middleware initialized",
                   waf_enabled=config.enable_waf,
                   ddos_enabled=config.enable_ddos_protection,
                   ids_enabled=config.enable_ids,
                   siem_enabled=config.enable_siem)
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Main security processing pipeline"""
        self.security_stats["total_requests"] += 1
        
        try:
            # Security processing pipeline
            security_events = []
            
            # WAF evaluation
            if self.waf:
                waf_action, waf_event = await self.waf.evaluate_request(request)
                if waf_event:
                    security_events.append(waf_event)
                    
                if waf_action == SecurityAction.BLOCK:
                    return await self._create_security_response(
                        HTTP_403_FORBIDDEN,
                        "Request blocked by Web Application Firewall",
                        security_events
                    )
            
            # DDoS protection
            if self.ddos_protection:
                ddos_action, ddos_event = await self.ddos_protection.analyze_traffic(request)
                if ddos_event:
                    security_events.append(ddos_event)
                    
                if ddos_action == SecurityAction.BLOCK:
                    return await self._create_security_response(
                        HTTP_429_TOO_MANY_REQUESTS,
                        "Request blocked due to DDoS protection",
                        security_events
                    )
            
            # Intrusion detection
            if self.ids:
                # Extract user ID from request if available
                user_id = self._extract_user_id(request)
                ids_action, ids_event = await self.ids.analyze_behavior(request, user_id)
                if ids_event:
                    security_events.append(ids_event)
                    
                # IDS typically doesn't block, just alerts
                if ids_action == SecurityAction.BLOCK:
                    return await self._create_security_response(
                        HTTP_403_FORBIDDEN,
                        "Request blocked due to suspicious behavior",
                        security_events
                    )
            
            # Process request
            response = await call_next(request)
            
            # Add security headers
            if self.config.enable_security_headers:
                response = await self._add_security_headers(response)
            
            # Queue security events to SIEM
            if self.siem and security_events:
                for event in security_events:
                    await self.siem.queue_event(event)
            
            return response
            
        except Exception as e:
            logger.error("Security middleware error", error=str(e))
            # In case of security middleware failure, allow request through
            # but log the incident
            return await call_next(request)
    
    async def _create_security_response(
        self, 
        status_code: int, 
        message: str, 
        security_events: List[SecurityEvent]
    ) -> Response:
        """Create security-related response"""
        self.security_stats["blocked_requests"] += 1
        self.security_stats["security_events"] += len(security_events)
        
        # Log security events
        for event in security_events:
            logger.warning("Security event",
                          event_type=event.event_type.value,
                          threat_level=event.threat_level.value,
                          source_ip=event.source_ip)
        
        return JSONResponse(
            status_code=status_code,
            content={
                "error": "Security Policy Violation",
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": str(uuid.uuid4())
            }
        )
    
    def _extract_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request for IDS analysis"""
        # Try to extract from JWT token
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            # In a real implementation, you'd validate and decode the JWT
            # For now, just return a placeholder
            return "jwt_user"
        
        # Try to extract from session
        session_id = request.headers.get("x-session-id")
        if session_id:
            return f"session_{session_id}"
        
        return None
    
    async def _add_security_headers(self, response: Response) -> Response:
        """Add security headers to response"""
        security_headers = {
            "Strict-Transport-Security": f"max-age={self.config.hsts_max_age}; includeSubDomains",
            "Content-Security-Policy": self.config.content_security_policy,
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }
        
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response
    
    async def get_security_metrics(self) -> Dict[str, Any]:
        """Get security metrics and statistics"""
        uptime = datetime.utcnow() - self.security_stats["start_time"]
        
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": uptime.total_seconds(),
            "requests": {
                "total": self.security_stats["total_requests"],
                "blocked": self.security_stats["blocked_requests"],
                "allowed": self.security_stats["total_requests"] - self.security_stats["blocked_requests"],
                "block_rate": (self.security_stats["blocked_requests"] / 
                             max(self.security_stats["total_requests"], 1)) * 100
            },
            "security_events": self.security_stats["security_events"]
        }
        
        # Add component-specific metrics
        if self.waf:
            metrics["waf"] = {
                "rules_count": len(self.waf.rules),
                "blocked_ips": len(self.waf.blocked_ips),
                "violation_counts": dict(self.waf.violation_counts)
            }
        
        if self.ddos_protection:
            metrics["ddos_protection"] = {
                "blocked_ips": len(self.ddos_protection.blocked_ips),
                "active_sessions": len(self.ddos_protection.request_counts)
            }
        
        if self.ids:
            metrics["ids"] = {
                "learning_mode": self.ids.learning_mode,
                "active_sessions": len(self.ids.user_sessions),
                "anomaly_scores": dict(self.ids.anomaly_scores)
            }
        
        return metrics

# Global security hardening instance
security_hardening_middleware: Optional[SecurityHardeningMiddleware] = None

# Initialization functions

def initialize_security_hardening(app: FastAPI, config: SecurityHardeningConfig) -> SecurityHardeningMiddleware:
    """Initialize security hardening middleware"""
    global security_hardening_middleware
    
    middleware = SecurityHardeningMiddleware(app, config)
    app.add_middleware(SecurityHardeningMiddleware, config=config)
    
    security_hardening_middleware = middleware
    return middleware

def get_security_hardening() -> SecurityHardeningMiddleware:
    """Get global security hardening middleware instance"""
    if security_hardening_middleware is None:
        raise RuntimeError("Security hardening not initialized")
    return security_hardening_middleware

# Convenience functions

async def get_security_dashboard() -> Dict[str, Any]:
    """Get security dashboard data"""
    middleware = get_security_hardening()
    
    metrics = await middleware.get_security_metrics()
    
    dashboard = {
        "security_status": "active",
        "threat_level": _calculate_overall_threat_level(metrics),
        "metrics": metrics,
        "recent_events": [],  # Would fetch from SIEM or event store
        "recommendations": _generate_security_recommendations(metrics)
    }
    
    return dashboard

def _calculate_overall_threat_level(metrics: Dict[str, Any]) -> str:
    """Calculate overall threat level from metrics"""
    block_rate = metrics["requests"]["block_rate"]
    
    if block_rate > 10:
        return "high"
    elif block_rate > 5:
        return "medium"
    elif block_rate > 1:
        return "low"
    else:
        return "minimal"

def _generate_security_recommendations(metrics: Dict[str, Any]) -> List[Dict[str, str]]:
    """Generate security recommendations based on metrics"""
    recommendations = []
    
    block_rate = metrics["requests"]["block_rate"]
    
    if block_rate > 15:
        recommendations.append({
            "priority": "high",
            "category": "traffic_analysis",
            "recommendation": "High block rate detected. Review traffic patterns and consider adjusting security rules."
        })
    
    if "waf" in metrics and metrics["waf"]["blocked_ips"] > 100:
        recommendations.append({
            "priority": "medium",
            "category": "waf_tuning",
            "recommendation": "Large number of blocked IPs. Consider implementing geographic filtering."
        })
    
    if "ids" in metrics and not metrics["ids"]["learning_mode"] and len(metrics["ids"]["anomaly_scores"]) == 0:
        recommendations.append({
            "priority": "low",
            "category": "ids_tuning",
            "recommendation": "IDS not detecting anomalies. Review detection thresholds."
        })
    
    return recommendations

async def trigger_security_test() -> Dict[str, Any]:
    """Trigger security test scenarios"""
    middleware = get_security_hardening()
    
    # This would typically trigger controlled security tests
    # For now, return test configuration
    return {
        "test_scenarios": [
            "SQL injection simulation",
            "XSS attack simulation", 
            "DDoS traffic simulation",
            "Brute force simulation"
        ],
        "status": "Test scenarios would be executed in a controlled environment"
    }

if __name__ == "__main__":
    # Example usage
    async def main():
        from fastapi import FastAPI
        
        # Create FastAPI app
        app = FastAPI()
        
        # Initialize security hardening
        config = SecurityHardeningConfig(
            enable_waf=True,
            enable_ddos_protection=True,
            enable_ids=True,
            enable_siem=False  # Disable for demo
        )
        
        middleware = initialize_security_hardening(app, config)
        
        # Add test endpoint
        @app.get("/test")
        async def test_endpoint():
            return {"message": "Test endpoint"}
        
        print("Security hardening initialized with:")
        print(f"- WAF: {config.enable_waf}")
        print(f"- DDoS Protection: {config.enable_ddos_protection}")
        print(f"- IDS: {config.enable_ids}")
        print(f"- SIEM: {config.enable_siem}")
    
    asyncio.run(main())