"""
MCP Protocol Core Implementation for Healthcare Platform V2.0

Core Model Context Protocol implementation with enterprise security, 
HIPAA compliance, and SOC2 audit logging for healthcare AI agent communication.
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization

# Import existing healthcare platform components
from app.core.database_unified import get_db, AuditEventType
from app.core.security import encryption_service, SecurityManager
from app.modules.audit_logger.service import audit_logger
from app.core.config import get_settings

# Import MCP schemas
from .schemas import (
    MCPMessage, MCPResponse, MCPMessageType, AgentStatus, SecurityLevel,
    MCPAgentInfo, ConsultationRequest, ConsultationResponse, 
    EmergencyAlert, MCPAuditLog, MedicalUrgency
)
from .models import MCPAgent, MCPMessageLog, AgentConsultation

logger = structlog.get_logger()
settings = get_settings()

class MCPProtocolError(Exception):
    """Base exception for MCP protocol errors."""
    pass

class AgentNotFoundError(MCPProtocolError):
    """Raised when an agent is not found in the registry."""
    pass

class SecurityViolationError(MCPProtocolError):
    """Raised when a security violation is detected."""
    pass

class MessageRoutingError(MCPProtocolError):
    """Raised when message routing fails.""" 
    pass

class MCPProtocol:
    """
    Model Context Protocol for secure AI agent communication.
    
    Provides encrypted, audited communication between medical AI agents
    with full HIPAA compliance and SOC2 audit logging.
    """
    
    def __init__(self):
        self.security_manager = SecurityManager()
        self.active_agents: Dict[str, MCPAgentInfo] = {}
        self.message_queue: Dict[str, List[MCPMessage]] = {}
        self.pending_responses: Dict[str, asyncio.Future] = {}
        self._shutdown_event = asyncio.Event()
        
        # Performance tracking
        self.message_count = 0
        self.error_count = 0
        self.avg_processing_time = 0.0
    
    async def initialize(self) -> None:
        """Initialize MCP protocol with database and security setup."""
        try:
            logger.info("Initializing MCP Protocol system")
            
            # Load existing agents from database
            await self._load_registered_agents()
            
            # Start background tasks
            asyncio.create_task(self._heartbeat_monitor())
            asyncio.create_task(self._message_cleanup_task())
            
            # Log system initialization
            await audit_logger.log_event(
                event_type=AuditEventType.SYSTEM_STARTUP,
                user_id="system",
                resource_type="mcp_protocol",
                action="protocol_initialized",
                details={"agent_count": len(self.active_agents)}
            )
            
            logger.info("MCP Protocol initialized successfully", 
                       agent_count=len(self.active_agents))
                       
        except Exception as e:
            logger.error("Failed to initialize MCP Protocol", error=str(e))
            raise MCPProtocolError(f"Initialization failed: {e}")
    
    async def register_agent(self, agent_info: MCPAgentInfo) -> bool:
        """
        Register a medical AI agent with the MCP protocol.
        
        Args:
            agent_info: Agent information and capabilities
            
        Returns:
            bool: True if registration successful
            
        Raises:
            MCPProtocolError: If registration fails
        """
        try:
            logger.info("Registering agent", agent_id=agent_info.agent_id)
            
            # Validate agent information
            await self._validate_agent_registration(agent_info)
            
            # Check for duplicate registration
            if agent_info.agent_id in self.active_agents:
                logger.warning("Agent already registered", agent_id=agent_info.agent_id)
                return False
            
            # Store agent in database
            async with get_db() as db:
                db_agent = MCPAgent(
                    agent_id=agent_info.agent_id,
                    agent_name=agent_info.agent_name,
                    status=agent_info.status.value,
                    capabilities=agent_info.capabilities.model_dump(),
                    endpoint_url=agent_info.endpoint_url,
                    public_key=agent_info.public_key,
                    total_consultations=0,
                    average_rating=0.0,
                    uptime_percentage=100.0,
                    compliance_status="verified",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                db.add(db_agent)
                await db.commit()
                await db.refresh(db_agent)
                
                # Add to active agents
                self.active_agents[agent_info.agent_id] = agent_info
                self.message_queue[agent_info.agent_id] = []
                
                # Log registration for SOC2 compliance
                await audit_logger.log_event(
                    event_type=AuditEventType.AGENT_REGISTERED,
                    user_id="system",
                    resource_type="mcp_agent",
                    resource_id=agent_info.agent_id,
                    action="agent_registered",
                    details={
                        "agent_name": agent_info.agent_name,
                        "specialties": agent_info.capabilities.medical_specialties,
                        "phi_capable": agent_info.capabilities.supports_phi_processing,
                        "emergency_capable": agent_info.capabilities.supports_emergency_cases,
                        "security_level": agent_info.capabilities.security_clearance.value
                    }
                )
                
                logger.info("Agent registered successfully", 
                           agent_id=agent_info.agent_id,
                           specialties=agent_info.capabilities.medical_specialties)
                
                return True
                
        except Exception as e:
            logger.error("Agent registration failed", 
                        agent_id=agent_info.agent_id, 
                        error=str(e))
            
            # Log registration failure
            await audit_logger.log_event(
                event_type=AuditEventType.AGENT_REGISTRATION_FAILED,
                user_id="system",
                resource_type="mcp_agent",
                resource_id=agent_info.agent_id,
                action="registration_failed",
                details={"error": str(e)}
            )
            
            raise MCPProtocolError(f"Agent registration failed: {e}")
    
    async def send_message(self, message: MCPMessage) -> MCPResponse:
        """
        Send encrypted message between agents with audit logging.
        
        Args:
            message: MCP message to send
            
        Returns:
            MCPResponse: Response from receiving agent
            
        Raises:
            MessageRoutingError: If message routing fails
            SecurityViolationError: If security validation fails
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info("Sending MCP message", 
                       message_id=message.message_id,
                       from_agent=message.from_agent,
                       to_agent=message.to_agent,
                       message_type=message.message_type.value)
            
            # Validate message security
            await self._validate_message_security(message)
            
            # Validate agents exist and are active
            await self._validate_agent_status(message.from_agent, message.to_agent)
            
            # Handle PHI encryption if needed
            if message.contains_phi:
                message = await self._encrypt_phi_content(message)
            
            # Route message to recipient
            if message.to_agent:
                # Direct message to specific agent
                response = await self._route_direct_message(message)
            else:
                # Broadcast message (for consultations, emergencies)
                response = await self._route_broadcast_message(message)
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Log message for audit compliance
            await self._log_message_audit(message, response, processing_time)
            
            # Update performance metrics
            self.message_count += 1
            self.avg_processing_time = (self.avg_processing_time + processing_time) / 2
            
            logger.info("MCP message sent successfully",
                       message_id=message.message_id,
                       processing_time_ms=processing_time)
            
            return response
            
        except Exception as e:
            self.error_count += 1
            
            logger.error("MCP message sending failed",
                        message_id=message.message_id,
                        error=str(e))
            
            # Log failure for audit
            await audit_logger.log_event(
                event_type=AuditEventType.MESSAGE_FAILED,
                user_id=message.from_agent,
                resource_type="mcp_message",
                resource_id=message.message_id,
                action="message_send_failed",
                details={"error": str(e), "to_agent": message.to_agent}
            )
            
            raise MessageRoutingError(f"Message sending failed: {e}")
    
    async def send_consultation_request(self, request: ConsultationRequest) -> List[ConsultationResponse]:
        """
        Send medical consultation request to appropriate specialist agents.
        
        Args:
            request: Medical consultation request
            
        Returns:
            List[ConsultationResponse]: Responses from consulting agents
        """
        try:
            logger.info("Processing consultation request",
                       consultation_id=request.consultation_id,
                       urgency=request.urgency_level.value,
                       specialties=request.requested_specialties)
            
            # Find appropriate agents for consultation
            target_agents = await self._find_consultation_agents(request)
            
            if not target_agents:
                raise MCPProtocolError("No suitable agents found for consultation")
            
            # Create MCP messages for each target agent
            messages = []
            for agent_id in target_agents:
                message = MCPMessage(
                    message_type=MCPMessageType.CONSULTATION_REQUEST,
                    from_agent=request.requesting_agent,
                    to_agent=agent_id,
                    payload=request.model_dump(),
                    security_level=SecurityLevel.PHI_ENCRYPTED if not request.anonymized else SecurityLevel.INTERNAL,
                    contains_phi=not request.anonymized,
                    urgency_level=request.urgency_level,
                    patient_id=request.patient_id_hash,
                    case_id=request.consultation_id
                )
                messages.append(message)
            
            # Send messages concurrently
            responses = []
            send_tasks = [self.send_message(msg) for msg in messages]
            
            # Wait for responses with timeout
            timeout_seconds = request.max_response_time_seconds
            try:
                mcp_responses = await asyncio.wait_for(
                    asyncio.gather(*send_tasks, return_exceptions=True),
                    timeout=timeout_seconds
                )
                
                # Process responses and convert to ConsultationResponse
                for i, mcp_response in enumerate(mcp_responses):
                    if isinstance(mcp_response, Exception):
                        logger.warning("Agent consultation failed",
                                     agent_id=target_agents[i],
                                     error=str(mcp_response))
                        continue
                    
                    if mcp_response.status == "success":
                        consultation_response = ConsultationResponse.model_validate(
                            mcp_response.response_data
                        )
                        responses.append(consultation_response)
                
            except asyncio.TimeoutError:
                logger.warning("Consultation request timed out",
                             consultation_id=request.consultation_id,
                             timeout_seconds=timeout_seconds)
            
            # Store consultation in database for audit
            await self._store_consultation_audit(request, responses)
            
            logger.info("Consultation request completed",
                       consultation_id=request.consultation_id,
                       responses_received=len(responses))
            
            return responses
            
        except Exception as e:
            logger.error("Consultation request failed",
                        consultation_id=request.consultation_id,
                        error=str(e))
            
            await audit_logger.log_event(
                event_type=AuditEventType.CONSULTATION_FAILED,
                user_id=request.requesting_agent,
                resource_type="medical_consultation",
                resource_id=request.consultation_id,
                action="consultation_failed",
                details={"error": str(e)}
            )
            
            raise MCPProtocolError(f"Consultation request failed: {e}")
    
    async def send_emergency_alert(self, alert: EmergencyAlert) -> List[MCPResponse]:
        """
        Send emergency alert to all capable agents with high priority.
        
        Args:
            alert: Emergency alert information
            
        Returns:
            List[MCPResponse]: Responses from alerted agents
        """
        try:
            logger.critical("Processing emergency alert",
                           alert_id=alert.alert_id,
                           emergency_type=alert.emergency_type,
                           severity=alert.severity_level)
            
            # Find all agents capable of handling emergencies
            emergency_agents = [
                agent_id for agent_id, agent_info in self.active_agents.items()
                if (agent_info.capabilities.supports_emergency_cases and 
                    agent_info.status == AgentStatus.ACTIVE)
            ]
            
            if not emergency_agents:
                raise MCPProtocolError("No emergency-capable agents available")
            
            # Create high-priority emergency messages
            messages = []
            for agent_id in emergency_agents:
                message = MCPMessage(
                    message_type=MCPMessageType.EMERGENCY_ALERT,
                    from_agent=alert.alerting_agent,
                    to_agent=agent_id,
                    payload=alert.model_dump(),
                    security_level=SecurityLevel.PHI_ENCRYPTED,
                    contains_phi=True,
                    urgency_level=MedicalUrgency.EMERGENCY,
                    requires_audit=True
                )
                messages.append(message)
            
            # Send emergency messages with high priority
            send_tasks = [self.send_message(msg) for msg in messages]
            responses = await asyncio.gather(*send_tasks, return_exceptions=True)
            
            # Filter successful responses
            successful_responses = [
                resp for resp in responses 
                if isinstance(resp, MCPResponse) and resp.status == "success"
            ]
            
            # Log emergency alert for critical audit
            await audit_logger.log_event(
                event_type=AuditEventType.EMERGENCY_ALERT,
                user_id=alert.alerting_agent,
                resource_type="emergency_alert",
                resource_id=alert.alert_id,
                action="emergency_alert_sent",
                details={
                    "emergency_type": alert.emergency_type,
                    "severity": alert.severity_level,
                    "agents_alerted": len(emergency_agents),
                    "responses_received": len(successful_responses),
                    "time_sensitive": alert.time_sensitive
                }
            )
            
            logger.critical("Emergency alert sent",
                           alert_id=alert.alert_id,
                           agents_alerted=len(emergency_agents),
                           responses_received=len(successful_responses))
            
            return successful_responses
            
        except Exception as e:
            logger.critical("Emergency alert failed",
                           alert_id=alert.alert_id,
                           error=str(e))
            
            await audit_logger.log_event(
                event_type=AuditEventType.EMERGENCY_ALERT_FAILED,
                user_id=alert.alerting_agent,
                resource_type="emergency_alert",
                resource_id=alert.alert_id,
                action="emergency_alert_failed",
                details={"error": str(e)}
            )
            
            raise MCPProtocolError(f"Emergency alert failed: {e}")
    
    async def get_agent_capabilities(self, agent_id: str) -> Optional[MCPAgentInfo]:
        """Get information and capabilities for a specific agent."""
        return self.active_agents.get(agent_id)
    
    async def list_active_agents(self, specialty_filter: Optional[str] = None) -> List[MCPAgentInfo]:
        """List all active agents, optionally filtered by medical specialty."""
        agents = [
            agent for agent in self.active_agents.values()
            if agent.status == AgentStatus.ACTIVE
        ]
        
        if specialty_filter:
            agents = [
                agent for agent in agents
                if specialty_filter in agent.capabilities.medical_specialties
            ]
        
        return agents
    
    async def update_agent_status(self, agent_id: str, status: AgentStatus) -> bool:
        """Update the status of a registered agent."""
        if agent_id not in self.active_agents:
            return False
        
        old_status = self.active_agents[agent_id].status
        self.active_agents[agent_id].status = status
        self.active_agents[agent_id].updated_at = datetime.utcnow()
        
        # Update database
        async with get_db() as db:
            result = await db.execute(
                select(MCPAgent).where(MCPAgent.agent_id == agent_id)
            )
            db_agent = result.scalar_one_or_none()
            
            if db_agent:
                db_agent.status = status.value
                db_agent.updated_at = datetime.utcnow()
                await db.commit()
        
        # Log status change
        await audit_logger.log_event(
            event_type=AuditEventType.AGENT_STATUS_CHANGED,
            user_id="system",
            resource_type="mcp_agent",
            resource_id=agent_id,
            action="status_updated",
            details={"old_status": old_status.value, "new_status": status.value}
        )
        
        return True
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the MCP protocol system."""
        logger.info("Shutting down MCP Protocol system")
        
        # Signal shutdown to background tasks
        self._shutdown_event.set()
        
        # Update all agents to offline status
        for agent_id in list(self.active_agents.keys()):
            await self.update_agent_status(agent_id, AgentStatus.OFFLINE)
        
        # Log system shutdown
        await audit_logger.log_event(
            event_type=AuditEventType.SYSTEM_SHUTDOWN,
            user_id="system",
            resource_type="mcp_protocol",
            action="protocol_shutdown",
            details={"final_agent_count": len(self.active_agents)}
        )
        
        logger.info("MCP Protocol shutdown complete")
    
    # Private helper methods
    
    async def _load_registered_agents(self) -> None:
        """Load previously registered agents from database."""
        async with get_db() as db:
            result = await db.execute(
                select(MCPAgent).where(MCPAgent.status == AgentStatus.ACTIVE.value)
            )
            db_agents = result.scalars().all()
            
            for db_agent in db_agents:
                # Reconstruct agent info from database
                from .schemas import AgentCapabilities
                
                capabilities = AgentCapabilities.model_validate(db_agent.capabilities)
                agent_info = MCPAgentInfo(
                    agent_id=db_agent.agent_id,
                    agent_name=db_agent.agent_name,
                    status=AgentStatus(db_agent.status),
                    capabilities=capabilities,
                    endpoint_url=db_agent.endpoint_url,
                    public_key=db_agent.public_key,
                    total_consultations=db_agent.total_consultations,
                    average_rating=db_agent.average_rating,
                    uptime_percentage=db_agent.uptime_percentage,
                    compliance_status=db_agent.compliance_status,
                    created_at=db_agent.created_at,
                    updated_at=db_agent.updated_at
                )
                
                self.active_agents[db_agent.agent_id] = agent_info
                self.message_queue[db_agent.agent_id] = []
    
    async def _validate_agent_registration(self, agent_info: MCPAgentInfo) -> None:
        """Validate agent registration meets healthcare compliance requirements."""
        # Check required fields
        if not agent_info.agent_id or not agent_info.agent_name:
            raise MCPProtocolError("Agent ID and name are required")
        
        # Validate medical specialties
        if not agent_info.capabilities.medical_specialties:
            raise MCPProtocolError("At least one medical specialty required")
        
        # Check compliance requirements
        if not agent_info.capabilities.hipaa_compliant:
            raise MCPProtocolError("Agent must be HIPAA compliant")
        
        if not agent_info.capabilities.soc2_compliant:
            raise MCPProtocolError("Agent must be SOC2 compliant")
        
        # Validate PHI processing capability
        if (agent_info.capabilities.supports_phi_processing and 
            agent_info.capabilities.security_clearance == SecurityLevel.PUBLIC):
            raise MCPProtocolError("PHI processing requires higher security clearance")
    
    async def _validate_message_security(self, message: MCPMessage) -> None:
        """Validate message meets security requirements."""
        # Check agent permissions
        from_agent = self.active_agents.get(message.from_agent)
        if not from_agent:
            raise SecurityViolationError(f"Unknown sending agent: {message.from_agent}")
        
        # Validate PHI handling
        if message.contains_phi:
            if not from_agent.capabilities.supports_phi_processing:
                raise SecurityViolationError("Agent not authorized for PHI processing")
            
            if message.security_level not in [SecurityLevel.PHI_RESTRICTED, SecurityLevel.PHI_ENCRYPTED]:
                raise SecurityViolationError("PHI messages require appropriate security level")
    
    async def _validate_agent_status(self, from_agent: str, to_agent: Optional[str]) -> None:
        """Validate that agents are active and available."""
        if from_agent not in self.active_agents:
            raise AgentNotFoundError(f"Sending agent not found: {from_agent}")
        
        if self.active_agents[from_agent].status != AgentStatus.ACTIVE:
            raise MCPProtocolError(f"Sending agent not active: {from_agent}")
        
        if to_agent:
            if to_agent not in self.active_agents:
                raise AgentNotFoundError(f"Receiving agent not found: {to_agent}")
            
            if self.active_agents[to_agent].status not in [AgentStatus.ACTIVE, AgentStatus.BUSY]:
                raise MCPProtocolError(f"Receiving agent not available: {to_agent}")
    
    async def _encrypt_phi_content(self, message: MCPMessage) -> MCPMessage:
        """Encrypt message content containing PHI."""
        try:
            # Use existing encryption service from healthcare platform
            encrypted_payload = await encryption_service.encrypt(
                json.dumps(message.payload),
                context=f"mcp_agent_{message.from_agent}"
            )
            
            # Create new message with encrypted content
            message.encrypted_payload = encrypted_payload
            message.payload = {"encrypted": True, "phi_encrypted": True}
            message.security_level = SecurityLevel.PHI_ENCRYPTED
            
            return message
            
        except Exception as e:
            logger.error("PHI encryption failed", message_id=message.message_id, error=str(e))
            raise SecurityViolationError(f"PHI encryption failed: {e}")
    
    async def _route_direct_message(self, message: MCPMessage) -> MCPResponse:
        """Route message to specific agent."""
        # This would integrate with the actual agent communication
        # For now, simulate agent response
        
        response = MCPResponse(
            request_message_id=message.message_id,
            from_agent=message.to_agent,
            to_agent=message.from_agent,
            status="success",
            response_data={"message": "Message received and processed"},
            processing_time_ms=100.0,
            confidence_score=0.95,
            contains_phi=message.contains_phi,
            audit_logged=True
        )
        
        return response
    
    async def _route_broadcast_message(self, message: MCPMessage) -> MCPResponse:
        """Route broadcast message to multiple agents."""
        # Find relevant agents based on message type and content
        target_agents = []
        
        if message.message_type == MCPMessageType.EMERGENCY_ALERT:
            target_agents = [
                agent_id for agent_id, agent_info in self.active_agents.items()
                if agent_info.capabilities.supports_emergency_cases
            ]
        
        # Send to all target agents (simplified)
        response = MCPResponse(
            request_message_id=message.message_id,
            from_agent="broadcast_handler",
            to_agent=message.from_agent,
            status="success",
            response_data={"agents_notified": len(target_agents)},
            processing_time_ms=200.0,
            confidence_score=1.0,
            contains_phi=message.contains_phi,
            audit_logged=True
        )
        
        return response
    
    async def _find_consultation_agents(self, request: ConsultationRequest) -> List[str]:
        """Find appropriate agents for a medical consultation."""
        suitable_agents = []
        
        for agent_id, agent_info in self.active_agents.items():
            if agent_info.status != AgentStatus.ACTIVE:
                continue
            
            # Check if agent has requested specialties
            agent_specialties = set(agent_info.capabilities.medical_specialties)
            requested_specialties = set(request.requested_specialties)
            
            if requested_specialties.intersection(agent_specialties):
                suitable_agents.append(agent_id)
            
            # For emergency cases, include all emergency-capable agents
            if (request.urgency_level == MedicalUrgency.EMERGENCY and
                agent_info.capabilities.supports_emergency_cases):
                suitable_agents.append(agent_id)
        
        return list(set(suitable_agents))  # Remove duplicates
    
    async def _log_message_audit(self, message: MCPMessage, response: MCPResponse, processing_time: float) -> None:
        """Log message for HIPAA/SOC2 audit compliance."""
        try:
            # Create audit log entry
            audit_log = MCPAuditLog(
                message_id=message.message_id,
                message_type=message.message_type,
                from_agent=message.from_agent,
                to_agent=message.to_agent,
                security_level=message.security_level,
                contains_phi=message.contains_phi,
                phi_access_reason=message.metadata.get("phi_access_reason"),
                processing_time_ms=processing_time,
                status=response.status,
                error_details=response.error_message,
                hipaa_logged=True,
                soc2_category="agent_communication"
            )
            
            # Store in database for compliance
            async with get_db() as db:
                log_entry = MCPMessageLog(
                    message_id=message.message_id,
                    message_type=message.message_type.value,
                    from_agent=message.from_agent,
                    to_agent=message.to_agent,
                    security_level=message.security_level.value,
                    contains_phi=message.contains_phi,
                    processing_time_ms=processing_time,
                    status=response.status,
                    timestamp=datetime.utcnow(),
                    audit_hash=self._generate_audit_hash(audit_log)
                )
                
                db.add(log_entry)
                await db.commit()
            
            # Log to main audit system
            await audit_logger.log_event(
                event_type=AuditEventType.AGENT_COMMUNICATION,
                user_id=message.from_agent,
                resource_type="mcp_message",
                resource_id=message.message_id,
                action="message_processed",
                details=audit_log.model_dump()
            )
            
        except Exception as e:
            logger.error("Audit logging failed", message_id=message.message_id, error=str(e))
            # Don't raise exception - audit failure shouldn't break message processing
    
    async def _store_consultation_audit(self, request: ConsultationRequest, responses: List[ConsultationResponse]) -> None:
        """Store consultation audit trail for compliance."""
        try:
            async with get_db() as db:
                consultation = AgentConsultation(
                    consultation_id=request.consultation_id,
                    requesting_agent=request.requesting_agent,
                    patient_id_hash=request.patient_id_hash,
                    case_summary=request.case_summary[:500],  # Truncate for storage
                    requested_specialties=request.requested_specialties,
                    urgency_level=request.urgency_level.value,
                    responses_received=len(responses),
                    anonymized=request.anonymized,
                    consent_obtained=request.consent_obtained,
                    phi_access_reason=request.phi_access_reason,
                    created_at=datetime.utcnow()
                )
                
                db.add(consultation)
                await db.commit()
                
        except Exception as e:
            logger.error("Consultation audit storage failed", 
                        consultation_id=request.consultation_id, 
                        error=str(e))
    
    def _generate_audit_hash(self, audit_log: MCPAuditLog) -> str:
        """Generate cryptographic hash for audit log integrity."""
        import hashlib
        
        audit_data = audit_log.model_dump_json(exclude={"audit_hash"})
        return hashlib.sha256(audit_data.encode()).hexdigest()
    
    async def _heartbeat_monitor(self) -> None:
        """Background task to monitor agent heartbeats."""
        while not self._shutdown_event.is_set():
            try:
                current_time = datetime.utcnow()
                inactive_agents = []
                
                for agent_id, agent_info in self.active_agents.items():
                    if (agent_info.last_heartbeat and 
                        (current_time - agent_info.last_heartbeat).total_seconds() > 300):  # 5 minutes
                        inactive_agents.append(agent_id)
                
                # Mark inactive agents as offline
                for agent_id in inactive_agents:
                    await self.update_agent_status(agent_id, AgentStatus.OFFLINE)
                    logger.warning("Agent marked offline due to missed heartbeat", agent_id=agent_id)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error("Heartbeat monitor error", error=str(e))
                await asyncio.sleep(60)
    
    async def _message_cleanup_task(self) -> None:
        """Background task to clean up old messages and logs."""
        while not self._shutdown_event.is_set():
            try:
                # Clean up messages older than 24 hours
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                
                async with get_db() as db:
                    # Clean up old message logs (keep for SOC2 compliance period)
                    retention_days = settings.AUDIT_LOG_RETENTION_DAYS
                    retention_cutoff = datetime.utcnow() - timedelta(days=retention_days)
                    
                    result = await db.execute(
                        select(MCPMessageLog).where(
                            MCPMessageLog.timestamp < retention_cutoff
                        )
                    )
                    old_logs = result.scalars().all()
                    
                    for log in old_logs:
                        await db.delete(log)
                    
                    await db.commit()
                    
                    if old_logs:
                        logger.info(f"Cleaned up {len(old_logs)} old message logs")
                
                # Sleep for 1 hour
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error("Message cleanup error", error=str(e))
                await asyncio.sleep(3600)