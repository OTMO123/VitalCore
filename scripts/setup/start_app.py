#!/usr/bin/env python3
"""
Start the IRIS API application with proper error handling and database setup.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def start_application():
    """Start the application with proper initialization."""
    print("🚀 Starting IRIS API Integration System...")
    print("=" * 60)
    
    try:
        # Check if required environment variables are set
        print("1. Checking environment configuration...")
        
        env_file = project_root / ".env"
        if not env_file.exists():
            print("❌ .env file not found")
            return False
        
        print("✅ .env file found")
        
        # Check database connectivity
        print("\n2. Testing database connectivity...")
        
        try:
            from app.core.config import get_settings
            settings = get_settings()
            print(f"✅ Database URL: {settings.DATABASE_URL}")
            
            # Test if we can create an engine without connecting
            from sqlalchemy.ext.asyncio import create_async_engine
            test_engine = create_async_engine(
                settings.DATABASE_URL,
                echo=False,
                pool_size=1,
                max_overflow=0,
                pool_pre_ping=True
            )
            
            # Try to connect
            async with test_engine.begin() as conn:
                result = await conn.execute("SELECT 1")
                print("✅ Database connection successful")
            
            await test_engine.dispose()
            
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            print("\n💡 Please ensure PostgreSQL is running:")
            print("   docker-compose up -d db")
            return False
        
        # Import and start the FastAPI app
        print("\n3. Starting FastAPI application...")
        
        try:
            from app.main import app
            print(f"✅ FastAPI app imported successfully")
            
            # Count routes
            route_count = len([route for route in app.routes if hasattr(route, 'methods')])
            print(f"✅ API has {route_count} endpoints configured")
            
        except Exception as e:
            print(f"❌ Failed to import FastAPI app: {e}")
            return False
        
        print("\n4. Application ready!")
        print("🌐 Server will start on: http://localhost:8000")
        print("📚 API Documentation: http://localhost:8000/docs")
        print("🏥 Health Check: http://localhost:8000/health")
        print("\n" + "=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Application startup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main entry point."""
    success = asyncio.run(start_application())
    
    if success:
        print("✅ Pre-flight checks passed! Starting server...")
        print("\nNow run:")
        print("uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    else:
        print("❌ Pre-flight checks failed. Fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()