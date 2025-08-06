"""
Point-of-Care Testing (POCT) Service for Healthcare Platform V2.0

Service layer for POCT operations, device management, and clinical workflow integration.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass

from .schemas import (
    POCTDevice, POCTDeviceType, POCTSession, POCTWorkflow, POCTQualityControl,
    BloodTestResults, AntigenTestResult, ECGAnalysis, PulseOxAnalysis, BPAnalysis,
    TestResultStatus, UrgencyLevel, QualityFlag
)
from .poct_analyzer import POCTAnalyzer, POCTConfig
from ..audit_logger.service import AuditLogService
from ..healthcare_records.service import HealthcareRecordService
from ...core.config import get_settings
from ...core.database import get_db_session

logger = logging.getLogger(__name__)
settings = get_settings()

@dataclass
class POCTDeviceStatus:
    """POCT device status information."""
    device_id: str
    is_online: bool
    last_heartbeat: datetime
    battery_level: Optional[float] = None
    error_status: Optional[str] = None
    tests_performed_today: int = 0

class POCTService:
    """
    Service layer for Point-of-Care Testing operations.
    
    Manages POCT devices, test sessions, quality control, and clinical integration.
    """
    
    def __init__(self):
        self.logger = logger.bind(component="POCTService")
        
        # Initialize POCT analyzer
        self.poct_config = POCTConfig()
        self.poct_analyzer = POCTAnalyzer()
        
        # Initialize services
        self.audit_service = AuditLogService()
        self.healthcare_service = HealthcareRecordService()
        
        # Device management
        self.registered_devices: Dict[str, POCTDevice] = {}
        self.device_status: Dict[str, POCTDeviceStatus] = {}
        
        # Session management
        self.active_sessions: Dict[str, POCTSession] = {}
        self.completed_sessions: Dict[str, POCTSession] = {}
        
        # Quality control
        self.qc_results: Dict[str, List[POCTQualityControl]] = {}
        
        # Workflow definitions
        self.workflows: Dict[str, POCTWorkflow] = {}
        self._initialize_default_workflows()
        
        self.logger.info("POCTService initialized successfully")
    
    def _initialize_default_workflows(self):
        """Initialize default POCT workflows."""
        try:
            # Emergency workflow
            emergency_workflow = POCTWorkflow(
                workflow_id="emergency_poct",
                workflow_name="Emergency POCT Panel",
                clinical_indication="Emergency department assessment",
                target_population="Emergency patients",
                required_tests=[
                    POCTDeviceType.BLOOD_GLUCOSE,
                    POCTDeviceType.ECG_MONITOR,
                    POCTDeviceType.PULSE_OXIMETER,
                    POCTDeviceType.BLOOD_PRESSURE_MONITOR
                ],
                test_sequence=["glucose", "ecg", "pulse_ox", "blood_pressure"],
                normal_value_actions={
                    "glucose": ["Continue routine care"],
                    "ecg": ["Monitor as indicated"],
                    "pulse_ox": ["Continue current oxygen therapy"],
                    "blood_pressure": ["Continue monitoring"]
                },
                abnormal_value_actions={
                    "glucose": ["Assess for diabetes", "Repeat if <70 or >200"],
                    "ecg": ["Cardiology consult if abnormal rhythm"],
                    "pulse_ox": ["Increase oxygen if <92%"],
                    "blood_pressure": ["Consider antihypertensive if >160/100"]
                },
                critical_value_protocols={
                    "glucose": ["Immediate intervention if <40 or >400"],
                    "ecg": ["Immediate cardiology if ventricular arrhythmia"],
                    "pulse_ox": ["Immediate respiratory support if <88%"],
                    "blood_pressure": ["Immediate intervention if >180/120"]
                }
            )
            
            # Diabetes monitoring workflow
            diabetes_workflow = POCTWorkflow(
                workflow_id="diabetes_monitoring",
                workflow_name="Diabetes Monitoring Panel",
                clinical_indication="Diabetes management",
                target_population="Diabetic patients",
                required_tests=[
                    POCTDeviceType.BLOOD_GLUCOSE,
                    POCTDeviceType.BLOOD_TEST_STRIPS
                ],
                test_sequence=["glucose", "hba1c_estimate"],
                normal_value_actions={
                    "glucose": ["Continue current medication regimen"],
                    "hba1c_estimate": ["Annual monitoring adequate"]
                },
                abnormal_value_actions={
                    "glucose": ["Adjust medication as needed"],
                    "hba1c_estimate": ["Consider medication adjustment"]
                },
                critical_value_protocols={
                    "glucose": ["Emergency intervention if <40 or >400"]
                }
            )
            
            # Cardiac screening workflow
            cardiac_workflow = POCTWorkflow(
                workflow_id="cardiac_screening",
                workflow_name="Cardiac Screening Panel",
                clinical_indication="Cardiac assessment",
                target_population="Patients with cardiac symptoms",
                required_tests=[
                    POCTDeviceType.ECG_MONITOR,
                    POCTDeviceType.BLOOD_PRESSURE_MONITOR,
                    POCTDeviceType.PULSE_OXIMETER
                ],
                test_sequence=["ecg", "blood_pressure", "pulse_ox"],
                normal_value_actions={
                    "ecg": ["Continue routine monitoring"],
                    "blood_pressure": ["Annual screening"],
                    "pulse_ox": ["No additional monitoring needed"]
                },
                abnormal_value_actions={
                    "ecg": ["Cardiology referral if abnormal"],
                    "blood_pressure": ["Lifestyle counseling, consider medication"],
                    "pulse_ox": ["Pulmonary evaluation if low"]
                },
                critical_value_protocols={
                    "ecg": ["Immediate cardiology if life-threatening rhythm"],
                    "blood_pressure": ["Emergency care if hypertensive crisis"],
                    "pulse_ox": ["Emergency respiratory support if <88%"]
                }
            )
            
            self.workflows = {
                "emergency_poct": emergency_workflow,
                "diabetes_monitoring": diabetes_workflow,
                "cardiac_screening": cardiac_workflow
            }
            
            self.logger.info("Default POCT workflows initialized", count=len(self.workflows))
            
        except Exception as e:
            self.logger.error(f"Failed to initialize default workflows: {str(e)}")
    
    async def register_device(self, device: POCTDevice) -> Dict[str, Any]:
        """
        Register a new POCT device.
        
        Args:
            device: POCT device configuration
            
        Returns:
            Registration result
        """
        try:
            # Validate device
            if device.device_id in self.registered_devices:
                raise ValueError(f"Device {device.device_id} already registered")
            
            if device.device_type not in POCTDeviceType:
                raise ValueError(f"Unsupported device type: {device.device_type}")
            
            # Register device
            self.registered_devices[device.device_id] = device
            
            # Initialize device status
            self.device_status[device.device_id] = POCTDeviceStatus(
                device_id=device.device_id,
                is_online=True,
                last_heartbeat=datetime.utcnow(),
                tests_performed_today=0
            )
            
            # Audit device registration
            await self.audit_service.log_event({
                "event_type": "device_registration",
                "device_id": device.device_id,
                "device_type": device.device_type.value,
                "location": device.location,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            self.logger.info(
                "POCT device registered",
                device_id=device.device_id,
                device_type=device.device_type.value,
                location=device.location
            )
            
            return {
                "status": "success",
                "device_id": device.device_id,
                "registration_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to register device: {str(e)}")
            raise
    
    async def start_poct_session(
        self,
        patient_id: str,
        workflow_id: str,
        operator_id: str,
        location: str
    ) -> POCTSession:
        """
        Start a new POCT session.
        
        Args:
            patient_id: Patient identifier
            workflow_id: Workflow identifier
            operator_id: Operator identifier
            location: Test location
            
        Returns:
            POCT session
        """
        try:
            session_id = str(uuid.uuid4())
            
            # Get workflow
            if workflow_id not in self.workflows:
                raise ValueError(f"Workflow {workflow_id} not found")
            workflow = self.workflows[workflow_id]
            
            # Create session
            session = POCTSession(
                session_id=session_id,
                patient_id=patient_id,
                operator_id=operator_id,
                location=location,
                workflow=workflow,
                start_timestamp=datetime.utcnow(),
                session_status=TestResultStatus.IN_PROGRESS,
                pending_tests=workflow.test_sequence.copy(),
                session_quality_score=0.0
            )
            
            # Store session
            self.active_sessions[session_id] = session
            
            # Audit session start
            await self.audit_service.log_event({
                "event_type": "poct_session_started",
                "session_id": session_id,
                "patient_id": patient_id,
                "workflow_id": workflow_id,
                "operator_id": operator_id,
                "location": location,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            self.logger.info(
                "POCT session started",
                session_id=session_id,
                patient_id=patient_id,
                workflow=workflow.workflow_name,
                pending_tests=len(session.pending_tests)
            )
            
            return session
            
        except Exception as e:
            self.logger.error(f"Failed to start POCT session: {str(e)}")
            raise
    
    async def complete_test_in_session(
        self,
        session_id: str,
        test_type: str,
        test_result: Union[BloodTestResults, AntigenTestResult, ECGAnalysis, PulseOxAnalysis, BPAnalysis]
    ) -> Dict[str, Any]:
        """
        Complete a test within a POCT session.
        
        Args:
            session_id: Session identifier
            test_type: Type of test completed
            test_result: Test result data
            
        Returns:
            Completion status
        """
        try:
            if session_id not in self.active_sessions:
                raise ValueError(f"Session {session_id} not found")
            
            session = self.active_sessions[session_id]
            
            # Add test result
            session.individual_results.append(test_result)
            
            # Move from pending to completed
            if test_type in session.pending_tests:
                session.pending_tests.remove(test_type)
                session.completed_tests.append(test_type)
            
            # Check for critical values and generate alerts
            critical_alerts = await self._check_critical_values(test_result)
            if critical_alerts:
                session.notifications_sent.extend(critical_alerts)
            
            # Update session quality score
            await self._update_session_quality_score(session)
            
            self.logger.info(
                "Test completed in POCT session",
                session_id=session_id,
                test_type=test_type,
                remaining_tests=len(session.pending_tests),
                critical_alerts=len(critical_alerts)
            )
            
            return {
                "status": "completed",
                "test_type": test_type,
                "remaining_tests": session.pending_tests,
                "critical_alerts": critical_alerts
            }
            
        except Exception as e:
            self.logger.error(f"Failed to complete test in session: {str(e)}")
            raise
    
    async def complete_poct_session(
        self,
        session_id: str,
        final_disposition: str,
        operator_notes: Optional[str] = None
    ) -> POCTSession:
        """
        Complete a POCT session.
        
        Args:
            session_id: Session identifier
            final_disposition: Final clinical disposition
            operator_notes: Optional operator notes
            
        Returns:
            Completed session
        """
        try:
            if session_id not in self.active_sessions:
                raise ValueError(f"Session {session_id} not found")
            
            session = self.active_sessions[session_id]
            
            # Complete session
            session.end_timestamp = datetime.utcnow()
            session.session_status = TestResultStatus.COMPLETED
            session.final_disposition = final_disposition
            session.operator_notes = operator_notes
            
            # Perform integrated analysis if multiple tests
            if len(session.individual_results) > 1:
                session.integrated_analysis = await self.poct_analyzer.perform_integrated_analysis(
                    session.individual_results,
                    session.patient_id,
                    session_id
                )
            
            # Generate final recommendations
            session.actions_taken = await self._generate_final_actions(session)
            
            # Move to completed sessions
            self.completed_sessions[session_id] = session
            del self.active_sessions[session_id]
            
            # Update healthcare record
            await self._update_healthcare_record(session)
            
            # Audit session completion
            await self.audit_service.log_event({
                "event_type": "poct_session_completed",
                "session_id": session_id,
                "final_disposition": final_disposition,
                "tests_completed": len(session.completed_tests),
                "session_duration_minutes": (session.end_timestamp - session.start_timestamp).total_seconds() / 60,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            self.logger.info(
                "POCT session completed",
                session_id=session_id,
                final_disposition=final_disposition,
                tests_completed=len(session.completed_tests),
                quality_score=session.session_quality_score
            )
            
            return session
            
        except Exception as e:
            self.logger.error(f"Failed to complete POCT session: {str(e)}")
            raise
    
    async def perform_quality_control(
        self,
        device_id: str,
        control_lot_number: str,
        expected_values: Dict[str, float],
        measured_values: Dict[str, float]
    ) -> POCTQualityControl:
        """
        Perform quality control for a POCT device.
        
        Args:
            device_id: Device identifier
            control_lot_number: QC material lot number
            expected_values: Expected QC values
            measured_values: Measured QC values
            
        Returns:
            Quality control results
        """
        try:
            if device_id not in self.registered_devices:
                raise ValueError(f"Device {device_id} not registered")
            
            # Calculate bias and precision
            bias_percentage = {}
            within_limits = True
            
            for analyte, expected in expected_values.items():
                if analyte in measured_values:
                    measured = measured_values[analyte]
                    bias = ((measured - expected) / expected) * 100
                    bias_percentage[analyte] = bias
                    
                    # Check if within acceptable limits (±10% for most analytes)
                    if abs(bias) > 10.0:
                        within_limits = False
            
            # Determine corrective actions
            corrective_actions = []
            device_status_after_qc = "operational"
            
            if not within_limits:
                corrective_actions.append("Recalibrate device")
                corrective_actions.append("Repeat QC with fresh control material")
                device_status_after_qc = "needs_calibration"
            
            # Create QC result
            qc_result = POCTQualityControl(
                qc_id=str(uuid.uuid4()),
                device_id=device_id,
                qc_timestamp=datetime.utcnow(),
                qc_type="daily",
                control_lot_number=control_lot_number,
                control_expiration=datetime.utcnow() + timedelta(days=30),  # Default
                expected_values=expected_values,
                measured_values=measured_values,
                within_acceptable_limits=within_limits,
                bias_percentage=bias_percentage,
                corrective_actions=corrective_actions,
                device_status_after_qc=device_status_after_qc,
                next_qc_due=datetime.utcnow() + timedelta(days=1),
                operator_id="system"  # Would be actual operator
            )
            
            # Store QC result
            if device_id not in self.qc_results:
                self.qc_results[device_id] = []
            self.qc_results[device_id].append(qc_result)
            
            # Update device status
            if device_id in self.device_status:
                self.device_status[device_id].error_status = None if within_limits else "QC_FAILED"
            
            self.logger.info(
                "Quality control performed",
                device_id=device_id,
                within_limits=within_limits,
                device_status=device_status_after_qc
            )
            
            return qc_result
            
        except Exception as e:
            self.logger.error(f"Failed to perform quality control: {str(e)}")
            raise
    
    async def get_device_status(self, device_id: str) -> Dict[str, Any]:
        """
        Get current status of a POCT device.
        
        Args:
            device_id: Device identifier
            
        Returns:
            Device status information
        """
        try:
            if device_id not in self.registered_devices:
                raise ValueError(f"Device {device_id} not registered")
            
            device = self.registered_devices[device_id]
            status = self.device_status.get(device_id)
            
            # Get recent QC results
            recent_qc = []
            if device_id in self.qc_results:
                recent_qc = self.qc_results[device_id][-5:]  # Last 5 QC results
            
            return {
                "device_id": device_id,
                "device_type": device.device_type.value,
                "location": device.location,
                "is_active": device.is_active,
                "is_online": status.is_online if status else False,
                "last_heartbeat": status.last_heartbeat.isoformat() if status else None,
                "battery_level": status.battery_level if status else None,
                "error_status": status.error_status if status else None,
                "tests_performed_today": status.tests_performed_today if status else 0,
                "last_maintenance": device.last_maintenance.isoformat(),
                "calibration_due_date": device.calibration_due_date.isoformat(),
                "maintenance_due_date": device.maintenance_due_date.isoformat(),
                "recent_qc_results": [qc.dict() for qc in recent_qc]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get device status: {str(e)}")
            raise
    
    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get current status of a POCT session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session status information
        """
        try:
            session = None
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
            elif session_id in self.completed_sessions:
                session = self.completed_sessions[session_id]
            
            if not session:
                raise ValueError(f"Session {session_id} not found")
            
            return {
                "session_id": session_id,
                "status": session.session_status.value,
                "patient_id": session.patient_id,
                "workflow_name": session.workflow.workflow_name,
                "start_time": session.start_timestamp.isoformat(),
                "end_time": session.end_timestamp.isoformat() if session.end_timestamp else None,
                "completed_tests": session.completed_tests,
                "pending_tests": session.pending_tests,
                "failed_tests": session.failed_tests,
                "quality_score": session.session_quality_score,
                "final_disposition": session.final_disposition,
                "requires_physician_review": session.integrated_analysis.requires_physician_review if session.integrated_analysis else False
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get session status: {str(e)}")
            raise
    
    async def _check_critical_values(self, test_result: Any) -> List[str]:
        """Check for critical values in test results."""
        alerts = []
        
        try:
            # Check based on test result type
            if hasattr(test_result, 'urgency_level'):
                if test_result.urgency_level == UrgencyLevel.CRITICAL:
                    alerts.append(f"CRITICAL: {type(test_result).__name__} result requires immediate attention")
                elif test_result.urgency_level == UrgencyLevel.HIGH:
                    alerts.append(f"HIGH PRIORITY: {type(test_result).__name__} result needs prompt review")
            
            # Specific checks for different test types
            if hasattr(test_result, 'test_value'):
                # Blood glucose critical values
                if hasattr(test_result, 'strip_config') and test_result.strip_config.test_type == 'glucose':
                    if test_result.test_value < 40:
                        alerts.append("CRITICAL: Severe hypoglycemia detected")
                    elif test_result.test_value > 400:
                        alerts.append("CRITICAL: Severe hyperglycemia detected")
            
        except Exception as e:
            self.logger.error(f"Failed to check critical values: {str(e)}")
        
        return alerts
    
    async def _update_session_quality_score(self, session: POCTSession):
        """Update the overall quality score for a session."""
        try:
            quality_scores = []
            
            for result in session.individual_results:
                if hasattr(result, 'confidence_score'):
                    quality_scores.append(result.confidence_score)
                elif hasattr(result, 'ai_confidence_score'):
                    quality_scores.append(result.ai_confidence_score)
            
            if quality_scores:
                session.session_quality_score = sum(quality_scores) / len(quality_scores)
            else:
                session.session_quality_score = 0.5  # Default
                
        except Exception as e:
            self.logger.error(f"Failed to update session quality score: {str(e)}")
    
    async def _generate_final_actions(self, session: POCTSession) -> List[str]:
        """Generate final actions based on session results."""
        actions = []
        
        try:
            # Check if integrated analysis provides recommendations
            if session.integrated_analysis:
                actions.extend(session.integrated_analysis.immediate_actions)
            
            # Add workflow-specific actions
            workflow = session.workflow
            for test_type in session.completed_tests:
                if test_type in workflow.normal_value_actions:
                    actions.extend(workflow.normal_value_actions[test_type])
            
            # Remove duplicates
            actions = list(set(actions))
            
        except Exception as e:
            self.logger.error(f"Failed to generate final actions: {str(e)}")
        
        return actions
    
    async def _update_healthcare_record(self, session: POCTSession):
        """Update patient healthcare record with POCT results."""
        try:
            # Create record entry for POCT session
            record_data = {
                "patient_id": session.patient_id,
                "encounter_type": "point_of_care_testing",
                "encounter_date": session.start_timestamp.isoformat(),
                "location": session.location,
                "tests_performed": session.completed_tests,
                "final_disposition": session.final_disposition,
                "quality_score": session.session_quality_score
            }
            
            # Add individual test results
            if session.individual_results:
                record_data["test_results"] = [
                    result.dict() if hasattr(result, 'dict') else str(result)
                    for result in session.individual_results
                ]
            
            # Add integrated analysis if available
            if session.integrated_analysis:
                record_data["integrated_analysis"] = session.integrated_analysis.dict()
            
            # Update healthcare record
            await self.healthcare_service.add_encounter_record(record_data)
            
        except Exception as e:
            self.logger.error(f"Failed to update healthcare record: {str(e)}")
    
    async def get_workflow_definitions(self) -> List[POCTWorkflow]:
        """Get all available POCT workflow definitions."""
        return list(self.workflows.values())
    
    async def create_custom_workflow(self, workflow_data: Dict[str, Any]) -> POCTWorkflow:
        """
        Create a custom POCT workflow.
        
        Args:
            workflow_data: Workflow configuration data
            
        Returns:
            Created workflow
        """
        try:
            workflow = POCTWorkflow(**workflow_data)
            self.workflows[workflow.workflow_id] = workflow
            
            self.logger.info(
                "Custom POCT workflow created",
                workflow_id=workflow.workflow_id,
                workflow_name=workflow.workflow_name
            )
            
            return workflow
            
        except Exception as e:
            self.logger.error(f"Failed to create custom workflow: {str(e)}")
            raise
    
    async def get_analytics_dashboard(self) -> Dict[str, Any]:
        """
        Get POCT analytics dashboard data.
        
        Returns:
            Analytics dashboard information
        """
        try:
            total_devices = len(self.registered_devices)
            online_devices = sum(1 for status in self.device_status.values() if status.is_online)
            
            total_sessions_today = len([
                s for s in {**self.active_sessions, **self.completed_sessions}.values()
                if s.start_timestamp.date() == datetime.utcnow().date()
            ])
            
            active_sessions_count = len(self.active_sessions)
            
            # Calculate average session quality
            completed_today = [
                s for s in self.completed_sessions.values()
                if s.end_timestamp and s.end_timestamp.date() == datetime.utcnow().date()
            ]
            avg_quality = sum(s.session_quality_score for s in completed_today) / len(completed_today) if completed_today else 0
            
            return {
                "device_metrics": {
                    "total_devices": total_devices,
                    "online_devices": online_devices,
                    "offline_devices": total_devices - online_devices,
                    "device_uptime_percentage": (online_devices / total_devices * 100) if total_devices > 0 else 0
                },
                "session_metrics": {
                    "sessions_today": total_sessions_today,
                    "active_sessions": active_sessions_count,
                    "completed_sessions": len(completed_today),
                    "average_session_quality": avg_quality
                },
                "workflow_metrics": {
                    "available_workflows": len(self.workflows),
                    "most_used_workflow": "emergency_poct"  # Simplified
                },
                "quality_metrics": {
                    "devices_needing_qc": len([
                        d for d, status in self.device_status.items()
                        if status.error_status == "QC_FAILED"
                    ]),
                    "average_test_quality": avg_quality
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get analytics dashboard: {str(e)}")
            raise