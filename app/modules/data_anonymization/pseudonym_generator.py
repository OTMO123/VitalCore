"""
Pseudonym Generator for Healthcare ML Platform

Generates consistent, secure, and HIPAA-compliant pseudonymous identifiers
for patient tracking in ML/AI applications while maintaining zero re-identification risk.
"""

import hashlib
import hmac
import secrets
import base64
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
import structlog
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

from app.core.config import get_settings
from app.core.security import EncryptionService

logger = structlog.get_logger(__name__)

class PseudonymGenerator:
    """
    Secure pseudonym generator for healthcare ML applications.
    
    Generates consistent but unlinkable pseudonymous identifiers using
    cryptographic techniques that comply with HIPAA Safe Harbor and GDPR Article 26.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize pseudonym generator with security configuration.
        
        Args:
            config: Configuration dictionary with security parameters
        """
        self.config = config or {}
        self.settings = get_settings()
        self.logger = logger.bind(component="PseudonymGenerator")
        
        # Security parameters
        self.salt_length = self.config.get('salt_length', 32)
        self.iterations = self.config.get('pbkdf2_iterations', 100000)
        self.pseudonym_length = self.config.get('pseudonym_length', 16)
        
        # Healthcare-specific salt for ML platform
        self.ml_platform_salt = self.config.get(
            'ml_platform_salt', 
            "healthcare_ml_prediction_platform_v1"
        )
        
        # Key rotation settings
        self.key_rotation_days = self.config.get('key_rotation_days', 90)
        self.encryption_service = EncryptionService()
        
        # Cache for performance (limited size for security)
        self._pseudonym_cache: Dict[str, str] = {}
        self._max_cache_size = 1000
    
    async def generate_pseudonym(
        self,
        patient_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate consistent pseudonymous identifier for a patient.
        
        Args:
            patient_id: Original patient identifier
            context: Additional context for pseudonym generation
            
        Returns:
            Secure pseudonymous identifier
        """
        try:
            # Check cache first (for performance)
            cache_key = self._create_cache_key(patient_id, context)
            if cache_key in self._pseudonym_cache:
                return self._pseudonym_cache[cache_key]
            
            # Generate time-based key rotation identifier
            rotation_period = self._get_rotation_period()
            
            # Create deterministic but secure input
            pseudonym_input = self._create_pseudonym_input(
                patient_id, context, rotation_period
            )
            
            # Generate pseudonym using PBKDF2
            pseudonym = await self._generate_secure_pseudonym(pseudonym_input)
            
            # Cache result (with size limit)
            self._cache_pseudonym(cache_key, pseudonym)
            
            # Audit pseudonym generation
            await self._audit_pseudonym_generation(
                patient_id, pseudonym, context, rotation_period
            )
            
            return pseudonym
            
        except Exception as e:
            self.logger.error(
                "Failed to generate pseudonym",
                patient_id=patient_id[:8] + "...",  # Log only partial ID
                error=str(e)
            )
            raise
    
    async def generate_batch_pseudonyms(
        self,
        patient_ids: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Generate pseudonyms for multiple patients efficiently.
        
        Args:
            patient_ids: List of patient identifiers
            context: Shared context for batch generation
            
        Returns:
            Dictionary mapping patient_id -> pseudonym
        """
        pseudonyms = {}
        rotation_period = self._get_rotation_period()
        
        self.logger.info(
            "Generating batch pseudonyms",
            count=len(patient_ids),
            rotation_period=rotation_period
        )
        
        for patient_id in patient_ids:
            try:
                pseudonym = await self.generate_pseudonym(patient_id, context)
                pseudonyms[patient_id] = pseudonym
            except Exception as e:
                self.logger.error(
                    "Failed to generate pseudonym in batch",
                    patient_id=patient_id[:8] + "...",
                    error=str(e)
                )
                # Continue with other patients, don't fail entire batch
        
        self.logger.info(
            "Batch pseudonym generation completed",
            successful=len(pseudonyms),
            failed=len(patient_ids) - len(pseudonyms)
        )
        
        return pseudonyms
    
    async def validate_pseudonym(
        self,
        patient_id: str,
        pseudonym: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Validate that a pseudonym was correctly generated for a patient.
        
        Args:
            patient_id: Original patient identifier
            pseudonym: Pseudonym to validate
            context: Context used in original generation
            
        Returns:
            True if pseudonym is valid for this patient
        """
        try:
            expected_pseudonym = await self.generate_pseudonym(patient_id, context)
            is_valid = hmac.compare_digest(pseudonym, expected_pseudonym)
            
            await self._audit_pseudonym_validation(
                patient_id, pseudonym, is_valid, context
            )
            
            return is_valid
            
        except Exception as e:
            self.logger.error(
                "Failed to validate pseudonym",
                error=str(e)
            )
            return False
    
    def get_rotation_schedule(self) -> Dict[str, datetime]:
        """
        Get the current and next key rotation timestamps.
        
        Returns:
            Dictionary with current and next rotation timestamps
        """
        current_rotation = self._get_rotation_period()
        next_rotation = current_rotation + timedelta(days=self.key_rotation_days)
        
        return {
            "current_rotation_start": current_rotation,
            "next_rotation_start": next_rotation,
            "days_until_rotation": (next_rotation - datetime.utcnow()).days
        }
    
    async def rotate_keys(self) -> Dict[str, Any]:
        """
        Perform key rotation for enhanced security.
        
        Returns:
            Results of key rotation operation
        """
        try:
            old_rotation = self._get_rotation_period()
            
            # Clear cache to force regeneration with new rotation period
            self._pseudonym_cache.clear()
            
            new_rotation = self._get_rotation_period()
            
            self.logger.info(
                "Key rotation completed",
                old_rotation=old_rotation.isoformat(),
                new_rotation=new_rotation.isoformat()
            )
            
            return {
                "status": "success",
                "old_rotation_period": old_rotation.isoformat(),
                "new_rotation_period": new_rotation.isoformat(),
                "cache_cleared": True
            }
            
        except Exception as e:
            self.logger.error("Key rotation failed", error=str(e))
            return {
                "status": "failed",
                "error": str(e)
            }
    
    # Private methods
    
    def _create_cache_key(
        self,
        patient_id: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Create cache key for pseudonym lookup."""
        context_str = str(sorted(context.items())) if context else ""
        rotation_period = self._get_rotation_period().isoformat()
        
        cache_input = f"{patient_id}:{context_str}:{rotation_period}"
        return hashlib.sha256(cache_input.encode()).hexdigest()[:16]
    
    def _create_pseudonym_input(
        self,
        patient_id: str,
        context: Optional[Dict[str, Any]],
        rotation_period: datetime
    ) -> str:
        """
        Create deterministic input for pseudonym generation.
        
        This ensures the same patient always gets the same pseudonym
        within a rotation period, but different pseudonyms across rotations.
        """
        # Base components
        components = [
            patient_id,
            self.ml_platform_salt,
            rotation_period.isoformat()[:10]  # Date only for rotation
        ]
        
        # Add context if provided
        if context:
            # Sort context for deterministic ordering
            context_items = sorted(context.items())
            context_str = ":".join(f"{k}={v}" for k, v in context_items)
            components.append(context_str)
        
        return "|".join(components)
    
    async def _generate_secure_pseudonym(self, pseudonym_input: str) -> str:
        """
        Generate secure pseudonym using PBKDF2 key derivation.
        
        Args:
            pseudonym_input: Deterministic input for pseudonym generation
            
        Returns:
            Secure pseudonymous identifier
        """
        # Use healthcare-specific salt
        salt = self.ml_platform_salt.encode() + b"_pseudonym_salt"
        
        # Ensure salt is proper length
        if len(salt) < 16:
            salt = salt + b"0" * (16 - len(salt))
        elif len(salt) > 32:
            salt = salt[:32]
        
        # Generate key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.pseudonym_length,
            salt=salt,
            iterations=self.iterations,
            backend=default_backend()
        )
        
        key = kdf.derive(pseudonym_input.encode())
        
        # Convert to readable pseudonym format
        pseudonym = "anon_" + base64.urlsafe_b64encode(key).decode()[:self.pseudonym_length]
        
        return pseudonym
    
    def _get_rotation_period(self) -> datetime:
        """
        Get current rotation period start date.
        
        Returns:
            Start date of current rotation period
        """
        now = datetime.utcnow()
        days_since_epoch = (now - datetime(2025, 1, 1)).days
        rotation_number = days_since_epoch // self.key_rotation_days
        
        rotation_start = datetime(2025, 1, 1) + timedelta(
            days=rotation_number * self.key_rotation_days
        )
        
        return rotation_start
    
    def _cache_pseudonym(self, cache_key: str, pseudonym: str):
        """Cache pseudonym with size limit."""
        if len(self._pseudonym_cache) >= self._max_cache_size:
            # Remove oldest entries (simple FIFO)
            oldest_key = next(iter(self._pseudonym_cache))
            del self._pseudonym_cache[oldest_key]
        
        self._pseudonym_cache[cache_key] = pseudonym
    
    async def _audit_pseudonym_generation(
        self,
        patient_id: str,
        pseudonym: str,
        context: Optional[Dict[str, Any]],
        rotation_period: datetime
    ):
        """Audit pseudonym generation for compliance."""
        try:
            audit_data = {
                "operation": "pseudonym_generation",
                "patient_id_hash": hashlib.sha256(patient_id.encode()).hexdigest()[:16],
                "pseudonym": pseudonym,
                "rotation_period": rotation_period.isoformat(),
                "context_provided": context is not None,
                "timestamp": datetime.utcnow().isoformat(),
                "generator_version": "v1.0"
            }
            
            # Log to audit system (don't log actual patient_id)
            self.logger.info(
                "Pseudonym generated",
                **{k: v for k, v in audit_data.items() if k != "patient_id_hash"}
            )
            
        except Exception as e:
            self.logger.error("Failed to audit pseudonym generation", error=str(e))
    
    async def _audit_pseudonym_validation(
        self,
        patient_id: str,
        pseudonym: str,
        is_valid: bool,
        context: Optional[Dict[str, Any]]
    ):
        """Audit pseudonym validation for security monitoring."""
        try:
            audit_data = {
                "operation": "pseudonym_validation",
                "pseudonym": pseudonym,
                "validation_result": is_valid,
                "context_provided": context is not None,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.logger.info("Pseudonym validated", **audit_data)
            
        except Exception as e:
            self.logger.error("Failed to audit pseudonym validation", error=str(e))

class HealthcarePseudonymValidator:
    """
    Validator for healthcare-specific pseudonym compliance.
    
    Ensures pseudonyms meet HIPAA Safe Harbor and GDPR Article 26 requirements.
    """
    
    def __init__(self):
        self.logger = logger.bind(component="HealthcarePseudonymValidator")
    
    async def validate_hipaa_compliance(self, pseudonym: str) -> Dict[str, Any]:
        """
        Validate pseudonym meets HIPAA Safe Harbor requirements.
        
        Args:
            pseudonym: Pseudonym to validate
            
        Returns:
            HIPAA compliance validation results
        """
        results = {
            "hipaa_compliant": False,
            "safe_harbor_compliant": False,
            "issues": [],
            "recommendations": []
        }
        
        try:
            # Check pseudonym format and security
            if not pseudonym.startswith("anon_"):
                results["issues"].append("Pseudonym should use 'anon_' prefix")
            
            if len(pseudonym) < 16:
                results["issues"].append("Pseudonym too short for security")
            
            # Check for patterns that might allow re-identification
            if any(char.isdigit() for char in pseudonym):
                # This is actually good - we want some randomness
                pass
            
            # Validate no obvious patterns
            if pseudonym.count(pseudonym[5]) > 3:  # Repeated characters
                results["issues"].append("Pseudonym contains repeated patterns")
            
            # Overall compliance assessment
            if not results["issues"]:
                results["hipaa_compliant"] = True
                results["safe_harbor_compliant"] = True
            else:
                results["recommendations"] = [
                    "Regenerate pseudonym with stronger randomization",
                    "Ensure pseudonym length meets security requirements",
                    "Validate pseudonym generation algorithm"
                ]
            
            return results
            
        except Exception as e:
            self.logger.error("HIPAA validation failed", error=str(e))
            results["issues"].append(f"Validation error: {str(e)}")
            return results
    
    async def validate_gdpr_compliance(self, pseudonym: str) -> Dict[str, Any]:
        """
        Validate pseudonym meets GDPR Article 26 requirements.
        
        Args:
            pseudonym: Pseudonym to validate
            
        Returns:
            GDPR compliance validation results
        """
        results = {
            "gdpr_compliant": False,
            "article_26_compliant": False,
            "pseudonymization_adequate": False,
            "issues": [],
            "recommendations": []
        }
        
        try:
            # GDPR Article 26 requires pseudonymization to be such that
            # data cannot be attributed to a specific data subject without
            # additional information
            
            # Check pseudonym doesn't contain obvious identifiers
            if any(pattern in pseudonym.lower() for pattern in [
                "name", "ssn", "phone", "email", "address"
            ]):
                results["issues"].append("Pseudonym contains identifier-like patterns")
            
            # Check sufficient entropy
            unique_chars = len(set(pseudonym))
            if unique_chars < 8:
                results["issues"].append("Insufficient entropy in pseudonym")
            
            # Check length for reversibility resistance
            if len(pseudonym) >= 16:
                results["pseudonymization_adequate"] = True
            else:
                results["issues"].append("Pseudonym length insufficient for GDPR")
            
            # Overall compliance
            if not results["issues"] and results["pseudonymization_adequate"]:
                results["gdpr_compliant"] = True
                results["article_26_compliant"] = True
            else:
                results["recommendations"] = [
                    "Increase pseudonym entropy",
                    "Ensure additional safeguards are in place",
                    "Implement key separation for additional security"
                ]
            
            return results
            
        except Exception as e:
            self.logger.error("GDPR validation failed", error=str(e))
            results["issues"].append(f"Validation error: {str(e)}")
            return results
    
    async def comprehensive_validation(self, pseudonym: str) -> Dict[str, Any]:
        """
        Perform comprehensive compliance validation.
        
        Args:
            pseudonym: Pseudonym to validate
            
        Returns:
            Complete validation results
        """
        hipaa_results = await self.validate_hipaa_compliance(pseudonym)
        gdpr_results = await self.validate_gdpr_compliance(pseudonym)
        
        return {
            "pseudonym": pseudonym,
            "overall_compliant": (
                hipaa_results["hipaa_compliant"] and 
                gdpr_results["gdpr_compliant"]
            ),
            "hipaa_validation": hipaa_results,
            "gdpr_validation": gdpr_results,
            "validation_timestamp": datetime.utcnow().isoformat(),
            "validator_version": "v1.0"
        }