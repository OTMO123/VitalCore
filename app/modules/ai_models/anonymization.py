"""
Built-in Anonymization Pipeline for AI Models

Comprehensive anonymization system for protecting PHI/PII data before
processing with AI models, with support for offline operation and
de-anonymization capabilities.
"""

import asyncio
import hashlib
import hmac
import json
import re
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import logging

from sqlalchemy import Column, String, JSON, DateTime, Boolean, Text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID

from ...core.database import Base, get_db
from ...core.security import encryption_service
from ...modules.audit_logger.service import audit_logger
from ...modules.audit_logger.schemas import AuditEventType

logger = logging.getLogger(__name__)


class PHIType(str, Enum):
    """Types of PHI/PII that can be detected and anonymized."""
    NAME = "name"
    DATE = "date"
    PHONE = "phone"
    EMAIL = "email"
    SSN = "ssn"
    ADDRESS = "address"
    MEDICAL_RECORD_NUMBER = "medical_record_number"
    ACCOUNT_NUMBER = "account_number"
    IP_ADDRESS = "ip_address"
    BIOMETRIC = "biometric"
    PHOTO = "photo"
    DEVICE_ID = "device_id"
    URL = "url"
    GEOGRAPHIC = "geographic"
    OTHER = "other"


class AnonymizationMethod(str, Enum):
    """Methods for anonymizing detected PHI."""
    REPLACEMENT = "replacement"
    MASKING = "masking"
    GENERALIZATION = "generalization"
    SUPPRESSION = "suppression"
    NOISE_ADDITION = "noise_addition"
    DATE_SHIFTING = "date_shifting"


@dataclass
class PHIDetectionResult:
    """Result of PHI detection scan."""
    has_phi: bool
    phi_entities: List[Dict[str, Any]]
    phi_types: List[PHIType]
    phi_fields: List[str]
    field_types: Dict[str, PHIType]
    confidence_scores: Dict[str, float]
    total_phi_count: int


@dataclass
class AnonymizedData:
    """Result of anonymization process."""
    anonymized_data: Union[Dict[str, Any], str]
    anonymization_applied: bool
    phi_detected: bool
    phi_types: List[PHIType]
    anonymization_map_id: Optional[str]
    original_data_hash: str
    anonymization_method: AnonymizationMethod
    reversible: bool
    created_at: datetime


class AnonymizationMap(Base):
    """Database model for storing anonymization mappings."""
    __tablename__ = "anonymization_maps"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    map_id = Column(String, unique=True, nullable=False, index=True)
    
    # Original data reference (encrypted)
    original_data_hash = Column(String, nullable=False)
    encrypted_mapping = Column(Text, nullable=False)
    
    # Context information
    model_id = Column(String, nullable=False)
    context_type = Column(String, nullable=False)  # "inference_input", "inference_output"
    
    # PHI information
    phi_types_detected = Column(JSON, default=list)
    anonymization_method = Column(String, nullable=False)
    reversible = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)  # For automatic cleanup
    used_count = Column(Integer, default=0)
    last_accessed = Column(DateTime)
    
    # Compliance tracking
    user_id = Column(String, nullable=False)
    audit_trail = Column(JSON, default=dict)


class PHIDetector:
    """PHI/PII detection engine with healthcare focus."""
    
    def __init__(self):
        self.phi_patterns = self._initialize_phi_patterns()
        self.medical_keywords = self._load_medical_keywords()
        
    def _initialize_phi_patterns(self) -> Dict[PHIType, List[Dict]]:
        """Initialize PHI detection patterns."""
        patterns = {
            PHIType.SSN: [
                {
                    "pattern": r'\b\d{3}-\d{2}-\d{4}\b',
                    "confidence": 0.95
                },
                {
                    "pattern": r'\b\d{9}\b',
                    "confidence": 0.7,
                    "context_required": True
                }
            ],
            PHIType.PHONE: [
                {
                    "pattern": r'\b\d{3}-\d{3}-\d{4}\b',
                    "confidence": 0.9
                },
                {
                    "pattern": r'\(\d{3}\)\s*\d{3}-\d{4}',
                    "confidence": 0.9
                },
                {
                    "pattern": r'\b\d{10}\b',
                    "confidence": 0.6,
                    "context_required": True
                }
            ],
            PHIType.EMAIL: [
                {
                    "pattern": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                    "confidence": 0.95
                }
            ],
            PHIType.DATE: [
                {
                    "pattern": r'\b\d{1,2}/\d{1,2}/\d{4}\b',
                    "confidence": 0.8
                },
                {
                    "pattern": r'\b\d{4}-\d{2}-\d{2}\b',
                    "confidence": 0.85
                },
                {
                    "pattern": r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b',
                    "confidence": 0.9
                }
            ],
            PHIType.ADDRESS: [
                {
                    "pattern": r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct)\b',
                    "confidence": 0.8
                }
            ],
            PHIType.MEDICAL_RECORD_NUMBER: [
                {
                    "pattern": r'\bMRN[:\s]*([A-Z0-9]{6,12})\b',
                    "confidence": 0.95
                },
                {
                    "pattern": r'\b(?:Medical Record|Patient ID)[:\s]*([A-Z0-9]{6,12})\b',
                    "confidence": 0.9
                }
            ],
            PHIType.IP_ADDRESS: [
                {
                    "pattern": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
                    "confidence": 0.8
                }
            ]
        }
        
        return patterns
    
    def _load_medical_keywords(self) -> List[str]:
        """Load medical context keywords."""
        return [
            "patient", "diagnosis", "treatment", "medication", "surgery",
            "hospital", "clinic", "doctor", "physician", "nurse",
            "medical record", "health record", "chart", "symptom",
            "condition", "disease", "therapy", "prescription"
        ]
    
    async def scan_data(self, data: Union[Dict[str, Any], str]) -> PHIDetectionResult:
        """
        Scan data for PHI/PII content.
        
        Args:
            data: Data to scan (dict or string)
            
        Returns:
            PHI detection results
        """
        try:
            logger.debug("Starting PHI detection scan")
            
            phi_entities = []
            phi_types = set()
            phi_fields = []
            field_types = {}
            confidence_scores = {}
            
            # Convert data to scannable format
            if isinstance(data, dict):
                scan_results = await self._scan_structured_data(data)
            else:
                scan_results = await self._scan_text_data(str(data))
            
            phi_entities.extend(scan_results["entities"])
            phi_types.update(scan_results["types"])
            phi_fields.extend(scan_results["fields"])
            field_types.update(scan_results["field_types"])
            confidence_scores.update(scan_results["confidence_scores"])
            
            result = PHIDetectionResult(
                has_phi=len(phi_entities) > 0,
                phi_entities=phi_entities,
                phi_types=list(phi_types),
                phi_fields=phi_fields,
                field_types=field_types,
                confidence_scores=confidence_scores,
                total_phi_count=len(phi_entities)
            )
            
            logger.debug(f"PHI scan complete: {result.total_phi_count} entities detected")
            return result
            
        except Exception as e:
            logger.error(f"Error in PHI detection: {str(e)}")
            return PHIDetectionResult(
                has_phi=False,
                phi_entities=[],
                phi_types=[],
                phi_fields=[],
                field_types={},
                confidence_scores={},
                total_phi_count=0
            )
    
    async def _scan_structured_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Scan structured data (JSON/dict) for PHI."""
        entities = []
        types = set()
        fields = []
        field_types = {}
        confidence_scores = {}
        
        for field_name, field_value in data.items():
            if isinstance(field_value, str):
                # Scan string values
                field_scan = await self._scan_text_data(field_value, field_name)
                
                if field_scan["entities"]:
                    entities.extend(field_scan["entities"])
                    types.update(field_scan["types"])
                    fields.append(field_name)
                    
                    # Determine primary PHI type for this field
                    if field_scan["entities"]:
                        primary_type = field_scan["entities"][0]["type"]
                        field_types[field_name] = PHIType(primary_type)
                        confidence_scores[field_name] = field_scan["entities"][0]["confidence"]
            
            elif isinstance(field_value, (dict, list)):
                # Recursively scan nested structures
                nested_scan = await self._scan_structured_data(
                    field_value if isinstance(field_value, dict) else {"items": field_value}
                )
                
                entities.extend(nested_scan["entities"])
                types.update(nested_scan["types"])
                fields.extend(nested_scan["fields"])
                field_types.update(nested_scan["field_types"])
                confidence_scores.update(nested_scan["confidence_scores"])
        
        return {
            "entities": entities,
            "types": types,
            "fields": fields,
            "field_types": field_types,
            "confidence_scores": confidence_scores
        }
    
    async def _scan_text_data(self, text: str, field_name: str = None) -> Dict[str, Any]:
        """Scan text data for PHI patterns."""
        entities = []
        types = set()
        
        # Check each PHI pattern
        for phi_type, patterns in self.phi_patterns.items():
            for pattern_info in patterns:
                pattern = pattern_info["pattern"]
                confidence = pattern_info["confidence"]
                context_required = pattern_info.get("context_required", False)
                
                matches = re.finditer(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    # If context is required, check for medical keywords nearby
                    if context_required:
                        context_window = text[max(0, match.start() - 50):match.end() + 50]
                        has_medical_context = any(
                            keyword in context_window.lower() 
                            for keyword in self.medical_keywords
                        )
                        
                        if not has_medical_context:
                            continue  # Skip if no medical context
                    
                    entity = {
                        "type": phi_type.value,
                        "text": match.group(),
                        "start": match.start(),
                        "end": match.end(),
                        "confidence": confidence,
                        "field_name": field_name,
                        "pattern": pattern
                    }
                    
                    entities.append(entity)
                    types.add(phi_type)
        
        return {
            "entities": entities,
            "types": types,
            "fields": [field_name] if field_name and entities else [],
            "field_types": {field_name: entities[0]["type"]} if field_name and entities else {},
            "confidence_scores": {field_name: entities[0]["confidence"]} if field_name and entities else {}
        }


class BuiltInAnonymization:
    """
    Built-in anonymization pipeline for AI models.
    
    Features:
    - Automatic PHI detection and anonymization
    - Reversible anonymization with secure mapping
    - Multiple anonymization methods
    - Healthcare compliance (HIPAA, SOC2)
    - Offline operation support
    """
    
    def __init__(self):
        self.phi_detector = PHIDetector()
        self.anonymization_maps: Dict[str, Dict] = {}
        
        # Anonymization settings
        self.default_method = AnonymizationMethod.REPLACEMENT
        self.enable_reversible = True
        self.map_retention_days = 90
        
    async def anonymize_for_model(
        self,
        data: Union[Dict[str, Any], str],
        model_id: str,
        context: str = "inference",
        user_id: str = "system"
    ) -> AnonymizedData:
        """
        Anonymize data for AI model processing.
        
        Args:
            data: Input data to anonymize
            model_id: Target model identifier
            context: Processing context
            user_id: User performing the operation
            
        Returns:
            Anonymized data with mapping information
        """
        try:
            start_time = datetime.utcnow()
            logger.info(f"Starting anonymization for model {model_id}")
            
            # Step 1: Detect PHI
            phi_result = await self.phi_detector.scan_data(data)
            
            if not phi_result.has_phi:
                # No PHI detected, return data unchanged
                return AnonymizedData(
                    anonymized_data=data,
                    anonymization_applied=False,
                    phi_detected=False,
                    phi_types=[],
                    anonymization_map_id=None,
                    original_data_hash=self._calculate_data_hash(data),
                    anonymization_method=AnonymizationMethod.REPLACEMENT,
                    reversible=False,
                    created_at=start_time
                )
            
            logger.info(f"Detected {phi_result.total_phi_count} PHI entities")
            
            # Step 2: Create anonymization mapping
            map_id = str(uuid.uuid4())
            anonymization_mapping = {}
            
            # Step 3: Apply anonymization
            if isinstance(data, dict):
                anonymized_data = await self._anonymize_structured_data(
                    data, phi_result, anonymization_mapping
                )
            else:
                anonymized_data = await self._anonymize_text_data(
                    str(data), phi_result, anonymization_mapping
                )
            
            # Step 4: Store mapping securely if reversible
            if self.enable_reversible and anonymization_mapping:
                await self._store_anonymization_mapping(
                    map_id, anonymization_mapping, data, model_id, context, user_id
                )
            
            # Step 5: Audit logging
            await audit_logger.log_event(
                event_type=AuditEventType.PHI_ANONYMIZED,
                user_id=user_id,
                resource_type="phi_anonymization",
                resource_id=map_id,
                action="data_anonymized",
                details={
                    "model_id": model_id,
                    "context": context,
                    "phi_types": [t.value for t in phi_result.phi_types],
                    "phi_count": phi_result.total_phi_count,
                    "anonymization_method": self.default_method.value,
                    "reversible": self.enable_reversible,
                    "processing_time_ms": (datetime.utcnow() - start_time).total_seconds() * 1000
                }
            )
            
            result = AnonymizedData(
                anonymized_data=anonymized_data,
                anonymization_applied=True,
                phi_detected=True,
                phi_types=phi_result.phi_types,
                anonymization_map_id=map_id if self.enable_reversible else None,
                original_data_hash=self._calculate_data_hash(data),
                anonymization_method=self.default_method,
                reversible=self.enable_reversible,
                created_at=start_time
            )
            
            logger.info(f"Anonymization completed: {map_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error in anonymization: {str(e)}")
            raise

    async def de_anonymize_data(
        self,
        anonymized_data: Union[Dict[str, Any], str],
        anonymization_map_id: str,
        user_id: str = "system"
    ) -> Union[Dict[str, Any], str]:
        """
        De-anonymize data using stored mapping.
        
        Args:
            anonymized_data: Anonymized data
            anonymization_map_id: Mapping identifier
            user_id: User requesting de-anonymization
            
        Returns:
            Original data
        """
        try:
            logger.info(f"Starting de-anonymization for map {anonymization_map_id}")
            
            # Retrieve mapping
            mapping_info = await self._retrieve_anonymization_mapping(anonymization_map_id)
            
            if not mapping_info:
                raise ValueError(f"Anonymization mapping {anonymization_map_id} not found")
            
            # Apply reverse mapping
            if isinstance(anonymized_data, dict):
                original_data = await self._de_anonymize_structured_data(
                    anonymized_data, mapping_info["mapping"]
                )
            else:
                original_data = await self._de_anonymize_text_data(
                    str(anonymized_data), mapping_info["mapping"]
                )
            
            # Update access tracking
            await self._update_mapping_access(anonymization_map_id, user_id)
            
            # Audit logging
            await audit_logger.log_event(
                event_type=AuditEventType.PHI_DEANONYMIZED,
                user_id=user_id,
                resource_type="phi_deanonymization",
                resource_id=anonymization_map_id,
                action="data_deanonymized",
                details={
                    "model_id": mapping_info.get("model_id"),
                    "context": mapping_info.get("context"),
                    "authorized": True
                }
            )
            
            logger.info(f"De-anonymization completed for map {anonymization_map_id}")
            return original_data
            
        except Exception as e:
            logger.error(f"Error in de-anonymization: {str(e)}")
            raise

    # Private helper methods
    
    async def _anonymize_structured_data(
        self,
        data: Dict[str, Any],
        phi_result: PHIDetectionResult,
        mapping: Dict[str, str]
    ) -> Dict[str, Any]:
        """Anonymize structured data."""
        anonymized = data.copy()
        
        for field_name in phi_result.phi_fields:
            if field_name in anonymized:
                phi_type = phi_result.field_types.get(field_name)
                original_value = str(anonymized[field_name])
                
                # Generate anonymous replacement
                anonymous_value = self._generate_anonymous_value(phi_type, original_value)
                
                # Store mapping
                mapping[anonymous_value] = original_value
                
                # Replace in data
                anonymized[field_name] = anonymous_value
        
        return anonymized
    
    async def _anonymize_text_data(
        self,
        text: str,
        phi_result: PHIDetectionResult,
        mapping: Dict[str, str]
    ) -> str:
        """Anonymize text data."""
        anonymized_text = text
        
        # Sort entities by position (reverse order to maintain positions)
        entities = sorted(phi_result.phi_entities, key=lambda x: x["start"], reverse=True)
        
        for entity in entities:
            phi_type = PHIType(entity["type"])
            original_value = entity["text"]
            
            # Generate anonymous replacement
            anonymous_value = self._generate_anonymous_value(phi_type, original_value)
            
            # Store mapping
            mapping[anonymous_value] = original_value
            
            # Replace in text
            start = entity["start"]
            end = entity["end"]
            anonymized_text = anonymized_text[:start] + anonymous_value + anonymized_text[end:]
        
        return anonymized_text
    
    def _generate_anonymous_value(self, phi_type: PHIType, original_value: str) -> str:
        """Generate anonymous replacement value."""
        if phi_type == PHIType.NAME:
            return f"Patient_{secrets.token_hex(3).upper()}"
        elif phi_type == PHIType.SSN:
            return f"XXX-XX-{secrets.randbelow(9999):04d}"
        elif phi_type == PHIType.PHONE:
            return f"555-{secrets.randbelow(900) + 100:03d}-{secrets.randbelow(9000) + 1000:04d}"
        elif phi_type == PHIType.EMAIL:
            return f"patient{secrets.token_hex(3)}@example.com"
        elif phi_type == PHIType.DATE:
            return f"[DATE_{secrets.token_hex(2).upper()}]"
        elif phi_type == PHIType.ADDRESS:
            return f"{secrets.randbelow(9999) + 1} Anonymous St, City ST 12345"
        elif phi_type == PHIType.MEDICAL_RECORD_NUMBER:
            return f"MRN_{secrets.token_hex(4).upper()}"
        elif phi_type == PHIType.IP_ADDRESS:
            return f"192.168.{secrets.randbelow(255)}.{secrets.randbelow(255)}"
        else:
            return f"[{phi_type.value.upper()}_{secrets.token_hex(3)}]"
    
    async def _store_anonymization_mapping(
        self,
        map_id: str,
        mapping: Dict[str, str],
        original_data: Union[Dict[str, Any], str],
        model_id: str,
        context: str,
        user_id: str
    ) -> None:
        """Store anonymization mapping securely."""
        try:
            # Encrypt mapping
            mapping_json = json.dumps(mapping)
            encrypted_mapping = await encryption_service.encrypt(
                mapping_json,
                context=f"anonymization_map_{map_id}"
            )
            
            # Calculate expiry
            expires_at = datetime.utcnow() + timedelta(days=self.map_retention_days)
            
            # Store in database
            async with get_db() as db:
                mapping_record = AnonymizationMap(
                    map_id=map_id,
                    original_data_hash=self._calculate_data_hash(original_data),
                    encrypted_mapping=encrypted_mapping,
                    model_id=model_id,
                    context_type=context,
                    phi_types_detected=[],  # Would be populated from phi_result
                    anonymization_method=self.default_method.value,
                    reversible=True,
                    expires_at=expires_at,
                    used_count=0,
                    user_id=user_id,
                    audit_trail={
                        "created_at": datetime.utcnow().isoformat(),
                        "created_by": user_id,
                        "mapping_size": len(mapping)
                    }
                )
                
                db.add(mapping_record)
                await db.commit()
                
            logger.info(f"Anonymization mapping stored: {map_id}")
            
        except Exception as e:
            logger.error(f"Error storing anonymization mapping: {str(e)}")
            raise
    
    async def _retrieve_anonymization_mapping(self, map_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve and decrypt anonymization mapping."""
        try:
            async with get_db() as db:
                from sqlalchemy import select
                
                query = select(AnonymizationMap).where(AnonymizationMap.map_id == map_id)
                result = await db.execute(query)
                mapping_record = result.scalar_one_or_none()
                
                if not mapping_record:
                    return None
                
                # Check expiry
                if mapping_record.expires_at and mapping_record.expires_at < datetime.utcnow():
                    logger.warning(f"Anonymization mapping {map_id} has expired")
                    return None
                
                # Decrypt mapping
                decrypted_mapping = await encryption_service.decrypt(
                    mapping_record.encrypted_mapping,
                    context=f"anonymization_map_{map_id}"
                )
                
                mapping_dict = json.loads(decrypted_mapping)
                
                return {
                    "mapping": mapping_dict,
                    "model_id": mapping_record.model_id,
                    "context": mapping_record.context_type,
                    "created_at": mapping_record.created_at
                }
                
        except Exception as e:
            logger.error(f"Error retrieving anonymization mapping: {str(e)}")
            return None
    
    async def _update_mapping_access(self, map_id: str, user_id: str) -> None:
        """Update mapping access tracking."""
        try:
            async with get_db() as db:
                from sqlalchemy import select, update
                
                query = select(AnonymizationMap).where(AnonymizationMap.map_id == map_id)
                result = await db.execute(query)
                mapping_record = result.scalar_one_or_none()
                
                if mapping_record:
                    mapping_record.used_count += 1
                    mapping_record.last_accessed = datetime.utcnow()
                    await db.commit()
                    
        except Exception as e:
            logger.error(f"Error updating mapping access: {str(e)}")
    
    def _calculate_data_hash(self, data: Union[Dict[str, Any], str]) -> str:
        """Calculate secure hash of data."""
        data_str = json.dumps(data, sort_keys=True) if isinstance(data, dict) else str(data)
        return hashlib.sha256(data_str.encode('utf-8')).hexdigest()
    
    async def _de_anonymize_structured_data(
        self,
        anonymized_data: Dict[str, Any],
        mapping: Dict[str, str]
    ) -> Dict[str, Any]:
        """De-anonymize structured data."""
        de_anonymized = anonymized_data.copy()
        
        for field_name, field_value in de_anonymized.items():
            if isinstance(field_value, str) and field_value in mapping:
                de_anonymized[field_name] = mapping[field_value]
        
        return de_anonymized
    
    async def _de_anonymize_text_data(
        self,
        anonymized_text: str,
        mapping: Dict[str, str]
    ) -> str:
        """De-anonymize text data."""
        de_anonymized_text = anonymized_text
        
        for anonymous_value, original_value in mapping.items():
            de_anonymized_text = de_anonymized_text.replace(anonymous_value, original_value)
        
        return de_anonymized_text