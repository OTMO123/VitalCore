"""
Immunization Service Layer

Business logic for managing immunization records with FHIR R4 compliance,
PHI encryption, and comprehensive audit logging.
"""

import uuid
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum

from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
import structlog

from app.core.security import EncryptionService, SecurityManager
from app.core.events.event_bus import get_event_bus, HealthcareEventBus
from app.core.events.definitions import ImmunizationRecorded, ImmunizationUpdated, ImmunizationDeleted
from app.core.exceptions import (
    ResourceNotFound, 
    ValidationError, 
    BusinessRuleViolation,
    UnauthorizedAccess
)
from app.core.monitoring import trace_method, metrics
from app.core.audit_logger import log_phi_access, AuditContext, AuditEventType, AuditSeverity
from app.modules.healthcare_records.models import (
    Immunization, 
    ImmunizationReaction, 
    VaccineInventory,
    ImmunizationSchedule,
    ImmunizationStatus,
    VaccineCode
)
from app.modules.healthcare_records.service import AccessContext
from app.core.database_unified import Patient

logger = structlog.get_logger(__name__)


# Using centralized event definitions from app.core.events


class ImmunizationService:
    """
    Service for managing immunization records.
    
    Handles CRUD operations for immunizations with proper PHI encryption,
    FHIR R4 compliance, and comprehensive audit logging.
    """
    
    def __init__(
        self,
        session: AsyncSession,
        encryption: EncryptionService,
        event_bus: Optional[HealthcareEventBus] = None,
        security_manager: Optional[SecurityManager] = None
    ):
        self.session = session
        self.encryption = encryption
        self.event_bus = event_bus or get_event_bus()
        self.security_manager = security_manager or SecurityManager()
        self.logger = logger.bind(service="ImmunizationService")
    
    @trace_method("create_immunization")
    @metrics.track_operation("immunization.create")
    async def create_immunization(
        self,
        immunization_data: Dict[str, Any],
        context: AccessContext
    ) -> Immunization:
        """
        Create a new immunization record with PHI encryption.
        
        Args:
            immunization_data: Immunization data including patient_id, vaccine details
            context: Access context for audit logging
            
        Returns:
            Created immunization record
            
        Raises:
            ValidationError: If required data is missing or invalid
            ResourceNotFound: If patient does not exist
            BusinessRuleViolation: If business rules are violated
        """
        try:
            self.logger.info("Creating immunization record", 
                           patient_id=immunization_data.get('patient_id'),
                           vaccine_code=immunization_data.get('vaccine_code'))
            
            # Validate required fields
            self._validate_immunization_data(immunization_data)
            
            # Verify patient exists
            patient_id = immunization_data['patient_id']
            await self._verify_patient_exists(patient_id)
            
            # Check for duplicate immunizations
            await self._check_duplicate_immunization(immunization_data)
            
            # Encrypt PHI fields
            encrypted_data = await self._encrypt_phi_fields(immunization_data)
            
            # Create immunization record
            immunization = Immunization(
                id=uuid.uuid4(),
                patient_id=uuid.UUID(patient_id),
                fhir_id=f"Immunization/{uuid.uuid4()}",
                status=immunization_data.get('status', ImmunizationStatus.COMPLETED.value),
                vaccine_code=immunization_data['vaccine_code'],
                vaccine_display=immunization_data.get('vaccine_display'),
                vaccine_system=immunization_data.get('vaccine_system', 'http://hl7.org/fhir/sid/cvx'),
                occurrence_datetime=immunization_data['occurrence_datetime'],
                recorded_date=datetime.utcnow(),
                location_encrypted=encrypted_data.get('location_encrypted'),
                primary_source=immunization_data.get('primary_source', True),
                lot_number_encrypted=encrypted_data.get('lot_number_encrypted'),
                expiration_date=immunization_data.get('expiration_date'),
                manufacturer_encrypted=encrypted_data.get('manufacturer_encrypted'),
                route_code=immunization_data.get('route_code'),
                route_display=immunization_data.get('route_display'),
                site_code=immunization_data.get('site_code'),
                site_display=immunization_data.get('site_display'),
                dose_quantity=immunization_data.get('dose_quantity'),
                dose_unit=immunization_data.get('dose_unit'),
                performer_type=immunization_data.get('performer_type'),
                performer_name_encrypted=encrypted_data.get('performer_name_encrypted'),
                performer_organization_encrypted=encrypted_data.get('performer_organization_encrypted'),
                indication_codes=immunization_data.get('indication_codes', []),
                contraindication_codes=immunization_data.get('contraindication_codes', []),
                reactions=immunization_data.get('reactions', []),
                fhir_resource=self._build_fhir_resource(immunization_data),
                created_by=uuid.UUID(context.user_id),
                tenant_id=immunization_data.get('tenant_id'),
                organization_id=immunization_data.get('organization_id')
            )
            
            # Add to session and flush to get ID
            self.session.add(immunization)
            await self.session.flush()
            
            # Update vaccine inventory if lot number provided
            if immunization_data.get('lot_number'):
                await self._update_vaccine_inventory(
                    immunization_data['vaccine_code'],
                    immunization_data['lot_number'],
                    -1,  # Decrease by 1
                    "administered"
                )
            
            # Commit transaction
            await self.session.commit()
            
            # Publish domain event using new event system
            await self.event_bus.publish_immunization_recorded(
                immunization_id=str(immunization.id),
                patient_id=str(patient_id),
                vaccine_code=immunization_data['vaccine_code'],
                vaccine_name=immunization_data.get('vaccine_display', immunization_data['vaccine_code']),
                administration_date=immunization_data['occurrence_datetime'],
                lot_number=immunization_data.get('lot_number'),
                manufacturer=immunization_data.get('manufacturer'),
                route=immunization_data.get('route_display'),
                site=immunization_data.get('site_display'),
                administering_provider_id=str(context.user_id),
                source_system="manual",
                fhir_compliant=True
            )
            
            # Audit PHI access
            await self._audit_immunization_access(
                immunization_id=str(immunization.id),
                patient_id=str(patient_id),
                context=context,
                access_type="create",
                fields_accessed=list(encrypted_data.keys())
            )
            
            self.logger.info("Immunization created successfully",
                           immunization_id=str(immunization.id),
                           patient_id=str(patient_id),
                           vaccine_code=immunization_data['vaccine_code'])
            
            return immunization
            
        except Exception as e:
            await self.session.rollback()
            self.logger.error("Failed to create immunization",
                            error=str(e),
                            patient_id=immunization_data.get('patient_id'))
            raise
    
    @trace_method("get_immunization")
    @metrics.track_operation("immunization.read")
    async def get_immunization(
        self,
        immunization_id: str,
        context: AccessContext,
        include_reactions: bool = False
    ) -> Immunization:
        """
        Get immunization by ID with PHI decryption.
        
        Args:
            immunization_id: Immunization ID
            context: Access context for audit logging
            include_reactions: Whether to include adverse reactions
            
        Returns:
            Immunization record with decrypted PHI
            
        Raises:
            ResourceNotFound: If immunization not found
            UnauthorizedAccess: If access denied
        """
        try:
            self.logger.info("Retrieving immunization",
                           immunization_id=immunization_id,
                           user_id=context.user_id)
            
            # Build query
            query = select(Immunization).where(
                and_(
                    Immunization.id == uuid.UUID(immunization_id),
                    Immunization.soft_deleted_at.is_(None)
                )
            ).options(selectinload(Immunization.patient))
            
            if include_reactions:
                query = query.options(selectinload(Immunization.adverse_reactions))
            
            # Execute query
            result = await self.session.execute(query)
            immunization = result.scalar_one_or_none()
            
            if not immunization:
                raise ResourceNotFound(f"Immunization {immunization_id} not found")
            
            # Check access permissions
            await self._check_access_permissions(immunization, context)
            
            # Decrypt PHI fields
            await self._decrypt_immunization_fields(immunization)
            
            # Audit PHI access
            await self._audit_immunization_access(
                immunization_id=immunization_id,
                patient_id=str(immunization.patient_id),
                context=context,
                access_type="read",
                fields_accessed=self._get_phi_fields_accessed(immunization)
            )
            
            self.logger.info("Immunization retrieved successfully",
                           immunization_id=immunization_id,
                           patient_id=str(immunization.patient_id))
            
            return immunization
            
        except Exception as e:
            self.logger.error("Failed to retrieve immunization",
                            error=str(e),
                            immunization_id=immunization_id)
            raise
    
    @trace_method("list_immunizations")
    @metrics.track_operation("immunization.list")
    async def list_immunizations(
        self,
        context: AccessContext,
        patient_id: Optional[str] = None,
        vaccine_codes: Optional[List[str]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        status_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Immunization], int]:
        """
        List immunizations with filtering and pagination.
        
        Args:
            context: Access context
            patient_id: Filter by patient ID
            vaccine_codes: Filter by vaccine codes
            date_from: Filter by date range start
            date_to: Filter by date range end
            status_filter: Filter by status
            limit: Maximum results to return
            offset: Results to skip
            
        Returns:
            Tuple of (immunizations list, total count)
        """
        try:
            self.logger.info("Listing immunizations",
                           patient_id=patient_id,
                           vaccine_codes=vaccine_codes,
                           user_id=context.user_id)
            
            # Build base query
            query = select(Immunization).where(
                Immunization.soft_deleted_at.is_(None)
            ).options(selectinload(Immunization.patient))
            
            count_query = select(func.count(Immunization.id)).where(
                Immunization.soft_deleted_at.is_(None)
            )
            
            # Apply filters
            filters = []
            
            if patient_id:
                patient_filter = Immunization.patient_id == uuid.UUID(patient_id)
                filters.append(patient_filter)
            
            if vaccine_codes:
                filters.append(Immunization.vaccine_code.in_(vaccine_codes))
            
            if date_from:
                filters.append(Immunization.occurrence_datetime >= date_from)
            
            if date_to:
                filters.append(Immunization.occurrence_datetime <= date_to)
            
            if status_filter:
                filters.append(Immunization.status == status_filter)
            
            # Apply tenant isolation
            if hasattr(context, 'tenant_id') and context.tenant_id:
                filters.append(Immunization.tenant_id == uuid.UUID(context.tenant_id))
            
            if filters:
                query = query.where(and_(*filters))
                count_query = count_query.where(and_(*filters))
            
            # Apply pagination and ordering
            query = query.order_by(desc(Immunization.occurrence_datetime))
            query = query.limit(limit).offset(offset)
            
            # Execute queries
            result = await self.session.execute(query)
            immunizations = result.scalars().all()
            
            count_result = await self.session.execute(count_query)
            total_count = count_result.scalar()
            
            # Decrypt PHI fields for accessible immunizations
            accessible_immunizations = []
            for immunization in immunizations:
                try:
                    await self._check_access_permissions(immunization, context)
                    await self._decrypt_immunization_fields(immunization)
                    accessible_immunizations.append(immunization)
                    
                    # Audit access
                    await self._audit_immunization_access(
                        immunization_id=str(immunization.id),
                        patient_id=str(immunization.patient_id),
                        context=context,
                        access_type="list",
                        fields_accessed=["vaccine_code", "occurrence_datetime"]
                    )
                except UnauthorizedAccess:
                    # Skip immunizations user doesn't have access to
                    continue
            
            self.logger.info("Immunizations listed successfully",
                           total_found=len(accessible_immunizations),
                           total_count=total_count,
                           user_id=context.user_id)
            
            return accessible_immunizations, total_count
            
        except Exception as e:
            self.logger.error("Failed to list immunizations",
                            error=str(e),
                            patient_id=patient_id)
            raise
    
    @trace_method("update_immunization")
    @metrics.track_operation("immunization.update")
    async def update_immunization(
        self,
        immunization_id: str,
        updates: Dict[str, Any],
        context: AccessContext
    ) -> Immunization:
        """
        Update immunization record with validation and encryption.
        
        Args:
            immunization_id: Immunization ID to update
            updates: Fields to update
            context: Access context
            
        Returns:
            Updated immunization record
        """
        try:
            self.logger.info("Updating immunization",
                           immunization_id=immunization_id,
                           updates=list(updates.keys()))
            
            # Get existing immunization
            immunization = await self.get_immunization(immunization_id, context)
            
            # Validate updates
            self._validate_immunization_updates(updates)
            
            # Encrypt PHI fields in updates
            encrypted_updates = await self._encrypt_phi_fields(updates)
            
            # Apply updates
            for field, value in updates.items():
                if field in ['location', 'lot_number', 'manufacturer', 'performer_name', 'performer_organization']:
                    # These are PHI fields - use encrypted version
                    encrypted_field = f"{field}_encrypted"
                    setattr(immunization, encrypted_field, encrypted_updates.get(encrypted_field))
                elif hasattr(immunization, field):
                    setattr(immunization, field, value)
            
            # Update metadata
            immunization.updated_at = datetime.utcnow()
            immunization.updated_by = uuid.UUID(context.user_id)
            
            # Update FHIR resource
            immunization.fhir_resource = self._build_fhir_resource(updates, immunization)
            
            # Commit changes
            await self.session.commit()
            
            # Audit update
            await self._audit_immunization_access(
                immunization_id=immunization_id,
                patient_id=str(immunization.patient_id),
                context=context,
                access_type="update",
                fields_accessed=list(updates.keys())
            )
            
            self.logger.info("Immunization updated successfully",
                           immunization_id=immunization_id)
            
            return immunization
            
        except Exception as e:
            await self.session.rollback()
            self.logger.error("Failed to update immunization",
                            error=str(e),
                            immunization_id=immunization_id)
            raise
    
    @trace_method("delete_immunization")
    @metrics.track_operation("immunization.delete")
    async def delete_immunization(
        self,
        immunization_id: str,
        context: AccessContext,
        reason: str
    ) -> None:
        """
        Soft delete immunization record.
        
        Args:
            immunization_id: Immunization ID to delete
            context: Access context
            reason: Reason for deletion
        """
        try:
            self.logger.info("Deleting immunization",
                           immunization_id=immunization_id,
                           reason=reason)
            
            # Get immunization
            immunization = await self.get_immunization(immunization_id, context)
            
            # Perform soft delete
            immunization.soft_deleted_at = datetime.utcnow()
            immunization.deletion_reason = reason
            immunization.deleted_by = uuid.UUID(context.user_id)
            immunization.status = ImmunizationStatus.ENTERED_IN_ERROR.value
            
            # Commit changes
            await self.session.commit()
            
            # Publish immunization deleted event
            await self.event_bus.publish_event(
                event_type="immunization.deleted",
                aggregate_id=immunization_id,
                publisher="healthcare_records",
                data={
                    "immunization_id": immunization_id,
                    "patient_id": str(immunization.patient_id),
                    "deletion_reason": reason,
                    "deleted_by_user_id": str(context.user_id),
                    "soft_delete": True,
                    "audit_preserved": True
                }
            )
            
            # Audit deletion
            await self._audit_immunization_access(
                immunization_id=immunization_id,
                patient_id=str(immunization.patient_id),
                context=context,
                access_type="delete",
                fields_accessed=["status", "soft_deleted_at"]
            )
            
            self.logger.info("Immunization deleted successfully",
                           immunization_id=immunization_id)
            
        except Exception as e:
            await self.session.rollback()
            self.logger.error("Failed to delete immunization",
                            error=str(e),
                            immunization_id=immunization_id)
            raise
    
    @trace_method("report_adverse_reaction")
    async def report_adverse_reaction(
        self,
        immunization_id: str,
        reaction_data: Dict[str, Any],
        context: AccessContext
    ) -> ImmunizationReaction:
        """Report an adverse reaction to an immunization."""
        try:
            # Get immunization
            immunization = await self.get_immunization(immunization_id, context)
            
            # Encrypt PHI fields
            encrypted_data = await self._encrypt_reaction_phi_fields(reaction_data)
            
            # Create reaction record
            reaction = ImmunizationReaction(
                id=uuid.uuid4(),
                immunization_id=uuid.UUID(immunization_id),
                reaction_date=reaction_data.get('reaction_date', datetime.utcnow()),
                onset_period=reaction_data.get('onset_period'),
                manifestation_code=reaction_data.get('manifestation_code'),
                manifestation_display=reaction_data.get('manifestation_display'),
                severity=reaction_data.get('severity'),
                outcome_code=reaction_data.get('outcome_code'),
                outcome_display=reaction_data.get('outcome_display'),
                description_encrypted=encrypted_data.get('description_encrypted'),
                treatment_encrypted=encrypted_data.get('treatment_encrypted'),
                reported_by_encrypted=encrypted_data.get('reported_by_encrypted'),
                report_date=datetime.utcnow(),
                created_by=uuid.UUID(context.user_id)
            )
            
            self.session.add(reaction)
            await self.session.commit()
            
            # Log adverse reaction for monitoring
            await self.event_bus.publish_event(
                event_type="security.violation_detected",
                aggregate_id=str(reaction.id),
                publisher="immunization_service",
                data={
                    "violation_type": "adverse_reaction_reported",
                    "severity": "high" if reaction_data.get('severity') == 'severe' else "medium",
                    "violation_description": f"Adverse reaction reported for immunization {immunization_id}",
                    "detection_method": "manual_report",
                    "resource_type": "immunization",
                    "resource_id": immunization_id,
                    "user_id": str(context.user_id),
                    "immediate_action_taken": "reaction_logged",
                    "requires_investigation": reaction_data.get('severity') == 'severe'
                }
            )
            
            self.logger.info("Adverse reaction reported",
                           immunization_id=immunization_id,
                           reaction_id=str(reaction.id),
                           severity=reaction_data.get('severity'))
            
            return reaction
            
        except Exception as e:
            await self.session.rollback()
            self.logger.error("Failed to report adverse reaction",
                            error=str(e),
                            immunization_id=immunization_id)
            raise
    
    # Private helper methods
    
    def _validate_immunization_data(self, data: Dict[str, Any]) -> None:
        """Validate immunization data."""
        required_fields = ['patient_id', 'vaccine_code', 'occurrence_datetime']
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"Required field '{field}' is missing or empty")
        
        # Validate vaccine code
        if data['vaccine_code'] not in [code.value for code in VaccineCode]:
            # Allow other vaccine codes but log warning
            self.logger.warning("Unknown vaccine code", vaccine_code=data['vaccine_code'])
        
        # Validate date
        if isinstance(data['occurrence_datetime'], str):
            try:
                data['occurrence_datetime'] = datetime.fromisoformat(data['occurrence_datetime'])
            except ValueError:
                raise ValidationError("Invalid occurrence_datetime format")
    
    def _validate_immunization_updates(self, updates: Dict[str, Any]) -> None:
        """Validate immunization update data."""
        # Prevent changing immutable fields
        immutable_fields = ['id', 'patient_id', 'created_at', 'created_by']
        for field in immutable_fields:
            if field in updates:
                raise ValidationError(f"Field '{field}' cannot be updated")
    
    async def _verify_patient_exists(self, patient_id: str) -> None:
        """Verify that the patient exists."""
        query = select(Patient).where(
            and_(
                Patient.id == uuid.UUID(patient_id),
                Patient.soft_deleted_at.is_(None)
            )
        )
        result = await self.session.execute(query)
        if not result.scalar_one_or_none():
            raise ResourceNotFound(f"Patient {patient_id} not found")
    
    async def _check_duplicate_immunization(self, data: Dict[str, Any]) -> None:
        """Check for duplicate immunization records."""
        query = select(Immunization).where(
            and_(
                Immunization.patient_id == uuid.UUID(data['patient_id']),
                Immunization.vaccine_code == data['vaccine_code'],
                Immunization.occurrence_datetime == data['occurrence_datetime'],
                Immunization.soft_deleted_at.is_(None)
            )
        )
        result = await self.session.execute(query)
        if result.scalar_one_or_none():
            raise BusinessRuleViolation(
                f"Duplicate immunization record for vaccine {data['vaccine_code']} "
                f"on {data['occurrence_datetime']}"
            )
    
    async def _encrypt_phi_fields(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Encrypt PHI fields in immunization data."""
        encrypted = {}
        phi_fields = [
            'location', 'lot_number', 'manufacturer', 
            'performer_name', 'performer_organization'
        ]
        
        for field in phi_fields:
            if field in data and data[field]:
                encrypted[f"{field}_encrypted"] = await self.encryption.encrypt(
                    str(data[field]),
                    context={'field_type': 'phi', 'field_name': field}
                )
        
        return encrypted
    
    async def _encrypt_reaction_phi_fields(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Encrypt PHI fields in reaction data."""
        encrypted = {}
        phi_fields = ['description', 'treatment', 'reported_by']
        
        for field in phi_fields:
            if field in data and data[field]:
                encrypted[f"{field}_encrypted"] = await self.encryption.encrypt(
                    str(data[field]),
                    context={'field_type': 'phi', 'field_name': field}
                )
        
        return encrypted
    
    async def _decrypt_immunization_fields(self, immunization: Immunization) -> None:
        """Decrypt PHI fields in immunization record."""
        phi_fields = [
            'location', 'lot_number', 'manufacturer',
            'performer_name', 'performer_organization'
        ]
        
        for field in phi_fields:
            encrypted_field = f"{field}_encrypted"
            if hasattr(immunization, encrypted_field):
                encrypted_value = getattr(immunization, encrypted_field)
                if encrypted_value:
                    try:
                        decrypted_value = await self.encryption.decrypt(encrypted_value)
                        setattr(immunization, field, decrypted_value)
                    except Exception as e:
                        self.logger.warning("Failed to decrypt field",
                                          field=field,
                                          error=str(e))
                        setattr(immunization, field, "[ENCRYPTED]")
    
    async def _check_access_permissions(
        self, 
        immunization: Immunization, 
        context: AccessContext
    ) -> None:
        """Check if user has access to immunization record."""
        # Implement role-based access control
        allowed_roles = {'admin', 'physician', 'nurse', 'pharmacist'}
        if context.role not in allowed_roles:
            raise UnauthorizedAccess(f"Role '{context.role}' not authorized for immunization access")
    
    def _get_phi_fields_accessed(self, immunization: Immunization) -> List[str]:
        """Get list of PHI fields accessed."""
        phi_fields = []
        if hasattr(immunization, 'location') and immunization.location:
            phi_fields.append('location')
        if hasattr(immunization, 'lot_number') and immunization.lot_number:
            phi_fields.append('lot_number')
        if hasattr(immunization, 'manufacturer') and immunization.manufacturer:
            phi_fields.append('manufacturer')
        if hasattr(immunization, 'performer_name') and immunization.performer_name:
            phi_fields.append('performer_name')
        if hasattr(immunization, 'performer_organization') and immunization.performer_organization:
            phi_fields.append('performer_organization')
        return phi_fields
    
    async def _audit_immunization_access(
        self,
        immunization_id: str,
        patient_id: str,
        context: AccessContext,
        access_type: str,
        fields_accessed: List[str]
    ) -> None:
        """Audit immunization access for HIPAA compliance."""
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
            resource_type="Immunization",
            resource_id=immunization_id,
            access_type=access_type
        )
    
    def _build_fhir_resource(
        self, 
        data: Dict[str, Any], 
        existing: Optional[Immunization] = None
    ) -> Dict[str, Any]:
        """Build FHIR R4 Immunization resource."""
        resource = {
            "resourceType": "Immunization",
            "id": str(existing.id) if existing else str(uuid.uuid4()),
            "meta": {
                "versionId": "1",
                "lastUpdated": datetime.utcnow().isoformat()
            },
            "status": data.get('status', ImmunizationStatus.COMPLETED.value),
            "vaccineCode": {
                "coding": [{
                    "system": data.get('vaccine_system', 'http://hl7.org/fhir/sid/cvx'),
                    "code": data['vaccine_code'],
                    "display": data.get('vaccine_display')
                }]
            },
            "patient": {
                "reference": f"Patient/{data['patient_id']}"
            },
            "occurrenceDateTime": data['occurrence_datetime'].isoformat() if isinstance(data['occurrence_datetime'], datetime) else data['occurrence_datetime'],
            "recorded": datetime.utcnow().isoformat(),
            "primarySource": data.get('primary_source', True)
        }
        
        # Add optional fields
        if data.get('route_code'):
            resource["route"] = {
                "coding": [{
                    "code": data['route_code'],
                    "display": data.get('route_display')
                }]
            }
        
        if data.get('site_code'):
            resource["site"] = {
                "coding": [{
                    "code": data['site_code'],
                    "display": data.get('site_display')
                }]
            }
        
        return resource
    
    async def _update_vaccine_inventory(
        self,
        vaccine_code: str,
        lot_number: str,
        quantity_change: int,
        reason: str
    ) -> None:
        """Update vaccine inventory levels."""
        query = select(VaccineInventory).where(
            and_(
                VaccineInventory.vaccine_code == vaccine_code,
                VaccineInventory.lot_number == lot_number
            )
        )
        result = await self.session.execute(query)
        inventory = result.scalar_one_or_none()
        
        if inventory:
            inventory.quantity_available += quantity_change
            if reason == "administered":
                inventory.quantity_administered += abs(quantity_change)
            
            # Log vaccine inventory update
            self.logger.info(
                "Vaccine inventory updated",
                vaccine_code=vaccine_code,
                lot_number=lot_number,
                quantity_change=quantity_change,
                reason=reason,
                new_quantity=inventory.quantity_available
            )