# Context Map - Agent-Orchestrated Healthcare Platform

## 1. Введение

Данный документ описывает архитектурную карту контекстов (Context Map) для платформы оркестрации AI-агентов в сфере здравоохранения. Документ следует принципам Domain-Driven Design (DDD) и использует нотацию C4 Model для визуализации архитектуры.

**Цель документа**: Определить границы ответственности между модулями системы, их взаимодействие и точки интеграции для обеспечения высокой модульности, безопасности и соответствия требованиям SOC2/HIPAA.

**Связанные документы**: 
- `project_spec.yaml` - высокоуровневое описание проекта
- `threat_model.md` - модель угроз безопасности
- `database_schema.sql` - схема базы данных

## 2. Перечень Bounded Contexts

### 2.1 User & Access Management Context

**Ответственность**: Управление пользователями, аутентификация, авторизация, RBAC

**Основные агрегаты**:
- **User** (Aggregate Root)
  - UserId (VO)
  - Credentials (VO)
  - MFASettings (VO)
  - LoginHistory (Entity)
- **Role** (Aggregate Root)
  - RoleId (VO)
  - Permissions (VO)
  - HierarchicalStructure (VO)
- **Session** (Aggregate Root)
  - SessionToken (VO)
  - ExpiryPolicy (VO)

### 2.2 IRIS Integration Context

**Ответственность**: Интеграция с внешними медицинскими системами (IRIS API), управление иммунизационными записями

**Основные агрегаты**:
- **ImmunizationRecord** (Aggregate Root)
  - FHIR R4 Resource (VO)
  - PatientReference (VO)
  - VaccineCode (VO)
- **APIEndpoint** (Aggregate Root)
  - EndpointConfig (VO)
  - RateLimitPolicy (VO)
  - CircuitBreakerState (VO)
- **IntegrationCredentials** (Aggregate Root)
  - EncryptedCredentials (VO)
  - RotationSchedule (VO)

### 2.3 Audit & Compliance Context

**Ответственность**: SOC2/HIPAA-совместимое логирование, неизменяемый audit trail, compliance отчетность

**Основные агрегаты**:
- **AuditLog** (Aggregate Root)
  - LogEntry (VO) - immutable
  - HashChain (VO)
  - ComplianceTags (VO)
- **ComplianceReport** (Aggregate Root)
  - ReportPeriod (VO)
  - Metrics (VO)
  - Attestations (Entity)

### 2.4 Data Retention & Purge Context

**Ответственность**: Управление жизненным циклом данных, автоматическое удаление, legal holds

**Основные агрегаты**:
- **RetentionPolicy** (Aggregate Root)
  - RetentionRules (VO)
  - PurgeStrategy (VO)
- **PurgeExecution** (Aggregate Root)
  - ExecutionPlan (VO)
  - PurgeResults (VO)
- **RetentionOverride** (Aggregate Root)
  - OverrideReason (VO)
  - ApprovalWorkflow (Entity)

### 2.5 Healthcare Records Context

**Ответственность**: Управление PHI/PII данными пациентов, соответствие FHIR стандартам

**Основные агрегаты**:
- **Patient** (Aggregate Root)
  - EncryptedPHI (VO)
  - ConsentStatus (VO)
  - MedicalRecordNumber (VO)
- **ClinicalDocument** (Aggregate Root)
  - DocumentMetadata (VO)
  - EncryptedContent (VO)
  - AccessControl (VO)

### 2.6 Encryption & Security Context

**Ответственность**: Шифрование данных, управление ключами, криптографические операции

**Основные агрегаты**:
- **EncryptionKey** (Aggregate Root)
  - KeyMaterial (VO) - encrypted
  - KeyRotationPolicy (VO)
  - KeyUsageAudit (Entity)
- **EncryptedField** (Aggregate Root)
  - FieldRegistry (VO)
  - EncryptionMetadata (VO)

### 2.7 Event Processing Context

**Ответственность**: Асинхронная обработка событий, гарантии доставки, event sourcing

**Основные агрегаты**:
- **Event** (Aggregate Root)
  - EventPayload (VO)
  - EventMetadata (VO)
  - DeliveryGuarantee (VO)
- **EventSubscription** (Aggregate Root)
  - SubscriberConfig (VO)
  - RetryPolicy (VO)
  - DeadLetterQueue (VO)

### 2.8 Configuration Management Context

**Ответственность**: Управление конфигурацией системы, feature flags, environment-specific настройки

**Основные агрегаты**:
- **Configuration** (Aggregate Root)
  - ConfigValue (VO)
  - ValidationRules (VO)
  - VersionHistory (Entity)
- **FeatureFlag** (Aggregate Root)
  - ToggleRules (VO)
  - RolloutStrategy (VO)

## 3. C4 Diagrams

### 3.1 Level 1: System Context Diagram

```mermaid
graph TB
    subgraph "External Users"
        HCP[Healthcare Professionals]
        Admin[System Administrators]
        Auditor[Compliance Auditors]
    end
    
    subgraph "Healthcare Platform"
        System[Agent-Orchestrated<br/>Healthcare Platform]
    end
    
    subgraph "External Systems"
        IRIS[IRIS API<br/>Immunization Registry]
        KMS[AWS KMS<br/>Key Management]
        SIEM[SIEM System<br/>Security Monitoring]
        Backup[Backup Storage<br/>S3/Glacier]
    end
    
    HCP -->|HTTPS/JWT| System
    Admin -->|HTTPS/MFA| System
    Auditor -->|Read-only Access| System
    
    System -->|OAuth2/HMAC| IRIS
    System -->|Encrypt/Decrypt| KMS
    System -->|Stream Logs| SIEM
    System -->|Archive Data| Backup
    
    style System fill:#1168bd,stroke:#333,stroke-width:4px
    style IRIS fill:#ff6b6b,stroke:#333,stroke-width:2px
    style KMS fill:#4ecdc4,stroke:#333,stroke-width:2px
```

### 3.2 Level 2: Container Diagram

```mermaid
graph TB
    subgraph "Healthcare Platform Containers"
        API[FastAPI<br/>Application]
        EventBus[Event Bus<br/>Internal]
        Cache[Redis Cache]
        
        subgraph "Data Layer"
            PG[(PostgreSQL<br/>+ RLS)]
            EventStore[(Event Store<br/>PostgreSQL)]
        end
        
        subgraph "Background Workers"
            PurgeWorker[Purge Scheduler<br/>Worker]
            AuditWorker[Audit Processor<br/>Worker]
            SyncWorker[IRIS Sync<br/>Worker]
        end
    end
    
    subgraph "External"
        IRIS[IRIS API]
        KMS[AWS KMS]
        Users[Users]
    end
    
    Users -->|HTTPS| API
    API -->|Query/Command| PG
    API -->|Publish| EventBus
    API -->|Cache| Cache
    
    EventBus -->|Subscribe| PurgeWorker
    EventBus -->|Subscribe| AuditWorker
    EventBus -->|Subscribe| SyncWorker
    EventBus -->|Persist| EventStore
    
    SyncWorker -->|OAuth2/HMAC| IRIS
    API -->|Encrypt/Decrypt| KMS
    PurgeWorker -->|Execute| PG
    AuditWorker -->|Write| PG
    
    style API fill:#1168bd,stroke:#333,stroke-width:2px
    style EventBus fill:#ff6b6b,stroke:#333,stroke-width:2px
    style PG fill:#4ecdc4,stroke:#333,stroke-width:2px
```

### 3.3 Component Diagram - IRIS Integration Context

```mermaid
graph LR
    subgraph "IRIS Integration Components"
        Client[IRIS Client<br/>Main Interface]
        Security[Security Layer<br/>Auth & Encryption]
        Resilience[Resilience Layer<br/>Circuit Breaker]
        Transport[Transport Layer<br/>HTTP Client]
        Cache[Cache Layer<br/>Response Cache]
        
        subgraph "Support Components"
            TokenMgr[Token Manager<br/>OAuth2]
            RateLimit[Rate Limiter<br/>Adaptive]
            Metrics[Metrics Collector]
        end
    end
    
    Client --> Security
    Security --> Resilience
    Resilience --> Transport
    Resilience --> Cache
    
    Security --> TokenMgr
    Resilience --> RateLimit
    Transport --> Metrics
    
    style Client fill:#1168bd,stroke:#333,stroke-width:2px
    style Security fill:#ff6b6b,stroke:#333,stroke-width:2px
    style Resilience fill:#4ecdc4,stroke:#333,stroke-width:2px
```

## 4. Событийная модель (Event Storming)

### 4.1 Основные доменные события

| Событие | Публикует | Подписчики | Описание |
|---------|-----------|------------|----------|
| **User.Created** | User Management | Audit, Event Store | Новый пользователь создан |
| **User.Authenticated** | User Management | Audit, Session Manager | Успешная аутентификация |
| **User.LockedOut** | User Management | Audit, Security Alert | Блокировка после неудачных попыток |
| **Role.Assigned** | User Management | Audit, Access Control | Роль назначена пользователю |
| **Immunization.Created** | IRIS Integration | Healthcare Records, Audit | Новая запись о прививке |
| **Immunization.Updated** | IRIS Integration | Healthcare Records, Audit | Обновление записи |
| **IRIS.SyncCompleted** | IRIS Integration | Healthcare Records | Синхронизация завершена |
| **CircuitBreaker.Opened** | IRIS Integration | Monitoring, Alert System | Прерыватель открыт |
| **PHI.Accessed** | Healthcare Records | Audit, Compliance | Доступ к PHI данным |
| **PHI.Encrypted** | Encryption | Audit | Данные зашифрованы |
| **Key.Rotated** | Encryption | All Contexts | Ротация ключа шифрования |
| **RetentionPolicy.Applied** | Data Retention | Purge Worker | Применена политика хранения |
| **Data.Purged** | Data Retention | Audit, Compliance | Данные удалены |
| **PurgeOverride.Created** | Data Retention | Audit, Approval Workflow | Создано исключение для удаления |
| **Audit.LogCreated** | Audit Context | Event Store, SIEM | Создана запись аудита |
| **Compliance.ReportGenerated** | Audit Context | Storage, Notification | Сгенерирован отчет |
| **Config.Changed** | Configuration | All Contexts | Изменена конфигурация |
| **FeatureFlag.Toggled** | Configuration | Affected Contexts | Переключен feature flag |

### 4.2 Событийные потоки (Event Flows)

```mermaid
sequenceDiagram
    participant U as User
    participant API as API Gateway
    participant Auth as Auth Service
    participant IRIS as IRIS Service
    participant Audit as Audit Service
    participant Event as Event Bus
    
    U->>API: Login Request
    API->>Auth: Authenticate
    Auth->>Event: User.Authenticated
    Event-->>Audit: Log Event
    
    U->>API: Create Immunization
    API->>IRIS: Create Record
    IRIS->>Event: Immunization.Created
    Event-->>Audit: Log PHI Access
    Event-->>HR: Update Patient Record
```

## 5. Взаимодействия между контекстами

### 5.1 Матрица взаимодействий

| Источник | Целевой контекст | Тип интеграции | Протокол | Описание |
|----------|------------------|----------------|----------|----------|
| User Management | Audit | Event | Event Bus | Все действия пользователей |
| User Management | All Contexts | Sync | JWT Token | Контекст пользователя |
| IRIS Integration | Healthcare Records | Event | Event Bus | Синхронизация данных |
| IRIS Integration | Encryption | Sync | Internal API | Шифрование PHI |
| Healthcare Records | Encryption | Sync | Internal API | Шифрование/дешифрование |
| Healthcare Records | Audit | Event | Event Bus | Доступ к PHI |
| Data Retention | Healthcare Records | Async | Event Bus | Удаление данных |
| Data Retention | Audit | Event | Event Bus | Логирование удалений |
| Configuration | All Contexts | Event | Event Bus | Изменения конфигурации |
| All Contexts | Event Processing | Event | Event Bus | Публикация событий |

### 5.2 Паттерны интеграции

```mermaid
graph LR
    subgraph "Synchronous Communication"
        A1[API Gateway] -->|REST| A2[Service]
        A2 -->|Response| A1
    end
    
    subgraph "Asynchronous Communication"
        B1[Publisher] -->|Event| EventBus[Event Bus]
        EventBus -->|Deliver| B2[Subscriber 1]
        EventBus -->|Deliver| B3[Subscriber 2]
    end
    
    subgraph "Shared Data"
        C1[Service 1] -->|Read/Write| DB[(PostgreSQL)]
        C2[Service 2] -->|Read Only| DB
    end
```

## 6. Границы и ограничения

### 6.1 Границы транзакций

| Контекст | Граница транзакции | Consistency Model |
|----------|-------------------|-------------------|
| User Management | Per aggregate (User, Role) | Strong consistency |
| IRIS Integration | Per API call | Eventual consistency |
| Healthcare Records | Per patient record | Strong consistency |
| Audit | Append-only, no transactions | Eventual consistency |
| Data Retention | Batch operations | Eventual consistency |

### 6.2 Data Ownership

```mermaid
graph TB
    subgraph "User Management"
        Users[Users Table]
        Roles[Roles Table]
        Permissions[Permissions Table]
    end
    
    subgraph "Healthcare Records"
        Patients[Patients Table]
        Immunizations[Immunizations Table]
    end
    
    subgraph "Audit & Compliance"
        AuditLogs[Audit Logs Table]
        AccessLogs[Access Logs Table]
    end
    
    subgraph "IRIS Integration"
        APIRequests[API Requests Table]
        APICredentials[API Credentials Table]
    end
    
    style Users fill:#e1f5fe
    style Patients fill:#fff3e0
    style AuditLogs fill:#f3e5f5
    style APIRequests fill:#e8f5e9
```

### 6.3 Security Boundaries

**Row Level Security (RLS)**:
- Patients таблица: доступ только к записям своей организации
- Audit logs: read-only для всех кроме системы
- API credentials: доступ только для service accounts

**Encryption Boundaries**:
- At rest: все PHI/PII поля в PostgreSQL
- In transit: TLS 1.3 для всех соединений
- Field-level: отдельное шифрование для sensitive данных

**Network Boundaries**:
- Internal services: private subnet
- External APIs: через API Gateway с WAF
- Database: изолированная subnet с security groups

## 7. Рекомендации по расширению

### 7.1 Масштабирование контекстов

**Легко масштабируемые**:
1. **IRIS Integration** - stateless, можно добавлять инстансы
2. **Audit Processing** - партиционирование по времени
3. **Event Processing** - горизонтальное масштабирование workers

**Требуют планирования**:
1. **Healthcare Records** - sharding по patient ID
2. **User Management** - кеширование сессий в Redis

### 7.2 Точки расширения

```mermaid
graph LR
    subgraph "Current System"
        Core[Core Platform]
    end
    
    subgraph "Future Integrations"
        HL7[HL7 FHIR Server]
        ML[ML Pipeline]
        Analytics[Analytics Engine]
        Mobile[Mobile Gateway]
    end
    
    Core -->|FHIR API| HL7
    Core -->|Event Stream| ML
    Core -->|Data Export| Analytics
    Core -->|GraphQL| Mobile
    
    style Core fill:#1168bd
    style HL7 fill:#e8f5e9
    style ML fill:#fff3e0
    style Analytics fill:#f3e5f5
    style Mobile fill:#e1f5fe
```

### 7.3 Рекомендации по миграции к микросервисам

**Приоритет выделения** (от высокого к низкому):
1. IRIS Integration → отдельный сервис
2. Audit & Compliance → отдельный сервис
3. Data Retention → background job service
4. Healthcare Records → остается в монолите дольше всего

**Подготовка**:
- Все контексты уже имеют четкие границы
- Event Bus готов для межсервисной коммуникации
- База данных подготовлена для разделения (отдельные схемы)

---

*Сгенерировано Claude Opus 4 — 2024-12-27 14:30:00 UTC*