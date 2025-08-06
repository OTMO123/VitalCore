"""
Edge AI Module for Healthcare Platform V2.0

On-device AI processing with Gemma 3N, Whisper voice-to-text,
and medical NER for privacy-first healthcare applications.
"""

from .schemas import (
    GemmaConfig, GemmaOutput, ReasoningChain, MedicalEntityList,
    ValidationResult, EmergencyAssessment, DeviceType, ProcessingMode,
    MedicalSpecialty, UrgencyLevel
)

try:
    from .gemma_engine import GemmaOnDeviceEngine
    _GEMMA_ENGINE_AVAILABLE = True
except ImportError:
    _GEMMA_ENGINE_AVAILABLE = False

__all__ = [
    "GemmaConfig",
    "GemmaOutput", 
    "ReasoningChain",
    "MedicalEntityList",
    "ValidationResult",
    "EmergencyAssessment",
    "DeviceType",
    "ProcessingMode",
    "MedicalSpecialty",
    "UrgencyLevel"
]

if _GEMMA_ENGINE_AVAILABLE:
    __all__.append("GemmaOnDeviceEngine")