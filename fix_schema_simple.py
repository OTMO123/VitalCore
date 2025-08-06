#!/usr/bin/env python3
"""
Простое исправление схемы базы данных
"""

import asyncio
import sys
sys.path.append('/mnt/c/Users/aurik/Code_Projects/2_scraper')

import logging
from sqlalchemy import text
from app.core.database_unified import get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fix_schema():
    """Добавляем недостающие колонки"""
    
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
            
            changes_made = False
            
            # Добавляем tenant_id если не существует
            if 'tenant_id' not in existing_columns:
                print("Добавляем колонку tenant_id...")
                await session.execute(text("""
                    ALTER TABLE patients 
                    ADD COLUMN tenant_id VARCHAR(255);
                """))
                changes_made = True
                print("OK - tenant_id добавлена")
            else:
                print("OK - tenant_id уже существует")
            
            # Добавляем organization_id если не существует
            if 'organization_id' not in existing_columns:
                print("Добавляем колонку organization_id...")
                await session.execute(text("""
                    ALTER TABLE patients 
                    ADD COLUMN organization_id VARCHAR(255);
                """))
                changes_made = True
                print("OK - organization_id добавлена")
            else:
                print("OK - organization_id уже существует")
            
            if changes_made:
                # Подтверждаем изменения
                await session.commit()
                print("OK - Изменения сохранены")
                
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
                    await session.commit()
                    print("OK - Индексы добавлены")
                except Exception as e:
                    print(f"WARNING - Ошибка с индексами: {e}")
            
            # Проверяем финальную схему
            result = await session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'patients' 
                ORDER BY column_name;
            """))
            final_columns = [row[0] for row in result.fetchall()]
            print(f"Финальные колонки: {final_columns}")
            
            # Проверяем наличие нужных полей
            required_fields = ['tenant_id', 'organization_id']
            missing = [f for f in required_fields if f not in final_columns]
            if missing:
                print(f"ОШИБКА - Отсутствуют поля: {missing}")
                return False
            else:
                print("OK - Все нужные поля присутствуют")
                return True
            
            break
        
    except Exception as e:
        print(f"ОШИБКА: {e}")
        return False

async def main():
    success = await fix_schema()
    if success:
        print("\nScheme successfully updated")
        return 0
    else:
        print("\nError updating schema")
        return 1

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)