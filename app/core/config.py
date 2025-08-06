from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, ConfigDict
from typing import List, Optional
from functools import lru_cache
import secrets

class Settings(BaseSettings):
    """Application settings with SOC2 compliance considerations."""
    
    # Application
    DEBUG: bool = Field(default=False, description="Debug mode")
    ENVIRONMENT: str = Field(default="development", description="Environment")
    
    # Security
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    JWT_SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32), description="JWT signing key")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Token expiry")
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql://postgres:password@localhost:5432/iris_db",
        description="Database connection string"
    )
    DATABASE_POOL_SIZE: int = Field(default=5, description="DB connection pool size")
    DATABASE_MAX_OVERFLOW: int = Field(default=10, description="DB max overflow")
    
    # IRIS API Configuration
    IRIS_API_BASE_URL: str = Field(
        default="https://api.mock-iris.com/v1",
        description="IRIS API base URL"
    )
    IRIS_API_KEY: Optional[str] = Field(default=None, description="IRIS API key")
    IRIS_API_SECRET: Optional[str] = Field(default=None, description="IRIS API secret")
    IRIS_API_TIMEOUT: int = Field(default=30, description="API timeout in seconds")
    IRIS_API_RETRY_ATTEMPTS: int = Field(default=3, description="Retry attempts")
    IRIS_API_CIRCUIT_BREAKER_THRESHOLD: int = Field(default=5, description="Circuit breaker threshold")
    IRIS_API_CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = Field(default=60, description="Circuit breaker recovery timeout")
    IRIS_API_RATE_LIMIT_PER_MINUTE: int = Field(default=60, description="API rate limit per minute")
    IRIS_API_BATCH_SIZE: int = Field(default=100, description="API batch size")
    IRIS_API_ENABLE_MOCK: bool = Field(default=False, description="Enable mock IRIS API")
    
    # Encryption
    ENCRYPTION_KEY: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="Data encryption key"
    )
    ENCRYPTION_SALT: str = Field(
        default_factory=lambda: secrets.token_urlsafe(16),
        description="Encryption salt for key derivation"
    )
    
    # Audit Logging
    ENABLE_AUDIT_LOGGING: bool = Field(default=True, description="Enable audit logging")
    AUDIT_LOG_RETENTION_DAYS: int = Field(default=2555, description="7 years retention")
    AUDIT_LOG_ENCRYPTION: bool = Field(default=True, description="Encrypt audit logs")
    
    # Purge Scheduler
    PURGE_CHECK_INTERVAL_MINUTES: int = Field(default=60, description="Purge check interval")
    DEFAULT_RETENTION_DAYS: int = Field(default=90, description="Default data retention")
    ENABLE_EMERGENCY_PURGE_SUSPENSION: bool = Field(default=True)
    
    # Redis (for background tasks)
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection string"
    )
    
    # CORS
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins"
    )
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(default=100)
    RATE_LIMIT_BURST: int = Field(default=20)
    
    # Phase 5 Performance Settings
    # API Optimization
    API_RESPONSE_COMPRESSION: bool = Field(default=True, description="Enable Brotli compression")
    API_CACHE_TTL_SECONDS: int = Field(default=300, description="API response cache TTL")
    API_MAX_RESPONSE_SIZE_MB: int = Field(default=50, description="Max API response size")
    
    # Database Performance
    DB_QUERY_TIMEOUT_SECONDS: int = Field(default=30, description="Database query timeout")
    DB_CONNECTION_POOL_RECYCLE: int = Field(default=3600, description="Pool connection recycle time")
    DB_ENABLE_QUERY_LOGGING: bool = Field(default=False, description="Enable SQL query logging")
    DB_SLOW_QUERY_THRESHOLD_MS: int = Field(default=1000, description="Slow query threshold")
    
    # Performance Monitoring
    ENABLE_PERFORMANCE_MONITORING: bool = Field(default=True, description="Enable performance monitoring")
    METRICS_COLLECTION_INTERVAL: int = Field(default=60, description="Metrics collection interval")
    PERFORMANCE_ALERTS_ENABLED: bool = Field(default=True, description="Enable performance alerts")
    
    # OpenTelemetry Configuration
    OTEL_ENABLED: bool = Field(default=True, description="Enable OpenTelemetry")
    OTEL_SERVICE_NAME: str = Field(default="iris-healthcare-api", description="Service name for tracing")
    OTEL_EXPORTER_ENDPOINT: Optional[str] = Field(default=None, description="OpenTelemetry exporter endpoint")
    OTEL_SAMPLE_RATE: float = Field(default=0.1, description="Trace sampling rate")
    
    # Prometheus Metrics
    PROMETHEUS_ENABLED: bool = Field(default=True, description="Enable Prometheus metrics")
    PROMETHEUS_PORT: int = Field(default=8001, description="Prometheus metrics port")
    PROMETHEUS_NAMESPACE: str = Field(default="iris_healthcare", description="Metrics namespace")
    
    # Load Testing Configuration
    LOAD_TESTING_ENABLED: bool = Field(default=False, description="Enable load testing endpoints")
    MAX_CONCURRENT_REQUESTS: int = Field(default=1000, description="Max concurrent requests")
    REQUEST_QUEUE_SIZE: int = Field(default=5000, description="Request queue size")
    
    # Geographic and Security
    GEOIP_DATABASE_PATH: Optional[str] = Field(default=None, description="GeoIP database path")
    ENABLE_GEOGRAPHIC_BLOCKING: bool = Field(default=False, description="Enable geographic blocking")
    ALLOWED_COUNTRIES: List[str] = Field(default=["US", "CA"], description="Allowed country codes")
    
    # System Resource Monitoring
    CPU_ALERT_THRESHOLD: float = Field(default=80.0, description="CPU usage alert threshold")
    MEMORY_ALERT_THRESHOLD: float = Field(default=85.0, description="Memory usage alert threshold")
    DISK_ALERT_THRESHOLD: float = Field(default=90.0, description="Disk usage alert threshold")
    
    # Advanced Caching
    REDIS_CACHE_TTL: int = Field(default=3600, description="Redis cache TTL")
    ENABLE_QUERY_RESULT_CACHING: bool = Field(default=True, description="Enable query result caching")
    CACHE_WARMUP_ENABLED: bool = Field(default=True, description="Enable cache warmup")
    
    # Phase 5 Security Enhancements
    ADVANCED_THREAT_DETECTION: bool = Field(default=True, description="Enable advanced threat detection")
    IP_REPUTATION_CHECKING: bool = Field(default=True, description="Enable IP reputation checking")
    USER_AGENT_VALIDATION: bool = Field(default=True, description="Enable user agent validation")
    
    # File System Monitoring
    ENABLE_FILE_MONITORING: bool = Field(default=True, description="Enable file system monitoring")
    MONITORED_DIRECTORIES: List[str] = Field(
        default=["/app/logs", "/app/data"],
        description="Directories to monitor"
    )
    
    # Production Logging Configuration
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(default="json", description="Log format")
    LOG_FILE_PATH: str = Field(default="logs/healthcare.log", description="Log file path")
    LOG_MAX_FILE_SIZE: str = Field(default="50MB", description="Max log file size")
    LOG_BACKUP_COUNT: int = Field(default=5, description="Log backup count")
    LOG_AUDIT_LEVEL: str = Field(default="INFO", description="Audit log level")
    LOG_SECURITY_LEVEL: str = Field(default="WARNING", description="Security log level")
    LOG_PHI_ACCESS: bool = Field(default=True, description="Log PHI access")
    LOG_COMPLIANCE_EVENTS: bool = Field(default=True, description="Log compliance events")
    
    # Security Headers Configuration
    SECURITY_HEADERS_ENABLED: bool = Field(default=True, description="Enable security headers")
    SECURITY_HEADER_HSTS_MAX_AGE: int = Field(default=31536000, description="HSTS max age")
    SECURITY_HEADER_CSP_ENABLED: bool = Field(default=True, description="Enable CSP headers")
    SECURITY_HEADER_FRAME_OPTIONS: str = Field(default="DENY", description="X-Frame-Options header")
    SECURITY_HEADER_CONTENT_TYPE_OPTIONS: str = Field(default="nosniff", description="X-Content-Type-Options")
    SECURITY_HEADER_XSS_PROTECTION: str = Field(default="1", description="X-XSS-Protection")
    
    # DDoS Protection Configuration
    DDOS_PROTECTION_ENABLED: bool = Field(default=True, description="Enable DDoS protection")
    DDOS_MAX_CONNECTIONS_PER_IP: int = Field(default=50, description="Max connections per IP")
    DDOS_RATE_LIMIT_WINDOW_SECONDS: int = Field(default=60, description="Rate limit window")
    DDOS_BAN_DURATION_SECONDS: int = Field(default=3600, description="Ban duration")
    DDOS_WHITELIST_IPS: List[str] = Field(default=["127.0.0.1", "::1"], description="Whitelisted IPs")
    
    # Database Connection Pool Configuration (Production Optimized)
    DB_POOL_SIZE_MIN: int = Field(default=10, description="Minimum pool size")
    DB_POOL_SIZE_MAX: int = Field(default=50, description="Maximum pool size")
    DB_POOL_PRE_PING: bool = Field(default=True, description="Enable pool pre-ping")
    DB_POOL_RECYCLE_SECONDS: int = Field(default=3600, description="Pool recycle time")
    DB_CONNECTION_TIMEOUT: int = Field(default=30, description="Connection timeout")
    DB_QUERY_TIMEOUT: int = Field(default=60, description="Query timeout")
    DB_POOL_CHECKOUT_TIMEOUT: int = Field(default=30, description="Pool checkout timeout")
    DB_POOL_OVERFLOW: int = Field(default=20, description="Pool overflow")
    DB_POOL_INVALIDATE_ON_DISCONNECT: bool = Field(default=True, description="Invalidate on disconnect")
    
    # Production Monitoring
    MONITORING_ENABLED: bool = Field(default=True, description="Enable monitoring")
    METRICS_ENDPOINT_ENABLED: bool = Field(default=True, description="Enable metrics endpoint")
    HEALTH_CHECK_INTERVAL_SECONDS: int = Field(default=30, description="Health check interval")
    PERFORMANCE_MONITORING_ENABLED: bool = Field(default=True, description="Enable performance monitoring")
    TRACE_SAMPLING_RATE: float = Field(default=0.1, description="Trace sampling rate")
    
    # Edge AI Service Configuration
    GEMMA_SERVICE_URL: str = Field(default="http://gemma-engine:8001", description="Gemma AI service URL")
    WHISPER_SERVICE_URL: str = Field(default="http://whisper-service:8002", description="Whisper service URL")
    MEDICAL_NER_SERVICE_URL: str = Field(default="http://medical-ner:8003", description="Medical NER service URL")
    
    # Edge AI Configuration
    EDGE_AI_ENABLED: bool = Field(default=True, description="Enable Edge AI services")
    GEMMA_MODEL_PATH: str = Field(default="/models/gemma-3n-medical", description="Gemma model path")
    WHISPER_MODEL: str = Field(default="base.en", description="Whisper model name")
    MEDICAL_VOCABULARY_PATH: str = Field(default="/models/medical_vocab.json", description="Medical vocabulary path")
    
    # Voice Processing Settings
    MAX_AUDIO_FILE_SIZE: int = Field(default=100 * 1024 * 1024, description="Max audio file size (100MB)")
    SUPPORTED_AUDIO_FORMATS: List[str] = Field(default=[".wav", ".mp3", ".m4a", ".ogg", ".flac"], description="Supported audio formats")
    VOICE_PROCESSING_TIMEOUT: int = Field(default=300, description="Voice processing timeout (5 minutes)")
    
    # Medical NER Settings
    NER_CONFIDENCE_THRESHOLD: float = Field(default=0.7, description="NER confidence threshold")
    MAX_ENTITIES_PER_REQUEST: int = Field(default=100, description="Max entities per NER request")
    SNOMED_MAPPING_ENABLED: bool = Field(default=True, description="Enable SNOMED CT mapping")
    ICD_MAPPING_ENABLED: bool = Field(default=True, description="Enable ICD-10 mapping")
    
    # Clinical Decision Support Settings
    CLINICAL_AI_MAX_TOKENS: int = Field(default=1024, description="Max tokens for clinical AI")
    CLINICAL_AI_TEMPERATURE: float = Field(default=0.1, description="Clinical AI temperature")
    EMERGENCY_PROCESSING_TIMEOUT: int = Field(default=60, description="Emergency processing timeout (1 minute)")
    
    # Healthcare Compliance Settings
    HIPAA_COMPLIANCE_ENABLED: bool = Field(default=True, description="Enable HIPAA compliance")
    SOC2_COMPLIANCE_ENABLED: bool = Field(default=True, description="Enable SOC2 compliance")
    FHIR_COMPLIANCE_ENABLED: bool = Field(default=True, description="Enable FHIR compliance")
    GDPR_COMPLIANCE_ENABLED: bool = Field(default=True, description="Enable GDPR compliance")
    
    # Background Task Settings
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/0", description="Celery broker URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/0", description="Celery result backend")
    CELERY_TASK_TIMEOUT: int = Field(default=300, description="Celery task timeout (5 minutes)")
    
    # File Storage Settings
    MAX_FILE_SIZE: int = Field(default=50 * 1024 * 1024, description="Max file size (50MB)")
    ALLOWED_EXTENSIONS: List[str] = Field(default=[".pdf", ".doc", ".docx", ".jpg", ".png", ".dicom"], description="Allowed file extensions")
    UPLOAD_PATH: str = Field(default="/tmp/uploads", description="Upload path")
    
    # MinIO/S3 settings for document storage
    MINIO_URL: str = Field(default="http://localhost:9000", description="MinIO URL")
    MINIO_ACCESS_KEY: str = Field(default="minioadmin", description="MinIO access key")
    MINIO_SECRET_KEY: str = Field(default="minio123secure", description="MinIO secret key")
    MINIO_BUCKET_NAME: str = Field(default="healthcare-documents", description="MinIO bucket name")
    
    @field_validator("SECRET_KEY", "ENCRYPTION_KEY", "ENCRYPTION_SALT")
    @classmethod
    def validate_keys(cls, v):
        if len(v) < 16:
            raise ValueError("Security keys must be at least 16 characters")
        return v
    
    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v):
        allowed_envs = ["development", "staging", "production", "test"]
        if v not in allowed_envs:
            raise ValueError(f"Environment must be one of {allowed_envs}")
        return v
    
    @field_validator("OTEL_SAMPLE_RATE")
    @classmethod
    def validate_sample_rate(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("OTEL_SAMPLE_RATE must be between 0.0 and 1.0")
        return v
    
    @field_validator("CPU_ALERT_THRESHOLD", "MEMORY_ALERT_THRESHOLD", "DISK_ALERT_THRESHOLD")
    @classmethod
    def validate_alert_thresholds(cls, v):
        if not 0.0 <= v <= 100.0:
            raise ValueError("Alert thresholds must be between 0.0 and 100.0")
        return v
    
    @field_validator("PROMETHEUS_PORT")
    @classmethod
    def validate_prometheus_port(cls, v):
        if not 1024 <= v <= 65535:
            raise ValueError("PROMETHEUS_PORT must be between 1024 and 65535")
        return v
    
    @field_validator("ALLOWED_COUNTRIES")
    @classmethod
    def validate_country_codes(cls, v):
        if v:
            for code in v:
                if not isinstance(code, str) or len(code) != 2:
                    raise ValueError("Country codes must be 2-character strings")
        return v
    
    @field_validator("NER_CONFIDENCE_THRESHOLD")
    @classmethod
    def validate_ner_threshold(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("NER_CONFIDENCE_THRESHOLD must be between 0.0 and 1.0")
        return v
    
    @field_validator("CLINICAL_AI_TEMPERATURE")
    @classmethod
    def validate_ai_temperature(cls, v):
        if not 0.0 <= v <= 2.0:
            raise ValueError("CLINICAL_AI_TEMPERATURE must be between 0.0 and 2.0")
        return v
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"
    
    @property
    def is_testing(self) -> bool:
        return self.ENVIRONMENT == "test"
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"
    
    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL for migrations."""
        return self.DATABASE_URL.replace("+asyncpg", "")
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # Ignore extra fields from .env that aren't defined
    )

@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()