"""
A2A (Agent-to-Agent) Communication Framework for Healthcare Platform V2.0

Advanced agent collaboration system enabling medical specialty agents to work together
on complex cases with full HIPAA/SOC2 compliance and audit trails.
"""

from .coordinator import A2ACoordinator
from .medical_agents import MedicalAgentFactory, BaseSpecialtyAgent
from .collaboration import CollaborationEngine, CollaborationSession
from .consensus import ConsensusEngine, ConsensusResult
from .schemas import (
    CollaborationRequest, CollaborationResponse, AgentCollaboration,
    MedicalSpecialty, ConsensusType, AgentRecommendation
)
from .models import A2ACollaborationSession, A2AAgentInteraction, A2AConsensusRecord

# Export main classes for easy import
__all__ = [
    "A2ACoordinator",
    "MedicalAgentFactory",
    "BaseSpecialtyAgent", 
    "CollaborationEngine",
    "CollaborationSession",
    "ConsensusEngine",
    "ConsensusResult",
    "CollaborationRequest",
    "CollaborationResponse", 
    "AgentCollaboration",
    "MedicalSpecialty",
    "ConsensusType",
    "AgentRecommendation",
    "A2ACollaborationSession",
    "A2AAgentInteraction",
    "A2AConsensusRecord"
]

# Module version for compatibility tracking
__version__ = "1.0.0"