"""
Patient Service Layer

Enhanced business logic for managing patient records with PHI encryption,
FHIR R4 compliance, and comprehensive audit logging.
"""

import uuid
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Tuple

from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
import structlog

from app.core.security import EncryptionService, SecurityManager
from app.core.event_bus_advanced import HybridEventBus as EventBus, BaseEvent as DomainEvent
from app.core.exceptions import (
    ResourceNotFound, 
    ValidationError, 
    BusinessRuleViolation,
    UnauthorizedAccess
)
from app.core.monitoring import trace_method, metrics
from app.core.audit_logger import log_phi_access, AuditContext, AuditEventType, AuditSeverity
from app.modules.healthcare_records.service import AccessContext
from app.core.database_unified import Patient, DataClassification
from app.modules.healthcare_records.models import Immunization

logger = structlog.get_logger(__name__)


# Domain Events  
class PatientCreatedEvent(DomainEvent):
    """Event for when a patient is created."""
    event_type: str = "PatientCreated"
    patient_id: str
    tenant_id: str
    created_by: str


class PatientUpdatedEvent(DomainEvent):
    """Event for when a patient is updated."""
    event_type: str = "PatientUpdated"
    patient_id: str
    updated_by: str
    changed_fields: List[str]


class PatientDeletedEvent(DomainEvent):
    """Event for when a patient is deleted."""
    event_type: str = "PatientDeleted"
    patient_id: str
    deleted_by: str
    reason: str


class PatientService:
    """
    Enhanced service for managing patient records.
    
    Provides comprehensive CRUD operations with PHI encryption,
    FHIR R4 compliance, and detailed audit logging.
    """
    
    def __init__(
        self,
        session: AsyncSession,
        encryption: EncryptionService,
        event_bus: EventBus,
        security_manager: Optional[SecurityManager] = None
    ):
        self.session = session
        self.encryption = encryption
        self.event_bus = event_bus
        self.security_manager = security_manager or SecurityManager()
        self.logger = logger.bind(service="PatientService")
    
    @trace_method("create_patient")
    @metrics.track_operation("patient.create")
    async def create_patient(
        self,
        patient_data: Dict[str, Any],
        context: AccessContext
    ) -> Patient:
        """
        Create a new patient record with PHI encryption.
        
        Args:
            patient_data: Patient data including demographic information
            context: Access context for audit logging
            
        Returns:
            Created patient record
            
        Raises:
            ValidationError: If required data is missing or invalid
            BusinessRuleViolation: If business rules are violated
        """
        try:
            self.logger.info("Creating patient record", 
                           context_user_id=context.user_id)
            
            # Validate required fields
            self._validate_patient_data(patient_data)
            
            # Check for duplicates
            await self._check_duplicate_patient(patient_data)
            
            # Encrypt PHI fields
            encrypted_data = await self._encrypt_phi_fields(patient_data)
            
            # Create patient record
            patient = Patient(
                id=uuid.uuid4(),
                external_id=patient_data.get('external_id'),
                mrn=patient_data.get('mrn'),
                first_name_encrypted=encrypted_data.get('first_name_encrypted'),
                last_name_encrypted=encrypted_data.get('last_name_encrypted'),
                middle_name_encrypted=encrypted_data.get('middle_name_encrypted'),
                date_of_birth_encrypted=encrypted_data.get('date_of_birth_encrypted'),
                ssn_encrypted=encrypted_data.get('ssn_encrypted'),
                phone_encrypted=encrypted_data.get('phone_encrypted'),
                email_encrypted=encrypted_data.get('email_encrypted'),
                address_line1_encrypted=encrypted_data.get('address_line1_encrypted'),
                address_line2_encrypted=encrypted_data.get('address_line2_encrypted'),
                city_encrypted=encrypted_data.get('city_encrypted'),
                state_encrypted=encrypted_data.get('state_encrypted'),
                postal_code_encrypted=encrypted_data.get('postal_code_encrypted'),
                country=patient_data.get('country', 'US'),
                gender=patient_data.get('gender'),
                race=patient_data.get('race'),
                ethnicity=patient_data.get('ethnicity'),
                language_preference=patient_data.get('language_preference'),
                marital_status=patient_data.get('marital_status'),
                emergency_contact_encrypted=encrypted_data.get('emergency_contact_encrypted'),
                insurance_info_encrypted=encrypted_data.get('insurance_info_encrypted'),
                data_classification=DataClassification.PHI.value,
                consent_status={
                    "status": patient_data.get('consent_status', 'pending'),
                    "types": patient_data.get('consent_types', ['treatment'])
                },
                fhir_resource=self._build_fhir_resource(patient_data),
                created_by=uuid.UUID(context.user_id),
                tenant_id=patient_data.get('tenant_id'),
                organization_id=patient_data.get('organization_id')
            )
            
            # Add to session and flush to get ID
            self.session.add(patient)
            await self.session.flush()
            
            # Create default consents if needed
            await self._create_default_consents(patient.id, context)
            
            # Commit transaction
            await self.session.commit()
            
            # Publish domain event
            await self.event_bus.publish(
                PatientCreatedEvent(
                    aggregate_id=str(patient.id),
                    aggregate_type="Patient",
                    publisher="patient_service",
                    patient_id=str(patient.id),
                    tenant_id=str(patient.tenant_id) if patient.tenant_id else "",
                    created_by=str(context.user_id)
                )
            )
            
            # Audit PHI access
            await self._audit_patient_access(
                patient_id=str(patient.id),
                context=context,
                access_type="create",
                fields_accessed=list(encrypted_data.keys())
            )
            
            self.logger.info("Patient created successfully",
                           patient_id=str(patient.id))
            
            return patient
            
        except Exception as e:
            await self.session.rollback()
            self.logger.error("Failed to create patient",
                            error=str(e))
            raise
    
    @trace_method("get_patient")
    @metrics.track_operation("patient.read")
    async def get_patient(
        self,
        patient_id: str,
        context: AccessContext,
        include_documents: bool = False,
        include_immunizations: bool = False
    ) -> Patient:
        """
        Get patient by ID with PHI decryption.
        
        Args:
            patient_id: Patient ID
            context: Access context for audit logging
            include_documents: Whether to include clinical documents
            include_immunizations: Whether to include immunization records
            
        Returns:
            Patient record with decrypted PHI
            
        Raises:
            ResourceNotFound: If patient not found
            UnauthorizedAccess: If access denied
        """
        try:
            self.logger.info("Retrieving patient",
                           patient_id=patient_id,
                           user_id=context.user_id)
            
            # Build query
            query = select(Patient).where(
                and_(
                    Patient.id == uuid.UUID(patient_id),
                    Patient.soft_deleted_at.is_(None)
                )
            )
            
            if include_documents:
                query = query.options(selectinload(Patient.clinical_documents))
            
            if include_immunizations:
                query = query.options(selectinload(Patient.immunizations))
            
            # Execute query
            result = await self.session.execute(query)
            patient = result.scalar_one_or_none()
            
            if not patient:
                raise ResourceNotFound(f"Patient {patient_id} not found")
            
            # Check access permissions
            await self._check_access_permissions(patient, context)
            
            # Decrypt PHI fields
            await self._decrypt_patient_fields(patient)
            
            # Audit PHI access
            await self._audit_patient_access(
                patient_id=patient_id,
                context=context,
                access_type="read",
                fields_accessed=self._get_phi_fields_accessed(patient)
            )
            
            self.logger.info("Patient retrieved successfully",
                           patient_id=patient_id)
            
            return patient
            
        except Exception as e:
            self.logger.error("Failed to retrieve patient",
                            error=str(e),
                            patient_id=patient_id)
            raise
    
    @trace_method("search_patients")
    @metrics.track_operation("patient.search")
    async def search_patients(
        self,
        context: AccessContext,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
        offset: int = 0,
        search_query: Optional[str] = None
    ) -> Tuple[List[Patient], int]:
        """
        Search patients with filtering and pagination.
        
        Args:
            context: Access context
            filters: Search filters (gender, age_min, age_max, etc.)
            limit: Maximum results to return
            offset: Results to skip
            search_query: Text search query
            
        Returns:
            Tuple of (patients list, total count)
        """
        try:
            self.logger.info("Searching patients",
                           filters=filters,
                           search_query=search_query,
                           user_id=context.user_id)
            
            # Build base query
            query = select(Patient).where(
                Patient.soft_deleted_at.is_(None)
            )
            
            count_query = select(func.count(Patient.id)).where(
                Patient.soft_deleted_at.is_(None)
            )
            
            # Apply filters
            query_filters = []
            
            if filters:
                if filters.get('gender'):
                    query_filters.append(Patient.gender == filters['gender'])
                
                if filters.get('tenant_id'):
                    query_filters.append(Patient.tenant_id == uuid.UUID(filters['tenant_id']))
                
                if filters.get('organization_id'):
                    query_filters.append(Patient.organization_id == uuid.UUID(filters['organization_id']))
                
                if filters.get('mrn'):
                    query_filters.append(Patient.mrn == filters['mrn'])
            
            # Apply tenant isolation
            if hasattr(context, 'tenant_id') and context.tenant_id:
                query_filters.append(Patient.tenant_id == uuid.UUID(context.tenant_id))
            
            if query_filters:
                query = query.where(and_(*query_filters))
                count_query = count_query.where(and_(*query_filters))
            
            # Apply pagination and ordering
            query = query.order_by(desc(Patient.created_at))
            query = query.limit(limit).offset(offset)
            
            # Execute queries
            result = await self.session.execute(query)
            patients = result.scalars().all()
            
            count_result = await self.session.execute(count_query)
            total_count = count_result.scalar()
            
            # Decrypt PHI fields for accessible patients
            accessible_patients = []
            for patient in patients:
                try:
                    await self._check_access_permissions(patient, context)
                    await self._decrypt_patient_fields(patient)
                    accessible_patients.append(patient)
                    
                    # Audit access (minimal fields for list view)
                    await self._audit_patient_access(
                        patient_id=str(patient.id),
                        context=context,
                        access_type="search",
                        fields_accessed=["first_name", "last_name"]
                    )
                except UnauthorizedAccess:
                    # Skip patients user doesn't have access to
                    continue
            
            self.logger.info("Patient search completed",
                           total_found=len(accessible_patients),
                           total_count=total_count)
            
            return accessible_patients, total_count
            
        except Exception as e:
            self.logger.error("Failed to search patients",
                            error=str(e))
            raise
    
    @trace_method("update_patient")
    @metrics.track_operation("patient.update")
    async def update_patient(
        self,
        patient_id: str,
        updates: Dict[str, Any],
        context: AccessContext
    ) -> Patient:
        """
        Update patient record with validation and encryption.
        
        Args:
            patient_id: Patient ID to update
            updates: Fields to update
            context: Access context
            
        Returns:
            Updated patient record
        """
        try:
            self.logger.info("Updating patient",
                           patient_id=patient_id,
                           updates=list(updates.keys()))
            
            # Get existing patient
            patient = await self.get_patient(patient_id, context)
            
            # Validate updates
            self._validate_patient_updates(updates)
            
            # Track changed fields
            changed_fields = []
            
            # Encrypt PHI fields in updates
            encrypted_updates = await self._encrypt_phi_fields(updates)
            
            # Apply updates
            for field, value in updates.items():
                if field in self._get_phi_field_names():
                    # These are PHI fields - use encrypted version
                    encrypted_field = f"{field}_encrypted"
                    if encrypted_field in encrypted_updates:
                        setattr(patient, encrypted_field, encrypted_updates[encrypted_field])
                        changed_fields.append(field)
                elif hasattr(patient, field) and field not in ['id', 'created_at', 'created_by']:
                    setattr(patient, field, value)
                    changed_fields.append(field)
            
            # Update consent status if provided
            if 'consent_status' in updates or 'consent_types' in updates:
                current_consent = patient.consent_status or {}
                if 'consent_status' in updates:
                    current_consent["status"] = updates['consent_status']
                if 'consent_types' in updates:
                    current_consent["types"] = updates['consent_types']
                patient.consent_status = current_consent
                changed_fields.append('consent_status')
            
            # Update metadata
            patient.updated_at = datetime.utcnow()
            patient.updated_by = uuid.UUID(context.user_id)
            
            # Update FHIR resource
            patient.fhir_resource = self._build_fhir_resource(updates, patient)
            
            # Commit changes
            await self.session.commit()
            
            # Publish update event
            await self.event_bus.publish(
                PatientUpdatedEvent(
                    aggregate_id=str(patient.id),
                    aggregate_type="Patient",
                    publisher="patient_service",
                    patient_id=patient_id,
                    updated_by=str(context.user_id),
                    changed_fields=changed_fields
                )
            )
            
            # Audit update
            await self._audit_patient_access(
                patient_id=patient_id,
                context=context,
                access_type="update",
                fields_accessed=changed_fields
            )
            
            self.logger.info("Patient updated successfully",
                           patient_id=patient_id,
                           changed_fields=changed_fields)
            
            return patient
            
        except Exception as e:
            await self.session.rollback()
            self.logger.error("Failed to update patient",
                            error=str(e),
                            patient_id=patient_id)
            raise
    
    @trace_method("soft_delete_patient")
    @metrics.track_operation("patient.delete")
    async def soft_delete_patient(
        self,
        patient_id: str,
        context: AccessContext,
        reason: str
    ) -> None:
        """
        Soft delete patient record for GDPR compliance.
        
        Args:
            patient_id: Patient ID to delete
            context: Access context
            reason: Reason for deletion
        """
        try:
            self.logger.info("Soft deleting patient",
                           patient_id=patient_id,
                           reason=reason)
            
            # Get patient
            patient = await self.get_patient(patient_id, context)
            
            # Perform soft delete
            patient.soft_deleted_at = datetime.utcnow()
            patient.deletion_reason = reason
            patient.deleted_by = uuid.UUID(context.user_id)
            
            # Commit changes
            await self.session.commit()
            
            # Publish deletion event
            await self.event_bus.publish(
                PatientDeletedEvent(
                    aggregate_id=str(patient.id),
                    aggregate_type="Patient",
                    publisher="patient_service",
                    patient_id=patient_id,
                    deleted_by=str(context.user_id),
                    reason=reason
                )
            )
            
            # Audit deletion
            await self._audit_patient_access(
                patient_id=patient_id,
                context=context,
                access_type="delete",
                fields_accessed=["soft_deleted_at", "deletion_reason"]
            )
            
            self.logger.info("Patient soft deleted successfully",
                           patient_id=patient_id)
            
        except Exception as e:
            await self.session.rollback()
            self.logger.error("Failed to soft delete patient",
                            error=str(e),
                            patient_id=patient_id)
            raise
    
    # Private helper methods
    
    def _validate_patient_data(self, data: Dict[str, Any]) -> None:
        """Validate patient data."""
        required_fields = ['first_name', 'last_name']
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"Required field '{field}' is missing or empty")
        
        # Validate email format if provided
        if data.get('email'):
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, data['email']):
                raise ValidationError("Invalid email format")
        
        # Validate date of birth if provided
        if data.get('date_of_birth'):
            if isinstance(data['date_of_birth'], str):
                try:
                    data['date_of_birth'] = datetime.fromisoformat(data['date_of_birth']).date()
                except ValueError:
                    raise ValidationError("Invalid date_of_birth format")
            
            # Check reasonable age limits
            if data['date_of_birth'] > date.today():
                raise ValidationError("Date of birth cannot be in the future")
            
            age = (date.today() - data['date_of_birth']).days // 365
            if age > 150:
                raise ValidationError("Age exceeds reasonable limits")
    
    def _validate_patient_updates(self, updates: Dict[str, Any]) -> None:
        """Validate patient update data."""
        # Prevent changing immutable fields
        immutable_fields = ['id', 'created_at', 'created_by']
        for field in immutable_fields:
            if field in updates:
                raise ValidationError(f"Field '{field}' cannot be updated")
    
    async def _check_duplicate_patient(self, data: Dict[str, Any]) -> None:
        """Check for duplicate patient records."""
        if data.get('mrn'):
            # Check for duplicate MRN
            query = select(Patient).where(
                and_(
                    Patient.mrn == data['mrn'],
                    Patient.soft_deleted_at.is_(None)
                )
            )
            result = await self.session.execute(query)
            if result.scalar_one_or_none():
                raise BusinessRuleViolation(f"Patient with MRN {data['mrn']} already exists")
        
        if data.get('ssn'):
            # Check for duplicate SSN (would need encrypted comparison in real implementation)
            self.logger.warning("SSN duplicate check not fully implemented")
    
    def _get_phi_field_names(self) -> List[str]:
        """Get list of PHI field names."""
        return [
            'first_name', 'last_name', 'middle_name', 'date_of_birth',
            'ssn', 'phone', 'email', 'address_line1', 'address_line2',
            'city', 'state', 'postal_code', 'emergency_contact', 'insurance_info'
        ]
    
    async def _encrypt_phi_fields(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Encrypt PHI fields in patient data."""
        encrypted = {}
        phi_fields = self._get_phi_field_names()
        
        for field in phi_fields:
            if field in data and data[field] is not None:
                if field == 'date_of_birth' and isinstance(data[field], date):
                    # Convert date to string for encryption
                    value = data[field].isoformat()
                else:
                    value = str(data[field])
                
                encrypted[f"{field}_encrypted"] = await self.encryption.encrypt(
                    value,
                    context={'field_type': 'phi', 'field_name': field}
                )
        
        return encrypted
    
    async def _decrypt_patient_fields(self, patient: Patient) -> None:
        """Decrypt PHI fields in patient record."""
        phi_fields = self._get_phi_field_names()
        
        for field in phi_fields:
            encrypted_field = f"{field}_encrypted"
            if hasattr(patient, encrypted_field):
                encrypted_value = getattr(patient, encrypted_field)
                if encrypted_value:
                    try:
                        decrypted_value = await self.encryption.decrypt(encrypted_value)
                        
                        # Handle date field conversion
                        if field == 'date_of_birth':
                            try:
                                decrypted_value = datetime.fromisoformat(decrypted_value).date()
                            except ValueError:
                                decrypted_value = None
                        
                        setattr(patient, field, decrypted_value)
                    except Exception as e:
                        self.logger.warning("Failed to decrypt field",
                                          field=field,
                                          error=str(e))
                        setattr(patient, field, "[ENCRYPTED]" if field != 'date_of_birth' else None)
    
    async def _check_access_permissions(
        self, 
        patient: Patient, 
        context: AccessContext
    ) -> None:
        """Check if user has access to patient record."""
        # Implement role-based access control
        allowed_roles = {'admin', 'physician', 'nurse', 'pharmacist', 'operator'}
        if context.role not in allowed_roles:
            raise UnauthorizedAccess(f"Role '{context.role}' not authorized for patient access")
    
    def _get_phi_fields_accessed(self, patient: Patient) -> List[str]:
        """Get list of PHI fields accessed."""
        phi_fields = []
        phi_field_names = self._get_phi_field_names()
        
        for field in phi_field_names:
            if hasattr(patient, field) and getattr(patient, field) is not None:
                phi_fields.append(field)
        
        return phi_fields
    
    async def _audit_patient_access(
        self,
        patient_id: str,
        context: AccessContext,
        access_type: str,
        fields_accessed: List[str]
    ) -> None:
        """Audit patient access for HIPAA compliance."""
        audit_context = AuditContext(
            user_id=context.user_id,
            ip_address=context.ip_address,
            session_id=context.session_id
        )
        
        await log_phi_access(
            user_id=context.user_id,
            patient_id=patient_id,
            fields_accessed=fields_accessed,
            purpose=context.purpose,
            context=audit_context,
            db=self.session,
            resource_type="Patient",
            resource_id=patient_id,
            access_type=access_type
        )
    
    def _build_fhir_resource(
        self, 
        data: Dict[str, Any], 
        existing: Optional[Patient] = None
    ) -> Dict[str, Any]:
        """Build FHIR R4 Patient resource."""
        resource = {
            "resourceType": "Patient",
            "id": str(existing.id) if existing else str(uuid.uuid4()),
            "meta": {
                "versionId": "1",
                "lastUpdated": datetime.utcnow().isoformat()
            },
            "active": data.get('active', True),
            "name": [{
                "use": "official",
                "family": data.get('last_name', ''),
                "given": [data.get('first_name', '')]
            }],
            "gender": data.get('gender'),
            "birthDate": data.get('date_of_birth').isoformat() if data.get('date_of_birth') else None
        }
        
        # Add identifiers
        if data.get('mrn'):
            resource["identifier"] = [{
                "use": "official",
                "type": {
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                        "code": "MR"
                    }]
                },
                "system": "http://hospital.smarthit.org",
                "value": data['mrn']
            }]
        
        # Add contact information (encrypted in storage)
        if data.get('phone') or data.get('email'):
            resource["telecom"] = []
            if data.get('phone'):
                resource["telecom"].append({
                    "system": "phone",
                    "value": "[ENCRYPTED]",
                    "use": "mobile"
                })
            if data.get('email'):
                resource["telecom"].append({
                    "system": "email",
                    "value": "[ENCRYPTED]"
                })
        
        # Add address (encrypted in storage)
        if any(data.get(field) for field in ['address_line1', 'city', 'state', 'postal_code']):
            resource["address"] = [{
                "use": "home",
                "type": "physical",
                "line": ["[ENCRYPTED]"],
                "city": "[ENCRYPTED]",
                "state": "[ENCRYPTED]",
                "postalCode": "[ENCRYPTED]",
                "country": data.get('country', 'US')
            }]
        
        return resource
    
    async def _create_default_consents(
        self,
        patient_id: uuid.UUID,
        context: AccessContext
    ) -> None:
        """Create default consent records for a new patient."""
        # Implementation would create default consent records
        # This is a placeholder for now
        self.logger.info("Creating default consents for patient",
                        patient_id=str(patient_id))
        pass