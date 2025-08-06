"""
Collaboration Engine for A2A Healthcare Platform V2.0

Orchestrates medical agent collaboration with real-time coordination,
case distribution, and quality monitoring. Ensures HIPAA/SOC2 compliance
throughout the collaboration lifecycle.
"""

import asyncio
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

# Import existing healthcare platform components
from app.core.database_unified import get_db, AuditEventType
from app.modules.audit_logger.service import audit_logger
from app.modules.mcp.protocol import MCPProtocol
from app.modules.mcp.schemas import ConsultationRequest as MCPConsultationRequest
from app.core.config import get_settings

# Import A2A components
from .schemas import (
    CollaborationRequest, CollaborationResponse, AgentCollaboration,
    CollaborationStatus, MedicalSpecialty, ConsensusType,
    AgentRecommendation
)
from .models import A2ACollaborationSession, A2AAgentInteraction
from .medical_agents import MedicalAgentFactory
from .consensus import ConsensusEngine

logger = structlog.get_logger()
settings = get_settings()

class CollaborationSession:
    """
    Individual collaboration session managing agent interactions.
    
    Tracks the lifecycle of a single medical case collaboration from
    initiation through consensus with full audit trail.
    """
    
    def __init__(self, collaboration_id: str, request: CollaborationRequest):
        self.collaboration_id = collaboration_id
        self.request = request
        self.status = CollaborationStatus.INITIALIZING
        self.responses: List[CollaborationResponse] = []
        self.participating_agents: Set[str] = set()
        self.start_time = datetime.utcnow()
        self.timeout_task: Optional[asyncio.Task] = None
        self.consensus_result = None
        
        # Performance tracking
        self.total_processing_time = 0.0
        self.fastest_response = float('inf')
        self.slowest_response = 0.0
        
    async def start_collaboration(self, collaboration_engine: 'CollaborationEngine') -> None:
        """Start the collaboration session."""
        try:
            logger.info("Starting collaboration session",
                       collaboration_id=self.collaboration_id,
                       case_id=self.request.case_id,
                       urgency=self.request.urgency_level)
            
            self.status = CollaborationStatus.ACTIVE
            
            # Find appropriate agents for collaboration
            target_agents = await collaboration_engine._select_collaboration_agents(self.request)
            
            if not target_agents:
                raise ValueError("No suitable agents found for collaboration")
            
            self.participating_agents = set(agent_id for agent_id, _ in target_agents)
            
            # Set up timeout
            timeout_minutes = self.request.max_response_time_minutes
            self.timeout_task = asyncio.create_task(
                self._handle_timeout(timeout_minutes, collaboration_engine)
            )
            
            # Send collaboration requests to agents
            await self._send_collaboration_requests(target_agents, collaboration_engine)
            
            # Update status
            self.status = CollaborationStatus.WAITING_FOR_RESPONSES
            
            # Log session start
            await audit_logger.log_event(
                event_type=AuditEventType.COLLABORATION_STARTED,
                user_id=self.request.requesting_agent,
                resource_type="collaboration_session",
                resource_id=self.collaboration_id,
                action="collaboration_started",
                details={
                    "case_id": self.request.case_id,
                    "participating_agents": list(self.participating_agents),
                    "requested_specialties": self.request.requested_specialties,
                    "urgency_level": self.request.urgency_level
                }
            )
            
        except Exception as e:
            self.status = CollaborationStatus.FAILED
            logger.error("Failed to start collaboration session",
                        collaboration_id=self.collaboration_id,
                        error=str(e))
            raise
    
    async def _send_collaboration_requests(self, 
                                         target_agents: List[tuple], 
                                         collaboration_engine: 'CollaborationEngine') -> None:
        """Send collaboration requests to selected agents."""
        
        request_tasks = []
        
        for agent_id, specialty in target_agents:
            task = asyncio.create_task(
                self._request_agent_collaboration(agent_id, specialty, collaboration_engine)
            )
            request_tasks.append(task)
        
        # Wait for all requests to be sent (not for responses)
        await asyncio.gather(*request_tasks, return_exceptions=True)
    
    async def _request_agent_collaboration(self, 
                                         agent_id: str, 
                                         specialty: MedicalSpecialty,
                                         collaboration_engine: 'CollaborationEngine') -> None:
        """Request collaboration from a specific agent."""
        try:
            # Get the medical agent
            agent = await MedicalAgentFactory.get_agent(specialty)
            
            # Process the collaboration request
            response_start_time = datetime.utcnow()
            recommendation = await agent.process_collaboration_request(self.request)
            response_time = (datetime.utcnow() - response_start_time).total_seconds() * 1000
            
            # Create collaboration response
            collaboration_response = CollaborationResponse(
                collaboration_id=self.collaboration_id,
                responding_agent=agent_id,
                recommendation=recommendation,
                processing_time_ms=response_time
            )
            
            # Add response to session
            await self._add_response(collaboration_response)
            
            # Check if we have enough responses for consensus
            await self._check_consensus_readiness(collaboration_engine)
            
        except Exception as e:
            logger.error("Agent collaboration request failed",
                        collaboration_id=self.collaboration_id,
                        agent_id=agent_id,
                        error=str(e))
            
            # Continue with other agents even if one fails
    
    async def _add_response(self, response: CollaborationResponse) -> None:
        """Add agent response to the collaboration session."""
        self.responses.append(response)
        
        # Update performance metrics
        response_time = response.processing_time_ms
        self.fastest_response = min(self.fastest_response, response_time)
        self.slowest_response = max(self.slowest_response, response_time)
        self.total_processing_time += response_time
        
        logger.info("Received agent response",
                   collaboration_id=self.collaboration_id,
                   agent_id=response.responding_agent,
                   confidence=response.recommendation.overall_confidence,
                   response_time_ms=response_time,
                   total_responses=len(self.responses))
    
    async def _check_consensus_readiness(self, collaboration_engine: 'CollaborationEngine') -> None:
        """Check if enough responses received for consensus analysis."""
        
        # Minimum responses needed (at least 2, or 60% of expected agents)
        min_responses = max(2, int(len(self.participating_agents) * 0.6))
        
        if len(self.responses) >= min_responses:
            # We have enough responses - proceed to consensus
            await self._initiate_consensus_analysis(collaboration_engine)
    
    async def _initiate_consensus_analysis(self, collaboration_engine: 'CollaborationEngine') -> None:
        """Initiate consensus analysis with available responses."""
        
        if self.status != CollaborationStatus.WAITING_FOR_RESPONSES:
            return  # Already processed
        
        try:
            logger.info("Initiating consensus analysis",
                       collaboration_id=self.collaboration_id,
                       response_count=len(self.responses))
            
            self.status = CollaborationStatus.ANALYZING_CONSENSUS
            
            # Cancel timeout task if running
            if self.timeout_task and not self.timeout_task.done():
                self.timeout_task.cancel()
            
            # Run consensus analysis
            consensus_engine = ConsensusEngine()
            self.consensus_result = await consensus_engine.analyze_consensus(
                self.collaboration_id,
                self.responses,
                self.request.consensus_mechanism
            )
            
            # Update session status
            if self.consensus_result.consensus_reached:
                self.status = CollaborationStatus.COMPLETED
            else:
                # Check if human review is required
                if self.consensus_result.requires_human_review:
                    self.status = CollaborationStatus.ESCALATED
                else:
                    self.status = CollaborationStatus.COMPLETED  # Completed without consensus
            
            # Store collaboration results
            await self._store_collaboration_results()
            
            # Notify completion
            await collaboration_engine._handle_collaboration_completion(self)
            
        except Exception as e:
            self.status = CollaborationStatus.FAILED
            logger.error("Consensus analysis failed",
                        collaboration_id=self.collaboration_id,
                        error=str(e))
    
    async def _handle_timeout(self, timeout_minutes: int, collaboration_engine: 'CollaborationEngine') -> None:
        """Handle collaboration timeout."""
        try:
            await asyncio.sleep(timeout_minutes * 60)  # Convert to seconds
            
            if self.status in [CollaborationStatus.WAITING_FOR_RESPONSES, CollaborationStatus.ACTIVE]:
                logger.warning("Collaboration session timed out",
                             collaboration_id=self.collaboration_id,
                             responses_received=len(self.responses),
                             timeout_minutes=timeout_minutes)
                
                if len(self.responses) >= 2:
                    # We have some responses - try consensus with what we have
                    await self._initiate_consensus_analysis(collaboration_engine)
                else:
                    # Not enough responses - mark as timed out
                    self.status = CollaborationStatus.TIMED_OUT
                    await collaboration_engine._handle_collaboration_completion(self)
        
        except asyncio.CancelledError:
            # Timeout was cancelled (normal when consensus reached early)
            pass
        except Exception as e:
            logger.error("Error handling collaboration timeout",
                        collaboration_id=self.collaboration_id,
                        error=str(e))
    
    async def _store_collaboration_results(self) -> None:
        """Store collaboration session results in database."""
        try:
            async with get_db() as db:
                # Calculate session metrics
                completion_time = datetime.utcnow()
                total_session_time = (completion_time - self.start_time).total_seconds() * 1000
                average_response_time = self.total_processing_time / len(self.responses) if self.responses else 0
                
                # Create or update collaboration session record
                session_record = A2ACollaborationSession(
                    collaboration_id=self.collaboration_id,
                    case_id=self.request.case_id,
                    requesting_agent=self.request.requesting_agent,
                    participating_agents=list(self.participating_agents),
                    total_participants=len(self.participating_agents),
                    collaboration_type=self.request.collaboration_type,
                    consensus_mechanism=self.request.consensus_mechanism.value,
                    max_response_time_minutes=self.request.max_response_time_minutes,
                    urgency_level=self.request.urgency_level,
                    patient_age=self.request.patient_age,
                    patient_gender=self.request.patient_gender,
                    patient_id_hash=self.request.patient_id_hash,
                    case_summary=self.request.case_summary,
                    chief_complaint=self.request.chief_complaint,
                    symptoms=self.request.symptoms,
                    vital_signs=self.request.vital_signs,
                    lab_results=self.request.lab_results,
                    imaging_results=self.request.imaging_results,
                    medical_history=self.request.medical_history,
                    current_medications=self.request.current_medications,
                    allergies=self.request.allergies,
                    requested_specialties=[s.value for s in self.request.requested_specialties],
                    clinical_questions=self.request.clinical_questions,
                    diagnostic_uncertainty=self.request.diagnostic_uncertainty,
                    treatment_dilemmas=self.request.treatment_dilemmas,
                    status=self.status.value,
                    responses_received=len(self.responses),
                    consensus_reached=self.consensus_result.consensus_reached if self.consensus_result else False,
                    human_review_required=self.consensus_result.requires_human_review if self.consensus_result else False,
                    escalation_triggered=self.consensus_result.escalation_triggered if self.consensus_result else False,
                    agreement_score=self.consensus_result.agreement_level if self.consensus_result else 0.0,
                    confidence_variance=self.consensus_result.confidence_standard_deviation if self.consensus_result else 0.0,
                    average_confidence=self.consensus_result.average_confidence if self.consensus_result else 0.0,
                    weighted_confidence=self.consensus_result.weighted_confidence if self.consensus_result else 0.0,
                    total_processing_time_ms=total_session_time,
                    average_response_time_ms=average_response_time,
                    fastest_response_ms=self.fastest_response if self.fastest_response != float('inf') else 0,
                    slowest_response_ms=self.slowest_response,
                    final_recommendation=self.consensus_result.consensus_recommendation.model_dump() if self.consensus_result and self.consensus_result.consensus_recommendation else None,
                    minority_opinions=[op.model_dump() for op in self.consensus_result.minority_opinions] if self.consensus_result else [],
                    follow_up_actions=[],  # Would be populated based on recommendations
                    safety_concerns=self.consensus_result.safety_concerns if self.consensus_result else [],
                    fhir_resources=self.request.fhir_resources,
                    anonymized=self.request.anonymized,
                    consent_obtained=self.request.consent_obtained,
                    phi_access_reason=self.request.phi_access_reason,
                    phi_accessed=not self.request.anonymized,
                    started_at=self.start_time,
                    completed_at=completion_time,
                    expires_at=self.request.expires_at,
                    session_hash=self._generate_session_hash()
                )
                
                db.add(session_record)
                await db.commit()
                await db.refresh(session_record)
                
                # Store individual agent interactions
                for response in self.responses:
                    interaction_record = A2AAgentInteraction(
                        collaboration_id=self.collaboration_id,
                        agent_id=response.responding_agent,
                        agent_specialty=response.recommendation.specialty.value,
                        interaction_type="recommendation",
                        primary_assessment=response.recommendation.primary_assessment,
                        differential_diagnoses=[dx.model_dump() for dx in response.recommendation.differential_diagnoses],
                        treatment_recommendations=[tr.model_dump() for tr in response.recommendation.treatment_recommendations],
                        clinical_reasoning=response.recommendation.primary_assessment,  # Simplified
                        overall_confidence=response.recommendation.overall_confidence,
                        specialist_confidence=response.recommendation.specialist_confidence,
                        requires_further_evaluation=response.recommendation.requires_further_evaluation,
                        peer_review_requested=response.peer_review_requested,
                        human_oversight_recommended=response.human_oversight_recommended,
                        follow_up_timeline=response.recommendation.follow_up_timeline,
                        warning_signs=response.recommendation.warning_signs,
                        escalation_criteria=response.recommendation.escalation_criteria,
                        processing_time_ms=response.processing_time_ms,
                        knowledge_sources=response.recommendation.knowledge_sources,
                        phi_accessed=not self.request.anonymized,
                        phi_access_justified=self.request.consent_obtained,
                        submitted_at=response.timestamp,
                        interaction_hash=hashlib.sha256(response.model_dump_json().encode()).hexdigest()
                    )
                    
                    db.add(interaction_record)
                
                await db.commit()
                
        except Exception as e:
            logger.error("Failed to store collaboration results",
                        collaboration_id=self.collaboration_id,
                        error=str(e))
    
    def _generate_session_hash(self) -> str:
        """Generate cryptographic hash of session data for integrity."""
        session_data = {
            "collaboration_id": self.collaboration_id,
            "case_id": self.request.case_id,
            "responses_count": len(self.responses),
            "consensus_reached": self.consensus_result.consensus_reached if self.consensus_result else False,
            "completed_at": datetime.utcnow().isoformat()
        }
        
        return hashlib.sha256(str(session_data).encode()).hexdigest()
    
    def get_collaboration_summary(self) -> AgentCollaboration:
        """Get summary of the collaboration session."""
        return AgentCollaboration(
            collaboration_id=self.collaboration_id,
            case_id=self.request.case_id,
            status=self.status,
            requesting_agent=self.request.requesting_agent,
            participating_agents=list(self.participating_agents),
            request=self.request,
            responses=self.responses,
            consensus_reached=self.consensus_result.consensus_reached if self.consensus_result else False,
            consensus_mechanism=self.request.consensus_mechanism,
            final_recommendation=self.consensus_result.consensus_recommendation if self.consensus_result else None,
            agreement_score=self.consensus_result.agreement_level if self.consensus_result else 0.0,
            confidence_variance=self.consensus_result.confidence_standard_deviation if self.consensus_result else 0.0,
            response_time_ms=(datetime.utcnow() - self.start_time).total_seconds() * 1000,
            human_review_required=self.consensus_result.requires_human_review if self.consensus_result else False,
            escalation_reason=self.consensus_result.safety_concerns[0] if self.consensus_result and self.consensus_result.safety_concerns else None,
            started_at=self.start_time,
            completed_at=datetime.utcnow() if self.status in [CollaborationStatus.COMPLETED, CollaborationStatus.ESCALATED, CollaborationStatus.FAILED] else None
        )

class CollaborationEngine:
    """
    Main collaboration engine orchestrating agent-to-agent medical consultations.
    
    Manages the lifecycle of medical collaborations, agent selection, load balancing,
    and quality assurance across the healthcare AI agent network.
    """
    
    def __init__(self):
        self.active_sessions: Dict[str, CollaborationSession] = {}
        self.mcp_protocol: Optional[MCPProtocol] = None
        self.agent_load: Dict[str, int] = defaultdict(int)  # Track agent workload
        
        # Configuration
        self.max_concurrent_sessions_per_agent = 5
        self.default_collaboration_timeout_minutes = 30
        
    async def initialize(self) -> None:
        """Initialize the collaboration engine."""
        try:
            logger.info("Initializing A2A Collaboration Engine")
            
            # Initialize MCP protocol for agent communication
            self.mcp_protocol = MCPProtocol()
            await self.mcp_protocol.initialize()
            
            # Start background tasks
            asyncio.create_task(self._monitor_active_sessions())
            asyncio.create_task(self._cleanup_expired_sessions())
            
            # Log initialization
            await audit_logger.log_event(
                event_type=AuditEventType.SYSTEM_STARTUP,
                user_id="collaboration_engine",
                resource_type="a2a_collaboration_engine",
                action="engine_initialized",
                details={"component": "collaboration_engine"}
            )
            
            logger.info("A2A Collaboration Engine initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize A2A Collaboration Engine", error=str(e))
            raise
    
    async def initiate_collaboration(self, request: CollaborationRequest) -> str:
        """
        Initiate a new agent collaboration session.
        
        Args:
            request: Collaboration request with case details
            
        Returns:
            str: Collaboration ID for tracking
        """
        try:
            logger.info("Initiating collaboration",
                       collaboration_id=request.collaboration_id,
                       case_id=request.case_id,
                       requesting_agent=request.requesting_agent)
            
            # Validate collaboration request
            await self._validate_collaboration_request(request)
            
            # Create collaboration session
            session = CollaborationSession(request.collaboration_id, request)
            self.active_sessions[request.collaboration_id] = session
            
            # Start collaboration asynchronously
            asyncio.create_task(session.start_collaboration(self))
            
            return request.collaboration_id
            
        except Exception as e:
            logger.error("Failed to initiate collaboration",
                        collaboration_id=request.collaboration_id,
                        error=str(e))
            raise
    
    async def get_collaboration_status(self, collaboration_id: str) -> Optional[AgentCollaboration]:
        """Get status of an active collaboration session."""
        session = self.active_sessions.get(collaboration_id)
        if session:
            return session.get_collaboration_summary()
        
        # Check database for completed sessions
        async with get_db() as db:
            result = await db.execute(
                select(A2ACollaborationSession).where(
                    A2ACollaborationSession.collaboration_id == collaboration_id
                )
            )
            db_session = result.scalar_one_or_none()
            
            if db_session:
                # Convert database record to AgentCollaboration
                return await self._convert_db_session_to_collaboration(db_session)
        
        return None
    
    async def list_active_collaborations(self) -> List[AgentCollaboration]:
        """List all currently active collaboration sessions."""
        active_collaborations = []
        
        for session in self.active_sessions.values():
            active_collaborations.append(session.get_collaboration_summary())
        
        return active_collaborations
    
    async def cancel_collaboration(self, collaboration_id: str, reason: str = "User cancellation") -> bool:
        """Cancel an active collaboration session."""
        session = self.active_sessions.get(collaboration_id)
        if not session:
            return False
        
        try:
            # Cancel timeout task
            if session.timeout_task and not session.timeout_task.done():
                session.timeout_task.cancel()
            
            # Update session status
            session.status = CollaborationStatus.FAILED
            
            # Log cancellation
            await audit_logger.log_event(
                event_type=AuditEventType.COLLABORATION_CANCELLED,
                user_id=session.request.requesting_agent,
                resource_type="collaboration_session",
                resource_id=collaboration_id,
                action="collaboration_cancelled",
                details={"reason": reason}
            )
            
            # Clean up
            await self._cleanup_session(collaboration_id)
            
            return True
            
        except Exception as e:
            logger.error("Failed to cancel collaboration",
                        collaboration_id=collaboration_id,
                        error=str(e))
            return False
    
    async def _validate_collaboration_request(self, request: CollaborationRequest) -> None:
        """Validate collaboration request meets requirements."""
        # Check required fields
        if not request.case_summary:
            raise ValueError("Case summary is required")
        
        if not request.chief_complaint:
            raise ValueError("Chief complaint is required")
        
        # Validate PHI handling
        if not request.anonymized and not request.consent_obtained:
            raise ValueError("Patient consent required for non-anonymized data")
        
        # Check reasonable timeout
        if request.max_response_time_minutes > 180:  # 3 hours max
            raise ValueError("Collaboration timeout too long (max 3 hours)")
        
        # Validate requested specialties
        if len(request.requested_specialties) > 8:
            raise ValueError("Too many specialties requested (max 8)")
    
    async def _select_collaboration_agents(self, request: CollaborationRequest) -> List[tuple]:
        """Select appropriate agents for collaboration based on request."""
        selected_agents = []
        
        # If specific specialties requested, prioritize those
        for specialty in request.requested_specialties:
            agent_id = f"{specialty.value}_agent_v1"
            
            # Check agent load
            if self.agent_load[agent_id] < self.max_concurrent_sessions_per_agent:
                selected_agents.append((agent_id, specialty))
                self.agent_load[agent_id] += 1
        
        # If no specific specialties or need more agents, add general medical agents
        if len(selected_agents) < 2:
            # Add internal medicine as baseline
            internal_med_id = "internal_medicine_agent_v1"
            if self.agent_load[internal_med_id] < self.max_concurrent_sessions_per_agent:
                selected_agents.append((internal_med_id, MedicalSpecialty.INTERNAL_MEDICINE))
                self.agent_load[internal_med_id] += 1
            
            # Add emergency medicine for urgent cases
            if request.urgency_level in ["urgent", "critical", "emergency"]:
                emergency_id = "emergency_agent_v1"
                if self.agent_load[emergency_id] < self.max_concurrent_sessions_per_agent:
                    selected_agents.append((emergency_id, MedicalSpecialty.EMERGENCY_MEDICINE))
                    self.agent_load[emergency_id] += 1
        
        return selected_agents
    
    async def _handle_collaboration_completion(self, session: CollaborationSession) -> None:
        """Handle completion of a collaboration session."""
        try:
            # Reduce agent load counts
            for agent_id in session.participating_agents:
                self.agent_load[agent_id] = max(0, self.agent_load[agent_id] - 1)
            
            # Log completion
            await audit_logger.log_event(
                event_type=AuditEventType.COLLABORATION_COMPLETED,
                user_id=session.request.requesting_agent,
                resource_type="collaboration_session",
                resource_id=session.collaboration_id,
                action="collaboration_completed",
                details={
                    "status": session.status.value,
                    "consensus_reached": session.consensus_result.consensus_reached if session.consensus_result else False,
                    "responses_received": len(session.responses),
                    "total_time_ms": (datetime.utcnow() - session.start_time).total_seconds() * 1000
                }
            )
            
            # Clean up session after delay (keep for a while for status queries)
            asyncio.create_task(self._delayed_session_cleanup(session.collaboration_id, delay_minutes=60))
            
        except Exception as e:
            logger.error("Error handling collaboration completion",
                        collaboration_id=session.collaboration_id,
                        error=str(e))
    
    async def _delayed_session_cleanup(self, collaboration_id: str, delay_minutes: int = 60) -> None:
        """Clean up session after delay."""
        await asyncio.sleep(delay_minutes * 60)
        await self._cleanup_session(collaboration_id)
    
    async def _cleanup_session(self, collaboration_id: str) -> None:
        """Clean up collaboration session."""
        if collaboration_id in self.active_sessions:
            session = self.active_sessions[collaboration_id]
            
            # Cancel any running tasks
            if session.timeout_task and not session.timeout_task.done():
                session.timeout_task.cancel()
            
            # Remove from active sessions
            del self.active_sessions[collaboration_id]
    
    async def _convert_db_session_to_collaboration(self, db_session: A2ACollaborationSession) -> AgentCollaboration:
        """Convert database session record to AgentCollaboration object."""
        # This is a simplified conversion - in practice would need to reconstruct full objects
        return AgentCollaboration(
            collaboration_id=db_session.collaboration_id,
            case_id=db_session.case_id,
            status=CollaborationStatus(db_session.status),
            requesting_agent=db_session.requesting_agent,
            participating_agents=db_session.participating_agents or [],
            request=None,  # Would need to reconstruct from stored data
            responses=[],  # Would need to load from A2AAgentInteraction table
            consensus_reached=db_session.consensus_reached,
            consensus_mechanism=ConsensusType(db_session.consensus_mechanism),
            agreement_score=db_session.agreement_score,
            confidence_variance=db_session.confidence_variance,
            response_time_ms=db_session.total_processing_time_ms,
            human_review_required=db_session.human_review_required,
            started_at=db_session.started_at,
            completed_at=db_session.completed_at
        )
    
    # Background monitoring tasks
    
    async def _monitor_active_sessions(self) -> None:
        """Monitor active collaboration sessions for health and performance."""
        while True:
            try:
                current_time = datetime.utcnow()
                
                # Check for sessions running too long
                long_running_sessions = []
                for collaboration_id, session in self.active_sessions.items():
                    session_duration = (current_time - session.start_time).total_seconds() / 60  # minutes
                    
                    if session_duration > 60:  # 1 hour threshold
                        long_running_sessions.append((collaboration_id, session_duration))
                
                if long_running_sessions:
                    logger.warning("Long-running collaboration sessions detected",
                                 count=len(long_running_sessions),
                                 sessions=long_running_sessions)
                
                # Log metrics
                logger.info("Active collaboration sessions",
                           active_count=len(self.active_sessions),
                           total_agent_load=sum(self.agent_load.values()))
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error("Error in session monitoring", error=str(e))
                await asyncio.sleep(300)
    
    async def _cleanup_expired_sessions(self) -> None:
        """Clean up expired collaboration sessions."""
        while True:
            try:
                current_time = datetime.utcnow()
                expired_sessions = []
                
                for collaboration_id, session in self.active_sessions.items():
                    # Sessions older than 4 hours are considered expired
                    if (current_time - session.start_time) > timedelta(hours=4):
                        expired_sessions.append(collaboration_id)
                
                # Clean up expired sessions
                for collaboration_id in expired_sessions:
                    logger.info("Cleaning up expired collaboration session",
                               collaboration_id=collaboration_id)
                    await self._cleanup_session(collaboration_id)
                
                await asyncio.sleep(3600)  # Check every hour
                
            except Exception as e:
                logger.error("Error in expired session cleanup", error=str(e))
                await asyncio.sleep(3600)
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the collaboration engine."""
        logger.info("Shutting down A2A Collaboration Engine")
        
        # Cancel all active sessions
        for collaboration_id in list(self.active_sessions.keys()):
            await self.cancel_collaboration(collaboration_id, "System shutdown")
        
        # Shutdown MCP protocol
        if self.mcp_protocol:
            await self.mcp_protocol.shutdown()
        
        logger.info("A2A Collaboration Engine shutdown complete")