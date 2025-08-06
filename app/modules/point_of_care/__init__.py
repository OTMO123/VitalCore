"""
Point-of-Care Testing (POCT) Module for Healthcare Platform V2.0

Real-time diagnostic analysis for blood test strips, rapid antigen tests, ECG monitoring,
pulse oximetry, and other point-of-care medical devices with AI-powered interpretation.
"""

from .schemas import (
    POCTDevice, POCTDeviceType, BloodTestStrip, BloodTestResults,
    RapidAntigenTest, AntigenTestResult, ECGSignal, ECGAnalysis,
    PulseOximetryReading, PulseOxAnalysis, BloodPressureReading, BPAnalysis,
    UrineAnalysis, IntegratedAnalysis, POCTWorkflow, POCTSession,
    POCTQualityControl, TestResultStatus, UrgencyLevel, QualityFlag
)
from .poct_analyzer import POCTAnalyzer
from .service import POCTService
from .router import router

__all__ = [
    # Schemas
    "POCTDevice", "POCTDeviceType", "BloodTestStrip", "BloodTestResults",
    "RapidAntigenTest", "AntigenTestResult", "ECGSignal", "ECGAnalysis",
    "PulseOximetryReading", "PulseOxAnalysis", "BloodPressureReading", "BPAnalysis",
    "UrineAnalysis", "IntegratedAnalysis", "POCTWorkflow", "POCTSession",
    "POCTQualityControl", "TestResultStatus", "UrgencyLevel", "QualityFlag",
    
    # Core components
    "POCTAnalyzer", "POCTService",
    
    # API router
    "router"
]