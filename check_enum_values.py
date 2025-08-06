#!/usr/bin/env python3
"""
Проверка допустимых значений enum в базе данных
"""

import asyncio
import sys
sys.path.append('/mnt/c/Users/aurik/Code_Projects/2_scraper')

from sqlalchemy import text
from app.core.database_unified import get_db

async def check_enum_values():
    """Проверяем допустимые значения enum dataclassification"""
    
    print("ПРОВЕРКА ENUM ЗНАЧЕНИЙ")
    print("=" * 50)
    
    try:
        async for session in get_db():
            # Проверяем enum значения
            result = await session.execute(text("""
                SELECT enumlabel 
                FROM pg_enum 
                WHERE enumtypid = (
                    SELECT oid 
                    FROM pg_type 
                    WHERE typname = 'dataclassification'
                );
            """))
            enum_values = [row[0] for row in result.fetchall()]
            print(f"Допустимые значения enum dataclassification: {enum_values}")
            
            # Проверяем также через information_schema
            result = await session.execute(text("""
                SELECT column_name, udt_name, data_type
                FROM information_schema.columns 
                WHERE table_name = 'patients' 
                AND column_name = 'data_classification';
            """))
            
            for row in result.fetchall():
                print(f"Колонка: {row[0]}, Тип: {row[1]}, Data type: {row[2]}")
            
            break
            
    except Exception as e:
        print(f"ОШИБКА: {e}")

if __name__ == "__main__":
    asyncio.run(check_enum_values())