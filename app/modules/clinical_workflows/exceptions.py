"""
Clinical Workflows Exceptions

Custom exceptions for clinical workflow operations with detailed error information
for debugging, auditing, and user feedback.
"""

from typing import Optional, Dict, Any, List
from uuid import UUID


class ClinicalWorkflowException(Exception):
    """Base exception for all clinical workflow operations."""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)


class WorkflowNotFoundError(ClinicalWorkflowException):
    """Workflow not found in the system."""
    
    def __init__(self, workflow_id: str, **kwargs):
        message = f"Clinical workflow not found: {workflow_id}"
        details = {"workflow_id": workflow_id}
        super().__init__(message, "WORKFLOW_NOT_FOUND", details, **kwargs)


class WorkflowStepNotFoundError(ClinicalWorkflowException):
    """Workflow step not found."""
    
    def __init__(self, step_id: str, workflow_id: Optional[str] = None, **kwargs):
        message = f"Workflow step not found: {step_id}"
        details = {"step_id": step_id}
        if workflow_id:
            details["workflow_id"] = workflow_id
        super().__init__(message, "WORKFLOW_STEP_NOT_FOUND", details, **kwargs)


class EncounterNotFoundError(ClinicalWorkflowException):
    """Clinical encounter not found."""
    
    def __init__(self, encounter_id: str, **kwargs):
        message = f"Clinical encounter not found: {encounter_id}"
        details = {"encounter_id": encounter_id}
        super().__init__(message, "ENCOUNTER_NOT_FOUND", details, **kwargs)


# Security and Authorization Exceptions

class PatientConsentRequiredError(ClinicalWorkflowException):
    """Patient consent verification failed or not found."""
    
    def __init__(
        self, 
        patient_id: str, 
        workflow_type: str,
        consent_type: Optional[str] = None,
        **kwargs
    ):
        message = f"Patient consent required for {workflow_type} workflow"
        details = {
            "patient_id": patient_id,
            "workflow_type": workflow_type,
            "consent_type": consent_type
        }
        super().__init__(message, "PATIENT_CONSENT_REQUIRED", details, **kwargs)


class ProviderAuthorizationError(ClinicalWorkflowException):
    """Provider lacks required permissions for clinical action."""
    
    def __init__(
        self, 
        provider_id: str, 
        action: str,
        patient_id: Optional[str] = None,
        required_permission: Optional[str] = None,
        **kwargs
    ):
        message = f"Provider {provider_id} not authorized for action: {action}"
        details = {
            "provider_id": provider_id,
            "action": action,
            "patient_id": patient_id,
            "required_permission": required_permission
        }
        super().__init__(message, "PROVIDER_AUTHORIZATION_ERROR", details, **kwargs)


class PHIAccessDeniedError(ClinicalWorkflowException):
    """Access to PHI data denied."""
    
    def __init__(
        self, 
        user_id: str, 
        patient_id: str,
        phi_field: str,
        reason: Optional[str] = None,
        **kwargs
    ):
        message = f"PHI access denied for field {phi_field}"
        details = {
            "user_id": user_id,
            "patient_id": patient_id,
            "phi_field": phi_field,
            "reason": reason
        }
        super().__init__(message, "PHI_ACCESS_DENIED", details, **kwargs)


class ConsentVerificationError(ClinicalWorkflowException):
    """Consent verification process failed."""
    
    def __init__(
        self, 
        patient_id: str, 
        consent_type: str,
        verification_error: Optional[str] = None,
        **kwargs
    ):
        message = f"Consent verification failed for {consent_type}"
        details = {
            "patient_id": patient_id,
            "consent_type": consent_type,
            "verification_error": verification_error
        }
        super().__init__(message, "CONSENT_VERIFICATION_ERROR", details, **kwargs)


# Validation Exceptions

class FHIRValidationError(ClinicalWorkflowException):
    """FHIR R4 resource validation failed."""
    
    def __init__(
        self, 
        resource_type: str, 
        validation_errors: List[str],
        resource_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        message = f"FHIR {resource_type} validation failed: {'; '.join(validation_errors)}"
        details = {
            "resource_type": resource_type,
            "validation_errors": validation_errors,
            "resource_data": resource_data
        }
        super().__init__(message, "FHIR_VALIDATION_ERROR", details, **kwargs)


class ClinicalCodeValidationError(ClinicalWorkflowException):
    """Clinical code validation failed."""
    
    def __init__(
        self, 
        code_system: str, 
        invalid_codes: List[str],
        validation_errors: Optional[List[str]] = None,
        **kwargs
    ):
        message = f"Invalid {code_system} codes: {', '.join(invalid_codes)}"
        details = {
            "code_system": code_system,
            "invalid_codes": invalid_codes,
            "validation_errors": validation_errors or []
        }
        super().__init__(message, "CLINICAL_CODE_VALIDATION_ERROR", details, **kwargs)


class VitalSignsValidationError(ClinicalWorkflowException):
    """Vital signs validation failed."""
    
    def __init__(
        self, 
        validation_errors: List[str],
        vital_signs_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        message = f"Vital signs validation failed: {'; '.join(validation_errors)}"
        details = {
            "validation_errors": validation_errors,
            "vital_signs_data": vital_signs_data
        }
        super().__init__(message, "VITAL_SIGNS_VALIDATION_ERROR", details, **kwargs)


class WorkflowValidationError(ClinicalWorkflowException):
    """General workflow validation failed."""
    
    def __init__(
        self, 
        field_name: str, 
        field_value: Any,
        validation_message: str,
        **kwargs
    ):
        message = f"Workflow validation failed for {field_name}: {validation_message}"
        details = {
            "field_name": field_name,
            "field_value": str(field_value),
            "validation_message": validation_message
        }
        super().__init__(message, "WORKFLOW_VALIDATION_ERROR", details, **kwargs)


# Workflow State Exceptions

class InvalidWorkflowStatusError(ClinicalWorkflowException):
    """Invalid workflow status transition."""
    
    def __init__(
        self, 
        workflow_id: str,
        current_status: str,
        attempted_status: str,
        **kwargs
    ):
        message = f"Invalid status transition from {current_status} to {attempted_status}"
        details = {
            "workflow_id": workflow_id,
            "current_status": current_status,
            "attempted_status": attempted_status
        }
        super().__init__(message, "INVALID_WORKFLOW_STATUS", details, **kwargs)


class WorkflowAlreadyCompletedError(ClinicalWorkflowException):
    """Cannot modify completed workflow."""
    
    def __init__(self, workflow_id: str, completed_at: str, **kwargs):
        message = f"Workflow {workflow_id} already completed at {completed_at}"
        details = {
            "workflow_id": workflow_id,
            "completed_at": completed_at
        }
        super().__init__(message, "WORKFLOW_ALREADY_COMPLETED", details, **kwargs)


class WorkflowStepOrderError(ClinicalWorkflowException):
    """Workflow step order violation."""
    
    def __init__(
        self, 
        workflow_id: str,
        step_order: int,
        reason: str,
        **kwargs
    ):
        message = f"Step order error in workflow {workflow_id}: {reason}"
        details = {
            "workflow_id": workflow_id,
            "step_order": step_order,
            "reason": reason
        }
        super().__init__(message, "WORKFLOW_STEP_ORDER_ERROR", details, **kwargs)


class WorkflowConcurrencyError(ClinicalWorkflowException):
    """Concurrent modification of workflow detected."""
    
    def __init__(
        self, 
        workflow_id: str,
        current_version: int,
        attempted_version: int,
        **kwargs
    ):
        message = f"Concurrent modification detected for workflow {workflow_id}"
        details = {
            "workflow_id": workflow_id,
            "current_version": current_version,
            "attempted_version": attempted_version
        }
        super().__init__(message, "WORKFLOW_CONCURRENCY_ERROR", details, **kwargs)


# Data and Encryption Exceptions

class PHIEncryptionError(ClinicalWorkflowException):
    """PHI data encryption failed."""
    
    def __init__(
        self, 
        field_name: str, 
        patient_id: str,
        encryption_error: Optional[str] = None,
        **kwargs
    ):
        message = f"Failed to encrypt PHI field {field_name}"
        details = {
            "field_name": field_name,
            "patient_id": patient_id,
            "encryption_error": encryption_error
        }
        super().__init__(message, "PHI_ENCRYPTION_ERROR", details, **kwargs)


class PHIDecryptionError(ClinicalWorkflowException):
    """PHI data decryption failed."""
    
    def __init__(
        self, 
        field_name: str, 
        patient_id: str,
        decryption_error: Optional[str] = None,
        **kwargs
    ):
        message = f"Failed to decrypt PHI field {field_name}"
        details = {
            "field_name": field_name,
            "patient_id": patient_id,
            "decryption_error": decryption_error
        }
        super().__init__(message, "PHI_DECRYPTION_ERROR", details, **kwargs)


class DataIntegrityError(ClinicalWorkflowException):
    """Data integrity check failed."""
    
    def __init__(
        self, 
        entity_type: str, 
        entity_id: str,
        integrity_check: str,
        **kwargs
    ):
        message = f"Data integrity check failed for {entity_type} {entity_id}: {integrity_check}"
        details = {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "integrity_check": integrity_check
        }
        super().__init__(message, "DATA_INTEGRITY_ERROR", details, **kwargs)


# Business Logic Exceptions

class ClinicalBusinessRuleError(ClinicalWorkflowException):
    """Clinical business rule validation failed."""
    
    def __init__(
        self, 
        rule_name: str, 
        rule_description: str,
        workflow_id: Optional[str] = None,
        **kwargs
    ):
        message = f"Clinical business rule violation: {rule_name}"
        details = {
            "rule_name": rule_name,
            "rule_description": rule_description,
            "workflow_id": workflow_id
        }
        super().__init__(message, "CLINICAL_BUSINESS_RULE_ERROR", details, **kwargs)


class DuplicateWorkflowError(ClinicalWorkflowException):
    """Duplicate workflow detected."""
    
    def __init__(
        self, 
        patient_id: str, 
        workflow_type: str,
        existing_workflow_id: str,
        **kwargs
    ):
        message = f"Duplicate {workflow_type} workflow found for patient {patient_id}"
        details = {
            "patient_id": patient_id,
            "workflow_type": workflow_type,
            "existing_workflow_id": existing_workflow_id
        }
        super().__init__(message, "DUPLICATE_WORKFLOW_ERROR", details, **kwargs)


class IncompleteWorkflowError(ClinicalWorkflowException):
    """Workflow cannot be completed due to missing required steps."""
    
    def __init__(
        self, 
        workflow_id: str, 
        missing_steps: List[str],
        completion_percentage: Optional[int] = None,
        **kwargs
    ):
        message = f"Workflow {workflow_id} incomplete: missing steps {', '.join(missing_steps)}"
        details = {
            "workflow_id": workflow_id,
            "missing_steps": missing_steps,
            "completion_percentage": completion_percentage
        }
        super().__init__(message, "INCOMPLETE_WORKFLOW_ERROR", details, **kwargs)


# Integration Exceptions

class FHIRResourceNotFoundError(ClinicalWorkflowException):
    """FHIR resource not found in external system."""
    
    def __init__(
        self, 
        resource_type: str, 
        resource_id: str,
        fhir_server: Optional[str] = None,
        **kwargs
    ):
        message = f"FHIR {resource_type} resource not found: {resource_id}"
        details = {
            "resource_type": resource_type,
            "resource_id": resource_id,
            "fhir_server": fhir_server
        }
        super().__init__(message, "FHIR_RESOURCE_NOT_FOUND", details, **kwargs)


class ExternalSystemIntegrationError(ClinicalWorkflowException):
    """External system integration failed."""
    
    def __init__(
        self, 
        system_name: str, 
        operation: str,
        error_message: Optional[str] = None,
        **kwargs
    ):
        message = f"Integration with {system_name} failed for operation {operation}"
        details = {
            "system_name": system_name,
            "operation": operation,
            "error_message": error_message
        }
        super().__init__(message, "EXTERNAL_SYSTEM_INTEGRATION_ERROR", details, **kwargs)


# Quality and Compliance Exceptions

class DocumentationQualityError(ClinicalWorkflowException):
    """Documentation quality requirements not met."""
    
    def __init__(
        self, 
        workflow_id: str, 
        quality_issues: List[str],
        current_quality_score: Optional[int] = None,
        **kwargs
    ):
        message = f"Documentation quality issues in workflow {workflow_id}"
        details = {
            "workflow_id": workflow_id,
            "quality_issues": quality_issues,
            "current_quality_score": current_quality_score
        }
        super().__init__(message, "DOCUMENTATION_QUALITY_ERROR", details, **kwargs)


class ComplianceViolationError(ClinicalWorkflowException):
    """Compliance requirement violation detected."""
    
    def __init__(
        self, 
        compliance_standard: str, 
        violation_type: str,
        violation_details: str,
        workflow_id: Optional[str] = None,
        **kwargs
    ):
        message = f"{compliance_standard} compliance violation: {violation_type}"
        details = {
            "compliance_standard": compliance_standard,
            "violation_type": violation_type,
            "violation_details": violation_details,
            "workflow_id": workflow_id
        }
        super().__init__(message, "COMPLIANCE_VIOLATION_ERROR", details, **kwargs)


class AuditTrailError(ClinicalWorkflowException):
    """Audit trail creation or verification failed."""
    
    def __init__(
        self, 
        audit_action: str, 
        entity_id: str,
        audit_error: str,
        **kwargs
    ):
        message = f"Audit trail error for {audit_action} on {entity_id}: {audit_error}"
        details = {
            "audit_action": audit_action,
            "entity_id": entity_id,
            "audit_error": audit_error
        }
        super().__init__(message, "AUDIT_TRAIL_ERROR", details, **kwargs)


# AI and Data Collection Exceptions

class AIDataCollectionError(ClinicalWorkflowException):
    """AI training data collection failed."""
    
    def __init__(
        self, 
        data_type: str, 
        workflow_id: str,
        collection_error: str,
        **kwargs
    ):
        message = f"AI data collection failed for {data_type}: {collection_error}"
        details = {
            "data_type": data_type,
            "workflow_id": workflow_id,
            "collection_error": collection_error
        }
        super().__init__(message, "AI_DATA_COLLECTION_ERROR", details, **kwargs)


class AnonymizationError(ClinicalWorkflowException):
    """Data anonymization process failed."""
    
    def __init__(
        self, 
        data_type: str, 
        anonymization_method: str,
        anonymization_error: str,
        **kwargs
    ):
        message = f"Anonymization failed for {data_type} using {anonymization_method}"
        details = {
            "data_type": data_type,
            "anonymization_method": anonymization_method,
            "anonymization_error": anonymization_error
        }
        super().__init__(message, "ANONYMIZATION_ERROR", details, **kwargs)