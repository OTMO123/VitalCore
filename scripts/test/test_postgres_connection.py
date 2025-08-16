#!/usr/bin/env python3
"""
Test database connectivity before starting the application.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_database_connection():
    """Test PostgreSQL database connectivity."""
    print("🔍 Testing PostgreSQL Database Connection")
    print("=" * 50)
    
    try:
        # Import settings
        from app.core.config import get_settings
        settings = get_settings()
        
        print(f"📊 Database URL: {settings.DATABASE_URL}")
        print(f"🔧 Debug Mode: {settings.DEBUG}")
        
        # Test 1: Basic import test
        print("\n1. Testing imports...")
        try:
            import asyncpg
            print("✅ asyncpg driver available")
        except ImportError:
            print("❌ asyncpg driver not installed")
            print("💡 Install with: pip install asyncpg")
            return False
        
        try:
            from sqlalchemy.ext.asyncio import create_async_engine
            print("✅ SQLAlchemy async support available")
        except ImportError:
            print("❌ SQLAlchemy async not available")
            return False
        
        # Test 2: Engine creation
        print("\n2. Creating database engine...")
        try:
            engine = create_async_engine(
                settings.DATABASE_URL,
                echo=settings.DEBUG,
                pool_size=1,
                max_overflow=0,
                pool_pre_ping=True,
                pool_recycle=3600,
            )
            print("✅ Database engine created successfully")
        except Exception as e:
            print(f"❌ Failed to create engine: {e}")
            return False
        
        # Test 3: Database connection
        print("\n3. Testing database connection...")
        try:
            async with engine.begin() as conn:
                result = await conn.execute("SELECT version();")
                version = result.scalar()
                print(f"✅ Connected to PostgreSQL: {version}")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            print("\n💡 Troubleshooting steps:")
            print("   1. Check if PostgreSQL container is running:")
            print("      docker ps | grep postgres")
            print("   2. Start PostgreSQL if not running:")
            print("      docker-compose up -d db")
            print("   3. Wait 10 seconds for startup:")
            print("      Start-Sleep -Seconds 10")
            print("   4. Check container logs:")
            print("      docker logs 2_scraper-db-1")
            return False
        
        # Test 4: Database schema check
        print("\n4. Checking database schema...")
        try:
            async with engine.begin() as conn:
                # Check if users table exists
                result = await conn.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'users'
                    );
                """)
                users_table_exists = result.scalar()
                
                if users_table_exists:
                    print("✅ Users table exists")
                else:
                    print("⚠️  Users table not found - migrations may be needed")
                    print("💡 Run: alembic upgrade head")
                
                # Check if patients table exists
                result = await conn.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'patients'
                    );
                """)
                patients_table_exists = result.scalar()
                
                if patients_table_exists:
                    print("✅ Patients table exists")
                else:
                    print("⚠️  Patients table not found - migrations may be needed")
        
        except Exception as e:
            print(f"⚠️  Schema check failed: {e}")
            print("💡 This might be normal if migrations haven't been run")
        
        # Test 5: Clean up
        print("\n5. Cleaning up...")
        await engine.dispose()
        print("✅ Database engine disposed")
        
        print("\n" + "=" * 50)
        print("🎉 DATABASE CONNECTION TEST PASSED!")
        print("✅ PostgreSQL is ready for the application")
        return True
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main entry point."""
    success = asyncio.run(test_database_connection())
    
    if success:
        print("\n🚀 Ready to start the application!")
        print("Run: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    else:
        print("\n🔧 Fix the database issues above before starting the application")
        print("\nCommon fixes:")
        print("1. Start PostgreSQL: docker-compose up -d db")
        print("2. Wait for startup: Start-Sleep -Seconds 10")
        print("3. Run migrations: alembic upgrade head")
        print("4. Re-test: python test_postgres_connection.py")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)