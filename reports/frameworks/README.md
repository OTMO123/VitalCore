# Frameworks Used - Clinical Workflows Restoration

## Framework Overview

This report documents all technical frameworks, methodologies, and tools employed during the successful clinical workflows restoration process.

## 🔧 Technical Frameworks

### FastAPI Framework
- **Purpose**: Web API framework for healthcare endpoints
- **Version**: Latest stable
- **Usage**: Clinical workflows REST API implementation
- **Benefits**: Automatic OpenAPI documentation, type validation, async support

### SQLAlchemy ORM
- **Purpose**: Database relationship management
- **Usage**: Patient-ClinicalWorkflow relationships
- **Implementation**: Declarative model definitions with proper foreign keys

### Docker & Docker Compose
- **Purpose**: Containerized microservices architecture
- **Services**: PostgreSQL, Redis, MinIO, FastAPI app
- **Usage**: Complete development and production environment

### PostgreSQL Database
- **Purpose**: Primary data storage with enterprise features
- **Usage**: Healthcare records, clinical workflows, audit logs
- **Features**: Row-level security, encryption, compliance

## 🎯 Troubleshooting Frameworks

### 5 Whys Methodology
- **Application**: Root cause analysis for 404 errors
- **Process**: Systematic questioning to identify true causes
- **Tools**: Diagnostic PowerShell scripts for evidence gathering

### Domain-Driven Design (DDD)
- **Implementation**: Bounded contexts for healthcare modules
- **Modules**: Auth, Clinical Workflows, Healthcare Records, Audit
- **Benefits**: Clear separation of concerns, maintainable architecture

### Event-Driven Architecture
- **Framework**: Custom event bus with PostgreSQL persistence
- **Usage**: Cross-module communication and audit logging
- **Compliance**: SOC2 Type II audit trail requirements

## 🔒 Security & Compliance Frameworks

### SOC2 Type II Compliance
- **Implementation**: Immutable audit logging with cryptographic integrity
- **Monitoring**: Security event tracking and compliance reporting
- **Controls**: Access controls, data classification, audit trails

### HIPAA Compliance
- **Implementation**: PHI/PII encryption with AES-256-GCM
- **Features**: Row-level security, access logging, data minimization
- **Audit**: Comprehensive PHI access tracking

### FHIR R4 Healthcare Standard
- **Purpose**: Healthcare data interoperability
- **Implementation**: FHIR-compliant patient data structures
- **Benefits**: Standard healthcare data exchange formats

---

*Framework documentation for enterprise healthcare system restoration*