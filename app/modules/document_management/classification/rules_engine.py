"""
Document Classification Rules Engine

Rule-based document classification using patterns, keywords, and file characteristics.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re
import structlog
from app.core.database_unified import DocumentType

logger = structlog.get_logger(__name__)

@dataclass
class ClassificationRule:
    """Single classification rule with conditions and target classification."""
    
    name: str
    document_type: DocumentType
    confidence: float
    category: str
    subcategory: Optional[str] = None
    conditions: Dict[str, Any] = None
    keywords: List[str] = None
    file_patterns: List[str] = None
    mime_types: List[str] = None
    priority: int = 0
    
    def __post_init__(self):
        if self.conditions is None:
            self.conditions = {}
        if self.keywords is None:
            self.keywords = []
        if self.file_patterns is None:
            self.file_patterns = []
        if self.mime_types is None:
            self.mime_types = []

class RulesEngine:
    """Rule-based document classification engine."""
    
    def __init__(self):
        self.rules: List[ClassificationRule] = []
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Initialize default classification rules for medical documents."""
        
        # Laboratory Reports
        self.rules.append(ClassificationRule(
            name="laboratory_report",
            document_type=DocumentType.LAB_RESULT,
            confidence=0.9,
            category="laboratory",
            subcategory="blood_work",
            keywords=[
                "lab results", "blood test", "complete blood count", "cbc", 
                "hemoglobin", "hematocrit", "white blood cells", "platelets",
                "glucose", "cholesterol", "triglycerides", "liver function",
                "kidney function", "urinalysis", "chemistry panel"
            ],
            file_patterns=[r".*lab.*\.pdf$", r".*blood.*\.pdf$", r".*test.*\.pdf$"],
            mime_types=["application/pdf", "text/plain"],
            priority=10
        ))
        
        # Radiology Reports
        self.rules.append(ClassificationRule(
            name="radiology_report",
            document_type=DocumentType.IMAGING,
            confidence=0.85,
            category="radiology",
            subcategory="diagnostic_imaging",
            keywords=[
                "x-ray", "ct scan", "mri", "ultrasound", "mammogram", 
                "bone scan", "pet scan", "radiology", "imaging", 
                "contrast", "radiologist", "impression", "findings"
            ],
            file_patterns=[r".*x-?ray.*\.pdf$", r".*ct.*\.pdf$", r".*mri.*\.pdf$"],
            mime_types=["application/pdf", "image/jpeg", "image/png"],
            priority=10
        ))
        
        # Prescription/Medication
        self.rules.append(ClassificationRule(
            name="prescription",
            document_type=DocumentType.PRESCRIPTION,
            confidence=0.9,
            category="medication",
            subcategory="prescription",
            keywords=[
                "prescription", "medication", "drug", "pharmacy", "rx", 
                "dosage", "refill", "pill", "tablet", "capsule", "mg", "ml",
                "twice daily", "once daily", "as needed", "prn"
            ],
            file_patterns=[r".*rx.*\.pdf$", r".*prescription.*\.pdf$", r".*med.*\.pdf$"],
            mime_types=["application/pdf", "text/plain"],
            priority=9
        ))
        
        # Clinical Notes
        self.rules.append(ClassificationRule(
            name="clinical_note",
            document_type=DocumentType.CLINICAL_NOTE,
            confidence=0.8,
            category="clinical",
            subcategory="progress_note",
            keywords=[
                "progress note", "clinical note", "office visit", "consultation",
                "assessment", "plan", "subjective", "objective", "soap",
                "chief complaint", "history of present illness", "physical exam"
            ],
            file_patterns=[r".*note.*\.pdf$", r".*visit.*\.pdf$", r".*consult.*\.pdf$"],
            mime_types=["application/pdf", "text/plain"],
            priority=8
        ))
        
        # Discharge Summary
        self.rules.append(ClassificationRule(
            name="discharge_summary",
            document_type=DocumentType.DISCHARGE_SUMMARY,
            confidence=0.9,
            category="hospital",
            subcategory="discharge",
            keywords=[
                "discharge summary", "hospital discharge", "admission date",
                "discharge date", "discharge diagnosis", "discharge medications",
                "follow-up", "discharge instructions", "hospitalization"
            ],
            file_patterns=[r".*discharge.*\.pdf$", r".*summary.*\.pdf$"],
            mime_types=["application/pdf", "text/plain"],
            priority=9
        ))
        
        # Insurance/Administrative
        self.rules.append(ClassificationRule(
            name="insurance_document",
            document_type=DocumentType.INSURANCE,
            confidence=0.8,
            category="administrative",
            subcategory="insurance",
            keywords=[
                "insurance", "claim", "benefits", "coverage", "copay",
                "deductible", "prior authorization", "eob", "explanation of benefits",
                "member id", "group number", "policy"
            ],
            file_patterns=[r".*insurance.*\.pdf$", r".*claim.*\.pdf$", r".*eob.*\.pdf$"],
            mime_types=["application/pdf", "text/plain"],
            priority=7
        ))
        
        # Generic Medical Document
        self.rules.append(ClassificationRule(
            name="medical_document",
            document_type=DocumentType.MEDICAL_RECORD,
            confidence=0.6,
            category="medical",
            subcategory="general",
            keywords=[
                "patient", "medical", "health", "doctor", "physician",
                "clinic", "hospital", "treatment", "diagnosis", "icd-10"
            ],
            file_patterns=[r".*medical.*\.pdf$", r".*health.*\.pdf$"],
            mime_types=["application/pdf", "text/plain"],
            priority=5
        ))
        
        # Default fallback
        self.rules.append(ClassificationRule(
            name="other_document",
            document_type=DocumentType.OTHER,
            confidence=0.3,
            category="general",
            subcategory="unclassified",
            keywords=[],
            file_patterns=[r".*\.pdf$", r".*\.txt$", r".*\.doc.*$"],
            mime_types=["application/pdf", "text/plain", "application/msword"],
            priority=1
        ))
        
        # Sort rules by priority (higher priority first)
        self.rules.sort(key=lambda r: r.priority, reverse=True)
    
    def classify_document(
        self, 
        text: str, 
        filename: str, 
        mime_type: str
    ) -> Tuple[DocumentType, float, str, Optional[str], List[str]]:
        """
        Classify a document using rule-based approach.
        
        Returns:
            Tuple of (document_type, confidence, category, subcategory, matched_keywords)
        """
        
        if not text:
            text = ""
        
        # Normalize inputs
        text_lower = text.lower()
        filename_lower = filename.lower()
        
        best_rule = None
        best_score = 0.0
        matched_keywords = []
        
        for rule in self.rules:
            score = 0.0
            rule_keywords = []
            
            # Check mime type match
            if rule.mime_types and mime_type in rule.mime_types:
                score += 0.2
            
            # Check filename patterns
            for pattern in rule.file_patterns:
                if re.match(pattern, filename_lower):
                    score += 0.3
                    break
            
            # Check keyword matches
            if rule.keywords:
                keyword_matches = 0
                for keyword in rule.keywords:
                    if keyword.lower() in text_lower:
                        keyword_matches += 1
                        rule_keywords.append(keyword)
                
                # Calculate keyword score (percentage of keywords found)
                if keyword_matches > 0:
                    keyword_score = min(keyword_matches / len(rule.keywords), 1.0) * 0.5
                    score += keyword_score
            
            # Apply rule's base confidence as a multiplier
            final_score = score * rule.confidence
            
            # Check if this is the best match so far
            if final_score > best_score:
                best_rule = rule
                best_score = final_score
                matched_keywords = rule_keywords
        
        if best_rule:
            logger.info(
                "Document classified using rules",
                rule_name=best_rule.name,
                document_type=best_rule.document_type.value,
                confidence=best_score,
                matched_keywords=matched_keywords[:5]  # Limit logged keywords
            )
            
            return (
                best_rule.document_type,
                min(best_score, 1.0),  # Cap confidence at 1.0
                best_rule.category,
                best_rule.subcategory,
                matched_keywords
            )
        
        # Fallback
        logger.warning("No classification rule matched, using default")
        return (
            DocumentType.OTHER,
            0.1,
            "general",
            "unclassified",
            []
        )
    
    def add_rule(self, rule: ClassificationRule):
        """Add a custom classification rule."""
        self.rules.append(rule)
        # Re-sort by priority
        self.rules.sort(key=lambda r: r.priority, reverse=True)
        
        logger.info(
            "Custom classification rule added",
            rule_name=rule.name,
            document_type=rule.document_type.value,
            priority=rule.priority
        )
    
    def get_rules_for_type(self, document_type: DocumentType) -> List[ClassificationRule]:
        """Get all rules that can classify documents as the specified type."""
        return [rule for rule in self.rules if rule.document_type == document_type]
    
    def get_rule_statistics(self) -> Dict[str, Any]:
        """Get statistics about loaded rules."""
        type_counts = {}
        for rule in self.rules:
            type_name = rule.document_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        return {
            "total_rules": len(self.rules),
            "rules_by_type": type_counts,
            "average_keywords_per_rule": sum(len(r.keywords) for r in self.rules) / len(self.rules) if self.rules else 0
        }