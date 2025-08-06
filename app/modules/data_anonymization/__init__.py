"""
Data Anonymization Module for Predictive Healthcare Platform

This module provides ML-ready anonymization capabilities that extend our existing
healthcare records anonymization engine for predictive analytics while maintaining
SOC2, HIPAA, FHIR, and GDPR compliance.

Key Components:
- MLAnonymizationEngine: Creates ML-ready anonymized patient profiles
- ClinicalFeatureExtractor: Extracts medically meaningful categories
- PseudonymGenerator: Generates consistent anonymous identifiers
- VectorFeaturePreparator: Prepares data for Clinical BERT embeddings
- ComplianceValidator: Ensures anonymization meets all regulatory requirements
"""

from .ml_anonymizer import MLAnonymizationEngine
from .clinical_features import ClinicalFeatureExtractor  
from .pseudonym_generator import PseudonymGenerator
from .vector_features import VectorFeaturePreparator
from .compliance_validator import ComplianceValidator
from .schemas import AnonymizedMLProfile, AnonymizationAuditTrail

__all__ = [
    "MLAnonymizationEngine",
    "ClinicalFeatureExtractor",
    "PseudonymGenerator", 
    "VectorFeaturePreparator",
    "ComplianceValidator",
    "AnonymizedMLProfile",
    "AnonymizationAuditTrail"
]