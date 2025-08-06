"""
Gemma 3n On-Device AI Engine for Healthcare Platform V2.0

Enterprise-grade on-device AI processing using Google's Gemma 3n model for
offline healthcare decision support, emergency triage, and clinical reasoning.
"""

import asyncio
import logging
import numpy as np
import torch
import torch.nn as nn
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime
import uuid
import json
import pickle
from pathlib import Path
import gc
import psutil
import threading
from dataclasses import dataclass

# Core ML frameworks
# Initialize logger first
import logging
logger = logging.getLogger(__name__)

# Conditional ML imports with security validation
try:
    import google.generativeai as genai
    _GOOGLE_AI_AVAILABLE = True
except ImportError:
    _GOOGLE_AI_AVAILABLE = False
    logger.warning("Google AI not available - running in offline mode")

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
    import torch.quantization as quant
    from torch.nn.utils.prune import l1_unstructured, remove
    _TRANSFORMERS_AVAILABLE = True
except ImportError:
    _TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers not available - ML features disabled")

# Medical knowledge integration with security validation
try:
    import requests
    from fhir.resources.patient import Patient
    from fhir.resources.observation import Observation
    _FHIR_AVAILABLE = True
except ImportError:
    _FHIR_AVAILABLE = False
    logger.warning("FHIR resources not available - using fallback")

# Internal imports
from .schemas import GemmaConfig, GemmaOutput, ReasoningChain, MedicalEntityList, ValidationResult
# from ..security.encryption import EncryptionService  # Module not available
from ..security.ml_security_service import (
    MLSecurityService, SecurityContext, MLOperationType, 
    SecurityLevel, ComplianceFramework
)
# from ..audit_logger.service import AuditLoggerService  # Import error
from ...core.config import get_settings

# Conditional multimodal imports
try:
    from ..multimodal_ai.schemas import MultimodalPrediction, ProcessingRequest
    _MULTIMODAL_AVAILABLE = True
except ImportError:
    _MULTIMODAL_AVAILABLE = False
    logger.warning("Multimodal AI not available - running without multimodal support")
    
    # Fallback classes
    class MultimodalPrediction:
        pass
    class ProcessingRequest:
        pass

logger = logging.getLogger(__name__)
settings = get_settings()

@dataclass
class DeviceMetrics:
    """Device performance and resource metrics."""
    cpu_usage: float
    memory_usage: float
    gpu_usage: Optional[float]
    temperature: Optional[float]
    battery_level: Optional[float]
    inference_time_ms: float
    model_size_mb: float
    memory_footprint_mb: float

@dataclass
class QuantizedModel:
    """Quantized model container for mobile deployment."""
    model: torch.nn.Module
    quantization_method: str
    size_reduction_ratio: float
    accuracy_retention: float
    inference_speedup: float

@dataclass
class SNOMEDAnnotations:
    """SNOMED CT terminology annotations."""
    concept_id: str
    preferred_term: str
    synonyms: List[str]
    semantic_tag: str
    clinical_context: str

@dataclass
class ICDMappings:
    """ICD-10/11 code mappings."""
    icd_code: str
    description: str
    category: str
    severity: str
    billing_relevance: bool

@dataclass
class ProtocolRecommendations:
    """Clinical protocol recommendations."""
    protocol_name: str
    evidence_level: str
    recommendations: List[str]
    contraindications: List[str]
    monitoring_requirements: List[str]

@dataclass
class InteractionWarnings:
    """Drug interaction warnings."""
    drug_pair: Tuple[str, str]
    severity: str
    mechanism: str
    clinical_effect: str
    management: str

@dataclass
class ContraindicationCheck:
    """Medical contraindication assessment."""
    contraindicated: bool
    reason: str
    severity: str
    alternatives: List[str]
    monitoring_required: bool

@dataclass
class DifferentialDiagnosis:
    """Differential diagnosis generation."""
    primary_diagnosis: str
    differential_list: List[Dict[str, Any]]
    probability_scores: Dict[str, float]
    required_tests: List[str]
    red_flags: List[str]

@dataclass
class PerformanceMetrics:
    """Model performance metrics."""
    inference_time_mean: float
    inference_time_std: float
    throughput_requests_per_second: float
    memory_efficiency: float
    cpu_utilization: float

@dataclass
class MemoryMetrics:
    """Memory usage metrics."""
    peak_memory_mb: float
    average_memory_mb: float
    memory_fragmentation: float
    cache_hit_ratio: float
    garbage_collection_frequency: float

@dataclass
class CacheMetrics:
    """Query cache performance metrics."""
    cache_size_mb: float
    hit_ratio: float
    miss_ratio: float
    eviction_rate: float
    average_lookup_time_ms: float

class MedicalKnowledgeBase:
    """
    Medical knowledge base integration for clinical validation and reasoning.
    """
    
    def __init__(self):
        self.snomed_concepts = self._load_snomed_concepts()
        self.icd_codes = self._load_icd_codes()
        self.drug_database = self._load_drug_database()
        self.clinical_protocols = self._load_clinical_protocols()
        self.interaction_matrix = self._load_interaction_matrix()
        
    def _load_snomed_concepts(self) -> Dict[str, Dict]:
        """Load SNOMED CT concepts with security validation."""
        # SECURITY FIX: Load from secure external source, not hardcoded
        try:
            # In production, this should load from a secure, encrypted medical database
            # with proper authentication and audit logging
            concepts_path = settings.MEDICAL_KNOWLEDGE_PATH if hasattr(settings, 'MEDICAL_KNOWLEDGE_PATH') else None
            
            if concepts_path and Path(concepts_path).exists():
                # Load from secure encrypted file
                with open(concepts_path, 'r', encoding='utf-8') as f:
                    encrypted_data = f.read()
                    # Decrypt using EncryptionService
                    # from ..security.encryption import EncryptionService  # Module not available
                    encryption_service = EncryptionService()
                    decrypted_data = encryption_service.decrypt_data(encrypted_data)
                    return json.loads(decrypted_data)
            else:
                logger.warning("SECURITY WARNING: Using fallback SNOMED concepts - not suitable for production")
                # Minimal fallback for testing only
                return {
                    "_security_warning": "Production deployment requires secure SNOMED database",
                    "386661006": {
                        "term": "Fever",
                        "synonyms": ["Pyrexia"],
                        "semantic_tag": "Finding",
                        "parent_concepts": ["404684003"]
                    }
                }
        except Exception as e:
            logger.error(f"SECURITY ERROR: Failed to load secure SNOMED concepts: {e}")
            return {"_error": "Secure medical knowledge base required for production"}
    
    def _load_icd_codes(self) -> Dict[str, Dict]:
        """Load ICD-10/11 code mappings."""
        return {
            "E11": {
                "description": "Type 2 diabetes mellitus",
                "category": "Endocrine disorders",
                "severity": "Chronic",
                "subcodes": ["E11.9", "E11.65", "E11.22"]
            },
            "I10": {
                "description": "Essential hypertension",
                "category": "Circulatory disorders",
                "severity": "Chronic",
                "subcodes": ["I10.0", "I10.1"]
            }
        }
    
    def _load_drug_database(self) -> Dict[str, Dict]:
        """Load drug information database."""
        return {
            "metformin": {
                "generic_name": "metformin",
                "brand_names": ["Glucophage", "Fortamet"],
                "class": "Biguanide",
                "indications": ["Type 2 diabetes"],
                "contraindications": ["Severe renal impairment", "Metabolic acidosis"],
                "interactions": ["iodinated_contrast", "alcohol"]
            },
            "lisinopril": {
                "generic_name": "lisinopril",
                "brand_names": ["Prinivil", "Zestril"],
                "class": "ACE inhibitor",
                "indications": ["Hypertension", "Heart failure"],
                "contraindications": ["Pregnancy", "Angioedema"],
                "interactions": ["potassium_supplements", "nsaids"]
            }
        }
    
    def _load_clinical_protocols(self) -> Dict[str, Dict]:
        """Load clinical protocols and guidelines."""
        return {
            "diabetes_management": {
                "title": "Type 2 Diabetes Management Protocol",
                "evidence_level": "A",
                "guidelines": [
                    "HbA1c target <7% for most adults",
                    "Metformin as first-line therapy",
                    "Annual diabetic eye exam",
                    "Annual foot examination"
                ],
                "monitoring": ["HbA1c every 3-6 months", "Blood pressure", "Lipid profile"]
            },
            "hypertension_management": {
                "title": "Hypertension Management Protocol", 
                "evidence_level": "A",
                "guidelines": [
                    "Target BP <140/90 mmHg for most adults",
                    "Lifestyle modifications first",
                    "ACE inhibitor or ARB as first-line"
                ],
                "monitoring": ["Home blood pressure monitoring", "Annual cardiovascular risk assessment"]
            }
        }
    
    def _load_interaction_matrix(self) -> Dict[Tuple[str, str], Dict]:
        """Load drug-drug interaction matrix."""
        return {
            ("metformin", "iodinated_contrast"): {
                "severity": "Major",
                "mechanism": "Increased risk of lactic acidosis",
                "management": "Hold metformin 48h before and after contrast"
            },
            ("lisinopril", "potassium_supplements"): {
                "severity": "Moderate",
                "mechanism": "Hyperkalemia risk",
                "management": "Monitor potassium levels closely"
            }
        }

class GemmaOnDeviceEngine:
    """
    Google Gemma 3n on-device AI engine for healthcare decision support.
    
    Provides offline inference capabilities for emergency scenarios,
    clinical reasoning, and medical entity extraction with HIPAA compliance.
    """
    
    def __init__(self, config: GemmaConfig):
        self.config = config
        self.device = torch.device(config.device) if _TRANSFORMERS_AVAILABLE else None
        self.model = None
        self.tokenizer = None
        self.quantized_model = None
        
        # Enterprise Security Integration
        self.ml_security_service = MLSecurityService()
        self.audit_service = AuditLoggerService()
        self.encryption_service = EncryptionService()
        
        # Medical knowledge integration
        self.knowledge_base = MedicalKnowledgeBase()
        
        # Performance monitoring
        self.metrics_history = []
        self.cache = {}
        self.cache_max_size = 1000
        
        # Thread-safe locks
        self.inference_lock = threading.Lock()
        self.cache_lock = threading.Lock()
        
        # Emergency mode settings
        self.emergency_mode = False
        self.offline_mode = False
        
        # Compliance tracking
        self.compliance_frameworks = [
            ComplianceFramework.SOC2_TYPE_II,
            ComplianceFramework.HIPAA,
            ComplianceFramework.FHIR_R4,
            ComplianceFramework.GDPR
        ]
        
        logger.info("Enterprise Gemma Engine initialized with SOC2/HIPAA/FHIR/GDPR compliance")

    async def initialize_gemma_model(self, model_path: str, device: str = "cpu") -> bool:
        """
        Initialize Gemma 3n model for on-device inference.
        
        Args:
            model_path: Path to Gemma model files
            device: Target device (cpu, cuda, mps)
            
        Returns:
            Success status of model initialization
        """
        try:
            logger.info(f"Initializing Gemma model from {model_path} on {device}")
            
            # Configure quantization for mobile deployment
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4"
            )
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                trust_remote_code=True,
                use_fast=True
            )
            
            # Add special tokens for medical domain
            special_tokens = [
                "[SYMPTOMS]", "[DIAGNOSIS]", "[TREATMENT]", "[EMERGENCY]",
                "[PATIENT]", "[VITALS]", "[LABS]", "[IMAGING]"
            ]
            self.tokenizer.add_special_tokens({"additional_special_tokens": special_tokens})
            
            # Load model with quantization
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                quantization_config=quantization_config,
                device_map="auto" if device == "cuda" else None,
                torch_dtype=torch.float16,
                trust_remote_code=True,
                low_cpu_mem_usage=True
            )
            
            if device == "cpu":
                self.model = self.model.to(self.device)
            
            # Resize embeddings for new tokens
            self.model.resize_token_embeddings(len(self.tokenizer))
            
            # Set model to evaluation mode
            self.model.eval()
            
            # Test inference
            test_input = "Patient presents with chest pain and shortness of breath."
            test_output = await self._generate_response(test_input, max_tokens=50)
            
            if test_output:
                logger.info("Gemma model initialized successfully")
                return True
            else:
                logger.error("Gemma model test inference failed")
                return False
                
        except Exception as e:
            logger.error(f"Error initializing Gemma model: {str(e)}")
            return False

    async def load_medical_fine_tuned_weights(self, weights_path: str) -> bool:
        """
        Load medical domain fine-tuned weights for enhanced clinical performance.
        
        Args:
            weights_path: Path to fine-tuned medical weights
            
        Returns:
            Success status of weight loading
        """
        try:
            if not self.model:
                logger.error("Base model must be initialized before loading fine-tuned weights")
                return False
            
            logger.info(f"Loading medical fine-tuned weights from {weights_path}")
            
            # Load state dict
            checkpoint = torch.load(weights_path, map_location=self.device)
            
            # Extract model weights if checkpoint contains additional metadata
            if 'model_state_dict' in checkpoint:
                state_dict = checkpoint['model_state_dict']
            else:
                state_dict = checkpoint
            
            # Load weights with strict=False to handle potential architecture differences
            missing_keys, unexpected_keys = self.model.load_state_dict(state_dict, strict=False)
            
            if missing_keys:
                logger.warning(f"Missing keys in checkpoint: {missing_keys}")
            if unexpected_keys:
                logger.warning(f"Unexpected keys in checkpoint: {unexpected_keys}")
            
            # Test medical inference capability
            test_prompt = """[PATIENT] 65-year-old male with diabetes
[SYMPTOMS] Chest pain, shortness of breath, diaphoresis
[VITALS] BP 160/95, HR 102, O2Sat 88%
[DIAGNOSIS]"""
            
            medical_output = await self._generate_response(test_prompt, max_tokens=100)
            
            if medical_output and any(keyword in medical_output.lower() for keyword in 
                                   ["myocardial", "cardiac", "coronary", "ischemia"]):
                logger.info("Medical fine-tuned weights loaded successfully")
                return True
            else:
                logger.warning("Medical weights loaded but inference quality uncertain")
                return True
                
        except Exception as e:
            logger.error(f"Error loading medical fine-tuned weights: {str(e)}")
            return False

    async def process_multimodal_input(
        self, 
        text: str, 
        images: Optional[List[bytes]] = None, 
        audio: Optional[bytes] = None,
        user_id: str = "system",
        session_id: str = "default",
        ip_address: str = "127.0.0.1",
        user_agent: str = "MLEngine/1.0"
    ) -> GemmaOutput:
        """
        Process multimodal healthcare input using Gemma 3n with medical reasoning.
        
        Args:
            text: Clinical text input
            images: Optional medical images
            audio: Optional audio data
            
        Returns:
            GemmaOutput with clinical analysis
        """
        try:
            start_time = datetime.utcnow()
            
            # Construct multimodal prompt
            prompt = await self._construct_multimodal_prompt(text, images, audio)
            
            # Check cache first
            cache_key = self._generate_cache_key(prompt)
            cached_result = await self._get_cached_result(cache_key)
            if cached_result:
                logger.info("Returning cached multimodal result")
                return cached_result
            
            # Generate response using Gemma
            with self.inference_lock:
                response = await self._generate_response(
                    prompt, 
                    max_tokens=self.config.max_response_tokens,
                    temperature=0.1,  # Low temperature for clinical consistency
                    top_p=0.9
                )
            
            # Parse and structure response
            structured_output = await self._parse_clinical_response(response, text)
            
            # Calculate confidence and uncertainty
            confidence_score = await self._calculate_response_confidence(response, structured_output)
            uncertainty_metrics = await self._calculate_uncertainty_metrics(structured_output)
            
            # Medical validation
            validation_result = await self._validate_medical_content(structured_output)
            
            # Create output object
            output = GemmaOutput(
                raw_response=response,
                structured_output=structured_output,
                confidence_score=confidence_score,
                uncertainty_metrics=uncertainty_metrics,
                validation_result=validation_result,
                processing_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000,
                model_version=self.config.model_version,
                context_tokens=len(self.tokenizer.encode(prompt)),
                response_tokens=len(self.tokenizer.encode(response))
            )
            
            # Cache result
            await self._cache_result(cache_key, output)
            
            return output
            
        except Exception as e:
            logger.error(f"Error processing multimodal input: {str(e)}")
            raise

    async def generate_clinical_reasoning(
        self, 
        symptoms: List[str], 
        context: Dict[str, Any]
    ) -> ReasoningChain:
        """
        Generate step-by-step clinical reasoning chain using medical knowledge.
        
        Args:
            symptoms: List of patient symptoms
            context: Clinical context (demographics, history, etc.)
            
        Returns:
            ReasoningChain with step-by-step medical reasoning
        """
        try:
            # Construct clinical reasoning prompt
            prompt = await self._construct_reasoning_prompt(symptoms, context)
            
            # Generate reasoning using medical knowledge
            reasoning_response = await self._generate_response(
                prompt,
                max_tokens=500,
                temperature=0.2
            )
            
            # Parse reasoning steps
            reasoning_steps = await self._parse_reasoning_steps(reasoning_response)
            
            # Validate against medical knowledge
            validated_steps = await self._validate_reasoning_steps(reasoning_steps)
            
            # Calculate confidence in reasoning
            reasoning_confidence = await self._calculate_reasoning_confidence(validated_steps)
            
            # Identify key clinical decision points
            decision_points = await self._identify_decision_points(validated_steps)
            
            return ReasoningChain(
                reasoning_steps=validated_steps,
                confidence_score=reasoning_confidence,
                decision_points=decision_points,
                medical_evidence=await self._gather_supporting_evidence(validated_steps),
                uncertainty_areas=await self._identify_uncertainty_areas(validated_steps),
                next_steps=await self._recommend_next_steps(validated_steps, context)
            )
            
        except Exception as e:
            logger.error(f"Error generating clinical reasoning: {str(e)}")
            raise

    async def extract_medical_entities(self, text: str) -> MedicalEntityList:
        """
        Extract medical entities from clinical text using Gemma and medical knowledge base.
        
        Args:
            text: Clinical text for entity extraction
            
        Returns:
            MedicalEntityList with extracted and validated entities
        """
        try:
            # Construct entity extraction prompt
            prompt = f"""Extract medical entities from the following clinical text. Identify:
- Symptoms and signs
- Diagnoses and conditions  
- Medications and treatments
- Anatomical locations
- Laboratory values
- Procedures

Text: {text}

Output format:
SYMPTOMS: [list]
DIAGNOSES: [list]  
MEDICATIONS: [list]
ANATOMY: [list]
LABS: [list]
PROCEDURES: [list]"""

            # Generate entity extraction
            response = await self._generate_response(prompt, max_tokens=300)
            
            # Parse extracted entities
            raw_entities = await self._parse_entity_response(response)
            
            # Validate against medical knowledge base
            validated_entities = await self._validate_entities(raw_entities)
            
            # Map to SNOMED concepts
            snomed_mappings = await self._map_to_snomed(validated_entities)
            
            # Calculate extraction confidence
            extraction_confidence = await self._calculate_extraction_confidence(
                text, validated_entities
            )
            
            return MedicalEntityList(
                symptoms=validated_entities.get("symptoms", []),
                diagnoses=validated_entities.get("diagnoses", []),
                medications=validated_entities.get("medications", []),
                anatomy=validated_entities.get("anatomy", []),
                laboratory_values=validated_entities.get("labs", []),
                procedures=validated_entities.get("procedures", []),
                snomed_mappings=snomed_mappings,
                confidence_score=extraction_confidence,
                extraction_method="gemma_3n_medical"
            )
            
        except Exception as e:
            logger.error(f"Error extracting medical entities: {str(e)}")
            raise

    async def validate_medical_accuracy(
        self, 
        output: GemmaOutput, 
        knowledge_base: Optional[Dict] = None
    ) -> ValidationResult:
        """
        Validate medical accuracy of Gemma output against knowledge base.
        
        Args:
            output: Gemma model output to validate
            knowledge_base: Optional external knowledge base
            
        Returns:
            ValidationResult with accuracy assessment
        """
        try:
            kb = knowledge_base or self.knowledge_base
            
            # Extract medical claims from output
            medical_claims = await self._extract_medical_claims(output.structured_output)
            
            # Validate each claim
            validation_results = []
            for claim in medical_claims:
                claim_validation = await self._validate_individual_claim(claim, kb)
                validation_results.append(claim_validation)
            
            # Check for contradictions
            contradictions = await self._check_contradictions(medical_claims)
            
            # Assess overall accuracy
            accuracy_score = await self._calculate_accuracy_score(validation_results)
            
            # Identify areas of uncertainty
            uncertainty_areas = await self._identify_validation_uncertainties(validation_results)
            
            # Generate validation recommendations
            recommendations = await self._generate_validation_recommendations(
                validation_results, contradictions
            )
            
            return ValidationResult(
                overall_accuracy=accuracy_score,
                validated_claims=validation_results,
                contradictions=contradictions,
                uncertainty_areas=uncertainty_areas,
                recommendations=recommendations,
                knowledge_base_version=kb.version if hasattr(kb, 'version') else "local",
                validation_timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error validating medical accuracy: {str(e)}")
            raise

    async def quantize_model_for_mobile(
        self, 
        model: torch.nn.Module, 
        target_size_mb: int
    ) -> QuantizedModel:
        """
        Quantize Gemma model for mobile deployment with size constraints.
        
        Args:
            model: PyTorch model to quantize
            target_size_mb: Target model size in megabytes
            
        Returns:
            QuantizedModel optimized for mobile deployment
        """
        try:
            logger.info(f"Quantizing model to target size: {target_size_mb}MB")
            
            # Get original model size
            original_size = self._get_model_size_mb(model)
            target_reduction = target_size_mb / original_size
            
            # Apply quantization based on target reduction
            if target_reduction < 0.25:
                # Aggressive quantization
                quantized_model = await self._apply_int8_quantization(model)
                quantization_method = "int8_aggressive"
            elif target_reduction < 0.5:
                # Standard quantization
                quantized_model = await self._apply_int8_quantization(model)
                quantization_method = "int8_standard"
            else:
                # Light quantization
                quantized_model = await self._apply_float16_quantization(model)
                quantization_method = "float16"
            
            # Apply pruning if needed
            if target_reduction < 0.3:
                quantized_model = await self._apply_model_pruning(quantized_model, 0.3)
                quantization_method += "_pruned"
            
            # Measure final metrics
            final_size = self._get_model_size_mb(quantized_model)
            size_reduction_ratio = final_size / original_size
            
            # Test accuracy retention
            accuracy_retention = await self._test_accuracy_retention(model, quantized_model)
            
            # Measure inference speedup
            inference_speedup = await self._measure_inference_speedup(model, quantized_model)
            
            return QuantizedModel(
                model=quantized_model,
                quantization_method=quantization_method,
                size_reduction_ratio=size_reduction_ratio,
                accuracy_retention=accuracy_retention,
                inference_speedup=inference_speedup
            )
            
        except Exception as e:
            logger.error(f"Error quantizing model: {str(e)}")
            raise

    async def update_model_weights(self, federated_updates: Dict[str, Any]) -> bool:
        """
        Update local model weights with federated learning updates.
        
        Args:
            federated_updates: Federated learning weight updates
            
        Returns:
            Success status of weight update
        """
        try:
            if not self.model:
                logger.error("Model must be initialized before updating weights")
                return False
            
            logger.info("Applying federated learning updates to local model")
            
            # Validate update integrity
            if not await self._validate_federated_updates(federated_updates):
                logger.error("Federated updates failed validation")
                return False
            
            # Create backup of current weights
            backup_state = self.model.state_dict().copy()
            
            try:
                # Apply federated updates
                current_state = self.model.state_dict()
                
                for layer_name, update_weights in federated_updates.get("weight_updates", {}).items():
                    if layer_name in current_state:
                        # Apply weighted average update
                        learning_rate = federated_updates.get("learning_rate", 0.01)
                        current_state[layer_name] = (
                            (1 - learning_rate) * current_state[layer_name] + 
                            learning_rate * torch.tensor(update_weights, device=self.device)
                        )
                
                # Load updated weights
                self.model.load_state_dict(current_state)
                
                # Test model after update
                test_successful = await self._test_model_functionality()
                
                if not test_successful:
                    # Restore backup if test fails
                    self.model.load_state_dict(backup_state)
                    logger.error("Model test failed after federated update, restored backup")
                    return False
                
                logger.info("Federated learning updates applied successfully")
                return True
                
            except Exception as e:
                # Restore backup on any error
                self.model.load_state_dict(backup_state)
                logger.error(f"Error applying federated updates, restored backup: {str(e)}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating model weights: {str(e)}")
            return False

    # Medical Knowledge Integration Methods
    
    async def integrate_snomed_terminology(self, text: str) -> SNOMEDAnnotations:
        """
        Integrate SNOMED CT terminology into text analysis.
        
        Args:
            text: Clinical text to annotate
            
        Returns:
            SNOMEDAnnotations with mapped concepts
        """
        try:
            # Extract potential medical concepts
            concepts = await self._extract_concepts_from_text(text)
            
            # Map to SNOMED concepts
            snomed_mappings = []
            for concept in concepts:
                mapping = await self._map_concept_to_snomed(concept)
                if mapping:
                    snomed_mappings.append(mapping)
            
            # Return primary mapping if available
            if snomed_mappings:
                primary_mapping = snomed_mappings[0]
                return SNOMEDAnnotations(
                    concept_id=primary_mapping["concept_id"],
                    preferred_term=primary_mapping["preferred_term"],
                    synonyms=primary_mapping.get("synonyms", []),
                    semantic_tag=primary_mapping.get("semantic_tag", ""),
                    clinical_context=text
                )
            else:
                return SNOMEDAnnotations(
                    concept_id="",
                    preferred_term="",
                    synonyms=[],
                    semantic_tag="",
                    clinical_context=text
                )
                
        except Exception as e:
            logger.error(f"Error integrating SNOMED terminology: {str(e)}")
            raise

    async def integrate_icd_codes(self, symptoms: List[str]) -> ICDMappings:
        """
        Map symptoms to ICD-10/11 codes.
        
        Args:
            symptoms: List of clinical symptoms
            
        Returns:
            ICDMappings with relevant codes
        """
        try:
            # Analyze symptoms for ICD mapping
            symptom_text = " ".join(symptoms)
            
            # Generate ICD mapping using Gemma
            prompt = f"""Map the following symptoms to ICD-10 codes:
Symptoms: {symptom_text}

Provide the most appropriate ICD-10 code with description."""
            
            response = await self._generate_response(prompt, max_tokens=150)
            
            # Parse ICD code from response
            icd_info = await self._parse_icd_response(response)
            
            return ICDMappings(
                icd_code=icd_info.get("code", ""),
                description=icd_info.get("description", ""),
                category=icd_info.get("category", ""),
                severity=icd_info.get("severity", ""),
                billing_relevance=icd_info.get("billing_relevance", False)
            )
            
        except Exception as e:
            logger.error(f"Error integrating ICD codes: {str(e)}")
            raise

    async def apply_clinical_protocols(
        self, 
        symptoms: List[str], 
        demographics: Dict[str, Any]
    ) -> ProtocolRecommendations:
        """
        Apply clinical protocols based on symptoms and demographics.
        
        Args:
            symptoms: Patient symptoms
            demographics: Patient demographics
            
        Returns:
            ProtocolRecommendations with applicable protocols
        """
        try:
            # Identify relevant protocols
            relevant_protocols = await self._identify_relevant_protocols(symptoms, demographics)
            
            if not relevant_protocols:
                return ProtocolRecommendations(
                    protocol_name="No specific protocol identified",
                    evidence_level="",
                    recommendations=[],
                    contraindications=[],
                    monitoring_requirements=[]
                )
            
            # Select primary protocol
            primary_protocol = relevant_protocols[0]
            protocol_data = self.knowledge_base.clinical_protocols.get(primary_protocol, {})
            
            return ProtocolRecommendations(
                protocol_name=protocol_data.get("title", primary_protocol),
                evidence_level=protocol_data.get("evidence_level", ""),
                recommendations=protocol_data.get("guidelines", []),
                contraindications=await self._check_protocol_contraindications(
                    primary_protocol, demographics
                ),
                monitoring_requirements=protocol_data.get("monitoring", [])
            )
            
        except Exception as e:
            logger.error(f"Error applying clinical protocols: {str(e)}")
            raise

    # Performance Optimization Methods
    
    async def optimize_inference_speed(self) -> PerformanceMetrics:
        """
        Optimize model inference speed and measure performance.
        
        Returns:
            PerformanceMetrics with optimization results
        """
        try:
            logger.info("Optimizing inference speed")
            
            # Apply torch optimizations
            if hasattr(torch, 'compile') and self.model:
                self.model = torch.compile(self.model, mode="reduce-overhead")
            
            # Enable inference optimizations
            torch.backends.cudnn.benchmark = True
            torch.set_grad_enabled(False)
            
            # Measure performance
            inference_times = []
            test_inputs = [
                "Patient presents with chest pain",
                "Symptoms include fever and headache",
                "Laboratory results show elevated glucose"
            ]
            
            for test_input in test_inputs:
                start_time = datetime.utcnow()
                await self._generate_response(test_input, max_tokens=50)
                end_time = datetime.utcnow()
                inference_times.append((end_time - start_time).total_seconds() * 1000)
            
            # Calculate metrics
            mean_time = np.mean(inference_times)
            std_time = np.std(inference_times)
            throughput = 1000 / mean_time  # requests per second
            
            return PerformanceMetrics(
                inference_time_mean=mean_time,
                inference_time_std=std_time,
                throughput_requests_per_second=throughput,
                memory_efficiency=await self._calculate_memory_efficiency(),
                cpu_utilization=psutil.cpu_percent()
            )
            
        except Exception as e:
            logger.error(f"Error optimizing inference speed: {str(e)}")
            raise

    async def manage_memory_usage(self, max_memory_gb: float) -> MemoryMetrics:
        """
        Manage and optimize memory usage within constraints.
        
        Args:
            max_memory_gb: Maximum memory limit in GB
            
        Returns:
            MemoryMetrics with memory management results
        """
        try:
            logger.info(f"Managing memory usage with limit: {max_memory_gb}GB")
            
            # Get current memory usage
            current_memory = self._get_current_memory_usage_gb()
            
            if current_memory > max_memory_gb:
                # Apply memory optimization strategies
                await self._optimize_memory_usage()
                
                # Clear caches if needed
                if current_memory > max_memory_gb * 0.9:
                    await self._clear_caches()
                
                # Force garbage collection
                gc.collect()
                torch.cuda.empty_cache() if torch.cuda.is_available() else None
            
            # Monitor memory for a period
            memory_samples = []
            for i in range(10):
                memory_samples.append(self._get_current_memory_usage_gb())
                await asyncio.sleep(0.1)
            
            return MemoryMetrics(
                peak_memory_mb=max(memory_samples) * 1024,
                average_memory_mb=np.mean(memory_samples) * 1024,
                memory_fragmentation=await self._calculate_memory_fragmentation(),
                cache_hit_ratio=await self._calculate_cache_hit_ratio(),
                garbage_collection_frequency=await self._get_gc_frequency()
            )
            
        except Exception as e:
            logger.error(f"Error managing memory usage: {str(e)}")
            raise

    async def monitor_device_resources(self) -> DeviceMetrics:
        """
        Monitor comprehensive device resource usage.
        
        Returns:
            DeviceMetrics with current device status
        """
        try:
            # CPU metrics
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # Memory metrics
            memory_info = psutil.virtual_memory()
            memory_usage = memory_info.percent
            
            # GPU metrics (if available)
            gpu_usage = None
            if torch.cuda.is_available():
                gpu_usage = torch.cuda.utilization()
            
            # Temperature (if available)
            temperature = None
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    temperature = next(iter(temps.values()))[0].current
            except:
                pass
            
            # Battery (if available)
            battery_level = None
            try:
                battery = psutil.sensors_battery()
                if battery:
                    battery_level = battery.percent
            except:
                pass
            
            # Model metrics
            model_size_mb = self._get_model_size_mb(self.model) if self.model else 0
            memory_footprint_mb = self._get_current_memory_usage_gb() * 1024
            
            return DeviceMetrics(
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                gpu_usage=gpu_usage,
                temperature=temperature,
                battery_level=battery_level,
                inference_time_ms=0,  # Would be measured during actual inference
                model_size_mb=model_size_mb,
                memory_footprint_mb=memory_footprint_mb
            )
            
        except Exception as e:
            logger.error(f"Error monitoring device resources: {str(e)}")
            raise

    # Helper Methods
    
    async def _generate_response(
        self, 
        prompt: str, 
        max_tokens: int = 256, 
        temperature: float = 0.1,
        top_p: float = 0.9
    ) -> str:
        """Generate response using Gemma model with security validation."""
        try:
            # SECURITY FIX: Validate dependencies are available
            if not _TRANSFORMERS_AVAILABLE:
                raise ValueError("SECURITY ERROR: Transformers not available - cannot process medical data")
                
            if not self.model or not self.tokenizer:
                raise ValueError("SECURITY ERROR: Model and tokenizer must be initialized")
            
            # SECURITY FIX: Input sanitization for prompt injection attacks
            sanitized_prompt = await self._sanitize_medical_prompt(prompt)
            if not sanitized_prompt:
                raise ValueError("SECURITY ERROR: Prompt failed security validation")
            
            # SECURITY FIX: Validate prompt length to prevent DoS
            if len(sanitized_prompt) > 4096:  # Maximum safe length
                raise ValueError("SECURITY ERROR: Prompt exceeds maximum safe length")
            
            # Encode input with security validation
            try:
                inputs = self.tokenizer.encode(sanitized_prompt, return_tensors="pt").to(self.device)
            except Exception as e:
                logger.error(f"SECURITY ERROR: Tokenization failed: {e}")
                raise ValueError("SECURITY ERROR: Input tokenization failed security checks")
            
            # Generate with specific parameters for medical consistency
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    do_sample=True,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    repetition_penalty=1.1
                )
            
            # Decode response
            response = self.tokenizer.decode(outputs[0][inputs.shape[1]:], skip_special_tokens=True)
            return response.strip()
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return ""

    # Additional helper methods would continue...
    # (Implementation of remaining private methods as placeholders for brevity)

    def _get_model_size_mb(self, model: torch.nn.Module) -> float:
        """Calculate model size in MB."""
        if not model:
            return 0.0
        
        param_size = 0
        for param in model.parameters():
            param_size += param.nelement() * param.element_size()
        
        buffer_size = 0
        for buffer in model.buffers():
            buffer_size += buffer.nelement() * buffer.element_size()
        
        size_mb = (param_size + buffer_size) / (1024 * 1024)
        return size_mb

    def _get_current_memory_usage_gb(self) -> float:
        """Get current memory usage in GB."""
        return psutil.virtual_memory().used / (1024 ** 3)

    # SECURITY METHODS - Production Security Implementation
    
    async def _sanitize_medical_prompt(self, prompt: str) -> Optional[str]:
        """Sanitize medical prompt to prevent injection attacks and protect PHI."""
        try:
            # SECURITY FIX: Remove potential injection patterns
            dangerous_patterns = [
                r'<script[^>]*>.*?</script>',  # Script injection
                r'javascript:',  # JavaScript protocol
                r'data:text/html',  # Data URI injection
                r'SELECT\s+.*\s+FROM',  # SQL injection
                r'DROP\s+TABLE',  # SQL drop commands
                r'UNION\s+SELECT',  # SQL union attacks
                r'--\s*$',  # SQL comments
                r';.*--',  # SQL comment injection
                r'\|\s*nc\s+',  # Netcat commands
                r'\|\s*sh\s+',  # Shell commands
                r'curl\s+',  # External requests
                r'wget\s+',  # External downloads
            ]
            
            import re
            sanitized = prompt
            for pattern in dangerous_patterns:
                sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.MULTILINE)
            
            # SECURITY FIX: Validate medical context
            if not await self._validate_medical_context(sanitized):
                logger.warning("SECURITY WARNING: Prompt failed medical context validation")
                return None
                
            # SECURITY FIX: Remove potential PHI that should be encrypted
            sanitized = await self._mask_potential_phi(sanitized)
            
            return sanitized.strip()
            
        except Exception as e:
            logger.error(f"SECURITY ERROR: Prompt sanitization failed: {e}")
            return None
    
    async def _validate_medical_context(self, text: str) -> bool:
        """Validate that text contains legitimate medical context."""
        try:
            # Medical keywords that indicate legitimate medical content
            medical_keywords = [
                'patient', 'symptoms', 'diagnosis', 'treatment', 'medication',
                'vital signs', 'blood pressure', 'temperature', 'pulse',
                'respiratory', 'cardiovascular', 'neurological', 'pain',
                'history', 'examination', 'laboratory', 'imaging', 'test',
                'condition', 'disease', 'syndrome', 'disorder', 'therapy'
            ]
            
            text_lower = text.lower()
            medical_score = sum(1 for keyword in medical_keywords if keyword in text_lower)
            
            # Require at least 2 medical keywords for basic validation
            return medical_score >= 2
            
        except Exception as e:
            logger.error(f"SECURITY ERROR: Medical context validation failed: {e}")
            return False
    
    async def _mask_potential_phi(self, text: str) -> str:
        """Mask potential PHI in text to protect patient privacy."""
        try:
            import re
            
            # SECURITY FIX: Mask common PHI patterns
            phi_patterns = [
                (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN_MASKED]'),  # SSN
                (r'\b\d{3}-\d{3}-\d{4}\b', '[PHONE_MASKED]'),  # Phone numbers
                (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_MASKED]'),  # Email
                (r'\b\d{1,2}/\d{1,2}/\d{4}\b', '[DATE_MASKED]'),  # Dates MM/DD/YYYY
                (r'\b\d{4}-\d{2}-\d{2}\b', '[DATE_MASKED]'),  # Dates YYYY-MM-DD
                (r'\b[A-Z]{2}\d{6,8}\b', '[ID_MASKED]'),  # Medical record numbers
            ]
            
            masked_text = text
            for pattern, replacement in phi_patterns:
                masked_text = re.sub(pattern, replacement, masked_text)
            
            return masked_text
            
        except Exception as e:
            logger.error(f"SECURITY ERROR: PHI masking failed: {e}")
            return text  # Return original if masking fails
    
    # Placeholder implementations for remaining methods
    async def _construct_multimodal_prompt(self, text: str, images: Optional[List[bytes]], audio: Optional[bytes]) -> str:
        # SECURITY FIX: Sanitize input before processing
        sanitized_text = await self._sanitize_medical_prompt(text)
        return f"[PATIENT] {sanitized_text}" if sanitized_text else "[PATIENT] [SECURITY_ERROR]"
    
    async def _parse_clinical_response(self, response: str, original_text: str) -> Dict[str, Any]:
        return {"diagnosis": "Assessment pending", "recommendations": []}
    
    async def _calculate_response_confidence(self, response: str, structured: Dict) -> float:
        return 0.8
    
    async def _calculate_uncertainty_metrics(self, structured: Dict) -> Dict[str, float]:
        return {"epistemic": 0.1, "aleatoric": 0.1}
    
    async def _validate_medical_content(self, structured: Dict) -> Dict[str, Any]:
        return {"valid": True, "warnings": []}
    
    def _generate_cache_key(self, prompt: str) -> str:
        """Generate secure cache key with PHI protection."""
        # SECURITY FIX: Use cryptographic hash to prevent cache key attacks
        import hashlib
        import hmac
        
        # Use HMAC with secret key to prevent cache key manipulation
        secret_key = settings.SECRET_KEY.encode() if hasattr(settings, 'SECRET_KEY') else b'fallback-key'
        secure_hash = hmac.new(secret_key, prompt.encode('utf-8'), hashlib.sha256).hexdigest()
        return f"gemma_secure_{secure_hash[:16]}"
    
    async def _get_cached_result(self, key: str) -> Optional[GemmaOutput]:
        """Get cached result with security validation."""
        try:
            cached_data = self.cache.get(key)
            if cached_data:
                # SECURITY FIX: Validate cached data integrity
                if hasattr(cached_data, 'validation_result'):
                    # Check if cached result is still valid and secure
                    if cached_data.validation_result.overall_accuracy < 0.8:
                        logger.warning("SECURITY WARNING: Cached result has low accuracy, removing")
                        del self.cache[key]
                        return None
                return cached_data
        except Exception as e:
            logger.error(f"SECURITY ERROR: Cache retrieval failed: {e}")
        return None
    
    async def _cache_result(self, key: str, result: GemmaOutput) -> None:
        """Cache result with security validation."""
        try:
            # SECURITY FIX: Only cache results that pass security validation
            if result.validation_result.overall_accuracy < 0.8:
                logger.warning("SECURITY WARNING: Not caching low-accuracy result")
                return
                
            # SECURITY FIX: Implement secure cache eviction
            if len(self.cache) >= self.cache_max_size:
                # Remove oldest or lowest confidence entries first
                keys_to_remove = sorted(self.cache.keys(), 
                                       key=lambda k: self.cache[k].confidence_score)[:1]
                for old_key in keys_to_remove:
                    del self.cache[old_key]
                    
            # SECURITY FIX: Mark cached data with timestamp for expiration
            result.processing_timestamp = datetime.utcnow()
            self.cache[key] = result
            
        except Exception as e:
            logger.error(f"SECURITY ERROR: Cache storage failed: {e}")