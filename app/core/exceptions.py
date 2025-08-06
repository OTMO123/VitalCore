"""
Core exceptions for the IRIS API Integration System.
"""


class IRISBaseException(Exception):
    """Base exception for IRIS system."""
    pass


class BusinessRuleViolation(IRISBaseException):
    """Raised when a business rule is violated."""
    pass


class ResourceNotFound(IRISBaseException):
    """Raised when a requested resource is not found."""
    pass


class UnauthorizedAccess(IRISBaseException):
    """Raised when user attempts unauthorized access."""
    pass


class ValidationError(IRISBaseException):
    """Raised when data validation fails."""
    pass


class EncryptionError(IRISBaseException):
    """Raised when encryption/decryption operations fail."""
    pass


class FHIRValidationError(IRISBaseException):
    """Raised when FHIR validation fails."""
    pass


class ConsentViolation(IRISBaseException):
    """Raised when patient consent requirements are violated."""
    pass


class PHIAccessViolation(IRISBaseException):
    """Raised when PHI access rules are violated."""
    pass


class DataRetentionViolation(IRISBaseException):
    """Raised when data retention policies are violated."""
    pass


class AuditLogError(IRISBaseException):
    """Raised when audit logging fails."""
    pass


class EventBusError(IRISBaseException):
    """Raised when event bus operations fail."""
    pass


class CircuitBreakerError(IRISBaseException):
    """Raised when circuit breaker is open."""
    pass


class RateLimitExceeded(IRISBaseException):
    """Raised when rate limits are exceeded."""
    pass


class AnalyticsError(IRISBaseException):
    """Raised when analytics operations fail."""
    pass


class RiskCalculationError(IRISBaseException):
    """Raised when risk calculation operations fail."""
    
    def __init__(self, error_code: str, message: str, patient_id: str = None, correlation_id: str = None):
        self.error_code = error_code
        self.message = message
        self.patient_id = patient_id
        self.correlation_id = correlation_id
        super().__init__(self.message)


class SOC2ComplianceError(IRISBaseException):
    """Raised when SOC2 compliance violations occur."""
    
    def __init__(self, control_id: str, violation_type: str, severity: str, message: str, remediation_required: bool = True):
        self.control_id = control_id
        self.violation_type = violation_type
        self.severity = severity
        self.message = message
        self.remediation_required = remediation_required
        super().__init__(self.message)