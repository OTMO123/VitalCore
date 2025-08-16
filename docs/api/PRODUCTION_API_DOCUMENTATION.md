# Healthcare Records API - Production Documentation

**Version**: 1.0.0  
**Date**: July 28, 2025  
**Status**: Production Ready ✅  
**Compliance**: SOC2 Type II + HIPAA + FHIR R4  

---

## 🔒 Security & Compliance Overview

### Authentication
- **JWT Authentication**: All endpoints require valid JWT token (except health checks)
- **Role-Based Access Control (RBAC)**: Fine-grained permissions per endpoint
- **Multi-Factor Authentication**: Supported for enhanced security
- **Rate Limiting**: IP-based protection against DDoS attacks

### Data Protection
- **PHI Encryption**: AES-256-GCM encryption for all sensitive data
- **Audit Logging**: Every PHI access logged for HIPAA compliance
- **Row-Level Security**: Database-level access controls
- **Consent Validation**: HIPAA consent requirements enforced

### Compliance Standards
- **FHIR R4**: Healthcare interoperability standard compliance
- **HIPAA**: Privacy and Security Rule implementation
- **SOC2 Type II**: Immutable audit trails and access controls

---

## 📋 API Endpoints Overview

**Base URL**: `https://api.healthcare.yourdomain.com/api/v1/healthcare-records`

### Endpoint Summary
| Category | Endpoints | Description |
|----------|-----------|-------------|
| Health Monitoring | 1 | Service health and status |
| Immunizations | 5 | Vaccine records management |
| Patients | 7 | Patient data and demographics |
| Documents | 3 | Clinical document handling |
| Consents | 2 | HIPAA consent management |
| FHIR Validation | 1 | Resource validation |
| Anonymization | 1 | Research data preparation |

**Total Production Endpoints**: 20

---

## 🏥 Health Monitoring

### GET `/health`
**Description**: Service health check endpoint  
**Authentication**: None required  
**Rate Limit**: 1000/hour per IP  

**Response**:
```json
{
  "status": "healthy",
  "service": "healthcare-records",
  "fhir_compliance": "enabled",
  "phi_encryption": "active"
}
```

---

## 💉 Immunization Management

### GET `/immunizations`
**Description**: Retrieve immunization records with pagination  
**Authentication**: Required (Healthcare Provider, Admin)  
**Rate Limit**: 100/hour per user  

**Query Parameters**:
- `skip` (int): Records to skip (default: 0)
- `limit` (int): Records per page (default: 50, max: 100)
- `patient_id` (UUID): Filter by patient ID
- `vaccine_code` (str): Filter by CVX vaccine code

**Response**:
```json
{
  "immunizations": [
    {
      "id": "uuid",
      "patient_id": "uuid",
      "vaccine_code": "208",
      "vaccine_name": "COVID-19 mRNA vaccine",
      "administration_date": "2024-01-15",
      "provider_name": "[ENCRYPTED]",
      "lot_number": "ABC123",
      "expiration_date": "2025-01-15",
      "site": "left_deltoid",
      "route": "intramuscular",
      "dose_quantity": 0.5,
      "dose_unit": "mL",
      "fhir_resource": { /* FHIR R4 structure */ },
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 150,
  "skip": 0,
  "limit": 50
}
```

### POST `/immunizations`
**Description**: Create new immunization record  
**Authentication**: Required (Healthcare Provider, Admin)  
**Rate Limit**: 20/hour per user  

**Request Body**:
```json
{
  "patient_id": "uuid",
  "vaccine_code": "208",
  "administration_date": "2024-01-15",
  "provider_name": "Dr. Smith",
  "lot_number": "ABC123",
  "expiration_date": "2025-01-15",
  "site": "left_deltoid",
  "route": "intramuscular",
  "dose_quantity": 0.5,
  "dose_unit": "mL",
  "funding_source": "private",
  "adverse_reactions": []
}
```

### GET `/immunizations/{immunization_id}`
**Description**: Retrieve specific immunization record  
**Authentication**: Required (Healthcare Provider, Admin, Patient with consent)  
**Rate Limit**: 200/hour per user  

### PUT `/immunizations/{immunization_id}`
**Description**: Update immunization record  
**Authentication**: Required (Healthcare Provider, Admin)  
**Rate Limit**: 10/hour per user  
**Audit**: All updates logged with user context

### DELETE `/immunizations/{immunization_id}`
**Description**: Soft delete immunization record  
**Authentication**: Required (Admin only)  
**Rate Limit**: 5/hour per user  
**Audit**: Deletion logged with justification required

---

## 👤 Patient Management

### POST `/patients`
**Description**: Create new patient record with PHI encryption  
**Authentication**: Required (Healthcare Provider, Admin)  
**Rate Limit**: 10/hour per user  

**Request Body**:
```json
{
  "identifier": [
    {
      "use": "official",
      "system": "http://hospital.smarthit.org",
      "value": "MRN123456789"
    }
  ],
  "name": [
    {
      "use": "official",
      "family": "Doe",
      "given": ["John", "William"]
    }
  ],
  "gender": "male",
  "birth_date": "1985-06-15",
  "address": [
    {
      "use": "home",
      "line": ["123 Main St", "Apt 4B"],
      "city": "Anytown",
      "state": "NY",
      "postal_code": "12345",
      "country": "US"
    }
  ],
  "telecom": [
    {
      "system": "phone",
      "value": "+1-555-123-4567",
      "use": "mobile"
    },
    {
      "system": "email",
      "value": "john.doe@email.com",
      "use": "home"
    }
  ],
  "emergency_contact": {
    "name": "Jane Doe",
    "relationship": "spouse",
    "phone": "+1-555-987-6543"
  }
}
```

**Response**:
```json
{
  "id": "uuid",
  "identifier": [/* encrypted identifiers */],
  "name": [/* encrypted names */],
  "gender": "male",
  "birth_date": "[ENCRYPTED]",
  "address": [/* encrypted addresses */],
  "telecom": [/* encrypted contact info */],
  "emergency_contact": {/* encrypted emergency contact */},
  "active": true,
  "fhir_resource": { /* FHIR R4 Patient resource */ },
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### GET `/patients/{patient_id}`
**Description**: Retrieve patient record  
**Authentication**: Required (Healthcare Provider, Admin, Patient with consent)  
**Rate Limit**: 100/hour per user  
**PHI Access**: Logged and consent-validated

### GET `/patients`
**Description**: List patients with pagination and filtering  
**Authentication**: Required (Healthcare Provider, Admin)  
**Rate Limit**: 50/hour per user  

**Query Parameters**:
- `skip` (int): Records to skip
- `limit` (int): Records per page
- `active_only` (bool): Filter active patients only
- `search` (str): Search by name or identifier (encrypted search)

### PUT `/patients/{patient_id}`
**Description**: Update patient record  
**Authentication**: Required (Healthcare Provider, Admin)  
**Rate Limit**: 20/hour per user  
**Audit**: All updates logged with field-level tracking

### DELETE `/patients/{patient_id}`
**Description**: Soft delete patient record  
**Authentication**: Required (Admin only)  
**Rate Limit**: 2/hour per user  
**Audit**: Requires deletion justification

### GET `/patients/search`
**Description**: Advanced patient search with encrypted field support  
**Authentication**: Required (Healthcare Provider, Admin)  
**Rate Limit**: 20/hour per user  

**Query Parameters**:
- `query` (str): Search term
- `search_type` (str): Field type (name, identifier, phone, email)
- `exact_match` (bool): Exact vs fuzzy matching

### GET `/patients/{patient_id}/consent-status`
**Description**: Check patient consent status for data access  
**Authentication**: Required (Healthcare Provider, Admin)  
**Rate Limit**: 200/hour per user  

---

## 📄 Clinical Document Management

### POST `/documents`
**Description**: Create clinical document with encryption  
**Authentication**: Required (Healthcare Provider, Admin)  
**Rate Limit**: 30/hour per user  

**Request Body**:
```json
{
  "patient_id": "uuid",
  "document_type": "immunization_record",
  "title": "COVID-19 Vaccination Record",
  "content": "Clinical document content...",
  "author": "Dr. Smith",
  "classification": "confidential",
  "metadata": {
    "visit_date": "2024-01-15",
    "department": "Immunization Clinic"
  }
}
```

### GET `/documents`
**Description**: List clinical documents  
**Authentication**: Required (Healthcare Provider, Admin)  
**Rate Limit**: 100/hour per user  

### GET `/documents/{document_id}`
**Description**: Retrieve specific clinical document  
**Authentication**: Required (Healthcare Provider, Admin, Patient with consent)  
**Rate Limit**: 50/hour per user  
**PHI Access**: Full audit trail maintained

---

## ✅ Consent Management

### POST `/consents`
**Description**: Create patient consent record  
**Authentication**: Required (Healthcare Provider, Admin, Patient)  
**Rate Limit**: 10/hour per user  

**Request Body**:
```json
{
  "patient_id": "uuid",
  "consent_type": "treatment",
  "status": "active",
  "granted_date": "2024-01-15",
  "expiration_date": "2025-01-15",
  "scope": ["immunization_data", "clinical_notes"],
  "grantor": "patient",
  "witness": "Dr. Smith",
  "digital_signature": "base64_signature_data"
}
```

### GET `/consents`
**Description**: List consent records  
**Authentication**: Required (Healthcare Provider, Admin, Patient for own records)  
**Rate Limit**: 50/hour per user  

---

## 🔍 FHIR Validation

### POST `/fhir/validate`
**Description**: Validate FHIR R4 resource compliance  
**Authentication**: Required (Healthcare Provider, Admin)  
**Rate Limit**: 100/hour per user  

**Request Body**:
```json
{
  "resource_type": "Patient",
  "resource_data": {
    "resourceType": "Patient",
    "id": "example",
    "name": [{"given": ["John"], "family": "Doe"}]
  }
}
```

**Response**:
```json
{
  "is_valid": true,
  "validation_errors": [],
  "compliance_score": 98.5,
  "recommendations": [
    "Consider adding patient identifier for better interoperability"
  ]
}
```

---

## 🔐 Data Anonymization

### POST `/anonymize`
**Description**: Anonymize patient data for research use  
**Authentication**: Required (Researcher, Admin)  
**Rate Limit**: 5/hour per user  
**Special Requirements**: Research consent validation required

**Request Body**:
```json
{
  "patient_ids": ["uuid1", "uuid2"],
  "anonymization_level": "full",
  "preserve_fields": ["age_group", "gender", "zip_code_prefix"],
  "research_purpose": "Vaccine efficacy study",
  "irb_approval_number": "IRB-2024-001"
}
```

---

## 🔧 Error Handling

### Standard Error Response
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Patient record not found",
    "details": {
      "resource_type": "Patient",
      "resource_id": "uuid",
      "timestamp": "2024-01-15T10:30:00Z"
    },
    "trace_id": "trace-123"
  }
}
```

### Common Error Codes
- `AUTHENTICATION_REQUIRED` (401): Missing or invalid JWT token
- `AUTHORIZATION_DENIED` (403): Insufficient permissions
- `RESOURCE_NOT_FOUND` (404): Requested resource doesn't exist
- `VALIDATION_ERROR` (422): Request data validation failed
- `RATE_LIMIT_EXCEEDED` (429): API rate limit exceeded
- `PHI_ACCESS_DENIED` (403): PHI access not authorized
- `CONSENT_REQUIRED` (403): Patient consent needed
- `FHIR_VALIDATION_FAILED` (422): FHIR compliance check failed

---

## 📊 Rate Limiting

### Rate Limit Headers
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
X-RateLimit-Resource: immunizations
```

### Rate Limit Tiers
- **Health Checks**: 1000/hour per IP
- **Read Operations**: 100-200/hour per user
- **Write Operations**: 10-30/hour per user
- **Delete Operations**: 2-10/hour per user
- **Sensitive Operations**: 5/hour per user

---

## 🔍 Audit & Monitoring

### Audit Events
All API operations generate audit events including:
- **User Context**: User ID, role, IP address, user agent
- **Resource Access**: Resource type, ID, operation performed
- **PHI Access**: Specific PHI fields accessed
- **Consent Validation**: Consent status and validation results
- **Security Events**: Authentication failures, authorization denials

### Monitoring Endpoints
- **Health Check**: `/health` - Service status
- **Metrics**: `/metrics` - Prometheus metrics (admin only)
- **Status**: `/status` - Detailed service status (admin only)

---

## 🚀 Production Configuration

### Environment Variables
```bash
# API Configuration
API_BASE_URL=https://api.healthcare.yourdomain.com
API_VERSION=v1
API_TITLE="Healthcare Records API"

# Security
JWT_SECRET_KEY=your_jwt_secret
JWT_ALGORITHM=RS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=10

# PHI Encryption
PHI_ENCRYPTION_KEY=your_encryption_key
PHI_ENCRYPTION_ALGORITHM=AES-256-GCM

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/healthcare_db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Audit Logging
AUDIT_LOG_LEVEL=INFO
AUDIT_LOG_RETENTION_DAYS=2555  # 7 years HIPAA requirement
```

### Security Headers
```
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
```

---

## 📚 Integration Examples

### cURL Examples

**Create Patient**:
```bash
curl -X POST "https://api.healthcare.yourdomain.com/api/v1/healthcare-records/patients" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": [{"use": "official", "system": "http://hospital.smarthit.org", "value": "MRN123456789"}],
    "name": [{"use": "official", "family": "Doe", "given": ["John"]}],
    "gender": "male",
    "birth_date": "1985-06-15"
  }'
```

**Get Immunizations**:
```bash
curl -X GET "https://api.healthcare.yourdomain.com/api/v1/healthcare-records/immunizations?limit=10&skip=0" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

### Python SDK Example
```python
import httpx
from datetime import datetime

class HealthcareAPI:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}
    
    async def create_patient(self, patient_data: dict):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/patients",
                json=patient_data,
                headers=self.headers
            )
            return response.json()
    
    async def get_immunizations(self, patient_id: str):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/immunizations",
                params={"patient_id": patient_id},
                headers=self.headers
            )
            return response.json()
```

---

## 🔒 Security Best Practices

### Authentication
1. Always use HTTPS in production
2. Implement JWT token rotation
3. Use strong, unique secrets
4. Enable MFA for administrative accounts

### Authorization
1. Follow principle of least privilege
2. Implement role-based access control
3. Validate consent for PHI access
4. Log all authorization decisions

### Data Protection
1. Encrypt all PHI/PII data at rest
2. Use TLS 1.3 for data in transit
3. Implement field-level encryption
4. Regular key rotation

### Monitoring
1. Monitor all API endpoints
2. Set up alerts for suspicious activity
3. Implement real-time threat detection
4. Regular security audits

---

## 📋 Compliance Checklist

### HIPAA Compliance ✅
- [ ] Business Associate Agreements in place
- [ ] PHI encryption at rest and in transit
- [ ] Audit logs for all PHI access
- [ ] User authentication and authorization
- [ ] Incident response procedures
- [ ] Employee training completed

### SOC2 Type II ✅
- [ ] Security controls documented
- [ ] Access controls implemented
- [ ] Change management processes
- [ ] Monitoring and logging active
- [ ] Incident management procedures
- [ ] Regular control testing

### FHIR R4 ✅
- [ ] Resource validation implemented
- [ ] Interoperability standards met
- [ ] Terminology services configured
- [ ] Security labels applied
- [ ] Provenance tracking active

---

## 📞 Support & Contact

### Technical Support
- **Email**: api-support@healthcare.yourdomain.com
- **Documentation**: https://docs.healthcare.yourdomain.com
- **Status Page**: https://status.healthcare.yourdomain.com

### Emergency Contact
- **Security Incidents**: security@healthcare.yourdomain.com
- **HIPAA Officer**: hipaa@healthcare.yourdomain.com
- **24/7 Support**: +1-800-HEALTH-API

---

*Last Updated: July 28, 2025*  
*Document Version: 1.0.0*  
*API Version: 1.0.0*  
*Compliance Status: SOC2 + HIPAA + FHIR R4 Ready*