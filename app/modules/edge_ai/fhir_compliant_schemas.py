"""
FHIR R4 Compliant Data Structures for Enterprise Healthcare ML

This module provides FHIR R4 compliant data structures and validation
for machine learning operations in healthcare environments, ensuring
full interoperability and regulatory compliance.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum
import uuid

class FHIRResourceType(str, Enum):
    """FHIR R4 Resource Types relevant to ML operations."""
    PATIENT = "Patient"
    OBSERVATION = "Observation"
    DIAGNOSTIC_REPORT = "DiagnosticReport"
    MEDICATION_REQUEST = "MedicationRequest"
    CONDITION = "Condition"
    PROCEDURE = "Procedure"
    ENCOUNTER = "Encounter"
    CARE_PLAN = "CarePlan"
    RISK_ASSESSMENT = "RiskAssessment"
    CLINICAL_IMPRESSION = "ClinicalImpression"

class FHIRStatus(str, Enum):
    """FHIR Resource Status values."""
    ACTIVE = "active"
    INACTIVE = "inactive" 
    ENTERED_IN_ERROR = "entered-in-error"
    DRAFT = "draft"
    FINAL = "final"
    AMENDED = "amended"
    CORRECTED = "corrected"
    CANCELLED = "cancelled"

class ObservationStatus(str, Enum):
    """FHIR Observation Status values."""
    REGISTERED = "registered"
    PRELIMINARY = "preliminary"
    FINAL = "final"
    AMENDED = "amended"
    CORRECTED = "corrected"
    CANCELLED = "cancelled"
    ENTERED_IN_ERROR = "entered-in-error"
    UNKNOWN = "unknown"

class FHIRIdentifier(BaseModel):
    """FHIR Identifier data type."""
    use: Optional[str] = Field(None, description="usual | official | temp | secondary")
    type: Optional[Dict[str, Any]] = Field(None, description="Description of identifier")
    system: Optional[str] = Field(None, description="The namespace for the identifier value")
    value: Optional[str] = Field(None, description="The value that is unique")
    period: Optional[Dict[str, str]] = Field(None, description="Time period when id is/was valid")

class FHIRCodeableConcept(BaseModel):
    """FHIR CodeableConcept data type."""
    coding: List[Dict[str, Any]] = Field(default_factory=list, description="Code defined by a terminology system")
    text: Optional[str] = Field(None, description="Plain text representation")

class FHIRQuantity(BaseModel):
    """FHIR Quantity data type."""
    value: Optional[float] = Field(None, description="Numerical value")
    comparator: Optional[str] = Field(None, description="< | <= | >= | >")
    unit: Optional[str] = Field(None, description="Unit representation")
    system: Optional[str] = Field(None, description="System that defines coded unit form") 
    code: Optional[str] = Field(None, description="Coded form of the unit")

class FHIRReference(BaseModel):
    """FHIR Reference data type."""
    reference: Optional[str] = Field(None, description="Literal reference, Relative, internal or absolute URL")
    type: Optional[str] = Field(None, description="Type the reference refers to")
    identifier: Optional[FHIRIdentifier] = Field(None, description="Logical reference")
    display: Optional[str] = Field(None, description="Text alternative for the resource")

class FHIRMeta(BaseModel):
    """FHIR Meta data type for resource metadata."""
    versionId: Optional[str] = Field(None, description="Version specific identifier")
    lastUpdated: Optional[datetime] = Field(None, description="When the resource version last changed")
    source: Optional[str] = Field(None, description="Identifies where the resource comes from")
    profile: List[str] = Field(default_factory=list, description="Profiles this resource claims to conform to")
    security: List[FHIRCodeableConcept] = Field(default_factory=list, description="Security Labels")
    tag: List[FHIRCodeableConcept] = Field(default_factory=list, description="Tags applied to this resource")

class FHIRPatient(BaseModel):
    """FHIR R4 Patient Resource for ML operations."""
    resourceType: str = Field(default="Patient", description="FHIR Resource Type")
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), description="Logical id")
    meta: Optional[FHIRMeta] = Field(None, description="Metadata about the resource")
    identifier: List[FHIRIdentifier] = Field(default_factory=list, description="An identifier for this patient")
    active: Optional[bool] = Field(True, description="Whether this patient's record is in active use")
    name: List[Dict[str, Any]] = Field(default_factory=list, description="A name associated with the patient")
    telecom: List[Dict[str, Any]] = Field(default_factory=list, description="A contact detail for the individual")
    gender: Optional[str] = Field(None, description="male | female | other | unknown")
    birthDate: Optional[str] = Field(None, description="The date of birth for the individual")
    address: List[Dict[str, Any]] = Field(default_factory=list, description="An address for the individual")
    maritalStatus: Optional[FHIRCodeableConcept] = Field(None, description="Marital (civil) status")
    contact: List[Dict[str, Any]] = Field(default_factory=list, description="A contact party for the patient")
    communication: List[Dict[str, Any]] = Field(default_factory=list, description="Patient's language")
    generalPractitioner: List[FHIRReference] = Field(default_factory=list, description="Patient's nominated primary care provider")
    managingOrganization: Optional[FHIRReference] = Field(None, description="Organization that is the custodian")

class FHIRObservation(BaseModel):
    """FHIR R4 Observation Resource for ML-generated clinical observations."""
    resourceType: str = Field(default="Observation", description="FHIR Resource Type")
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), description="Logical id")
    meta: Optional[FHIRMeta] = Field(None, description="Metadata about the resource")
    identifier: List[FHIRIdentifier] = Field(default_factory=list, description="Business Identifier for observation")
    status: ObservationStatus = Field(..., description="registered | preliminary | final | amended +")
    category: List[FHIRCodeableConcept] = Field(default_factory=list, description="Classification of type of observation")
    code: FHIRCodeableConcept = Field(..., description="Type of observation (code / type)")
    subject: Optional[FHIRReference] = Field(None, description="Who and/or what the observation is about")
    encounter: Optional[FHIRReference] = Field(None, description="Healthcare event during which this observation is made")
    effectiveDateTime: Optional[datetime] = Field(None, description="Clinically relevant time/time-period")
    issued: Optional[datetime] = Field(None, description="Date/Time this version was made available")
    performer: List[FHIRReference] = Field(default_factory=list, description="Who is responsible for the observation")
    valueQuantity: Optional[FHIRQuantity] = Field(None, description="Actual result")
    valueCodeableConcept: Optional[FHIRCodeableConcept] = Field(None, description="Actual result")
    valueString: Optional[str] = Field(None, description="Actual result") 
    dataAbsentReason: Optional[FHIRCodeableConcept] = Field(None, description="Why the result is missing")
    interpretation: List[FHIRCodeableConcept] = Field(default_factory=list, description="High, low, normal, etc.")
    note: List[Dict[str, Any]] = Field(default_factory=list, description="Comments about the observation")
    method: Optional[FHIRCodeableConcept] = Field(None, description="How it was done")
    specimen: Optional[FHIRReference] = Field(None, description="Specimen used for this observation")
    device: Optional[FHIRReference] = Field(None, description="Device used for this observation")
    referenceRange: List[Dict[str, Any]] = Field(default_factory=list, description="Provides guide for interpretation")
    derivedFrom: List[FHIRReference] = Field(default_factory=list, description="Related measurements the observation is made from")
    component: List[Dict[str, Any]] = Field(default_factory=list, description="Component results")

class FHIRDiagnosticReport(BaseModel):
    """FHIR R4 DiagnosticReport Resource for ML-generated diagnostic insights."""
    resourceType: str = Field(default="DiagnosticReport", description="FHIR Resource Type")
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), description="Logical id")
    meta: Optional[FHIRMeta] = Field(None, description="Metadata about the resource")
    identifier: List[FHIRIdentifier] = Field(default_factory=list, description="Business identifier for report")
    status: str = Field(..., description="registered | partial | preliminary | final +")
    category: List[FHIRCodeableConcept] = Field(default_factory=list, description="Service category")
    code: FHIRCodeableConcept = Field(..., description="Name/Code for this diagnostic report")
    subject: Optional[FHIRReference] = Field(None, description="The subject of the report")
    encounter: Optional[FHIRReference] = Field(None, description="Health care event when test ordered")
    effectiveDateTime: Optional[datetime] = Field(None, description="Clinically relevant time/time-period")
    issued: Optional[datetime] = Field(None, description="DateTime this version was made available")
    performer: List[FHIRReference] = Field(default_factory=list, description="Responsible Diagnostic Service")
    resultsInterpreter: List[FHIRReference] = Field(default_factory=list, description="Primary result interpreter")
    specimen: List[FHIRReference] = Field(default_factory=list, description="Specimens this report is based on")
    result: List[FHIRReference] = Field(default_factory=list, description="Observations")
    imagingStudy: List[FHIRReference] = Field(default_factory=list, description="Reference to imaging studies")
    conclusion: Optional[str] = Field(None, description="Clinical conclusion (interpretation) of test results")
    conclusionCode: List[FHIRCodeableConcept] = Field(default_factory=list, description="Codes for the clinical conclusion")
    presentedForm: List[Dict[str, Any]] = Field(default_factory=list, description="Entire report as issued")

class FHIRRiskAssessment(BaseModel):
    """FHIR R4 RiskAssessment Resource for ML-generated risk predictions."""
    resourceType: str = Field(default="RiskAssessment", description="FHIR Resource Type")
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), description="Logical id")
    meta: Optional[FHIRMeta] = Field(None, description="Metadata about the resource")
    identifier: List[FHIRIdentifier] = Field(default_factory=list, description="Unique identifier for the assessment")
    status: str = Field(..., description="registered | preliminary | final | amended +")
    method: Optional[FHIRCodeableConcept] = Field(None, description="Evaluation mechanism")
    code: Optional[FHIRCodeableConcept] = Field(None, description="Type of assessment")
    subject: FHIRReference = Field(..., description="Who/what does assessment apply to")
    encounter: Optional[FHIRReference] = Field(None, description="Where was assessment performed")
    occurrenceDateTime: Optional[datetime] = Field(None, description="When was assessment made")
    performer: Optional[FHIRReference] = Field(None, description="Who did assessment")
    reasonCode: List[FHIRCodeableConcept] = Field(default_factory=list, description="Why the assessment was necessary")
    reasonReference: List[FHIRReference] = Field(default_factory=list, description="Why the assessment was necessary")
    basis: List[FHIRReference] = Field(default_factory=list, description="Information used in assessment") 
    prediction: List[Dict[str, Any]] = Field(default_factory=list, description="Outcome predicted")
    mitigation: Optional[str] = Field(None, description="How to reduce risk")
    note: List[Dict[str, Any]] = Field(default_factory=list, description="Comments on the risk assessment")

class FHIRClinicalImpression(BaseModel):
    """FHIR R4 ClinicalImpression Resource for ML-generated clinical assessments."""
    resourceType: str = Field(default="ClinicalImpression", description="FHIR Resource Type")
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), description="Logical id")
    meta: Optional[FHIRMeta] = Field(None, description="Metadata about the resource")
    identifier: List[FHIRIdentifier] = Field(default_factory=list, description="Business identifier")
    status: str = Field(..., description="draft | completed | entered-in-error")
    statusReason: Optional[FHIRCodeableConcept] = Field(None, description="Reason for current status")
    code: Optional[FHIRCodeableConcept] = Field(None, description="Kind of assessment performed")
    description: Optional[str] = Field(None, description="Why/how the assessment was performed")
    subject: FHIRReference = Field(..., description="Patient or group assessed")
    encounter: Optional[FHIRReference] = Field(None, description="Encounter created as part of")
    effectiveDateTime: Optional[datetime] = Field(None, description="Time of assessment")
    date: Optional[datetime] = Field(None, description="When the assessment was documented")
    assessor: Optional[FHIRReference] = Field(None, description="The clinician performing the assessment")
    previous: Optional[FHIRReference] = Field(None, description="Reference to last assessment")
    problem: List[FHIRReference] = Field(default_factory=list, description="Relevant impressions of patient state")
    investigation: List[Dict[str, Any]] = Field(default_factory=list, description="One or more sets of investigations")
    protocol: List[str] = Field(default_factory=list, description="Clinical Protocol followed")
    summary: Optional[str] = Field(None, description="Summary of the assessment")
    finding: List[Dict[str, Any]] = Field(default_factory=list, description="Possible or likely findings")
    prognosisCodeableConcept: List[FHIRCodeableConcept] = Field(default_factory=list, description="Estimate of likely outcome")
    prognosisReference: List[FHIRReference] = Field(default_factory=list, description="RiskAssessment expressing likely outcome")
    supportingInfo: List[FHIRReference] = Field(default_factory=list, description="Information supporting the clinical impression")
    note: List[Dict[str, Any]] = Field(default_factory=list, description="Comments made about the ClinicalImpression")

class FHIRBundle(BaseModel):
    """FHIR R4 Bundle Resource for ML operation results."""
    resourceType: str = Field(default="Bundle", description="FHIR Resource Type")
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), description="Logical id")
    meta: Optional[FHIRMeta] = Field(None, description="Metadata about the resource")
    identifier: Optional[FHIRIdentifier] = Field(None, description="Persistent identifier for the bundle")
    type: str = Field(..., description="document | message | transaction | transaction-response | batch | batch-response | history | searchset | collection")
    timestamp: Optional[datetime] = Field(None, description="When the bundle was assembled")
    total: Optional[int] = Field(None, description="If search, the total number of matches")
    link: List[Dict[str, str]] = Field(default_factory=list, description="Links related to this Bundle")
    entry: List[Dict[str, Any]] = Field(default_factory=list, description="Entry in the bundle - will have a resource or information")
    signature: Optional[Dict[str, Any]] = Field(None, description="Digital Signature")

class MLFHIRConverter:
    """
    Converter for ML outputs to FHIR R4 compliant resources.
    
    Ensures all ML-generated healthcare data is properly structured
    according to FHIR R4 specifications for interoperability.
    """
    
    @staticmethod
    def convert_ml_observation_to_fhir(
        ml_result: Dict[str, Any],
        patient_reference: str,
        performer_reference: str = "Device/ml-engine"
    ) -> FHIRObservation:
        """Convert ML observation result to FHIR Observation."""
        
        # Create coding for ML-generated observation
        ml_coding = {
            "system": "http://loinc.org",
            "code": "72133-2", 
            "display": "Machine learning analysis"
        }
        
        observation = FHIRObservation(
            status=ObservationStatus.FINAL,
            category=[FHIRCodeableConcept(
                coding=[{
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "survey",
                    "display": "Survey"
                }],
                text="ML Analysis"
            )],
            code=FHIRCodeableConcept(
                coding=[ml_coding],
                text="Machine Learning Clinical Analysis"
            ),
            subject=FHIRReference(reference=patient_reference),
            effectiveDateTime=datetime.utcnow(),
            issued=datetime.utcnow(),
            performer=[FHIRReference(reference=performer_reference)],
            valueString=ml_result.get("analysis", ""),
            note=[{
                "text": f"ML Confidence: {ml_result.get('confidence', 0.0):.2f}",
                "time": datetime.utcnow().isoformat()
            }]
        )
        
        return observation
    
    @staticmethod
    def convert_ml_diagnosis_to_fhir(
        ml_diagnosis: Dict[str, Any],
        patient_reference: str,
        encounter_reference: Optional[str] = None
    ) -> FHIRDiagnosticReport:
        """Convert ML diagnosis to FHIR DiagnosticReport."""
        
        report = FHIRDiagnosticReport(
            status="final",
            category=[FHIRCodeableConcept(
                coding=[{
                    "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                    "code": "LAB",
                    "display": "Laboratory"
                }],
                text="ML Diagnostic Analysis"
            )],
            code=FHIRCodeableConcept(
                coding=[{
                    "system": "http://loinc.org",
                    "code": "11502-2",
                    "display": "Laboratory report"
                }],
                text="Machine Learning Diagnostic Report"
            ),
            subject=FHIRReference(reference=patient_reference),
            encounter=FHIRReference(reference=encounter_reference) if encounter_reference else None,
            effectiveDateTime=datetime.utcnow(),
            issued=datetime.utcnow(),
            performer=[FHIRReference(reference="Device/ml-engine")],
            conclusion=ml_diagnosis.get("conclusion", ""),
            conclusionCode=[FHIRCodeableConcept(
                coding=[{
                    "system": "http://snomed.info/sct",
                    "code": ml_diagnosis.get("snomed_code", "439401001"),
                    "display": ml_diagnosis.get("diagnosis", "Clinical finding")
                }]
            )]
        )
        
        return report
    
    @staticmethod
    def convert_ml_risk_to_fhir(
        ml_risk: Dict[str, Any],
        patient_reference: str
    ) -> FHIRRiskAssessment:
        """Convert ML risk assessment to FHIR RiskAssessment."""
        
        risk_assessment = FHIRRiskAssessment(
            status="final",
            method=FHIRCodeableConcept(
                coding=[{
                    "system": "http://terminology.hl7.org/CodeSystem/risk-assessment-method",
                    "code": "machine-learning",
                    "display": "Machine Learning"
                }],
                text="AI/ML Risk Assessment"
            ),
            subject=FHIRReference(reference=patient_reference),
            occurrenceDateTime=datetime.utcnow(),
            performer=FHIRReference(reference="Device/ml-engine"),
            prediction=[{
                "outcome": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": ml_risk.get("outcome_code", "365980008"),
                        "display": ml_risk.get("outcome", "Clinical risk")
                    }]
                },
                "probabilityDecimal": ml_risk.get("probability", 0.0),
                "rationale": ml_risk.get("rationale", "")
            }],
            mitigation=ml_risk.get("mitigation", ""),
            note=[{
                "text": f"ML Model: {ml_risk.get('model_version', 'unknown')}",
                "time": datetime.utcnow().isoformat()
            }]
        )
        
        return risk_assessment

    @staticmethod
    def create_ml_bundle(
        resources: List[BaseModel],
        bundle_type: str = "collection"
    ) -> FHIRBundle:
        """Create FHIR Bundle containing ML-generated resources."""
        
        entries = []
        for resource in resources:
            entries.append({
                "resource": resource.dict(exclude_none=True)
            })
        
        bundle = FHIRBundle(
            type=bundle_type,
            timestamp=datetime.utcnow(),
            total=len(entries),
            entry=entries
        )
        
        return bundle

    @staticmethod
    def validate_fhir_compliance(resource: BaseModel) -> Dict[str, Any]:
        """Validate FHIR R4 compliance of generated resources."""
        
        validation_result = {
            "is_compliant": True,
            "resource_type": resource.resourceType if hasattr(resource, 'resourceType') else "Unknown",
            "validation_errors": [],
            "warnings": [],
            "fhir_version": "R4",
            "validation_timestamp": datetime.utcnow().isoformat()
        }
        
        # Basic FHIR compliance checks
        if not hasattr(resource, 'resourceType'):
            validation_result["is_compliant"] = False
            validation_result["validation_errors"].append("Missing required resourceType")
        
        if hasattr(resource, 'id') and resource.id:
            # Validate ID format (alphanumeric, hyphen, period - max 64 chars)
            import re
            if not re.match(r'^[A-Za-z0-9\-\.]{1,64}$', resource.id):
                validation_result["warnings"].append("ID format may not be optimal")
        
        if hasattr(resource, 'meta') and resource.meta:
            if resource.meta.lastUpdated and resource.meta.lastUpdated > datetime.utcnow():
                validation_result["warnings"].append("lastUpdated is in the future")
        
        return validation_result