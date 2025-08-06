#!/bin/bash
# Quick Database Fix for 100% Backend Reliability

echo "🚀 Quick Database Fix for 100% Backend Reliability"
echo "=================================================="

# Method 1: Try Docker
echo "📦 Method 1: Starting PostgreSQL with Docker..."
echo "Command to run in PowerShell:"
echo "docker-compose up -d db redis"
echo ""

# Method 2: SQLite Fallback
echo "🔄 Method 2: SQLite Fallback (if Docker fails)..."

# Backup original config
cp app/core/config.py app/core/config.py.backup

# Create SQLite config
cat > app/core/config.py.sqlite << 'EOF'
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, ConfigDict
from typing import List, Optional
from functools import lru_cache
import secrets

class Settings(BaseSettings):
    """Application settings with SQLite for demo."""
    
    # Application
    DEBUG: bool = Field(default=True, description="Debug mode")
    ENVIRONMENT: str = Field(default="development", description="Environment")
    
    # Security
    SECRET_KEY: str = Field(default="demo-secret-key-32-characters-long")
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Token expiry")
    
    # Database - SQLite for demo
    DATABASE_URL: str = Field(
        default="sqlite:///./demo_app.db",
        description="SQLite database for demo"
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
    
    # Encryption
    ENCRYPTION_KEY: str = Field(
        default="demo-encryption-key-32-chars-long",
        description="Data encryption key"
    )
    ENCRYPTION_SALT: str = Field(
        default="demo-salt-16-chars",
        description="Encryption salt for key derivation"
    )
    
    # Audit Logging
    AUDIT_LOG_RETENTION_DAYS: int = Field(default=2555, description="7 years retention")
    AUDIT_LOG_ENCRYPTION: bool = Field(default=True, description="Encrypt audit logs")
    
    # Add other fields from original...
    model_config = ConfigDict(env_file=".env", case_sensitive=True)

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
EOF

echo "✅ SQLite config created"
echo ""

# Method 3: Instructions
echo "📋 INSTRUCTIONS:"
echo "================"
echo ""
echo "🔥 OPTION A (Recommended): Use Docker"
echo "In PowerShell run:"
echo "  docker-compose up -d db redis"
echo "  Wait 30 seconds for DB to start"
echo "  alembic upgrade head"
echo "  ./restart_backend.sh"
echo ""
echo "🔥 OPTION B: Use SQLite (if Docker fails)"
echo "  mv app/core/config.py.sqlite app/core/config.py"
echo "  ./restart_backend.sh"
echo "  # SQLite will auto-create tables"
echo ""
echo "🔥 OPTION C: Quick Test"
echo "  ./tests/100_percent_api_test.sh"
echo "  # Should show improvement after database fix"
echo ""
echo "💡 After any option, run: ./tests/100_percent_api_test.sh"