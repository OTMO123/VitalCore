#!/usr/bin/env python3
"""
Детальная диагностика проблемы создания пациента
Логирует каждый шаг процесса для выявления точной проблемы
"""

import asyncio
import sys
import os
import traceback
import json
from datetime import datetime
sys.path.append('/mnt/c/Users/aurik/Code_Projects/2_scraper')

import logging
from sqlalchemy.ext.asyncio import AsyncSession

# Настройка простого логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

logger = logging.getLogger(__name__)

async def detailed_patient_creation_diagnosis():
    """Подробная диагностика всего процесса создания пациента"""
    
    print("НАЧИНАЕМ ДЕТАЛЬНУЮ ДИАГНОСТИКУ СОЗДАНИЯ ПАЦИЕНТА")
    print("=" * 80)
    
    # Тестовые данные пациента
    test_patient_data = {
        "resourceType": "Patient",
        "identifier": [{
            "use": "official",
            "type": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                    "code": "MR"
                }]
            },
            "system": "http://hospital.smarthit.org",
            "value": "DIAG001"
        }],
        "name": [{
            "use": "official",
            "family": "DiagnosticTest",
            "given": ["Patient"]
        }],
        "gender": "male",
        "birthDate": "1990-01-01",
        "active": True,
        "organization_id": "550e8400-e29b-41d4-a716-446655440000"
    }
    
    try:
        # ===== ШАГ 1: ПРОВЕРКА ИМПОРТОВ =====
        print("\nШАГ 1: Проверка импортов и зависимостей")
        try:
            from app.core.database_unified import get_db, Patient, DataClassification
            print("✅ database_unified импортирован")
        except Exception as e:
            print(f"❌ Ошибка импорта database_unified: {e}")
            return False
            
        try:
            from app.core.security import SecurityManager
            print("✅ SecurityManager импортирован")
        except Exception as e:
            print(f"❌ Ошибка импорта SecurityManager: {e}")
            return False
            
        try:
            from app.modules.healthcare_records.service import PatientService
            print("✅ PatientService импортирован")
        except Exception as e:
            print(f"❌ Ошибка импорта PatientService: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            return False
            
        # ===== ШАГ 2: ПРОВЕРКА МОДЕЛИ PATIENT =====
        print("\n🗃️ ШАГ 2: Анализ модели Patient")
        patient_fields = [attr for attr in dir(Patient) if not attr.startswith('_')]
        print(f"📋 Поля модели Patient: {patient_fields}")
        
        # Проверяем наличие критических полей
        critical_fields = ['tenant_id', 'organization_id', 'external_id', 'mrn']
        for field in critical_fields:
            if hasattr(Patient, field):
                print(f"✅ Поле {field} найдено")
            else:
                print(f"❌ Поле {field} ОТСУТСТВУЕТ")
        
        # ===== ШАГ 3: ПРОВЕРКА ПОДКЛЮЧЕНИЯ К БД =====
        print("\n💾 ШАГ 3: Проверка подключения к базе данных")
        async for session in get_db():
            print("✅ Подключение к БД успешно")
            
            # Проверяем схему таблицы patients
            try:
                inspector = inspect(session.bind)
                if hasattr(inspector, 'get_columns'):
                    columns = inspector.get_columns('patients')
                    print(f"📊 Колонки таблицы patients: {[col['name'] for col in columns]}")
                else:
                    print("⚠️ Не удалось получить схему таблицы")
            except Exception as e:
                print(f"⚠️ Ошибка при проверке схемы: {e}")
            
            # ===== ШАГ 4: СОЗДАНИЕ SECURITY MANAGER =====
            print("\n🔐 ШАГ 4: Инициализация SecurityManager")
            try:
                security_manager = SecurityManager()
                print("✅ SecurityManager создан")
                
                # Тест шифрования
                test_data = "test_encryption"
                encrypted = security_manager.encrypt_data(test_data)
                print(f"✅ Тест шифрования прошел: {len(encrypted)} символов")
                
            except Exception as e:
                print(f"❌ Ошибка SecurityManager: {e}")
                print(f"Traceback: {traceback.format_exc()}")
                return False
            
            # ===== ШАГ 5: ИНИЦИАЛИЗАЦИЯ PATIENT SERVICE =====
            print("\n🏥 ШАГ 5: Создание PatientService")
            try:
                # Импортируем функцию создания сервиса
                from app.modules.healthcare_records.service import get_healthcare_service
                service = await get_healthcare_service(session=session)
                print("✅ PatientService создан через get_healthcare_service")
                
            except Exception as e:
                print(f"❌ Ошибка создания PatientService: {e}")
                print(f"Traceback: {traceback.format_exc()}")
                
                # Пробуем создать напрямую
                try:
                    patient_service = PatientService(session)
                    print("✅ PatientService создан напрямую")
                except Exception as e2:
                    print(f"❌ Ошибка прямого создания: {e2}")
                    return False
            
            # ===== ШАГ 6: СОЗДАНИЕ КОНТЕКСТА =====
            print("\n👤 ШАГ 6: Создание AccessContext")
            try:
                from app.modules.healthcare_records.service import AccessContext
                context = AccessContext(
                    user_id="test-user-id",
                    purpose="treatment",
                    role="admin",
                    ip_address="127.0.0.1",
                    session_id="test-session"
                )
                print("✅ AccessContext создан")
                print(f"📋 Контекст: {context.__dict__}")
                
            except Exception as e:
                print(f"❌ Ошибка создания AccessContext: {e}")
                print(f"Traceback: {traceback.format_exc()}")
                # Продолжаем без контекста
                context = None
            
            # ===== ШАГ 7: ПОПЫТКА СОЗДАНИЯ ПАЦИЕНТА ЧЕРЕЗ СЕРВИС =====
            print("\n🏗️ ШАГ 7: Создание пациента через PatientService")
            try:
                print(f"📨 Входные данные: {json.dumps(test_patient_data, indent=2)}")
                
                # Вызываем create_patient
                if context:
                    result = await service.patient_service.create_patient(test_patient_data, context)
                else:
                    print("⚠️ Создаем без контекста")
                    result = await service.patient_service.create_patient(test_patient_data)
                
                print(f"✅ Пациент создан через сервис: {result}")
                
            except Exception as e:
                print(f"❌ ОШИБКА ПРИ СОЗДАНИИ ЧЕРЕЗ СЕРВИС: {e}")
                print(f"🔍 Полный traceback:")
                print(traceback.format_exc())
                
                # ===== ШАГ 8: ПРЯМОЕ СОЗДАНИЕ В БД =====
                print("\n🔧 ШАГ 8: Попытка прямого создания в БД")
                try:
                    # Создаем минимального пациента
                    patient = Patient(
                        external_id=test_patient_data["identifier"][0]["value"],
                        mrn=f"MRN-{test_patient_data['identifier'][0]['value']}",
                        first_name_encrypted=security_manager.encrypt_data(test_patient_data["name"][0]["given"][0]),
                        last_name_encrypted=security_manager.encrypt_data(test_patient_data["name"][0]["family"]),
                        date_of_birth_encrypted=security_manager.encrypt_data(test_patient_data["birthDate"]),
                        data_classification="phi",
                        consent_status={"status": "pending", "types": ["treatment"]}
                    )
                    
                    session.add(patient)
                    await session.commit()
                    await session.refresh(patient)
                    
                    print(f"✅ Пациент создан напрямую в БД: {patient.id}")
                    
                    # Проверяем поля созданного пациента
                    print("📋 Поля созданного пациента:")
                    for attr in dir(patient):
                        if not attr.startswith('_') and hasattr(patient, attr):
                            try:
                                value = getattr(patient, attr)
                                if not callable(value):
                                    print(f"  {attr}: {value}")
                            except Exception:
                                print(f"  {attr}: <не удалось получить значение>")
                    
                except Exception as e2:
                    print(f"❌ ОШИБКА ПРЯМОГО СОЗДАНИЯ: {e2}")
                    print(f"🔍 Traceback: {traceback.format_exc()}")
                    return False
            
            break  # Выходим из цикла async for
        
        print("\n" + "=" * 80)
        print("🎯 ДИАГНОСТИКА ЗАВЕРШЕНА")
        return True
        
    except Exception as e:
        print(f"\n💥 КРИТИЧЕСКАЯ ОШИБКА ДИАГНОСТИКИ: {e}")
        print(f"🔍 Traceback: {traceback.format_exc()}")
        return False

async def main():
    """Главная функция"""
    success = await detailed_patient_creation_diagnosis()
    
    if success:
        print("\n✅ Диагностика успешно завершена")
        return 0
    else:
        print("\n❌ Диагностика выявила критические проблемы")
        return 1

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)