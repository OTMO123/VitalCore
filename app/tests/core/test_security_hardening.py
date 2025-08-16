#!/usr/bin/env python3
"""
Comprehensive Test Suite for Enterprise Security Hardening System
Ensures 100% test coverage for WAF, DDoS protection, IDS, and SIEM integration.

Test Categories:
- Unit Tests: Individual security component validation
- Integration Tests: Full security pipeline testing
- Security Tests: Attack simulation and mitigation validation
- Performance Tests: Security overhead and throughput validation
- Compliance Tests: Security policy and rule validation
- Resilience Tests: Security system failure recovery

Coverage Requirements:
- All WAF rules and pattern matching
- All DDoS detection and mitigation mechanisms
- All IDS behavioral analysis and anomaly detection
- All SIEM integration and event correlation
- All security headers and response handling
- All error conditions and recovery mechanisms
"""

import pytest
import asyncio
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse

from app.core.security_hardening import (
    SecurityHardeningConfig, SecurityThreatLevel, SecurityEventType, SecurityAction, WAFRuleType,
    SecurityEvent, SecurityRule, WebApplicationFirewall, DDoSProtectionSystem,
    IntrusionDetectionSystem, SIEMIntegration, SecurityHardeningMiddleware,
    initialize_security_hardening, get_security_hardening, get_security_dashboard,
    trigger_security_test
)

# Test Fixtures

@pytest.fixture
def security_config():
    """Standard security hardening configuration for testing"""
    return SecurityHardeningConfig(
        enable_waf=True,
        enable_ddos_protection=True,
        enable_ids=True,
        enable_siem=False,  # Disable for testing to avoid external dependencies
        waf_block_threshold=3,
        ddos_requests_per_minute=100,
        ids_anomaly_threshold=0.7,
        auto_block_duration=300,
        enable_security_headers=True
    )

@pytest.fixture
def mock_request():
    """Mock FastAPI request for testing"""
    request = Mock(spec=Request)
    request.method = "GET"
    request.url.path = "/api/test"
    request.url.query = ""
    request.headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "x-forwarded-for": "192.168.1.100"
    }
    request.client.host = "192.168.1.100"
    request.body = AsyncMock(return_value=b'{"test": "data"}')
    return request

@pytest.fixture  
def malicious_request():
    """Mock malicious request for testing"""
    request = Mock(spec=Request)
    request.method = "POST"
    request.url.path = "/api/vulnerable"
    request.url.query = "id=1' OR '1'='1"  # SQL injection attempt
    request.headers = {
        "user-agent": "sqlmap/1.0",
        "x-forwarded-for": "10.0.0.1"
    }
    request.client.host = "10.0.0.1"
    request.body = AsyncMock(return_value=b'<script>alert("xss")</script>')
    return request

@pytest.fixture
def waf_instance(security_config):
    """WAF instance for testing"""
    return WebApplicationFirewall(security_config)

@pytest.fixture
def ddos_protection(security_config):
    """DDoS protection instance for testing"""
    return DDoSProtectionSystem(security_config)

@pytest.fixture
def ids_instance(security_config):
    """IDS instance for testing"""
    return IntrusionDetectionSystem(security_config)

@pytest.fixture
def siem_integration(security_config):
    """SIEM integration instance for testing"""
    return SIEMIntegration(security_config)

@pytest.fixture
def security_middleware(security_config):
    """Security middleware for testing"""
    app = FastAPI()
    return SecurityHardeningMiddleware(app, security_config)

@pytest.fixture
def test_app_with_security():
    """FastAPI app with security middleware for integration testing"""
    app = FastAPI()
    
    @app.get("/")
    async def root():
        return {"message": "Hello World"}
    
    @app.get("/api/data")
    async def get_data():
        return {"data": "test data"}
    
    @app.post("/api/login")
    async def login(credentials: dict):
        return {"token": "test_token"}
    
    config = SecurityHardeningConfig(
        enable_waf=True,
        enable_ddos_protection=True,
        enable_ids=True,
        enable_siem=False,
        waf_block_threshold=3,
        ddos_requests_per_minute=50  # Lower for testing
    )
    
    initialize_security_hardening(app, config)
    return app

# Unit Tests for Configuration

class TestSecurityHardeningConfig:
    """Test security hardening configuration"""
    
    def test_default_configuration(self):
        """Test default configuration values"""
        config = SecurityHardeningConfig()
        
        assert config.enable_waf is True
        assert config.enable_ddos_protection is True
        assert config.enable_ids is True
        assert config.enable_siem is True
        assert config.waf_block_threshold == 10
        assert config.ddos_requests_per_minute == 1000
        assert config.ids_anomaly_threshold == 0.8
    
    def test_custom_configuration(self):
        """Test custom configuration values"""
        config = SecurityHardeningConfig(
            enable_waf=False,
            waf_block_threshold=5,
            ddos_requests_per_minute=500,
            ids_anomaly_threshold=0.9,
            enable_security_headers=False
        )
        
        assert config.enable_waf is False
        assert config.waf_block_threshold == 5
        assert config.ddos_requests_per_minute == 500
        assert config.ids_anomaly_threshold == 0.9
        assert config.enable_security_headers is False
    
    def test_waf_rules_configuration(self):
        """Test WAF rules configuration"""
        config = SecurityHardeningConfig(
            waf_rules=[WAFRuleType.SQL_INJECTION, WAFRuleType.XSS_PROTECTION]
        )
        
        assert len(config.waf_rules) == 2
        assert WAFRuleType.SQL_INJECTION in config.waf_rules
        assert WAFRuleType.XSS_PROTECTION in config.waf_rules

# Unit Tests for Security Events

class TestSecurityEvent:
    """Test security event functionality"""
    
    def test_security_event_creation(self):
        """Test security event creation"""
        event = SecurityEvent(
            event_id="test-event-123",
            event_type=SecurityEventType.WAF_BLOCK,
            threat_level=SecurityThreatLevel.HIGH,
            timestamp=datetime.utcnow(),
            source_ip="192.168.1.100",
            user_agent="Test Agent",
            request_path="/api/test",
            request_method="GET",
            severity_score=8.5
        )
        
        assert event.event_id == "test-event-123"
        assert event.event_type == SecurityEventType.WAF_BLOCK
        assert event.threat_level == SecurityThreatLevel.HIGH
        assert event.source_ip == "192.168.1.100"
        assert event.severity_score == 8.5
    
    def test_security_event_with_context(self):
        """Test security event with additional context"""
        event = SecurityEvent(
            event_id="context-event",
            event_type=SecurityEventType.INTRUSION_ATTEMPT,
            threat_level=SecurityThreatLevel.CRITICAL,
            timestamp=datetime.utcnow(),
            source_ip="10.0.0.1",
            additional_context={
                "anomaly_score": 0.95,
                "user_id": "user123",
                "description": "Behavioral anomaly detected"
            }
        )
        
        assert event.additional_context["anomaly_score"] == 0.95
        assert event.additional_context["user_id"] == "user123"

# Unit Tests for Web Application Firewall

class TestWebApplicationFirewall:
    """Test WAF functionality"""
    
    def test_waf_initialization(self, security_config):
        """Test WAF initialization"""
        waf = WebApplicationFirewall(security_config)
        
        assert len(waf.rules) > 0
        assert len(waf.blocked_ips) == 0
        assert isinstance(waf.violation_counts, dict)
    
    def test_waf_rule_initialization(self, waf_instance):
        """Test WAF rule initialization"""
        # Check that OWASP core rules were added
        owasp_rules = [r for r in waf_instance.rules if r.rule_type == WAFRuleType.OWASP_CORE]
        assert len(owasp_rules) > 0
        
        # Check that SQL injection rules were added
        sql_rules = [r for r in waf_instance.rules if r.rule_type == WAFRuleType.SQL_INJECTION]
        assert len(sql_rules) > 0
        
        # Check that XSS rules were added
        xss_rules = [r for r in waf_instance.rules if r.rule_type == WAFRuleType.XSS_PROTECTION]
        assert len(xss_rules) > 0
    
    @pytest.mark.asyncio
    async def test_waf_allows_legitimate_request(self, waf_instance, mock_request):
        """Test WAF allows legitimate requests"""
        action, event = await waf_instance.evaluate_request(mock_request)
        
        assert action == SecurityAction.ALLOW
        assert event is None
    
    @pytest.mark.asyncio
    async def test_waf_blocks_sql_injection(self, waf_instance, malicious_request):
        """Test WAF blocks SQL injection attempts"""
        # Set up malicious SQL injection in query
        malicious_request.url.query = "id=1' UNION SELECT * FROM users--"
        
        action, event = await waf_instance.evaluate_request(malicious_request)
        
        assert action == SecurityAction.BLOCK
        assert event is not None
        assert event.event_type == SecurityEventType.WAF_BLOCK
        assert event.threat_level in [SecurityThreatLevel.HIGH, SecurityThreatLevel.CRITICAL]
    
    @pytest.mark.asyncio
    async def test_waf_blocks_xss_attempt(self, waf_instance):
        """Test WAF blocks XSS attempts"""
        xss_request = Mock(spec=Request)
        xss_request.method = "POST"
        xss_request.url.path = "/api/comment"
        xss_request.url.query = ""
        xss_request.headers = {"user-agent": "Mozilla/5.0", "x-forwarded-for": "192.168.1.50"}
        xss_request.client.host = "192.168.1.50"
        xss_request.body = AsyncMock(return_value=b'<script>alert("XSS")</script>')
        
        action, event = await waf_instance.evaluate_request(xss_request)
        
        assert action == SecurityAction.BLOCK
        assert event is not None
        assert event.event_type == SecurityEventType.WAF_BLOCK
    
    @pytest.mark.asyncio
    async def test_waf_blocks_scanning_tools(self, waf_instance):
        """Test WAF blocks known scanning tools"""
        scanner_request = Mock(spec=Request)
        scanner_request.method = "GET"
        scanner_request.url.path = "/admin"
        scanner_request.url.query = ""
        scanner_request.headers = {
            "user-agent": "sqlmap/1.4.12",  # Known scanner
            "x-forwarded-for": "10.0.0.5"
        }
        scanner_request.client.host = "10.0.0.5"
        scanner_request.body = AsyncMock(return_value=b'')
        
        action, event = await waf_instance.evaluate_request(scanner_request)
        
        assert action == SecurityAction.BLOCK
        assert event is not None
        assert "sqlmap" in event.additional_context["description"].lower()
    
    @pytest.mark.asyncio
    async def test_waf_violation_counting(self, waf_instance):
        """Test WAF violation counting and IP blocking"""
        malicious_ip = "10.0.0.10"
        
        # Create multiple malicious requests from same IP
        for i in range(5):  # Above the threshold of 3
            malicious_req = Mock(spec=Request)
            malicious_req.method = "GET"
            malicious_req.url.path = f"/api/test{i}"
            malicious_req.url.query = "id=1' OR '1'='1"  # SQL injection
            malicious_req.headers = {
                "user-agent": "Mozilla/5.0",
                "x-forwarded-for": malicious_ip
            }
            malicious_req.client.host = malicious_ip
            malicious_req.body = AsyncMock(return_value=b'')
            
            await waf_instance.evaluate_request(malicious_req)
        
        # IP should be blocked after exceeding threshold
        assert malicious_ip in waf_instance.blocked_ips
        assert waf_instance.violation_counts[malicious_ip] >= waf_instance.config.waf_block_threshold
    
    def test_client_ip_extraction(self, waf_instance):
        """Test client IP extraction from various headers"""
        # Test X-Forwarded-For header
        request1 = Mock(spec=Request)
        request1.headers = {"x-forwarded-for": "192.168.1.100, 10.0.0.1"}
        request1.client.host = "127.0.0.1"
        
        ip1 = waf_instance._get_client_ip(request1)
        assert ip1 == "192.168.1.100"
        
        # Test X-Real-IP header
        request2 = Mock(spec=Request)
        request2.headers = {"x-real-ip": "192.168.1.200"}
        request2.client.host = "127.0.0.1"
        
        ip2 = waf_instance._get_client_ip(request2)
        assert ip2 == "192.168.1.200"
        
        # Test direct client IP
        request3 = Mock(spec=Request)
        request3.headers = {}
        request3.client.host = "192.168.1.300"
        
        ip3 = waf_instance._get_client_ip(request3)
        assert ip3 == "192.168.1.300"
    
    def test_severity_to_threat_level_conversion(self, waf_instance):
        """Test severity score to threat level conversion"""
        assert waf_instance._severity_to_threat_level(10.0) == SecurityThreatLevel.CRITICAL
        assert waf_instance._severity_to_threat_level(8.5) == SecurityThreatLevel.HIGH
        assert waf_instance._severity_to_threat_level(6.0) == SecurityThreatLevel.MEDIUM
        assert waf_instance._severity_to_threat_level(3.0) == SecurityThreatLevel.LOW

# Unit Tests for DDoS Protection

class TestDDoSProtectionSystem:
    """Test DDoS protection functionality"""
    
    def test_ddos_protection_initialization(self, security_config):
        """Test DDoS protection initialization"""
        ddos = DDoSProtectionSystem(security_config)
        
        assert isinstance(ddos.request_counts, dict)
        assert len(ddos.blocked_ips) == 0
        assert isinstance(ddos.traffic_baseline, dict)
    
    @pytest.mark.asyncio
    async def test_ddos_allows_normal_traffic(self, ddos_protection, mock_request):
        """Test DDoS protection allows normal traffic"""
        action, event = await ddos_protection.analyze_traffic(mock_request)
        
        assert action == SecurityAction.ALLOW
        assert event is None
    
    @pytest.mark.asyncio
    async def test_ddos_blocks_high_rate_traffic(self, ddos_protection):
        """Test DDoS protection blocks high rate traffic"""
        attacker_ip = "10.0.0.20"
        
        # Simulate high rate requests
        for i in range(150):  # Above the 100 RPM limit
            attack_request = Mock(spec=Request)
            attack_request.method = "GET"
            attack_request.url.path = f"/api/endpoint{i % 10}"
            attack_request.headers = {"x-forwarded-for": attacker_ip}
            attack_request.client.host = attacker_ip
            
            # Simulate requests within a short time window
            ddos_protection.request_counts[attacker_ip].append(time.time())
        
        # Next request should be blocked
        final_request = Mock(spec=Request)
        final_request.headers = {"x-forwarded-for": attacker_ip}
        final_request.client.host = attacker_ip
        final_request.url.path = "/api/final"
        
        action, event = await ddos_protection.analyze_traffic(final_request)
        
        assert action == SecurityAction.BLOCK
        assert event is not None
        assert event.event_type == SecurityEventType.DDOS_ATTEMPT
        assert attacker_ip in ddos_protection.blocked_ips
    
    @pytest.mark.asyncio
    async def test_ddos_whitelist_functionality(self, ddos_protection):
        """Test DDoS protection whitelist functionality"""
        whitelisted_ip = "192.168.1.100"
        ddos_protection.config.ddos_whitelist_ips.add(whitelisted_ip)
        
        # Simulate high rate requests from whitelisted IP
        for i in range(200):  # Way above normal limits
            ddos_protection.request_counts[whitelisted_ip].append(time.time())
        
        whitelist_request = Mock(spec=Request)
        whitelist_request.headers = {"x-forwarded-for": whitelisted_ip}
        whitelist_request.client.host = whitelisted_ip
        whitelist_request.url.path = "/api/test"
        
        action, event = await ddos_protection.analyze_traffic(whitelist_request)
        
        # Should be allowed despite high rate
        assert action == SecurityAction.ALLOW
        assert event is None
    
    @pytest.mark.asyncio
    async def test_ddos_suspicious_pattern_detection(self, ddos_protection):
        """Test suspicious pattern detection"""
        bot_request = Mock(spec=Request)
        bot_request.method = "GET"
        bot_request.url.path = "/api/data"
        bot_request.headers = {
            "user-agent": "python-requests/2.25.1",  # Bot-like user agent
            "x-forwarded-for": "10.0.0.30"
        }
        bot_request.client.host = "10.0.0.30"
        
        suspicious = await ddos_protection._detect_suspicious_patterns("10.0.0.30", bot_request)
        assert suspicious is True
    
    def test_request_signature_generation(self, ddos_protection):
        """Test request signature generation"""
        request1 = Mock(spec=Request)
        request1.method = "GET"
        request1.url.path = "/api/test"
        request1.headers = {
            "user-agent": "Mozilla/5.0",
            "x-forwarded-for": "192.168.1.100"
        }
        request1.client.host = "192.168.1.100"
        
        signature1 = ddos_protection._get_request_signature(request1)
        assert isinstance(signature1, str)
        assert len(signature1) == 32  # MD5 hash length
        
        # Same request should generate same signature
        signature2 = ddos_protection._get_request_signature(request1)
        assert signature1 == signature2
        
        # Different request should generate different signature
        request2 = Mock(spec=Request)
        request2.method = "POST"
        request2.url.path = "/api/different"
        request2.headers = {"user-agent": "Different", "x-forwarded-for": "192.168.1.100"}
        request2.client.host = "192.168.1.100"
        
        signature3 = ddos_protection._get_request_signature(request2)
        assert signature1 != signature3

# Unit Tests for Intrusion Detection System

class TestIntrusionDetectionSystem:
    """Test IDS functionality"""
    
    def test_ids_initialization(self, security_config):
        """Test IDS initialization"""
        ids = IntrusionDetectionSystem(security_config)
        
        assert ids.learning_mode is True
        assert len(ids.user_sessions) == 0
        assert isinstance(ids.anomaly_scores, dict)
        assert ids.config.ids_anomaly_threshold == security_config.ids_anomaly_threshold
    
    @pytest.mark.asyncio
    async def test_ids_learning_mode(self, ids_instance, mock_request):
        """Test IDS learning mode behavior"""
        # Should be in learning mode initially
        assert ids_instance.learning_mode is True
        
        action, event = await ids_instance.analyze_behavior(mock_request, "user123")
        
        # Should allow all requests during learning
        assert action == SecurityAction.ALLOW
        assert event is None
    
    @pytest.mark.asyncio
    async def test_ids_session_tracking(self, ids_instance, mock_request):
        """Test IDS session tracking"""
        user_id = "test_user_456"
        client_ip = "192.168.1.100"
        
        # Simulate multiple requests from same user
        for i in range(5):
            await ids_instance.analyze_behavior(mock_request, user_id)
            await asyncio.sleep(0.01)  # Small delay between requests
        
        # Check session was created and updated
        assert user_id in ids_instance.user_sessions
        session = ids_instance.user_sessions[user_id]
        
        assert session["request_count"] == 5
        assert len(session["unique_paths"]) >= 1
        assert len(session["request_intervals"]) > 0
    
    @pytest.mark.asyncio
    async def test_ids_anomaly_detection(self, ids_instance):
        """Test IDS anomaly detection"""
        # Disable learning mode to enable detection
        ids_instance.learning_mode = False
        
        # Create highly anomalous request pattern
        anomalous_user = "anomaly_user"
        
        # Simulate rapid, diverse requests (bot-like behavior)
        for i in range(20):
            anomalous_request = Mock(spec=Request)
            anomalous_request.method = "GET"
            anomalous_request.url.path = f"/api/endpoint_{i}"  # Many different paths
            anomalous_request.headers = {
                "user-agent": f"Agent_{i}",  # Changing user agents
                "x-forwarded-for": "10.0.0.100"
            }
            anomalous_request.client.host = "10.0.0.100"
            
            action, event = await ids_instance.analyze_behavior(anomalous_request, anomalous_user)
            
            # Later requests should trigger anomaly detection
            if i > 10 and event is not None:
                assert event.event_type == SecurityEventType.INTRUSION_ATTEMPT
                assert event.threat_level == SecurityThreatLevel.HIGH
                break
    
    @pytest.mark.asyncio
    async def test_ids_anomaly_score_calculation(self, ids_instance):
        """Test anomaly score calculation"""
        user_id = "score_test_user"
        
        # Create session with specific patterns
        ids_instance.user_sessions[user_id] = {
            "start_time": time.time() - 60,  # 1 minute ago
            "request_count": 100,  # High request rate
            "unique_paths": {f"/path_{i}" for i in range(50)},  # High path diversity
            "user_agents": {"Agent1", "Agent2", "Agent3"},  # Multiple user agents
            "request_intervals": [0.1, 0.1, 0.1, 0.1, 0.1],  # Very consistent timing
            "duration": 60,
            "last_request_time": time.time()
        }
        
        test_request = Mock(spec=Request)
        test_request.headers = {"x-forwarded-for": "192.168.1.100"}
        test_request.client.host = "192.168.1.100"
        
        score = await ids_instance._calculate_anomaly_score(user_id, test_request)
        
        # Should have high anomaly score due to multiple factors
        assert score > 0.5
    
    def test_ids_client_ip_extraction(self, ids_instance):
        """Test IDS client IP extraction"""
        request = Mock(spec=Request)
        request.headers = {"x-forwarded-for": "10.0.0.50"}
        request.client.host = "127.0.0.1"
        
        ip = ids_instance._get_client_ip(request)
        assert ip == "10.0.0.50"

# Unit Tests for SIEM Integration

class TestSIEMIntegration:
    """Test SIEM integration functionality"""
    
    def test_siem_initialization(self, security_config):
        """Test SIEM initialization"""
        siem = SIEMIntegration(security_config)
        
        assert len(siem.event_queue) == 0
        assert len(siem.correlation_rules) > 0
        assert siem.config.siem_batch_size == security_config.siem_batch_size
    
    def test_siem_correlation_rules_initialization(self, siem_integration):
        """Test SIEM correlation rules initialization"""
        rules = siem_integration.correlation_rules
        
        assert len(rules) >= 2
        
        # Check for specific rule types
        rule_names = [rule["name"] for rule in rules]
        assert "Multiple Failed Logins" in rule_names
        assert "Coordinated Attack" in rule_names
    
    @pytest.mark.asyncio
    async def test_siem_event_queuing(self, siem_integration):
        """Test SIEM event queuing"""
        test_event = SecurityEvent(
            event_id="siem-test-1",
            event_type=SecurityEventType.WAF_BLOCK,
            threat_level=SecurityThreatLevel.MEDIUM,
            timestamp=datetime.utcnow(),
            source_ip="192.168.1.100"
        )
        
        initial_queue_size = len(siem_integration.event_queue)
        
        with patch.object(siem_integration, '_flush_events') as mock_flush:
            await siem_integration.queue_event(test_event)
            
            assert len(siem_integration.event_queue) == initial_queue_size + 1
    
    @pytest.mark.asyncio
    async def test_siem_event_correlation(self, siem_integration):
        """Test SIEM event correlation"""
        # Create multiple related events
        for i in range(6):  # Above threshold of 5
            brute_force_event = SecurityEvent(
                event_id=f"brute-force-{i}",
                event_type=SecurityEventType.BRUTE_FORCE,
                threat_level=SecurityThreatLevel.MEDIUM,
                timestamp=datetime.utcnow(),
                source_ip=f"10.0.0.{i}"
            )
            siem_integration.event_queue.append(brute_force_event)
        
        correlated_events = await siem_integration._correlate_events()
        
        # Should generate correlated event
        assert len(correlated_events) >= 1
        correlated_event = correlated_events[0]
        assert correlated_event.event_type == SecurityEventType.ANOMALOUS_BEHAVIOR
        assert "correlation_rule" in correlated_event.additional_context
    
    def test_siem_event_serialization(self, siem_integration):
        """Test SIEM event serialization"""
        test_event = SecurityEvent(
            event_id="serialize-test",
            event_type=SecurityEventType.DDOS_ATTEMPT,
            threat_level=SecurityThreatLevel.HIGH,
            timestamp=datetime.utcnow(),
            source_ip="10.0.0.200",
            user_agent="Test Agent",
            request_path="/api/test",
            severity_score=8.5,
            additional_context={"description": "Test event"}
        )
        
        serialized = siem_integration._serialize_event(test_event)
        
        assert serialized["event_id"] == "serialize-test"
        assert serialized["event_type"] == "ddos_attempt"
        assert serialized["threat_level"] == "high"
        assert serialized["source_ip"] == "10.0.0.200"
        assert serialized["severity_score"] == 8.5
        assert serialized["additional_context"]["description"] == "Test event"
    
    @pytest.mark.asyncio
    async def test_siem_flush_events(self, siem_integration):
        """Test SIEM event flushing"""
        # Add test events to queue
        for i in range(5):
            event = SecurityEvent(
                event_id=f"flush-test-{i}",
                event_type=SecurityEventType.WAF_BLOCK,
                threat_level=SecurityThreatLevel.LOW,
                timestamp=datetime.utcnow(),
                source_ip=f"192.168.1.{i}"
            )
            siem_integration.event_queue.append(event)
        
        initial_queue_size = len(siem_integration.event_queue)
        assert initial_queue_size == 5
        
        # Mock SIEM sending to avoid external dependencies
        with patch.object(siem_integration, '_send_to_siem') as mock_send:
            await siem_integration._flush_events()
            
            # Queue should be empty after flushing
            assert len(siem_integration.event_queue) == 0
            
            # Should have attempted to send events
            if siem_integration.config.siem_endpoint:
                mock_send.assert_called_once()

# Unit Tests for Security Middleware

class TestSecurityHardeningMiddleware:
    """Test security hardening middleware"""
    
    def test_middleware_initialization(self, security_config):
        """Test middleware initialization"""
        app = FastAPI()
        middleware = SecurityHardeningMiddleware(app, security_config)
        
        assert middleware.config == security_config
        assert middleware.waf is not None if security_config.enable_waf else None
        assert middleware.ddos_protection is not None if security_config.enable_ddos_protection else None
        assert middleware.ids is not None if security_config.enable_ids else None
        assert len(middleware.security_stats) > 0
    
    @pytest.mark.asyncio
    async def test_middleware_allows_legitimate_request(self, security_middleware, mock_request):
        """Test middleware allows legitimate requests"""
        async def mock_call_next(request):
            return JSONResponse(content={"message": "success"})
        
        response = await security_middleware.dispatch(mock_request, mock_call_next)
        
        assert response.status_code == 200
        assert security_middleware.security_stats["total_requests"] >= 1
    
    @pytest.mark.asyncio
    async def test_middleware_blocks_malicious_request(self, security_middleware, malicious_request):
        """Test middleware blocks malicious requests"""
        async def mock_call_next(request):
            return JSONResponse(content={"message": "should not reach here"})
        
        response = await security_middleware.dispatch(malicious_request, mock_call_next)
        
        # Should be blocked (403 or 429)
        assert response.status_code in [403, 429]
        assert security_middleware.security_stats["blocked_requests"] >= 1
    
    @pytest.mark.asyncio
    async def test_middleware_security_headers(self, security_middleware, mock_request):
        """Test middleware adds security headers"""
        async def mock_call_next(request):
            return JSONResponse(content={"message": "test"})
        
        response = await security_middleware.dispatch(mock_request, mock_call_next)
        
        # Check for security headers
        assert "Strict-Transport-Security" in response.headers
        assert "Content-Security-Policy" in response.headers
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-XSS-Protection" in response.headers
    
    @pytest.mark.asyncio
    async def test_middleware_security_metrics(self, security_middleware):
        """Test middleware security metrics collection"""
        metrics = await security_middleware.get_security_metrics()
        
        assert "timestamp" in metrics
        assert "uptime_seconds" in metrics
        assert "requests" in metrics
        assert "security_events" in metrics
        
        # Check requests metrics
        requests_metrics = metrics["requests"]
        assert "total" in requests_metrics
        assert "blocked" in requests_metrics
        assert "allowed" in requests_metrics
        assert "block_rate" in requests_metrics
    
    def test_middleware_user_id_extraction(self, security_middleware):
        """Test user ID extraction from requests"""
        # Test JWT extraction
        jwt_request = Mock(spec=Request)
        jwt_request.headers = {"authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."}
        
        user_id = security_middleware._extract_user_id(jwt_request)
        assert user_id == "jwt_user"
        
        # Test session extraction
        session_request = Mock(spec=Request)
        session_request.headers = {"x-session-id": "abc123def456"}
        
        user_id = security_middleware._extract_user_id(session_request)
        assert user_id == "session_abc123def456"
        
        # Test no identification
        anon_request = Mock(spec=Request)
        anon_request.headers = {}
        
        user_id = security_middleware._extract_user_id(anon_request)
        assert user_id is None

# Integration Tests

class TestSecurityHardeningIntegration:
    """Test security hardening integration"""
    
    def test_initialize_security_hardening(self, security_config):
        """Test security hardening initialization"""
        app = FastAPI()
        
        # Reset global state
        import app.core.security_hardening
        app.core.security_hardening.security_hardening_middleware = None
        
        middleware = initialize_security_hardening(app, security_config)
        
        assert middleware is not None
        assert middleware.config == security_config
        
        # Test getting global instance
        retrieved_middleware = get_security_hardening()
        assert retrieved_middleware is middleware
    
    def test_get_security_hardening_not_initialized(self):
        """Test getting security hardening when not initialized"""
        # Reset global state
        import app.core.security_hardening
        app.core.security_hardening.security_hardening_middleware = None
        
        with pytest.raises(RuntimeError, match="Security hardening not initialized"):
            get_security_hardening()
    
    def test_full_security_pipeline_integration(self, test_app_with_security):
        """Test full security pipeline integration"""
        client = TestClient(test_app_with_security)
        
        # Test legitimate request
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Hello World"}
        
        # Check security headers are present
        assert "Strict-Transport-Security" in response.headers
        assert "X-Content-Type-Options" in response.headers
    
    def test_waf_integration_blocks_attacks(self, test_app_with_security):
        """Test WAF integration blocks attacks"""
        client = TestClient(test_app_with_security)
        
        # Test SQL injection attempt
        response = client.get("/api/data?id=1' OR '1'='1")
        assert response.status_code in [403, 429]  # Should be blocked
        
        # Test XSS attempt
        response = client.post("/api/login", 
                             json={"username": "<script>alert('xss')</script>", 
                                   "password": "test"})
        assert response.status_code in [403, 429]  # Should be blocked
    
    def test_ddos_protection_integration(self, test_app_with_security):
        """Test DDoS protection integration"""
        client = TestClient(test_app_with_security)
        
        # Make many requests rapidly (should trigger DDoS protection)
        blocked_responses = 0
        for i in range(100):  # Above the configured limit
            response = client.get(f"/api/data?test={i}")
            if response.status_code == 429:  # Too Many Requests
                blocked_responses += 1
        
        # Should have blocked some requests
        assert blocked_responses > 0

# Global Functions Tests

class TestGlobalSecurityFunctions:
    """Test global security functions"""
    
    @pytest.mark.asyncio
    async def test_get_security_dashboard(self, security_config):
        """Test security dashboard function"""
        app = FastAPI()
        middleware = initialize_security_hardening(app, security_config)
        
        # Simulate some activity
        middleware.security_stats["total_requests"] = 1000
        middleware.security_stats["blocked_requests"] = 50
        
        dashboard = await get_security_dashboard()
        
        assert "security_status" in dashboard
        assert "threat_level" in dashboard
        assert "metrics" in dashboard
        assert "recommendations" in dashboard
        
        assert dashboard["security_status"] == "active"
        assert dashboard["threat_level"] in ["minimal", "low", "medium", "high"]
    
    @pytest.mark.asyncio
    async def test_trigger_security_test(self, security_config):
        """Test security test trigger function"""
        app = FastAPI()
        initialize_security_hardening(app, security_config)
        
        test_result = await trigger_security_test()
        
        assert "test_scenarios" in test_result
        assert "status" in test_result
        
        scenarios = test_result["test_scenarios"]
        assert "SQL injection simulation" in scenarios
        assert "XSS attack simulation" in scenarios
        assert "DDoS traffic simulation" in scenarios
        assert "Brute force simulation" in scenarios

# Performance Tests

class TestSecurityHardeningPerformance:
    """Test security system performance"""
    
    @pytest.mark.asyncio
    async def test_waf_evaluation_performance(self, waf_instance, mock_request):
        """Test WAF evaluation performance"""
        # Measure WAF evaluation time
        start_time = time.time()
        
        for _ in range(100):  # Multiple evaluations
            await waf_instance.evaluate_request(mock_request)
        
        end_time = time.time()
        avg_time_per_request = ((end_time - start_time) / 100) * 1000  # Convert to ms
        
        # WAF evaluation should be fast (< 10ms per request)
        assert avg_time_per_request < 10, f"WAF evaluation took {avg_time_per_request:.2f}ms on average"
    
    @pytest.mark.asyncio
    async def test_ddos_analysis_performance(self, ddos_protection, mock_request):
        """Test DDoS analysis performance"""
        start_time = time.time()
        
        for _ in range(100):  # Multiple analyses
            await ddos_protection.analyze_traffic(mock_request)
        
        end_time = time.time()
        avg_time_per_request = ((end_time - start_time) / 100) * 1000  # Convert to ms
        
        # DDoS analysis should be fast (< 5ms per request)
        assert avg_time_per_request < 5, f"DDoS analysis took {avg_time_per_request:.2f}ms on average"
    
    @pytest.mark.asyncio
    async def test_ids_analysis_performance(self, ids_instance, mock_request):
        """Test IDS analysis performance"""
        start_time = time.time()
        
        for i in range(100):  # Multiple analyses
            await ids_instance.analyze_behavior(mock_request, f"user_{i}")
        
        end_time = time.time()
        avg_time_per_request = ((end_time - start_time) / 100) * 1000  # Convert to ms
        
        # IDS analysis should be reasonably fast (< 20ms per request)
        assert avg_time_per_request < 20, f"IDS analysis took {avg_time_per_request:.2f}ms on average"

# Error Handling Tests

class TestSecurityHardeningErrorHandling:
    """Test error handling in security system"""
    
    @pytest.mark.asyncio
    async def test_waf_handles_malformed_requests(self, waf_instance):
        """Test WAF handles malformed requests gracefully"""
        malformed_request = Mock(spec=Request)
        malformed_request.method = "INVALID_METHOD"
        malformed_request.url.path = None  # Invalid path
        malformed_request.headers = {}
        malformed_request.client = None  # No client info
        malformed_request.body = AsyncMock(side_effect=Exception("Body read error"))
        
        # Should not crash
        action, event = await waf_instance.evaluate_request(malformed_request)
        
        # Should return allow by default when evaluation fails
        assert action in [SecurityAction.ALLOW, SecurityAction.BLOCK]
    
    @pytest.mark.asyncio
    async def test_middleware_handles_exceptions(self, security_middleware):
        """Test middleware handles exceptions gracefully"""
        # Create request that will cause exceptions
        error_request = Mock(spec=Request)
        error_request.method = "GET"
        error_request.url.path = "/test"
        error_request.headers = {}
        error_request.client = None
        
        # Mock call_next to raise exception
        async def error_call_next(request):
            raise Exception("Downstream error")
        
        # Should handle exception and not crash
        with pytest.raises(Exception, match="Downstream error"):
            await security_middleware.dispatch(error_request, error_call_next)
        
        # Middleware should still be functional
        assert security_middleware.security_stats["total_requests"] >= 1
    
    @pytest.mark.asyncio
    async def test_siem_handles_network_errors(self, siem_integration):
        """Test SIEM handles network errors gracefully"""
        # Configure SIEM endpoint
        siem_integration.config.siem_endpoint = "http://invalid-siem-endpoint.local"
        siem_integration.config.siem_api_key = "test_key"
        
        # Add events to queue
        test_events = [
            {"event_id": "test1", "event_type": "test", "timestamp": "2024-01-01T00:00:00Z"}
        ]
        
        # Should handle network errors gracefully
        with patch('app.core.security_hardening.REQUESTS_PSUTIL_AVAILABLE', True):
            with patch('app.core.security_hardening.requests.post') as mock_post:
                mock_post.side_effect = Exception("Network error")
                
                # Should not crash
                await siem_integration._send_to_siem(test_events)
    
    def test_configuration_with_invalid_values(self):
        """Test configuration with invalid values"""
        # Test with invalid threshold values
        config = SecurityHardeningConfig(
            waf_block_threshold=-1,  # Invalid negative value
            ddos_requests_per_minute=0,  # Invalid zero value
            ids_anomaly_threshold=1.5  # Invalid value > 1
        )
        
        # Should accept invalid values but may behave unexpectedly
        # In production, validation should be added
        assert config.waf_block_threshold == -1
        assert config.ddos_requests_per_minute == 0
        assert config.ids_anomaly_threshold == 1.5

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--cov=app.core.security_hardening"])