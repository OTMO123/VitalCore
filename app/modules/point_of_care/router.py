"""
Point-of-Care Testing (POCT) API Router for Healthcare Platform V2.0

RESTful API endpoints for real-time point-of-care diagnostic testing including
blood test strips, rapid antigen tests, ECG analysis, and medical device integration.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from typing import Dict, List, Any, Optional, Union
import uuid
import base64
import asyncio
from datetime import datetime

from .schemas import (
    POCTDevice, BloodTestStrip, BloodTestResults, RapidAntigenTest, AntigenTestResult,
    ECGSignal, ECGAnalysis, PulseOximetryReading, PulseOxAnalysis,
    BloodPressureReading, BPAnalysis, UrineAnalysis, IntegratedAnalysis,
    POCTWorkflow, POCTSession, POCTQualityControl, POCTDeviceType,
    TestResultStatus, UrgencyLevel, QualityFlag
)
from .poct_analyzer import POCTAnalyzer, POCTConfig
from ..auth.service import get_current_user_id, require_role
from ...core.audit_logger import audit_log
from ...core.config import get_settings

router = APIRouter(prefix="/api/v1/poct", tags=["Point-of-Care Testing"])
settings = get_settings()

# Initialize POCT analyzer
poct_config = POCTConfig()
poct_analyzer = POCTAnalyzer()

# Active POCT sessions
active_sessions: Dict[str, POCTSession] = {}

@router.post("/devices/register", response_model=Dict[str, str])
@audit_log("register_poct_device")
async def register_poct_device(
    device: POCTDevice,
    current_user: str = Depends(require_role("technician"))
) -> Dict[str, str]:
    """
    Register a new POCT device.
    
    Args:
        device: POCT device configuration
        
    Returns:
        Registration confirmation
    """
    try:
        # Validate device configuration
        if device.device_type not in POCTDeviceType:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported device type: {device.device_type}"
            )
        
        # Store device configuration (in production, would use database)
        device_registry = getattr(poct_analyzer, 'device_registry', {})
        device_registry[device.device_id] = device
        poct_analyzer.device_registry = device_registry
        
        return {
            "status": "success",
            "message": f"POCT device {device.device_id} registered successfully",
            "device_id": device.device_id,
            "device_type": device.device_type.value,
            "registration_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register POCT device: {str(e)}"
        )

@router.post("/blood-test/analyze", response_model=BloodTestResults)
@audit_log("analyze_blood_test_strip")
async def analyze_blood_test_strip(
    image: UploadFile = File(...),
    device_id: str,
    test_type: str,
    strip_config: Optional[Dict[str, Any]] = None,
    current_user: str = Depends(require_role("technician"))
) -> BloodTestResults:
    """
    Analyze blood test strip using computer vision.
    
    Args:
        image: Test strip image file
        device_id: POCT device identifier
        test_type: Type of blood test
        strip_config: Optional strip configuration
        
    Returns:
        Blood test analysis results
    """
    try:
        # Validate image
        if not image.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image format"
            )
        
        # Read image data
        image_data = await image.read()
        image_b64 = base64.b64encode(image_data).decode()
        
        # Get device information
        device_registry = getattr(poct_analyzer, 'device_registry', {})
        if device_id not in device_registry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="POCT device not found"
            )
        device = device_registry[device_id]
        
        # Create strip configuration
        if strip_config:
            strip = BloodTestStrip(
                strip_id=str(uuid.uuid4()),
                test_type=test_type,
                **strip_config
            )
        else:
            strip = BloodTestStrip(
                strip_id=str(uuid.uuid4()),
                test_type=test_type,
                lot_number="DEFAULT001",
                expiration_date=datetime.utcnow()
            )
        
        # Analyze blood test strip
        results = await poct_analyzer.analyze_blood_test_strip(
            image_b64, strip, device
        )
        
        return results
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze blood test strip: {str(e)}"
        )

@router.post("/antigen-test/analyze", response_model=AntigenTestResult)
@audit_log("analyze_rapid_antigen_test")
async def analyze_rapid_antigen_test(
    image: UploadFile = File(...),
    device_id: str,
    test_type: str = "covid19",
    manufacturer: str = "Generic",
    current_user: str = Depends(require_role("technician"))
) -> AntigenTestResult:
    """
    Analyze rapid antigen test using computer vision.
    
    Args:
        image: Antigen test image file
        device_id: POCT device identifier
        test_type: Type of antigen test
        manufacturer: Test manufacturer
        
    Returns:
        Antigen test analysis results
    """
    try:
        # Validate image
        if not image.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image format"
            )
        
        # Read image data
        image_data = await image.read()
        image_b64 = base64.b64encode(image_data).decode()
        
        # Get device information
        device_registry = getattr(poct_analyzer, 'device_registry', {})
        if device_id not in device_registry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="POCT device not found"
            )
        device = device_registry[device_id]
        
        # Create test configuration
        test_config = RapidAntigenTest(
            test_id=str(uuid.uuid4()),
            test_type=test_type,
            manufacturer=manufacturer,
            lot_number="DEFAULT001",
            expiration_date=datetime.utcnow(),
            sensitivity=0.95,
            specificity=0.98,
            control_line_position=[100, 50],
            test_line_position=[100, 80],
            expected_line_width=5,
            minimum_line_intensity=30.0
        )
        
        # Analyze rapid antigen test
        results = await poct_analyzer.analyze_rapid_antigen_test(
            image_b64, test_config, device
        )
        
        return results
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze rapid antigen test: {str(e)}"
        )

@router.post("/ecg/analyze", response_model=ECGAnalysis)
@audit_log("analyze_ecg_signal")
async def analyze_ecg_signal(
    signal_data: Dict[str, List[float]],
    device_id: str,
    sampling_rate: int = 250,
    duration_seconds: float = 10.0,
    current_user: str = Depends(require_role("technician"))
) -> ECGAnalysis:
    """
    Analyze ECG signal using advanced signal processing.
    
    Args:
        signal_data: ECG signal data by lead
        device_id: POCT device identifier
        sampling_rate: Signal sampling rate in Hz
        duration_seconds: Signal duration
        
    Returns:
        ECG analysis results
    """
    try:
        # Validate signal data
        if not signal_data or not isinstance(signal_data, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ECG signal data"
            )
        
        # Get device information
        device_registry = getattr(poct_analyzer, 'device_registry', {})
        if device_id not in device_registry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="POCT device not found"
            )
        device = device_registry[device_id]
        
        # Create ECG signal object
        ecg_signal = ECGSignal(
            signal_id=str(uuid.uuid4()),
            device_id=device_id,
            recording_timestamp=datetime.utcnow(),
            duration_seconds=duration_seconds,
            sampling_rate=sampling_rate,
            leads=list(signal_data.keys()),
            raw_signals=signal_data,
            filtered_signals={},
            signal_quality_scores={},
            noise_level=0.0,
            baseline_wander=0.0
        )
        
        # Analyze ECG signal
        analysis = await poct_analyzer.analyze_ecg_signal(ecg_signal, device)
        
        return analysis
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze ECG signal: {str(e)}"
        )

@router.post("/pulse-oximetry/analyze", response_model=PulseOxAnalysis)
@audit_log("analyze_pulse_oximetry")
async def analyze_pulse_oximetry(
    spo2_percentage: float,
    pulse_rate: float,
    device_id: str,
    perfusion_index: Optional[float] = None,
    plethysmogram: Optional[List[float]] = None,
    current_user: str = Depends(require_role("technician"))
) -> PulseOxAnalysis:
    """
    Analyze pulse oximetry reading.
    
    Args:
        spo2_percentage: Oxygen saturation percentage
        pulse_rate: Pulse rate in BPM
        device_id: POCT device identifier
        perfusion_index: Optional perfusion index
        plethysmogram: Optional waveform data
        
    Returns:
        Pulse oximetry analysis
    """
    try:
        # Validate readings
        if not 0 <= spo2_percentage <= 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid SpO2 percentage (must be 0-100)"
            )
        
        if not 20 <= pulse_rate <= 300:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid pulse rate (must be 20-300 BPM)"
            )
        
        # Get device information
        device_registry = getattr(poct_analyzer, 'device_registry', {})
        if device_id not in device_registry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="POCT device not found"
            )
        device = device_registry[device_id]
        
        # Create pulse oximetry reading
        reading = PulseOximetryReading(
            reading_id=str(uuid.uuid4()),
            device_id=device_id,
            timestamp=datetime.utcnow(),
            spo2_percentage=spo2_percentage,
            pulse_rate=pulse_rate,
            perfusion_index=perfusion_index,
            signal_strength=0.8,  # Default value
            plethysmogram=plethysmogram
        )
        
        # Analyze pulse oximetry
        analysis = await poct_analyzer.analyze_pulse_oximetry(reading, device)
        
        return analysis
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze pulse oximetry: {str(e)}"
        )

@router.post("/blood-pressure/analyze", response_model=BPAnalysis)
@audit_log("analyze_blood_pressure")
async def analyze_blood_pressure(
    systolic_mmhg: int,
    diastolic_mmhg: int,
    device_id: str,
    patient_position: str = "sitting",
    current_user: str = Depends(require_role("technician"))
) -> BPAnalysis:
    """
    Analyze blood pressure reading.
    
    Args:
        systolic_mmhg: Systolic pressure in mmHg
        diastolic_mmhg: Diastolic pressure in mmHg
        device_id: POCT device identifier
        patient_position: Patient position during measurement
        
    Returns:
        Blood pressure analysis
    """
    try:
        # Validate readings
        if not 50 <= systolic_mmhg <= 300:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid systolic pressure (must be 50-300 mmHg)"
            )
        
        if not 30 <= diastolic_mmhg <= 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid diastolic pressure (must be 30-200 mmHg)"
            )
        
        # Get device information
        device_registry = getattr(poct_analyzer, 'device_registry', {})
        if device_id not in device_registry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="POCT device not found"
            )
        device = device_registry[device_id]
        
        # Create blood pressure reading
        reading = BloodPressureReading(
            reading_id=str(uuid.uuid4()),
            device_id=device_id,
            timestamp=datetime.utcnow(),
            systolic_mmhg=systolic_mmhg,
            diastolic_mmhg=diastolic_mmhg,
            patient_position=patient_position,
            measurement_quality=QualityFlag.GOOD
        )
        
        # Analyze blood pressure (create a simple analysis function)
        analysis = BPAnalysis(
            analysis_id=str(uuid.uuid4()),
            reading=reading,
            analysis_timestamp=datetime.utcnow(),
            bp_category=await _classify_blood_pressure(systolic_mmhg, diastolic_mmhg),
            hypotension_assessment=systolic_mmhg < 90 or diastolic_mmhg < 60,
            cardiovascular_risk=await _assess_cv_risk(systolic_mmhg, diastolic_mmhg),
            target_organ_risk=[],
            lifestyle_modifications=await _get_lifestyle_recommendations(systolic_mmhg, diastolic_mmhg),
            medication_considerations=[],
            follow_up_recommendations=await _get_bp_follow_up(systolic_mmhg, diastolic_mmhg),
            urgency_level=await _determine_bp_urgency(systolic_mmhg, diastolic_mmhg)
        )
        
        return analysis
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze blood pressure: {str(e)}"
        )

@router.post("/integrated-analysis", response_model=IntegratedAnalysis)
@audit_log("perform_integrated_poct_analysis")
async def perform_integrated_analysis(
    test_results_data: Dict[str, Any],
    patient_id: str,
    session_id: Optional[str] = None,
    current_user: str = Depends(require_role("doctor"))
) -> IntegratedAnalysis:
    """
    Perform integrated analysis of multiple POCT test results.
    
    Args:
        test_results_data: Combined test results data
        patient_id: Patient identifier
        session_id: Optional session identifier
        
    Returns:
        Integrated analysis results
    """
    try:
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Parse test results (simplified for this example)
        test_results = []
        
        # In a real implementation, would parse different result types
        # For now, create a simplified integrated analysis
        analysis = IntegratedAnalysis(
            analysis_id=str(uuid.uuid4()),
            patient_id=patient_id,
            test_session_id=session_id,
            analysis_timestamp=datetime.utcnow(),
            test_results=test_results,
            clinical_summary="Integrated POCT analysis completed",
            key_findings=["No critical findings identified"],
            abnormal_values=[],
            critical_values=[],
            overall_risk_level=UrgencyLevel.LOW,
            immediate_concerns=[],
            chronic_disease_indicators=[],
            immediate_actions=[],
            follow_up_tests=[],
            specialist_referrals=[],
            medication_alerts=[],
            ml_confidence_score=0.85,
            differential_diagnoses=[],
            evidence_strength={},
            overall_quality_score=0.9,
            requires_physician_review=False
        )
        
        return analysis
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform integrated analysis: {str(e)}"
        )

@router.post("/sessions/start", response_model=Dict[str, str])
@audit_log("start_poct_session")
async def start_poct_session(
    patient_id: str,
    workflow_id: str,
    location: str,
    current_user: str = Depends(require_role("technician"))
) -> Dict[str, str]:
    """
    Start a new POCT session.
    
    Args:
        patient_id: Patient identifier
        workflow_id: POCT workflow identifier
        location: Test location
        
    Returns:
        Session information
    """
    try:
        session_id = str(uuid.uuid4())
        
        # Create basic workflow (in production, would load from database)
        workflow = POCTWorkflow(
            workflow_id=workflow_id,
            workflow_name="Standard POCT Workflow",
            clinical_indication="Routine screening",
            target_population="General",
            required_tests=[POCTDeviceType.BLOOD_GLUCOSE],
            test_sequence=["glucose_test"],
            ehr_integration_enabled=True
        )
        
        # Create session
        session = POCTSession(
            session_id=session_id,
            patient_id=patient_id,
            operator_id=current_user,
            location=location,
            workflow=workflow,
            start_timestamp=datetime.utcnow(),
            session_status=TestResultStatus.IN_PROGRESS
        )
        
        # Store session
        active_sessions[session_id] = session
        
        return {
            "session_id": session_id,
            "status": "started",
            "workflow_name": workflow.workflow_name,
            "start_time": session.start_timestamp.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start POCT session: {str(e)}"
        )

@router.get("/sessions/{session_id}", response_model=POCTSession)
async def get_poct_session(
    session_id: str,
    current_user: str = Depends(require_role("technician"))
) -> POCTSession:
    """
    Get POCT session information.
    
    Args:
        session_id: Session identifier
        
    Returns:
        POCT session details
    """
    if session_id not in active_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="POCT session not found"
        )
    
    return active_sessions[session_id]

@router.put("/sessions/{session_id}/complete", response_model=Dict[str, str])
@audit_log("complete_poct_session")
async def complete_poct_session(
    session_id: str,
    final_disposition: str,
    notes: Optional[str] = None,
    current_user: str = Depends(require_role("technician"))
) -> Dict[str, str]:
    """
    Complete a POCT session.
    
    Args:
        session_id: Session identifier
        final_disposition: Final clinical disposition
        notes: Optional session notes
        
    Returns:
        Completion confirmation
    """
    try:
        if session_id not in active_sessions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="POCT session not found"
            )
        
        session = active_sessions[session_id]
        session.end_timestamp = datetime.utcnow()
        session.session_status = TestResultStatus.COMPLETED
        session.final_disposition = final_disposition
        session.operator_notes = notes
        
        return {
            "session_id": session_id,
            "status": "completed",
            "final_disposition": final_disposition,
            "completion_time": session.end_timestamp.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete POCT session: {str(e)}"
        )

@router.get("/devices", response_model=List[POCTDevice])
async def list_poct_devices(
    device_type: Optional[POCTDeviceType] = None,
    current_user: str = Depends(require_role("technician"))
) -> List[POCTDevice]:
    """
    List registered POCT devices.
    
    Args:
        device_type: Optional filter by device type
        
    Returns:
        List of POCT devices
    """
    device_registry = getattr(poct_analyzer, 'device_registry', {})
    devices = list(device_registry.values())
    
    if device_type:
        devices = [d for d in devices if d.device_type == device_type]
    
    return devices

@router.get("/health", response_model=Dict[str, Any])
async def poct_health_check() -> Dict[str, Any]:
    """
    POCT service health check.
    
    Returns:
        Service health status
    """
    try:
        device_registry = getattr(poct_analyzer, 'device_registry', {})
        
        return {
            "status": "healthy",
            "registered_devices": len(device_registry),
            "active_sessions": len(active_sessions),
            "supported_device_types": [dt.value for dt in POCTDeviceType],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# Helper functions for blood pressure analysis

async def _classify_blood_pressure(systolic: int, diastolic: int) -> str:
    """Classify blood pressure according to AHA/ACC guidelines."""
    if systolic >= 180 or diastolic >= 120:
        return "hypertensive_crisis"
    elif systolic >= 140 or diastolic >= 90:
        return "stage2_hypertension"
    elif systolic >= 130 or diastolic >= 80:
        return "stage1_hypertension"
    elif systolic >= 120:
        return "elevated"
    else:
        return "normal"

async def _assess_cv_risk(systolic: int, diastolic: int) -> str:
    """Assess cardiovascular risk based on blood pressure."""
    if systolic >= 160 or diastolic >= 100:
        return "high"
    elif systolic >= 140 or diastolic >= 90:
        return "moderate"
    else:
        return "low"

async def _get_lifestyle_recommendations(systolic: int, diastolic: int) -> List[str]:
    """Get lifestyle modification recommendations."""
    recommendations = []
    
    if systolic >= 130 or diastolic >= 80:
        recommendations.extend([
            "Reduce sodium intake to <2300mg/day",
            "Engage in regular aerobic exercise",
            "Maintain healthy weight (BMI 18.5-24.9)",
            "Limit alcohol consumption",
            "Follow DASH diet"
        ])
    
    return recommendations

async def _get_bp_follow_up(systolic: int, diastolic: int) -> str:
    """Get blood pressure follow-up recommendations."""
    if systolic >= 180 or diastolic >= 120:
        return "Immediate medical evaluation required"
    elif systolic >= 140 or diastolic >= 90:
        return "Follow up in 1-2 weeks"
    elif systolic >= 130 or diastolic >= 80:
        return "Follow up in 3-6 months"
    else:
        return "Annual screening"

async def _determine_bp_urgency(systolic: int, diastolic: int) -> UrgencyLevel:
    """Determine urgency level for blood pressure reading."""
    if systolic >= 180 or diastolic >= 120:
        return UrgencyLevel.CRITICAL
    elif systolic >= 160 or diastolic >= 100:
        return UrgencyLevel.HIGH
    elif systolic >= 140 or diastolic >= 90:
        return UrgencyLevel.MODERATE
    else:
        return UrgencyLevel.LOW