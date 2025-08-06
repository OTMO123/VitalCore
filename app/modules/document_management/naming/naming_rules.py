"""
Filename Generation Rules Engine

Rule-based intelligent filename generation for medical documents.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re
import structlog
from datetime import datetime
from app.core.database_unified import DocumentType

logger = structlog.get_logger(__name__)

@dataclass
class NamingRule:
    """Single naming rule with conditions and naming pattern."""
    
    name: str
    document_type: DocumentType
    template: str
    category: str
    priority: int = 0
    conditions: Dict[str, Any] = None
    required_fields: List[str] = None
    format_options: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.conditions is None:
            self.conditions = {}
        if self.required_fields is None:
            self.required_fields = []
        if self.format_options is None:
            self.format_options = {}

class NamingRulesEngine:
    """Rule-based filename generation engine for medical documents."""
    
    def __init__(self):
        self.rules: List[NamingRule] = []
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Initialize default naming rules for medical documents."""
        
        # Laboratory Reports
        self.rules.append(NamingRule(
            name="laboratory_report",
            document_type=DocumentType.LAB_RESULT,
            template="LAB_{date}_{test_type}_{patient_id}",
            category="laboratory",
            priority=10,
            required_fields=["date", "patient_id"],
            format_options={
                "date_format": "%Y%m%d",
                "test_type_extraction": ["cbc", "bmp", "lipid", "liver", "kidney", "glucose"],
                "max_length": 50
            }
        ))
        
        # Radiology Reports
        self.rules.append(NamingRule(
            name="radiology_report",
            document_type=DocumentType.IMAGING,
            template="RAD_{date}_{modality}_{body_part}_{patient_id}",
            category="radiology",
            priority=10,
            required_fields=["date", "patient_id"],
            format_options={
                "date_format": "%Y%m%d",
                "modality_extraction": ["xray", "ct", "mri", "ultrasound", "mammogram"],
                "body_part_extraction": ["chest", "abdomen", "head", "spine", "extremity"],
                "max_length": 60
            }
        ))
        
        # Clinical Notes
        self.rules.append(NamingRule(
            name="clinical_note",
            document_type=DocumentType.CLINICAL_NOTE,
            template="NOTE_{date}_{visit_type}_{provider}_{patient_id}",
            category="clinical",
            priority=8,
            required_fields=["date", "patient_id"],
            format_options={
                "date_format": "%Y%m%d",
                "visit_type_extraction": ["office", "consult", "followup", "initial"],
                "provider_extraction": True,
                "max_length": 55
            }
        ))
        
        # Discharge Summary
        self.rules.append(NamingRule(
            name="discharge_summary",
            document_type=DocumentType.DISCHARGE_SUMMARY,
            template="DISC_{admit_date}_{discharge_date}_{patient_id}",
            category="hospital",
            priority=9,
            required_fields=["patient_id"],
            format_options={
                "date_format": "%Y%m%d",
                "date_extraction": ["admission", "discharge"],
                "max_length": 45
            }
        ))
        
        # Prescription
        self.rules.append(NamingRule(
            name="prescription",
            document_type=DocumentType.PRESCRIPTION,
            template="RX_{date}_{medication}_{patient_id}",
            category="medication",
            priority=9,
            required_fields=["date", "patient_id"],
            format_options={
                "date_format": "%Y%m%d",
                "medication_extraction": True,
                "max_length": 50
            }
        ))
        
        # Insurance Documents
        self.rules.append(NamingRule(
            name="insurance_document",
            document_type=DocumentType.INSURANCE,
            template="INS_{date}_{doc_type}_{patient_id}",
            category="administrative",
            priority=7,
            required_fields=["patient_id"],
            format_options={
                "date_format": "%Y%m%d",
                "doc_type_extraction": ["claim", "eob", "auth", "benefits"],
                "max_length": 45
            }
        ))
        
        # Generic Medical Record
        self.rules.append(NamingRule(
            name="medical_record",
            document_type=DocumentType.MEDICAL_RECORD,
            template="MED_{date}_{category}_{patient_id}",
            category="medical",
            priority=5,
            required_fields=["patient_id"],
            format_options={
                "date_format": "%Y%m%d",
                "category_extraction": True,
                "max_length": 45
            }
        ))
        
        # Default fallback
        self.rules.append(NamingRule(
            name="default_document",
            document_type=DocumentType.OTHER,
            template="DOC_{date}_{type}_{patient_id}",
            category="general",
            priority=1,
            required_fields=[],
            format_options={
                "date_format": "%Y%m%d",
                "max_length": 40
            }
        ))
        
        # Sort rules by priority (higher priority first)
        self.rules.sort(key=lambda r: r.priority, reverse=True)
    
    def generate_filename(
        self,
        document_type: DocumentType,
        text: str,
        original_filename: str,
        extracted_data: Dict[str, Any] = None
    ) -> Tuple[str, float, str, Dict[str, Any]]:
        """
        Generate a smart filename based on document type and content.
        
        Returns:
            Tuple of (filename, confidence, method, metadata)
        """
        
        if extracted_data is None:
            extracted_data = {}
        
        # Find matching rule
        matching_rule = None
        for rule in self.rules:
            if rule.document_type == document_type:
                matching_rule = rule
                break
        
        if not matching_rule:
            # Use default rule
            matching_rule = self.rules[-1]  # Last rule is default
        
        # Extract information from text and filename
        extracted_info = self._extract_information(
            text, 
            original_filename, 
            matching_rule,
            extracted_data
        )
        
        # Generate filename using template
        generated_filename = self._apply_template(
            matching_rule.template,
            extracted_info,
            matching_rule.format_options
        )
        
        # Calculate confidence based on how much information we extracted
        confidence = self._calculate_confidence(
            matching_rule,
            extracted_info,
            generated_filename != original_filename
        )
        
        # Ensure filename is safe and within limits
        safe_filename = self._sanitize_filename(
            generated_filename,
            matching_rule.format_options.get("max_length", 50)
        )
        
        logger.info(
            "Filename generated using naming rules",
            rule_name=matching_rule.name,
            original=original_filename,
            generated=safe_filename,
            confidence=confidence
        )
        
        return (
            safe_filename,
            confidence,
            f"rules_engine_{matching_rule.name}",
            {
                "rule_used": matching_rule.name,
                "extracted_fields": list(extracted_info.keys()),
                "template": matching_rule.template,
                "original_filename": original_filename
            }
        )
    
    def _extract_information(
        self,
        text: str,
        filename: str,
        rule: NamingRule,
        provided_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Extract relevant information from text and filename."""
        
        extracted = {}
        text_lower = text.lower()
        
        # Start with provided data
        extracted.update(provided_data)
        
        # Extract date information
        if "date" in rule.template:
            date_str = self._extract_date(text, filename)
            if date_str:
                extracted["date"] = date_str
            else:
                # Use current date as fallback
                extracted["date"] = datetime.now().strftime(
                    rule.format_options.get("date_format", "%Y%m%d")
                )
        
        # Extract patient ID
        if "patient_id" in rule.template:
            patient_id = self._extract_patient_id(text, filename, provided_data)
            if patient_id:
                extracted["patient_id"] = patient_id
            else:
                extracted["patient_id"] = "UNKNOWN"
        
        # Document type specific extractions
        if rule.document_type == DocumentType.LAB_RESULT:
            test_type = self._extract_test_type(text, rule.format_options.get("test_type_extraction", []))
            if test_type:
                extracted["test_type"] = test_type
                
        elif rule.document_type == DocumentType.IMAGING:
            modality = self._extract_modality(text, rule.format_options.get("modality_extraction", []))
            body_part = self._extract_body_part(text, rule.format_options.get("body_part_extraction", []))
            if modality:
                extracted["modality"] = modality
            if body_part:
                extracted["body_part"] = body_part
                
        elif rule.document_type == DocumentType.CLINICAL_NOTE:
            visit_type = self._extract_visit_type(text, rule.format_options.get("visit_type_extraction", []))
            provider = self._extract_provider(text) if rule.format_options.get("provider_extraction") else None
            if visit_type:
                extracted["visit_type"] = visit_type
            if provider:
                extracted["provider"] = provider
                
        elif rule.document_type == DocumentType.PRESCRIPTION:
            medication = self._extract_medication(text) if rule.format_options.get("medication_extraction") else None
            if medication:
                extracted["medication"] = medication
        
        return extracted
    
    def _extract_date(self, text: str, filename: str) -> Optional[str]:
        """Extract date from text or filename."""
        
        # Common date patterns
        date_patterns = [
            r'\b(\d{4}-\d{2}-\d{2})\b',  # YYYY-MM-DD
            r'\b(\d{2}/\d{2}/\d{4})\b',  # MM/DD/YYYY
            r'\b(\d{1,2}/\d{1,2}/\d{4})\b',  # M/D/YYYY
            r'\b(\d{4}\d{2}\d{2})\b',    # YYYYMMDD
        ]
        
        # Try filename first
        for pattern in date_patterns:
            match = re.search(pattern, filename)
            if match:
                date_str = match.group(1).replace('/', '').replace('-', '')
                if len(date_str) == 8:
                    return date_str
        
        # Try text content
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                date_str = match.group(1).replace('/', '').replace('-', '')
                if len(date_str) == 8:
                    return date_str
        
        return None
    
    def _extract_patient_id(self, text: str, filename: str, provided_data: Dict[str, Any]) -> Optional[str]:
        """Extract patient ID from various sources."""
        
        # Check provided data first
        if "patient_id" in provided_data:
            return str(provided_data["patient_id"])
        
        # Look for common patient ID patterns
        id_patterns = [
            r'\bMRN[:\s]*([A-Z0-9]{6,12})\b',
            r'\bPatient\s+ID[:\s]*([A-Z0-9]{6,12})\b',
            r'\bID[:\s]*([A-Z0-9]{6,12})\b',
        ]
        
        for pattern in id_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_test_type(self, text: str, test_types: List[str]) -> Optional[str]:
        """Extract test type from text."""
        text_lower = text.lower()
        
        for test_type in test_types:
            if test_type.lower() in text_lower:
                return test_type.upper()
        
        # Look for common test abbreviations
        if "complete blood count" in text_lower or "cbc" in text_lower:
            return "CBC"
        elif "basic metabolic" in text_lower or "bmp" in text_lower:
            return "BMP"
        elif "lipid" in text_lower:
            return "LIPID"
        elif "glucose" in text_lower:
            return "GLUCOSE"
        
        return None
    
    def _extract_modality(self, text: str, modalities: List[str]) -> Optional[str]:
        """Extract imaging modality from text."""
        text_lower = text.lower()
        
        for modality in modalities:
            if modality.lower() in text_lower:
                return modality.upper()
        
        # Check for variations
        if "x-ray" in text_lower or "xray" in text_lower:
            return "XRAY"
        elif "ct scan" in text_lower or " ct " in text_lower:
            return "CT"
        elif "mri" in text_lower or "magnetic resonance" in text_lower:
            return "MRI"
        
        return None
    
    def _extract_body_part(self, text: str, body_parts: List[str]) -> Optional[str]:
        """Extract body part from text."""
        text_lower = text.lower()
        
        for part in body_parts:
            if part.lower() in text_lower:
                return part.upper()
        
        return None
    
    def _extract_visit_type(self, text: str, visit_types: List[str]) -> Optional[str]:
        """Extract visit type from text."""
        text_lower = text.lower()
        
        for visit_type in visit_types:
            if visit_type.lower() in text_lower:
                return visit_type.upper()
        
        if "follow up" in text_lower or "followup" in text_lower:
            return "FOLLOWUP"
        elif "consultation" in text_lower:
            return "CONSULT"
        elif "office visit" in text_lower:
            return "OFFICE"
        
        return None
    
    def _extract_provider(self, text: str) -> Optional[str]:
        """Extract provider name from text."""
        
        # Look for doctor name patterns
        provider_patterns = [
            r'\bDr\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b',
            r'\b([A-Z][a-z]+),?\s+M\.?D\.?\b',
        ]
        
        for pattern in provider_patterns:
            match = re.search(pattern, text)
            if match:
                name = match.group(1).replace(',', '').replace('.', '').replace(' ', '')
                return name[:10]  # Limit length
        
        return None
    
    def _extract_medication(self, text: str) -> Optional[str]:
        """Extract medication name from text."""
        
        # Common medication patterns
        med_patterns = [
            r'\b([A-Z][a-z]+(?:ine|ol|pril|ide|mycin|cillin))\b',  # Common drug endings
            r'\b([A-Z][a-z]{4,12})\s+\d+\s*mg\b',  # Drug name followed by dosage
        ]
        
        for pattern in med_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)[:10]  # Limit length
        
        return None
    
    def _apply_template(
        self,
        template: str,
        data: Dict[str, str],
        format_options: Dict[str, Any]
    ) -> str:
        """Apply template with extracted data."""
        
        result = template
        
        # Replace placeholders
        for key, value in data.items():
            placeholder = f"{{{key}}}"
            if placeholder in result:
                result = result.replace(placeholder, str(value))
        
        # Remove unfilled placeholders
        result = re.sub(r'\{[^}]+\}', 'UNKNOWN', result)
        
        return result
    
    def _calculate_confidence(
        self,
        rule: NamingRule,
        extracted_info: Dict[str, str],
        improved_from_original: bool
    ) -> float:
        """Calculate confidence score for generated filename."""
        
        confidence = 0.5  # Base confidence
        
        # Bonus for having required fields
        for field in rule.required_fields:
            if field in extracted_info and extracted_info[field] != "UNKNOWN":
                confidence += 0.2
        
        # Bonus for additional extracted information
        non_required_fields = len(extracted_info) - len(rule.required_fields)
        confidence += min(non_required_fields * 0.1, 0.2)
        
        # Bonus if we improved from original
        if improved_from_original:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _sanitize_filename(self, filename: str, max_length: int) -> str:
        """Sanitize filename for filesystem compatibility."""
        
        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Limit length
        if len(filename) > max_length:
            # Try to preserve extension
            if '.' in filename:
                name, ext = filename.rsplit('.', 1)
                name = name[:max_length - len(ext) - 1]
                filename = f"{name}.{ext}"
            else:
                filename = filename[:max_length]
        
        return filename
    
    def add_rule(self, rule: NamingRule):
        """Add a custom naming rule."""
        self.rules.append(rule)
        # Re-sort by priority
        self.rules.sort(key=lambda r: r.priority, reverse=True)
        
        logger.info(
            "Custom naming rule added",
            rule_name=rule.name,
            document_type=rule.document_type.value,
            priority=rule.priority
        )