"""
Doctor History Service - Business Logic for Linked Medical Timeline
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, text, join
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
import uuid
import structlog
from collections import defaultdict

from app.core.database_unified import (
    Patient, AuditLog, User, Consent,
    get_db, HealthcareSessionManager
)
from app.core.security import encryption_service, SecurityManager
from app.core.exceptions import ResourceNotFound, UnauthorizedAccess
from app.modules.doctor_history.schemas import (
    MedicalEventBase, LinkedTimelineEvent, CaseSummary, DoctorHistoryResponse,
    LinkedTimelineResponse, CareCycle, CareCyclesResponse, EventType, 
    EventPriority, CarePhase, TimelineFilters
)

logger = structlog.get_logger()


class DoctorHistoryService:
    """Service for doctor history mode and linked medical timeline."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.security_manager = SecurityManager()
    
    async def get_case_history(
        self, 
        case_id: uuid.UUID, 
        user_id: str,
        filters: Optional[TimelineFilters] = None
    ) -> DoctorHistoryResponse:
        """
        Get comprehensive case history for doctor review.
        
        Args:
            case_id: Medical case identifier
            user_id: Requesting doctor user ID
            filters: Optional timeline filters
            
        Returns:
            DoctorHistoryResponse: Complete case history with timeline
        """
        try:
            # Verify user has doctor role and case access
            await self._verify_case_access(case_id, user_id)
            
            # Get case summary
            case_summary = await self._build_case_summary(case_id)
            
            # Get timeline events
            timeline_events = await self._get_timeline_events(case_id, filters)
            
            # Get patient demographics (encrypted)
            patient_demographics = await self._get_patient_demographics(case_summary.patient_id)
            
            # Build care context
            care_context = await self._build_care_context(case_id)
            
            # Calculate date range
            if timeline_events:
                date_range = {
                    "start": min(event.event_date for event in timeline_events),
                    "end": max(event.event_date for event in timeline_events)
                }
            else:
                date_range = {
                    "start": case_summary.start_date,
                    "end": case_summary.last_updated
                }
            
            return DoctorHistoryResponse(
                case_summary=case_summary,
                timeline_events=timeline_events,
                patient_demographics=patient_demographics,
                care_context=care_context,
                total_events=len(timeline_events),
                date_range=date_range
            )
            
        except Exception as e:
            logger.error(f"Error getting case history: {str(e)}", case_id=str(case_id))
            raise
    
    async def get_linked_timeline(
        self,
        case_id: uuid.UUID,
        user_id: str,
        filters: Optional[TimelineFilters] = None
    ) -> LinkedTimelineResponse:
        """
        Get linked medical timeline with event correlations.
        
        Args:
            case_id: Medical case identifier
            user_id: Requesting doctor user ID
            filters: Optional timeline filters
            
        Returns:
            LinkedTimelineResponse: Enhanced timeline with linking analysis
        """
        try:
            # Verify access
            await self._verify_case_access(case_id, user_id)
            
            # Get enhanced timeline events
            linked_events = await self._get_linked_timeline_events(case_id, filters)
            
            # Perform correlation analysis
            event_correlations = await self._analyze_event_correlations(linked_events)
            
            # Identify care transitions
            care_transitions = await self._identify_care_transitions(linked_events)
            
            # Identify critical pathways
            critical_paths = await self._identify_critical_paths(linked_events)
            
            # Get patient ID from case
            case_summary = await self._build_case_summary(case_id)
            
            # Timeline metadata
            if linked_events:
                timeline_start = min(event.event_date for event in linked_events)
                timeline_end = max(event.event_date for event in linked_events)
            else:
                timeline_start = datetime.utcnow()
                timeline_end = datetime.utcnow()
            
            return LinkedTimelineResponse(
                case_id=case_id,
                patient_id=case_summary.patient_id,
                timeline_events=linked_events,
                event_correlations=event_correlations,
                care_transitions=care_transitions,
                critical_paths=critical_paths,
                timeline_start=timeline_start,
                timeline_end=timeline_end,
                total_linked_events=len(linked_events)
            )
            
        except Exception as e:
            logger.error(f"Error getting linked timeline: {str(e)}", case_id=str(case_id))
            raise
    
    async def get_care_cycles(
        self,
        patient_id: uuid.UUID,
        user_id: str,
        include_completed: bool = True
    ) -> CareCyclesResponse:
        """
        Get patient care cycles for care management.
        
        Args:
            patient_id: Patient identifier
            user_id: Requesting doctor user ID
            include_completed: Whether to include completed cycles
            
        Returns:
            CareCyclesResponse: Patient care cycles and analytics
        """
        try:
            # Verify patient access
            await self._verify_patient_access(patient_id, user_id)
            
            # Get active care cycles
            active_cycles = await self._get_care_cycles(patient_id, active_only=True)
            
            # Get completed cycles if requested
            completed_cycles = []
            if include_completed:
                completed_cycles = await self._get_care_cycles(patient_id, completed_only=True)
            
            # Calculate analytics
            total_active = len(active_cycles)
            total_completed = len(completed_cycles)
            
            # Average cycle duration
            avg_duration = None
            if completed_cycles:
                durations = []
                for cycle in completed_cycles:
                    if cycle.actual_end_date:
                        duration = (cycle.actual_end_date - cycle.start_date).days
                        durations.append(duration)
                if durations:
                    avg_duration = sum(durations) / len(durations)
            
            # Care complexity assessment
            complexity_score = await self._calculate_care_complexity(patient_id)
            
            # Primary care areas
            primary_care_areas = await self._get_primary_care_areas(patient_id)
            
            # Care coordination notes
            coordination_notes = await self._get_care_coordination_notes(patient_id)
            
            return CareCyclesResponse(
                patient_id=patient_id,
                active_cycles=active_cycles,
                completed_cycles=completed_cycles,
                total_active_cycles=total_active,
                total_completed_cycles=total_completed,
                average_cycle_duration=avg_duration,
                care_complexity_score=complexity_score,
                primary_care_areas=primary_care_areas,
                care_coordination_notes=coordination_notes
            )
            
        except Exception as e:
            logger.error(f"Error getting care cycles: {str(e)}", patient_id=str(patient_id))
            raise
    
    # Private helper methods
    
    async def _verify_case_access(self, case_id: uuid.UUID, user_id: str) -> None:
        """Verify user has access to the medical case."""
        try:
            # Check if user has doctor role
            user_query = select(User).where(User.id == user_id)
            result = await self.db.execute(user_query)
            user = result.scalar_one_or_none()
            
            if not user:
                raise UnauthorizedAccess("User not found")
            
            # For now, assume doctors can access cases they're involved in
            # In production, this would check case assignments, care team membership, etc.
            if not user.role or user.role.lower() not in ['doctor', 'physician', 'admin']:
                raise UnauthorizedAccess("Insufficient privileges for case access")
                
        except Exception as e:
            logger.error(f"Case access verification failed: {str(e)}")
            raise
    
    async def _verify_patient_access(self, patient_id: uuid.UUID, user_id: str) -> None:
        """Verify user has access to patient data."""
        try:
            # Similar verification for patient access
            user_query = select(User).where(User.id == user_id)
            result = await self.db.execute(user_query)
            user = result.scalar_one_or_none()
            
            if not user:
                raise UnauthorizedAccess("User not found")
            
            if not user.role or user.role.lower() not in ['doctor', 'physician', 'admin']:
                raise UnauthorizedAccess("Insufficient privileges for patient access")
                
        except Exception as e:
            logger.error(f"Patient access verification failed: {str(e)}")
            raise
    
    async def _build_case_summary(self, case_id: uuid.UUID) -> CaseSummary:
        """Build case summary from available data."""
        # For now, create a mock case summary
        # In production, this would query actual case tables
        return CaseSummary(
            case_id=case_id,
            patient_id=uuid.uuid4(),  # Would be from actual case data
            case_title="Sample Medical Case",
            case_status="Active",
            start_date=datetime.utcnow() - timedelta(days=30),
            last_updated=datetime.utcnow(),
            primary_diagnosis="Sample Diagnosis",
            secondary_diagnoses=["Secondary Diagnosis 1"],
            attending_physician="Dr. Smith",
            care_team=["Dr. Smith", "Nurse Johnson"],
            total_events=5,
            critical_events=1,
            last_critical_event=datetime.utcnow() - timedelta(days=7)
        )
    
    async def _get_timeline_events(
        self, 
        case_id: uuid.UUID, 
        filters: Optional[TimelineFilters] = None
    ) -> List[MedicalEventBase]:
        """Get timeline events for a case."""
        # Mock timeline events - in production would query actual medical event tables
        events = []
        base_date = datetime.utcnow() - timedelta(days=30)
        
        for i in range(5):
            event = MedicalEventBase(
                event_id=uuid.uuid4(),
                event_type=EventType.CONSULTATION if i % 2 == 0 else EventType.LAB_RESULT,
                title=f"Medical Event {i+1}",
                description=f"Description for medical event {i+1}",
                event_date=base_date + timedelta(days=i*7),
                priority=EventPriority.HIGH if i == 0 else EventPriority.MEDIUM,
                provider_name=f"Provider {i+1}",
                location="Medical Center",
                parent_case_id=case_id
            )
            events.append(event)
        
        # Apply filters if provided
        if filters:
            events = self._apply_timeline_filters(events, filters)
            
        return sorted(events, key=lambda x: x.event_date, reverse=True)
    
    async def _get_linked_timeline_events(
        self, 
        case_id: uuid.UUID, 
        filters: Optional[TimelineFilters] = None
    ) -> List[LinkedTimelineEvent]:
        """Get enhanced timeline events with linking information."""
        # Mock linked timeline events
        events = []
        base_date = datetime.utcnow() - timedelta(days=30)
        correlation_id = uuid.uuid4()
        
        for i in range(5):
            event = LinkedTimelineEvent(
                event_id=uuid.uuid4(),
                event_type=EventType.CONSULTATION if i % 2 == 0 else EventType.LAB_RESULT,
                title=f"Linked Medical Event {i+1}",
                description=f"Enhanced description for event {i+1}",
                event_date=base_date + timedelta(days=i*7),
                priority=EventPriority.HIGH if i == 0 else EventPriority.MEDIUM,
                provider_name=f"Provider {i+1}",
                location="Medical Center",
                parent_case_id=case_id,
                correlation_id=correlation_id if i < 2 else None,
                sequence_number=i+1,
                care_phase=CarePhase.ASSESSMENT if i < 2 else CarePhase.INTERVENTION,
                outcome_status="Completed" if i < 3 else "In Progress",
                clinical_data={"key": f"value_{i}"},
                diagnostic_codes=[f"ICD10-{i:03d}"],
                fhir_resource_type="Observation" if i % 2 == 0 else "DiagnosticReport"
            )
            events.append(event)
        
        if filters:
            events = self._apply_timeline_filters(events, filters)
            
        return sorted(events, key=lambda x: x.event_date, reverse=True)
    
    async def _get_patient_demographics(self, patient_id: uuid.UUID) -> Dict[str, Any]:
        """Get patient demographics (with proper encryption handling)."""
        try:
            query = select(Patient).where(Patient.id == patient_id)
            result = await self.db.execute(query)
            patient = result.scalar_one_or_none()
            
            if not patient:
                return {"error": "Patient not found"}
            
            # Return basic demographics (encrypted fields would be decrypted in production)
            return {
                "patient_id": str(patient.id),
                "date_of_birth": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
                "gender": patient.gender if hasattr(patient, 'gender') else None,
                "active_status": patient.active if hasattr(patient, 'active') else True,
                # Other demographics would be decrypted here in production
                "demographics_encrypted": True
            }
        except Exception as e:
            logger.error(f"Error getting patient demographics: {str(e)}")
            return {"error": "Unable to retrieve demographics"}
    
    async def _build_care_context(self, case_id: uuid.UUID) -> Dict[str, Any]:
        """Build care context information."""
        return {
            "care_setting": "Inpatient",
            "care_level": "Acute",
            "quality_measures": {
                "satisfaction_score": 4.5,
                "safety_incidents": 0,
                "readmission_risk": "Low"
            },
            "care_coordination": {
                "primary_coordinator": "Care Coordinator Smith",
                "active_consultations": 2,
                "pending_referrals": 1
            }
        }
    
    async def _get_care_cycles(
        self, 
        patient_id: uuid.UUID, 
        active_only: bool = False,
        completed_only: bool = False
    ) -> List[CareCycle]:
        """Get care cycles for a patient."""
        # Mock care cycles - in production would query actual care cycle tables
        cycles = []
        
        if not completed_only:
            # Active cycle
            active_cycle = CareCycle(
                cycle_id=uuid.uuid4(),
                patient_id=patient_id,
                cycle_name="Primary Care Management",
                care_phase=CarePhase.INTERVENTION,
                start_date=datetime.utcnow() - timedelta(days=60),
                target_end_date=datetime.utcnow() + timedelta(days=30),
                assessment_data={"assessment": "comprehensive"},
                care_plan={"plan": "integrated care"},
                interventions=[{"type": "medication", "status": "active"}],
                completion_percentage=75.0,
                milestones_achieved=["Assessment Complete", "Care Plan Approved"],
                pending_actions=["Follow-up Appointment", "Lab Results Review"],
                care_team_members=["Dr. Smith", "Nurse Johnson", "Care Coordinator Brown"]
            )
            cycles.append(active_cycle)
        
        if not active_only:
            # Completed cycle
            completed_cycle = CareCycle(
                cycle_id=uuid.uuid4(),
                patient_id=patient_id,
                cycle_name="Post-Surgical Care",
                care_phase=CarePhase.EVALUATION,
                start_date=datetime.utcnow() - timedelta(days=120),
                target_end_date=datetime.utcnow() - timedelta(days=30),
                actual_end_date=datetime.utcnow() - timedelta(days=25),
                assessment_data={"assessment": "post-operative"},
                care_plan={"plan": "recovery protocol"},
                interventions=[{"type": "physical therapy", "status": "completed"}],
                outcomes={"recovery": "excellent", "complications": "none"},
                completion_percentage=100.0,
                milestones_achieved=["Surgery Complete", "Recovery Goals Met", "Discharge Criteria Met"],
                quality_indicators={"infection_rate": 0, "patient_satisfaction": 4.8},
                patient_satisfaction=4.8,
                care_team_members=["Dr. Johnson", "PT Specialist", "Discharge Planner"]
            )
            cycles.append(completed_cycle)
        
        return cycles
    
    async def _analyze_event_correlations(self, events: List[LinkedTimelineEvent]) -> Dict[str, List[uuid.UUID]]:
        """Analyze correlations between timeline events."""
        correlations = defaultdict(list)
        
        # Group by correlation ID
        for event in events:
            if event.correlation_id:
                correlations[str(event.correlation_id)].append(event.event_id)
        
        # Add temporal correlations (events within 24 hours)
        temporal_groups = []
        sorted_events = sorted(events, key=lambda x: x.event_date)
        
        for i, event in enumerate(sorted_events):
            related_events = [event.event_id]
            for j, other_event in enumerate(sorted_events[i+1:], i+1):
                if abs((event.event_date - other_event.event_date).total_seconds()) <= 24 * 3600:
                    related_events.append(other_event.event_id)
            
            if len(related_events) > 1:
                correlations[f"temporal_group_{i}"] = related_events
        
        return dict(correlations)
    
    async def _identify_care_transitions(self, events: List[LinkedTimelineEvent]) -> List[Dict[str, Any]]:
        """Identify care transition points."""
        transitions = []
        
        # Look for care phase changes
        sorted_events = sorted(events, key=lambda x: x.event_date)
        for i in range(len(sorted_events) - 1):
            current = sorted_events[i]
            next_event = sorted_events[i + 1]
            
            if current.care_phase != next_event.care_phase:
                transitions.append({
                    "from_phase": current.care_phase,
                    "to_phase": next_event.care_phase,
                    "transition_date": next_event.event_date,
                    "from_event_id": str(current.event_id),
                    "to_event_id": str(next_event.event_id),
                    "transition_type": "care_phase_change"
                })
        
        return transitions
    
    async def _identify_critical_paths(self, events: List[LinkedTimelineEvent]) -> List[Dict[str, Any]]:
        """Identify critical care pathways."""
        critical_paths = []
        
        # Find sequences of high priority events
        high_priority_events = [e for e in events if e.priority == EventPriority.HIGH]
        
        if len(high_priority_events) >= 2:
            critical_paths.append({
                "pathway_name": "High Priority Care Sequence",
                "events": [str(e.event_id) for e in high_priority_events],
                "start_date": min(e.event_date for e in high_priority_events),
                "end_date": max(e.event_date for e in high_priority_events),
                "pathway_type": "priority_sequence",
                "risk_level": "high"
            })
        
        return critical_paths
    
    def _apply_timeline_filters(self, events: List, filters: TimelineFilters) -> List:
        """Apply filters to timeline events."""
        filtered_events = events
        
        if filters.event_types:
            filtered_events = [e for e in filtered_events if e.event_type in filters.event_types]
        
        if filters.priority_levels:
            filtered_events = [e for e in filtered_events if e.priority in filters.priority_levels]
        
        if filters.date_from:
            filtered_events = [e for e in filtered_events if e.event_date >= filters.date_from]
            
        if filters.date_to:
            filtered_events = [e for e in filtered_events if e.event_date <= filters.date_to]
        
        if filters.provider_filter:
            filtered_events = [e for e in filtered_events 
                             if filters.provider_filter.lower() in (e.provider_name or "").lower()]
        
        return filtered_events
    
    async def _calculate_care_complexity(self, patient_id: uuid.UUID) -> float:
        """Calculate care complexity score."""
        # Mock complexity calculation
        return 7.5  # Scale of 1-10
    
    async def _get_primary_care_areas(self, patient_id: uuid.UUID) -> List[str]:
        """Get primary care areas for the patient."""
        return ["Cardiology", "Endocrinology", "Primary Care"]
    
    async def _get_care_coordination_notes(self, patient_id: uuid.UUID) -> Optional[str]:
        """Get care coordination notes."""
        return "Patient requires coordinated care between cardiology and endocrinology teams. Regular monitoring needed."