"""
Point-of-Care Testing Analyzer for Healthcare Platform V2.0

Enterprise-grade POCT analyzer providing real-time diagnostic data processing,
ML-enhanced interpretation, and automated quality control for point-of-care testing.
"""

import asyncio
import logging
import uuid
import numpy as np
import cv2
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import base64

# Machine learning frameworks
import torch
import torch.nn as nn
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
import lightgbm as lgb
import xgboost as xgb

# Image processing
from PIL import Image
import matplotlib.pyplot as plt
import seaborn as sns

# Signal processing
from scipy import signal, stats
from scipy.fft import fft, fftfreq
import pandas as pd

# Internal imports
from .schemas import (
    POCTConfig, BloodTestResults, UrineAnalysis, AntigenTestResult,
    GlucoseAnalysis, ECGAnalysis, PulseOxAnalysis, BPAnalysis,
    IntegratedAnalysis, MLInterpretation, AnomalyDetection,
    FollowUpRecommendations, DiagnosticConfidence, TrendAnalysis,
    QualityControlReport
)
from ..multimodal_ai.schemas import MultimodalPrediction
from ..security.encryption import EncryptionService
from ..audit_logger.service import AuditLogService
from ...core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class POCTDeviceType(str, Enum):
    """Types of POCT devices."""
    BLOOD_GLUCOSE_METER = "blood_glucose_meter"
    PULSE_OXIMETER = "pulse_oximeter"
    BLOOD_PRESSURE_MONITOR = "blood_pressure_monitor"
    ECG_MONITOR = "ecg_monitor"
    RAPID_ANTIGEN_TEST = "rapid_antigen_test"
    URINE_ANALYZER = "urine_analyzer"
    BLOOD_TEST_STRIPS = "blood_test_strips"
    COAGULATION_MONITOR = "coagulation_monitor"
    PREGNANCY_TEST = "pregnancy_test"
    THERMOMETER = "thermometer"

class TestStatus(str, Enum):
    """Status of POCT test."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    INVALID = "invalid"
    REQUIRES_REPEAT = "requires_repeat"

class QualityLevel(str, Enum):
    """Quality levels for POCT results."""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    INVALID = "invalid"

@dataclass
class POCTConfig:
    """Configuration for POCT analyzer."""
    
    # Device settings
    supported_devices: List[POCTDeviceType] = None
    auto_device_detection: bool = True
    device_calibration_required: bool = True
    
    # Quality control
    enable_quality_control: bool = True
    quality_threshold: float = 0.8
    auto_repeat_on_poor_quality: bool = True
    
    # ML interpretation
    enable_ml_interpretation: bool = True
    ml_confidence_threshold: float = 0.7
    enable_anomaly_detection: bool = True
    
    # Clinical integration
    integrate_with_ehr: bool = True
    auto_generate_alerts: bool = True
    critical_value_notification: bool = True
    
    # Data processing
    real_time_processing: bool = True
    batch_processing_enabled: bool = True
    data_retention_days: int = 365
    
    def __post_init__(self):
        if self.supported_devices is None:
            self.supported_devices = list(POCTDeviceType)

class POCTAnalyzer:
    """
    Enterprise POCT analyzer for real-time diagnostic data processing.
    
    Provides comprehensive analysis of point-of-care testing results with
    ML-enhanced interpretation, quality control, and clinical decision support.
    """
    
    def __init__(self, config: POCTConfig):
        self.config = config
        self.logger = logger.bind(component="POCTAnalyzer")
        
        # Initialize ML models
        self.ml_models = {}
        self.scalers = {}
        self._initialize_ml_models()
        
        # Initialize services
        self.encryption_service = EncryptionService()
        self.audit_service = AuditLogService()
        
        # Reference ranges and normal values
        self.reference_ranges = self._load_reference_ranges()
        self.critical_values = self._load_critical_values()
        
        # Quality control parameters
        self.quality_metrics = {}
        self.device_calibrations = {}
        
        # Analysis cache
        self.analysis_cache: Dict[str, Any] = {}
        
        self.logger.info("POCTAnalyzer initialized successfully")

    def _initialize_ml_models(self):
        """Initialize ML models for POCT interpretation."""
        try:
            # Glucose prediction model
            self.ml_models["glucose"] = GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=3,
                random_state=42
            )
            
            # Blood pressure risk model
            self.ml_models["blood_pressure"] = RandomForestRegressor(
                n_estimators=100,
                max_depth=5,
                random_state=42
            )
            
            # ECG anomaly detection model
            self.ml_models["ecg"] = lgb.LGBMClassifier(
                n_estimators=100,
                learning_rate=0.1,
                num_leaves=31,
                random_state=42
            )
            
            # Urine analysis model
            self.ml_models["urine"] = xgb.XGBClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=3,
                random_state=42
            )
            
            # Initialize scalers
            for model_name in self.ml_models.keys():
                self.scalers[model_name] = StandardScaler()
            
            self.logger.info("ML models initialized for POCT interpretation")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize ML models: {str(e)}")
            raise

    def _load_reference_ranges(self) -> Dict[str, Dict[str, Tuple[float, float]]]:
        """Load reference ranges for laboratory values."""
        return {
            "glucose": {
                "fasting": (70.0, 100.0),  # mg/dL
                "random": (70.0, 140.0),
                "postprandial": (70.0, 140.0)
            },
            "blood_pressure": {
                "systolic": (90.0, 120.0),  # mmHg
                "diastolic": (60.0, 80.0)
            },
            "pulse_oximetry": {
                "spo2": (95.0, 100.0),  # %
                "pulse_rate": (60.0, 100.0)  # bpm
            },
            "urine": {
                "protein": (0.0, 30.0),  # mg/dL
                "glucose": (0.0, 15.0),
                "ketones": (0.0, 5.0),
                "specific_gravity": (1.003, 1.030)
            }
        }

    def _load_critical_values(self) -> Dict[str, Dict[str, Union[float, Tuple[float, float]]]]:
        """Load critical values requiring immediate attention."""
        return {
            "glucose": {
                "severe_hypoglycemia": 40.0,
                "severe_hyperglycemia": 400.0
            },
            "blood_pressure": {
                "hypertensive_crisis": (180.0, 120.0),  # (systolic, diastolic)
                "severe_hypotension": (90.0, 60.0)
            },
            "pulse_oximetry": {
                "critical_hypoxemia": 88.0,
                "critical_bradycardia": 50.0,
                "critical_tachycardia": 150.0
            }
        }

    async def process_blood_test_strips(
        self, 
        image: bytes, 
        test_type: str
    ) -> BloodTestResults:
        """
        Process blood test strips using image analysis.
        
        Args:
            image: Image of blood test strip
            test_type: Type of blood test
            
        Returns:
            BloodTestResults with analyzed values
        """
        try:
            test_id = str(uuid.uuid4())
            
            # Decode and process image
            processed_image = await self._process_test_strip_image(image)
            
            # Extract color regions for analysis
            color_regions = await self._extract_color_regions(processed_image, test_type)
            
            # Analyze color intensity and match to reference
            color_analysis = await self._analyze_color_intensity(color_regions, test_type)
            
            # Convert color analysis to quantitative values
            quantitative_results = await self._convert_to_quantitative_values(
                color_analysis, test_type
            )
            
            # Apply ML interpretation
            ml_interpretation = None
            if self.config.enable_ml_interpretation:
                ml_interpretation = await self._apply_ml_interpretation_blood_test(
                    quantitative_results, test_type
                )
            
            # Quality assessment
            quality_assessment = await self._assess_strip_quality(processed_image, color_regions)
            
            # Check for critical values
            critical_alerts = await self._check_critical_values(quantitative_results, test_type)
            
            # Generate clinical interpretation
            clinical_interpretation = await self._generate_clinical_interpretation_blood_test(
                quantitative_results, test_type, ml_interpretation
            )
            
            blood_test_results = BloodTestResults(
                test_id=test_id,
                test_type=test_type,
                quantitative_results=quantitative_results,
                color_analysis=color_analysis,
                reference_ranges=self.reference_ranges.get(test_type, {}),
                abnormal_flags=await self._identify_abnormal_flags(quantitative_results, test_type),
                critical_alerts=critical_alerts,
                quality_assessment=quality_assessment,
                ml_interpretation=ml_interpretation,
                clinical_interpretation=clinical_interpretation,
                confidence_score=quality_assessment.get("overall_confidence", 0.8),
                requires_confirmation=quality_assessment.get("quality_level") == QualityLevel.POOR.value
            )
            
            # Audit test processing
            await self._audit_poct_test(test_id, test_type, "blood_test_strips", blood_test_results)
            
            self.logger.info(
                "Blood test strip processed",
                test_id=test_id,
                test_type=test_type,
                quality_level=quality_assessment.get("quality_level"),
                critical_alerts=len(critical_alerts)
            )
            
            return blood_test_results
            
        except Exception as e:
            self.logger.error(
                "Failed to process blood test strips",
                test_type=test_type,
                error=str(e)
            )
            raise

    async def analyze_urine_test_results(self, spectral_data: Dict[str, Any]) -> UrineAnalysis:
        """
        Analyze urine test results using spectral analysis.
        
        Args:
            spectral_data: Spectral analysis data from urine analyzer
            
        Returns:
            UrineAnalysis with comprehensive results
        """
        try:
            analysis_id = str(uuid.uuid4())
            
            # Extract spectral features
            spectral_features = await self._extract_spectral_features(spectral_data)
            
            # Analyze individual urine components
            urine_components = await self._analyze_urine_components(spectral_features)
            
            # Apply ML model for urine analysis
            ml_predictions = None
            if self.config.enable_ml_interpretation and "urine" in self.ml_models:
                ml_predictions = await self._apply_ml_urine_analysis(spectral_features)
            
            # Check for abnormal findings
            abnormal_findings = await self._identify_urine_abnormalities(urine_components)
            
            # Generate microscopic analysis (if available)
            microscopic_analysis = await self._analyze_urine_microscopy(
                spectral_data.get("microscopy_data", {})
            )
            
            # Clinical correlation
            clinical_correlation = await self._correlate_urine_findings(
                urine_components, abnormal_findings, microscopic_analysis
            )
            
            # Quality control
            quality_metrics = await self._assess_urine_test_quality(spectral_data, urine_components)
            
            urine_analysis = UrineAnalysis(
                analysis_id=analysis_id,
                urine_components=urine_components,
                spectral_features=spectral_features,
                abnormal_findings=abnormal_findings,
                microscopic_analysis=microscopic_analysis,
                ml_predictions=ml_predictions,
                clinical_correlation=clinical_correlation,
                quality_metrics=quality_metrics,
                reference_ranges=self.reference_ranges.get("urine", {}),
                diagnostic_significance=await self._assess_diagnostic_significance_urine(abnormal_findings),
                follow_up_recommendations=await self._generate_urine_follow_up_recommendations(
                    abnormal_findings, clinical_correlation
                )
            )
            
            self.logger.info(
                "Urine analysis completed",
                analysis_id=analysis_id,
                abnormal_findings_count=len(abnormal_findings),
                quality_score=quality_metrics.get("overall_quality", 0)
            )
            
            return urine_analysis
            
        except Exception as e:
            self.logger.error(
                "Failed to analyze urine test results",
                error=str(e)
            )
            raise

    async def process_rapid_antigen_tests(self, image: bytes) -> AntigenTestResult:
        """
        Process rapid antigen test results using computer vision.
        
        Args:
            image: Image of rapid antigen test
            
        Returns:
            AntigenTestResult with test interpretation
        """
        try:
            test_id = str(uuid.uuid4())
            
            # Process test image
            processed_image = await self._process_antigen_test_image(image)
            
            # Detect test lines
            line_detection = await self._detect_test_lines(processed_image)
            
            # Analyze line intensity
            line_intensity = await self._analyze_line_intensity(line_detection)
            
            # Determine test result
            test_result = await self._interpret_antigen_test(line_intensity)
            
            # Calculate confidence
            result_confidence = await self._calculate_antigen_test_confidence(
                line_intensity, line_detection
            )
            
            # Quality assessment
            image_quality = await self._assess_antigen_test_image_quality(processed_image)
            
            # Generate interpretation
            clinical_interpretation = await self._generate_antigen_test_interpretation(
                test_result, result_confidence, image_quality
            )
            
            antigen_test_result = AntigenTestResult(
                test_id=test_id,
                test_result=test_result,
                line_detection=line_detection,
                line_intensity=line_intensity,
                result_confidence=result_confidence,
                image_quality=image_quality,
                clinical_interpretation=clinical_interpretation,
                requires_confirmation=result_confidence < self.config.ml_confidence_threshold or 
                                   image_quality.get("quality_score", 0) < self.config.quality_threshold,
                test_validity=await self._validate_antigen_test(line_detection, image_quality)
            )
            
            self.logger.info(
                "Rapid antigen test processed",
                test_id=test_id,
                test_result=test_result,
                confidence=result_confidence,
                requires_confirmation=antigen_test_result.requires_confirmation
            )
            
            return antigen_test_result
            
        except Exception as e:
            self.logger.error(
                "Failed to process rapid antigen test",
                error=str(e)
            )
            raise

    async def analyze_glucose_meter_data(
        self, 
        glucose_reading: float, 
        context: Dict[str, Any]
    ) -> GlucoseAnalysis:
        """
        Analyze glucose meter data with clinical context.
        
        Args:
            glucose_reading: Blood glucose reading in mg/dL
            context: Clinical context (timing, patient info, etc.)
            
        Returns:
            GlucoseAnalysis with comprehensive assessment
        """
        try:
            analysis_id = str(uuid.uuid4())
            
            # Validate glucose reading
            reading_validity = await self._validate_glucose_reading(glucose_reading)
            
            # Determine measurement context
            measurement_context = await self._determine_glucose_context(context)
            
            # Apply appropriate reference ranges
            applicable_ranges = await self._get_glucose_reference_ranges(measurement_context)
            
            # Assess glucose level
            glucose_assessment = await self._assess_glucose_level(
                glucose_reading, applicable_ranges, measurement_context
            )
            
            # Apply ML prediction for diabetes risk
            diabetes_risk = None
            if self.config.enable_ml_interpretation and "glucose" in self.ml_models:
                diabetes_risk = await self._predict_diabetes_risk(glucose_reading, context)
            
            # Check for critical values
            critical_assessment = await self._assess_glucose_criticality(glucose_reading)
            
            # Generate trend analysis (if historical data available)
            trend_analysis = await self._analyze_glucose_trends(
                glucose_reading, context.get("historical_readings", [])
            )
            
            # Clinical recommendations
            clinical_recommendations = await self._generate_glucose_recommendations(
                glucose_assessment, critical_assessment, trend_analysis, context
            )
            
            glucose_analysis = GlucoseAnalysis(
                analysis_id=analysis_id,
                glucose_reading=glucose_reading,
                measurement_context=measurement_context,
                glucose_assessment=glucose_assessment,
                applicable_ranges=applicable_ranges,
                diabetes_risk=diabetes_risk,
                critical_assessment=critical_assessment,
                trend_analysis=trend_analysis,
                clinical_recommendations=clinical_recommendations,
                reading_validity=reading_validity,
                requires_immediate_action=critical_assessment.get("requires_immediate_action", False),
                follow_up_timing=await self._determine_glucose_follow_up_timing(
                    glucose_assessment, critical_assessment
                )
            )
            
            self.logger.info(
                "Glucose analysis completed",
                analysis_id=analysis_id,
                glucose_reading=glucose_reading,
                assessment_level=glucose_assessment.get("level", "normal"),
                requires_immediate_action=glucose_analysis.requires_immediate_action
            )
            
            return glucose_analysis
            
        except Exception as e:
            self.logger.error(
                "Failed to analyze glucose meter data",
                glucose_reading=glucose_reading,
                error=str(e)
            )
            raise

    async def process_ecg_data(
        self, 
        ecg_signal: List[float], 
        sampling_rate: int
    ) -> ECGAnalysis:
        """
        Process ECG data with advanced signal analysis.
        
        Args:
            ecg_signal: ECG signal data
            sampling_rate: Sampling rate in Hz
            
        Returns:
            ECGAnalysis with comprehensive cardiac assessment
        """
        try:
            analysis_id = str(uuid.uuid4())
            
            # Preprocess ECG signal
            preprocessed_signal = await self._preprocess_ecg_signal(ecg_signal, sampling_rate)
            
            # Extract ECG features
            ecg_features = await self._extract_ecg_features(preprocessed_signal, sampling_rate)
            
            # Detect R-peaks
            r_peaks = await self._detect_r_peaks(preprocessed_signal, sampling_rate)
            
            # Calculate heart rate and HRV
            heart_rate_analysis = await self._analyze_heart_rate(r_peaks, sampling_rate)
            
            # Detect arrhythmias
            arrhythmia_detection = await self._detect_arrhythmias(
                preprocessed_signal, r_peaks, sampling_rate
            )
            
            # Apply ML model for ECG interpretation
            ml_interpretation = None
            if self.config.enable_ml_interpretation and "ecg" in self.ml_models:
                ml_interpretation = await self._apply_ml_ecg_analysis(ecg_features)
            
            # Generate clinical interpretation
            clinical_interpretation = await self._generate_ecg_clinical_interpretation(
                ecg_features, heart_rate_analysis, arrhythmia_detection, ml_interpretation
            )
            
            # Quality assessment
            signal_quality = await self._assess_ecg_signal_quality(preprocessed_signal, r_peaks)
            
            # Risk stratification
            cardiac_risk = await self._assess_cardiac_risk(
                heart_rate_analysis, arrhythmia_detection, ecg_features
            )
            
            ecg_analysis = ECGAnalysis(
                analysis_id=analysis_id,
                ecg_features=ecg_features,
                heart_rate_analysis=heart_rate_analysis,
                arrhythmia_detection=arrhythmia_detection,
                ml_interpretation=ml_interpretation,
                clinical_interpretation=clinical_interpretation,
                signal_quality=signal_quality,
                cardiac_risk=cardiac_risk,
                r_peak_positions=r_peaks.tolist() if isinstance(r_peaks, np.ndarray) else r_peaks,
                signal_duration_seconds=len(ecg_signal) / sampling_rate,
                recommendations=await self._generate_ecg_recommendations(
                    arrhythmia_detection, cardiac_risk, signal_quality
                )
            )
            
            self.logger.info(
                "ECG analysis completed",
                analysis_id=analysis_id,
                heart_rate=heart_rate_analysis.get("mean_heart_rate", 0),
                arrhythmias_detected=len(arrhythmia_detection.get("detected_arrhythmias", [])),
                signal_quality=signal_quality.get("quality_score", 0)
            )
            
            return ecg_analysis
            
        except Exception as e:
            self.logger.error(
                "Failed to process ECG data",
                signal_length=len(ecg_signal),
                sampling_rate=sampling_rate,
                error=str(e)
            )
            raise

    async def analyze_pulse_oximetry(
        self, 
        spo2: float, 
        pulse_rate: int
    ) -> PulseOxAnalysis:
        """
        Analyze pulse oximetry data.
        
        Args:
            spo2: Oxygen saturation percentage
            pulse_rate: Pulse rate in beats per minute
            
        Returns:
            PulseOxAnalysis with assessment
        """
        try:
            analysis_id = str(uuid.uuid4())
            
            # Validate measurements
            measurement_validity = await self._validate_pulse_ox_measurements(spo2, pulse_rate)
            
            # Assess oxygen saturation
            spo2_assessment = await self._assess_spo2_level(spo2)
            
            # Assess pulse rate
            pulse_assessment = await self._assess_pulse_rate(pulse_rate)
            
            # Combined assessment
            combined_assessment = await self._assess_combined_pulse_ox(spo2, pulse_rate)
            
            # Check for critical values
            critical_flags = await self._check_pulse_ox_critical_values(spo2, pulse_rate)
            
            # Generate recommendations
            clinical_recommendations = await self._generate_pulse_ox_recommendations(
                spo2_assessment, pulse_assessment, critical_flags
            )
            
            pulse_ox_analysis = PulseOxAnalysis(
                analysis_id=analysis_id,
                spo2_reading=spo2,
                pulse_rate_reading=pulse_rate,
                spo2_assessment=spo2_assessment,
                pulse_assessment=pulse_assessment,
                combined_assessment=combined_assessment,
                critical_flags=critical_flags,
                measurement_validity=measurement_validity,
                clinical_recommendations=clinical_recommendations,
                reference_ranges=self.reference_ranges.get("pulse_oximetry", {}),
                requires_intervention=any(flag.get("critical", False) for flag in critical_flags)
            )
            
            self.logger.info(
                "Pulse oximetry analysis completed",
                analysis_id=analysis_id,
                spo2=spo2,
                pulse_rate=pulse_rate,
                critical_flags_count=len(critical_flags)
            )
            
            return pulse_ox_analysis
            
        except Exception as e:
            self.logger.error(
                "Failed to analyze pulse oximetry",
                spo2=spo2,
                pulse_rate=pulse_rate,
                error=str(e)
            )
            raise

    # Helper methods for POCT analysis
    
    async def _process_test_strip_image(self, image: bytes) -> np.ndarray:
        """Process test strip image for analysis."""
        try:
            # Decode image
            nparr = np.frombuffer(image, np.uint8)
            cv_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Preprocessing
            # 1. Convert to RGB
            rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
            
            # 2. Normalize lighting
            lab = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            l = clahe.apply(l)
            processed_image = cv2.merge([l, a, b])
            processed_image = cv2.cvtColor(processed_image, cv2.COLOR_LAB2RGB)
            
            return processed_image
            
        except Exception as e:
            self.logger.error(f"Failed to process test strip image: {str(e)}")
            raise

    async def _extract_color_regions(self, image: np.ndarray, test_type: str) -> Dict[str, Any]:
        """Extract color regions from test strip."""
        # Simplified color region extraction
        # In production, would use sophisticated color detection
        
        height, width = image.shape[:2]
        regions = {}
        
        # Define region of interest based on test type
        if test_type == "glucose":
            regions["test_pad"] = image[height//3:2*height//3, width//4:3*width//4]
        elif test_type == "protein":
            regions["test_pad"] = image[height//4:height//2, width//3:2*width//3]
        
        return regions

    async def _analyze_color_intensity(self, color_regions: Dict[str, Any], test_type: str) -> Dict[str, float]:
        """Analyze color intensity in test regions."""
        analysis = {}
        
        for region_name, region_image in color_regions.items():
            if region_image is not None:
                # Calculate color intensity metrics
                mean_rgb = np.mean(region_image, axis=(0, 1))
                analysis[f"{region_name}_red"] = float(mean_rgb[0])
                analysis[f"{region_name}_green"] = float(mean_rgb[1]) 
                analysis[f"{region_name}_blue"] = float(mean_rgb[2])
                
                # Calculate overall intensity
                analysis[f"{region_name}_intensity"] = float(np.mean(mean_rgb))
        
        return analysis

    # Additional helper methods would continue here...
    # (Many more methods for signal processing, ML interpretation, etc.)