"""
Clinical XAI Engine for Healthcare Platform V2.0

Enterprise-grade explainable AI engine providing comprehensive interpretability
for healthcare AI decisions with SHAP explanations, attention visualization,
uncertainty quantification, and clinical reasoning chains.
"""

import asyncio
import logging
import uuid
import numpy as np
import torch
import torch.nn as nn
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum

# XAI and interpretability frameworks
import shap
import captum
from captum.attr import IntegratedGradients, DeepLift, GradientShap, Occlusion
from captum.attr import LayerGradCam, LayerAttribution, LayerConductance
import lime
from lime.lime_text import LimeTextExplainer
from lime.lime_tabular import LimeTabularExplainer

# Medical knowledge and visualization
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# Internal imports
from .schemas import (
    XAIConfig, SHAPExplanation, AttentionMaps, MultimodalExplanation,
    CounterfactualExamples, RuleExplanation, FeatureImportance,
    UncertaintyExplanation, TemporalExplanation, ImageExplanation,
    ValidationMetrics
)
from ..multimodal_ai.schemas import MultimodalPrediction, FusedEmbedding
from ..edge_ai.schemas import GemmaOutput, ReasoningChain
from ...core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class ExplanationMethod(str, Enum):
    """Available explanation methods."""
    SHAP = "shap"
    LIME = "lime"
    INTEGRATED_GRADIENTS = "integrated_gradients"
    GRAD_CAM = "grad_cam"
    ATTENTION_MAPS = "attention_maps"
    COUNTERFACTUALS = "counterfactuals"
    RULE_BASED = "rule_based"

class ExplanationType(str, Enum):
    """Types of explanations."""
    GLOBAL = "global"
    LOCAL = "local"
    INSTANCE = "instance"
    COHORT = "cohort"

class MedicalSpecialty(str, Enum):
    """Medical specialties for context-aware explanations."""
    CARDIOLOGY = "cardiology"
    NEUROLOGY = "neurology"
    ONCOLOGY = "oncology"
    RADIOLOGY = "radiology"
    EMERGENCY_MEDICINE = "emergency_medicine"
    INTERNAL_MEDICINE = "internal_medicine"

@dataclass
class XAIConfig:
    """Configuration for Clinical XAI Engine."""
    
    # Core XAI settings
    enable_shap_explanations: bool = True
    enable_attention_visualization: bool = True
    enable_uncertainty_quantification: bool = True
    enable_counterfactuals: bool = True
    
    # Explanation settings
    max_features_to_explain: int = 20
    explanation_sample_size: int = 1000
    confidence_threshold: float = 0.7
    uncertainty_threshold: float = 0.3
    
    # Visualization settings
    generate_visualizations: bool = True
    save_explanation_plots: bool = True
    interactive_explanations: bool = True
    
    # Clinical settings
    use_medical_terminology: bool = True
    specialty_specific_explanations: bool = True
    patient_friendly_mode: bool = False
    
    # Performance settings
    explanation_timeout_seconds: int = 300
    cache_explanations: bool = True
    batch_explanations: bool = True

class ClinicalXAIEngine:
    """
    Enterprise clinical explainable AI engine for healthcare decisions.
    
    Provides comprehensive interpretability for multimodal healthcare AI
    with clinical reasoning, uncertainty quantification, and visual explanations.
    """
    
    def __init__(self, config: XAIConfig):
        self.config = config
        self.logger = logger.bind(component="ClinicalXAIEngine")
        
        # Initialize explanation methods
        self.shap_explainer = None
        self.lime_explainer = None
        self.captum_explainers = {}
        
        # Medical knowledge bases
        self.medical_ontology = self._load_medical_ontology()
        self.clinical_rules = self._load_clinical_rules()
        self.drug_interactions = self._load_drug_interactions()
        
        # Explanation cache
        self.explanation_cache: Dict[str, Any] = {}
        self.visualization_cache: Dict[str, bytes] = {}
        
        # Statistical models for uncertainty
        self.uncertainty_models = {}
        
        self.logger.info("ClinicalXAIEngine initialized successfully")

    def _load_medical_ontology(self) -> Dict[str, Any]:
        """Load medical ontology for clinical explanations."""
        return {
            "conditions": {
                "diabetes": {
                    "icd_codes": ["E11", "E10"],
                    "snomed_codes": ["73211009"],
                    "symptoms": ["polyuria", "polydipsia", "fatigue"],
                    "risk_factors": ["obesity", "family_history", "age"],
                    "complications": ["nephropathy", "retinopathy", "neuropathy"]
                },
                "hypertension": {
                    "icd_codes": ["I10"],
                    "snomed_codes": ["38341003"],
                    "symptoms": ["headache", "dizziness", "chest_pain"],
                    "risk_factors": ["age", "obesity", "smoking", "stress"],
                    "complications": ["stroke", "heart_attack", "kidney_disease"]
                }
            },
            "medications": {
                "metformin": {
                    "indications": ["diabetes", "prediabetes"],
                    "contraindications": ["kidney_disease", "liver_disease"],
                    "side_effects": ["nausea", "diarrhea", "lactic_acidosis"]
                }
            }
        }

    def _load_clinical_rules(self) -> Dict[str, Any]:
        """Load clinical decision rules."""
        return {
            "diabetes_screening": {
                "rule": "Age >= 45 OR BMI >= 25 AND risk_factors >= 1",
                "evidence_level": "A",
                "guideline": "ADA 2023 Standards of Care"
            },
            "hypertension_diagnosis": {
                "rule": "SBP >= 140 OR DBP >= 90 on two separate occasions",
                "evidence_level": "A", 
                "guideline": "ACC/AHA 2017 Guidelines"
            }
        }

    def _load_drug_interactions(self) -> Dict[str, Any]:
        """Load drug interaction database."""
        return {
            ("warfarin", "aspirin"): {
                "severity": "major",
                "effect": "increased_bleeding_risk",
                "mechanism": "additive_anticoagulation"
            },
            ("metformin", "contrast_dye"): {
                "severity": "major",
                "effect": "lactic_acidosis_risk",
                "mechanism": "renal_impairment"
            }
        }

    async def generate_shap_explanations(
        self, 
        model: Any, 
        input_data: Dict[str, Any]
    ) -> SHAPExplanation:
        """
        Generate SHAP explanations for model predictions.
        
        Args:
            model: Trained model to explain
            input_data: Input data for explanation
            
        Returns:
            SHAPExplanation with feature attributions
        """
        try:
            explanation_id = str(uuid.uuid4())
            
            # Initialize SHAP explainer based on model type
            if self.shap_explainer is None:
                self.shap_explainer = await self._initialize_shap_explainer(model, input_data)
            
            # Extract feature data
            if "multimodal_features" in input_data:
                features = self._extract_multimodal_features(input_data["multimodal_features"])
            else:
                features = self._extract_tabular_features(input_data)
            
            # Generate SHAP values
            shap_values = self.shap_explainer.shap_values(features)
            
            # Process SHAP values for different data types
            if isinstance(shap_values, list):
                # Multi-class classification
                processed_shap_values = self._process_multiclass_shap(shap_values)
            else:
                # Binary classification or regression
                processed_shap_values = shap_values
            
            # Calculate feature importance
            feature_importance = np.abs(processed_shap_values).mean(axis=0)
            feature_names = self._get_feature_names(input_data)
            
            # Create feature importance ranking
            importance_ranking = sorted(
                zip(feature_names, feature_importance),
                key=lambda x: x[1],
                reverse=True
            )[:self.config.max_features_to_explain]
            
            # Generate clinical interpretation
            clinical_interpretation = await self._generate_clinical_interpretation(
                importance_ranking, input_data
            )
            
            # Create visualizations
            visualizations = {}
            if self.config.generate_visualizations:
                visualizations = await self._create_shap_visualizations(
                    processed_shap_values, feature_names, explanation_id
                )
            
            shap_explanation = SHAPExplanation(
                explanation_id=explanation_id,
                shap_values=processed_shap_values.tolist(),
                feature_importance=dict(importance_ranking),
                feature_names=feature_names,
                base_value=float(self.shap_explainer.expected_value),
                clinical_interpretation=clinical_interpretation,
                visualizations=visualizations,
                explanation_method="TreeSHAP" if hasattr(self.shap_explainer, 'model') else "KernelSHAP",
                confidence_score=await self._calculate_explanation_confidence(processed_shap_values)
            )
            
            # Cache explanation
            if self.config.cache_explanations:
                self.explanation_cache[explanation_id] = shap_explanation
            
            self.logger.info(
                "SHAP explanation generated",
                explanation_id=explanation_id,
                feature_count=len(feature_names),
                top_feature=importance_ranking[0][0] if importance_ranking else "none"
            )
            
            return shap_explanation
            
        except Exception as e:
            self.logger.error(
                "Failed to generate SHAP explanations",
                error=str(e)
            )
            raise

    async def create_attention_visualizations(
        self, 
        transformer_output: Dict[str, Any]
    ) -> AttentionMaps:
        """
        Create attention visualizations for transformer models.
        
        Args:
            transformer_output: Output from transformer model with attention
            
        Returns:
            AttentionMaps with visualization data
        """
        try:
            attention_id = str(uuid.uuid4())
            
            # Extract attention weights
            attention_weights = transformer_output.get("attention_weights")
            if attention_weights is None:
                raise ValueError("No attention weights found in transformer output")
            
            # Convert to numpy if needed
            if isinstance(attention_weights, torch.Tensor):
                attention_weights = attention_weights.detach().cpu().numpy()
            
            # Process attention weights for different heads and layers
            processed_attention = await self._process_attention_weights(attention_weights)
            
            # Extract tokens/features
            input_tokens = transformer_output.get("input_tokens", [])
            if isinstance(input_tokens, torch.Tensor):
                input_tokens = input_tokens.tolist()
            
            # Calculate attention statistics
            attention_stats = {
                "mean_attention": float(np.mean(processed_attention)),
                "max_attention": float(np.max(processed_attention)),
                "attention_entropy": float(self._calculate_attention_entropy(processed_attention)),
                "focused_tokens": await self._identify_focused_tokens(processed_attention, input_tokens)
            }
            
            # Generate medical entity attention
            medical_attention = await self._analyze_medical_entity_attention(
                processed_attention, input_tokens
            )
            
            # Create attention visualizations
            visualizations = {}
            if self.config.generate_visualizations:
                visualizations = await self._create_attention_visualizations(
                    processed_attention, input_tokens, attention_id
                )
            
            attention_maps = AttentionMaps(
                attention_id=attention_id,
                attention_weights=processed_attention.tolist(),
                input_tokens=input_tokens,
                attention_statistics=attention_stats,
                medical_entity_attention=medical_attention,
                layer_wise_attention=await self._extract_layer_wise_attention(attention_weights),
                head_wise_attention=await self._extract_head_wise_attention(attention_weights),
                visualizations=visualizations,
                clinical_interpretation=await self._interpret_attention_clinically(
                    processed_attention, input_tokens
                )
            )
            
            self.logger.info(
                "Attention visualization created",
                attention_id=attention_id,
                token_count=len(input_tokens),
                mean_attention=attention_stats["mean_attention"]
            )
            
            return attention_maps
            
        except Exception as e:
            self.logger.error(
                "Failed to create attention visualizations",
                error=str(e)
            )
            raise

    async def explain_multimodal_decision(
        self, 
        fusion_output: FusedEmbedding
    ) -> MultimodalExplanation:
        """
        Explain multimodal AI decision with cross-modal analysis.
        
        Args:
            fusion_output: Fused multimodal embedding
            
        Returns:
            MultimodalExplanation with modality-specific insights
        """
        try:
            explanation_id = str(uuid.uuid4())
            
            # Analyze modality contributions
            modality_contributions = await self._analyze_modality_contributions(fusion_output)
            
            # Generate modality-specific explanations
            modality_explanations = {}
            
            for embedding in fusion_output.component_embeddings:
                modality_type = type(embedding).__name__
                
                if "ClinicalText" in modality_type:
                    modality_explanations["clinical_text"] = await self._explain_text_contribution(
                        embedding, fusion_output
                    )
                elif "Image" in modality_type:
                    modality_explanations["medical_image"] = await self._explain_image_contribution(
                        embedding, fusion_output
                    )
                elif "Audio" in modality_type:
                    modality_explanations["audio"] = await self._explain_audio_contribution(
                        embedding, fusion_output
                    )
                elif "Lab" in modality_type:
                    modality_explanations["lab_data"] = await self._explain_lab_contribution(
                        embedding, fusion_output
                    )
                elif "Omics" in modality_type:
                    modality_explanations["genomic_data"] = await self._explain_genomic_contribution(
                        embedding, fusion_output
                    )
            
            # Analyze cross-modal interactions
            cross_modal_interactions = await self._analyze_cross_modal_interactions(
                fusion_output.component_embeddings
            )
            
            # Generate fusion explanation
            fusion_explanation = await self._explain_fusion_mechanism(
                fusion_output.fusion_method, fusion_output.attention_weights
            )
            
            # Calculate explanation confidence
            explanation_confidence = await self._calculate_multimodal_explanation_confidence(
                modality_explanations, cross_modal_interactions
            )
            
            # Generate clinical summary
            clinical_summary = await self._generate_multimodal_clinical_summary(
                modality_explanations, cross_modal_interactions, fusion_output
            )
            
            multimodal_explanation = MultimodalExplanation(
                explanation_id=explanation_id,
                modality_contributions=modality_contributions,
                modality_explanations=modality_explanations,
                cross_modal_interactions=cross_modal_interactions,
                fusion_explanation=fusion_explanation,
                attention_analysis=await self._analyze_fusion_attention(fusion_output),
                uncertainty_analysis=await self._analyze_multimodal_uncertainty(fusion_output),
                clinical_summary=clinical_summary,
                explanation_confidence=explanation_confidence,
                recommendations=await self._generate_multimodal_recommendations(
                    modality_explanations, cross_modal_interactions
                )
            )
            
            self.logger.info(
                "Multimodal explanation generated",
                explanation_id=explanation_id,
                modality_count=len(modality_explanations),
                explanation_confidence=explanation_confidence
            )
            
            return multimodal_explanation
            
        except Exception as e:
            self.logger.error(
                "Failed to explain multimodal decision",
                error=str(e)
            )
            raise

    async def generate_counterfactual_examples(
        self, 
        patient_data: Dict[str, Any], 
        prediction: Dict[str, Any]
    ) -> CounterfactualExamples:
        """
        Generate counterfactual examples for clinical decision making.
        
        Args:
            patient_data: Original patient data
            prediction: Model prediction to explain
            
        Returns:
            CounterfactualExamples with alternative scenarios
        """
        try:
            counterfactual_id = str(uuid.uuid4())
            
            # Identify modifiable features
            modifiable_features = await self._identify_modifiable_features(patient_data)
            
            # Generate counterfactuals for different scenarios
            counterfactuals = []
            
            # Scenario 1: Treatment response counterfactual
            if "medications" in patient_data:
                treatment_counterfactual = await self._generate_treatment_counterfactual(
                    patient_data, prediction, modifiable_features
                )
                counterfactuals.append(treatment_counterfactual)
            
            # Scenario 2: Risk factor modification
            risk_factor_counterfactual = await self._generate_risk_factor_counterfactual(
                patient_data, prediction, modifiable_features
            )
            counterfactuals.append(risk_factor_counterfactual)
            
            # Scenario 3: Lifestyle intervention
            lifestyle_counterfactual = await self._generate_lifestyle_counterfactual(
                patient_data, prediction, modifiable_features
            )
            counterfactuals.append(lifestyle_counterfactual)
            
            # Analyze counterfactual feasibility
            feasibility_analysis = await self._analyze_counterfactual_feasibility(
                counterfactuals, patient_data
            )
            
            # Calculate clinical impact
            clinical_impact = await self._calculate_counterfactual_clinical_impact(
                counterfactuals, prediction
            )
            
            # Generate actionable recommendations
            actionable_recommendations = await self._generate_actionable_recommendations(
                counterfactuals, feasibility_analysis
            )
            
            counterfactual_examples = CounterfactualExamples(
                counterfactual_id=counterfactual_id,
                original_prediction=prediction,
                counterfactual_scenarios=counterfactuals,
                modifiable_features=modifiable_features,
                feasibility_analysis=feasibility_analysis,
                clinical_impact=clinical_impact,
                actionable_recommendations=actionable_recommendations,
                explanation_confidence=await self._calculate_counterfactual_confidence(counterfactuals),
                clinical_validity=await self._validate_counterfactual_clinical_validity(counterfactuals)
            )
            
            self.logger.info(
                "Counterfactual examples generated",
                counterfactual_id=counterfactual_id,
                scenario_count=len(counterfactuals),
                modifiable_features=len(modifiable_features)
            )
            
            return counterfactual_examples
            
        except Exception as e:
            self.logger.error(
                "Failed to generate counterfactual examples",
                error=str(e)
            )
            raise

    async def create_clinical_rule_explanations(
        self, 
        decision: Dict[str, Any]
    ) -> RuleExplanation:
        """
        Create rule-based explanations for clinical decisions.
        
        Args:
            decision: Clinical decision to explain
            
        Returns:
            RuleExplanation with rule-based reasoning
        """
        try:
            rule_id = str(uuid.uuid4())
            
            # Identify applicable clinical rules
            applicable_rules = await self._identify_applicable_rules(decision)
            
            # Evaluate rule conditions
            rule_evaluations = {}
            for rule_name, rule_data in applicable_rules.items():
                evaluation = await self._evaluate_rule_conditions(rule_data, decision)
                rule_evaluations[rule_name] = evaluation
            
            # Generate rule-based reasoning
            rule_reasoning = await self._generate_rule_reasoning(rule_evaluations)
            
            # Check for rule conflicts
            rule_conflicts = await self._detect_rule_conflicts(rule_evaluations)
            
            # Calculate rule confidence
            rule_confidence = await self._calculate_rule_confidence(rule_evaluations)
            
            # Generate evidence summary
            evidence_summary = await self._generate_evidence_summary(applicable_rules)
            
            # Create guideline references
            guideline_references = await self._extract_guideline_references(applicable_rules)
            
            rule_explanation = RuleExplanation(
                rule_id=rule_id,
                applicable_rules=applicable_rules,
                rule_evaluations=rule_evaluations,
                rule_reasoning=rule_reasoning,
                rule_conflicts=rule_conflicts,
                evidence_level=await self._determine_evidence_level(applicable_rules),
                guideline_references=guideline_references,
                clinical_confidence=rule_confidence,
                recommendations=await self._generate_rule_based_recommendations(rule_evaluations),
                validation_status=await self._validate_rule_consistency(rule_evaluations)
            )
            
            self.logger.info(
                "Clinical rule explanation created",
                rule_id=rule_id,
                applicable_rules_count=len(applicable_rules),
                rule_confidence=rule_confidence
            )
            
            return rule_explanation
            
        except Exception as e:
            self.logger.error(
                "Failed to create clinical rule explanations",
                error=str(e)
            )
            raise

    async def calculate_feature_importance(
        self, 
        model_output: Dict[str, Any]
    ) -> FeatureImportance:
        """
        Calculate comprehensive feature importance for model predictions.
        
        Args:
            model_output: Model output with predictions and features
            
        Returns:
            FeatureImportance with detailed feature analysis
        """
        try:
            importance_id = str(uuid.uuid4())
            
            # Extract features and predictions
            features = model_output.get("features", {})
            predictions = model_output.get("predictions", {})
            
            # Calculate different types of feature importance
            importance_methods = {}
            
            # Permutation importance
            if "permutation_importance" in model_output:
                importance_methods["permutation"] = model_output["permutation_importance"]
            else:
                importance_methods["permutation"] = await self._calculate_permutation_importance(
                    features, predictions
                )
            
            # Gradient-based importance
            if "gradient_importance" in model_output:
                importance_methods["gradient"] = model_output["gradient_importance"]
            else:
                importance_methods["gradient"] = await self._calculate_gradient_importance(
                    features, predictions
                )
            
            # Clinical importance (domain-specific)
            importance_methods["clinical"] = await self._calculate_clinical_importance(
                features, predictions
            )
            
            # Aggregate importance scores
            aggregated_importance = await self._aggregate_importance_scores(importance_methods)
            
            # Rank features by importance
            feature_ranking = sorted(
                aggregated_importance.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            # Generate feature insights
            feature_insights = await self._generate_feature_insights(
                feature_ranking, features, predictions
            )
            
            # Calculate importance stability
            importance_stability = await self._calculate_importance_stability(importance_methods)
            
            feature_importance = FeatureImportance(
                importance_id=importance_id,
                feature_scores=aggregated_importance,
                feature_ranking=feature_ranking,
                importance_methods=importance_methods,
                feature_insights=feature_insights,
                clinical_relevance=await self._assess_clinical_relevance(feature_ranking),
                statistical_significance=await self._assess_statistical_significance(feature_ranking),
                importance_stability=importance_stability,
                visualization_data=await self._create_importance_visualizations(
                    feature_ranking, importance_id
                ) if self.config.generate_visualizations else {}
            )
            
            self.logger.info(
                "Feature importance calculated",
                importance_id=importance_id,
                feature_count=len(aggregated_importance),
                top_feature=feature_ranking[0][0] if feature_ranking else "none"
            )
            
            return feature_importance
            
        except Exception as e:
            self.logger.error(
                "Failed to calculate feature importance",
                error=str(e)
            )
            raise

    async def generate_uncertainty_explanations(
        self, 
        prediction: Dict[str, Any]
    ) -> UncertaintyExplanation:
        """
        Generate explanations for prediction uncertainty.
        
        Args:
            prediction: Model prediction with uncertainty metrics
            
        Returns:
            UncertaintyExplanation with uncertainty analysis
        """
        try:
            uncertainty_id = str(uuid.uuid4())
            
            # Extract uncertainty metrics
            uncertainty_metrics = prediction.get("uncertainty_metrics", {})
            
            # Decompose uncertainty sources
            uncertainty_sources = await self._decompose_uncertainty_sources(uncertainty_metrics)
            
            # Analyze aleatoric uncertainty (data uncertainty)
            aleatoric_analysis = await self._analyze_aleatoric_uncertainty(
                uncertainty_metrics, prediction
            )
            
            # Analyze epistemic uncertainty (model uncertainty)
            epistemic_analysis = await self._analyze_epistemic_uncertainty(
                uncertainty_metrics, prediction
            )
            
            # Generate uncertainty explanations
            uncertainty_explanations = {
                "data_quality": await self._explain_data_quality_uncertainty(aleatoric_analysis),
                "model_confidence": await self._explain_model_confidence_uncertainty(epistemic_analysis),
                "feature_uncertainty": await self._explain_feature_uncertainty(uncertainty_sources),
                "prediction_stability": await self._explain_prediction_stability(uncertainty_metrics)
            }
            
            # Calculate uncertainty impact on decision
            decision_impact = await self._calculate_uncertainty_decision_impact(
                uncertainty_metrics, prediction
            )
            
            # Generate uncertainty mitigation recommendations
            mitigation_recommendations = await self._generate_uncertainty_mitigation_recommendations(
                uncertainty_sources, uncertainty_explanations
            )
            
            # Assess clinical implications of uncertainty
            clinical_implications = await self._assess_uncertainty_clinical_implications(
                uncertainty_metrics, prediction
            )
            
            uncertainty_explanation = UncertaintyExplanation(
                uncertainty_id=uncertainty_id,
                uncertainty_sources=uncertainty_sources,
                aleatoric_analysis=aleatoric_analysis,
                epistemic_analysis=epistemic_analysis,
                uncertainty_explanations=uncertainty_explanations,
                decision_impact=decision_impact,
                mitigation_recommendations=mitigation_recommendations,
                clinical_implications=clinical_implications,
                confidence_intervals=await self._calculate_confidence_intervals(uncertainty_metrics),
                uncertainty_visualization=await self._create_uncertainty_visualizations(
                    uncertainty_metrics, uncertainty_id
                ) if self.config.generate_visualizations else {}
            )
            
            self.logger.info(
                "Uncertainty explanation generated",
                uncertainty_id=uncertainty_id,
                total_uncertainty=uncertainty_metrics.get("total_uncertainty", 0),
                sources_count=len(uncertainty_sources)
            )
            
            return uncertainty_explanation
            
        except Exception as e:
            self.logger.error(
                "Failed to generate uncertainty explanations",
                error=str(e)
            )
            raise

    # Helper methods for XAI implementation
    
    async def _initialize_shap_explainer(self, model: Any, input_data: Dict[str, Any]):
        """Initialize appropriate SHAP explainer for the model."""
        try:
            # Determine model type and create appropriate explainer
            if hasattr(model, 'predict_proba'):
                # Tree-based model
                return shap.TreeExplainer(model)
            elif hasattr(model, 'predict'):
                # General ML model
                background_data = self._create_background_data(input_data)
                return shap.KernelExplainer(model.predict, background_data)
            else:
                # Neural network model
                background_data = self._create_background_data(input_data)
                return shap.DeepExplainer(model, background_data)
        except Exception as e:
            self.logger.error(f"Failed to initialize SHAP explainer: {str(e)}")
            raise

    def _create_background_data(self, input_data: Dict[str, Any]) -> np.ndarray:
        """Create background data for SHAP explainer."""
        if "features" in input_data:
            features = input_data["features"]
            if isinstance(features, dict):
                return np.array([list(features.values())])
            elif isinstance(features, list):
                return np.array([features])
            else:
                return np.array([[0] * 10])  # Default background
        return np.array([[0] * 10])

    def _extract_multimodal_features(self, multimodal_data: Dict[str, Any]) -> np.ndarray:
        """Extract features from multimodal data."""
        features = []
        
        # Extract text features
        if "text_embedding" in multimodal_data:
            text_features = multimodal_data["text_embedding"]
            if isinstance(text_features, list):
                features.extend(text_features[:50])  # Limit for performance
        
        # Extract image features
        if "image_features" in multimodal_data:
            image_features = multimodal_data["image_features"]
            if isinstance(image_features, list):
                features.extend(image_features[:50])
        
        # Extract tabular features
        if "tabular_features" in multimodal_data:
            tabular_features = multimodal_data["tabular_features"]
            if isinstance(tabular_features, dict):
                features.extend(list(tabular_features.values()))
        
        return np.array([features]) if features else np.array([[0]])

    def _extract_tabular_features(self, input_data: Dict[str, Any]) -> np.ndarray:
        """Extract tabular features from input data."""
        if "features" in input_data:
            features = input_data["features"]
            if isinstance(features, dict):
                return np.array([list(features.values())])
            elif isinstance(features, list):
                return np.array([features])
        
        # Default feature extraction
        return np.array([[1, 2, 3, 4, 5]])  # Placeholder

    def _get_feature_names(self, input_data: Dict[str, Any]) -> List[str]:
        """Get feature names from input data."""
        if "feature_names" in input_data:
            return input_data["feature_names"]
        elif "features" in input_data and isinstance(input_data["features"], dict):
            return list(input_data["features"].keys())
        else:
            return [f"feature_{i}" for i in range(10)]  # Default names

    async def _generate_clinical_interpretation(
        self, 
        importance_ranking: List[Tuple[str, float]], 
        input_data: Dict[str, Any]
    ) -> str:
        """Generate clinical interpretation of feature importance."""
        interpretation = "Clinical Analysis:\n"
        
        for feature_name, importance in importance_ranking[:5]:
            clinical_meaning = await self._get_clinical_meaning(feature_name, importance)
            interpretation += f"- {feature_name}: {clinical_meaning}\n"
        
        return interpretation

    async def _get_clinical_meaning(self, feature_name: str, importance: float) -> str:
        """Get clinical meaning of a feature."""
        # Map features to clinical meanings
        clinical_mappings = {
            "age": "Patient age is a significant risk factor",
            "bmi": "Body mass index indicates metabolic health status",
            "blood_pressure": "Blood pressure levels affect cardiovascular risk",
            "glucose": "Blood glucose levels indicate diabetes risk",
            "cholesterol": "Cholesterol levels affect cardiovascular health"
        }
        
        base_meaning = clinical_mappings.get(feature_name.lower(), f"{feature_name} shows clinical significance")
        
        if importance > 0.5:
            return f"{base_meaning} (high importance: {importance:.3f})"
        elif importance > 0.2:
            return f"{base_meaning} (moderate importance: {importance:.3f})"
        else:
            return f"{base_meaning} (low importance: {importance:.3f})"

    # Additional helper methods would continue here...
    # (Many more helper methods for visualization, analysis, etc.)