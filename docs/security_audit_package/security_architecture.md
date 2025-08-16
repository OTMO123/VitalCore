# Security Architecture - IRIS API Integration System

## Executive Summary

The IRIS API Integration System implements a comprehensive security architecture designed for healthcare environments with strict compliance requirements. The system provides enterprise-grade security controls, end-to-end encryption, immutable audit trails, and automated compliance monitoring.

## 🏗️ Architecture Overview

### **System Components**
```
┌─────────────────────────────────────────────────────────────────┐
│                    IRIS API Integration System                  │
├─────────────────────────────────────────────────────────────────┤
│  Frontend (React/TypeScript)                                   │
│  ├─ Authentication UI                                           │
│  ├─ Role-based Dashboards                                       │
│  ├─ Secure API Communication                                    │
│  └─ Real-time Audit Monitoring                                  │
├─────────────────────────────────────────────────────────────────┤
│  API Gateway (FastAPI)                                         │
│  ├─ Security Headers Middleware                                 │
│  ├─ Rate Limiting                                              │
│  ├─ JWT Token Validation                                        │
│  ├─ PHI Audit Middleware                                        │
│  └─ CORS Protection                                             │
├─────────────────────────────────────────────────────────────────┤
│  Business Logic Layer                                          │
│  ├─ Authentication Service                                      │
│  ├─ Authorization Service (RBAC)                               │
│  ├─ PHI Encryption Service                                      │
│  ├─ Audit Logging Service                                       │
│  └─ Compliance Monitoring                                       │
├─────────────────────────────────────────────────────────────────┤
│  Data Layer                                                    │
│  ├─ PostgreSQL (Encrypted at Rest)                             │
│  ├─ Redis (Session Management)                                  │
│  ├─ Audit Log Storage (Immutable)                               │
│  └─ Backup Systems                                              │
└─────────────────────────────────────────────────────────────────┘
```

### **Security Layers**

#### **1. Network Security**
- **HTTPS Enforcement**: All communications encrypted with TLS 1.3
- **CORS Protection**: Strict origin validation
- **Rate Limiting**: DoS protection with configurable thresholds
- **IP Whitelisting**: Configurable IP access controls

#### **2. Authentication & Authorization**
- **JWT with RS256**: Asymmetric signing for enhanced security
- **Short-lived Tokens**: 15-minute access tokens, 7-day refresh tokens
- **Role-Based Access Control**: Hierarchical permission system
- **Session Management**: Secure session handling with Redis

#### **3. Data Protection**
- **PHI Encryption**: AES-256-GCM with field-specific keys
- **Encryption at Rest**: Database-level encryption
- **Encryption in Transit**: TLS 1.3 for all communications
- **Key Management**: Secure key derivation and rotation

#### **4. Audit & Compliance**
- **Immutable Audit Trails**: Blockchain-style hash chaining
- **Real-time Monitoring**: Automated compliance violations detection
- **Comprehensive Logging**: All user actions and system events
- **Audit Log Integrity**: Cryptographic tamper detection

## 🔐 Security Controls Implementation

### **Authentication System**

**Location:** `app/core/security.py`

```python
class SecurityManager:
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create JWT with RS256 signing and security claims"""
        # RS256 asymmetric signing
        # Short-lived tokens (15 minutes)
        # Unique JTI for replay protection
        # Comprehensive security claims
```

**Key Features:**
- **Asymmetric Signing**: RS256 algorithm for enhanced security
- **Token Blacklisting**: JTI-based token revocation
- **Failed Login Tracking**: Brute-force protection
- **Account Lockout**: Automated lockout after failed attempts

### **PHI Encryption Service**

**Location:** `app/core/security.py:469`

```python
class EncryptionService:
    async def encrypt(self, data: str, context: Dict[str, Any]) -> str:
        """AES-256-GCM with context-aware field-level encryption"""
        # Field-specific key derivation
        # AES-256-GCM authenticated encryption
        # Integrity checksums
        # Context-aware encryption
```

**Key Features:**
- **AES-256-GCM**: Authenticated encryption with integrity
- **Field-Level Encryption**: Context-aware encryption keys
- **Integrity Verification**: Cryptographic checksums
- **Key Derivation**: PBKDF2 with salt for unique keys

### **Audit Logging System**

**Location:** `app/core/audit_logger.py`

```python
class ImmutableAuditLogger:
    async def log_event(self, event_type: AuditEventType, message: str) -> str:
        """Immutable audit logging with hash chaining"""
        # Blockchain-style hash chaining
        # Tamper detection
        # Comprehensive event details
        # Integrity verification
```

**Key Features:**
- **Hash Chaining**: Blockchain-style integrity verification
- **Tamper Detection**: Cryptographic proof of immutability
- **Event Classification**: Comprehensive event categorization
- **Retention Policies**: Automated data lifecycle management

### **Access Control Matrix**

**Location:** `app/core/security.py:389`

```python
def require_role(required_role: str):
    """Hierarchical role-based access control"""
    # Role hierarchy validation
    # Permission inheritance
    # Context-aware access control
```

**Role Hierarchy:**
- **Super Admin**: Full system access
- **Admin**: Administrative functions
- **Physician**: Patient data access
- **Nurse**: Limited patient data access
- **User**: Basic system access

## 🛡️ Security Middleware Stack

### **Security Headers Middleware**

**Location:** `app/core/security_headers.py`

```python
class SecurityHeadersMiddleware:
    """Comprehensive security headers implementation"""
    # Content Security Policy (CSP)
    # HTTP Strict Transport Security (HSTS)
    # X-Frame-Options
    # X-Content-Type-Options
    # X-XSS-Protection
```

### **PHI Audit Middleware**

**Location:** `app/core/phi_audit_middleware.py`

```python
class PHIAuditMiddleware:
    """HIPAA-compliant PHI access auditing"""
    # Automatic PHI detection
    # Access logging
    # Consent validation
    # Audit trail generation
```

### **Rate Limiting**

**Location:** `app/core/security.py:424`

```python
class RateLimiter:
    """In-memory rate limiting for API endpoints"""
    # Configurable rate limits
    # Client-based limiting
    # Distributed rate limiting support
```

## 🔒 Cryptographic Implementation

### **Key Management**

**Key Derivation:**
- **PBKDF2-HMAC-SHA256**: 100,000 iterations
- **Field-Specific Keys**: Context-aware key generation
- **Salt Management**: Unique salts per encryption context

**Key Rotation:**
- **Automated Rotation**: Scheduled key rotation
- **Backward Compatibility**: Support for legacy encrypted data
- **Re-encryption**: Seamless data re-encryption

### **Encryption Algorithms**

**Symmetric Encryption:**
- **Algorithm**: AES-256-GCM
- **Key Size**: 256-bit keys
- **Nonce**: 96-bit random nonces
- **Authentication**: Authenticated encryption

**Asymmetric Encryption:**
- **Algorithm**: RSA-2048 for JWT signing
- **Key Management**: Secure key generation and storage
- **Signature Verification**: RS256 algorithm

### **Integrity Verification**

**Audit Log Integrity:**
- **Hash Algorithm**: SHA-256
- **Chain Structure**: Previous hash + current data
- **Tamper Detection**: Cryptographic verification

**Data Integrity:**
- **Checksums**: SHA-256 checksums for encrypted data
- **Verification**: Automatic integrity checks
- **Corruption Detection**: Real-time integrity monitoring

## 🚨 Security Monitoring

### **Real-time Security Monitoring**

**Location:** `app/modules/audit_logger/service.py:190`

```python
class ComplianceMonitoringHandler:
    """Real-time compliance monitoring and alerting"""
    # Failed login threshold monitoring
    # Privileged access pattern detection
    # Data export monitoring
    # Suspicious activity detection
```

### **Security Event Detection**

**Monitored Events:**
- **Failed Login Attempts**: Brute-force detection
- **Privileged Access**: Unusual admin activity
- **Data Export**: Large data export monitoring
- **Security Violations**: Automated violation detection

### **Alerting System**

**Alert Types:**
- **Critical**: Security breaches, system compromises
- **High**: Failed login thresholds, privilege escalations
- **Medium**: Unusual access patterns, compliance violations
- **Low**: Information events, routine activities

## 📊 Compliance Integration

### **SOC2 Type 2 Controls**

**Security Controls:**
- **CC6.1**: Logical access controls
- **CC6.2**: Authentication and authorization
- **CC6.3**: System access management
- **CC6.6**: Vulnerability management

**Availability Controls:**
- **A1.1**: System availability monitoring
- **A1.2**: Capacity management
- **A1.3**: System backup and recovery

### **HIPAA Controls**

**Administrative Safeguards:**
- **§164.308(a)(1)**: Security management process
- **§164.308(a)(3)**: Assigned security responsibility
- **§164.308(a)(4)**: Information workforce training

**Physical Safeguards:**
- **§164.310(a)(1)**: Facility access controls
- **§164.310(d)(1)**: Device and media controls

**Technical Safeguards:**
- **§164.312(a)(1)**: Access control
- **§164.312(c)(1)**: Integrity controls
- **§164.312(d)**: Person or entity authentication
- **§164.312(e)(1)**: Transmission security

### **GDPR Controls**

**Data Protection:**
- **Article 25**: Data protection by design
- **Article 30**: Records of processing activities
- **Article 32**: Security of processing
- **Article 35**: Data protection impact assessment

## 🔧 Security Configuration

### **Environment Security**

**Development:**
- **Debug Mode**: Enabled with enhanced logging
- **CORS**: Permissive for development
- **HTTPS**: Optional for local development

**Production:**
- **Debug Mode**: Disabled
- **CORS**: Strict origin validation
- **HTTPS**: Enforced with HSTS
- **Security Headers**: Full security header stack

### **Database Security**

**Encryption:**
- **At Rest**: Database-level encryption
- **In Transit**: TLS-encrypted connections
- **Backup**: Encrypted backup storage

**Access Control:**
- **Connection Pooling**: Secure connection management
- **Query Parameterization**: SQL injection prevention
- **Privilege Separation**: Minimal database privileges

## 🚀 Deployment Security

### **Container Security**

**Docker Security:**
- **Non-root User**: Containers run as non-root
- **Resource Limits**: CPU and memory constraints
- **Network Isolation**: Secure container networking
- **Image Scanning**: Security vulnerability scanning

### **Infrastructure Security**

**Network Security:**
- **Firewall Rules**: Strict ingress/egress controls
- **VPC Isolation**: Network segmentation
- **Load Balancer**: SSL termination and health checks

**Secret Management:**
- **Environment Variables**: Secure secret injection
- **Key Rotation**: Automated key rotation
- **Access Control**: Least privilege principle

---

**Document Version:** 1.0
**Last Updated:** [Current Date]
**Review Status:** Ready for Security Audit
**Classification:** Confidential - Security Documentation