"""
Test Database Configuration
Cross-database compatibility settings for tests
"""

import os
from app.core.config import Settings

class TestConfig(Settings):
    """Test-specific configuration that ensures SQLite compatibility"""
    
    # Use SQLite for tests to avoid PostgreSQL dependency
    DATABASE_URL: str = "sqlite:///./test.db"
    
    # Override any PostgreSQL-specific settings
    ENVIRONMENT: str = "test"
    DEBUG: bool = True
    
    # Disable features that require PostgreSQL
    ENABLE_POSTGRES_FEATURES: bool = False
    
    class Config:
        env_file = ".env.test"

# Test database configuration
TEST_DATABASE_URL = "sqlite:///./test.db"

# Function to get test settings
def get_test_settings():
    """Get test-specific settings"""
    return TestSettings()
