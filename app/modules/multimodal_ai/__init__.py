"""
Multimodal AI Module for Healthcare Platform V2.0

Provides advanced multimodal data fusion capabilities for healthcare AI with
support for clinical text, medical imaging, audio processing, lab data, and genomic data.
"""

from .fusion_engine import MultimodalFusionEngine, FusionConfig
from .schemas import (
    ClinicalTextEmbedding, ImageEmbedding, AudioEmbedding, LabEmbedding, 
    OmicsEmbedding, FusedEmbedding, MultimodalPrediction
)

__all__ = [
    "MultimodalFusionEngine", 
    "FusionConfig",
    "ClinicalTextEmbedding",
    "ImageEmbedding", 
    "AudioEmbedding",
    "LabEmbedding",
    "OmicsEmbedding",
    "FusedEmbedding",
    "MultimodalPrediction"
]