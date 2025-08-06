"""
Offline-Capable AI Model Management System for Healthcare Platform

Supports dynamic loading, switching, and management of AI models (Gemma 3N, Llama, Whisper, etc.)
with built-in anonymization and cross-platform deployment for mobile/desktop offline use.

Features:
- Offline model deployment and inference
- Cross-platform compatibility (ONNX, TensorFlow Lite)
- Built-in anonymization pipeline
- Model hot-swapping without downtime
- Mobile/desktop optimization
- Compliance with SOC2, HIPAA, FHIR R4
"""

from .model_registry import OfflineModelRegistry, ModelMetadata
from .model_loader import UniversalModelLoader, ModelAdapter
from .inference_engine import OfflineInferenceEngine
from .anonymization import BuiltInAnonymization
from .cross_platform import CrossPlatformConverter
from .mobile_optimizer import MobileModelOptimizer

__all__ = [
    "OfflineModelRegistry",
    "ModelMetadata", 
    "UniversalModelLoader",
    "ModelAdapter",
    "OfflineInferenceEngine",
    "BuiltInAnonymization",
    "CrossPlatformConverter",
    "MobileModelOptimizer"
]