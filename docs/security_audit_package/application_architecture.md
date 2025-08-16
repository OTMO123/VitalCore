# Application Architecture - IRIS API Integration System

## Overview

IRIS API Integration System is a healthcare-focused backend application built with modern security-first architecture. The system is designed as a modular monolith with event-driven patterns, implementing comprehensive security controls for healthcare data protection.

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        IRIS API Integration System                      │
├─────────────────────────────────────────────────────────────────────────┤
│                              Frontend Layer                             │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │ React/TypeScript Application (Port 3000)                           ││
│  │ ├─ Role-based Dashboards (Admin, Doctor, Patient)                  ││
│  │ ├─ Authentication UI (Login, Register, MFA)                        ││
│  │ ├─ Patient Management Interface                                     ││
│  │ ├─ Document Management System                                       ││
│  │ ├─ Audit Monitoring Dashboard                                       ││
│  │ ├─ Compliance Reporting Interface                                   ││
│  │ └─ Real-time Notifications                                          ││
│  └─────────────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────────────┤
│                              API Gateway Layer                          │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │ FastAPI Application (Port 8000)                                    ││
│  │ ├─ Security Headers Middleware                                      ││
│  │ ├─ CORS Middleware                                                  ││
│  │ ├─ PHI Audit Middleware                                             ││
│  │ ├─ Rate Limiting Middleware                                         ││
│  │ ├─ Authentication Middleware                                        ││
│  │ └─ Request/Response Logging                                         ││
│  └─────────────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────────────┤
│                           Business Logic Layer                          │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │ Modular Services Architecture                                       ││
│  │ ├─ Authentication Service (JWT, OAuth2)                            ││
│  │ ├─ Authorization Service (RBAC)                                     ││
│  │ ├─ Audit Logging Service (Immutable Logs)                          ││
│  │ ├─ PHI Encryption Service (AES-256-GCM)                            ││
│  │ ├─ Patient Management Service                                       ││
│  │ ├─ Document Management Service                                      ││
│  │ ├─ IRIS API Integration Service                                     ││
│  │ ├─ Compliance Monitoring Service                                    ││
│  │ ├─ Analytics Service                                                ││
│  │ └─ Notification Service                                             ││
│  └─────────────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────────────┤
│                           Event Processing Layer                        │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │ Advanced Event Bus System                                           ││
│  │ ├─ Event Publishers (Service Layer)                                 ││
│  │ ├─ Event Handlers (Audit, Compliance, Notifications)               ││
│  │ ├─ Event Routing (Type-based Routing)                              ││
│  │ ├─ Event Persistence (PostgreSQL)                                  ││
│  │ └─ Event Replay (Forensic Analysis)                                 ││
│  └─────────────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────────────┤
│                              Data Layer                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │ PostgreSQL Database (Primary Storage)                              ││
│  │ ├─ Users & Authentication                                           ││
│  │ ├─ Patient Records (Encrypted PHI)                                  ││
│  │ ├─ Audit Logs (Immutable Hash Chain)                               ││
│  │ ├─ Documents & Files                                                ││
│  │ ├─ Compliance Reports                                               ││
│  │ └─ System Configuration                                             ││
│  └─────────────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │ Redis Cache (Session & Background Tasks)                           ││
│  │ ├─ Session Management                                               ││
│  │ ├─ Token Blacklisting                                               ││
│  │ ├─ Rate Limiting Counters                                           ││
│  │ ├─ Celery Task Queue                                                ││
│  │ └─ Real-time Notifications                                          ││
│  └─────────────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────────────┤
│                           External Integrations                         │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │ IRIS API Integration                                                ││
│  │ ├─ FHIR R4 Compliance                                               ││
│  │ ├─ Healthcare Data Exchange                                         ││
│  │ ├─ Clinical Decision Support                                        ││
│  │ └─ Interoperability Standards                                       ││
│  └─────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
```

## 🔧 Technology Stack

### **Backend Stack**
- **Framework**: FastAPI 0.104+ (Python 3.11+)
- **Database**: PostgreSQL 15+ with asyncpg
- **Cache/Queue**: Redis 7+ with Celery
- **Authentication**: JWT with RS256 signing
- **Encryption**: AES-256-GCM for PHI data
- **ORM**: SQLAlchemy 2.0 with async support
- **Migrations**: Alembic for database versioning
- **Testing**: Pytest with async support
- **Logging**: Structlog for structured logging

### **Frontend Stack**
- **Framework**: React 18+ with TypeScript
- **Build Tool**: Vite for fast development
- **UI Components**: Shadcn/ui component library
- **Styling**: Tailwind CSS for responsive design
- **State Management**: Redux Toolkit with RTK Query
- **Routing**: React Router v6
- **Authentication**: JWT token management
- **Testing**: Jest and React Testing Library

### **DevOps & Infrastructure**
- **Containerization**: Docker with multi-stage builds
- **Orchestration**: Docker Compose for local development
- **Database Migrations**: Alembic versioning system
- **Environment Management**: Python-dotenv
- **Process Management**: Production-ready WSGI/ASGI

## 📁 Project Structure

```
2_scraper/
├── app/                           # Backend application
│   ├── __init__.py
│   ├── main.py                    # FastAPI application entry point
│   ├── core/                      # Core system components
│   │   ├── __init__.py
│   │   ├── config.py              # Configuration management
│   │   ├── database.py            # Database connection
│   │   ├── database_unified.py    # Unified database models
│   │   ├── security.py            # Security & encryption services
│   │   ├── audit_logger.py        # Immutable audit logging
│   │   ├── event_bus_advanced.py  # Event-driven architecture
│   │   ├── security_headers.py    # Security middleware
│   │   └── phi_audit_middleware.py # PHI access auditing
│   ├── modules/                   # Business logic modules
│   │   ├── __init__.py
│   │   ├── auth/                  # Authentication & authorization
│   │   │   ├── __init__.py
│   │   │   ├── router.py          # Auth endpoints
│   │   │   ├── service.py         # Auth business logic
│   │   │   └── schemas.py         # Auth data models
│   │   ├── audit_logger/          # Audit logging module
│   │   │   ├── __init__.py
│   │   │   ├── router.py          # Audit endpoints
│   │   │   ├── service.py         # Audit service
│   │   │   └── schemas.py         # Audit data models
│   │   ├── healthcare_records/    # Patient management
│   │   │   ├── __init__.py
│   │   │   ├── router.py          # Patient endpoints
│   │   │   ├── service.py         # Patient business logic
│   │   │   └── schemas.py         # Patient data models
│   │   ├── document_management/   # Document handling
│   │   │   ├── __init__.py
│   │   │   ├── router.py          # Document endpoints
│   │   │   ├── service.py         # Document processing
│   │   │   └── storage_backend.py # File storage
│   │   ├── iris_api/              # IRIS API integration
│   │   │   ├── __init__.py
│   │   │   ├── router.py          # IRIS endpoints
│   │   │   ├── service.py         # IRIS business logic
│   │   │   └── client.py          # IRIS API client
│   │   ├── dashboard/             # Dashboard services
│   │   │   ├── __init__.py
│   │   │   ├── router.py          # Dashboard endpoints
│   │   │   └── service.py         # Dashboard data
│   │   ├── analytics/             # Analytics services
│   │   │   ├── __init__.py
│   │   │   ├── router.py          # Analytics endpoints
│   │   │   └── service.py         # Analytics processing
│   │   └── risk_stratification/   # Risk assessment
│   │       ├── __init__.py
│   │       ├── router.py          # Risk endpoints
│   │       └── service.py         # Risk algorithms
│   ├── schemas/                   # Shared data models
│   │   ├── __init__.py
│   │   └── fhir_r4.py            # FHIR R4 schemas
│   ├── tests/                     # Test suite
│   │   ├── __init__.py
│   │   ├── conftest.py           # Test configuration
│   │   ├── core/                 # Core component tests
│   │   ├── integration/          # Integration tests
│   │   └── smoke/                # Smoke tests
│   └── utils/                     # Utility functions
│       └── __init__.py
├── frontend/                      # Frontend application
│   ├── src/
│   │   ├── components/            # React components
│   │   │   ├── auth/             # Authentication components
│   │   │   ├── dashboard/        # Dashboard components
│   │   │   ├── patient/          # Patient management
│   │   │   ├── audit/            # Audit monitoring
│   │   │   └── common/           # Shared components
│   │   ├── pages/                # Page components
│   │   │   ├── auth/             # Auth pages
│   │   │   ├── dashboard/        # Dashboard pages
│   │   │   ├── patients/         # Patient pages
│   │   │   └── audit/            # Audit pages
│   │   ├── services/             # API services
│   │   │   ├── api.ts            # API configuration
│   │   │   ├── auth.service.ts   # Auth service
│   │   │   ├── patient.service.ts # Patient service
│   │   │   └── audit.service.ts  # Audit service
│   │   ├── store/                # State management
│   │   │   ├── index.ts          # Store configuration
│   │   │   └── slices/           # Redux slices
│   │   ├── types/                # TypeScript types
│   │   │   ├── index.ts          # Common types
│   │   │   └── patient.ts        # Patient types
│   │   └── utils/                # Utility functions
│   ├── public/                   # Static assets
│   ├── package.json              # Dependencies
│   └── vite.config.ts            # Vite configuration
├── docs/                         # Documentation
│   ├── security_audit_package/   # Security documentation
│   ├── api/                      # API documentation
│   └── context/                  # Development context
├── alembic/                      # Database migrations
│   ├── versions/                 # Migration files
│   ├── env.py                    # Migration environment
│   └── script.py.mako            # Migration template
├── scripts/                      # Utility scripts
│   ├── setup/                    # Setup scripts
│   ├── test/                     # Test scripts
│   └── powershell/               # PowerShell scripts
├── data/                         # Data storage
│   ├── backups/                  # Database backups
│   ├── exports/                  # Data exports
│   └── seeds/                    # Seed data
├── requirements.txt              # Python dependencies
├── docker-compose.yml            # Docker configuration
├── Dockerfile                    # Container definition
├── CLAUDE.md                     # AI assistant context
└── README.md                     # Project documentation
```

## 🔐 Security Architecture

### **Authentication Flow**
```
Client Request → Security Headers → Rate Limiting → JWT Validation → Role Check → API Endpoint
      ↓              ↓                ↓              ↓             ↓           ↓
  HTTPS/TLS      CSP, HSTS       IP-based      RS256 Verify   RBAC Check   Business Logic
```

### **PHI Data Flow**
```
PHI Input → Validation → Classification → Encryption → Database Storage
    ↓           ↓            ↓              ↓             ↓
  Schemas   Data Types   AUTO_PHI_TAG   AES-256-GCM   Encrypted Fields
    ↓
Audit Log (PHI_ACCESSED event with hash chaining)
```

### **Event-Driven Architecture**
```
Service Action → Event Publisher → Event Bus → Event Handlers → Side Effects
      ↓              ↓              ↓           ↓              ↓
  User Login    AuditEvent      Type Router   AuditLogger   Immutable Log
  PHI Access    PHIEvent        Subscribers   Compliance    Alert System
  Security      SecurityEvent   Async Proc    Monitoring    Notification
```

## 🏥 Healthcare-Specific Features

### **FHIR R4 Compliance**
- **Patient Resource**: Complete patient demographics and identifiers
- **Observation Resource**: Clinical observations and measurements
- **Condition Resource**: Patient conditions and diagnoses
- **Medication Resource**: Medication information and prescriptions
- **Encounter Resource**: Healthcare encounters and visits

### **PHI Data Protection**
- **Field-Level Encryption**: Individual PHI fields encrypted separately
- **Context-Aware Keys**: Different encryption keys per field type
- **Audit Trail**: Complete access history for all PHI data
- **Consent Management**: Granular consent tracking and enforcement

### **Clinical Decision Support**
- **Risk Stratification**: Patient risk assessment algorithms
- **Population Health**: Aggregate health analytics
- **Quality Metrics**: Healthcare quality measurements
- **Reporting**: Regulatory reporting capabilities

## 🚀 Deployment Architecture

### **Development Environment**
```
Local Development:
├── Backend: FastAPI dev server (port 8000)
├── Frontend: Vite dev server (port 3000)
├── Database: PostgreSQL (port 5432)
├── Cache: Redis (port 6379)
└── Mock Services: WireMock for testing
```

### **Production Environment**
```
Production Deployment:
├── Load Balancer (HTTPS termination)
├── API Gateway (FastAPI + Gunicorn)
├── Frontend (Static files + CDN)
├── Database Cluster (PostgreSQL with replication)
├── Cache Cluster (Redis with clustering)
├── Message Queue (Celery workers)
└── Monitoring (Logging + Metrics)
```

### **Docker Configuration**
```dockerfile
# Multi-stage build for production
FROM python:3.11-slim as base
# Security hardening
FROM base as security
USER nobody
EXPOSE 8000
# Application layer
FROM security as app
COPY --from=build /app /app
CMD ["gunicorn", "app.main:app"]
```

## 📊 Performance Characteristics

### **Response Time Targets**
- **Authentication**: <100ms (JWT validation)
- **PHI Access**: <200ms (encryption/decryption)
- **Database Queries**: <50ms (optimized queries)
- **API Endpoints**: <300ms (business logic)
- **Audit Logging**: <10ms (async processing)

### **Scalability Features**
- **Async Processing**: FastAPI async/await throughout
- **Connection Pooling**: PostgreSQL connection pooling
- **Event-Driven**: Decoupled services via event bus
- **Caching**: Redis caching for frequent queries
- **Background Tasks**: Celery for heavy processing

### **Security Performance**
- **JWT Validation**: <5ms per request
- **PHI Encryption**: <10ms per field
- **Audit Logging**: <1ms per event
- **Rate Limiting**: <1ms per request
- **RBAC Check**: <2ms per request

## 🔍 Monitoring & Observability

### **Audit Logging**
- **Immutable Logs**: Blockchain-style hash chaining
- **Event Classification**: Comprehensive event taxonomy
- **Real-time Monitoring**: Continuous compliance monitoring
- **Forensic Analysis**: Complete audit trail reconstruction

### **Security Monitoring**
- **Failed Login Detection**: Brute force attack detection
- **Privilege Escalation**: Unauthorized access monitoring
- **Data Export Monitoring**: Large data export detection
- **Anomaly Detection**: Machine learning-based anomaly detection

### **Performance Monitoring**
- **Request Tracing**: Distributed tracing support
- **Metric Collection**: Application performance metrics
- **Health Checks**: Comprehensive health monitoring
- **Error Tracking**: Structured error logging and tracking

## 🧪 Testing Strategy

### **Test Categories**
- **Unit Tests**: Individual component testing
- **Integration Tests**: Service integration testing
- **Security Tests**: Security vulnerability testing
- **Compliance Tests**: Regulatory compliance testing
- **Performance Tests**: Load and stress testing

### **Test Coverage**
- **Code Coverage**: >90% test coverage target
- **Security Coverage**: 100% security function coverage
- **API Coverage**: 100% endpoint testing
- **Database Coverage**: 100% model testing
- **Frontend Coverage**: >85% component testing

---

**Document Version:** 1.0
**Last Updated:** [Current Date]
**Architecture Status:** Production Ready
**Classification:** Technical Architecture Documentation