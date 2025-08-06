#!/usr/bin/env python3
"""
Create database tables using SQLAlchemy models.
"""
import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine

# Suppress SQLAlchemy logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

from app.core.database import Base
from app.core.config import get_settings

async def create_tables():
    """Create all tables using SQLAlchemy models."""
    print("Creating database tables...")
    
    settings = get_settings()
    # Convert to async URL if needed
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
    
    engine = create_async_engine(db_url, echo=False)
    
    try:
        async with engine.begin() as conn:
            # Create all tables defined in Base metadata
            await conn.run_sync(Base.metadata.create_all)
        
        print("[SUCCESS] All database tables created successfully")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to create tables: {e}")
        return False
    finally:
        await engine.dispose()

if __name__ == "__main__":
    success = asyncio.run(create_tables())
    exit(0 if success else 1)