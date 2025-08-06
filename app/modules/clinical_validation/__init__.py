"""
Clinical Validation Framework for Healthcare Platform V2.0

This module provides comprehensive clinical validation capabilities for AI/ML systems
in healthcare applications, including:

- Validation study design and management
- Statistical analysis and hypothesis testing  
- Evidence synthesis and meta-analysis
- Regulatory compliance assessment
- Performance metrics calculation
- Validation report generation

The framework supports SOC2 Type II and HIPAA compliance with comprehensive
audit logging and security controls.
"""

# Handle optional clinical validation dependencies
try:
    from .schemas import (
        ValidationStudyCreate,
        ValidationStudyUpdate,
        ValidationStudyResponse,
        ValidationProtocolCreate,
        ValidationProtocolUpdate,
        ValidationProtocolResponse,
        ValidationEvidenceCreate,
        ValidationEvidenceUpdate,
        ValidationEvidenceResponse,
        ValidationReportResponse,
        ClinicalMetricsResponse,
        ValidationDashboardResponse
    )
    SCHEMAS_AVAILABLE = True
except ImportError:
    SCHEMAS_AVAILABLE = False

try:
    from .service import ClinicalValidationService
    SERVICE_AVAILABLE = True
except ImportError:
    SERVICE_AVAILABLE = False

try:
    from .validation_engine import ClinicalValidationEngine
    ENGINE_AVAILABLE = True
except ImportError:
    ENGINE_AVAILABLE = False

# Create placeholder classes for missing models
class ValidationStudy:
    def __init__(self, *args, **kwargs):
        raise ImportError("Clinical validation models not available")

class ValidationProtocol:
    def __init__(self, *args, **kwargs):
        raise ImportError("Clinical validation models not available")

class ValidationEvidence:
    def __init__(self, *args, **kwargs):
        raise ImportError("Clinical validation models not available")

class ValidationReport:
    def __init__(self, *args, **kwargs):
        raise ImportError("Clinical validation models not available")

class ClinicalMetrics:
    def __init__(self, *args, **kwargs):
        raise ImportError("Clinical validation models not available")

class ValidationDashboard:
    def __init__(self, *args, **kwargs):
        raise ImportError("Clinical validation models not available")

# Define proper enum placeholders instead of string placeholders
from enum import Enum

class ValidationStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class EvidenceLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"

class RegulatoryStandard(str, Enum):
    FDA_510K = "fda_510k"
    FDA_PMA = "fda_pma"
    CE_MARK = "ce_mark"
    ISO_13485 = "iso_13485"

class ValidationLevel(str, Enum):
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    COMPREHENSIVE = "comprehensive"
    REGULATORY = "regulatory"

class ClinicalDomain(str, Enum):
    CARDIOLOGY = "cardiology"
    RADIOLOGY = "radiology"
    PATHOLOGY = "pathology"
    EMERGENCY = "emergency"
    GENERAL = "general"

# Create placeholder services if not available
if not SERVICE_AVAILABLE:
    class ClinicalValidationService:
        def __init__(self, *args, **kwargs):
            raise ImportError("Clinical validation service not available")

if not ENGINE_AVAILABLE:
    class ClinicalValidationEngine:
        def __init__(self, *args, **kwargs):
            raise ImportError("Clinical validation engine not available")

__all__ = [
    # Models
    "ValidationStudy",
    "ValidationProtocol",
    "ValidationEvidence", 
    "ValidationReport",
    "ClinicalMetrics",
    "ValidationDashboard",
    "ValidationStatus",
    "EvidenceLevel",
    "RegulatoryStandard",
    "ValidationLevel",
    "ClinicalDomain",
    
    # Schemas
    "ValidationStudyCreate",
    "ValidationStudyUpdate", 
    "ValidationStudyResponse",
    "ValidationProtocolCreate",
    "ValidationProtocolUpdate",
    "ValidationProtocolResponse",
    "ValidationEvidenceCreate",
    "ValidationEvidenceUpdate",
    "ValidationEvidenceResponse",
    "ValidationReportResponse",
    "ClinicalMetricsResponse",
    "ValidationDashboardResponse",
    
    # Services
    "ClinicalValidationService",
    "ClinicalValidationEngine"
]

__version__ = "1.0.0"
__author__ = "Healthcare Platform Development Team"
__description__ = "Clinical Validation Framework for AI/ML Healthcare Systems"