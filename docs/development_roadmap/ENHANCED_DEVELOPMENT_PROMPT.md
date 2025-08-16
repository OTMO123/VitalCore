# Enhanced Development Prompt for IRIS API Integration System

## 🎯 System Context & Current State

### **Project Overview**
You are working on the **IRIS API Integration System** - a healthcare-focused backend application with enterprise-grade security and compliance features. This system handles Protected Health Information (PHI) and must comply with SOC2 Type 2, HIPAA, and GDPR regulations.

### **Current Architecture Status**
- ✅ **Core Security Foundation**: JWT authentication, PHI encryption, immutable audit logging
- ✅ **Compliance Framework**: SOC2/HIPAA/GDPR basic implementation (91% complete)
- ✅ **Modular Monolith**: Event-driven architecture with DDD patterns
- ✅ **Test Infrastructure**: Comprehensive pytest framework with fixtures
- ✅ **Production Ready**: Docker deployment, security middleware stack

### **Technology Stack**
- **Backend**: FastAPI 0.104+ (Python 3.11+), PostgreSQL 15+, Redis 7+
- **Security**: JWT RS256, AES-256-GCM encryption, RBAC authorization
- **Testing**: Pytest with async support, comprehensive test fixtures
- **Frontend**: React 18+ TypeScript, Vite, Shadcn/ui, Redux Toolkit
- **DevOps**: Docker, Alembic migrations, structured logging

## 🏗️ Development Principles & Standards

### **SOLID Principles Implementation**
1. **Single Responsibility**: Each module/class has one reason to change
2. **Open/Closed**: Extensible through interfaces, closed for modification
3. **Liskov Substitution**: Derived classes must be substitutable for base classes
4. **Interface Segregation**: Clients shouldn't depend on unused interfaces
5. **Dependency Inversion**: Depend on abstractions, not concretions

### **Test-Driven Development (TDD)**
1. **Red**: Write failing test first
2. **Green**: Write minimal code to pass test
3. **Refactor**: Improve code while keeping tests green
4. **Cycle**: Repeat for each feature/requirement

### **Domain-Driven Design (DDD)**
- **Bounded Contexts**: Healthcare Records, Audit Logging, Authentication, Document Management
- **Entities**: User, Patient, AuditLog, Document with rich domain logic
- **Value Objects**: Immutable objects (Email, EncryptedField, AuditHash)
- **Aggregates**: Consistency boundaries (Patient + Records, User + Sessions)
- **Services**: Domain services for complex business logic
- **Repositories**: Data access abstraction layer

### **Security-First Development**
- **Defense in Depth**: Multiple security layers
- **Principle of Least Privilege**: Minimal required permissions
- **Zero Trust**: Verify every request, encrypt everything
- **Fail Secure**: Secure defaults, fail closed
- **Audit Everything**: Complete audit trail for compliance

### **Compliance-Driven Development**
- **SOC2 Type 2**: Security, availability, processing integrity controls
- **HIPAA**: Administrative, physical, technical safeguards
- **GDPR**: Data protection by design, privacy by default

## 📋 Development Workflow Requirements

### **Code Quality Standards**
```python
# Example: SOLID compliance with type hints and comprehensive testing
from typing import Protocol, AsyncGenerator
from abc import ABC, abstractmethod

class AuditLogRepository(Protocol):
    """Interface segregation - specific audit operations"""
    async def create_log(self, event: AuditEvent) -> str: ...
    async def verify_integrity(self, start_id: str, end_id: str) -> bool: ...

class SecurityEventHandler(ABC):
    """Open/closed principle - extensible event handling"""
    @abstractmethod
    async def handle(self, event: SecurityEvent) -> None: ...

@pytest.mark.asyncio
async def test_audit_log_creation_with_integrity():
    """TDD: Test behavior first, then implementation"""
    # Arrange
    repository = MockAuditRepository()
    event = create_test_security_event()
    
    # Act
    log_id = await repository.create_log(event)
    
    # Assert
    assert log_id is not None
    assert await repository.verify_integrity("genesis", log_id)
```

### **Security Testing Requirements**
```python
@pytest.mark.security
@pytest.mark.hipaa
async def test_phi_access_requires_valid_authorization():
    """Security-first: Test access controls before implementation"""
    # Test unauthorized access fails
    with pytest.raises(HTTPException) as exc:
        await patient_service.get_phi_data(patient_id, invalid_token)
    assert exc.value.status_code == 401
    
    # Test authorized access succeeds with audit
    result = await patient_service.get_phi_data(patient_id, valid_token)
    assert result.data is not None
    assert audit_was_logged(patient_id, user_id, "PHI_ACCESSED")
```

### **Compliance Testing Requirements**
```python
@pytest.mark.compliance
@pytest.mark.soc2
class TestSOC2Compliance:
    """Compliance verification through automated testing"""
    
    async def test_access_control_cc6_1(self):
        """SOC2 CC6.1 - Logical access controls"""
        # Test role-based access control
        assert await verify_rbac_enforcement()
    
    async def test_audit_controls_cc6_7(self):
        """SOC2 CC6.7 - System monitoring"""
        # Test comprehensive audit logging
        assert await verify_audit_completeness()
```

## 🚀 Development Implementation Approach

### **Feature Development Cycle**
1. **Requirements Analysis**: Define business requirements with compliance context
2. **Test Design**: Write comprehensive test suite (unit, integration, security)
3. **Interface Design**: Define clean interfaces following SOLID principles
4. **Implementation**: Develop with security-first approach
5. **Integration**: Integrate with existing modules using DDD patterns
6. **Compliance Verification**: Validate against SOC2/HIPAA/GDPR requirements
7. **Performance Testing**: Ensure security doesn't compromise performance
8. **Documentation**: Update architecture and compliance documentation

### **Code Organization Patterns**
```
app/modules/{domain}/
├── __init__.py
├── domain/                     # Domain layer (DDD)
│   ├── entities.py            # Domain entities
│   ├── value_objects.py       # Immutable value objects
│   ├── services.py            # Domain services
│   └── events.py              # Domain events
├── application/               # Application layer
│   ├── services.py            # Application services
│   ├── commands.py            # Command handlers
│   ├── queries.py             # Query handlers
│   └── interfaces.py          # Application interfaces
├── infrastructure/            # Infrastructure layer
│   ├── repositories.py        # Data access implementation
│   ├── external_services.py   # External service clients
│   └── encryption.py          # Encryption implementation
├── presentation/              # Presentation layer
│   ├── router.py              # FastAPI routes
│   ├── schemas.py             # Pydantic models
│   └── dependencies.py        # FastAPI dependencies
└── tests/                     # Comprehensive tests
    ├── unit/                  # Unit tests
    ├── integration/           # Integration tests
    ├── security/              # Security tests
    └── compliance/            # Compliance tests
```

### **Error Handling Standards**
```python
class DomainException(Exception):
    """Base domain exception with compliance context"""
    def __init__(self, message: str, audit_context: dict = None):
        super().__init__(message)
        self.audit_context = audit_context or {}

class SecurityViolationError(DomainException):
    """Security violation with automatic incident response"""
    def __init__(self, violation_type: str, user_id: str, details: dict):
        super().__init__(f"Security violation: {violation_type}")
        self.violation_type = violation_type
        self.user_id = user_id
        self.details = details
        # Trigger automatic security incident response
        asyncio.create_task(self._trigger_security_response())
```

## 🔐 Security & Compliance Integration

### **Security-First Development Checklist**
- [ ] **Input Validation**: All inputs validated with Pydantic schemas
- [ ] **Authorization**: Every endpoint protected with appropriate RBAC
- [ ] **Encryption**: All PHI encrypted with AES-256-GCM
- [ ] **Audit Logging**: All actions logged with immutable audit trail
- [ ] **Rate Limiting**: DoS protection on all public endpoints
- [ ] **Security Headers**: Complete security header implementation
- [ ] **Error Handling**: No sensitive data in error responses
- [ ] **Dependency Security**: All dependencies scanned for vulnerabilities

### **Compliance Integration Patterns**
```python
@compliance_monitor(regulations=["HIPAA", "GDPR"])
@audit_phi_access
async def get_patient_record(
    patient_id: str,
    current_user: User = Depends(require_role("physician")),
    purpose: AccessPurpose = AccessPurpose.TREATMENT
) -> PatientRecord:
    """Example: Compliance-integrated endpoint"""
    # Automatic compliance validation
    await validate_phi_access_request(
        user=current_user,
        patient_id=patient_id,
        purpose=purpose,
        minimum_necessary=True
    )
    
    # Business logic with automatic audit
    record = await patient_repository.get_by_id(patient_id)
    
    # Automatic compliance event generation
    return record
```

## 🧪 Testing Strategy & Requirements

### **Testing Pyramid Implementation**
1. **Unit Tests (70%)**: Fast, isolated, comprehensive domain logic testing
2. **Integration Tests (20%)**: Module integration, database, external services
3. **E2E Tests (10%)**: Complete user workflows, security scenarios

### **Security Testing Requirements**
- **Authentication Testing**: Valid/invalid tokens, role escalation attempts
- **Authorization Testing**: RBAC enforcement, resource-level permissions
- **Encryption Testing**: PHI encryption/decryption, key rotation
- **Audit Testing**: Log integrity, tamper detection, completeness
- **Vulnerability Testing**: SQL injection, XSS, CSRF, input validation

### **Performance Testing with Security**
```python
@pytest.mark.performance
@pytest.mark.security
async def test_phi_encryption_performance():
    """Ensure security doesn't compromise performance"""
    timer = PerformanceTimer()
    
    with timer:
        encrypted_data = await encryption_service.encrypt_phi_batch(
            test_phi_data, 
            batch_size=1000
        )
    
    # Security requirement: <100ms per encryption
    assert timer.elapsed_ms < 100
    # Compliance requirement: All data encrypted
    assert all(is_encrypted(data) for data in encrypted_data)
```

## 📊 Development Metrics & KPIs

### **Code Quality Metrics**
- **Test Coverage**: >90% for security-critical code, >85% overall
- **Cyclomatic Complexity**: <10 per function/method
- **SOLID Compliance**: Measured through static analysis
- **Security Vulnerability Count**: Zero critical, <5 medium

### **Performance Metrics**
- **API Response Time**: <300ms for 95th percentile
- **Encryption Performance**: <100ms per PHI field
- **Audit Log Performance**: <10ms per log entry
- **Database Query Performance**: <50ms for complex queries

### **Compliance Metrics**
- **SOC2 Control Coverage**: 100% automated testing
- **HIPAA Safeguard Implementation**: 100% coverage
- **GDPR Rights Implementation**: All rights automated
- **Audit Coverage**: 100% of user actions logged

## 🔄 Continuous Integration Requirements

### **CI/CD Pipeline Stages**
1. **Code Quality**: Linting, type checking, complexity analysis
2. **Security Scanning**: Dependency scan, SAST, secret detection
3. **Unit Testing**: Fast feedback on business logic
4. **Integration Testing**: Database, external services, event bus
5. **Security Testing**: RBAC, encryption, audit integrity
6. **Compliance Testing**: Automated regulation compliance checks
7. **Performance Testing**: Security performance validation
8. **Documentation**: Auto-update architecture diagrams

### **Deployment Requirements**
- **Zero-Downtime Deployment**: Rolling updates with health checks
- **Database Migrations**: Automated, reversible migrations
- **Security Configuration**: Automated security hardening
- **Compliance Validation**: Pre-deployment compliance checks
- **Monitoring Setup**: Automatic monitoring configuration

## 💡 Innovation & Future-Proofing

### **Emerging Technology Integration**
- **AI/ML Security**: Automated threat detection, anomaly detection
- **Zero-Trust Architecture**: Service mesh, micro-segmentation
- **Quantum-Safe Cryptography**: Future-proof encryption algorithms
- **Federated Identity**: SSO integration, identity federation

### **Scalability Considerations**
- **Microservices Migration**: Gradual decomposition strategy
- **Event Sourcing**: Complete audit trail with event sourcing
- **CQRS**: Read/write separation for performance
- **Multi-Tenant Architecture**: Secure tenant isolation

---

## 🎯 Development Execution Prompt

**When developing new features, always:**

1. **Start with Tests**: Write failing tests that define expected behavior
2. **Design Interfaces**: Create clean abstractions following SOLID principles
3. **Implement Security**: Security controls are not optional, they're requirements
4. **Validate Compliance**: Every feature must pass compliance validation
5. **Measure Performance**: Security must not compromise user experience
6. **Document Decisions**: Architecture decisions have compliance implications
7. **Automate Everything**: Manual processes are compliance risks

**Remember**: This is a healthcare system handling PHI. Security, privacy, and compliance are not afterthoughts—they're core functional requirements that drive every design decision.

**Code with the mindset**: "How will this be audited? How could this be attacked? How does this protect patient privacy?"

---

**Document Version:** 1.0
**Last Updated:** [Current Date]
**Scope:** Complete development guidance for healthcare compliance
**Classification:** Internal Development Guidelines