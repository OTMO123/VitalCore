"""
FHIR R4 Data Models and Validation Schemas

Implements FHIR R4 resource structures for healthcare interoperability.
Based on HL7 FHIR R4 specification.
"""

from datetime import date, datetime, timezone
from typing import Optional, List, Dict, Any, Union, Literal
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
import re


class FHIRResourceType(str, Enum):
    """FHIR Resource Types"""
    PATIENT = "Patient"
    IMMUNIZATION = "Immunization"
    OBSERVATION = "Observation"
    ENCOUNTER = "Encounter"
    CONDITION = "Condition"
    MEDICATION_REQUEST = "MedicationRequest"
    DIAGNOSTIC_REPORT = "DiagnosticReport"
    DOCUMENT_REFERENCE = "DocumentReference"


class AdministrativeGender(str, Enum):
    """FHIR Administrative Gender value set"""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNKNOWN = "unknown"


class ImmunizationStatus(str, Enum):
    """Immunization status codes"""
    COMPLETED = "completed"
    ENTERED_IN_ERROR = "entered-in-error"
    NOT_DONE = "not-done"


# Base FHIR Data Types
class FHIRIdentifier(BaseModel):
    """FHIR Identifier data type"""
    use: Optional[str] = Field(None, description="usual | official | temp | secondary | old")
    type: Optional[Dict[str, Any]] = Field(None, description="Description of identifier")
    system: Optional[str] = Field(None, description="The namespace for the identifier value")
    value: Optional[str] = Field(None, description="The value that is unique")
    period: Optional[Dict[str, Any]] = Field(None, description="Time period when id is/was valid for use")
    assigner: Optional[str] = Field(None, description="Organization that issued id")

    @field_validator('system')
    @classmethod
    def validate_system_uri(cls, v):
        if v and not re.match(r'^https?://|urn:', v):
            raise ValueError('System must be a valid URI')
        return v


class FHIRHumanName(BaseModel):
    """FHIR HumanName data type"""
    use: Optional[str] = Field(None, description="usual | official | temp | nickname | anonymous | old | maiden")
    text: Optional[str] = Field(None, description="Text representation of the full name")
    family: Optional[str] = Field(None, description="Family name (often called 'Surname')")
    given: Optional[List[str]] = Field(None, description="Given names (not always 'first'). Includes middle names")
    prefix: Optional[List[str]] = Field(None, description="Parts that come before the name")
    suffix: Optional[List[str]] = Field(None, description="Parts that come after the name")
    period: Optional[Dict[str, Any]] = Field(None, description="Time period when name was/is in use")


class FHIRAddress(BaseModel):
    """FHIR Address data type"""
    use: Optional[str] = Field(None, description="home | work | temp | old | billing")
    type: Optional[str] = Field(None, description="postal | physical | both")
    text: Optional[str] = Field(None, description="Text representation of the address")
    line: Optional[List[str]] = Field(None, description="Street name, number, direction & P.O. Box etc.")
    city: Optional[str] = Field(None, description="Name of city, town etc.")
    district: Optional[str] = Field(None, description="District name (aka county)")
    state: Optional[str] = Field(None, description="Sub-unit of country (abbreviations ok)")
    postalCode: Optional[str] = Field(None, description="Postal code for area")
    country: Optional[str] = Field(None, description="Country (e.g. can be ISO 3166 2 or 3 letter code)")
    period: Optional[Dict[str, Any]] = Field(None, description="Time period when address was/is in use")


class FHIRContactPoint(BaseModel):
    """FHIR ContactPoint data type"""
    system: Optional[str] = Field(None, description="phone | fax | email | pager | url | sms | other")
    value: Optional[str] = Field(None, description="The actual contact point details")
    use: Optional[str] = Field(None, description="home | work | temp | old | mobile")
    rank: Optional[int] = Field(None, description="Specify preferred order of use (1 = highest)")
    period: Optional[Dict[str, Any]] = Field(None, description="Time period when the contact point was/is in use")

    @field_validator('system')
    @classmethod
    def validate_system(cls, v):
        valid_systems = {'phone', 'fax', 'email', 'pager', 'url', 'sms', 'other'}
        if v and v not in valid_systems:
            raise ValueError(f'System must be one of {valid_systems}')
        return v


class FHIRCoding(BaseModel):
    """FHIR Coding data type"""
    system: Optional[str] = Field(None, description="Identity of the terminology system")
    version: Optional[str] = Field(None, description="Version of the system - if relevant")
    code: Optional[str] = Field(None, description="Symbol in syntax defined by the system")
    display: Optional[str] = Field(None, description="Representation defined by the system")
    userSelected: Optional[bool] = Field(None, description="If this coding was chosen directly by the user")


class FHIRCodeableConcept(BaseModel):
    """FHIR CodeableConcept data type"""
    coding: Optional[List[FHIRCoding]] = Field(None, description="Code defined by a terminology system")
    text: Optional[str] = Field(None, description="Plain text representation of the concept")


class FHIRReference(BaseModel):
    """FHIR Reference data type"""
    reference: Optional[str] = Field(None, description="Literal reference, Relative, internal or absolute URL")
    type: Optional[str] = Field(None, description="Type the reference refers to (e.g. 'Patient')")
    identifier: Optional[FHIRIdentifier] = Field(None, description="Logical reference, when literal reference is not known")
    display: Optional[str] = Field(None, description="Text alternative for the resource")


class FHIRQuantity(BaseModel):
    """FHIR Quantity data type"""
    value: Optional[float] = Field(None, description="Numerical value (with implicit precision)")
    comparator: Optional[str] = Field(None, description="< | <= | >= | > - how to understand the value")
    unit: Optional[str] = Field(None, description="Unit representation")
    system: Optional[str] = Field(None, description="System that defines coded unit form")
    code: Optional[str] = Field(None, description="Coded form of the unit")


class FHIRPeriod(BaseModel):
    """FHIR Period data type"""
    start: Optional[datetime] = Field(None, description="Starting time with inclusive boundary")
    end: Optional[datetime] = Field(None, description="End time with inclusive boundary, if not ongoing")

    @model_validator(mode='after')
    def validate_period(self):
        if self.end and self.start and self.end < self.start:
            raise ValueError('End time must be after start time')
        return self


# FHIR Resource Models
class FHIRPatient(BaseModel):
    """FHIR Patient Resource - Enhanced for Enterprise Healthcare Compliance"""
    resourceType: Literal["Patient"] = Field(default="Patient")
    id: Optional[str] = Field(None, description="Logical id of this artifact")
    meta: Optional[Dict[str, Any]] = Field(None, description="Metadata about the resource")
    implicitRules: Optional[str] = Field(None, description="A set of rules under which this content was created")
    language: Optional[str] = Field(None, description="Language of the resource content")
    text: Optional[Dict[str, Any]] = Field(None, description="Text summary of the resource")
    contained: Optional[List[Dict[str, Any]]] = Field(None, description="Contained, inline Resources")
    extension: Optional[List[Dict[str, Any]]] = Field(None, description="Additional content defined by implementations")
    modifierExtension: Optional[List[Dict[str, Any]]] = Field(None, description="Extensions that cannot be ignored")
    
    # Core Patient Elements (FHIR R4 Required)
    identifier: Optional[List[FHIRIdentifier]] = Field(None, description="An identifier for this patient")
    active: Optional[bool] = Field(True, description="Whether this patient's record is in active use")
    name: Optional[List[FHIRHumanName]] = Field(None, description="A name associated with the patient")
    telecom: Optional[List[FHIRContactPoint]] = Field(None, description="A contact detail for the individual")
    gender: Optional[AdministrativeGender] = Field(None, description="male | female | other | unknown")
    birthDate: Optional[date] = Field(None, description="The date of birth for the individual")
    
    # Administrative Elements
    deceasedBoolean: Optional[bool] = Field(None, description="Indicates if the individual is deceased")
    deceasedDateTime: Optional[datetime] = Field(None, description="Indicates date/time the individual died")
    address: Optional[List[FHIRAddress]] = Field(None, description="An address for the individual")
    maritalStatus: Optional[FHIRCodeableConcept] = Field(None, description="Marital (civil) status of a patient")
    multipleBirthBoolean: Optional[bool] = Field(None, description="Whether patient is part of a multiple birth")
    multipleBirthInteger: Optional[int] = Field(None, description="The actual birth order")
    photo: Optional[List[Dict[str, Any]]] = Field(None, description="Image of the patient")
    
    # Contact and Emergency Information
    contact: Optional[List[Dict[str, Any]]] = Field(None, description="A contact party (e.g. guardian, partner, friend) for the patient")
    communication: Optional[List[Dict[str, Any]]] = Field(None, description="A language which may be used to communicate with the patient")
    
    # Care Team and Provider References
    generalPractitioner: Optional[List[FHIRReference]] = Field(None, description="Patient's nominated primary care provider")
    managingOrganization: Optional[FHIRReference] = Field(None, description="Organization that is the custodian of the patient record")
    
    # Links to other patient resources
    link: Optional[List[Dict[str, Any]]] = Field(None, description="Link to another patient resource that concerns the same actual patient")

    @model_validator(mode='after')
    def validate_patient_requirements(self):
        """Validate FHIR R4 Patient business rules"""
        # At least one identifier should be present
        if not self.identifier or len(self.identifier) == 0:
            # This is allowed but recommended to have at least one identifier
            pass
        
        # If deceased, cannot have multiple birth information
        if (self.deceasedBoolean or self.deceasedDateTime) and (self.multipleBirthBoolean or self.multipleBirthInteger):
            # This is actually allowed in FHIR, just documenting the business logic
            pass
        
        # Only one deceased field should be present
        if self.deceasedBoolean is not None and self.deceasedDateTime is not None:
            raise ValueError("Only one of deceasedBoolean or deceasedDateTime should be provided")
        
        # Only one multipleBirth field should be present
        if self.multipleBirthBoolean is not None and self.multipleBirthInteger is not None:
            raise ValueError("Only one of multipleBirthBoolean or multipleBirthInteger should be provided")
        
        return self

    @field_validator('identifier')
    @classmethod
    def validate_identifiers(cls, v):
        """Validate patient identifiers for healthcare compliance"""
        if v:
            for identifier in v:
                # MRN identifiers should have proper system
                if identifier.type and identifier.type.get('coding'):
                    for coding in identifier.type['coding']:
                        if coding.get('code') == 'MR' and not identifier.system:
                            raise ValueError("MRN identifiers must specify a system")
        return v

    model_config = ConfigDict(use_enum_values=True)


class FHIRImmunization(BaseModel):
    """FHIR Immunization Resource - Enhanced for Enterprise Healthcare Compliance"""
    resourceType: Literal["Immunization"] = Field(default="Immunization")
    id: Optional[str] = Field(None, description="Logical id of this artifact")
    meta: Optional[Dict[str, Any]] = Field(None, description="Metadata about the resource")
    implicitRules: Optional[str] = Field(None, description="A set of rules under which this content was created")
    language: Optional[str] = Field(None, description="Language of the resource content")
    text: Optional[Dict[str, Any]] = Field(None, description="Text summary of the resource")
    contained: Optional[List[Dict[str, Any]]] = Field(None, description="Contained, inline Resources")
    extension: Optional[List[Dict[str, Any]]] = Field(None, description="Additional content defined by implementations")
    modifierExtension: Optional[List[Dict[str, Any]]] = Field(None, description="Extensions that cannot be ignored")
    
    # Core Immunization Elements (FHIR R4 Required)
    identifier: Optional[List[FHIRIdentifier]] = Field(None, description="Business identifier")
    status: ImmunizationStatus = Field(..., description="completed | entered-in-error | not-done")
    statusReason: Optional[FHIRCodeableConcept] = Field(None, description="Reason not done")
    vaccineCode: FHIRCodeableConcept = Field(..., description="Vaccine product administered")
    patient: FHIRReference = Field(..., description="Who was immunized")
    encounter: Optional[FHIRReference] = Field(None, description="Encounter immunization was part of")
    
    # Occurrence (date/time of administration) - Choice element
    occurrenceDateTime: Optional[datetime] = Field(None, description="Vaccine administration date")
    occurrenceString: Optional[str] = Field(None, description="Vaccine administration date as string")
    
    # Recording and Source Information
    recorded: Optional[datetime] = Field(None, description="When the immunization was first captured in the subject's record")
    primarySource: Optional[bool] = Field(True, description="Indicates context the data was recorded in")
    reportOrigin: Optional[FHIRCodeableConcept] = Field(None, description="Indicates the source of a secondarily reported record")
    
    # Location and Provider
    location: Optional[FHIRReference] = Field(None, description="Where immunization occurred")
    manufacturer: Optional[FHIRReference] = Field(None, description="Vaccine manufacturer")
    lotNumber: Optional[str] = Field(None, description="Vaccine lot number")
    expirationDate: Optional[date] = Field(None, description="Vaccine expiration date")
    
    # Administration Details
    site: Optional[FHIRCodeableConcept] = Field(None, description="Body site vaccine was administered")
    route: Optional[FHIRCodeableConcept] = Field(None, description="How vaccine entered body")
    doseQuantity: Optional[FHIRQuantity] = Field(None, description="Amount of vaccine administered")
    
    # Performers and Education
    performer: Optional[List[Dict[str, Any]]] = Field(None, description="Who performed event")
    note: Optional[List[Dict[str, Any]]] = Field(None, description="Additional immunization notes")
    
    # Clinical Reasoning
    reasonCode: Optional[List[FHIRCodeableConcept]] = Field(None, description="Why immunization occurred")
    reasonReference: Optional[List[FHIRReference]] = Field(None, description="Why immunization occurred")
    
    # Dosage and Potency
    isSubpotent: Optional[bool] = Field(None, description="Dose potency")
    subpotentReason: Optional[List[FHIRCodeableConcept]] = Field(None, description="Reason for being subpotent")
    
    # Patient Education
    education: Optional[List[Dict[str, Any]]] = Field(None, description="Educational material presented to patient")
    
    # Program and Funding
    programEligibility: Optional[List[FHIRCodeableConcept]] = Field(None, description="Patient eligibility for a vaccination program")
    fundingSource: Optional[FHIRCodeableConcept] = Field(None, description="Funding source for the vaccine")
    
    # Adverse Reactions
    reaction: Optional[List[Dict[str, Any]]] = Field(None, description="Details of a reaction that follows immunization")
    
    # Protocol Applied
    protocolApplied: Optional[List[Dict[str, Any]]] = Field(None, description="Protocol followed by the provider")

    @model_validator(mode='after')
    def validate_immunization_requirements(self):
        """Validate FHIR R4 Immunization business rules"""
        # Ensure only one of occurrenceDateTime or occurrenceString is provided
        if self.occurrenceDateTime is not None and self.occurrenceString is not None:
            raise ValueError('Only one of occurrenceDateTime or occurrenceString should be provided')
        
        # At least one occurrence field should be provided for completed immunizations
        if (self.status == ImmunizationStatus.COMPLETED and 
            self.occurrenceDateTime is None and self.occurrenceString is None):
            raise ValueError('Completed immunizations must have occurrence date/time')
        
        # If not done, status reason should be provided
        if self.status == ImmunizationStatus.NOT_DONE and not self.statusReason:
            raise ValueError('Immunizations with status "not-done" should have a status reason')
        
        # Primary source should be True if no report origin is specified
        if not self.reportOrigin and self.primarySource is not True:
            raise ValueError('Primary source should be True when no report origin is specified')
        
        # Validate vaccine code has proper coding system
        if self.vaccineCode and self.vaccineCode.coding:
            for coding in self.vaccineCode.coding:
                if not coding.system:
                    raise ValueError('Vaccine code must include coding system (e.g., CVX)')
                    
        return self

    @field_validator('patient')
    @classmethod
    def validate_patient_reference(cls, v):
        """Validate patient reference is properly formatted"""
        if not v.reference and not v.identifier:
            raise ValueError('Patient reference must include either reference or identifier')
        if v.reference and not v.reference.startswith('Patient/'):
            raise ValueError('Patient reference must be in format "Patient/{id}"')
        return v

    @field_validator('vaccineCode')
    @classmethod
    def validate_vaccine_code(cls, v):
        """Validate vaccine code follows standard terminologies"""
        if v.coding:
            for coding in v.coding:
                # Check for standard vaccine code systems
                valid_systems = [
                    'http://hl7.org/fhir/sid/cvx',  # CVX vaccine codes
                    'http://hl7.org/fhir/sid/ndc',  # NDC codes
                    'http://snomed.info/sct'        # SNOMED CT
                ]
                if coding.system and coding.system not in valid_systems:
                    # Log warning but don't fail validation for flexibility
                    pass
                if not coding.code:
                    raise ValueError('Vaccine coding must include code')
        return v

    model_config = ConfigDict(use_enum_values=True)


class FHIRObservation(BaseModel):
    """FHIR Observation Resource"""
    resourceType: Literal["Observation"] = Field(default="Observation")
    id: Optional[str] = Field(None, description="Logical id of this artifact")
    meta: Optional[Dict[str, Any]] = Field(None, description="Metadata about the resource")
    identifier: Optional[List[FHIRIdentifier]] = Field(None, description="Business identifier")
    basedOn: Optional[List[FHIRReference]] = Field(None, description="Fulfills plan, proposal or order")
    partOf: Optional[List[FHIRReference]] = Field(None, description="Part of referenced event")
    status: str = Field(..., description="registered | preliminary | final | amended +")
    category: Optional[List[FHIRCodeableConcept]] = Field(None, description="Classification of type of observation")
    code: FHIRCodeableConcept = Field(..., description="Type of observation (code / type)")
    subject: Optional[FHIRReference] = Field(None, description="Who and/or what the observation is about")
    focus: Optional[List[FHIRReference]] = Field(None, description="What the observation is about, when it is not about the subject of record")
    encounter: Optional[FHIRReference] = Field(None, description="Healthcare event during which this observation is made")
    effectiveDateTime: Optional[datetime] = Field(None, description="Clinically relevant time/time-period for observation")
    effectivePeriod: Optional[FHIRPeriod] = Field(None, description="Clinically relevant time/time-period for observation")
    issued: Optional[datetime] = Field(None, description="Date/Time this version was made available")
    performer: Optional[List[FHIRReference]] = Field(None, description="Who is responsible for the observation")
    valueQuantity: Optional[FHIRQuantity] = Field(None, description="Actual result")
    valueCodeableConcept: Optional[FHIRCodeableConcept] = Field(None, description="Actual result")
    valueString: Optional[str] = Field(None, description="Actual result")
    valueBoolean: Optional[bool] = Field(None, description="Actual result")
    valueInteger: Optional[int] = Field(None, description="Actual result")
    valueRange: Optional[Dict[str, Any]] = Field(None, description="Actual result")
    valueRatio: Optional[Dict[str, Any]] = Field(None, description="Actual result")
    valueSampledData: Optional[Dict[str, Any]] = Field(None, description="Actual result")
    valueTime: Optional[str] = Field(None, description="Actual result")
    valueDateTime: Optional[datetime] = Field(None, description="Actual result")
    valuePeriod: Optional[FHIRPeriod] = Field(None, description="Actual result")
    dataAbsentReason: Optional[FHIRCodeableConcept] = Field(None, description="Why the result is missing")
    interpretation: Optional[List[FHIRCodeableConcept]] = Field(None, description="High, low, normal, etc.")
    note: Optional[List[Dict[str, Any]]] = Field(None, description="Comments about the observation")
    bodySite: Optional[FHIRCodeableConcept] = Field(None, description="Observed body part")
    method: Optional[FHIRCodeableConcept] = Field(None, description="How it was done")
    specimen: Optional[FHIRReference] = Field(None, description="Specimen used for this observation")
    device: Optional[FHIRReference] = Field(None, description="(Measurement) Device")
    referenceRange: Optional[List[Dict[str, Any]]] = Field(None, description="Provides guide for interpretation")
    hasMember: Optional[List[FHIRReference]] = Field(None, description="Related resource that belongs to the Observation group")
    derivedFrom: Optional[List[FHIRReference]] = Field(None, description="Related measurements the observation is made from")
    component: Optional[List[Dict[str, Any]]] = Field(None, description="Component results")

    model_config = ConfigDict(use_enum_values=True)


class FHIRAllergyIntolerance(BaseModel):
    """FHIR AllergyIntolerance Resource - Enhanced for Enterprise Healthcare Compliance"""
    resourceType: Literal["AllergyIntolerance"] = Field(default="AllergyIntolerance")
    id: Optional[str] = Field(None, description="Logical id of this artifact")
    meta: Optional[Dict[str, Any]] = Field(None, description="Metadata about the resource")
    implicitRules: Optional[str] = Field(None, description="A set of rules under which this content was created")
    language: Optional[str] = Field(None, description="Language of the resource content")
    text: Optional[Dict[str, Any]] = Field(None, description="Text summary of the resource")
    contained: Optional[List[Dict[str, Any]]] = Field(None, description="Contained, inline Resources")
    extension: Optional[List[Dict[str, Any]]] = Field(None, description="Additional content defined by implementations")
    modifierExtension: Optional[List[Dict[str, Any]]] = Field(None, description="Extensions that cannot be ignored")
    
    # Core AllergyIntolerance Elements
    identifier: Optional[List[FHIRIdentifier]] = Field(None, description="External ids for this item")
    clinicalStatus: Optional[FHIRCodeableConcept] = Field(None, description="active | inactive | resolved")
    verificationStatus: Optional[FHIRCodeableConcept] = Field(None, description="unconfirmed | confirmed | refuted | entered-in-error")
    type: Optional[str] = Field(None, description="allergy | intolerance - Underlying mechanism (if known)")
    category: Optional[List[str]] = Field(None, description="food | medication | environment | biologic")
    criticality: Optional[str] = Field(None, description="low | high | unable-to-assess")
    
    # What causes the allergy/intolerance
    code: Optional[FHIRCodeableConcept] = Field(None, description="Code that identifies the allergy or intolerance")
    patient: FHIRReference = Field(..., description="Who the sensitivity is for")
    encounter: Optional[FHIRReference] = Field(None, description="Encounter when the allergy or intolerance was asserted")
    
    # Timing
    onsetDateTime: Optional[datetime] = Field(None, description="When allergy or intolerance was identified")
    onsetAge: Optional[Dict[str, Any]] = Field(None, description="When allergy or intolerance was identified")
    onsetPeriod: Optional[FHIRPeriod] = Field(None, description="When allergy or intolerance was identified")
    onsetRange: Optional[Dict[str, Any]] = Field(None, description="When allergy or intolerance was identified")  
    onsetString: Optional[str] = Field(None, description="When allergy or intolerance was identified")
    
    # Recording and Source
    recordedDate: Optional[datetime] = Field(None, description="Date record was believed accurate")
    recorder: Optional[FHIRReference] = Field(None, description="Who recorded the sensitivity")
    asserter: Optional[FHIRReference] = Field(None, description="Source of the information about the allergy")
    
    # Clinical Information
    lastOccurrence: Optional[datetime] = Field(None, description="Date(/time) of last known occurrence of a reaction")
    note: Optional[List[Dict[str, Any]]] = Field(None, description="Additional text not captured in other fields")
    reaction: Optional[List[Dict[str, Any]]] = Field(None, description="Adverse Reaction Events linked to exposure to substance")

    @field_validator('patient')
    @classmethod
    def validate_patient_reference(cls, v):
        """Validate patient reference is properly formatted"""
        if not v.reference and not v.identifier:
            raise ValueError('Patient reference must include either reference or identifier')
        if v.reference and not v.reference.startswith('Patient/'):
            raise ValueError('Patient reference must be in format "Patient/{id}"')
        return v

    @field_validator('category')
    @classmethod
    def validate_category(cls, v):
        """Validate allergy category values"""
        if v:
            valid_categories = ['food', 'medication', 'environment', 'biologic']
            for category in v:
                if category not in valid_categories:
                    raise ValueError(f'Category must be one of {valid_categories}')
        return v

    model_config = ConfigDict(use_enum_values=True)


class FHIRBundle(BaseModel):
    """FHIR Bundle Resource - For collections and batch operations"""
    resourceType: Literal["Bundle"] = Field(default="Bundle")
    id: Optional[str] = Field(None, description="Logical id of this artifact")
    meta: Optional[Dict[str, Any]] = Field(None, description="Metadata about the resource")
    implicitRules: Optional[str] = Field(None, description="A set of rules under which this content was created")
    language: Optional[str] = Field(None, description="Language of the resource content")
    
    # Bundle-specific elements
    identifier: Optional[FHIRIdentifier] = Field(None, description="Persistent identifier for the bundle")
    type: str = Field(..., description="document | message | transaction | transaction-response | batch | batch-response | history | searchset | collection")
    timestamp: Optional[datetime] = Field(None, description="When the bundle was assembled")
    total: Optional[int] = Field(None, description="If search, the total number of matches")
    link: Optional[List[Dict[str, Any]]] = Field(None, description="Links related to this Bundle")
    entry: Optional[List[Dict[str, Any]]] = Field(None, description="Entry in the bundle - will have a resource or information")
    signature: Optional[Dict[str, Any]] = Field(None, description="Digital Signature")
    
    # Enterprise transaction control (SOC2/HIPAA compliance)
    rollback_on_error: Optional[bool] = Field(None, description="For transaction bundles, rollback all changes on any error (enterprise compliance)")

    @field_validator('type')
    @classmethod
    def validate_bundle_type(cls, v):
        """Validate bundle type"""
        valid_types = [
            'document', 'message', 'transaction', 'transaction-response',
            'batch', 'batch-response', 'history', 'searchset', 'collection'
        ]
        if v not in valid_types:
            raise ValueError(f'Bundle type must be one of {valid_types}')
        return v

    @model_validator(mode='after')
    def validate_bundle_requirements(self):
        """Validate FHIR Bundle business rules"""
        # Search bundles should have total
        if self.type == 'searchset' and self.total is None:
            # This is recommended but not strictly required
            pass
        
        # Document bundles should have timestamp
        if self.type == 'document' and not self.timestamp:
            raise ValueError('Document bundles must have a timestamp')
        
        # Transaction bundles with rollback_on_error should be flagged
        if self.type == 'transaction' and self.rollback_on_error is True:
            # This is enterprise-specific behavior for SOC2/HIPAA compliance
            pass
        
        return self

    model_config = ConfigDict(use_enum_values=True)


# Terminology Validation
class TerminologyValidator:
    """FHIR R4 Terminology Validation for Standard Code Systems"""
    
    # Standard terminology systems
    TERMINOLOGY_SYSTEMS = {
        'CVX': 'http://hl7.org/fhir/sid/cvx',
        'SNOMED_CT': 'http://snomed.info/sct',
        'LOINC': 'http://loinc.org',
        'ICD_10': 'http://hl7.org/fhir/sid/icd-10',
        'NDC': 'http://hl7.org/fhir/sid/ndc',
        'CPT': 'http://www.ama-assn.org/go/cpt',
        'RXNORM': 'http://www.nlm.nih.gov/research/umls/rxnorm'
    }
    
    # Common vaccine codes (CVX)
    VACCINE_CODES = {
        '03': 'MMR',
        '08': 'Hep B, adolescent or pediatric',
        '20': 'DTaP',
        '21': 'varicella',
        '88': 'influenza, unspecified formulation',
        '94': 'MMRV',
        '115': 'Tdap',
        '207': 'COVID-19, mRNA, LNP-S, PF, 100 mcg/0.5mL dose',
        '208': 'COVID-19, mRNA, LNP-S, PF, 30 mcg/0.3mL dose',
        '212': 'COVID-19, viral vector, non-replicating, recombinant spike protein-Ad26, PF, 0.5mL'
    }
    
    @classmethod
    def validate_vaccine_code(cls, coding: FHIRCoding) -> bool:
        """Validate vaccine code against CVX terminology"""
        if not coding.system or not coding.code:
            return False
        
        if coding.system == cls.TERMINOLOGY_SYSTEMS['CVX']:
            # In a production system, this would validate against the full CVX terminology
            # For now, we'll check against our common codes
            return coding.code in cls.VACCINE_CODES
        
        return True  # Allow other systems
    
    @classmethod
    def validate_terminology_binding(cls, codeable_concept: FHIRCodeableConcept, 
                                   expected_system: str) -> bool:
        """Validate that a CodeableConcept uses expected terminology system"""
        if not codeable_concept.coding:
            return False
        
        for coding in codeable_concept.coding:
            if coding.system == expected_system:
                return True
        
        return False


# Bundle Helper Functions
def create_fhir_bundle(bundle_type: str, resources: List[Dict[str, Any]], 
                      total: Optional[int] = None) -> FHIRBundle:
    """Create a FHIR Bundle with resources"""
    entries = []
    for resource in resources:
        entry = {
            "resource": resource
        }
        # Add fullUrl for resources with IDs
        if resource.get('id'):
            entry["fullUrl"] = f"{resource['resourceType']}/{resource['id']}"
        
        entries.append(entry)
    
    bundle_data = {
        "type": bundle_type,
        "entry": entries
    }
    
    if total is not None:
        bundle_data["total"] = total
    
    if bundle_type in ['document', 'message']:
        bundle_data["timestamp"] = datetime.now(timezone.utc)
    
    return FHIRBundle(**bundle_data)


def create_search_bundle(resources: List[Dict[str, Any]], total: int, 
                        links: Optional[List[Dict[str, Any]]] = None) -> FHIRBundle:
    """Create a FHIR searchset Bundle"""
    bundle_data = {
        "type": "searchset",
        "total": total,
        "entry": []
    }
    
    for resource in resources:
        entry = {
            "resource": resource,
            "search": {
                "mode": "match"
            }
        }
        # Add fullUrl for search results
        if resource.get('id'):
            entry["fullUrl"] = f"{resource['resourceType']}/{resource['id']}"
        
        bundle_data["entry"].append(entry)
    
    if links:
        bundle_data["link"] = links
    
    return FHIRBundle(**bundle_data)


# Validation function
def validate_fhir_resource(resource: Union[FHIRPatient, FHIRImmunization, FHIRObservation, FHIRAllergyIntolerance]) -> bool:
    """Validate FHIR resource structure and business rules"""
    try:
        # Pydantic validation happens automatically during instantiation
        # Additional business rule validation can be added here
        
        if isinstance(resource, FHIRPatient):
            # Patient-specific validation
            if resource.name and len(resource.name) == 0:
                raise ValueError("Patient must have at least one name")
                
        elif isinstance(resource, FHIRImmunization):
            # Immunization-specific validation
            if not resource.patient:
                raise ValueError("Immunization must reference a patient")
            if not resource.vaccineCode:
                raise ValueError("Immunization must specify vaccine code")
                
        elif isinstance(resource, FHIRObservation):
            # Observation-specific validation
            if not resource.status:
                raise ValueError("Observation must have status")
            if not resource.code:
                raise ValueError("Observation must have code")
        
        return True
        
    except Exception:
        return False


# Helper functions for FHIR resource creation
def create_patient_identifier(system: str, value: str, use: str = "usual") -> FHIRIdentifier:
    """Create a FHIR patient identifier"""
    return FHIRIdentifier(
        use=use,
        system=system,
        value=value
    )


def create_human_name(family: str, given: List[str], use: str = "official") -> FHIRHumanName:
    """Create a FHIR human name"""
    return FHIRHumanName(
        use=use,
        family=family,
        given=given
    )


def create_vaccine_code(system: str, code: str, display: str) -> FHIRCodeableConcept:
    """Create a vaccine code"""
    return FHIRCodeableConcept(
        coding=[FHIRCoding(
            system=system,
            code=code,
            display=display
        )]
    )


def create_patient_reference(patient_id: str) -> FHIRReference:
    """Create a patient reference"""
    return FHIRReference(
        reference=f"Patient/{patient_id}",
        type="Patient"
    )