# Context Map - Agent-Orchestrated Healthcare Platform

## 1. Введение

Данный документ представляет архитектурную карту контекстов (Context Map) для платформы "Agent-Orchestrated App" - высокомодульной системы управления медицинскими данными с продакшн-уровнем безопасности. Документ следует принципам Domain-Driven Design (DDD), использует нотацию C4 Model для визуализации и Event Storming для моделирования событийных потоков.

**Цель документа**: Определить четкие границы между модулями системы, их взаимодействие и точки интеграции для обеспечения высокой модульности, аудируемости и безопасности уровня production.

**Связанная документация**:
- `project_spec.yaml` - высокоуровневое описание проекта
- `event_contracts.yaml` - контракты событий системы
- `secure_pipeline.yml` - CI/CD конфигурация

## 2. Перечень Bounded Contexts

### 2.1 User Management Context

**Ответственность**: Управление пользователями, аутентификация, авторизация, управление доступом на основе ролей (RBAC)

**Основные бизнес-объекты**:
- **User** (Aggregate Root)
  - UserId (Value Object)
  - Email (Value Object)
  - PasswordHash (Value Object)
  - MFAConfiguration (Value Object)
  - AccountStatus (Value Object)
- **Role** (Aggregate Root)
  - RoleId (Value Object)
  - RoleName (Value Object)
  - Permissions (Value Object Collection)
- **Session** (Aggregate Root)
  - SessionToken (Value Object)
  - UserId (Value Object)
  - ExpirationTime (Value Object)
  - IPAddress (Value Object)

### 2.2 Agent Orchestration Context

**Ответственность**: Управление AI-агентами, оркестрация задач, координация выполнения

**Основные бизнес-объекты**:
- **Agent** (Aggregate Root)
  - AgentId (Value Object)
  - AgentType (Value Object)
  - Capabilities (Value Object Collection)
  - Status (Value Object)
- **Task** (Aggregate Root)
  - TaskId (Value Object)
  - TaskDefinition (Entity)
  - ExecutionPlan (Value Object)
  - Priority (Value Object)
- **Workflow** (Aggregate Root)
  - WorkflowId (Value Object)
  - Steps (Entity Collection)
  - ExecutionState (Value Object)

### 2.3 Healthcare Data Context

**Ответственность**: Управление медицинскими данными, соответствие FHIR стандартам, обработка PHI/PII

**Основные бизнес-объекты**:
- **Patient** (Aggregate Root)
  - PatientId (Value Object)
  - Demographics (Entity) - encrypted
  - ConsentStatus (Value Object)
  - MedicalRecordNumber (Value Object)
- **ClinicalDocument** (Aggregate Root)
  - DocumentId (Value Object)
  - DocumentType (Value Object)
  - EncryptedContent (Value Object)
  - Metadata (Entity)
- **Immunization** (Entity)
  - VaccineCode (Value Object)
  - AdministrationDate (Value Object)
  - Provider (Value Object)

### 2.4 Audit & Logging Context

**Ответственность**: Неизменяемое логирование всех операций, соответствие SOC2/HIPAA, формирование отчетности

**Основные бизнес-объекты**:
- **AuditLog** (Aggregate Root)
  - LogId (Value Object)
  - Timestamp (Value Object)
  - EventType (Value Object)
  - ActorId (Value Object)
  - ResourceId (Value Object)
  - HashChain (Value Object) - для целостности
- **ComplianceReport** (Aggregate Root)
  - ReportId (Value Object)
  - ReportPeriod (Value Object)
  - Metrics (Entity Collection)
- **AccessLog** (Entity)
  - AccessTime (Value Object)
  - ResourceAccessed (Value Object)
  - AccessResult (Value Object)

### 2.5 Integration Context

**Ответственность**: Интеграция с внешними системами (IRIS API), управление API подключениями

**Основные бизнес-объекты**:
- **APIEndpoint** (Aggregate Root)
  - EndpointId (Value Object)
  - URL (Value Object)
  - AuthConfiguration (Entity)
  - RateLimitPolicy (Value Object)
- **APICredentials** (Aggregate Root)
  - CredentialId (Value Object)
  - EncryptedSecret (Value Object)
  - ExpirationDate (Value Object)
- **IntegrationRequest** (Entity)
  - RequestId (Value Object)
  - Status (Value Object)
  - RetryCount (Value Object)

### 2.6 Data Retention Context

**Ответственность**: Управление жизненным циклом данных, автоматическое удаление, соблюдение политик хранения

**Основные бизнес-объекты**:
- **RetentionPolicy** (Aggregate Root)
  - PolicyId (Value Object)
  - DataType (Value Object)
  - RetentionPeriod (Value Object)
  - PurgeStrategy (Value Object)
- **PurgeExecution** (Aggregate Root)
  - ExecutionId (Value Object)
  - ScheduledTime (Value Object)
  - AffectedRecords (Value Object Collection)
- **RetentionOverride** (Entity)
  - OverrideReason (Value Object)
  - ApprovalStatus (Value Object)

### 2.7 Security & Encryption Context

**Ответственность**: Шифрование данных, управление ключами, криптографические операции

**Основные бизнес-объекты**:
- **EncryptionKey** (Aggregate Root)
  - KeyId (Value Object)
  - KeyVersion (Value Object)
  - Algorithm (Value Object)
  - RotationSchedule (Value Object)
- **EncryptedData** (Entity)
  - DataId (Value Object)
  - CipherText (Value Object)
  - EncryptionMetadata (Value Object)

## 3. C4 Diagrams

### 3.1 Level 1: System Context Diagram

```mermaid
graph TB
    subgraph "Users"
        HCP[Healthcare Professionals]
        Admin[System Administrators]
        Auditor[Compliance Auditors]
        Agent[AI Agents]
    end
    
    subgraph "Agent-Orchestrated Platform"
        System[Agent-Orchestrated<br/>Healthcare System]
    end
    
    subgraph "External Systems"
        IRIS[IRIS API<br/>Immunization Registry]
        Vault[HashiCorp Vault<br/>Secrets Management]
        SIEM[SIEM System<br/>Security Monitoring]
        S3[AWS S3<br/>Document Storage]
    end
    
    HCP -->|HTTPS/JWT| System
    Admin -->|HTTPS/MFA| System
    Auditor -->|Read-only API| System
    Agent -->|Internal API| System
    
    System -->|OAuth2/HMAC| IRIS
    System -->|mTLS| Vault
    System -->|Syslog/HTTPS| SIEM
    System -->|S3 API| S3
    
    style System fill:#1168bd,stroke:#333,stroke-width:4px,color:#fff
    style IRIS fill:#ff6b6b,stroke:#333,stroke-width:2px
    style Vault fill:#4ecdc4,stroke:#333,stroke-width:2px
```

### 3.2 Level 2: Container Diagram

```mermaid
graph TB
    subgraph "Kubernetes Cluster"
        subgraph "Application Layer"
            API[FastAPI<br/>REST API]
            GraphQL[GraphQL<br/>Gateway]
            WSGateway[WebSocket<br/>Gateway]
        end
        
        subgraph "Core Services"
            UserSvc[User Management<br/>Service]
            AgentSvc[Agent Orchestration<br/>Service]
            HealthSvc[Healthcare Data<br/>Service]
            AuditSvc[Audit Service]
        end
        
        subgraph "Infrastructure"
            EventBus[NATS<br/>Event Bus]
            Cache[Redis Cache]
            
            subgraph "Data Layer"
                PG[(PostgreSQL<br/>+ RLS)]
                EventStore[(Event Store<br/>PostgreSQL)]
            end
        end
        
        subgraph "Background Jobs"
            PurgeJob[Data Purge<br/>Scheduler]
            SyncJob[IRIS Sync<br/>Worker]
            ReportJob[Report<br/>Generator]
        end
    end
    
    subgraph "External"
        Users[Users]
        IRIS[IRIS API]
        Vault[Vault]
    end
    
    Users -->|HTTPS| API
    Users -->|WSS| WSGateway
    API -->|gRPC| UserSvc
    API -->|gRPC| AgentSvc
    API -->|gRPC| HealthSvc
    
    UserSvc -->|SQL| PG
    AgentSvc -->|SQL| PG
    HealthSvc -->|SQL| PG
    AuditSvc -->|SQL| PG
    
    UserSvc -->|Publish| EventBus
    AgentSvc -->|Publish| EventBus
    HealthSvc -->|Publish| EventBus
    
    EventBus -->|Subscribe| AuditSvc
    EventBus -->|Subscribe| PurgeJob
    EventBus -->|Subscribe| SyncJob
    EventBus -->|Persist| EventStore
    
    SyncJob -->|HTTPS| IRIS
    API -->|Get Secrets| Vault
    
    style API fill:#1168bd,stroke:#333,stroke-width:2px,color:#fff
    style EventBus fill:#ff6b6b,stroke:#333,stroke-width:2px,color:#fff
    style PG fill:#4ecdc4,stroke:#333,stroke-width:2px
```

### 3.3 Component Diagram - Agent Orchestration Context

```mermaid
graph LR
    subgraph "Agent Orchestration Components"
        Coordinator[Task Coordinator<br/>Component]
        Scheduler[Task Scheduler<br/>Component]
        Executor[Task Executor<br/>Component]
        Monitor[Task Monitor<br/>Component]
        
        subgraph "Agent Registry"
            Registry[Agent Registry]
            Discovery[Agent Discovery]
            Health[Health Check]
        end
        
        subgraph "Workflow Engine"
            WFEngine[Workflow Engine]
            StateManager[State Manager]
            RuleEngine[Rule Engine]
        end
    end
    
    Coordinator --> Scheduler
    Scheduler --> Executor
    Executor --> Monitor
    Monitor --> Coordinator
    
    Executor --> Registry
    Registry --> Discovery
    Discovery --> Health
    
    Coordinator --> WFEngine
    WFEngine --> StateManager
    WFEngine --> RuleEngine
    
    style Coordinator fill:#1168bd,stroke:#333,stroke-width:2px,color:#fff
    style WFEngine fill:#ff6b6b,stroke:#333,stroke-width:2px,color:#fff
    style Registry fill:#4ecdc4,stroke:#333,stroke-width:2px
```

## 4. Событийная модель (Event Storming)

### 4.1 Основные доменные события

| Событие | Источник | Подписчики | Описание |
|---------|----------|------------|----------|
| **User.Created** | User Management | Audit, Agent Orchestration | Создан новый пользователь |
| **User.Authenticated** | User Management | Audit, Session Manager | Успешная аутентификация |
| **User.RoleAssigned** | User Management | Audit, Access Control | Назначена роль пользователю |
| **User.Deactivated** | User Management | All Contexts | Деактивация учетной записи |
| **Agent.Registered** | Agent Orchestration | Audit, Task Scheduler | Регистрация нового агента |
| **Task.Created** | Agent Orchestration | Task Queue, Audit | Создана новая задача |
| **Task.Assigned** | Agent Orchestration | Agent, Monitor | Задача назначена агенту |
| **Task.Completed** | Agent Orchestration | Workflow Engine, Audit | Задача выполнена |
| **Workflow.Started** | Agent Orchestration | Task Scheduler, Audit | Запущен рабочий процесс |
| **Patient.Created** | Healthcare Data | Audit, Data Retention | Создана карта пациента |
| **PHI.Accessed** | Healthcare Data | Audit, Compliance | Доступ к PHI данным |
| **Document.Uploaded** | Healthcare Data | Encryption, Audit | Загружен медицинский документ |
| **Immunization.Recorded** | Healthcare Data | IRIS Sync, Audit | Записана информация о прививке |
| **Data.Encrypted** | Security | Audit | Данные зашифрованы |
| **Key.Rotated** | Security | All Contexts | Ротация ключа шифрования |
| **Audit.LogCreated** | Audit | Event Store, SIEM | Создана запись аудита |
| **Compliance.ReportGenerated** | Audit | Storage, Notification | Сгенерирован отчет соответствия |
| **Integration.RequestSent** | Integration | Audit, Monitoring | Отправлен запрос к внешней системе |
| **Integration.ResponseReceived** | Integration | Processing Queue, Audit | Получен ответ от внешней системы |
| **RetentionPolicy.Applied** | Data Retention | Purge Scheduler | Применена политика хранения |
| **Data.Purged** | Data Retention | Audit, Compliance | Данные удалены |

### 4.2 Событийная цепочка примера

```mermaid
sequenceDiagram
    participant U as User
    participant API as API Gateway
    participant Auth as Auth Service
    participant Agent as Agent Service
    participant Health as Healthcare Service
    participant Audit as Audit Service
    participant Bus as Event Bus
    
    U->>API: Request Patient Data
    API->>Auth: Validate Token
    Auth->>Bus: User.Authenticated
    Bus-->>Audit: Log Authentication
    
    API->>Agent: Create Task
    Agent->>Bus: Task.Created
    Bus-->>Audit: Log Task Creation
    
    Agent->>Agent: Assign to AI Agent
    Agent->>Bus: Task.Assigned
    
    Agent->>Health: Process Request
    Health->>Bus: PHI.Accessed
    Bus-->>Audit: Log PHI Access
    
    Health->>API: Return Encrypted Data
    API->>U: Response
```

## 5. Взаимодействия между контекстами

### 5.1 Матрица взаимодействий

| Источник | Целевой контекст | Тип | Протокол | Паттерн | Описание |
|----------|------------------|-----|----------|---------|----------|
| User Management | Audit & Logging | Async | Event Bus | Pub/Sub | Все события пользователей |
| User Management | All Contexts | Sync | JWT | Shared Kernel | Контекст безопасности |
| Agent Orchestration | Healthcare Data | Sync | gRPC | Customer/Supplier | Обработка медданных |
| Agent Orchestration | Audit & Logging | Async | Event Bus | Pub/Sub | Логирование операций |
| Healthcare Data | Security & Encryption | Sync | Internal API | ACL | Шифрование PHI |
| Healthcare Data | Integration | Async | Event Bus | Pub/Sub | Синхронизация с IRIS |
| Integration | External Systems | Sync | REST/SOAP | ACL | Внешние вызовы |
| Data Retention | Healthcare Data | Async | Event Bus | Pub/Sub | Удаление данных |
| Security & Encryption | All Contexts | Sync | Internal API | Shared Kernel | Крипто-операции |
| All Contexts | Audit & Logging | Async | Event Bus | Pub/Sub | Аудит всех операций |

### 5.2 Диаграмма интеграционных паттернов

```mermaid
graph TB
    subgraph "Synchronous Patterns"
        REQ[Request/Response<br/>gRPC, REST]
        SK[Shared Kernel<br/>JWT, Common Types]
    end
    
    subgraph "Asynchronous Patterns"
        PS[Pub/Sub<br/>Event Bus]
        CQRS[CQRS<br/>Command/Query Split]
    end
    
    subgraph "Anti-Corruption Layer"
        ACL[ACL<br/>External Integration]
        TRANS[Translation Layer]
    end
    
    subgraph "Data Patterns"
        ES[Event Sourcing]
        CDC[Change Data Capture]
    end
    
    REQ --> SK
    PS --> CQRS
    ACL --> TRANS
    ES --> CDC
    
    style REQ fill:#1168bd,color:#fff
    style PS fill:#ff6b6b,color:#fff
    style ACL fill:#4ecdc4
    style ES fill:#ffd93d
```

## 6. Границы и ограничения

### 6.1 Границы транзакций

| Контекст | Scope | Consistency Model | Isolation Level |
|----------|-------|-------------------|-----------------|
| User Management | Per Aggregate | Strong Consistency | Read Committed |
| Agent Orchestration | Per Workflow | Eventual Consistency | Read Committed |
| Healthcare Data | Per Patient | Strong Consistency | Serializable |
| Audit & Logging | Append-Only | Eventual Consistency | Read Uncommitted |
| Integration | Per Request | At-Least-Once | Read Committed |
| Data Retention | Batch Operation | Eventual Consistency | Read Committed |

### 6.2 Data Ownership

```mermaid
graph LR
    subgraph "User Management Owns"
        Users[(users)]
        Roles[(roles)]
        Sessions[(sessions)]
    end
    
    subgraph "Healthcare Data Owns"
        Patients[(patients)]
        Documents[(documents)]
        Immunizations[(immunizations)]
    end
    
    subgraph "Agent Orchestration Owns"
        Agents[(agents)]
        Tasks[(tasks)]
        Workflows[(workflows)]
    end
    
    subgraph "Audit & Logging Owns"
        AuditLogs[(audit_logs)]
        AccessLogs[(access_logs)]
        ComplianceReports[(reports)]
    end
    
    style Users fill:#e3f2fd
    style Patients fill:#fff8e1
    style Agents fill:#f3e5f5
    style AuditLogs fill:#e8f5e9
```

### 6.3 Security Boundaries

**Row Level Security (RLS)**:
```sql
-- Пример политики для таблицы patients
CREATE POLICY patient_isolation ON patients
    FOR ALL 
    TO application_user
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
```

**Encryption Boundaries**:
- **At Rest**: AES-256-GCM для всех PHI/PII полей
- **In Transit**: TLS 1.3 минимум для всех соединений
- **Field Level**: Детерминированное шифрование для поисковых полей

**Network Segmentation**:
```mermaid
graph TB
    subgraph "DMZ"
        LB[Load Balancer]
        WAF[Web Application Firewall]
    end
    
    subgraph "Application Tier"
        API[API Services]
        Bus[Event Bus]
    end
    
    subgraph "Data Tier"
        DB[(PostgreSQL)]
        Cache[(Redis)]
    end
    
    LB --> API
    API --> Bus
    API --> DB
    API --> Cache
    
    style DMZ fill:#ffcdd2
    style "Application Tier" fill:#fff9c4
    style "Data Tier" fill:#c8e6c9
```

## 7. Рекомендации по расширению

### 7.1 Масштабирование контекстов

**Горизонтально масштабируемые**:
1. **Agent Orchestration** - stateless агенты, партиционирование по типу задач
2. **Integration Context** - множественные инстансы с load balancing
3. **Audit & Logging** - партиционирование по времени

**Вертикально масштабируемые**:
1. **Healthcare Data** - требует тщательного шардирования по patient_id
2. **Security & Encryption** - ограничено производительностью HSM

### 7.2 Точки расширения

```mermaid
graph LR
    subgraph "Current System"
        Core[Core Platform]
        EventBus[Event Bus<br/>NATS]
    end
    
    subgraph "Future Extensions"
        FHIR[FHIR Server<br/>HL7 Compliant]
        ML[ML Pipeline<br/>TensorFlow]
        Analytics[Real-time Analytics<br/>Apache Flink]
        Blockchain[Audit Blockchain<br/>Hyperledger]
        IoT[IoT Gateway<br/>Medical Devices]
    end
    
    Core -->|FHIR API| FHIR
    EventBus -->|Event Stream| ML
    EventBus -->|CDC| Analytics
    Core -->|Audit Trail| Blockchain
    IoT -->|MQTT| EventBus
    
    style Core fill:#1168bd,color:#fff
    style EventBus fill:#ff6b6b,color:#fff
    style FHIR fill:#4ecdc4
    style ML fill:#ffd93d
    style Analytics fill:#f8bbd0
```

### 7.3 Миграционная стратегия

**Phase 1 - Извлечение сервисов** (0-6 месяцев):
- Integration Context → отдельный микросервис
- Audit & Logging → отдельный сервис с собственной БД

**Phase 2 - Декомпозиция данных** (6-12 месяцев):
- Разделение схем БД по контекстам
- Внедрение Saga pattern для распределенных транзакций

**Phase 3 - Полная автономия** (12+ месяцев):
- Каждый контекст как отдельный deployment
- Service mesh для управления коммуникациями

**Подготовительные шаги**:
- ✅ Event Bus уже готов для асинхронной коммуникации
- ✅ Четкие границы контекстов определены
- ✅ API Gateway для единой точки входа
- 🔄 Необходимо внедрить distributed tracing
- 🔄 Подготовить схемы БД к разделению

---

*Сгенерировано Claude Opus 4 — 2024-12-27 15:45:00 UTC*