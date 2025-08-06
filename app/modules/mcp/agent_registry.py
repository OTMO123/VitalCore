"""
MCP Agent Registry for Healthcare Platform V2.0

Centralized registry for managing MCP agents with full compliance tracking,
security validation, and performance monitoring.
"""

import asyncio
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
import structlog

# Import existing healthcare platform components
from app.core.database_unified import get_db, AuditEventType
from app.core.security import encryption_service, SecurityManager
from app.modules.audit_logger.service import audit_logger
from app.core.config import get_settings

# Import MCP components
from .schemas import (
    MCPAgentInfo, AgentCapabilities, AgentStatus, SecurityLevel,
    MCPMessage, MCPResponse, MedicalUrgency
)
from .models import MCPAgent, MCPPerformanceMetrics, MCPSecurityEvent

logger = structlog.get_logger()
settings = get_settings()

class AgentRegistrationError(Exception):
    """Raised when agent registration fails."""
    pass

class SecurityValidationError(Exception):
    """Raised when agent security validation fails."""
    pass

class AgentRegistry:
    """
    Centralized registry for MCP agents with enterprise security and compliance.
    
    Manages agent registration, discovery, health monitoring, and security validation
    for healthcare AI agents with full SOC2/HIPAA compliance.
    """
    
    def __init__(self):
        self.security_manager = SecurityManager()
        self._agent_cache: Dict[str, MCPAgentInfo] = {}
        self._capability_index: Dict[str, Set[str]] = {}  # specialty -> agent_ids
        self._security_clearance_index: Dict[SecurityLevel, Set[str]] = {}
        self._performance_cache: Dict[str, Dict[str, float]] = {}
        self._shutdown_event = asyncio.Event()
    
    async def initialize(self) -> None:
        """Initialize the agent registry with database and monitoring."""
        try:
            logger.info("Initializing MCP Agent Registry")
            
            # Load existing agents from database
            await self._load_agents_from_database()
            
            # Build capability indexes for fast lookup
            await self._build_capability_indexes()
            
            # Start background monitoring tasks
            asyncio.create_task(self._agent_health_monitor())
            asyncio.create_task(self._performance_metrics_collector())
            asyncio.create_task(self._security_audit_task())
            
            # Log initialization for audit
            await audit_logger.log_event(
                event_type=AuditEventType.SYSTEM_STARTUP,
                user_id="system",
                resource_type="mcp_agent_registry",
                action="registry_initialized",
                details={
                    "agent_count": len(self._agent_cache),
                    "indexed_specialties": len(self._capability_index),
                    "security_levels": list(self._security_clearance_index.keys())
                }
            )
            
            logger.info("MCP Agent Registry initialized successfully",
                       agent_count=len(self._agent_cache))
            
        except Exception as e:
            logger.error("Failed to initialize MCP Agent Registry", error=str(e))
            raise
    
    async def register_agent(self, agent_info: MCPAgentInfo) -> str:
        """
        Register a new medical AI agent with comprehensive validation.
        
        Args:
            agent_info: Complete agent information and capabilities
            
        Returns:
            str: Registration ID for tracking
            
        Raises:
            AgentRegistrationError: If registration fails validation
            SecurityValidationError: If security requirements not met
        """
        registration_id = f"reg_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{agent_info.agent_id[:8]}"
        
        try:
            logger.info("Processing agent registration",
                       agent_id=agent_info.agent_id,
                       registration_id=registration_id,
                       specialties=agent_info.capabilities.medical_specialties)
            
            # Phase 1: Pre-registration validation
            await self._validate_agent_prerequisites(agent_info)
            
            # Phase 2: Security clearance validation
            await self._validate_security_clearance(agent_info)
            
            # Phase 3: Compliance verification
            await self._verify_compliance_requirements(agent_info)
            
            # Phase 4: Capability assessment
            await self._assess_agent_capabilities(agent_info)
            
            # Phase 5: Database registration
            await self._store_agent_registration(agent_info, registration_id)
            
            # Phase 6: Index updates
            await self._update_capability_indexes(agent_info)
            
            # Phase 7: Cache updates
            self._agent_cache[agent_info.agent_id] = agent_info
            
            # Phase 8: Security event logging
            await self._log_registration_security_event(agent_info, registration_id, "success")
            
            # Phase 9: Audit logging for SOC2 compliance
            await audit_logger.log_event(
                event_type=AuditEventType.AGENT_REGISTERED,
                user_id="system",
                resource_type="mcp_agent",
                resource_id=agent_info.agent_id,
                action="agent_registered_successfully",
                details={
                    "registration_id": registration_id,
                    "agent_name": agent_info.agent_name,
                    "specialties": agent_info.capabilities.medical_specialties,
                    "security_clearance": agent_info.capabilities.security_clearance.value,
                    "phi_processing": agent_info.capabilities.supports_phi_processing,
                    "emergency_capable": agent_info.capabilities.supports_emergency_cases,
                    "compliance_verified": True
                }
            )
            
            logger.info("Agent registered successfully",
                       agent_id=agent_info.agent_id,
                       registration_id=registration_id,
                       total_agents=len(self._agent_cache))
            
            return registration_id
            
        except (AgentRegistrationError, SecurityValidationError) as e:
            # Log registration failure
            await self._log_registration_security_event(agent_info, registration_id, "failed", str(e))
            
            await audit_logger.log_event(
                event_type=AuditEventType.AGENT_REGISTRATION_FAILED,
                user_id="system",
                resource_type="mcp_agent",
                resource_id=agent_info.agent_id,
                action="agent_registration_failed",
                details={
                    "registration_id": registration_id,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }
            )
            
            logger.error("Agent registration failed",
                        agent_id=agent_info.agent_id,
                        registration_id=registration_id,
                        error=str(e))
            raise
            
        except Exception as e:
            # Unexpected error
            await self._log_registration_security_event(agent_info, registration_id, "error", str(e))
            logger.error("Unexpected error during agent registration",
                        agent_id=agent_info.agent_id,
                        error=str(e))
            raise AgentRegistrationError(f"Registration failed due to unexpected error: {e}")
    
    async def get_agent(self, agent_id: str) -> Optional[MCPAgentInfo]:
        """Get agent information by ID."""
        return self._agent_cache.get(agent_id)
    
    async def list_agents(self, 
                         status_filter: Optional[AgentStatus] = None,
                         specialty_filter: Optional[str] = None,
                         security_level_filter: Optional[SecurityLevel] = None) -> List[MCPAgentInfo]:
        """
        List agents with optional filtering.
        
        Args:
            status_filter: Filter by agent status
            specialty_filter: Filter by medical specialty  
            security_level_filter: Filter by security clearance level
            
        Returns:
            List[MCPAgentInfo]: Filtered list of agents
        """
        agents = list(self._agent_cache.values())
        
        # Apply filters
        if status_filter:
            agents = [agent for agent in agents if agent.status == status_filter]
        
        if specialty_filter:
            agents = [
                agent for agent in agents
                if specialty_filter in agent.capabilities.medical_specialties
            ]
        
        if security_level_filter:
            agents = [
                agent for agent in agents
                if agent.capabilities.security_clearance == security_level_filter
            ]
        
        return agents
    
    async def find_agents_by_capability(self, 
                                      specialties: List[str],
                                      urgency_level: MedicalUrgency = MedicalUrgency.ROUTINE,
                                      requires_phi_access: bool = False,
                                      min_confidence_threshold: float = 0.0) -> List[MCPAgentInfo]:
        """
        Find agents matching specific capability requirements.
        
        Args:
            specialties: Required medical specialties
            urgency_level: Required urgency handling capability
            requires_phi_access: Whether PHI processing is needed
            min_confidence_threshold: Minimum confidence threshold
            
        Returns:
            List[MCPAgentInfo]: Matching agents sorted by suitability
        """
        try:
            matching_agents = []
            
            for agent in self._agent_cache.values():
                # Check if agent is active
                if agent.status != AgentStatus.ACTIVE:
                    continue
                
                # Check specialty match
                agent_specialties = set(agent.capabilities.medical_specialties)
                required_specialties = set(specialties)
                
                if not required_specialties.intersection(agent_specialties):
                    # Check if it's an emergency and agent supports emergency cases
                    if urgency_level != MedicalUrgency.EMERGENCY or not agent.capabilities.supports_emergency_cases:
                        continue
                
                # Check PHI processing capability
                if requires_phi_access and not agent.capabilities.supports_phi_processing:
                    continue
                
                # Check confidence threshold
                if agent.capabilities.confidence_threshold < min_confidence_threshold:
                    continue
                
                # Check urgency handling capability
                if urgency_level == MedicalUrgency.EMERGENCY and not agent.capabilities.supports_emergency_cases:
                    continue
                
                matching_agents.append(agent)
            
            # Sort by suitability (accuracy score, response time, uptime)
            matching_agents.sort(key=lambda a: (
                -a.capabilities.accuracy_score,  # Higher accuracy first
                a.capabilities.average_response_time_ms,  # Faster response first
                -a.uptime_percentage  # Higher uptime first
            ))
            
            logger.info("Found matching agents",
                       specialties=specialties,
                       urgency=urgency_level.value,
                       requires_phi=requires_phi_access,
                       matches_found=len(matching_agents))
            
            return matching_agents
            
        except Exception as e:
            logger.error("Error finding agents by capability", error=str(e))
            return []
    
    async def update_agent_status(self, agent_id: str, status: AgentStatus, reason: Optional[str] = None) -> bool:
        """
        Update agent status with audit logging.
        
        Args:
            agent_id: Agent identifier
            status: New status
            reason: Optional reason for status change
            
        Returns:
            bool: True if update successful
        """
        try:
            if agent_id not in self._agent_cache:
                logger.warning("Attempted to update non-existent agent", agent_id=agent_id)
                return False
            
            old_status = self._agent_cache[agent_id].status
            self._agent_cache[agent_id].status = status
            self._agent_cache[agent_id].updated_at = datetime.utcnow()
            
            # Update in database
            async with get_db() as db:
                result = await db.execute(
                    select(MCPAgent).where(MCPAgent.agent_id == agent_id)
                )
                db_agent = result.scalar_one_or_none()
                
                if db_agent:
                    db_agent.status = status.value
                    db_agent.updated_at = datetime.utcnow()
                    await db.commit()
            
            # Log status change for audit
            await audit_logger.log_event(
                event_type=AuditEventType.AGENT_STATUS_CHANGED,
                user_id="system",
                resource_type="mcp_agent",
                resource_id=agent_id,
                action="status_updated",
                details={
                    "old_status": old_status.value,
                    "new_status": status.value,
                    "reason": reason,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            logger.info("Agent status updated",
                       agent_id=agent_id,
                       old_status=old_status.value,
                       new_status=status.value,
                       reason=reason)
            
            return True
            
        except Exception as e:
            logger.error("Failed to update agent status",
                        agent_id=agent_id,
                        status=status.value,
                        error=str(e))
            return False
    
    async def record_agent_performance(self, agent_id: str, performance_data: Dict[str, Any]) -> None:
        """
        Record performance metrics for an agent.
        
        Args:
            agent_id: Agent identifier
            performance_data: Performance metrics data
        """
        try:
            if agent_id not in self._agent_cache:
                logger.warning("Performance data for non-existent agent", agent_id=agent_id)
                return
            
            # Update cache
            self._performance_cache[agent_id] = performance_data
            
            # Store in database
            async with get_db() as db:
                metrics = MCPPerformanceMetrics(
                    agent_id=agent_id,
                    measurement_timestamp=datetime.utcnow(),
                    response_time_ms=performance_data.get("response_time_ms", 0.0),
                    cpu_usage_percent=performance_data.get("cpu_usage_percent"),
                    memory_usage_mb=performance_data.get("memory_usage_mb"),
                    active_connections=performance_data.get("active_connections", 0),
                    messages_processed_last_hour=performance_data.get("messages_processed_last_hour", 0),
                    messages_failed_last_hour=performance_data.get("messages_failed_last_hour", 0),
                    average_confidence_score=performance_data.get("average_confidence_score"),
                    consultations_completed=performance_data.get("consultations_completed", 0),
                    consultations_escalated=performance_data.get("consultations_escalated", 0),
                    accuracy_score=performance_data.get("accuracy_score"),
                    uptime_seconds=performance_data.get("uptime_seconds", 0),
                    error_rate_percent=performance_data.get("error_rate_percent", 0.0),
                    phi_accesses_compliant=performance_data.get("phi_accesses_compliant", 0),
                    phi_accesses_total=performance_data.get("phi_accesses_total", 0),
                    audit_logs_generated=performance_data.get("audit_logs_generated", 0)
                )
                
                db.add(metrics)
                await db.commit()
            
            # Update agent info with latest performance
            agent = self._agent_cache[agent_id]
            if "response_time_ms" in performance_data:
                agent.capabilities.average_response_time_ms = int(performance_data["response_time_ms"])
            if "accuracy_score" in performance_data:
                agent.capabilities.accuracy_score = performance_data["accuracy_score"]
            
            logger.debug("Performance data recorded",
                        agent_id=agent_id,
                        metrics_count=len(performance_data))
            
        except Exception as e:
            logger.error("Failed to record agent performance",
                        agent_id=agent_id,
                        error=str(e))
    
    async def deregister_agent(self, agent_id: str, reason: str) -> bool:
        """
        Deregister an agent with audit logging.
        
        Args:
            agent_id: Agent identifier
            reason: Reason for deregistration
            
        Returns:
            bool: True if deregistration successful
        """
        try:
            if agent_id not in self._agent_cache:
                logger.warning("Attempted to deregister non-existent agent", agent_id=agent_id)
                return False
            
            agent_info = self._agent_cache[agent_id]
            
            # Mark as offline in database (soft delete for audit trail)
            async with get_db() as db:
                result = await db.execute(
                    select(MCPAgent).where(MCPAgent.agent_id == agent_id)
                )
                db_agent = result.scalar_one_or_none()
                
                if db_agent:
                    db_agent.status = AgentStatus.OFFLINE.value
                    db_agent.updated_at = datetime.utcnow()
                    # Store deregistration reason in audit metadata
                    audit_metadata = db_agent.audit_metadata or {}
                    audit_metadata["deregistration_reason"] = reason
                    audit_metadata["deregistered_at"] = datetime.utcnow().isoformat()
                    db_agent.audit_metadata = audit_metadata
                    await db.commit()
            
            # Remove from indexes and cache
            await self._remove_from_indexes(agent_id)
            del self._agent_cache[agent_id]
            if agent_id in self._performance_cache:
                del self._performance_cache[agent_id]
            
            # Log deregistration for audit
            await audit_logger.log_event(
                event_type=AuditEventType.AGENT_DEREGISTERED,
                user_id="system",
                resource_type="mcp_agent",
                resource_id=agent_id,
                action="agent_deregistered",
                details={
                    "agent_name": agent_info.agent_name,
                    "reason": reason,
                    "specialties": agent_info.capabilities.medical_specialties,
                    "total_consultations": agent_info.total_consultations,
                    "deregistration_timestamp": datetime.utcnow().isoformat()
                }
            )
            
            logger.info("Agent deregistered successfully",
                       agent_id=agent_id,
                       reason=reason,
                       remaining_agents=len(self._agent_cache))
            
            return True
            
        except Exception as e:
            logger.error("Failed to deregister agent",
                        agent_id=agent_id,
                        error=str(e))
            return False
    
    async def get_registry_statistics(self) -> Dict[str, Any]:
        """Get comprehensive registry statistics for monitoring."""
        try:
            stats = {
                "total_agents": len(self._agent_cache),
                "active_agents": len([a for a in self._agent_cache.values() if a.status == AgentStatus.ACTIVE]),
                "offline_agents": len([a for a in self._agent_cache.values() if a.status == AgentStatus.OFFLINE]),
                "busy_agents": len([a for a in self._agent_cache.values() if a.status == AgentStatus.BUSY]),
                "error_agents": len([a for a in self._agent_cache.values() if a.status == AgentStatus.ERROR]),
                "specialties_covered": len(self._capability_index),
                "security_levels": {
                    level.value: len(agents) 
                    for level, agents in self._security_clearance_index.items()
                },
                "phi_capable_agents": len([
                    a for a in self._agent_cache.values() 
                    if a.capabilities.supports_phi_processing
                ]),
                "emergency_capable_agents": len([
                    a for a in self._agent_cache.values() 
                    if a.capabilities.supports_emergency_cases
                ]),
                "total_consultations": sum(a.total_consultations for a in self._agent_cache.values()),
                "average_uptime": sum(a.uptime_percentage for a in self._agent_cache.values()) / max(len(self._agent_cache), 1),
                "registry_uptime_hours": (datetime.utcnow() - datetime.utcnow().replace(hour=0, minute=0, second=0)).total_seconds() / 3600
            }
            
            return stats
            
        except Exception as e:
            logger.error("Failed to generate registry statistics", error=str(e))
            return {"error": str(e)}
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the agent registry."""
        logger.info("Shutting down MCP Agent Registry")
        
        # Signal shutdown to background tasks
        self._shutdown_event.set()
        
        # Mark all agents as offline
        for agent_id in list(self._agent_cache.keys()):
            await self.update_agent_status(agent_id, AgentStatus.OFFLINE, "registry_shutdown")
        
        # Log shutdown for audit
        await audit_logger.log_event(
            event_type=AuditEventType.SYSTEM_SHUTDOWN,
            user_id="system",
            resource_type="mcp_agent_registry",
            action="registry_shutdown",
            details={
                "final_agent_count": len(self._agent_cache),
                "shutdown_timestamp": datetime.utcnow().isoformat()
            }
        )
        
        logger.info("MCP Agent Registry shutdown complete")
    
    # Private helper methods
    
    async def _validate_agent_prerequisites(self, agent_info: MCPAgentInfo) -> None:
        """Validate basic prerequisites for agent registration."""
        if not agent_info.agent_id or len(agent_info.agent_id) < 3:
            raise AgentRegistrationError("Agent ID must be at least 3 characters")
        
        if not agent_info.agent_name or len(agent_info.agent_name) < 3:
            raise AgentRegistrationError("Agent name must be at least 3 characters")
        
        if not agent_info.capabilities.medical_specialties:
            raise AgentRegistrationError("At least one medical specialty is required")
        
        # Check for duplicate agent ID
        if agent_info.agent_id in self._agent_cache:
            raise AgentRegistrationError(f"Agent ID already registered: {agent_info.agent_id}")
    
    async def _validate_security_clearance(self, agent_info: MCPAgentInfo) -> None:
        """Validate security clearance and permissions."""
        capabilities = agent_info.capabilities
        
        # Check HIPAA compliance requirement
        if not capabilities.hipaa_compliant:
            raise SecurityValidationError("Agent must be HIPAA compliant for healthcare platform")
        
        # Check SOC2 compliance requirement
        if not capabilities.soc2_compliant:
            raise SecurityValidationError("Agent must be SOC2 Type II compliant")
        
        # Validate PHI processing authorization
        if capabilities.supports_phi_processing:
            if capabilities.security_clearance == SecurityLevel.PUBLIC:
                raise SecurityValidationError("PHI processing requires higher security clearance")
            
            if not agent_info.public_key:
                raise SecurityValidationError("Public key required for PHI processing agents")
        
        # Validate emergency processing authorization
        if capabilities.supports_emergency_cases:
            if capabilities.security_clearance == SecurityLevel.PUBLIC:
                raise SecurityValidationError("Emergency processing requires security clearance")
    
    async def _verify_compliance_requirements(self, agent_info: MCPAgentInfo) -> None:
        """Verify healthcare compliance requirements."""
        capabilities = agent_info.capabilities
        
        # Check FHIR compliance
        if not capabilities.supported_fhir_resources:
            logger.warning("Agent has no FHIR resource support", agent_id=agent_info.agent_id)
        
        # Validate confidence threshold
        if capabilities.confidence_threshold < 0.1 or capabilities.confidence_threshold > 1.0:
            raise AgentRegistrationError("Confidence threshold must be between 0.1 and 1.0")
        
        # Check response time requirements
        if capabilities.average_response_time_ms > 30000:  # 30 seconds
            logger.warning("Agent has high response time",
                          agent_id=agent_info.agent_id,
                          response_time=capabilities.average_response_time_ms)
    
    async def _assess_agent_capabilities(self, agent_info: MCPAgentInfo) -> None:
        """Assess and validate agent capabilities."""
        capabilities = agent_info.capabilities
        
        # Validate medical specialties
        valid_specialties = {
            'cardiology', 'neurology', 'emergency_medicine', 'internal_medicine',
            'pulmonology', 'endocrinology', 'psychiatry', 'dermatology',
            'radiology', 'pathology', 'general_practice', 'oncology',
            'pediatrics', 'obstetrics_gynecology', 'orthopedics', 'anesthesiology'
        }
        
        invalid_specialties = set(capabilities.medical_specialties) - valid_specialties
        if invalid_specialties:
            raise AgentRegistrationError(f"Invalid medical specialties: {invalid_specialties}")
        
        # Validate concurrent consultation limits
        if capabilities.max_concurrent_consultations > 100:
            raise AgentRegistrationError("Maximum concurrent consultations limit too high (max 100)")
        
        if capabilities.max_concurrent_consultations < 1:
            raise AgentRegistrationError("Must support at least 1 concurrent consultation")
    
    async def _store_agent_registration(self, agent_info: MCPAgentInfo, registration_id: str) -> None:
        """Store agent registration in database."""
        try:
            async with get_db() as db:
                db_agent = MCPAgent(
                    agent_id=agent_info.agent_id,
                    agent_name=agent_info.agent_name,
                    status=agent_info.status.value,
                    capabilities=agent_info.capabilities.model_dump(),
                    endpoint_url=agent_info.endpoint_url,
                    public_key=agent_info.public_key,
                    total_consultations=agent_info.total_consultations,
                    average_rating=agent_info.average_rating,
                    uptime_percentage=agent_info.uptime_percentage,
                    compliance_status=agent_info.compliance_status,
                    security_clearance=agent_info.capabilities.security_clearance.value,
                    phi_access_approved=agent_info.capabilities.supports_phi_processing,
                    hipaa_compliant=agent_info.capabilities.hipaa_compliant,
                    soc2_compliant=agent_info.capabilities.soc2_compliant,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    audit_metadata={"registration_id": registration_id}
                )
                
                # Generate audit hash for integrity
                agent_data = agent_info.model_dump_json()
                db_agent.audit_hash = hashlib.sha256(agent_data.encode()).hexdigest()
                
                db.add(db_agent)
                await db.commit()
                await db.refresh(db_agent)
                
        except Exception as e:
            logger.error("Failed to store agent registration", error=str(e))
            raise AgentRegistrationError(f"Database storage failed: {e}")
    
    async def _update_capability_indexes(self, agent_info: MCPAgentInfo) -> None:
        """Update capability indexes for fast lookup."""
        agent_id = agent_info.agent_id
        
        # Update specialty index
        for specialty in agent_info.capabilities.medical_specialties:
            if specialty not in self._capability_index:
                self._capability_index[specialty] = set()
            self._capability_index[specialty].add(agent_id)
        
        # Update security clearance index
        clearance = agent_info.capabilities.security_clearance
        if clearance not in self._security_clearance_index:
            self._security_clearance_index[clearance] = set()
        self._security_clearance_index[clearance].add(agent_id)
    
    async def _remove_from_indexes(self, agent_id: str) -> None:
        """Remove agent from all indexes."""
        # Remove from specialty index
        for specialty_agents in self._capability_index.values():
            specialty_agents.discard(agent_id)
        
        # Remove from security clearance index
        for clearance_agents in self._security_clearance_index.values():
            clearance_agents.discard(agent_id)
    
    async def _load_agents_from_database(self) -> None:
        """Load existing agents from database."""
        try:
            async with get_db() as db:
                result = await db.execute(
                    select(MCPAgent).where(MCPAgent.status != "deregistered")
                )
                db_agents = result.scalars().all()
                
                for db_agent in db_agents:
                    # Reconstruct agent info
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
                        last_heartbeat=db_agent.last_heartbeat,
                        compliance_status=db_agent.compliance_status,
                        created_at=db_agent.created_at,
                        updated_at=db_agent.updated_at
                    )
                    
                    self._agent_cache[db_agent.agent_id] = agent_info
                    
            logger.info(f"Loaded {len(self._agent_cache)} agents from database")
            
        except Exception as e:
            logger.error("Failed to load agents from database", error=str(e))
            raise
    
    async def _build_capability_indexes(self) -> None:
        """Build capability indexes from loaded agents."""
        self._capability_index.clear()
        self._security_clearance_index.clear()
        
        for agent_info in self._agent_cache.values():
            await self._update_capability_indexes(agent_info)
        
        logger.info("Built capability indexes",
                   specialties=len(self._capability_index),
                   security_levels=len(self._security_clearance_index))
    
    async def _log_registration_security_event(self, agent_info: MCPAgentInfo, 
                                             registration_id: str, 
                                             status: str, 
                                             error_message: Optional[str] = None) -> None:
        """Log security event for agent registration."""
        try:
            async with get_db() as db:
                security_event = MCPSecurityEvent(
                    event_id=f"reg_{registration_id}",
                    event_type="agent_registration",
                    severity_level="medium" if status == "success" else "high",
                    agent_id=agent_info.agent_id,
                    security_violation_type="registration_attempt" if status != "success" else None,
                    attempted_action=f"register_agent_{agent_info.agent_id}",
                    access_denied_reason=error_message if status == "failed" else None,
                    phi_potentially_exposed=False,
                    systems_affected=["mcp_agent_registry"],
                    automated_response_taken=True,
                    incident_resolved=status == "success",
                    event_timestamp=datetime.utcnow(),
                    detection_timestamp=datetime.utcnow(),
                    resolution_timestamp=datetime.utcnow() if status == "success" else None
                )
                
                db.add(security_event)
                await db.commit()
                
        except Exception as e:
            logger.error("Failed to log registration security event", error=str(e))
    
    # Background monitoring tasks
    
    async def _agent_health_monitor(self) -> None:
        """Background task to monitor agent health."""
        while not self._shutdown_event.is_set():
            try:
                current_time = datetime.utcnow()
                
                for agent_id, agent_info in list(self._agent_cache.items()):
                    # Check heartbeat timeout
                    if (agent_info.last_heartbeat and 
                        (current_time - agent_info.last_heartbeat).total_seconds() > 300):  # 5 minutes
                        
                        await self.update_agent_status(
                            agent_id, 
                            AgentStatus.OFFLINE, 
                            "heartbeat_timeout"
                        )
                        
                        logger.warning("Agent marked offline due to heartbeat timeout",
                                     agent_id=agent_id,
                                     last_heartbeat=agent_info.last_heartbeat)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error("Agent health monitor error", error=str(e))
                await asyncio.sleep(60)
    
    async def _performance_metrics_collector(self) -> None:
        """Background task to collect performance metrics."""
        while not self._shutdown_event.is_set():
            try:
                # Collect registry-wide performance metrics
                stats = await self.get_registry_statistics()
                
                # Log performance metrics for monitoring
                logger.info("Registry performance metrics",
                           total_agents=stats["total_agents"],
                           active_agents=stats["active_agents"],
                           average_uptime=stats["average_uptime"])
                
                await asyncio.sleep(300)  # Every 5 minutes
                
            except Exception as e:
                logger.error("Performance metrics collector error", error=str(e))
                await asyncio.sleep(300)
    
    async def _security_audit_task(self) -> None:
        """Background task for security auditing."""
        while not self._shutdown_event.is_set():
            try:
                # Audit agent compliance status
                non_compliant_agents = []
                
                for agent_id, agent_info in self._agent_cache.items():
                    if (not agent_info.capabilities.hipaa_compliant or
                        not agent_info.capabilities.soc2_compliant):
                        non_compliant_agents.append(agent_id)
                
                if non_compliant_agents:
                    logger.warning("Non-compliant agents detected",
                                 agent_count=len(non_compliant_agents),
                                 agents=non_compliant_agents)
                
                # Check for expired compliance validations
                current_time = datetime.utcnow()
                for agent_info in self._agent_cache.values():
                    if (agent_info.last_compliance_check and
                        (current_time - agent_info.last_compliance_check).days > 90):
                        
                        logger.warning("Agent compliance check overdue",
                                     agent_id=agent_info.agent_id,
                                     days_overdue=(current_time - agent_info.last_compliance_check).days)
                
                await asyncio.sleep(3600)  # Every hour
                
            except Exception as e:
                logger.error("Security audit task error", error=str(e))
                await asyncio.sleep(3600)