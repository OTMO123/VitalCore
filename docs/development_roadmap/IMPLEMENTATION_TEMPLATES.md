# Implementation Templates & Practical Examples

## 🎯 Ready-to-Use Code Templates

These templates follow TDD/SOLID principles while maintaining security foundations and focusing on working functionality.

## 🔧 Backend Implementation Templates

### **1. Patient Service - Complete Implementation**

```python
# app/modules/healthcare_records/enhanced_service.py

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from fastapi import HTTPException, Depends
import uuid
from datetime import datetime

from app.core.security import EncryptionService, get_current_user
from app.core.audit_logger import audit_logger, AuditEventType
from app.core.database_unified import Patient, User
from .schemas import CreatePatientRequest, UpdatePatientRequest, PatientResponse, PatientFilters
from .repository import PatientRepository

class EnhancedPatientService:
    """Complete patient service with PHI protection and audit logging"""
    
    def __init__(self, 
                 repository: PatientRepository,
                 encryption_service: EncryptionService):
        self.repository = repository
        self.encryption = encryption_service
        
        # PHI fields that require encryption
        self.phi_fields = {
            'first_name', 'last_name', 'ssn', 'phone', 'email', 
            'address_line1', 'address_line2', 'emergency_contact_name',
            'emergency_contact_phone', 'insurance_id'
        }
    
    async def create_patient(self, 
                           patient_data: CreatePatientRequest, 
                           current_user: User,
                           db: AsyncSession) -> PatientResponse:
        """Create new patient with PHI encryption and comprehensive audit logging"""
        
        # 1. Validate user permissions
        if not self._can_create_patient(current_user):
            raise HTTPException(status_code=403, detail="Insufficient permissions to create patient")
        
        # 2. Encrypt PHI fields
        encrypted_data = await self._encrypt_phi_fields(patient_data.dict())
        
        # 3. Generate patient ID
        patient_id = str(uuid.uuid4())
        encrypted_data['id'] = patient_id
        
        # 4. Create patient record
        try:
            patient = await self.repository.create(encrypted_data, db)
            
            # 5. Log patient creation for audit
            await audit_logger.log_event(
                event_type=AuditEventType.PATIENT_CREATED,
                message=f"Patient created: {patient_id}",
                details={
                    "patient_id": patient_id,
                    "created_by": current_user.id,
                    "created_by_role": current_user.role,
                    "fields_created": list(patient_data.dict().keys())
                },
                context={
                    "user_id": current_user.id,
                    "session_id": getattr(current_user, 'session_id', None),
                    "ip_address": getattr(current_user, 'ip_address', None)
                },
                contains_phi=True,
                db=db
            )
            
            # 6. Return decrypted response
            return await self._create_patient_response(patient, current_user)
            
        except Exception as e:
            # Log creation failure
            await audit_logger.log_event(
                event_type=AuditEventType.PATIENT_CREATED,
                message=f"Patient creation failed: {str(e)}",
                details={
                    "error": str(e),
                    "attempted_by": current_user.id
                },
                context={"user_id": current_user.id},
                severity="high",
                db=db
            )
            raise HTTPException(status_code=500, detail="Failed to create patient")
    
    async def get_patient(self, 
                         patient_id: str, 
                         current_user: User,
                         purpose: str = "treatment",
                         db: AsyncSession) -> PatientResponse:
        """Get patient with access control and PHI audit logging"""
        
        # 1. Validate patient exists
        patient = await self.repository.get_by_id(patient_id, db)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # 2. Validate access permissions
        if not await self._validate_patient_access(patient_id, current_user, purpose):
            # Log unauthorized access attempt
            await audit_logger.log_event(
                event_type=AuditEventType.SECURITY_VIOLATION,
                message=f"Unauthorized patient access attempt",
                details={
                    "patient_id": patient_id,
                    "attempted_by": current_user.id,
                    "purpose": purpose,
                    "violation_type": "unauthorized_patient_access"
                },
                context={"user_id": current_user.id},
                severity="high",
                db=db
            )
            raise HTTPException(status_code=403, detail="Access denied")
        
        # 3. Decrypt PHI fields for authorized access
        decrypted_patient = await self._decrypt_patient_data(patient)
        
        # 4. Log PHI access for HIPAA audit
        await audit_logger.log_event(
            event_type=AuditEventType.PHI_ACCESSED,
            message=f"Patient PHI accessed",
            details={
                "patient_id": patient_id,
                "accessed_by": current_user.id,
                "access_purpose": purpose,
                "fields_accessed": list(self.phi_fields),
                "access_method": "direct_patient_view"
            },
            context={
                "user_id": current_user.id,
                "session_id": getattr(current_user, 'session_id', None)
            },
            contains_phi=True,
            data_classification="PHI",
            db=db
        )
        
        return await self._create_patient_response(decrypted_patient, current_user)
    
    async def update_patient(self, 
                           patient_id: str, 
                           updates: UpdatePatientRequest,
                           current_user: User,
                           db: AsyncSession) -> PatientResponse:
        """Update patient with change tracking and audit logging"""
        
        # 1. Get current patient for change tracking
        current_patient = await self.repository.get_by_id(patient_id, db)
        if not current_patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # 2. Validate update permissions
        if not await self._validate_patient_update_access(patient_id, current_user):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # 3. Encrypt updated PHI fields
        update_data = updates.dict(exclude_unset=True)
        encrypted_updates = await self._encrypt_phi_fields(update_data)
        
        # 4. Track what fields are being changed
        changed_fields = await self._get_changed_fields(current_patient, encrypted_updates)
        
        # 5. Update patient record
        try:
            updated_patient = await self.repository.update(patient_id, encrypted_updates, db)
            
            # 6. Log patient update for audit
            await audit_logger.log_event(
                event_type=AuditEventType.PATIENT_UPDATED,
                message=f"Patient updated: {patient_id}",
                details={
                    "patient_id": patient_id,
                    "updated_by": current_user.id,
                    "fields_changed": changed_fields,
                    "update_timestamp": datetime.utcnow().isoformat()
                },
                context={
                    "user_id": current_user.id,
                    "session_id": getattr(current_user, 'session_id', None)
                },
                contains_phi=True,
                db=db
            )
            
            return await self._create_patient_response(updated_patient, current_user)
            
        except Exception as e:
            await audit_logger.log_event(
                event_type=AuditEventType.PATIENT_UPDATED,
                message=f"Patient update failed: {str(e)}",
                details={
                    "patient_id": patient_id,
                    "attempted_by": current_user.id,
                    "error": str(e)
                },
                context={"user_id": current_user.id},
                severity="high",
                db=db
            )
            raise HTTPException(status_code=500, detail="Failed to update patient")
    
    async def search_patients(self, 
                            query: str,
                            filters: Optional[PatientFilters],
                            current_user: User,
                            page: int = 1,
                            size: int = 20,
                            db: AsyncSession) -> Dict[str, Any]:
        """Search patients with role-based filtering and audit logging"""
        
        # 1. Apply role-based access filters
        access_filters = await self._get_user_access_filters(current_user)
        
        # 2. Combine with search filters
        combined_filters = self._combine_filters(filters, access_filters)
        
        # 3. Perform search
        search_results = await self.repository.search_patients(
            query=query,
            filters=combined_filters,
            page=page,
            size=size,
            db=db
        )
        
        # 4. Decrypt patient data for search results
        decrypted_patients = []
        for patient in search_results['patients']:
            decrypted_patient = await self._decrypt_patient_list_fields(patient)
            decrypted_patients.append(decrypted_patient)
        
        # 5. Log search activity
        await audit_logger.log_event(
            event_type=AuditEventType.PATIENT_SEARCH,
            message=f"Patient search performed",
            details={
                "search_query": query,
                "results_count": len(decrypted_patients),
                "searched_by": current_user.id,
                "filters_applied": combined_filters
            },
            context={"user_id": current_user.id},
            db=db
        )
        
        return {
            "patients": decrypted_patients,
            "pagination": search_results['pagination'],
            "total_count": search_results['total_count']
        }
    
    async def delete_patient(self, 
                           patient_id: str,
                           current_user: User,
                           reason: str,
                           db: AsyncSession) -> Dict[str, str]:
        """Soft delete patient with comprehensive audit logging"""
        
        # 1. Validate delete permissions (usually admin only)
        if not self._can_delete_patient(current_user):
            raise HTTPException(status_code=403, detail="Insufficient permissions to delete patient")
        
        # 2. Get patient data before deletion for audit
        patient = await self.repository.get_by_id(patient_id, db)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # 3. Perform soft delete
        try:
            await self.repository.soft_delete(patient_id, current_user.id, reason, db)
            
            # 4. Log patient deletion
            await audit_logger.log_event(
                event_type=AuditEventType.PATIENT_DELETED,
                message=f"Patient deleted: {patient_id}",
                details={
                    "patient_id": patient_id,
                    "deleted_by": current_user.id,
                    "deletion_reason": reason,
                    "deletion_timestamp": datetime.utcnow().isoformat()
                },
                context={
                    "user_id": current_user.id,
                    "session_id": getattr(current_user, 'session_id', None)
                },
                severity="high",
                contains_phi=True,
                db=db
            )
            
            return {"status": "success", "message": "Patient deleted successfully"}
            
        except Exception as e:
            await audit_logger.log_event(
                event_type=AuditEventType.PATIENT_DELETED,
                message=f"Patient deletion failed: {str(e)}",
                details={
                    "patient_id": patient_id,
                    "attempted_by": current_user.id,
                    "error": str(e)
                },
                context={"user_id": current_user.id},
                severity="high",
                db=db
            )
            raise HTTPException(status_code=500, detail="Failed to delete patient")
    
    # Private helper methods
    async def _encrypt_phi_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt PHI fields in patient data"""
        encrypted_data = data.copy()
        
        for field, value in data.items():
            if field in self.phi_fields and value is not None:
                encrypted_data[field] = await self.encryption.encrypt(
                    str(value),
                    context={
                        "field": field,
                        "classification": "PHI",
                        "patient_id": data.get('id')
                    }
                )
        
        return encrypted_data
    
    async def _decrypt_patient_data(self, patient: Patient) -> Patient:
        """Decrypt all PHI fields for authorized access"""
        for field in self.phi_fields:
            encrypted_value = getattr(patient, field, None)
            if encrypted_value:
                try:
                    decrypted_value = await self.encryption.decrypt(encrypted_value)
                    setattr(patient, field, decrypted_value)
                except Exception as e:
                    # Log decryption failure but don't fail the request
                    print(f"Failed to decrypt field {field}: {e}")
                    setattr(patient, field, "[DECRYPTION_FAILED]")
        
        return patient
    
    async def _decrypt_patient_list_fields(self, patient: Patient) -> Patient:
        """Decrypt only necessary fields for patient list view"""
        list_fields = {'first_name', 'last_name', 'phone', 'email'}
        
        for field in list_fields:
            if field in self.phi_fields:
                encrypted_value = getattr(patient, field, None)
                if encrypted_value:
                    try:
                        decrypted_value = await self.encryption.decrypt(encrypted_value)
                        setattr(patient, field, decrypted_value)
                    except Exception:
                        setattr(patient, field, "[ENCRYPTED]")
        
        return patient
    
    def _can_create_patient(self, user: User) -> bool:
        """Check if user can create patients"""
        return user.role in ['admin', 'physician', 'nurse']
    
    def _can_delete_patient(self, user: User) -> bool:
        """Check if user can delete patients"""
        return user.role in ['admin', 'super_admin']
    
    async def _validate_patient_access(self, patient_id: str, user: User, purpose: str) -> bool:
        """Validate if user can access specific patient"""
        # Admin users can access any patient
        if user.role in ['admin', 'super_admin']:
            return True
        
        # Physicians can access their assigned patients
        if user.role == 'physician':
            # Check if patient is assigned to this physician
            is_assigned = await self.repository.is_patient_assigned_to_physician(
                patient_id, user.id
            )
            return is_assigned
        
        # Nurses can access patients in their department
        if user.role == 'nurse':
            # Check if patient is in nurse's department
            same_department = await self.repository.is_patient_in_nurse_department(
                patient_id, user.id
            )
            return same_department
        
        return False
    
    async def _validate_patient_update_access(self, patient_id: str, user: User) -> bool:
        """Validate if user can update specific patient"""
        # Only physicians and admins can update patients
        if user.role not in ['physician', 'admin', 'super_admin']:
            return False
        
        return await self._validate_patient_access(patient_id, user, "treatment")
    
    async def _create_patient_response(self, patient: Patient, user: User) -> PatientResponse:
        """Create patient response with appropriate fields for user role"""
        patient_dict = {
            "id": patient.id,
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "date_of_birth": patient.date_of_birth,
            "gender": patient.gender,
            "phone": patient.phone,
            "email": patient.email,
            "created_at": patient.created_at,
            "updated_at": patient.updated_at
        }
        
        # Include sensitive fields only for authorized roles
        if user.role in ['admin', 'physician']:
            patient_dict.update({
                "ssn": patient.ssn,
                "address_line1": patient.address_line1,
                "address_line2": patient.address_line2,
                "city": patient.city,
                "state": patient.state,
                "zip_code": patient.zip_code,
                "emergency_contact_name": patient.emergency_contact_name,
                "emergency_contact_phone": patient.emergency_contact_phone,
                "insurance_provider": patient.insurance_provider,
                "insurance_id": patient.insurance_id
            })
        
        return PatientResponse(**patient_dict)
    
    async def _get_changed_fields(self, current_patient: Patient, updates: Dict[str, Any]) -> List[str]:
        """Get list of fields that are being changed"""
        changed_fields = []
        
        for field, new_value in updates.items():
            current_value = getattr(current_patient, field, None)
            if current_value != new_value:
                changed_fields.append(field)
        
        return changed_fields
    
    async def _get_user_access_filters(self, user: User) -> Dict[str, Any]:
        """Get access filters based on user role"""
        if user.role in ['admin', 'super_admin']:
            return {}  # No restrictions for admins
        
        if user.role == 'physician':
            return {"assigned_physician_id": user.id}
        
        if user.role == 'nurse':
            return {"department_id": user.department_id}
        
        return {"id": None}  # No access for other roles
    
    def _combine_filters(self, user_filters: Optional[PatientFilters], 
                        access_filters: Dict[str, Any]) -> Dict[str, Any]:
        """Combine user search filters with access control filters"""
        combined = access_filters.copy()
        
        if user_filters:
            if user_filters.gender:
                combined["gender"] = user_filters.gender
            if user_filters.age_min:
                combined["age_min"] = user_filters.age_min
            if user_filters.age_max:
                combined["age_max"] = user_filters.age_max
            if user_filters.department_id:
                combined["department_id"] = user_filters.department_id
        
        return combined

# TDD Test Examples
@pytest.mark.asyncio
async def test_create_patient_encrypts_phi_data(patient_service, test_user, db_session):
    """Test that patient creation properly encrypts PHI data"""
    # Arrange
    patient_data = CreatePatientRequest(
        first_name="John",
        last_name="Doe",
        ssn="123-45-6789",
        date_of_birth="1990-01-01",
        gender="M",
        phone="555-0123",
        email="john.doe@example.com"
    )
    
    # Act
    patient_response = await patient_service.create_patient(
        patient_data, test_user, db_session
    )
    
    # Assert - Response should contain decrypted data
    assert patient_response.first_name == "John"
    assert patient_response.last_name == "Doe"
    assert patient_response.ssn == "123-45-6789"
    
    # Assert - Database should contain encrypted data
    db_patient = await patient_service.repository.get_raw_by_id(
        patient_response.id, db_session
    )
    assert db_patient.first_name != "John"  # Should be encrypted
    assert db_patient.ssn != "123-45-6789"  # Should be encrypted
    
    # Assert - Audit log should contain creation event
    audit_logs = await audit_logger.search_audit_logs(
        event_type=AuditEventType.PATIENT_CREATED,
        user_id=test_user.id,
        db=db_session
    )
    assert len(audit_logs) == 1
    assert audit_logs[0]["details"]["patient_id"] == patient_response.id

@pytest.mark.asyncio
async def test_get_patient_logs_phi_access(patient_service, test_patient, test_user, db_session):
    """Test that patient retrieval logs PHI access"""
    # Act
    patient_response = await patient_service.get_patient(
        test_patient.id, test_user, "treatment", db_session
    )
    
    # Assert - Patient data returned
    assert patient_response.id == test_patient.id
    
    # Assert - PHI access logged
    audit_logs = await audit_logger.search_audit_logs(
        event_type=AuditEventType.PHI_ACCESSED,
        user_id=test_user.id,
        db=db_session
    )
    assert len(audit_logs) == 1
    assert audit_logs[0]["details"]["patient_id"] == test_patient.id
    assert audit_logs[0]["details"]["access_purpose"] == "treatment"

@pytest.mark.asyncio
async def test_unauthorized_patient_access_denied(patient_service, test_patient, 
                                                unauthorized_user, db_session):
    """Test that unauthorized access is denied and logged"""
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await patient_service.get_patient(
            test_patient.id, unauthorized_user, "treatment", db_session
        )
    
    assert exc_info.value.status_code == 403
    
    # Assert - Security violation logged
    audit_logs = await audit_logger.search_audit_logs(
        event_type=AuditEventType.SECURITY_VIOLATION,
        user_id=unauthorized_user.id,
        db=db_session
    )
    assert len(audit_logs) == 1
    assert "unauthorized_patient_access" in audit_logs[0]["details"]["violation_type"]
```

### **2. FastAPI Router with Complete Error Handling**

```python
# app/modules/healthcare_records/enhanced_router.py

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import io

from app.core.database_unified import get_db
from app.core.security import get_current_user, require_role
from app.core.monitoring import track_performance, track_api_usage
from .enhanced_service import EnhancedPatientService
from .schemas import (
    CreatePatientRequest, UpdatePatientRequest, PatientResponse, 
    PatientListResponse, PatientFilters, BulkPatientOperation
)

router = APIRouter()

# Dependency injection
def get_patient_service() -> EnhancedPatientService:
    return EnhancedPatientService()

@router.post("/patients", response_model=PatientResponse)
@track_performance()
@track_api_usage()
async def create_patient(
    patient_data: CreatePatientRequest,
    current_user = Depends(require_role("physician")),
    db: AsyncSession = Depends(get_db),
    patient_service: EnhancedPatientService = Depends(get_patient_service)
):
    """
    Create a new patient record
    
    Requires physician role or higher. All PHI data is automatically encrypted
    and the creation is logged for audit compliance.
    
    **Security Features:**
    - PHI data encryption
    - Role-based access control
    - Comprehensive audit logging
    - Input validation and sanitization
    """
    try:
        patient = await patient_service.create_patient(patient_data, current_user, db)
        return patient
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Unexpected error in create_patient: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/patients/{patient_id}", response_model=PatientResponse)
@track_performance()
async def get_patient(
    patient_id: str,
    purpose: str = Query("treatment", description="Purpose of access (treatment, payment, operations)"),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    patient_service: EnhancedPatientService = Depends(get_patient_service)
):
    """
    Retrieve patient information
    
    **Access Control:**
    - Admins: Can access any patient
    - Physicians: Can access assigned patients
    - Nurses: Can access patients in their department
    
    **Audit Logging:**
    - All PHI access is logged for HIPAA compliance
    - Access purpose is recorded
    - Failed access attempts are logged as security violations
    """
    try:
        patient = await patient_service.get_patient(patient_id, current_user, purpose, db)
        return patient
    except PermissionError:
        raise HTTPException(status_code=403, detail="Access denied")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/patients/{patient_id}", response_model=PatientResponse)
@track_performance()
async def update_patient(
    patient_id: str,
    updates: UpdatePatientRequest,
    current_user = Depends(require_role("physician")),
    db: AsyncSession = Depends(get_db),
    patient_service: EnhancedPatientService = Depends(get_patient_service)
):
    """
    Update patient information
    
    **Change Tracking:**
    - All changes are tracked and logged
    - Previous values are preserved for audit
    - Field-level change history is maintained
    """
    try:
        patient = await patient_service.update_patient(patient_id, updates, current_user, db)
        return patient
    except PermissionError:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/patients", response_model=PatientListResponse)
@track_performance()
async def list_patients(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    search: Optional[str] = Query(None, description="Search query"),
    gender: Optional[str] = Query(None, description="Filter by gender"),
    age_min: Optional[int] = Query(None, ge=0, description="Minimum age"),
    age_max: Optional[int] = Query(None, le=120, description="Maximum age"),
    department_id: Optional[str] = Query(None, description="Filter by department"),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    patient_service: EnhancedPatientService = Depends(get_patient_service)
):
    """
    List and search patients
    
    **Role-based Filtering:**
    - Results are automatically filtered based on user role and permissions
    - Search queries are logged for audit compliance
    - Only authorized fields are returned in list view
    """
    try:
        filters = PatientFilters(
            gender=gender,
            age_min=age_min,
            age_max=age_max,
            department_id=department_id
        )
        
        result = await patient_service.search_patients(
            query=search or "",
            filters=filters,
            current_user=current_user,
            page=page,
            size=size,
            db=db
        )
        
        return PatientListResponse(
            patients=result["patients"],
            pagination={
                "page": page,
                "size": size,
                "total": result["total_count"],
                "pages": (result["total_count"] + size - 1) // size
            }
        )
    except Exception as e:
        logger.error(f"Error in list_patients: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve patients")

@router.delete("/patients/{patient_id}")
@track_performance()
async def delete_patient(
    patient_id: str,
    reason: str = Query(..., description="Reason for deletion"),
    current_user = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
    patient_service: EnhancedPatientService = Depends(get_patient_service)
):
    """
    Soft delete patient record
    
    **Security Requirements:**
    - Requires admin role
    - Deletion reason is mandatory
    - Operation is logged for audit
    - Data is soft deleted (not physically removed)
    """
    try:
        result = await patient_service.delete_patient(patient_id, current_user, reason, db)
        return result
    except PermissionError:
        raise HTTPException(status_code=403, detail="Admin role required")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/patients/bulk-operation")
@track_performance()
async def bulk_patient_operation(
    operation: BulkPatientOperation,
    current_user = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
    patient_service: EnhancedPatientService = Depends(get_patient_service)
):
    """
    Perform bulk operations on patients
    
    **Supported Operations:**
    - bulk_update: Update multiple patients
    - bulk_export: Export patient data
    - bulk_assign: Assign patients to physician
    """
    try:
        if operation.operation_type == "bulk_update":
            result = await patient_service.bulk_update_patients(
                operation.patient_ids,
                operation.update_data,
                current_user,
                db
            )
        elif operation.operation_type == "bulk_export":
            result = await patient_service.bulk_export_patients(
                operation.patient_ids,
                operation.export_format,
                current_user,
                db
            )
        elif operation.operation_type == "bulk_assign":
            result = await patient_service.bulk_assign_patients(
                operation.patient_ids,
                operation.physician_id,
                current_user,
                db
            )
        else:
            raise HTTPException(status_code=400, detail="Unsupported operation type")
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

@router.get("/patients/{patient_id}/audit-log")
@track_performance()
async def get_patient_audit_log(
    patient_id: str,
    current_user = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Get audit log for specific patient
    
    **Admin Only Feature:**
    - Complete audit trail for patient
    - Shows all access, modifications, and operations
    - Includes security events and violations
    """
    try:
        audit_logs = await audit_logger.search_audit_logs(
            event_type=None,  # All event types
            user_id=None,     # All users
            start_time=None,
            end_time=None,
            db=db
        )
        
        # Filter logs related to this patient
        patient_logs = [
            log for log in audit_logs
            if log.get("details", {}).get("patient_id") == patient_id
        ]
        
        return {"patient_id": patient_id, "audit_logs": patient_logs}
    except Exception as e:
        logger.error(f"Error retrieving audit log: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve audit log")

@router.post("/patients/import")
@track_performance()
async def import_patients(
    file: UploadFile = File(..., description="CSV file with patient data"),
    current_user = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
    patient_service: EnhancedPatientService = Depends(get_patient_service)
):
    """
    Import patients from CSV file
    
    **File Requirements:**
    - CSV format with required headers
    - Maximum file size: 10MB
    - Maximum 1000 records per import
    
    **Security Features:**
    - File validation and sanitization
    - Virus scanning (if configured)
    - Complete audit logging of import process
    """
    try:
        # Validate file
        if file.content_type != "text/csv":
            raise HTTPException(status_code=400, detail="Only CSV files are allowed")
        
        if file.size > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
        
        # Read and process file
        content = await file.read()
        result = await patient_service.import_patients_from_csv(
            content, current_user, db
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in patient import: {e}")
        raise HTTPException(status_code=500, detail="Import failed")

@router.get("/patients/export")
@track_performance()
async def export_patients(
    format: str = Query("csv", description="Export format (csv, xlsx, json)"),
    filters: Optional[str] = Query(None, description="JSON string of filters"),
    current_user = Depends(require_role("physician")),
    db: AsyncSession = Depends(get_db),
    patient_service: EnhancedPatientService = Depends(get_patient_service)
):
    """
    Export patient data
    
    **Export Formats:**
    - CSV: Comma-separated values
    - XLSX: Excel spreadsheet
    - JSON: JSON format
    
    **Security Features:**
    - Role-based data filtering
    - PHI handling according to user permissions
    - Complete audit logging of export operations
    """
    try:
        # Parse filters if provided
        filter_dict = {}
        if filters:
            import json
            filter_dict = json.loads(filters)
        
        # Generate export
        export_data = await patient_service.export_patients(
            format=format,
            filters=filter_dict,
            current_user=current_user,
            db=db
        )
        
        # Return file stream
        if format == "csv":
            media_type = "text/csv"
            filename = f"patients_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        elif format == "xlsx":
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = f"patients_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        else:
            media_type = "application/json"
            filename = f"patients_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        return StreamingResponse(
            io.BytesIO(export_data),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in patient export: {e}")
        raise HTTPException(status_code=500, detail="Export failed")

# Error handlers
@router.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return HTTPException(status_code=400, detail=str(exc))

@router.exception_handler(PermissionError)
async def permission_error_handler(request, exc):
    return HTTPException(status_code=403, detail=str(exc))

@router.exception_handler(Exception)
async def general_error_handler(request, exc):
    logger.error(f"Unhandled error in patients router: {exc}")
    return HTTPException(status_code=500, detail="Internal server error")
```
