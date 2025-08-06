"""
Healthcare Records Database Models

Database models for the Healthcare Records module implementing FHIR R4 compliance
with PHI encryption and audit logging.
"""

import uuid
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from enum import Enum

from sqlalchemy import Column, String, DateTime, Boolean, Text, JSON, ForeignKey, Index, Integer, Date
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database_unified import ArrayType, UUIDType
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

from app.core.database_unified import Base, DataClassification, ConsentStatus, Patient


class ImmunizationStatus(str, Enum):
    """FHIR R4 Immunization status values."""
    COMPLETED = "completed"
    ENTERED_IN_ERROR = "entered-in-error"
    NOT_DONE = "not-done"


class VaccineCode(str, Enum):
    """Common vaccine codes from CVX."""
    COVID19_PFIZER = "208"
    COVID19_MODERNA = "207" 
    COVID19_JANSSEN = "212"
    INFLUENZA = "88"
    HEPATITIS_B = "08"
    MMR = "03"
    TDAP = "115"
    HPV = "62"


class ReactionSeverity(str, Enum):
    """Reaction severity levels."""
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"


class Immunization(Base):
    """
    Immunization record model implementing FHIR R4 Immunization resource.
    
    All PHI fields are encrypted at rest and require proper access controls.
    Implements comprehensive audit logging for HIPAA compliance.
    """
    __table_args__ = {'extend_existing': True}
    __tablename__ = "immunizations"
    
    # Primary identification
    id = Column(UUIDType(), primary_key=True, default=uuid.uuid4)
    external_id = Column(String(255), index=True, comment="External system identifier")
    
    # FHIR Resource identification
    fhir_id = Column(String(255), unique=True, index=True, comment="FHIR resource ID")
    version = Column(String(50), default="1", comment="FHIR resource version")
    
    # Patient relationship (required) - Enterprise Healthcare FHIR R4 Compliant
    patient_id = Column(UUIDType(), ForeignKey("patients.id"), nullable=False, index=True)
    # Enterprise architecture: Patient relationship is managed by core database_unified
    patient = relationship("Patient", back_populates="immunizations")
    
    # Core immunization data
    status = Column(String(50), nullable=False, default=ImmunizationStatus.COMPLETED.value, comment="FHIR status")
    vaccine_code = Column(String(50), nullable=False, comment="CVX vaccine code")
    vaccine_display = Column(String(255), comment="Human readable vaccine name")
    vaccine_system = Column(String(255), default="http://hl7.org/fhir/sid/cvx", comment="Coding system")
    
    # Administration details
    occurrence_datetime = Column(DateTime, nullable=False, comment="When vaccination was performed")
    recorded_date = Column(DateTime, default=func.now(), comment="When record was created")
    
    # Location and provider (encrypted PHI)
    location_encrypted = Column(Text, comment="Encrypted location/clinic name")
    primary_source = Column(Boolean, default=True, comment="Information from primary source")
    
    # Vaccine details
    lot_number_encrypted = Column(Text, comment="Encrypted vaccine lot number")
    expiration_date = Column(Date, comment="Vaccine expiration date")
    manufacturer_encrypted = Column(Text, comment="Encrypted manufacturer name")
    
    # Administration details
    route_code = Column(String(50), comment="Route of administration code")
    route_display = Column(String(255), comment="Route description")
    site_code = Column(String(50), comment="Body site code")
    site_display = Column(String(255), comment="Body site description")
    dose_quantity = Column(String(50), comment="Dose amount")
    dose_unit = Column(String(50), comment="Dose unit")
    
    # Provider information (encrypted PHI)
    performer_type = Column(String(100), comment="Type of performer")
    performer_name_encrypted = Column(Text, comment="Encrypted performer name")
    performer_organization_encrypted = Column(Text, comment="Encrypted organization")
    
    # Clinical information
    indication_codes = Column(ArrayType(String), comment="Reason codes for vaccination")
    contraindication_codes = Column(ArrayType(String), comment="Contraindication codes")
    
    # Reactions and adverse events
    reactions = Column(JSON, comment="Adverse reactions data")
    
    # FHIR resource
    fhir_resource = Column(JSON, comment="Complete FHIR R4 resource")
    
    # Consent and classification
    data_classification = Column(String(50), default=DataClassification.PHI.value, nullable=False)
    consent_required = Column(Boolean, default=True, comment="Whether consent is required for access")
    
    # Audit and compliance
    access_logs = Column(JSON, default=list, comment="PHI access audit trail")
    last_accessed_at = Column(DateTime, comment="Last PHI access timestamp")
    last_accessed_by = Column(UUIDType(), comment="Last user to access PHI")
    
    # Metadata
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(UUIDType(), nullable=False)
    updated_by = Column(UUIDType())
    
    # Soft delete
    soft_deleted_at = Column(DateTime, comment="Soft delete timestamp")
    deletion_reason = Column(Text, comment="Reason for deletion")
    deleted_by = Column(UUIDType(), comment="User who deleted record")
    
    # Tenant isolation
    tenant_id = Column(UUIDType(), index=True, comment="Tenant isolation")
    organization_id = Column(UUIDType(), index=True, comment="Organization context")
    
    # Database indexes for performance
    __table_args__ = (
        Index('idx_immunizations_patient_date', 'patient_id', 'occurrence_datetime'),
        Index('idx_immunizations_vaccine_code', 'vaccine_code'),
        Index('idx_immunizations_status', 'status'),
        Index('idx_immunizations_tenant', 'tenant_id', 'soft_deleted_at'),
        Index('idx_immunizations_created', 'created_at'),
        Index('idx_immunizations_fhir', 'fhir_id'),
    )
    
    def __repr__(self):
        return f"<Immunization(id={self.id}, vaccine={self.vaccine_display}, patient_id={self.patient_id})>"
    
    @property
    def is_active(self) -> bool:
        """Check if immunization record is active."""
        return self.soft_deleted_at is None and self.status == ImmunizationStatus.COMPLETED.value
    
    def to_fhir_dict(self, decrypt_phi: bool = False, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Convert to FHIR R4 Immunization resource format with enhanced compliance."""
        from app.core.security import security_manager
        
        # Base FHIR R4 structure
        fhir_resource = {
            "resourceType": "Immunization",
            "id": str(self.id),
            "meta": {
                "versionId": self.version or "1",
                "lastUpdated": self.updated_at.isoformat() if self.updated_at else self.created_at.isoformat(),
                "security": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ActReason",
                        "code": "HTEST" if self.data_classification != "PHI" else "PHI",
                        "display": "PHI" if self.data_classification == "PHI" else "Test Data"
                    }
                ]
            },
            "text": {
                "status": "generated",
                "div": f"<div xmlns=\"http://www.w3.org/1999/xhtml\">Immunization: {self.vaccine_display or 'Unknown vaccine'}</div>"
            },
            
            # Required fields
            "status": self.status,
            "vaccineCode": {
                "coding": [{
                    "system": self.vaccine_system or "http://hl7.org/fhir/sid/cvx",
                    "code": self.vaccine_code,
                    "display": self.vaccine_display
                }]
            },
            "patient": {
                "reference": f"Patient/{self.patient_id}",
                "type": "Patient"
            },
            "occurrenceDateTime": self.occurrence_datetime.isoformat(),
            "recorded": self.recorded_date.isoformat() if self.recorded_date else None,
            "primarySource": self.primary_source
        }
        
        # Optional fields with proper FHIR structure
        if self.lot_number_encrypted:
            if decrypt_phi and user_context:
                try:
                    decrypted_lot = security_manager.decrypt_data(self.lot_number_encrypted)
                    fhir_resource["lotNumber"] = decrypted_lot
                except Exception:
                    fhir_resource["lotNumber"] = "[ENCRYPTED]"
            else:
                fhir_resource["lotNumber"] = "[ENCRYPTED]"
        
        if self.expiration_date:
            fhir_resource["expirationDate"] = self.expiration_date.isoformat()
        
        # Administration site
        if self.site_code or self.site_display:
            fhir_resource["site"] = {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ActSite",
                    "code": self.site_code,
                    "display": self.site_display
                }]
            }
        
        # Route of administration
        if self.route_code or self.route_display:
            fhir_resource["route"] = {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v3-RouteOfAdministration",
                    "code": self.route_code,
                    "display": self.route_display
                }]
            }
        
        # Dose quantity
        if self.dose_quantity:
            fhir_resource["doseQuantity"] = {
                "value": float(self.dose_quantity) if self.dose_quantity.replace('.', '').isdigit() else None,
                "unit": self.dose_unit,
                "system": "http://unitsofmeasure.org",
                "code": self.dose_unit
            }
        
        # Performer information
        if self.performer_name_encrypted:
            performer_display = "[ENCRYPTED]"
            if decrypt_phi and user_context:
                try:
                    performer_display = security_manager.decrypt_data(self.performer_name_encrypted)
                except Exception:
                    pass
            
            fhir_resource["performer"] = [{
                "function": {
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0443",
                        "code": "AP",
                        "display": "Administering Provider"
                    }]
                },
                "actor": {
                    "display": performer_display
                }
            }]
        
        # Location (encrypted)
        if self.location_encrypted:
            location_display = "[ENCRYPTED]"
            if decrypt_phi and user_context:
                try:
                    location_display = security_manager.decrypt_data(self.location_encrypted)
                except Exception:
                    pass
            
            fhir_resource["location"] = {
                "display": location_display
            }
        
        # Manufacturer (encrypted)
        if self.manufacturer_encrypted:
            manufacturer_display = "[ENCRYPTED]"
            if decrypt_phi and user_context:
                try:
                    manufacturer_display = security_manager.decrypt_data(self.manufacturer_encrypted)
                except Exception:
                    pass
            
            fhir_resource["manufacturer"] = {
                "display": manufacturer_display
            }
        
        # Indication codes
        if self.indication_codes:
            fhir_resource["reasonCode"] = []
            for code in self.indication_codes:
                fhir_resource["reasonCode"].append({
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": code,
                        "display": code  # In production, look up the display name
                    }]
                })
        
        # Reactions
        if self.reactions:
            fhir_resource["reaction"] = self.reactions
        
        # FHIR Extensions for additional data
        extensions = []
        
        # Data classification extension
        extensions.append({
            "url": "http://fhir.local/StructureDefinition/data-classification",
            "valueString": self.data_classification
        })
        
        # Consent required extension
        extensions.append({
            "url": "http://fhir.local/StructureDefinition/consent-required",
            "valueBoolean": self.consent_required
        })
        
        if extensions:
            fhir_resource["extension"] = extensions
        
        return fhir_resource


class ImmunizationReaction(Base):
    """
    Immunization reaction/adverse event model.
    
    Tracks adverse reactions to immunizations with proper PHI protection.
    """
    __tablename__ = "immunization_reactions"
    
    # Primary identification
    id = Column(UUIDType(), primary_key=True, default=uuid.uuid4)
    
    # Relationships
    immunization_id = Column(UUIDType(), ForeignKey("immunizations.id"), nullable=False)
    immunization = relationship("Immunization", backref="adverse_reactions")
    
    # Reaction details
    reaction_date = Column(DateTime, comment="When reaction occurred")
    onset_period = Column(String(100), comment="Onset period description")
    
    # Clinical manifestation
    manifestation_code = Column(String(50), comment="Reaction manifestation code")
    manifestation_display = Column(String(255), comment="Human readable manifestation")
    manifestation_system = Column(String(255), comment="Coding system")
    
    # Severity and outcome
    severity = Column(String(50), comment="Reaction severity")
    outcome_code = Column(String(50), comment="Outcome code")
    outcome_display = Column(String(255), comment="Outcome description")
    
    # Clinical details (encrypted PHI)
    description_encrypted = Column(Text, comment="Encrypted reaction description")
    treatment_encrypted = Column(Text, comment="Encrypted treatment details")
    
    # Reporting
    reported_by_encrypted = Column(Text, comment="Encrypted reporter information")
    report_date = Column(DateTime, comment="When reaction was reported")
    
    # FHIR compliance
    fhir_resource = Column(JSON, comment="FHIR Observation resource for reaction")
    
    # Metadata
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(UUIDType(), nullable=False)
    
    # Soft delete
    soft_deleted_at = Column(DateTime)
    
    def __repr__(self):
        return f"<ImmunizationReaction(id={self.id}, severity={self.severity})>"


class VaccineInventory(Base):
    """
    Vaccine inventory tracking model.
    
    Manages vaccine stock, lot tracking, and expiration monitoring.
    """
    __tablename__ = "vaccine_inventory"
    
    # Primary identification
    id = Column(UUIDType(), primary_key=True, default=uuid.uuid4)
    
    # Vaccine identification
    vaccine_code = Column(String(50), nullable=False, index=True)
    vaccine_name = Column(String(255), nullable=False)
    manufacturer = Column(String(255))
    
    # Lot information
    lot_number = Column(String(100), nullable=False, index=True)
    expiration_date = Column(Date, nullable=False, index=True)
    
    # Inventory tracking
    quantity_received = Column(Integer, default=0)
    quantity_available = Column(Integer, default=0)
    quantity_administered = Column(Integer, default=0)
    quantity_wasted = Column(Integer, default=0)
    
    # Storage information
    storage_location = Column(String(255))
    storage_temperature = Column(String(50))
    cold_chain_maintained = Column(Boolean, default=True)
    
    # Dates
    received_date = Column(DateTime)
    first_use_date = Column(DateTime)
    last_use_date = Column(DateTime)
    
    # Metadata
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(UUIDType(), nullable=False)
    
    # Tenant isolation
    tenant_id = Column(UUIDType(), index=True)
    organization_id = Column(UUIDType(), index=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_vaccine_inventory_code_lot', 'vaccine_code', 'lot_number'),
        Index('idx_vaccine_inventory_expiration', 'expiration_date'),
        Index('idx_vaccine_inventory_available', 'quantity_available'),
    )
    
    def __repr__(self):
        return f"<VaccineInventory(vaccine={self.vaccine_name}, lot={self.lot_number})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if vaccine lot is expired."""
        return self.expiration_date < date.today()
    
    @property
    def is_available(self) -> bool:
        """Check if vaccine is available for use."""
        return self.quantity_available > 0 and not self.is_expired and self.cold_chain_maintained


class ImmunizationSchedule(Base):
    """
    Immunization schedule and reminder model.
    
    Tracks recommended immunization schedules and generates reminders.
    """
    __tablename__ = "immunization_schedules"
    
    # Primary identification
    id = Column(UUIDType(), primary_key=True, default=uuid.uuid4)
    
    # Patient relationship
    patient_id = Column(UUIDType(), ForeignKey("patients.id"), nullable=False, index=True)
    patient = relationship("Patient")
    
    # Schedule details
    vaccine_code = Column(String(50), nullable=False)
    vaccine_name = Column(String(255), nullable=False)
    series_name = Column(String(255), comment="Vaccine series name")
    dose_number = Column(Integer, comment="Dose number in series")
    
    # Timing
    recommended_date = Column(Date, comment="Recommended administration date")
    earliest_date = Column(Date, comment="Earliest acceptable date")
    latest_date = Column(Date, comment="Latest recommended date")
    
    # Status
    status = Column(String(50), default="due", comment="Schedule status")
    completed_immunization_id = Column(UUIDType(), ForeignKey("immunizations.id"))
    completed_immunization = relationship("Immunization")
    completion_date = Column(Date, comment="Date completed")
    
    # Reminders
    reminder_sent = Column(Boolean, default=False)
    reminder_date = Column(Date, comment="When reminder was sent")
    reminder_method = Column(String(50), comment="Reminder delivery method")
    
    # Clinical guidelines
    guideline_source = Column(String(255), comment="Guideline/protocol source")
    contraindications = Column(ArrayType(String), comment="Known contraindications")
    
    # Metadata
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(UUIDType(), nullable=False)
    
    # Tenant isolation
    tenant_id = Column(UUIDType(), index=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_schedule_patient_vaccine', 'patient_id', 'vaccine_code'),
        Index('idx_schedule_recommended_date', 'recommended_date'),
        Index('idx_schedule_status', 'status'),
    )
    
    def __repr__(self):
        return f"<ImmunizationSchedule(patient_id={self.patient_id}, vaccine={self.vaccine_name})>"