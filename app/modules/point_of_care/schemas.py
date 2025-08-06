"""
Point-of-Care Testing (POCT) Schemas for Healthcare Platform V2.0

Data models and schemas for real-time point-of-care diagnostic testing including
blood test strips, rapid antigen tests, ECG analysis, and medical device integration.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum
import uuid


class POCTDeviceType(str, Enum):
    """Point-of-care testing device types."""
    BLOOD_GLUCOSE = "blood_glucose"
    BLOOD_TEST_STRIP = "blood_test_strip"
    RAPID_ANTIGEN = "rapid_antigen"
    ECG_MONITOR = "ecg_monitor"
    PULSE_OXIMETER = "pulse_oximeter"
    BLOOD_PRESSURE = "blood_pressure"
    THERMOMETER = "thermometer"
    URINE_ANALYZER = "urine_analyzer"
    PREGNANCY_TEST = "pregnancy_test"
    CHOLESTEROL_TEST = "cholesterol_test"
    HEMOGLOBIN_TEST = "hemoglobin_test"
    INR_COAGULATION = "inr_coagulation"


class TestResultStatus(str, Enum):
    """Test result processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    INVALID = "invalid"
    REQUIRES_REPEAT = "requires_repeat"


class UrgencyLevel(str, Enum):
    """Clinical urgency levels."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class QualityFlag(str, Enum):
    """Test quality indicators."""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    UNACCEPTABLE = "unacceptable"


class POCTDevice(BaseModel):
    """Point-of-care testing device configuration."""
    
    device_id: str
    device_type: POCTDeviceType
    manufacturer: str
    model: str
    serial_number: str
    firmware_version: str
    calibration_date: datetime
    last_maintenance: datetime
    certification_number: Optional[str] = None
    location: str
    operator_id: Optional[str] = None
    is_active: bool = True
    communication_protocol: str = "bluetooth"  # bluetooth, usb, wifi, serial
    data_format: str = "json"  # json, hl7, csv, proprietary
    
    # Device capabilities
    supported_tests: List[str]
    measurement_range: Dict[str, tuple]
    accuracy_specifications: Dict[str, float]
    precision_specifications: Dict[str, float]
    
    # Quality control
    last_qc_test: Optional[datetime] = None
    qc_status: str = "valid"
    calibration_due_date: datetime
    maintenance_due_date: datetime


class BloodTestStrip(BaseModel):
    """Blood test strip analysis configuration."""
    
    strip_id: str
    test_type: str  # glucose, cholesterol, hemoglobin, etc.
    lot_number: str
    expiration_date: datetime
    storage_temperature: Optional[float] = None
    image_capture_settings: Dict[str, Any] = Field(default_factory=dict)
    color_calibration: Dict[str, Any] = Field(default_factory=dict)
    
    # Analysis parameters
    roi_coordinates: List[int] = Field(default_factory=list)  # Region of interest
    color_thresholds: Dict[str, tuple] = Field(default_factory=dict)
    expected_color_patterns: List[str] = Field(default_factory=list)


class BloodTestResults(BaseModel):
    """Blood test strip analysis results."""
    
    test_id: str
    device_id: str
    strip_config: BloodTestStrip
    test_timestamp: datetime
    
    # Raw measurements
    raw_image_data: Optional[str] = None  # Base64 encoded image
    color_values: Dict[str, List[float]]
    intensity_measurements: List[float]
    
    # Processed results
    test_value: float
    unit: str
    reference_range: tuple
    interpretation: str  # "normal", "low", "high", "critical"
    confidence_score: float = Field(ge=0.0, le=1.0)
    
    # Quality indicators
    image_quality_score: float = Field(ge=0.0, le=1.0)
    strip_alignment_score: float = Field(ge=0.0, le=1.0)
    lighting_quality_score: float = Field(ge=0.0, le=1.0)
    overall_quality: QualityFlag
    
    # Clinical context
    urgency_level: UrgencyLevel
    clinical_notes: Optional[str] = None
    requires_confirmation: bool = False


class RapidAntigenTest(BaseModel):
    """Rapid antigen test configuration."""
    
    test_id: str
    test_type: str  # covid19, influenza, strep, etc.
    manufacturer: str
    lot_number: str
    expiration_date: datetime
    sensitivity: float  # Manufacturer specified
    specificity: float  # Manufacturer specified
    
    # Image analysis settings
    control_line_position: List[int]
    test_line_position: List[int]
    expected_line_width: int
    minimum_line_intensity: float


class AntigenTestResult(BaseModel):
    """Rapid antigen test analysis results."""
    
    test_id: str
    device_id: str
    test_config: RapidAntigenTest
    test_timestamp: datetime
    
    # Raw analysis
    raw_image: Optional[str] = None  # Base64 encoded
    control_line_detected: bool
    test_line_detected: bool
    control_line_intensity: float
    test_line_intensity: float
    
    # Interpretation
    result: str  # "positive", "negative", "invalid"
    confidence_score: float = Field(ge=0.0, le=1.0)
    interpretation_notes: str
    
    # Quality control
    test_validity: bool
    quality_flags: List[str] = Field(default_factory=list)
    operator_verification: bool = False
    
    # Clinical context
    patient_symptoms: Optional[List[str]] = None
    risk_factors: Optional[List[str]] = None
    urgency_level: UrgencyLevel = UrgencyLevel.MODERATE


class ECGSignal(BaseModel):
    """ECG signal data structure."""
    
    signal_id: str
    device_id: str
    recording_timestamp: datetime
    duration_seconds: float
    sampling_rate: int  # Hz
    leads: List[str]  # Lead names (I, II, III, aVR, aVL, aVF, V1-V6)
    
    # Signal data
    raw_signals: Dict[str, List[float]]  # Lead name -> signal values
    filtered_signals: Dict[str, List[float]]
    annotations: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Signal quality
    signal_quality_scores: Dict[str, float]
    noise_level: float
    baseline_wander: float
    artifacts_detected: List[str] = Field(default_factory=list)


class ECGAnalysis(BaseModel):
    """ECG analysis results."""
    
    analysis_id: str
    signal: ECGSignal
    analysis_timestamp: datetime
    
    # Rhythm analysis
    heart_rate: float  # BPM
    rhythm_type: str  # "normal_sinus", "atrial_fib", "ventricular_tach", etc.
    rhythm_regularity: str  # "regular", "irregular"
    
    # Interval measurements
    pr_interval: Optional[float] = None  # ms
    qrs_duration: Optional[float] = None  # ms
    qt_interval: Optional[float] = None  # ms
    qtc_interval: Optional[float] = None  # Corrected QT
    
    # Morphology analysis
    p_wave_analysis: Dict[str, Any] = Field(default_factory=dict)
    qrs_morphology: Dict[str, Any] = Field(default_factory=dict)
    t_wave_analysis: Dict[str, Any] = Field(default_factory=dict)
    
    # Clinical interpretation
    primary_interpretation: str
    secondary_findings: List[str] = Field(default_factory=list)
    clinical_significance: str
    urgency_level: UrgencyLevel
    
    # AI analysis
    ai_confidence_score: float = Field(ge=0.0, le=1.0)
    ml_model_version: str
    feature_importance: Dict[str, float] = Field(default_factory=dict)
    
    # Quality metrics
    analysis_quality: QualityFlag
    requires_cardiologist_review: bool = False


class PulseOximetryReading(BaseModel):
    """Pulse oximetry measurement."""
    
    reading_id: str
    device_id: str
    timestamp: datetime
    
    # Measurements
    spo2_percentage: float = Field(ge=0.0, le=100.0)
    pulse_rate: float  # BPM
    perfusion_index: Optional[float] = None
    
    # Signal quality
    signal_strength: float = Field(ge=0.0, le=1.0)
    motion_artifact: bool = False
    poor_perfusion: bool = False
    
    # Waveform data (optional)
    plethysmogram: Optional[List[float]] = None
    
    
class PulseOxAnalysis(BaseModel):
    """Pulse oximetry analysis results."""
    
    analysis_id: str
    reading: PulseOximetryReading
    analysis_timestamp: datetime
    
    # Clinical interpretation
    hypoxemia_level: str  # "none", "mild", "moderate", "severe"
    pulse_regularity: str  # "regular", "irregular"
    clinical_significance: str
    urgency_level: UrgencyLevel
    
    # Trending analysis
    baseline_comparison: Optional[Dict[str, float]] = None
    trend_analysis: Optional[str] = None
    
    # Quality assessment
    measurement_reliability: QualityFlag
    requires_repeat: bool = False


class BloodPressureReading(BaseModel):
    """Blood pressure measurement."""
    
    reading_id: str
    device_id: str
    timestamp: datetime
    
    # Measurements
    systolic_mmhg: int = Field(ge=50, le=300)
    diastolic_mmhg: int = Field(ge=30, le=200)
    mean_arterial_pressure: Optional[float] = None
    pulse_pressure: Optional[float] = None
    
    # Measurement context
    patient_position: str = "sitting"  # sitting, lying, standing
    cuff_size: str = "adult"  # pediatric, adult, large_adult
    measurement_method: str = "automated"  # manual, automated
    
    # Quality indicators
    measurement_quality: QualityFlag
    motion_detected: bool = False
    irregular_pulse_detected: bool = False
    
    
class BPAnalysis(BaseModel):
    """Blood pressure analysis results."""
    
    analysis_id: str
    reading: BloodPressureReading
    analysis_timestamp: datetime
    
    # Clinical classification (AHA/ACC 2017)
    bp_category: str  # "normal", "elevated", "stage1_hypertension", "stage2_hypertension", "hypertensive_crisis"
    hypotension_assessment: bool = False
    
    # Risk assessment
    cardiovascular_risk: str  # "low", "moderate", "high"
    target_organ_risk: List[str] = Field(default_factory=list)
    
    # Clinical recommendations
    lifestyle_modifications: List[str] = Field(default_factory=list)
    medication_considerations: List[str] = Field(default_factory=list)
    follow_up_recommendations: str
    urgency_level: UrgencyLevel


class UrineAnalysis(BaseModel):
    """Urine analysis results."""
    
    analysis_id: str
    device_id: str
    test_timestamp: datetime
    
    # Physical properties
    color: str
    clarity: str  # "clear", "slightly_cloudy", "cloudy", "turbid"
    specific_gravity: float = Field(ge=1.000, le=1.040)
    
    # Chemical analysis
    protein: str  # "negative", "trace", "1+", "2+", "3+", "4+"
    glucose: str  # "negative", "trace", "1+", "2+", "3+", "4+"
    ketones: str  # "negative", "trace", "small", "moderate", "large"
    blood: str  # "negative", "trace", "1+", "2+", "3+"
    bilirubin: str  # "negative", "1+", "2+", "3+"
    urobilinogen: str  # "normal", "1+", "2+", "3+", "4+"
    nitrites: str  # "negative", "positive"
    leukocyte_esterase: str  # "negative", "trace", "1+", "2+", "3+"
    ph: float = Field(ge=4.5, le=9.0)
    
    # Microscopic (if available)
    rbc_per_hpf: Optional[int] = None
    wbc_per_hpf: Optional[int] = None
    bacteria: Optional[str] = None
    epithelial_cells: Optional[str] = None
    casts: Optional[List[str]] = None
    crystals: Optional[List[str]] = None
    
    # Clinical interpretation
    clinical_significance: str
    abnormal_findings: List[str] = Field(default_factory=list)
    urgency_level: UrgencyLevel
    requires_culture: bool = False


class IntegratedAnalysis(BaseModel):
    """Integrated POCT analysis combining multiple test results."""
    
    analysis_id: str
    patient_id: str
    test_session_id: str
    analysis_timestamp: datetime
    
    # Combined test results
    test_results: List[Union[BloodTestResults, AntigenTestResult, ECGAnalysis, 
                            PulseOxAnalysis, BPAnalysis, UrineAnalysis]]
    
    # Integrated interpretation
    clinical_summary: str
    key_findings: List[str]
    abnormal_values: List[Dict[str, Any]]
    critical_values: List[Dict[str, Any]]
    
    # Risk assessment
    overall_risk_level: UrgencyLevel
    immediate_concerns: List[str] = Field(default_factory=list)
    chronic_disease_indicators: List[str] = Field(default_factory=list)
    
    # Clinical recommendations
    immediate_actions: List[str] = Field(default_factory=list)
    follow_up_tests: List[str] = Field(default_factory=list)
    specialist_referrals: List[str] = Field(default_factory=list)
    medication_alerts: List[str] = Field(default_factory=list)
    
    # AI analysis
    ml_confidence_score: float = Field(ge=0.0, le=1.0)
    differential_diagnoses: List[Dict[str, float]] = Field(default_factory=list)
    evidence_strength: Dict[str, float] = Field(default_factory=dict)
    
    # Quality and validation
    overall_quality_score: float = Field(ge=0.0, le=1.0)
    requires_physician_review: bool = False
    validation_status: str = "pending"  # pending, validated, rejected


class POCTWorkflow(BaseModel):
    """Complete POCT workflow configuration."""
    
    workflow_id: str
    workflow_name: str
    clinical_indication: str
    target_population: str
    
    # Workflow steps
    required_tests: List[POCTDeviceType]
    test_sequence: List[str]
    decision_points: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Clinical protocols
    normal_value_actions: Dict[str, List[str]] = Field(default_factory=dict)
    abnormal_value_actions: Dict[str, List[str]] = Field(default_factory=dict)
    critical_value_protocols: Dict[str, List[str]] = Field(default_factory=dict)
    
    # Quality requirements
    minimum_quality_thresholds: Dict[str, float] = Field(default_factory=dict)
    repeat_test_criteria: List[str] = Field(default_factory=list)
    
    # Integration settings
    ehr_integration_enabled: bool = True
    lab_system_integration: bool = False
    notification_protocols: Dict[str, List[str]] = Field(default_factory=dict)


class POCTSession(BaseModel):
    """Complete POCT session record."""
    
    session_id: str
    patient_id: str
    operator_id: str
    location: str
    workflow: POCTWorkflow
    
    # Session metadata
    start_timestamp: datetime
    end_timestamp: Optional[datetime] = None
    session_status: TestResultStatus = TestResultStatus.PENDING
    
    # Test execution
    completed_tests: List[str] = Field(default_factory=list)
    pending_tests: List[str] = Field(default_factory=list)
    failed_tests: List[str] = Field(default_factory=list)
    
    # Results and analysis
    individual_results: List[Any] = Field(default_factory=list)
    integrated_analysis: Optional[IntegratedAnalysis] = None
    
    # Clinical outcome
    final_disposition: Optional[str] = None
    actions_taken: List[str] = Field(default_factory=list)
    notifications_sent: List[str] = Field(default_factory=list)
    
    # Quality metrics
    session_quality_score: float = Field(ge=0.0, le=1.0, default=0.0)
    operator_notes: Optional[str] = None
    technical_issues: List[str] = Field(default_factory=list)


class POCTQualityControl(BaseModel):
    """Quality control data for POCT devices."""
    
    qc_id: str
    device_id: str
    qc_timestamp: datetime
    qc_type: str  # "daily", "weekly", "monthly", "maintenance"
    
    # Control materials
    control_lot_number: str
    control_expiration: datetime
    expected_values: Dict[str, float]
    measured_values: Dict[str, float]
    
    # QC results
    within_acceptable_limits: bool
    bias_percentage: Dict[str, float] = Field(default_factory=dict)
    precision_cv: Dict[str, float] = Field(default_factory=dict)
    
    # Actions taken
    corrective_actions: List[str] = Field(default_factory=list)
    device_status_after_qc: str  # "operational", "needs_calibration", "out_of_service"
    next_qc_due: datetime
    
    # Operator information
    operator_id: str
    supervisor_reviewed: bool = False
    notes: Optional[str] = None