"""
Clinical BERT Service for Healthcare ML Platform

Integrates Bio_ClinicalBERT for medical text embeddings with healthcare-specific
preprocessing, anonymization validation, and production-ready error handling.
"""

import asyncio
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
import structlog
import re
from dataclasses import dataclass

# Handle optional ML dependencies
try:
    import numpy as np
    import torch
    from transformers import AutoTokenizer, AutoModel
    ML_DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    # Create mock objects for missing dependencies
    np = None
    torch = None
    AutoTokenizer = None
    AutoModel = None
    ML_DEPENDENCIES_AVAILABLE = False
    MISSING_ML_DEPS_ERROR = str(e)

from app.core.config import get_settings
from app.modules.data_anonymization.schemas import AnonymizedMLProfile
from app.core.security import EncryptionService

# Handle optional audit service import
try:
    from app.modules.audit_logger.service import SOC2AuditService, get_audit_service
    AUDIT_SERVICE_AVAILABLE = True
except ImportError:
    SOC2AuditService = None
    get_audit_service = None
    AUDIT_SERVICE_AVAILABLE = False

logger = structlog.get_logger(__name__)

@dataclass
class ClinicalTextEmbedding:
    """Clinical text embedding with metadata."""
    text_hash: str
    embedding_vector: List[float]
    embedding_dimension: int
    model_version: str
    processing_timestamp: datetime
    confidence_score: float
    clinical_categories: List[str]
    anonymization_validated: bool

@dataclass 
class ClinicalBERTConfig:
    """Configuration for Clinical BERT service."""
    model_name: str = "emilyalsentzer/Bio_ClinicalBERT"
    max_sequence_length: int = 512
    batch_size: int = 16
    device: str = "cpu"  # "cuda" if GPU available
    cache_embeddings: bool = True
    max_cache_size: int = 10000
    enable_preprocessing: bool = True
    validate_anonymization: bool = True

class ClinicalTextPreprocessor:
    """Preprocess clinical text for Bio_ClinicalBERT."""
    
    def __init__(self):
        self.logger = logger.bind(component="ClinicalTextPreprocessor")
        
        # Clinical abbreviations and their expansions
        self.clinical_abbreviations = {
            "htn": "hypertension",
            "dm": "diabetes mellitus", 
            "cad": "coronary artery disease",
            "chf": "congestive heart failure",
            "copd": "chronic obstructive pulmonary disease",
            "mi": "myocardial infarction",
            "afib": "atrial fibrillation",
            "dvt": "deep vein thrombosis",
            "pe": "pulmonary embolism",
            "gerd": "gastroesophageal reflux disease",
            "uti": "urinary tract infection",
            "pneumonia": "pneumonia",
            "asthma": "asthma",
            "rash": "skin rash",
            "fever": "elevated temperature"
        }
        
        # Medical terms that should be preserved
        self.preserve_medical_terms = {
            "symptoms", "diagnosis", "treatment", "medication", "procedure",
            "vital signs", "laboratory", "radiology", "pathology", "surgery"
        }
        
        # Patterns for potential PHI that should be removed
        self.phi_patterns = [
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b\d{10,}\b',  # Long numbers (could be IDs)
            r'\b[A-Z]{2}\d{8}\b',  # State ID patterns
            r'\b\w+@\w+\.\w+\b',  # Email addresses
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'  # Phone numbers
        ]
    
    async def preprocess_clinical_text(
        self, 
        text: str, 
        preserve_clinical_meaning: bool = True
    ) -> str:
        """
        Preprocess clinical text for Bio_ClinicalBERT.
        
        Args:
            text: Raw clinical text
            preserve_clinical_meaning: Whether to preserve clinical abbreviations
            
        Returns:
            Preprocessed clinical text safe for embedding
        """
        try:
            if not text or not text.strip():
                return ""
            
            processed_text = text.lower().strip()
            
            # Remove potential PHI
            processed_text = await self._remove_phi_patterns(processed_text)
            
            # Expand clinical abbreviations if requested
            if preserve_clinical_meaning:
                processed_text = self._expand_clinical_abbreviations(processed_text)
            
            # Normalize medical terminology
            processed_text = self._normalize_medical_terms(processed_text)
            
            # Clean and standardize formatting
            processed_text = self._clean_text_formatting(processed_text)
            
            # Validate anonymization
            if not await self._validate_text_anonymization(processed_text):
                self.logger.warning("Text failed anonymization validation")
                return ""
            
            return processed_text
            
        except Exception as e:
            self.logger.error("Clinical text preprocessing failed", error=str(e))
            return ""
    
    async def _remove_phi_patterns(self, text: str) -> str:
        """Remove patterns that could contain PHI."""
        for pattern in self.phi_patterns:
            text = re.sub(pattern, "[REDACTED]", text)
        return text
    
    def _expand_clinical_abbreviations(self, text: str) -> str:
        """Expand common clinical abbreviations."""
        for abbrev, expansion in self.clinical_abbreviations.items():
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(abbrev) + r'\b'
            text = re.sub(pattern, expansion, text, flags=re.IGNORECASE)
        return text
    
    def _normalize_medical_terms(self, text: str) -> str:
        """Normalize medical terminology for consistent embeddings."""
        # Standardize common medical phrases
        normalizations = {
            r'\bblood pressure\b': 'bp',
            r'\bheart rate\b': 'hr', 
            r'\btemperature\b': 'temp',
            r'\brespiratory rate\b': 'rr',
            r'\boxygen saturation\b': 'o2sat'
        }
        
        for pattern, replacement in normalizations.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text
    
    def _clean_text_formatting(self, text: str) -> str:
        """Clean and standardize text formatting."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but preserve medical notation
        text = re.sub(r'[^\w\s\-\./]', ' ', text)
        
        # Standardize spacing
        text = text.strip()
        
        return text
    
    async def _validate_text_anonymization(self, text: str) -> bool:
        """Validate that text doesn't contain obvious PHI."""
        # Check for common PHI patterns
        phi_indicators = [
            r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',  # Names
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # Dates
            r'\b\w+@\w+\.\w+\b',  # Emails
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'  # Phone numbers
        ]
        
        for pattern in phi_indicators:
            if re.search(pattern, text):
                return False
        
        return True

class ClinicalBERTService:
    """
    Production-ready Clinical BERT service for healthcare ML platform.
    
    Provides Bio_ClinicalBERT embeddings with healthcare-specific preprocessing,
    caching, batch processing, and comprehensive error handling.
    """
    
    def __init__(self, config: Optional[ClinicalBERTConfig] = None):
        """
        Initialize Clinical BERT service.
        
        Args:
            config: Clinical BERT configuration
        """
        self.config = config or ClinicalBERTConfig()
        self.settings = get_settings()
        self.logger = logger.bind(component="ClinicalBERTService")
        
        # Check if ML dependencies are available
        if not ML_DEPENDENCIES_AVAILABLE:
            self.logger.warning(
                "ML dependencies not available",
                error=MISSING_ML_DEPS_ERROR,
                status="limited_functionality"
            )
        
        # Initialize components
        self.preprocessor = ClinicalTextPreprocessor()
        
        # Initialize audit service if available
        if AUDIT_SERVICE_AVAILABLE and get_audit_service is not None:
            try:
                self.audit_service = get_audit_service()
            except RuntimeError:
                # Audit service not initialized yet - will be set later
                self.audit_service = None
                self.logger.info("Audit service not initialized yet - will be available after startup")
        else:
            self.audit_service = None
            self.logger.warning("Audit service not available - ML predictions will not be audited")
            
        self.encryption_service = EncryptionService()
        
        # Model components (loaded lazily)
        self.tokenizer: Optional[Any] = None
        self.model: Optional[Any] = None
        self.device = None
        
        # Initialize device only if torch is available
        if ML_DEPENDENCIES_AVAILABLE and torch is not None:
            self.device = torch.device(self.config.device)
        else:
            self.device = "cpu"  # Fallback device name
        
        # Embedding cache for performance
        self.embedding_cache: Dict[str, ClinicalTextEmbedding] = {}
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Model metadata
        self.model_loaded = False
        self.model_load_timestamp: Optional[datetime] = None
        
        self.logger.info(
            "Clinical BERT service initialized",
            model_name=self.config.model_name,
            device=str(self.device),
            cache_enabled=self.config.cache_embeddings,
            ml_dependencies_available=ML_DEPENDENCIES_AVAILABLE
        )
    
    async def initialize_model(self) -> bool:
        """
        Initialize Bio_ClinicalBERT model and tokenizer.
        
        Returns:
            True if initialization successful
        """
        try:
            if self.model_loaded:
                return True
            
            # Check if ML dependencies are available
            if not ML_DEPENDENCIES_AVAILABLE:
                self.logger.error(
                    "Cannot initialize model: ML dependencies not available",
                    error=MISSING_ML_DEPS_ERROR,
                    required_packages=["torch", "transformers", "numpy"]
                )
                return False
            
            self.logger.info("Loading Bio_ClinicalBERT model...")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.config.model_name,
                do_lower_case=True
            )
            
            # Load model
            self.model = AutoModel.from_pretrained(
                self.config.model_name,
                output_hidden_states=True
            )
            
            # Move to device
            self.model.to(self.device)
            self.model.eval()  # Set to evaluation mode
            
            self.model_loaded = True
            self.model_load_timestamp = datetime.utcnow()
            
            self.logger.info(
                "Bio_ClinicalBERT model loaded successfully",
                model_name=self.config.model_name,
                device=str(self.device),
                load_time=self.model_load_timestamp.isoformat()
            )
            
            return True
            
        except Exception as e:
            self.logger.error(
                "Failed to load Bio_ClinicalBERT model",
                model_name=self.config.model_name,
                error=str(e)
            )
            return False
    
    async def generate_clinical_embedding(
        self,
        clinical_text: str,
        profile: Optional[AnonymizedMLProfile] = None
    ) -> Optional[ClinicalTextEmbedding]:
        """
        Generate Clinical BERT embedding for medical text.
        
        Args:
            clinical_text: Clinical text to embed
            profile: Associated anonymized ML profile for validation
            
        Returns:
            Clinical text embedding with metadata
        """
        try:
            if not clinical_text or not clinical_text.strip():
                return None
            
            # Ensure model is loaded
            if not await self.initialize_model():
                raise RuntimeError("Failed to initialize Clinical BERT model")
            
            # Create text hash for caching
            text_hash = hashlib.sha256(clinical_text.encode()).hexdigest()[:16]
            
            # Check cache first
            if self.config.cache_embeddings and text_hash in self.embedding_cache:
                self.cache_hits += 1
                cached_embedding = self.embedding_cache[text_hash]
                
                self.logger.debug(
                    "Clinical embedding cache hit",
                    text_hash=text_hash,
                    cache_hits=self.cache_hits
                )
                
                return cached_embedding
            
            self.cache_misses += 1
            
            # Preprocess clinical text
            processed_text = await self.preprocessor.preprocess_clinical_text(
                clinical_text, preserve_clinical_meaning=True
            )
            
            if not processed_text:
                self.logger.warning("Clinical text preprocessing failed or returned empty")
                return None
            
            # Validate anonymization if profile provided
            anonymization_validated = True
            if profile and self.config.validate_anonymization:
                anonymization_validated = await self._validate_profile_anonymization(
                    profile, processed_text
                )
            
            # Generate embedding
            embedding_vector = await self._generate_bert_embedding(processed_text)
            
            if embedding_vector is None:
                return None
            
            # Extract clinical categories
            clinical_categories = await self._extract_clinical_categories(processed_text)
            
            # Calculate confidence score
            confidence_score = await self._calculate_embedding_confidence(
                processed_text, embedding_vector
            )
            
            # Create embedding object
            clinical_embedding = ClinicalTextEmbedding(
                text_hash=text_hash,
                embedding_vector=embedding_vector,
                embedding_dimension=len(embedding_vector),
                model_version=self.config.model_name,
                processing_timestamp=datetime.utcnow(),
                confidence_score=confidence_score,
                clinical_categories=clinical_categories,
                anonymization_validated=anonymization_validated
            )
            
            # Cache the embedding
            if self.config.cache_embeddings:
                self._cache_embedding(text_hash, clinical_embedding)
            
            # Audit embedding generation
            if self.audit_service is not None:
                await self._audit_embedding_generation(
                    clinical_embedding, processed_text, profile
                )
            
            self.logger.info(
                "Clinical embedding generated successfully",
                text_hash=text_hash,
                embedding_dimension=clinical_embedding.embedding_dimension,
                confidence_score=confidence_score,
                clinical_categories_count=len(clinical_categories),
                anonymization_validated=anonymization_validated
            )
            
            return clinical_embedding
            
        except Exception as e:
            self.logger.error(
                "Failed to generate clinical embedding",
                error=str(e),
                text_length=len(clinical_text) if clinical_text else 0
            )
            return None
    
    async def batch_generate_embeddings(
        self,
        clinical_texts: List[str],
        profiles: Optional[List[AnonymizedMLProfile]] = None
    ) -> List[Optional[ClinicalTextEmbedding]]:
        """
        Generate Clinical BERT embeddings for multiple texts efficiently.
        
        Args:
            clinical_texts: List of clinical texts to embed
            profiles: Optional list of associated ML profiles
            
        Returns:
            List of clinical text embeddings
        """
        if profiles and len(profiles) != len(clinical_texts):
            raise ValueError("Profiles list must match clinical texts list length")
        
        embeddings = []
        start_time = datetime.utcnow()
        
        self.logger.info(
            "Starting batch clinical embedding generation",
            text_count=len(clinical_texts),
            batch_size=self.config.batch_size
        )
        
        # Process in batches for memory efficiency
        for i in range(0, len(clinical_texts), self.config.batch_size):
            batch_texts = clinical_texts[i:i + self.config.batch_size]
            batch_profiles = None
            if profiles:
                batch_profiles = profiles[i:i + self.config.batch_size]
            
            # Process batch
            batch_embeddings = await self._process_embedding_batch(
                batch_texts, batch_profiles
            )
            embeddings.extend(batch_embeddings)
            
            # Log progress
            if (i + self.config.batch_size) % 100 == 0:
                self.logger.info(
                    "Batch embedding progress",
                    completed=min(i + self.config.batch_size, len(clinical_texts)),
                    total=len(clinical_texts)
                )
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        successful_embeddings = sum(1 for emb in embeddings if emb is not None)
        
        self.logger.info(
            "Batch clinical embedding generation completed",
            total_texts=len(clinical_texts),
            successful_embeddings=successful_embeddings,
            failed_embeddings=len(clinical_texts) - successful_embeddings,
            processing_time_seconds=processing_time,
            cache_hit_rate=self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0.0
        )
        
        return embeddings
    
    async def update_ml_profile_with_embedding(
        self,
        profile: AnonymizedMLProfile,
        clinical_text: str
    ) -> AnonymizedMLProfile:
        """
        Update ML profile with Clinical BERT embedding.
        
        Args:
            profile: Anonymized ML profile to update
            clinical_text: Clinical text to embed
            
        Returns:
            Updated ML profile with embedding
        """
        try:
            # Generate clinical embedding
            clinical_embedding = await self.generate_clinical_embedding(
                clinical_text, profile
            )
            
            if clinical_embedding and clinical_embedding.anonymization_validated:
                # Update profile with embedding
                profile.clinical_text_embedding = clinical_embedding.embedding_vector
                
                # Add embedding metadata to categorical features
                profile.categorical_features.update({
                    "clinical_embedding_dimension": clinical_embedding.embedding_dimension,
                    "clinical_embedding_confidence": clinical_embedding.confidence_score,
                    "clinical_categories": ",".join(clinical_embedding.clinical_categories),
                    "embedding_model_version": clinical_embedding.model_version,
                    "embedding_timestamp": clinical_embedding.processing_timestamp.isoformat()
                })
                
                # Mark as prediction ready if embedding is good quality
                if clinical_embedding.confidence_score >= 0.7:
                    profile.prediction_ready = True
                
                self.logger.info(
                    "ML profile updated with clinical embedding",
                    profile_id=profile.profile_id,
                    embedding_dimension=clinical_embedding.embedding_dimension,
                    confidence_score=clinical_embedding.confidence_score
                )
            else:
                self.logger.warning(
                    "Failed to update ML profile with embedding",
                    profile_id=profile.profile_id,
                    embedding_generated=clinical_embedding is not None,
                    anonymization_validated=clinical_embedding.anonymization_validated if clinical_embedding else False
                )
            
            return profile
            
        except Exception as e:
            self.logger.error(
                "Failed to update ML profile with embedding",
                profile_id=profile.profile_id,
                error=str(e)
            )
            return profile
    
    async def get_embedding_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score (0.0 to 1.0)
        """
        try:
            if not ML_DEPENDENCIES_AVAILABLE or np is None:
                self.logger.error(
                    "Cannot calculate similarity: ML dependencies not available",
                    error=MISSING_ML_DEPS_ERROR
                )
                return 0.0
            
            if len(embedding1) != len(embedding2):
                raise ValueError("Embeddings must have same dimension")
            
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0.0 or norm2 == 0.0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            
            # Normalize to 0-1 range
            similarity = (similarity + 1.0) / 2.0
            
            return float(np.clip(similarity, 0.0, 1.0))
            
        except Exception as e:
            self.logger.error("Failed to calculate embedding similarity", error=str(e))
            return 0.0
    
    async def get_service_health(self) -> Dict[str, Any]:
        """
        Get Clinical BERT service health status.
        
        Returns:
            Service health information
        """
        try:
            health_status = {
                "service": "clinical_bert",
                "status": "healthy" if self.model_loaded else "unhealthy",
                "model_loaded": self.model_loaded,
                "model_name": self.config.model_name,
                "device": str(self.device),
                "cache_enabled": self.config.cache_embeddings,
                "cache_size": len(self.embedding_cache),
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "cache_hit_rate": self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0.0,
                "model_load_timestamp": self.model_load_timestamp.isoformat() if self.model_load_timestamp else None,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Test embedding generation if model is loaded
            if self.model_loaded:
                test_text = "Patient presents with chest pain and shortness of breath."
                test_embedding = await self.generate_clinical_embedding(test_text)
                health_status["test_embedding_successful"] = test_embedding is not None
                if test_embedding:
                    health_status["test_embedding_dimension"] = test_embedding.embedding_dimension
                    health_status["test_confidence_score"] = test_embedding.confidence_score
            
            return health_status
            
        except Exception as e:
            self.logger.error("Failed to get service health", error=str(e))
            return {
                "service": "clinical_bert",
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    # PRIVATE HELPER METHODS
    
    async def _generate_bert_embedding(self, text: str) -> Optional[List[float]]:
        """Generate BERT embedding for preprocessed text."""
        try:
            # Tokenize text
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                max_length=self.config.max_sequence_length,
                truncation=True,
                padding=True
            )
            
            # Move to device
            inputs = {key: value.to(self.device) for key, value in inputs.items()}
            
            # Generate embedding
            with torch.no_grad():
                outputs = self.model(**inputs)
                
                # Use [CLS] token embedding (first token)
                cls_embedding = outputs.last_hidden_state[:, 0, :].squeeze()
                
                # Convert to list
                embedding_vector = cls_embedding.cpu().numpy().tolist()
            
            return embedding_vector
            
        except Exception as e:
            self.logger.error("Failed to generate BERT embedding", error=str(e))
            return None
    
    async def _process_embedding_batch(
        self,
        texts: List[str],
        profiles: Optional[List[AnonymizedMLProfile]] = None
    ) -> List[Optional[ClinicalTextEmbedding]]:
        """Process a batch of texts for embedding generation."""
        embeddings = []
        
        for i, text in enumerate(texts):
            profile = profiles[i] if profiles else None
            embedding = await self.generate_clinical_embedding(text, profile)
            embeddings.append(embedding)
        
        return embeddings
    
    async def _validate_profile_anonymization(
        self,
        profile: AnonymizedMLProfile,
        text: str
    ) -> bool:
        """Validate that profile and text maintain anonymization."""
        try:
            # Check if profile is marked as compliance validated
            if not profile.compliance_validated:
                return False
            
            # Check for obvious PHI in text
            phi_patterns = [
                r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',  # Names
                r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
                r'\b\w+@\w+\.\w+\b'  # Email
            ]
            
            for pattern in phi_patterns:
                if re.search(pattern, text):
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error("Failed to validate profile anonymization", error=str(e))
            return False
    
    async def _extract_clinical_categories(self, text: str) -> List[str]:
        """Extract clinical categories from processed text."""
        categories = []
        
        # Define clinical category keywords
        category_keywords = {
            "symptoms": ["pain", "ache", "fever", "nausea", "fatigue", "cough"],
            "vital_signs": ["blood pressure", "heart rate", "temperature", "respiratory"],
            "medications": ["medication", "drug", "prescription", "therapy"],
            "procedures": ["surgery", "procedure", "operation", "treatment"],
            "diagnosis": ["diagnosis", "condition", "disease", "disorder"],
            "anatomy": ["heart", "lung", "liver", "kidney", "brain", "stomach"]
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in text.lower() for keyword in keywords):
                categories.append(category)
        
        return categories
    
    async def _calculate_embedding_confidence(
        self,
        text: str,
        embedding: List[float]
    ) -> float:
        """Calculate confidence score for embedding quality."""
        try:
            confidence = 1.0
            
            # Check text length (longer text generally better)
            if len(text) < 20:
                confidence *= 0.7
            elif len(text) < 50:
                confidence *= 0.9
            
            # Check embedding magnitude (should not be too small) - only if numpy available
            if ML_DEPENDENCIES_AVAILABLE and np is not None:
                embedding_magnitude = np.linalg.norm(embedding)
                if embedding_magnitude < 1.0:
                    confidence *= 0.8
            else:
                # Fallback calculation without numpy
                magnitude_squared = sum(x * x for x in embedding)
                embedding_magnitude = magnitude_squared ** 0.5
                if embedding_magnitude < 1.0:
                    confidence *= 0.8
            
            # Check for medical content
            medical_terms = ["patient", "medical", "clinical", "diagnosis", "treatment"]
            if not any(term in text.lower() for term in medical_terms):
                confidence *= 0.6
            
            return min(confidence, 1.0)
            
        except Exception as e:
            self.logger.error("Failed to calculate embedding confidence", error=str(e))
            return 0.5
    
    def _cache_embedding(self, text_hash: str, embedding: ClinicalTextEmbedding):
        """Cache embedding for performance optimization."""
        if len(self.embedding_cache) >= self.config.max_cache_size:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self.embedding_cache))
            del self.embedding_cache[oldest_key]
        
        self.embedding_cache[text_hash] = embedding
    
    async def _audit_embedding_generation(
        self,
        embedding: ClinicalTextEmbedding,
        processed_text: str,
        profile: Optional[AnonymizedMLProfile]
    ):
        """Audit embedding generation for compliance."""
        try:
            audit_data = {
                "operation": "clinical_embedding_generation",
                "embedding_hash": embedding.text_hash,
                "embedding_dimension": embedding.embedding_dimension,
                "model_version": embedding.model_version,
                "confidence_score": embedding.confidence_score,
                "clinical_categories": embedding.clinical_categories,
                "anonymization_validated": embedding.anonymization_validated,
                "profile_id": profile.profile_id if profile else None,
                "text_length": len(processed_text),
                "processing_timestamp": embedding.processing_timestamp.isoformat()
            }
            
            self.logger.info("Clinical embedding generation audited", **audit_data)
            
        except Exception as e:
            self.logger.error("Failed to audit embedding generation", error=str(e))