"""
ML Prediction Module for Healthcare Platform

Provides Clinical BERT embeddings, disease prediction algorithms,
and ML-ready healthcare analytics with full HIPAA compliance.
"""

try:
    from .clinical_bert import ClinicalBERTService
    __all__ = ["ClinicalBERTService"]
except ImportError as e:
    # ML dependencies not installed, create placeholder
    class ClinicalBERTService:
        def __init__(self):
            raise ImportError(f"ML dependencies not installed: {e}")
    
    __all__ = ["ClinicalBERTService"]