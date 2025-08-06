#!/usr/bin/env python3
"""
Исправление схемы базы данных - добавление недостающих колонок
"""

import asyncio
import sys
sys.path.append('/mnt/c/Users/aurik/Code_Projects/2_scraper')

import logging
from sqlalchemy import text
from app.core.database_unified import get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fix_database_schema():
    """Добавляем недостающие колонки в таблицу patients"""
    
    print("ИСПРАВЛЕНИЕ СХЕМЫ БАЗЫ ДАННЫХ")
    print("=" * 50)
    
    try:
        async for session in get_db():
            # Проверяем существующие колонки
            result = await session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'patients' 
                ORDER BY column_name;
            """))
            existing_columns = [row[0] for row in result.fetchall()]
            print(f"Существующие колонки: {existing_columns}")
            
            # Добавляем tenant_id если не существует
            if 'tenant_id' not in existing_columns:
                print("Добавляем колонку tenant_id...")
                await session.execute(text("""
                    ALTER TABLE patients 
                    ADD COLUMN tenant_id VARCHAR(255);
                """))
                print("OK - Колонка tenant_id добавлена")
            else:
                print("OK - Колонка tenant_id уже существует")
            
            # Добавляем organization_id если не существует
            if 'organization_id' not in existing_columns:
                print("Добавляем колонку organization_id...")
                await session.execute(text("""
                    ALTER TABLE patients 
                    ADD COLUMN organization_id VARCHAR(255);
                """))
                print("✅ Колонка organization_id добавлена")
            else:
                print("✅ Колонка organization_id уже существует")
            
            # Добавляем индексы
            print("Добавляем индексы...")
            try:
                await session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_patients_tenant_id 
                    ON patients(tenant_id);
                """))
                await session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_patients_organization_id 
                    ON patients(organization_id);
                """))
                print("✅ Индексы добавлены")
            except Exception as e:
                print(f"⚠️ Индексы уже существуют или ошибка: {e}")
            
            # Подтверждаем изменения
            await session.commit()
            print("✅ Изменения сохранены")
            
            # Проверяем обновленную схему
            result = await session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'patients' 
                ORDER BY column_name;
            """))
            updated_columns = [row[0] for row in result.fetchall()]
            print(f"Обновленные колонки: {updated_columns}")
            
            break
        
        return True
        
    except Exception as e:
        print(f"ОШИБКА: {e}")
        return False

async def main():
    success = await fix_database_schema()
    if success:
        print("\n✅ Схема базы данных успешно обновлена")
        return 0
    else:
        print("\n❌ Ошибка обновления схемы")
        return 1

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)