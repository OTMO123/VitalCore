# DEVELOPMENT_CONTEXT.md

## 🏥 Healthcare Document Management System - Development Context

**Project Type**: Enterprise-grade healthcare SaaS platform with SOC2 Type II compliance  
**Last Updated**: 2025-06-29  
**Version**: Production-ready with document management extensions needed

---

## 📊 CURRENT SYSTEM STATE

### ✅ PRODUCTION-READY COMPONENTS
- **Authentication**: JWT RS256 with MFA, OAuth2-compliant
- **Patient Management**: FHIR R4 compliant with PHI encryption (AES-256-GCM)
- **Audit Logging**: SOC2 Type II compliant immutable audit trails
- **IRIS API Integration**: Production-ready with circuit breakers
- **Database**: PostgreSQL with advanced encryption and soft deletes
- **Event System**: Advanced event bus with hybrid message handling
- **Testing**: Comprehensive test suite with 80%+ coverage

### ❌ DOCUMENT MANAGEMENT GAPS
- File storage backend (need MinIO integration)
- Document upload/drag-drop interface
- Document classification and auto-naming
- Version control and audit trails for files
- Bulk document processing
- Document search and indexing

---

## 🏗️ CRITICAL ARCHITECTURE INFORMATION

### **Database Connection & Sessions**
```python
# ALWAYS use these imports for database operations
from app.core.database_unified import get_db, Patient, ClinicalDocument, AuditLog
from sqlalchemy.ext.asyncio import AsyncSession

# Standard dependency injection pattern
async def endpoint_function(
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
```

### **Security & Encryption**
```python
# ALWAYS use SecurityManager for encryption
from app.core.security import SecurityManager, EncryptionService

security_manager = SecurityManager()
encrypted_data = security_manager.encrypt_data(sensitive_data)
decrypted_data = security_manager.decrypt_data(encrypted_data)

# PHI fields that MUST be encrypted
PHI_FIELDS = {
    'ssn', 'date_of_birth', 'first_name', 'last_name', 'middle_name',
    'address_line1', 'address_line2', 'city', 'postal_code',
    'phone_number', 'email', 'mrn'
}
```

### **Audit Logging Pattern**
```python
# ALWAYS log PHI access and security events
from app.core.audit_logger import audit_logger, AuditEventType, AuditSeverity

await audit_logger.log_event(
    event_type=AuditEventType.PATIENT_ACCESSED,
    user_id=current_user_id,
    resource_id=patient_id,
    details={"fields_accessed": ["first_name", "last_name"]},
    severity=AuditSeverity.INFO
)
```

---

## 🔧 EXISTING MODULES & ENDPOINTS

### **Patient Management** (`/app/modules/healthcare_records/`)
**Endpoints**:
- `POST /healthcare/patients` - Create patient
- `GET /healthcare/patients/{patient_id}` - Get patient
- `GET /healthcare/patients` - List patients  
- `PUT /healthcare/patients/{patient_id}` - Update patient
- `DELETE /healthcare/patients/{patient_id}` - Soft delete patient
- `GET /healthcare/patients/search` - Search patients

**Key Models**:
```python
class Patient(Base):
    id: UUID = Field(primary_key=True)
    first_name_encrypted: str
    last_name_encrypted: str  
    date_of_birth_encrypted: str
    ssn_encrypted: Optional[str]
    consent_status: Dict[str, Any]
    soft_deleted_at: Optional[datetime]
```

### **Clinical Documents** (`/app/modules/healthcare_records/`)
**Endpoints**:
- `POST /healthcare/documents` - Create clinical document ⚠️ **FAILING (500)**
- `GET /healthcare/documents` - List documents
- `GET /healthcare/documents/{document_id}` - Get document

**Key Models**:
```python
class ClinicalDocument(Base):
    id: UUID
    patient_id: UUID
    document_type: DocumentType
    title: str
    storage_key: str  # MinIO storage reference
    mime_type: str
    size_bytes: int
    hash_sha256: str
    metadata: Dict[str, Any]
```

### **Authentication** (`/app/modules/auth/`)
**Endpoints**:
- `POST /auth/login` - User login
- `POST /auth/refresh` - Token refresh
- `POST /auth/logout` - Logout

**Roles**:
```python
class UserRole(str, Enum):
    USER = "user"
    OPERATOR = "operator" 
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
```

### **IRIS API Integration** (`/app/modules/iris_api/`)
**Endpoints**:
- `GET /iris/health` - Health check
- `POST /iris/test-connection` - Test connectivity
- Various clinical data endpoints

---

## 🚨 CRITICAL DEVELOPMENT GUIDELINES

### **ALWAYS CHECK THESE BEFORE CODING**

#### **1. Database Enum Values**
```python
# Check existing enums in app/core/database_unified.py
class AuditEventType(str, Enum):
    USER_LOGIN = "user_login"
    PATIENT_CREATED = "patient_created"
    PATIENT_ACCESSED = "patient_accessed"
    # ADD NEW VALUES HERE - never modify existing ones

class DocumentType(str, Enum):
    LAB_RESULT = "lab_result"
    IMAGING = "imaging"
    CLINICAL_NOTE = "clinical_note"
    # ADD NEW DOCUMENT TYPES HERE
```

#### **2. Router Registration Pattern**
```python
# In app/main.py - ALWAYS follow this pattern
from app.modules.your_module.router import router as your_router
app.include_router(your_router, prefix="/your-prefix", tags=["Your Module"])
```

#### **3. Schema Validation**
```python
# ALWAYS use Pydantic schemas for request/response validation
from pydantic import BaseModel, Field, validator

class DocumentCreate(BaseModel):
    patient_id: str = Field(..., description="Patient UUID")
    document_type: DocumentType
    title: str = Field(..., min_length=1, max_length=255)
    
    @validator('patient_id')
    def validate_patient_id(cls, v):
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('Invalid UUID format')
```

#### **4. Error Handling Pattern**
```python
# ALWAYS use this error handling pattern
try:
    # Your operation here
    result = await some_operation()
    
    logger.info("Operation successful", 
               operation="operation_name",
               user_id=current_user_id,
               resource_id=resource_id)
    
    return result
    
except SpecificException as e:
    logger.error("Specific error occurred", 
                error=str(e), 
                user_id=current_user_id)
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Specific error message"
    )
except Exception as e:
    logger.error("Unexpected error", 
                error=str(e),
                user_id=current_user_id)
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal server error"
    )
```

---

## 📁 DIRECTORY STRUCTURE

```
app/
├── core/                          # Core infrastructure
│   ├── database_unified.py        # ⚠️ Main database models & enums
│   ├── security.py               # Encryption & auth utilities
│   ├── audit_logger.py           # SOC2 audit logging
│   ├── event_bus_advanced.py     # Event system
│   └── config.py                 # Configuration
├── modules/                       # Business logic modules
│   ├── auth/                     # Authentication (COMPLETE)
│   ├── healthcare_records/       # Patient & documents (PARTIAL)
│   ├── iris_api/                 # IRIS integration (COMPLETE)
│   ├── dashboard/                # Analytics dashboard (COMPLETE)
│   └── audit_logger/             # Audit management (COMPLETE)
├── schemas/                       # Pydantic schemas
│   └── fhir_r4.py               # FHIR compliance schemas
└── tests/                        # Comprehensive test suite
    ├── core/                     # Core component tests
    ├── integration/              # Integration tests
    └── smoke/                    # Smoke tests
```

---

## 🔐 SECURITY REQUIREMENTS

### **PHI Data Handling**
```python
# ALWAYS encrypt PHI fields before database storage
phi_fields = ['first_name', 'last_name', 'ssn', 'date_of_birth']
for field in phi_fields:
    if data.get(field):
        encrypted_value = security_manager.encrypt_data(data[field])
        setattr(entity, f"{field}_encrypted", encrypted_value)
```

### **Access Control**
```python
# ALWAYS require role-based access
@router.post("/sensitive-endpoint")
async def sensitive_operation(
    _: dict = Depends(require_role("admin")),  # Require admin role
    current_user_id: str = Depends(get_current_user_id)
):
```

### **Rate Limiting**
```python
# ALWAYS add rate limiting to public endpoints
async def public_endpoint(
    _rate_limit: bool = Depends(check_rate_limit)
):
```

---

## 🧪 TESTING REQUIREMENTS

### **Test File Naming**
```
tests/
├── core/
│   └── test_your_module.py      # Unit tests
├── integration/
│   └── test_your_integration.py # Integration tests
└── smoke/
    └── test_your_smoke.py       # Basic functionality tests
```

### **Test Pattern**
```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_endpoint_success():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/your-endpoint", json=test_data)
    
    assert response.status_code == 201
    assert response.json()["id"] is not None
```

---

## 🚀 DOCUMENT MANAGEMENT TODO

### **Next Implementation Priority**
1. **MinIO Storage Service** - File storage backend
2. **Document Upload API** - Fix failing clinical documents endpoint
3. **Document Processing Pipeline** - OCR, classification, smart naming
4. **React Upload Interface** - Drag-drop file upload
5. **Document Search** - Full-text search with Elasticsearch

### **Database Schema Extensions Needed**
```sql
-- Document storage table (to be created)
CREATE TABLE document_storage (
    id UUID PRIMARY KEY,
    patient_id UUID REFERENCES patients(id),
    original_filename VARCHAR(255) NOT NULL,
    storage_path VARCHAR(500) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    document_category VARCHAR(100), -- Lab, Imaging, Clinical Notes
    extracted_text TEXT, -- OCR/PDF text
    tags TEXT[],
    version INTEGER DEFAULT 1,
    parent_document_id UUID REFERENCES document_storage(id),
    uploaded_at TIMESTAMP DEFAULT NOW()
);
```

### **Services to Implement**
```python
# Required new services
class DocumentStorageService:  # MinIO integration
class DocumentClassificationService:  # AI classification  
class DocumentProcessingService:  # OCR, text extraction
class DocumentSearchService:  # Elasticsearch integration
```

---

## ⚡ DEVELOPMENT COMMANDS

### **Start Development Environment**
```bash
# Backend
docker-compose up -d  # Starts PostgreSQL, Redis
python app/main.py    # Starts FastAPI server on :8000

# Frontend  
cd frontend
npm run dev          # Starts React dev server on :5173

# Database Migration
alembic upgrade head
```

### **Testing Commands**
```bash
pytest app/tests/                    # Run all tests
pytest app/tests/core/ -v           # Core tests with verbose
pytest app/tests/integration/ -k "patient"  # Specific integration tests
```

### **PowerShell Scripts Available**
```powershell
./scripts/powershell/Test-Authentication.ps1  # Test auth flow
./scripts/powershell/test_create_patient.ps1   # Test patient creation
./scripts/powershell/start_services.ps1        # Start all services
```

---

## 🔍 DEBUGGING CHECKLIST

### **When Endpoints Fail (500 errors)**
1. Check database enum values match code enums
2. Verify all required foreign key relationships exist  
3. Check encryption service is properly initialized
4. Verify audit logging doesn't have circular dependencies
5. Check database connection and session handling

### **When Authentication Fails**
1. Verify JWT token format (RS256, not HS256)
2. Check user exists in database with correct role
3. Verify rate limiting isn't blocking requests
4. Check CORS configuration for frontend

### **When Database Operations Fail**
1. Check database migrations are up to date (`alembic upgrade head`)
2. Verify soft delete filters (`soft_deleted_at.is_(None)`)
3. Check UUID format validation
4. Verify PHI encryption/decryption is working

---

## 📞 CRITICAL CONTACTS & RESOURCES

### **External APIs**
- **IRIS API**: Production integration available, OAuth2/HMAC auth
- **Frontend**: React TypeScript with Material-UI on port 5173
- **Database**: PostgreSQL with connection pooling

### **Environment Variables Required**
```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/db
JWT_SECRET_KEY=your-rs256-private-key
ENCRYPTION_KEY=your-aes-256-key  
REDIS_URL=redis://localhost:6379
IRIS_API_BASE_URL=your-iris-api-url
```

---

## 🎯 IMMEDIATE NEXT STEPS

1. **Fix Clinical Documents Endpoint** - Currently returning 500 error
2. **Implement MinIO Storage Service** - For secure file storage  
3. **Add Document Upload Interface** - React drag-drop component
4. **Create Document Classification** - AI-powered document categorization
5. **Implement Document Search** - Full-text search capabilities

**Priority**: Start with fixing the failing clinical documents endpoint, then implement MinIO storage service.

---

**⚠️ REMEMBER**: This system is production-grade with SOC2/HIPAA compliance. NEVER compromise on security, encryption, or audit logging. Always test thoroughly before deployment.