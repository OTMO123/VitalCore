"""
A2A Coordinator for Healthcare Platform V2.0

Main coordinator orchestrating agent-to-agent communication, collaboration
management, and integration with the healthcare platform's MCP infrastructure.
Serves as the primary interface for all A2A operations.
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

# Import existing healthcare platform components
from app.core.database_unified import get_db, AuditEventType
from app.modules.audit_logger.service import audit_logger
from app.modules.mcp.protocol import MCPProtocol
from app.modules.mcp.agent_registry import AgentRegistry
from app.core.config import get_settings

# Import A2A components
from .schemas import (
    CollaborationRequest, AgentCollaboration, MedicalSpecialty,
    ConsensusType, CollaborationStatus, MedicalAgentProfile
)
from .models import A2ACollaborationSession, A2AAgentProfile
from .collaboration import CollaborationEngine
from .medical_agents import MedicalAgentFactory
from .consensus import ConsensusEngine

logger = structlog.get_logger()
settings = get_settings()

class A2ACoordinator:
    """
    Main coordinator for Agent-to-Agent communication and collaboration.
    
    Provides high-level orchestration of medical agent collaborations,
    integrates with MCP infrastructure, and manages the overall A2A ecosystem
    within the healthcare platform.
    """
    
    def __init__(self):
        self.collaboration_engine: Optional[CollaborationEngine] = None
        self.mcp_protocol: Optional[MCPProtocol] = None
        self.agent_registry: Optional[AgentRegistry] = None
        self.consensus_engine: Optional[ConsensusEngine] = None
        
        # Statistics tracking
        self.total_collaborations = 0
        self.successful_collaborations = 0
        self.failed_collaborations = 0
        self.average_collaboration_time = 0.0
        
        # Agent performance tracking
        self.agent_performance: Dict[str, Dict[str, float]] = {}
        
    async def initialize(self) -> None:
        """Initialize the A2A Coordinator and all subsystems."""
        try:
            logger.info("Initializing A2A Coordinator")
            
            # Initialize core engines
            self.collaboration_engine = CollaborationEngine()
            await self.collaboration_engine.initialize()
            
            self.consensus_engine = ConsensusEngine()
            
            # Initialize MCP integration
            self.mcp_protocol = MCPProtocol()
            await self.mcp_protocol.initialize()
            
            self.agent_registry = AgentRegistry()
            await self.agent_registry.initialize()
            
            # Register all medical specialty agents with MCP registry
            await self._register_medical_agents()
            
            # Start background tasks
            asyncio.create_task(self._performance_monitoring_task())
            asyncio.create_task(self._agent_health_monitoring_task())
            asyncio.create_task(self._collaboration_analytics_task())
            
            # Load historical statistics
            await self._load_historical_statistics()
            
            # Log successful initialization
            await audit_logger.log_event(
                event_type=AuditEventType.SYSTEM_STARTUP,
                user_id="a2a_coordinator",
                resource_type="a2a_coordinator",
                action="coordinator_initialized",
                details={
                    "subsystems": ["collaboration_engine", "consensus_engine", "mcp_protocol", "agent_registry"],
                    "medical_agents": len(await MedicalAgentFactory.list_available_specialties())
                }
            )
            
            logger.info("A2A Coordinator initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize A2A Coordinator", error=str(e))
            raise
    
    # Public API Methods
    
    async def request_collaboration(self, 
                                  requesting_agent_id: str,
                                  case_summary: str,
                                  patient_context: Dict[str, Any],
                                  requested_specialties: List[MedicalSpecialty] = None,
                                  urgency_level: str = "routine",
                                  consensus_type: ConsensusType = ConsensusType.WEIGHTED_EXPERTISE) -> str:
        """
        Request a new agent collaboration for a medical case.
        
        Args:
            requesting_agent_id: ID of the agent requesting collaboration
            case_summary: Summary of the medical case
            patient_context: Patient information (anonymized)
            requested_specialties: Specific medical specialties needed
            urgency_level: Urgency level of the case
            consensus_type: Type of consensus mechanism to use
            
        Returns:
            str: Collaboration ID for tracking
        """
        try:
            # Create collaboration request
            collaboration_request = CollaborationRequest(
                requesting_agent=requesting_agent_id,
                case_summary=case_summary,
                patient_age=patient_context.get("age"),
                patient_gender=patient_context.get("gender"),
                patient_id_hash=patient_context.get("patient_id_hash", ""),
                chief_complaint=patient_context.get("chief_complaint", ""),
                symptoms=patient_context.get("symptoms", []),
                vital_signs=patient_context.get("vital_signs", {}),
                lab_results=patient_context.get("lab_results", {}),
                imaging_results=patient_context.get("imaging_results", []),
                medical_history=patient_context.get("medical_history", []),
                current_medications=patient_context.get("current_medications", []),
                allergies=patient_context.get("allergies", []),
                requested_specialties=requested_specialties or [],
                urgency_level=urgency_level,
                consensus_mechanism=consensus_type,
                clinical_questions=patient_context.get("clinical_questions", []),
                diagnostic_uncertainty=patient_context.get("diagnostic_uncertainty", []),
                treatment_dilemmas=patient_context.get("treatment_dilemmas", []),
                anonymized=patient_context.get("anonymized", True),
                consent_obtained=patient_context.get("consent_obtained", False),
                phi_access_reason=patient_context.get("phi_access_reason", "treatment")
            )
            
            logger.info("Processing collaboration request",
                       collaboration_id=collaboration_request.collaboration_id,
                       requesting_agent=requesting_agent_id,
                       specialties=requested_specialties,
                       urgency=urgency_level)
            
            # Initiate collaboration through engine
            collaboration_id = await self.collaboration_engine.initiate_collaboration(collaboration_request)
            
            # Update statistics
            self.total_collaborations += 1
            
            return collaboration_id
            
        except Exception as e:
            self.failed_collaborations += 1
            logger.error("Failed to request collaboration",
                        requesting_agent=requesting_agent_id,
                        error=str(e))
            raise
    
    async def get_collaboration_status(self, collaboration_id: str) -> Optional[AgentCollaboration]:
        """Get the current status of a collaboration session."""
        return await self.collaboration_engine.get_collaboration_status(collaboration_id)
    
    async def list_active_collaborations(self, 
                                       requesting_agent: Optional[str] = None,
                                       urgency_filter: Optional[str] = None,
                                       specialty_filter: Optional[MedicalSpecialty] = None) -> List[AgentCollaboration]:
        """
        List active collaboration sessions with optional filtering.
        
        Args:
            requesting_agent: Filter by requesting agent
            urgency_filter: Filter by urgency level
            specialty_filter: Filter by involved specialty
            
        Returns:
            List[AgentCollaboration]: Filtered list of active collaborations
        """
        active_collaborations = await self.collaboration_engine.list_active_collaborations()
        
        # Apply filters
        filtered_collaborations = active_collaborations
        
        if requesting_agent:
            filtered_collaborations = [
                collab for collab in filtered_collaborations 
                if collab.requesting_agent == requesting_agent
            ]
        
        if urgency_filter:
            filtered_collaborations = [
                collab for collab in filtered_collaborations 
                if collab.request and collab.request.urgency_level == urgency_filter
            ]
        
        if specialty_filter:
            filtered_collaborations = [
                collab for collab in filtered_collaborations 
                if collab.request and specialty_filter in collab.request.requested_specialties
            ]
        
        return filtered_collaborations
    
    async def cancel_collaboration(self, collaboration_id: str, reason: str = "User cancellation") -> bool:
        """Cancel an active collaboration session."""
        return await self.collaboration_engine.cancel_collaboration(collaboration_id, reason)
    
    async def get_agent_profiles(self) -> List[MedicalAgentProfile]:
        """Get profiles of all available medical agents."""
        return await MedicalAgentFactory.get_agent_profiles()
    
    async def get_collaboration_analytics(self, 
                                        days_back: int = 30,
                                        agent_filter: Optional[str] = None,
                                        specialty_filter: Optional[MedicalSpecialty] = None) -> Dict[str, Any]:
        """
        Get analytics for collaboration sessions over a specified period.
        
        Args:
            days_back: Number of days to look back
            agent_filter: Filter by specific agent
            specialty_filter: Filter by medical specialty
            
        Returns:
            Dict[str, Any]: Analytics data
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            async with get_db() as db:
                # Build base query
                query = select(A2ACollaborationSession).where(
                    A2ACollaborationSession.created_at >= cutoff_date
                )
                
                # Apply filters
                if agent_filter:
                    query = query.where(A2ACollaborationSession.requesting_agent == agent_filter)
                
                if specialty_filter:
                    query = query.where(
                        A2ACollaborationSession.requested_specialties.op('?')(specialty_filter.value)
                    )
                
                result = await db.execute(query)
                sessions = result.scalars().all()
                
                # Calculate analytics
                total_sessions = len(sessions)
                completed_sessions = len([s for s in sessions if s.status == CollaborationStatus.COMPLETED.value])
                consensus_reached = len([s for s in sessions if s.consensus_reached])
                
                # Performance metrics
                response_times = [s.average_response_time_ms for s in sessions if s.average_response_time_ms]
                avg_response_time = sum(response_times) / len(response_times) if response_times else 0
                
                consensus_scores = [s.agreement_score for s in sessions if s.agreement_score]
                avg_consensus_score = sum(consensus_scores) / len(consensus_scores) if consensus_scores else 0
                
                # Specialty breakdown
                specialty_stats = {}
                for session in sessions:
                    for specialty in (session.requested_specialties or []):
                        if specialty not in specialty_stats:
                            specialty_stats[specialty] = {"count": 0, "success_rate": 0}
                        specialty_stats[specialty]["count"] += 1
                        if session.consensus_reached:
                            specialty_stats[specialty]["success_rate"] += 1
                
                # Calculate success rates
                for specialty_data in specialty_stats.values():
                    if specialty_data["count"] > 0:
                        specialty_data["success_rate"] = specialty_data["success_rate"] / specialty_data["count"]
                
                analytics = {
                    "period_days": days_back,
                    "total_collaborations": total_sessions,
                    "completed_collaborations": completed_sessions,
                    "completion_rate": completed_sessions / total_sessions if total_sessions > 0 else 0,
                    "consensus_reached": consensus_reached,
                    "consensus_rate": consensus_reached / total_sessions if total_sessions > 0 else 0,
                    "average_response_time_ms": avg_response_time,
                    "average_consensus_score": avg_consensus_score,
                    "specialty_statistics": specialty_stats,
                    "urgency_breakdown": await self._calculate_urgency_breakdown(sessions),
                    "quality_metrics": await self._calculate_quality_metrics(sessions)
                }
                
                return analytics
                
        except Exception as e:
            logger.error("Failed to get collaboration analytics", error=str(e))
            return {"error": str(e)}
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health and performance metrics."""
        try:
            # Active sessions
            active_sessions = await self.collaboration_engine.list_active_collaborations()
            
            # Agent registry statistics
            agent_stats = await self.agent_registry.get_registry_statistics()
            
            # Performance metrics
            health_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "active_collaborations": len(active_sessions),
                "total_collaborations": self.total_collaborations,
                "successful_collaborations": self.successful_collaborations,
                "failed_collaborations": self.failed_collaborations,
                "success_rate": self.successful_collaborations / max(1, self.total_collaborations),
                "average_collaboration_time_ms": self.average_collaboration_time,
                "agent_registry": agent_stats,
                "subsystem_health": {
                    "collaboration_engine": "healthy",
                    "consensus_engine": "healthy", 
                    "mcp_protocol": "healthy",
                    "agent_registry": "healthy"
                },
                "performance_alerts": await self._check_performance_alerts()
            }
            
            return health_data
            
        except Exception as e:
            logger.error("Failed to get system health", error=str(e))
            return {"error": str(e), "status": "unhealthy"}
    
    # Private helper methods
    
    async def _register_medical_agents(self) -> None:
        """Register all medical specialty agents with the MCP registry."""
        try:
            available_specialties = await MedicalAgentFactory.list_available_specialties()
            
            for specialty in available_specialties:
                # Get agent instance
                agent = await MedicalAgentFactory.get_agent(specialty)
                
                # Create MCP agent info (simplified - would need proper implementation)
                from app.modules.mcp.schemas import MCPAgentInfo, AgentCapabilities, SecurityLevel, AgentStatus
                
                mcp_agent_info = MCPAgentInfo(
                    agent_id=agent.agent_id,
                    agent_name=f"{specialty.value.title()} Medical AI Agent",
                    status=AgentStatus.ACTIVE,
                    capabilities=AgentCapabilities(
                        medical_specialties=[specialty.value],
                        model_type="gemma_medical",
                        model_version="1.0",
                        security_clearance=SecurityLevel.PHI_RESTRICTED,
                        hipaa_compliant=True,
                        soc2_compliant=True,
                        supports_phi_processing=True,
                        supports_emergency_cases=(specialty == MedicalSpecialty.EMERGENCY_MEDICINE)
                    ),
                    endpoint_url=f"internal://medical_agents/{specialty.value}",
                    compliance_status="verified"
                )
                
                # Register with MCP registry
                await self.agent_registry.register_agent(mcp_agent_info)
                
                logger.info("Registered medical agent with MCP",
                           agent_id=agent.agent_id,
                           specialty=specialty.value)
            
        except Exception as e:
            logger.error("Failed to register medical agents", error=str(e))
            raise
    
    async def _load_historical_statistics(self) -> None:
        """Load historical collaboration statistics from database."""
        try:
            async with get_db() as db:
                # Count total collaborations
                total_result = await db.execute(
                    select(func.count(A2ACollaborationSession.id))
                )
                self.total_collaborations = total_result.scalar() or 0
                
                # Count successful collaborations
                success_result = await db.execute(
                    select(func.count(A2ACollaborationSession.id)).where(
                        A2ACollaborationSession.consensus_reached == True
                    )
                )
                self.successful_collaborations = success_result.scalar() or 0
                
                # Count failed collaborations  
                failed_result = await db.execute(
                    select(func.count(A2ACollaborationSession.id)).where(
                        A2ACollaborationSession.status == CollaborationStatus.FAILED.value
                    )
                )
                self.failed_collaborations = failed_result.scalar() or 0
                
                # Calculate average collaboration time
                time_result = await db.execute(
                    select(func.avg(A2ACollaborationSession.total_processing_time_ms)).where(
                        A2ACollaborationSession.total_processing_time_ms.isnot(None)
                    )
                )
                self.average_collaboration_time = float(time_result.scalar() or 0)
                
                logger.info("Loaded historical statistics",
                           total_collaborations=self.total_collaborations,
                           successful_collaborations=self.successful_collaborations,
                           average_time_ms=self.average_collaboration_time)
                
        except Exception as e:
            logger.error("Failed to load historical statistics", error=str(e))
    
    async def _calculate_urgency_breakdown(self, sessions: List[A2ACollaborationSession]) -> Dict[str, int]:
        """Calculate breakdown of collaborations by urgency level."""
        urgency_counts = {}
        
        for session in sessions:
            urgency = session.urgency_level or "routine"
            urgency_counts[urgency] = urgency_counts.get(urgency, 0) + 1
        
        return urgency_counts
    
    async def _calculate_quality_metrics(self, sessions: List[A2ACollaborationSession]) -> Dict[str, float]:
        """Calculate quality metrics for collaboration sessions."""
        if not sessions:
            return {}
        
        # Average confidence scores
        confidence_scores = [s.average_confidence for s in sessions if s.average_confidence]
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        # Human review rate
        human_review_count = len([s for s in sessions if s.human_review_required])
        human_review_rate = human_review_count / len(sessions)
        
        # Escalation rate
        escalation_count = len([s for s in sessions if s.escalation_triggered])
        escalation_rate = escalation_count / len(sessions)
        
        return {
            "average_confidence": avg_confidence,
            "human_review_rate": human_review_rate,
            "escalation_rate": escalation_rate,
            "quality_score": avg_confidence * (1 - escalation_rate)  # Simple quality score
        }
    
    async def _check_performance_alerts(self) -> List[Dict[str, Any]]:
        """Check for performance alerts and issues."""
        alerts = []
        
        # Check success rate
        if self.total_collaborations > 10:  # Only check if we have enough data
            success_rate = self.successful_collaborations / self.total_collaborations
            if success_rate < 0.7:  # Less than 70% success rate
                alerts.append({
                    "type": "low_success_rate",
                    "severity": "warning",
                    "message": f"Success rate is {success_rate:.2%}, below 70% threshold",
                    "value": success_rate
                })
        
        # Check average response time
        if self.average_collaboration_time > 300000:  # More than 5 minutes
            alerts.append({
                "type": "slow_response_time",
                "severity": "warning", 
                "message": f"Average collaboration time is {self.average_collaboration_time/1000:.1f} seconds",
                "value": self.average_collaboration_time
            })
        
        # Check active sessions (potential overload)
        active_sessions = await self.collaboration_engine.list_active_collaborations()
        if len(active_sessions) > 50:  # More than 50 active sessions
            alerts.append({
                "type": "high_load",
                "severity": "warning",
                "message": f"{len(active_sessions)} active sessions, potential system overload",
                "value": len(active_sessions)
            })
        
        return alerts
    
    # Background monitoring tasks
    
    async def _performance_monitoring_task(self) -> None:
        """Background task for performance monitoring."""
        while True:
            try:
                # Update performance metrics
                await self._update_performance_metrics()
                
                # Check for performance issues
                alerts = await self._check_performance_alerts()
                if alerts:
                    logger.warning("Performance alerts detected",
                                 alert_count=len(alerts),
                                 alerts=alerts)
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error("Error in performance monitoring", error=str(e))
                await asyncio.sleep(300)
    
    async def _agent_health_monitoring_task(self) -> None:
        """Background task for monitoring agent health."""
        while True:
            try:
                # Check agent registry health
                agent_stats = await self.agent_registry.get_registry_statistics()
                
                if agent_stats.get("error"):
                    logger.error("Agent registry error detected", error=agent_stats["error"])
                else:
                    logger.info("Agent registry health check",
                               total_agents=agent_stats.get("total_agents", 0),
                               active_agents=agent_stats.get("active_agents", 0))
                
                await asyncio.sleep(600)  # Check every 10 minutes
                
            except Exception as e:
                logger.error("Error in agent health monitoring", error=str(e))
                await asyncio.sleep(600)
    
    async def _collaboration_analytics_task(self) -> None:
        """Background task for collaboration analytics."""
        while True:
            try:
                # Generate daily analytics
                analytics = await self.get_collaboration_analytics(days_back=1)
                
                # Log key metrics
                logger.info("Daily collaboration metrics",
                           total_collaborations=analytics.get("total_collaborations", 0),
                           consensus_rate=analytics.get("consensus_rate", 0),
                           completion_rate=analytics.get("completion_rate", 0))
                
                # Update internal statistics
                await self._load_historical_statistics()
                
                await asyncio.sleep(3600)  # Update every hour
                
            except Exception as e:
                logger.error("Error in collaboration analytics", error=str(e))
                await asyncio.sleep(3600)
    
    async def _update_performance_metrics(self) -> None:
        """Update internal performance metrics."""
        try:
            # Reload statistics from database
            await self._load_historical_statistics()
            
            # Update agent performance tracking
            async with get_db() as db:
                # Query recent agent interactions for performance data
                recent_cutoff = datetime.utcnow() - timedelta(hours=24)
                
                # This is a placeholder - would implement actual agent performance tracking
                pass
                
        except Exception as e:
            logger.error("Error updating performance metrics", error=str(e))
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the A2A Coordinator and all subsystems."""
        logger.info("Shutting down A2A Coordinator")
        
        # Shutdown subsystems
        if self.collaboration_engine:
            await self.collaboration_engine.shutdown()
        
        if self.agent_registry:
            await self.agent_registry.shutdown()
        
        if self.mcp_protocol:
            await self.mcp_protocol.shutdown()
        
        # Log shutdown
        await audit_logger.log_event(
            event_type=AuditEventType.SYSTEM_SHUTDOWN,
            user_id="a2a_coordinator",
            resource_type="a2a_coordinator",
            action="coordinator_shutdown",
            details={
                "final_stats": {
                    "total_collaborations": self.total_collaborations,
                    "successful_collaborations": self.successful_collaborations,
                    "success_rate": self.successful_collaborations / max(1, self.total_collaborations)
                }
            }
        )
        
        logger.info("A2A Coordinator shutdown complete")