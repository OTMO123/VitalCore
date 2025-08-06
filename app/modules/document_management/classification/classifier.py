"""
Main Document Classification Service

Orchestrates different classification approaches: rule-based, ML-based, and hybrid.
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import re
import hashlib

import structlog

from app.core.database_unified import DocumentType

logger = structlog.get_logger(__name__)


@dataclass
class ClassificationResult:
    """Result of document classification."""
    
    document_type: DocumentType
    confidence: float
    category: str
    subcategory: Optional[str]
    tags: List[str]
    metadata: Dict[str, Any]
    classification_method: str
    processing_time_ms: int
    success: bool
    error: Optional[str] = None


class ClassificationEngineInterface(ABC):
    """Interface for classification engines."""
    
    @abstractmethod
    async def classify_document(
        self, 
        text: str, 
        filename: str, 
        mime_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ClassificationResult:
        """Classify document and return result."""
        pass
    
    @abstractmethod
    def get_confidence_threshold(self) -> float:
        """Get minimum confidence threshold for this engine."""
        pass


class RuleBasedClassifier(ClassificationEngineInterface):
    """Rule-based document classifier using pattern matching."""
    
    def __init__(self):
        self.logger = logger.bind(classifier="RuleBasedClassifier")
        self._load_classification_rules()
    
    def _load_classification_rules(self):
        """Load classification rules for medical documents."""
        
        # Medical document patterns
        self.document_patterns = {
            DocumentType.LAB_RESULT: {
                "patterns": [
                    r"(?i)\b(lab|laboratory)\s+(result|report|test)\b",
                    r"(?i)\b(blood|urine|stool)\s+(test|analysis)\b",
                    r"(?i)\b(hemoglobin|glucose|cholesterol|creatinine)\b",
                    r"(?i)\b(CBC|BMP|CMP|lipid\s+panel)\b",
                    r"(?i)\b(reference\s+range|normal\s+range)\b",
                    r"(?i)\b(specimen|sample)\s+(collected|drawn)\b"
                ],
                "categories": ["blood_work", "urinalysis", "microbiology", "chemistry"],
                "confidence_boost": 0.9
            },
            
            DocumentType.IMAGING: {
                "patterns": [
                    r"(?i)\b(x-ray|xray|radiograph|CT|MRI|ultrasound|echocardiogram)\b",
                    r"(?i)\b(imaging|radiology|radiologic)\s+(study|report|examination)\b",
                    r"(?i)\b(scan|mammogram|angiogram|arthrogram)\b",
                    r"(?i)\b(contrast|without\s+contrast|with\s+and\s+without)\b",
                    r"(?i)\b(findings|impression|conclusion)\b.*\b(normal|abnormal|unremarkable)\b",
                    r"(?i)\b(axial|sagittal|coronal)\s+(images|views)\b"
                ],
                "categories": ["ct_scan", "mri", "x_ray", "ultrasound", "mammography"],
                "confidence_boost": 0.85
            },
            
            DocumentType.CLINICAL_NOTE: {
                "patterns": [
                    r"(?i)\b(chief\s+complaint|history\s+of\s+present\s+illness|HPI)\b",
                    r"(?i)\b(physical\s+examination|PE|assessment|plan)\b",
                    r"(?i)\b(subjective|objective|assessment|plan|SOAP)\b",
                    r"(?i)\b(vital\s+signs|blood\s+pressure|heart\s+rate|temperature)\b",
                    r"(?i)\b(diagnosis|differential\s+diagnosis|impression)\b",
                    r"(?i)\b(medications|prescriptions|allergies)\b"
                ],
                "categories": ["progress_note", "consultation", "admission_note", "discharge_summary"],
                "confidence_boost": 0.8
            },
            
            DocumentType.PRESCRIPTION: {
                "patterns": [
                    r"(?i)\b(prescription|Rx|medication|drug)\b",
                    r"(?i)\b(take|tablet|capsule|mg|ml|dose|dosage)\b",
                    r"(?i)\b(daily|twice\s+daily|three\s+times|as\s+needed|PRN)\b",
                    r"(?i)\b(refill|quantity|days\s+supply)\b",
                    r"(?i)\b(generic|brand|substitute)\b",
                    r"(?i)\bDEA\s+#\b"
                ],
                "categories": ["new_prescription", "refill", "controlled_substance"],
                "confidence_boost": 0.95
            },
            
            DocumentType.INSURANCE: {
                "patterns": [
                    r"(?i)\b(insurance|coverage|benefit|claim|authorization)\b",
                    r"(?i)\b(copay|deductible|coinsurance|out-of-pocket)\b",
                    r"(?i)\b(policy|member|subscriber|group\s+number)\b",
                    r"(?i)\b(EOB|explanation\s+of\s+benefits)\b",
                    r"(?i)\b(prior\s+authorization|pre-auth|approval)\b",
                    r"(?i)\b(medicare|medicaid|commercial\s+insurance)\b"
                ],
                "categories": ["prior_auth", "benefits_verification", "claim_form", "eob"],
                "confidence_boost": 0.85
            },
            
            DocumentType.PATHOLOGY: {
                "patterns": [
                    r"(?i)\b(pathology|histology|cytology|biopsy)\s+(report|result)\b",
                    r"(?i)\b(microscopic|macroscopic)\s+(description|examination)\b",
                    r"(?i)\b(specimen|tissue|cell|slide)\b",
                    r"(?i)\b(malignant|benign|carcinoma|adenoma|dysplasia)\b",
                    r"(?i)\b(grade|stage|margin|lymph\s+node)\b",
                    r"(?i)\b(immunohistochemistry|IHC|special\s+stain)\b"
                ],
                "categories": ["surgical_pathology", "cytopathology", "autopsy", "frozen_section"],
                "confidence_boost": 0.9
            }
        }
        
        # Category-specific patterns
        self.category_patterns = {
            "urgent": [
                r"(?i)\b(urgent|stat|emergency|critical|abnormal)\b",
                r"(?i)\b(immediate|asap|priority)\b"
            ],
            "follow_up": [
                r"(?i)\b(follow.?up|return|next\s+visit|recheck)\b",
                r"(?i)\b(in\s+\d+\s+(days?|weeks?|months?))\b"
            ],
            "consultation": [
                r"(?i)\b(consult|referral|second\s+opinion)\b",
                r"(?i)\b(specialist|cardiologist|neurologist|oncologist)\b"
            ]
        }
    
    async def classify_document(
        self, 
        text: str, 
        filename: str, 
        mime_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ClassificationResult:
        """Classify document using rule-based patterns."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Clean and normalize text for pattern matching
            normalized_text = self._normalize_text(text)
            
            # Score each document type
            type_scores = {}
            matched_patterns = {}
            
            for doc_type, rules in self.document_patterns.items():
                score, patterns = self._calculate_type_score(normalized_text, rules)
                type_scores[doc_type] = score
                matched_patterns[doc_type] = patterns
            
            # Find best match
            if not type_scores or max(type_scores.values()) == 0:
                return self._create_unknown_result(filename, mime_type, start_time)
            
            best_type = max(type_scores.items(), key=lambda x: x[1])
            document_type, confidence = best_type
            
            # Determine category and subcategory
            category = self._determine_category(document_type, normalized_text, filename)
            subcategory = self._determine_subcategory(document_type, category, normalized_text)
            
            # Extract tags
            tags = self._extract_tags(normalized_text, document_type)
            
            # Add filename-based confidence boost
            confidence = self._apply_filename_boost(confidence, filename, document_type)
            
            processing_time = int((asyncio.get_event_loop().time() - start_time) * 1000)
            
            self.logger.info(
                "Rule-based classification completed",
                document_type=document_type.value,
                confidence=confidence,
                category=category,
                processing_time=processing_time
            )
            
            return ClassificationResult(
                document_type=document_type,
                confidence=confidence,
                category=category,
                subcategory=subcategory,
                tags=tags,
                metadata={
                    "matched_patterns": matched_patterns[document_type],
                    "all_scores": {dt.value: score for dt, score in type_scores.items()},
                    "filename_boost_applied": True,
                    "text_length": len(text)
                },
                classification_method="rule_based",
                processing_time_ms=processing_time,
                success=True
            )
            
        except Exception as e:
            processing_time = int((asyncio.get_event_loop().time() - start_time) * 1000)
            self.logger.error("Rule-based classification failed", error=str(e))
            
            return ClassificationResult(
                document_type=DocumentType.OTHER,
                confidence=0.0,
                category="error",
                subcategory=None,
                tags=[],
                metadata={"error": str(e)},
                classification_method="rule_based",
                processing_time_ms=processing_time,
                success=False,
                error=str(e)
            )
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for better pattern matching."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters that might interfere with matching
        text = re.sub(r'[^\w\s\-\.]', ' ', text)
        
        return text.strip()
    
    def _calculate_type_score(self, text: str, rules: Dict[str, Any]) -> Tuple[float, List[str]]:
        """Calculate confidence score for a document type."""
        patterns = rules["patterns"]
        confidence_boost = rules["confidence_boost"]
        
        matched_patterns = []
        total_matches = 0
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                matched_patterns.append(pattern)
                total_matches += len(matches)
        
        if not matched_patterns:
            return 0.0, []
        
        # Base score from pattern matches
        pattern_score = min(len(matched_patterns) / len(patterns), 1.0)
        
        # Frequency bonus (more matches = higher confidence)
        frequency_bonus = min(total_matches / 10.0, 0.2)
        
        # Apply confidence boost
        final_score = (pattern_score + frequency_bonus) * confidence_boost
        
        return min(final_score, 1.0), matched_patterns
    
    def _determine_category(self, doc_type: DocumentType, text: str, filename: str) -> str:
        """Determine document category."""
        type_rules = self.document_patterns.get(doc_type, {})
        categories = type_rules.get("categories", ["general"])
        
        # Check filename for category hints
        filename_lower = filename.lower()
        for category in categories:
            if category.replace("_", "").replace(" ", "") in filename_lower.replace("_", "").replace(" ", ""):
                return category
        
        # Check text for category patterns
        for category in categories:
            category_clean = category.replace('_', r'\s*')
            category_pattern = rf"(?i)\b{category_clean}\b"
            if re.search(category_pattern, text):
                return category
        
        # Default to first category
        return categories[0] if categories else "general"
    
    def _determine_subcategory(self, doc_type: DocumentType, category: str, text: str) -> Optional[str]:
        """Determine document subcategory."""
        # Check for urgent/priority indicators
        for pattern in self.category_patterns.get("urgent", []):
            if re.search(pattern, text):
                return "urgent"
        
        # Check for follow-up indicators
        for pattern in self.category_patterns.get("follow_up", []):
            if re.search(pattern, text):
                return "follow_up"
        
        # Check for consultation indicators
        for pattern in self.category_patterns.get("consultation", []):
            if re.search(pattern, text):
                return "consultation"
        
        return None
    
    def _extract_tags(self, text: str, doc_type: DocumentType) -> List[str]:
        """Extract relevant tags from document text."""
        tags = []
        
        # Common medical tags
        medical_terms = [
            "diabetes", "hypertension", "cancer", "cardiac", "respiratory",
            "neurological", "orthopedic", "dermatology", "gastroenterology",
            "endocrinology", "oncology", "cardiology", "neurology"
        ]
        
        for term in medical_terms:
            if re.search(rf"(?i)\b{term}", text):
                tags.append(term)
        
        # Document-specific tags
        if doc_type == DocumentType.LAB_RESULT:
            lab_tags = ["blood_work", "urinalysis", "chemistry", "hematology"]
            for tag in lab_tags:
                tag_clean = tag.replace('_', r'\s*')
                if re.search(rf"(?i)\b{tag_clean}", text):
                    tags.append(tag)
        
        elif doc_type == DocumentType.IMAGING:
            imaging_tags = ["ct", "mri", "xray", "ultrasound", "nuclear_medicine"]
            for tag in imaging_tags:
                tag_clean = tag.replace('_', r'\s*')
                if re.search(rf"(?i)\b{tag_clean}", text):
                    tags.append(tag)
        
        # Limit to most relevant tags
        return tags[:10]
    
    def _apply_filename_boost(self, confidence: float, filename: str, doc_type: DocumentType) -> float:
        """Apply confidence boost based on filename patterns."""
        filename_lower = filename.lower()
        
        filename_indicators = {
            DocumentType.LAB_RESULT: ["lab", "blood", "urine", "test", "result"],
            DocumentType.IMAGING: ["xray", "ct", "mri", "scan", "imaging", "radiology"],
            DocumentType.CLINICAL_NOTE: ["note", "visit", "progress", "clinical"],
            DocumentType.PRESCRIPTION: ["rx", "prescription", "medication", "drug"],
            DocumentType.INSURANCE: ["insurance", "auth", "claim", "coverage"],
            DocumentType.PATHOLOGY: ["path", "biopsy", "tissue", "histology"]
        }
        
        indicators = filename_indicators.get(doc_type, [])
        for indicator in indicators:
            if indicator in filename_lower:
                return min(confidence + 0.1, 1.0)
        
        return confidence
    
    def _create_unknown_result(self, filename: str, mime_type: str, start_time: float) -> ClassificationResult:
        """Create result for unknown/unclassifiable documents."""
        processing_time = int((asyncio.get_event_loop().time() - start_time) * 1000)
        
        return ClassificationResult(
            document_type=DocumentType.OTHER,
            confidence=0.5,  # Neutral confidence for unknown
            category="unknown",
            subcategory=None,
            tags=["unclassified"],
            metadata={
                "filename": filename,
                "mime_type": mime_type,
                "reason": "no_patterns_matched"
            },
            classification_method="rule_based",
            processing_time_ms=processing_time,
            success=True
        )
    
    def get_confidence_threshold(self) -> float:
        """Get minimum confidence threshold for rule-based classification."""
        return 0.6


class DocumentClassifier:
    """
    Main document classification service.
    
    Orchestrates different classification engines and provides unified interface.
    """
    
    def __init__(self, engines: Optional[List[ClassificationEngineInterface]] = None):
        self.engines = engines or [RuleBasedClassifier()]
        self.logger = logger.bind(service="DocumentClassifier")
    
    async def classify_document(
        self,
        text: str,
        filename: str,
        mime_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        prefer_engine: Optional[str] = None
    ) -> ClassificationResult:
        """
        Classify document using available engines.
        
        Uses ensemble approach - tries multiple engines and combines results.
        """
        try:
            self.logger.info(
                "Starting document classification",
                filename=filename,
                mime_type=mime_type,
                text_length=len(text),
                engines_count=len(self.engines)
            )
            
            # Run classification with all engines
            results = []
            for engine in self.engines:
                try:
                    result = await engine.classify_document(text, filename, mime_type, metadata)
                    if result.success:
                        results.append(result)
                except Exception as e:
                    self.logger.warning("Engine classification failed", engine=type(engine).__name__, error=str(e))
            
            if not results:
                return self._create_fallback_result(filename, mime_type)
            
            # If only one result, return it
            if len(results) == 1:
                return results[0]
            
            # Ensemble decision making
            return self._combine_results(results, filename, mime_type)
            
        except Exception as e:
            self.logger.error("Document classification failed", error=str(e))
            return self._create_error_result(filename, mime_type, str(e))
    
    def _combine_results(
        self, 
        results: List[ClassificationResult], 
        filename: str, 
        mime_type: str
    ) -> ClassificationResult:
        """Combine results from multiple engines using ensemble approach."""
        
        # Weight results by confidence and engine reliability
        weighted_results = []
        
        for result in results:
            # Give higher weight to rule-based for medical documents
            weight = 1.0
            if result.classification_method == "rule_based":
                weight = 1.2
            elif result.classification_method == "ml_based":
                weight = 1.1
            
            weighted_score = result.confidence * weight
            weighted_results.append((weighted_score, result))
        
        # Sort by weighted score
        weighted_results.sort(key=lambda x: x[0], reverse=True)
        best_result = weighted_results[0][1]
        
        # Check for consensus
        type_votes = {}
        for _, result in weighted_results:
            doc_type = result.document_type
            if doc_type not in type_votes:
                type_votes[doc_type] = []
            type_votes[doc_type].append(result.confidence)
        
        # If multiple engines agree, boost confidence
        if len(type_votes.get(best_result.document_type, [])) > 1:
            consensus_boost = 0.1
            best_result.confidence = min(best_result.confidence + consensus_boost, 1.0)
        
        # Add ensemble metadata
        best_result.metadata["ensemble_classification"] = True
        best_result.metadata["engines_used"] = len(results)
        best_result.metadata["consensus"] = len(type_votes.get(best_result.document_type, []))
        
        return best_result
    
    def _create_fallback_result(self, filename: str, mime_type: str) -> ClassificationResult:
        """Create fallback result when all engines fail."""
        return ClassificationResult(
            document_type=DocumentType.OTHER,
            confidence=0.3,
            category="unclassified",
            subcategory=None,
            tags=["fallback"],
            metadata={
                "filename": filename,
                "mime_type": mime_type,
                "fallback_reason": "all_engines_failed"
            },
            classification_method="fallback",
            processing_time_ms=0,
            success=True
        )
    
    def _create_error_result(self, filename: str, mime_type: str, error: str) -> ClassificationResult:
        """Create error result when classification fails completely."""
        return ClassificationResult(
            document_type=DocumentType.OTHER,
            confidence=0.0,
            category="error",
            subcategory=None,
            tags=["error"],
            metadata={
                "filename": filename,
                "mime_type": mime_type,
                "error": error
            },
            classification_method="error",
            processing_time_ms=0,
            success=False,
            error=error
        )
    
    async def batch_classify(
        self,
        documents: List[Tuple[str, str, str]],  # (text, filename, mime_type)
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> List[ClassificationResult]:
        """Classify multiple documents in batch."""
        if metadata is None:
            metadata = [None] * len(documents)
        
        tasks = []
        for i, (text, filename, mime_type) in enumerate(documents):
            task = self.classify_document(text, filename, mime_type, metadata[i])
            tasks.append(task)
        
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_supported_document_types(self) -> List[DocumentType]:
        """Get list of supported document types."""
        return list(DocumentType)
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for classification service."""
        try:
            # Test with sample document
            test_text = "This is a test medical document for classification health check."
            result = await self.classify_document(
                test_text,
                "health_check.txt",
                "text/plain"
            )
            
            return {
                "status": "healthy" if result.success else "degraded",
                "engines_count": len(self.engines),
                "test_result": result.success,
                "supported_types": len(self.get_supported_document_types())
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "engines_count": len(self.engines)
            }


# Factory function
def get_document_classifier(
    engines: Optional[List[ClassificationEngineInterface]] = None
) -> DocumentClassifier:
    """Factory function to create document classifier."""
    return DocumentClassifier(engines)