# Threat Model для Agent-Orchestrated Healthcare Platform

## 1. Введение

### 1.1 Цель документа

Данный документ представляет комплексный анализ угроз безопасности для платформы оркестрации AI-агентов, предназначенной для обработки медицинских данных. Анализ выполнен с использованием методологий STRIDE (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege) и диаграмм потоков данных (DFD). Документ служит основой для принятия архитектурных решений по безопасности и соответствию требованиям SOC2 и HIPAA.

### 1.2 Сфера применения

Анализ охватывает следующие ключевые компоненты системы:

**Основная инфраструктура**: PostgreSQL 15+ с Row Level Security (RLS), обеспечивающий изоляцию данных на уровне базы данных и криптографическую целостность audit trail через hash chaining механизм.

**API слой**: FastAPI приложение, реализующее модульную монолитную архитектуру с JWT/HMAC аутентификацией и field-level encryption для PHI/PII данных.

**Система обмена сообщениями**: Внутренняя Event Bus с гарантиями доставки at-least-once, поддержкой transactional outbox pattern и возможностью replay событий из PostgreSQL event store.

**Внешние интеграции**: API Gateway для взаимодействия с IRIS (Immunization Registry Information Systems) и другими внешними медицинскими системами с поддержкой OAuth2/HMAC аутентификации.

## 2. Контекст и границы системы

### 2.1 Архитектурный обзор

Система построена по принципу Defense in Depth с множественными уровнями защиты. Центральным элементом является PostgreSQL база данных, выступающая как единый источник истины с immutable audit logs и encrypted storage для sensitive данных. FastAPI приложение обрабатывает бизнес-логику через изолированные модули, коммуницирующие через Event Bus. Все внешние взаимодействия проходят через защищенный API Gateway с rate limiting и circuit breaker механизмами.

### 2.2 Границы доверия

Система определяет четыре основные зоны доверия. Внутренняя зона включает PostgreSQL и core business logic модули. DMZ содержит API Gateway и authentication сервисы. Внешняя зона охватывает IRIS endpoints и сторонние медицинские системы. Пользовательская зона включает authenticated healthcare professionals и системных администраторов.

## 3. Диаграмма потоков данных (Level 0)

```
[External User] --HTTPS--> [API Gateway] --JWT--> [FastAPI App]
                                |                        |
                                v                        v
                          [Rate Limiter]           [Event Bus]
                                |                        |
                                v                        v
                          [IRIS API Client] <------[PostgreSQL]
                                                   (RLS + Encryption)
```

## 4. Анализ угроз по STRIDE

### 4.1 Spoofing (Подмена идентичности)

**Угроза S1: Подмена JWT токенов**
Злоумышленник может попытаться создать или модифицировать JWT токены для получения несанкционированного доступа к API endpoints. При успешной атаке возможен доступ к PHI данным пациентов или выполнение административных операций.

*Оценка риска*: Высокий (вероятность: средняя, воздействие: критическое)

*Меры смягчения*: Реализация JWT с коротким временем жизни (15 минут), использование refresh tokens с ротацией, подписание токенов с использованием RS256 алгоритма с регулярной ротацией ключей. Внедрение JTI (JWT ID) для предотвращения replay атак.

**Угроза S2: API Key compromise для IRIS integration**
Компрометация API ключей для взаимодействия с внешними медицинскими системами может привести к несанкционированному доступу к immunization records.

*Оценка риска*: Высокий (вероятность: низкая, воздействие: критическое)

*Меры смягчения*: Хранение API ключей в зашифрованном виде в отдельной таблице api_credentials с использованием envelope encryption. Реализация автоматической ротации ключей каждые 90 дней. Мониторинг аномальной активности через audit logs.

### 4.2 Tampering (Модификация данных)

**Угроза T1: Модификация audit logs**
Попытка изменения immutable audit logs для сокрытия несанкционированной активности нарушает требования SOC2 compliance.

*Оценка риска*: Критический (вероятность: низкая, воздействие: критическое)

*Меры смягчения*: Использование PostgreSQL rules для запрета UPDATE/DELETE операций на audit_logs таблице. Реализация blockchain-style hash chaining где каждая запись содержит hash предыдущей. Периодическая верификация целостности через stored procedure verify_audit_log_integrity().

**Угроза T2: SQL Injection в динамических запросах**
Внедрение вредоносного SQL кода через user input может привести к несанкционированному доступу или модификации данных.

*Оценка риска*: Средний (вероятность: низкая, воздействие: высокое)

*Меры смягчения*: Использование SQLAlchemy ORM с параметризованными запросами. Валидация всех входных данных через Pydantic models. Code review процесс для любых raw SQL запросов. Реализация stored procedures для сложных операций.

### 4.3 Repudiation (Отказ от авторства)

**Угроза R1: Отрицание выполнения критических операций**
Пользователи могут отрицать выполнение операций с PHI данными или изменение конфигурации системы.

*Оценка риска*: Средний (вероятность: средняя, воздействие: среднее)

*Меры смягчения*: Comprehensive audit logging всех операций с correlation_id для end-to-end tracing. Цифровые подписи для критических операций. Интеграция с SIEM системами для centralized log management.

### 4.4 Information Disclosure (Раскрытие информации)

**Угроза I1: Утечка PHI через error messages**
Детальные error messages могут раскрывать sensitive информацию о пациентах или внутренней структуре системы.

*Оценка риска*: Высокий (вероятность: средняя, воздействие: высокое)

*Меры смягчения*: Реализация глобального exception handler в FastAPI, возвращающего generic error messages пользователям. Детальные errors логируются только во внутренние системы. Автоматическое обнаружение и маскирование PII/PHI в логах.

**Угроза I2: Side-channel атаки через timing analysis**
Анализ времени ответа API может раскрыть информацию о существовании записей или результатах аутентификации.

*Оценка риска*: Низкий (вероятность: низкая, воздействие: среднее)

*Меры смягчения*: Constant-time сравнение для authentication операций. Добавление controlled random delay для sensitive endpoints. Rate limiting для предотвращения automated timing analysis.

### 4.5 Denial of Service

**Угроза D1: Event Bus overflow**
Flood атака на Event Bus может привести к memory exhaustion и недоступности системы.

*Оценка риска*: Высокий (вероятность: средняя, воздействие: высокое)

*Меры смягчения*: Реализация backpressure механизма с spillover в PostgreSQL. Per-publisher rate limiting. Circuit breaker для изоляции проблемных subscribers. Мониторинг queue depth с автоматическими alerts.

**Угроза D2: Database connection pool exhaustion**
Исчерпание database connections может сделать систему недоступной для легитимных пользователей.

*Оценка риска*: Средний (вероятность: средняя, воздействие: среднее)

*Меры смягчения*: Динамическое управление connection pool размером. Statement timeout configuration. Query performance monitoring с автоматическим kill для long-running queries. Separate read/write connection pools.

### 4.6 Elevation of Privilege

**Угроза E1: RLS bypass через application vulnerabilities**
Обход Row Level Security через уязвимости в application layer может дать доступ к данным других tenants.

*Оценка риска*: Критический (вероятность: низкая, воздействие: критическое)

*Меры смягчения*: Строгое разделение application и database users. Использование set_config() для передачи user context в RLS policies. Regular security audits RLS правил. Принцип least privilege для database connections.

**Угроза E2: Privilege escalation через role manipulation**
Манипуляция с user_roles таблицей может привести к несанкционированному повышению привилегий.

*Оценка риска*: Высокий (вероятность: низкая, воздействие: высокое)

*Меры смягчения*: Temporal validity checks для role assignments. Approval workflow для privilege changes. Audit trail всех изменений ролей. Separation of duties - администраторы не могут изменять свои собственные роли.

## 5. Специфичные угрозы для Healthcare

### 5.1 HIPAA Compliance угрозы

**Угроза H1: Недостаточное шифрование PHI at rest**
Несоответствие HIPAA требованиям по шифрованию может привести к regulatory penalties.

*Оценка риска*: Критический (вероятность: низкая, воздействие: критическое)

*Меры смягчения*: AES-256-GCM шифрование для всех PHI полей. Separate encryption keys per data classification. Integration с HSM или AWS KMS для key management. Regular encryption audit через encrypted_fields_registry таблицу.

### 5.2 Data Integrity угрозы

**Угроза DI1: Corruption иммунизационных записей**
Повреждение данных о прививках может привести к медицинским ошибкам.

*Оценка риска*: Критический (вероятность: очень низкая, воздействие: критическое)

*Меры смягчения*: Checksums для критических данных. Bi-directional sync verification с IRIS. Immutable event sourcing для всех изменений. Point-in-time recovery capabilities.

## 6. Контрмеры и приоритеты

### 6.1 Immediate Priority (Sprint 1)

Реализация comprehensive encryption layer является первоочередной задачей. Это включает field-level encryption для PHI данных, secure key management с поддержкой rotation, и audit trail для всех cryptographic операций. Параллельно необходимо внедрить JWT authentication с proper token lifecycle management и protection против common attacks.

### 6.2 Short-term (Month 1)

Развертывание полноценной audit logging системы с hash chaining для integrity verification. Настройка RLS policies с thorough testing для multi-tenant isolation. Реализация rate limiting и circuit breaker patterns для всех external integrations.

### 6.3 Long-term (Quarter 1)

Интеграция с enterprise SIEM решением для centralized security monitoring. Внедрение automated security scanning в CI/CD pipeline. Разработка incident response playbooks специфичных для healthcare данных. Regular penetration testing с focus на healthcare-specific attack vectors.

## 7. Мониторинг и метрики безопасности

### 7.1 Key Risk Indicators (KRI)

Система должна отслеживать следующие критические показатели: количество failed authentication attempts per user/IP, anomalous data access patterns, encryption/decryption operation failures, audit log integrity check failures, и deviation от normal API usage patterns.

### 7.2 Security Operations Center (SOC) Integration

Все security events должны транслироваться в real-time в SOC dashboard. Critical events (попытки обхода RLS, массовый экспорт PHI, integrity check failures) должны генерировать immediate alerts. Retention период для security logs должен соответствовать SOC2 требованиям (минимум 1 год).

## 8. Compliance Mapping

### 8.1 SOC2 Controls

Trust Service Criteria покрываются следующим образом: CC6.1 (Logical Access Controls) через JWT и RLS, CC6.7 (Encryption) через field-level encryption, CC7.2 (System Monitoring) через comprehensive audit logs, A1.2 (System Inputs) через input validation и sanitization.

### 8.2 HIPAA Safeguards

Administrative Safeguards реализуются через role-based access control и audit trails. Physical Safeguards не применимы для cloud deployment но должны быть задокументированы для on-premise installations. Technical Safeguards покрываются через encryption, access controls, и audit mechanisms.

## 9. Заключение и следующие шаги

Данная threat model идентифицирует критические риски для healthcare AI platform и предоставляет actionable рекомендации по их митигации. Следующими шагами являются: проведение security design review с участием всех stakeholders, приоритизация implementation задач based на risk assessment, и установление regular cadence для threat model updates по мере эволюции системы.

Документ должен пересматриваться quarterly или при существенных изменениях архитектуры. Security team должна maintain отдельный risk register для tracking митigation progress и emerging threats specific to healthcare AI systems.