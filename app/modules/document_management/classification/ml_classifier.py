"""
ML-Based Document Classifier

Simple machine learning classifier for documents using lightweight approaches.
Falls back gracefully when heavy ML libraries are not available.
"""

import asyncio
import re
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Tuple
from collections import Counter
import math

import structlog

from app.core.database_unified import DocumentType
from .classifier import ClassificationEngineInterface, ClassificationResult

logger = structlog.get_logger(__name__)


@dataclass
class MLClassificationResult:
    """Extended result with ML-specific information."""
    
    base_result: ClassificationResult
    feature_scores: Dict[str, float]
    model_version: str
    training_samples: int


class SimpleNaiveBayesClassifier:
    """Simple Naive Bayes classifier implementation without external dependencies."""
    
    def __init__(self):
        self.logger = logger.bind(classifier="SimpleNaiveBayesClassifier")
        self.word_counts = {}
        self.class_counts = {}
        self.vocabulary = set()
        self.trained = False
        
        # Use pre-trained knowledge for medical documents
        self._initialize_medical_knowledge()
    
    def _initialize_medical_knowledge(self):
        """Initialize with medical domain knowledge."""
        
        # Pre-defined medical vocabularies for each document type
        medical_vocabulary = {
            DocumentType.LAB_RESULT: [
                "laboratory", "lab", "test", "result", "blood", "urine", "specimen", 
                "reference", "range", "normal", "abnormal", "hemoglobin", "glucose",
                "cholesterol", "creatinine", "white", "cell", "count", "platelet",
                "chemistry", "hematology", "microbiology", "CBC", "BMP", "CMP"
            ],
            
            DocumentType.IMAGING: [
                "imaging", "radiology", "xray", "ct", "mri", "ultrasound", "scan",
                "contrast", "without", "findings", "impression", "radiologist",
                "examination", "study", "axial", "sagittal", "coronal", "mammogram",
                "angiogram", "nuclear", "medicine", "pet", "bone", "scan"
            ],
            
            DocumentType.CLINICAL_NOTE: [
                "clinical", "note", "visit", "patient", "history", "physical",
                "examination", "assessment", "plan", "diagnosis", "treatment",
                "medication", "symptom", "complaint", "vital", "signs", "SOAP",
                "subjective", "objective", "progress", "consultation", "admission"
            ],
            
            DocumentType.PRESCRIPTION: [
                "prescription", "medication", "drug", "dose", "dosage", "tablet",
                "capsule", "take", "daily", "twice", "refill", "quantity", "DEA",
                "pharmacy", "generic", "brand", "substitute", "controlled", "substance"
            ],
            
            DocumentType.INSURANCE: [
                "insurance", "coverage", "benefit", "claim", "authorization", "policy",
                "member", "subscriber", "copay", "deductible", "coinsurance", "EOB",
                "medicare", "medicaid", "commercial", "prior", "approval", "denial"
            ],
            
            DocumentType.PATHOLOGY: [
                "pathology", "biopsy", "tissue", "specimen", "microscopic", "macroscopic",
                "histology", "cytology", "malignant", "benign", "carcinoma", "adenoma",
                "grade", "stage", "margin", "lymph", "node", "immunohistochemistry"
            ]
        }
        
        # Initialize word counts with medical knowledge
        self.word_counts = {}
        self.class_counts = {}
        
        for doc_type, words in medical_vocabulary.items():
            self.class_counts[doc_type] = len(words) * 10  # Give some weight
            self.word_counts[doc_type] = {}
            
            for word in words:
                # Higher counts for more specific medical terms
                count = 10 if len(word) > 6 else 5
                self.word_counts[doc_type][word.lower()] = count
                self.vocabulary.add(word.lower())
        
        # Add OTHER type with general terms
        self.class_counts[DocumentType.OTHER] = 50
        self.word_counts[DocumentType.OTHER] = {
            word: 1 for word in ["document", "file", "text", "content", "information"]
        }
        
        self.trained = True
        
        self.logger.info(
            "Medical knowledge initialized",
            vocabulary_size=len(self.vocabulary),
            document_types=len(self.class_counts)
        )
    
    def _extract_features(self, text: str) -> Dict[str, int]:
        """Extract features from text (simple word counts)."""
        # Simple tokenization
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Count words
        word_counts = Counter(words)
        
        # Filter by vocabulary
        features = {}
        for word, count in word_counts.items():
            if word in self.vocabulary:
                features[word] = count
        
        return features
    
    def predict(self, text: str) -> Tuple[DocumentType, float, Dict[str, float]]:
        """Predict document type using Naive Bayes."""
        if not self.trained:
            return DocumentType.OTHER, 0.0, {}
        
        features = self._extract_features(text)
        
        if not features:
            return DocumentType.OTHER, 0.5, {}
        
        # Calculate probabilities for each class
        class_scores = {}
        feature_scores = {}
        
        total_docs = sum(self.class_counts.values())
        
        for doc_type in self.class_counts:
            # Prior probability
            prior = self.class_counts[doc_type] / total_docs
            
            # Likelihood
            likelihood = 1.0
            type_word_counts = self.word_counts.get(doc_type, {})
            total_words_in_class = sum(type_word_counts.values()) + len(self.vocabulary)  # Laplace smoothing
            
            for word, count in features.items():
                word_count_in_class = type_word_counts.get(word, 0) + 1  # Laplace smoothing
                word_prob = word_count_in_class / total_words_in_class
                likelihood *= (word_prob ** count)
            
            # Posterior probability (log space for numerical stability)
            log_posterior = math.log(prior) + math.log(likelihood)
            class_scores[doc_type] = log_posterior
            
            # Store feature contributions
            feature_scores[doc_type.value] = {
                word: type_word_counts.get(word, 0) for word in features
            }
        
        # Find best class
        best_type = max(class_scores.items(), key=lambda x: x[1])
        predicted_type, log_score = best_type
        
        # Convert to confidence (normalize scores)
        scores = list(class_scores.values())
        max_score = max(scores)
        normalized_scores = [math.exp(score - max_score) for score in scores]
        total_prob = sum(normalized_scores)
        
        best_idx = list(class_scores.keys()).index(predicted_type)
        confidence = normalized_scores[best_idx] / total_prob
        
        return predicted_type, confidence, feature_scores.get(predicted_type.value, {})


class MLClassifier(ClassificationEngineInterface):
    """ML-based document classifier with fallback capabilities."""
    
    def __init__(self, model_path: Optional[str] = None):
        self.logger = logger.bind(classifier="MLClassifier")
        self.model_path = model_path
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize ML model with fallback to simple implementation."""
        try:
            # Try to load advanced ML model if available
            self._try_load_advanced_model()
        except Exception as e:
            self.logger.info("Advanced ML not available, using simple model", error=str(e))
            
        # Always have simple model as fallback
        self.simple_model = SimpleNaiveBayesClassifier()
        
        self.logger.info(
            "ML classifier initialized",
            has_advanced_model=self.model is not None,
            has_simple_model=True
        )
    
    def _try_load_advanced_model(self):
        """Try to load advanced ML models like scikit-learn."""
        try:
            # Try to import scikit-learn
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.naive_bayes import MultinomialNB
            from sklearn.pipeline import Pipeline
            
            # Create a simple pipeline
            self.model = Pipeline([
                ('tfidf', TfidfVectorizer(max_features=1000, stop_words='english')),
                ('classifier', MultinomialNB())
            ])
            
            # In a real implementation, you would load a pre-trained model
            # For now, we'll rely on the simple model
            self.model = None
            
        except ImportError:
            self.model = None
    
    async def classify_document(
        self, 
        text: str, 
        filename: str, 
        mime_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ClassificationResult:
        """Classify document using ML approach."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            if self.model is not None:
                # Use advanced model if available
                result = await self._classify_with_advanced_model(
                    text, filename, mime_type, metadata, start_time
                )
            else:
                # Use simple model
                result = await self._classify_with_simple_model(
                    text, filename, mime_type, metadata, start_time
                )
            
            return result
            
        except Exception as e:
            processing_time = int((asyncio.get_event_loop().time() - start_time) * 1000)
            self.logger.error("ML classification failed", error=str(e))
            
            return ClassificationResult(
                document_type=DocumentType.OTHER,
                confidence=0.0,
                category="error",
                subcategory=None,
                tags=[],
                metadata={"error": str(e), "model_type": "ml_fallback"},
                classification_method="ml_based",
                processing_time_ms=processing_time,
                success=False,
                error=str(e)
            )
    
    async def _classify_with_simple_model(
        self,
        text: str,
        filename: str,
        mime_type: str,
        metadata: Optional[Dict[str, Any]],
        start_time: float
    ) -> ClassificationResult:
        """Classify using simple Naive Bayes model."""
        
        predicted_type, confidence, feature_scores = self.simple_model.predict(text)
        
        # Determine category based on prediction
        category = self._determine_category(predicted_type, text)
        
        # Extract tags based on features
        tags = self._extract_ml_tags(feature_scores, text)
        
        processing_time = int((asyncio.get_event_loop().time() - start_time) * 1000)
        
        self.logger.info(
            "Simple ML classification completed",
            predicted_type=predicted_type.value,
            confidence=confidence,
            processing_time=processing_time
        )
        
        return ClassificationResult(
            document_type=predicted_type,
            confidence=confidence,
            category=category,
            subcategory=None,
            tags=tags,
            metadata={
                "model_type": "simple_naive_bayes",
                "feature_scores": feature_scores,
                "features_used": len(feature_scores),
                "text_length": len(text)
            },
            classification_method="ml_based",
            processing_time_ms=processing_time,
            success=True
        )
    
    async def _classify_with_advanced_model(
        self,
        text: str,
        filename: str,
        mime_type: str,
        metadata: Optional[Dict[str, Any]],
        start_time: float
    ) -> ClassificationResult:
        """Classify using advanced ML model (when available)."""
        # This would be implemented when advanced models are available
        # For now, fall back to simple model
        return await self._classify_with_simple_model(
            text, filename, mime_type, metadata, start_time
        )
    
    def _determine_category(self, doc_type: DocumentType, text: str) -> str:
        """Determine category based on document type and content."""
        category_mapping = {
            DocumentType.LAB_RESULT: "laboratory",
            DocumentType.IMAGING: "radiology",
            DocumentType.CLINICAL_NOTE: "clinical",
            DocumentType.PRESCRIPTION: "pharmacy",
            DocumentType.INSURANCE: "administrative",
            DocumentType.PATHOLOGY: "pathology",
            DocumentType.OTHER: "general"
        }
        
        return category_mapping.get(doc_type, "general")
    
    def _extract_ml_tags(self, feature_scores: Dict[str, int], text: str) -> List[str]:
        """Extract tags based on ML feature scores."""
        tags = []
        
        # Get top features
        sorted_features = sorted(feature_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Take top 5 features as tags
        for feature, score in sorted_features[:5]:
            if score > 0:
                tags.append(feature)
        
        # Add ML-specific tags
        tags.append("ml_classified")
        
        return tags
    
    def get_confidence_threshold(self) -> float:
        """Get minimum confidence threshold for ML classification."""
        return 0.5


# Factory function
def get_ml_classifier(model_path: Optional[str] = None) -> MLClassifier:
    """Factory function to create ML classifier."""
    return MLClassifier(model_path)