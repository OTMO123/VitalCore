"""
Vector Feature Preparator for Healthcare ML Platform

Prepares clinical data and text for Clinical BERT embeddings and ML processing
while maintaining medical similarity for disease prediction algorithms.
"""

import re
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import structlog
from collections import defaultdict

from .schemas import AnonymizedMLProfile, AgeGroup, PregnancyStatus, SeasonCategory, LocationCategory

logger = structlog.get_logger(__name__)

class VectorFeaturePreparator:
    """
    Prepares clinical features for vector embeddings and ML processing.
    
    Optimizes clinical text and categorical features for Clinical BERT
    while preserving medical similarity for disease prediction.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize vector feature preparator.
        
        Args:
            config: Configuration for feature preparation
        """
        self.config = config or {}
        self.logger = logger.bind(component="VectorFeaturePreparator")
        
        # Clinical text preprocessing settings
        self.max_text_length = self.config.get('max_text_length', 512)
        self.min_text_length = self.config.get('min_text_length', 10)
        
        # Medical domain vocabulary
        self._load_medical_vocabulary()
        
        # Feature encoding configurations
        self.categorical_encodings = self._initialize_categorical_encodings()
    
    # CLINICAL BERT PREPARATION METHODS
    
    async def prepare_clinical_text_for_bert(
        self,
        clinical_text: str,
        categories: Dict[str, Any]
    ) -> str:
        """
        Prepare clinical text for Clinical BERT embedding.
        
        Args:
            clinical_text: Raw clinical text
            categories: Patient categorical features
            
        Returns:
            Enhanced clinical text optimized for Clinical BERT
        """
        try:
            # Clean and normalize clinical text
            cleaned_text = await self.sanitize_clinical_text(clinical_text)
            
            # Enhance with medical context
            enhanced_text = await self.enhance_with_medical_context(
                cleaned_text, categories
            )
            
            # Validate text quality
            if not await self.validate_text_for_embedding(enhanced_text):
                # Fallback to basic clinical context
                enhanced_text = self.create_clinical_prompt_template(
                    categories.get("age_group", "unknown"),
                    categories.get("pregnancy_status", "not_pregnant"),
                    categories.get("season_category", "winter")
                )
            
            self.logger.info(
                "Clinical text prepared for BERT",
                original_length=len(clinical_text),
                enhanced_length=len(enhanced_text)
            )
            
            return enhanced_text
            
        except Exception as e:
            self.logger.error(
                "Failed to prepare clinical text for BERT",
                error=str(e)
            )
            # Return safe fallback
            return self._create_fallback_clinical_text(categories)
    
    async def enhance_with_medical_context(
        self,
        text: str,
        patient_features: Dict[str, Any]
    ) -> str:
        """
        Enhance clinical text with patient-specific medical context.
        
        Args:
            text: Clinical text to enhance
            patient_features: Patient categorical features
            
        Returns:
            Enhanced clinical text with medical context
        """
        try:
            # Extract key patient characteristics
            age_group = patient_features.get("age_group", "unknown")
            pregnancy_status = patient_features.get("pregnancy_status", "not_pregnant")
            season = patient_features.get("season_category", "winter")
            location = patient_features.get("location_category", "unknown")
            medical_history = patient_features.get("medical_history_categories", [])
            
            # Build medical context prompt
            context_parts = []
            
            # Age and pregnancy context
            if pregnancy_status != "not_pregnant":
                context_parts.append(f"pregnant patient in {pregnancy_status.replace('_', ' ')}")
            else:
                context_parts.append(f"patient in {age_group.replace('_', ' ')} age group")
            
            # Seasonal and location context
            if season and location:
                context_parts.append(f"during {season} season in {location.replace('_', ' ')} area")
            
            # Medical history context
            if medical_history:
                history_text = ", ".join([
                    hist.replace("_history", "").replace("_", " ") 
                    for hist in medical_history[:3]  # Limit to top 3
                ])
                context_parts.append(f"with history of {history_text}")
            
            # Combine original text with context
            context_string = ". ".join(context_parts)
            enhanced_text = f"{text.strip()}. Patient characteristics: {context_string}."
            
            # Ensure length limits
            if len(enhanced_text) > self.max_text_length:
                # Truncate while preserving medical context
                text_limit = self.max_text_length - len(context_string) - 50
                truncated_text = text[:text_limit].strip()
                enhanced_text = f"{truncated_text}. Patient characteristics: {context_string}."
            
            return enhanced_text
            
        except Exception as e:
            self.logger.error(
                "Failed to enhance text with medical context",
                error=str(e)
            )
            return text  # Return original text as fallback
    
    def create_clinical_prompt_template(
        self,
        age_group: str,
        pregnancy: str,
        season: str
    ) -> str:
        """
        Create clinical prompt template for consistent embeddings.
        
        Args:
            age_group: Patient age group
            pregnancy: Pregnancy status
            season: Season category
            
        Returns:
            Standardized clinical prompt template
        """
        # Base medical prompt
        prompt_parts = ["Clinical assessment for"]
        
        # Add demographic context
        if pregnancy != "not_pregnant" and "pregnant" in pregnancy:
            prompt_parts.append(f"{pregnancy.replace('_', ' ')} patient")
        else:
            prompt_parts.append(f"{age_group.replace('_', ' ')} patient")
        
        # Add temporal context
        prompt_parts.append(f"during {season} season")
        
        # Add clinical focus
        prompt_parts.append("with focus on symptom evaluation and disease risk assessment")
        
        return " ".join(prompt_parts) + "."
    
    async def validate_text_for_embedding(self, text: str) -> bool:
        """
        Validate clinical text quality for embedding generation.
        
        Args:
            text: Clinical text to validate
            
        Returns:
            True if text is suitable for embedding
        """
        if not text or len(text.strip()) < self.min_text_length:
            return False
        
        if len(text) > self.max_text_length:
            return False
        
        # Check for medical content
        medical_keywords = [
            "patient", "clinical", "symptom", "diagnosis", "treatment",
            "medical", "health", "condition", "disease", "therapy"
        ]
        
        text_lower = text.lower()
        medical_content = any(keyword in text_lower for keyword in medical_keywords)
        
        # Check for meaningful content (not just spaces/punctuation)
        word_count = len(text.split())
        
        return medical_content and word_count >= 5
    
    async def sanitize_clinical_text(self, text: str) -> str:
        """
        Sanitize clinical text for safe processing.
        
        Args:
            text: Raw clinical text
            
        Returns:
            Sanitized clinical text
        """
        if not text:
            return ""
        
        # Remove potential PII patterns (extra safety)
        # Names pattern (simple)
        text = re.sub(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', '[NAME]', text)
        
        # Phone numbers
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
        
        # SSN patterns
        text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', text)
        
        # Email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
        
        # Clean whitespace and normalize
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove very long words (likely corrupted data)
        words = text.split()
        cleaned_words = [word for word in words if len(word) <= 50]
        
        return ' '.join(cleaned_words)
    
    async def batch_prepare_texts(
        self,
        texts: List[str],
        categories: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Prepare multiple clinical texts efficiently.
        
        Args:
            texts: List of clinical texts
            categories: List of patient categorical features
            
        Returns:
            List of prepared clinical texts
        """
        if len(texts) != len(categories):
            raise ValueError("Texts and categories lists must have same length")
        
        prepared_texts = []
        
        for text, category in zip(texts, categories):
            try:
                prepared_text = await self.prepare_clinical_text_for_bert(
                    text, category
                )
                prepared_texts.append(prepared_text)
            except Exception as e:
                self.logger.error(
                    "Failed to prepare text in batch",
                    error=str(e)
                )
                # Add fallback text
                prepared_texts.append(
                    self._create_fallback_clinical_text(category)
                )
        
        self.logger.info(
            "Batch text preparation completed",
            total_texts=len(texts),
            successful=len(prepared_texts)
        )
        
        return prepared_texts
    
    # FEATURE VECTOR METHODS
    
    def encode_categorical_features(self, features: Dict[str, Any]) -> List[float]:
        """
        Encode categorical features as numerical vectors.
        
        Args:
            features: Dictionary of categorical features
            
        Returns:
            List of encoded numerical features
        """
        encoded_features = []
        
        # Age group encoding
        age_group = features.get("age_group", "unknown")
        age_encoding = self.categorical_encodings["age_group"].get(age_group, 0.0)
        encoded_features.append(age_encoding)
        
        # Gender encoding
        gender = features.get("gender_category", "unknown")
        gender_encoding = self.categorical_encodings["gender"].get(gender, 0.0)
        encoded_features.append(gender_encoding)
        
        # Pregnancy status encoding
        pregnancy = features.get("pregnancy_status", "not_pregnant")
        pregnancy_encoding = self.categorical_encodings["pregnancy"].get(pregnancy, 0.0)
        encoded_features.append(pregnancy_encoding)
        
        # Season encoding
        season = features.get("season_category", "winter")
        season_encoding = self.categorical_encodings["season"].get(season, 0.0)
        encoded_features.append(season_encoding)
        
        # Location encoding
        location = features.get("location_category", "unknown")
        location_encoding = self.categorical_encodings["location"].get(location, 0.0)
        encoded_features.append(location_encoding)
        
        # Medical history encoding (multi-hot encoding)
        medical_history = features.get("medical_history_categories", [])
        for category in self.categorical_encodings["medical_categories"]:
            encoded_features.append(1.0 if category in medical_history else 0.0)
        
        # Risk factors encoding (count-based)
        risk_factors = features.get("risk_factors", [])
        encoded_features.append(float(len(risk_factors)))
        
        return encoded_features
    
    def normalize_numerical_features(self, features: Dict[str, Any]) -> Dict[str, float]:
        """
        Normalize numerical features for ML processing.
        
        Args:
            features: Dictionary of features including numerical ones
            
        Returns:
            Normalized numerical features
        """
        normalized = {}
        
        # Comorbidity indicators
        comorbidity = features.get("comorbidity_indicators", {})
        
        # Normalize comorbidity count (0-10 scale)
        comorbidity_count = comorbidity.get("total_comorbidity_count", 0)
        normalized["comorbidity_count_normalized"] = min(comorbidity_count / 10.0, 1.0)
        
        # Normalize weighted score (0-20 scale)
        weighted_score = comorbidity.get("weighted_comorbidity_score", 0)
        normalized["comorbidity_score_normalized"] = min(weighted_score / 20.0, 1.0)
        
        # Care complexity encoding
        complexity = features.get("care_complexity", "low_complexity")
        complexity_mapping = {
            "low_complexity": 0.25,
            "moderate_complexity": 0.5,
            "high_complexity": 0.75,
            "very_high_complexity": 1.0
        }
        normalized["care_complexity_normalized"] = complexity_mapping.get(complexity, 0.25)
        
        # Utilization pattern encoding
        utilization = features.get("utilization_pattern", "low_utilization")
        utilization_mapping = {
            "no_recent_utilization": 0.0,
            "low_utilization": 0.2,
            "moderate_utilization": 0.4,
            "high_utilization": 0.7,
            "very_high_utilization": 1.0
        }
        normalized["utilization_normalized"] = utilization_mapping.get(utilization, 0.2)
        
        return normalized
    
    def create_similarity_feature_vector(
        self,
        profile: AnonymizedMLProfile
    ) -> List[float]:
        """
        Create feature vector optimized for similarity matching.
        
        Args:
            profile: Anonymized ML profile
            
        Returns:
            Similarity-optimized feature vector
        """
        features = []
        
        # Demographic features (weighted for medical similarity)
        categorical_features = self.encode_categorical_features(
            profile.categorical_features
        )
        features.extend(categorical_features)
        
        # Normalized numerical features
        normalized_features = self.normalize_numerical_features(
            profile.categorical_features
        )
        features.extend(normalized_features.values())
        
        # Similarity weights (for weighted distance calculations)
        similarity_metadata = profile.similarity_metadata
        weight_features = [
            similarity_metadata.get("medical_similarity_weight", 0.8),
            similarity_metadata.get("demographic_similarity_weight", 0.3),
            similarity_metadata.get("temporal_similarity_weight", 0.5),
            similarity_metadata.get("geographic_similarity_weight", 0.4)
        ]
        features.extend(weight_features)
        
        return features
    
    def combine_text_and_categorical_features(
        self,
        text_embedding: List[float],
        categories: Dict[str, Any]
    ) -> List[float]:
        """
        Combine Clinical BERT text embedding with categorical features.
        
        Args:
            text_embedding: 768-dimensional Clinical BERT embedding
            categories: Categorical feature dictionary
            
        Returns:
            Combined feature vector
        """
        if len(text_embedding) != 768:
            raise ValueError("Text embedding must be 768-dimensional")
        
        # Start with text embedding (768 dimensions)
        combined_features = text_embedding.copy()
        
        # Add categorical features
        categorical_encoded = self.encode_categorical_features(categories)
        combined_features.extend(categorical_encoded)
        
        # Add normalized numerical features
        normalized_features = self.normalize_numerical_features(categories)
        combined_features.extend(normalized_features.values())
        
        return combined_features
    
    async def validate_feature_quality(
        self,
        features: List[float]
    ) -> Dict[str, Any]:
        """
        Validate quality of prepared features.
        
        Args:
            features: Feature vector to validate
            
        Returns:
            Feature quality metrics
        """
        if not features:
            return {
                "valid": False,
                "issues": ["Empty feature vector"],
                "quality_score": 0.0
            }
        
        issues = []
        quality_score = 1.0
        
        # Check for NaN or infinite values
        nan_count = sum(1 for f in features if np.isnan(f) or np.isinf(f))
        if nan_count > 0:
            issues.append(f"Contains {nan_count} NaN/infinite values")
            quality_score -= 0.3
        
        # Check feature range (should be mostly 0-1 for normalized features)
        out_of_range = sum(1 for f in features if f < -1.0 or f > 1.0)
        if out_of_range > len(features) * 0.1:  # More than 10% out of range
            issues.append(f"Too many features out of normal range: {out_of_range}")
            quality_score -= 0.2
        
        # Check for sufficient variance
        feature_variance = np.var(features) if len(features) > 1 else 0
        if feature_variance < 0.01:
            issues.append("Low feature variance may reduce ML effectiveness")
            quality_score -= 0.1
        
        # Check vector length
        expected_min_length = 10  # Minimum expected features
        if len(features) < expected_min_length:
            issues.append(f"Feature vector too short: {len(features)}")
            quality_score -= 0.2
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "quality_score": max(quality_score, 0.0),
            "feature_count": len(features),
            "nan_count": nan_count,
            "variance": float(feature_variance)
        }
    
    # ML READINESS VALIDATION
    
    def check_vector_dimension_consistency(
        self,
        vectors: List[List[float]]
    ) -> bool:
        """
        Check that all vectors have consistent dimensions.
        
        Args:
            vectors: List of feature vectors
            
        Returns:
            True if all vectors have same dimension
        """
        if not vectors:
            return True
        
        first_dim = len(vectors[0])
        return all(len(vector) == first_dim for vector in vectors)
    
    async def calculate_feature_importance(
        self,
        features: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Calculate importance scores for different feature types.
        
        Args:
            features: Feature dictionary
            
        Returns:
            Feature importance scores
        """
        importance_scores = {}
        
        # Medical history importance (high for disease prediction)
        medical_history = features.get("medical_history_categories", [])
        importance_scores["medical_history"] = min(len(medical_history) * 0.2, 1.0)
        
        # Age importance (varies by age group)
        age_group = features.get("age_group", "unknown")
        age_importance_map = {
            "pediatric": 0.8,
            "elderly": 0.9,
            "reproductive_age": 0.7,
            "middle_age": 0.6,
            "young_adult": 0.5
        }
        importance_scores["age"] = age_importance_map.get(age_group, 0.5)
        
        # Pregnancy importance (very high when pregnant)
        pregnancy = features.get("pregnancy_status", "not_pregnant")
        importance_scores["pregnancy"] = 0.9 if "pregnant" in pregnancy else 0.1
        
        # Seasonal importance (medium for disease patterns)
        importance_scores["season"] = 0.6
        
        # Location importance (medium for exposure patterns)
        importance_scores["location"] = 0.5
        
        # Risk factors importance (high)
        risk_factors = features.get("risk_factors", [])
        importance_scores["risk_factors"] = min(len(risk_factors) * 0.15, 1.0)
        
        return importance_scores
    
    def generate_feature_metadata(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate metadata about extracted features.
        
        Args:
            features: Feature dictionary
            
        Returns:
            Feature metadata
        """
        metadata = {
            "feature_extraction_timestamp": datetime.utcnow().isoformat(),
            "feature_extractor_version": "v1.0",
            "total_features": len(features),
            "feature_types": {}
        }
        
        # Categorize feature types
        categorical_features = [
            "age_group", "gender_category", "pregnancy_status",
            "location_category", "season_category"
        ]
        
        list_features = [
            "medical_history_categories", "medication_categories",
            "allergy_categories", "risk_factors"
        ]
        
        numerical_features = [
            "comorbidity_indicators", "utilization_pattern", "care_complexity"
        ]
        
        metadata["feature_types"]["categorical"] = [
            f for f in categorical_features if f in features
        ]
        metadata["feature_types"]["list_based"] = [
            f for f in list_features if f in features
        ]
        metadata["feature_types"]["numerical"] = [
            f for f in numerical_features if f in features
        ]
        
        # Calculate feature complexity
        total_categories = sum(
            len(features.get(f, [])) if isinstance(features.get(f), list) else 1
            for f in features
        )
        metadata["feature_complexity_score"] = min(total_categories / 20.0, 1.0)
        
        return metadata
    
    # PRIVATE HELPER METHODS
    
    def _load_medical_vocabulary(self):
        """Load medical domain vocabulary for text processing."""
        self.medical_vocabulary = {
            "symptoms": [
                "fever", "cough", "shortness of breath", "chest pain",
                "headache", "nausea", "vomiting", "diarrhea", "fatigue"
            ],
            "conditions": [
                "pneumonia", "asthma", "diabetes", "hypertension",
                "depression", "anxiety", "arthritis", "cancer"
            ],
            "treatments": [
                "medication", "therapy", "surgery", "rehabilitation",
                "counseling", "monitoring", "prevention"
            ]
        }
    
    def _initialize_categorical_encodings(self) -> Dict[str, Dict[str, float]]:
        """Initialize categorical feature encodings."""
        return {
            "age_group": {
                "pediatric": 0.1,
                "young_adult": 0.2,
                "reproductive_age": 0.4,
                "middle_age": 0.6,
                "older_adult": 0.8,
                "elderly": 1.0
            },
            "gender": {
                "male": 0.3,
                "female": 0.6,
                "other": 0.9
            },
            "pregnancy": {
                "not_pregnant": 0.0,
                "pregnant_trimester_1": 0.3,
                "pregnant_trimester_2": 0.6,
                "pregnant_trimester_3": 0.9,
                "postpartum": 1.0
            },
            "season": {
                "winter": 0.1,
                "spring": 0.4,
                "summer": 0.7,
                "fall": 1.0
            },
            "location": {
                "urban_northeast": 0.1,
                "urban_southeast": 0.2,
                "urban_midwest": 0.3,
                "urban_west": 0.4,
                "rural_northeast": 0.6,
                "rural_southeast": 0.7,
                "rural_midwest": 0.8,
                "rural_west": 0.9
            },
            "medical_categories": [
                "respiratory_history", "cardiac_history", "allergic_history",
                "diabetic_history", "neurological_history", "psychiatric_history",
                "oncological_history", "infectious_disease_history",
                "autoimmune_history", "surgical_history"
            ]
        }
    
    def _create_fallback_clinical_text(self, categories: Dict[str, Any]) -> str:
        """Create fallback clinical text when processing fails."""
        age_group = categories.get("age_group", "adult")
        pregnancy = categories.get("pregnancy_status", "not_pregnant")
        season = categories.get("season_category", "winter")
        
        if "pregnant" in pregnancy:
            return f"Clinical assessment for pregnant patient during {season} season."
        else:
            return f"Clinical assessment for {age_group.replace('_', ' ')} patient during {season} season."