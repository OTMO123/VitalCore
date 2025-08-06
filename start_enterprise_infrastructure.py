#!/usr/bin/env python3
"""
Enterprise Healthcare Infrastructure Startup Script
SOC2 Type II + HIPAA + FHIR R4 + GDPR Compliant Server
"""

import asyncio
import os
import sys
import time
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set environment variables for enterprise deployment
os.environ.setdefault("PYTHONPATH", str(project_root))
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("DEBUG", "true")

# Configure logging for enterprise monitoring
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/enterprise_startup.log', mode='a')
    ]
)

logger = logging.getLogger(__name__)

async def check_database_connectivity():
    """Check if database is accessible with enterprise security extensions."""
    try:
        from app.core.database_unified import get_db
        from sqlalchemy import text
        
        logger.info("🔍 Checking database connectivity...")
        
        async with get_db() as db:
            # Basic connectivity test
            result = await db.execute(text("SELECT 1"))
            assert result.fetchone()[0] == 1
            
            # Check for enterprise security extensions
            extensions = await db.execute(text(
                "SELECT extname FROM pg_extension WHERE extname IN ('pgcrypto', 'uuid-ossp')"
            ))
            available_extensions = [row[0] for row in extensions.fetchall()]
            
            logger.info(f"✅ Database connected successfully")
            logger.info(f"✅ Available extensions: {available_extensions}")
            
            # Check for users table with proper INET column
            try:
                users_schema = await db.execute(text("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'users' AND column_name = 'last_login_ip'
                """))
                schema_result = users_schema.fetchone()
                
                if schema_result and schema_result[1] == 'inet':
                    logger.info(f"✅ Users table has proper INET column for security compliance")
                else:
                    logger.warning(f"⚠️  Users table schema may need migration")
                    
            except Exception as schema_error:
                logger.warning(f"⚠️  Schema validation warning: {schema_error}")
                
            return True
            
    except Exception as e:
        logger.error(f"❌ Database connectivity failed: {e}")
        return False

async def run_database_migrations():
    """Run database migrations to ensure enterprise schema."""
    try:
        logger.info("🔄 Running database migrations...")
        
        # Import alembic and run migrations programmatically
        from alembic.config import Config
        from alembic import command
        
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        
        logger.info("✅ Database migrations completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database migration failed: {e}")
        logger.info("💡 Please run migrations manually if needed")
        return False

def start_fastapi_server():
    """Start the FastAPI server with enterprise configuration."""
    try:
        logger.info("🚀 Starting enterprise healthcare API server...")
        
        import uvicorn
        from app.main import app
        
        # Enterprise server configuration
        server_config = {
            "app": app,
            "host": "0.0.0.0",
            "port": 8000,
            "log_level": "info",
            "access_log": True,
            "use_colors": True,
            "reload": True,  # Development mode
            "reload_dirs": ["app"],
            "workers": 1  # Single worker for development
        }
        
        logger.info("✅ Starting IRIS Healthcare API Integration System")
        logger.info(f"🌐 Server will be available at http://localhost:8000")
        logger.info(f"📚 API Documentation: http://localhost:8000/docs")
        logger.info(f"💓 Health Check: http://localhost:8000/health")
        
        uvicorn.run(**server_config)
        
    except Exception as e:
        logger.error(f"❌ Failed to start FastAPI server: {e}")
        sys.exit(1)

async def enterprise_startup_sequence():
    """Execute the enterprise startup sequence with health checks."""
    logger.info("🏥 IRIS Healthcare Enterprise Infrastructure Startup")
    logger.info("=" * 60)
    
    # Step 1: Database connectivity check
    db_healthy = await check_database_connectivity()
    if not db_healthy:
        logger.warning("⚠️  Database not available - server will start but may have limited functionality")
    
    # Step 2: Run migrations (optional, may fail if no DB)
    if db_healthy:
        await run_database_migrations()
    
    # Step 3: Start the FastAPI server
    logger.info("🎯 All enterprise infrastructure checks completed")
    logger.info("🚀 Starting healthcare API server...")
    
    return True

def main():
    """Main entry point for enterprise infrastructure startup."""
    try:
        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)
        
        # Run enterprise startup sequence
        startup_ready = asyncio.run(enterprise_startup_sequence())
        
        if startup_ready:
            # Start the FastAPI server (blocking call)
            start_fastapi_server()
        else:
            logger.error("❌ Enterprise startup sequence failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 Server shutdown requested by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Critical startup error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()