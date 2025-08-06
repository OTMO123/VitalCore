"""
MCP (Model Context Protocol) Module for Healthcare Platform V2.0

Secure communication protocol for AI agents with full HIPAA/SOC2 compliance.
Enables encrypted agent-to-agent communication with audit trails and PHI protection.
"""

from .protocol import MCPProtocol, MCPMessage, MCPResponse
from .agent_registry import AgentRegistry, AgentCapabilities
from .security_layer import MCPSecurity
from .schemas import (
    MCPMessageType, AgentStatus, SecurityLevel,
    MCPAgentInfo, ConsultationRequest, ConsultationResponse
)

# Export main classes for easy import
__all__ = [
    "MCPProtocol",
    "MCPMessage", 
    "MCPResponse",
    "AgentRegistry",
    "AgentCapabilities",
    "MCPSecurity",
    "MCPMessageType",
    "AgentStatus",
    "SecurityLevel",
    "MCPAgentInfo",
    "ConsultationRequest",
    "ConsultationResponse"
]

# Module version for compatibility tracking
__version__ = "1.0.0"