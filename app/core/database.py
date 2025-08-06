from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, String, Boolean, Text, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID, INET
from datetime import datetime
from typing import AsyncGenerator, Optional
import structlog
import uuid

from app.core.config import get_settings

logger = structlog.get_logger()

class Base(DeclarativeBase):
    """Base class for all database models."""
    pass

class BaseModel(Base):
    """Base model with common fields for audit and tracking."""
    __abstract__ = True
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    # Note: is_deleted and deleted_at fields are not in the actual migration

class AuditLog(BaseModel):
    """Immutable audit log entries for SOC2 compliance."""
    __tablename__ = "audit_logs"
    
    # Core audit fields
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    resource_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Event details
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    outcome: Mapped[str] = mapped_column(String(50), nullable=False)  # success, failure, error
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Detailed information
    event_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Security and integrity
    checksum: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    encrypted_payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Compliance fields
    retention_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    purge_hold: Mapped[bool] = mapped_column(Boolean, default=False)

class User(BaseModel):
    """User model for authentication and authorization."""
    __tablename__ = "users"
    
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # RBAC fields
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Security tracking
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Additional fields from migration
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    mfa_secret: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_login_ip: Mapped[Optional[str]] = mapped_column(INET, nullable=True)
    password_changed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False)
    is_system_user: Mapped[bool] = mapped_column(Boolean, default=False)

class IRISApiLog(BaseModel):
    """IRIS API interaction logging."""
    __tablename__ = "iris_api_logs"
    
    request_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    endpoint: Mapped[str] = mapped_column(String(500), nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    
    # Request/Response tracking
    status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    response_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Encrypted payloads (for security)
    encrypted_request: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    encrypted_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Error tracking
    error_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

class PurgePolicy(BaseModel):
    """Data retention and purge policies."""
    __tablename__ = "purge_policies"
    
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    retention_days: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Override conditions
    enable_legal_hold: Mapped[bool] = mapped_column(Boolean, default=True)
    enable_investigation_hold: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Purge configuration
    soft_delete_window_days: Mapped[int] = mapped_column(Integer, default=30)
    cascade_delete: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Metadata
    policy_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)

# Database engine and session management
# Lazy initialization to avoid module-level database connection
engine = None
AsyncSessionLocal = None

def get_engine():
    """Get or create the database engine."""
    global engine
    if engine is None:
        settings = get_settings()
        database_url = settings.DATABASE_URL
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
        elif database_url.startswith("sqlite://"):
            database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://")

        # Create engine with appropriate parameters based on database type
        if database_url.startswith("sqlite"):
            engine = create_async_engine(
                database_url,
                echo=settings.DEBUG,
                future=True
            )
        else:
            engine = create_async_engine(
                database_url,
                pool_size=settings.DATABASE_POOL_SIZE,
                max_overflow=settings.DATABASE_MAX_OVERFLOW,
                echo=settings.DEBUG,
                future=True
            )
    return engine

def get_session_factory():
    """Get or create the session factory."""
    global AsyncSessionLocal
    if AsyncSessionLocal is None:
        AsyncSessionLocal = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False
        )
    return AsyncSessionLocal

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error("Database session error", error=str(e))
            raise
        finally:
            await session.close()

async def init_db() -> None:
    """Initialize database tables."""
    try:
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise

async def close_db() -> None:
    """Close database connections."""
    engine = get_engine()
    await engine.dispose()
    logger.info("Database connections closed")