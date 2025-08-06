#!/usr/bin/env python3
"""
Скрипт диагностики базы данных для IRIS API
Запустите в той же среде где работает uvicorn для диагностики проблем с БД
"""

import asyncio
import sys
import os
import traceback
from datetime import datetime

# Добавляем текущую директорию в path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def main():
    print("🔧 IRIS Database Diagnostic Tool")
    print("=" * 50)
    print(f"Timestamp: {datetime.now()}")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print()

    # 1. Проверка импортов
    print("📦 Checking imports...")
    try:
        import asyncpg
        print("✅ asyncpg imported successfully")
    except ImportError as e:
        print(f"❌ asyncpg import failed: {e}")
        return

    try:
        import sqlalchemy
        print(f"✅ sqlalchemy imported successfully (version: {sqlalchemy.__version__})")
    except ImportError as e:
        print(f"❌ sqlalchemy import failed: {e}")
        return

    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        print("✅ sqlalchemy async extensions imported")
    except ImportError as e:
        print(f"❌ sqlalchemy async import failed: {e}")
        return

    print()

    # 2. Проверка конфигурации
    print("⚙️ Checking configuration...")
    try:
        from app.core.config import get_settings
        settings = get_settings()
        print(f"✅ Settings loaded successfully")
        print(f"   DATABASE_URL: {settings.DATABASE_URL[:50]}...")
        print(f"   DEBUG: {settings.DEBUG}")
        print(f"   ENVIRONMENT: {settings.ENVIRONMENT}")
    except Exception as e:
        print(f"❌ Settings loading failed: {e}")
        traceback.print_exc()
        return

    print()

    # 3. Прямое тестирование подключения к PostgreSQL
    print("🗄️ Testing direct PostgreSQL connection...")
    try:
        # Извлекаем параметры из DATABASE_URL
        import re
        db_url = settings.DATABASE_URL
        if db_url.startswith("postgresql+asyncpg://"):
            db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
        
        # Тестируем подключение
        conn = await asyncpg.connect(db_url)
        await conn.execute("SELECT 1")
        version = await conn.fetchrow("SELECT version()")
        print(f"✅ Direct PostgreSQL connection successful")
        print(f"   PostgreSQL version: {version['version'][:80]}...")
        await conn.close()
    except Exception as e:
        print(f"❌ Direct PostgreSQL connection failed: {e}")
        print("   Possible issues:")
        print("   - PostgreSQL service not running")
        print("   - Wrong database URL in .env")
        print("   - Network connectivity issues")
        print("   - Database authentication failure")
        return

    print()

    # 4. Тестирование SQLAlchemy engine
    print("🔧 Testing SQLAlchemy async engine...")
    try:
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=True,  # Включаем SQL логирование
            pool_size=2,
            max_overflow=5
        )
        
        async with engine.begin() as conn:
            result = await conn.execute(sqlalchemy.text("SELECT current_database(), current_user"))
            row = result.fetchone()
            print(f"✅ SQLAlchemy engine connection successful")
            print(f"   Current database: {row[0]}")
            print(f"   Current user: {row[1]}")
        
        await engine.dispose()
    except Exception as e:
        print(f"❌ SQLAlchemy engine connection failed: {e}")
        traceback.print_exc()
        return

    print()

    # 5. Тестирование моделей базы данных
    print("📊 Testing database models...")
    try:
        from app.core.database_unified import User, Base
        print("✅ Database models imported successfully")
        print(f"   User table: {User.__tablename__}")
        print(f"   Base metadata tables: {len(Base.metadata.tables)}")
    except Exception as e:
        print(f"❌ Database models import failed: {e}")
        traceback.print_exc()
        return

    print()

    # 6. Проверка существования таблиц
    print("🏗️ Checking database tables...")
    try:
        engine = create_async_engine(settings.DATABASE_URL)
        
        async with engine.begin() as conn:
            # Проверяем какие таблицы существуют
            result = await conn.execute(sqlalchemy.text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in result.fetchall()]
            
            if tables:
                print(f"✅ Found {len(tables)} tables in database:")
                for table in tables:
                    print(f"   - {table}")
            else:
                print("⚠️ No tables found in database")
                print("   You may need to run: alembic upgrade head")
        
        await engine.dispose()
    except Exception as e:
        print(f"❌ Table check failed: {e}")
        traceback.print_exc()
        return

    print()

    # 7. Тестирование создания пользователя
    print("👤 Testing user creation (if tables exist)...")
    try:
        from app.core.database_unified import get_db
        from app.modules.auth.service import auth_service
        from app.modules.auth.schemas import UserCreate
        
        # Тестируем получение сессии БД
        async for db in get_db():
            print("✅ Database session created successfully")
            
            # Проверяем существование таблицы users
            result = await db.execute(sqlalchemy.text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'users'
                )
            """))
            
            table_exists = result.scalar()
            
            if table_exists:
                print("✅ Users table exists")
                
                # Проверяем количество пользователей
                result = await db.execute(sqlalchemy.text("SELECT COUNT(*) FROM users"))
                user_count = result.scalar()
                print(f"   Current user count: {user_count}")
                
            else:
                print("❌ Users table does not exist")
                print("   Run: alembic upgrade head")
            
            break
            
    except Exception as e:
        print(f"❌ User service test failed: {e}")
        traceback.print_exc()

    print()

    # 8. Итоговые рекомендации
    print("=" * 50)
    print("🎯 DIAGNOSTIC SUMMARY")
    print("=" * 50)
    print()
    print("If you're experiencing 500 errors during login:")
    print()
    print("1. ✅ Check PostgreSQL service is running:")
    print("   - Windows: services.msc -> PostgreSQL")
    print("   - Or check if port 5432/5433 is listening")
    print()
    print("2. ✅ Verify database connection in .env:")
    print("   - DATABASE_URL should match your PostgreSQL setup")
    print("   - Check username, password, host, port, database name")
    print()
    print("3. ✅ Run database migrations:")
    print("   - alembic upgrade head")
    print("   - This creates necessary tables")
    print()
    print("4. ✅ Check uvicorn startup logs:")
    print("   - Look for database connection errors")
    print("   - Look for table creation/migration errors")
    print()
    print("5. ✅ Test manual connection:")
    print("   - psql -h localhost -p 5432 -U test_user -d test_iris_db")
    print()
    print(f"Diagnostic completed at: {datetime.now()}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Diagnostic interrupted by user")
    except Exception as e:
        print(f"\n💥 Diagnostic failed: {e}")
        traceback.print_exc()