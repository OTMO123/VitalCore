#!/usr/bin/env python3
"""
Простая диагностика проблемы создания пациента
"""

import asyncio
import sys
import os
import traceback
import json
from datetime import datetime
sys.path.append('/mnt/c/Users/aurik/Code_Projects/2_scraper')

import logging

# Настройка простого логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

logger = logging.getLogger(__name__)

async def diagnose_patient_creation():
    """Диагностика проблемы создания пациента"""
    
    print("ДИАГНОСТИКА СОЗДАНИЯ ПАЦИЕНТА")
    print("=" * 50)
    
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
            "value": "DEBUG001"
        }],
        "name": [{
            "use": "official",
            "family": "TestPatient",
            "given": ["Debug"]
        }],
        "gender": "male",
        "birthDate": "1990-01-01",
        "active": True,
        "organization_id": "550e8400-e29b-41d4-a716-446655440000"
    }
    
    try:
        # ШАГ 1: Проверка импортов
        print("\nШАГ 1: Проверка импортов")
        try:
            from app.core.database_unified import get_db, Patient, DataClassification
            print("OK - database_unified импортирован")
        except Exception as e:
            print(f"ОШИБКА импорта database_unified: {e}")
            return False
            
        try:
            from app.core.security import SecurityManager
            print("OK - SecurityManager импортирован")
        except Exception as e:
            print(f"ОШИБКА импорта SecurityManager: {e}")
            return False
            
        # ШАГ 2: Проверка модели Patient
        print("\nШАГ 2: Анализ модели Patient")
        patient_fields = [attr for attr in dir(Patient) if not attr.startswith('_')]
        print(f"Поля модели Patient: {patient_fields}")
        
        # Проверяем наличие критических полей
        critical_fields = ['tenant_id', 'organization_id', 'external_id', 'mrn']
        missing_fields = []
        for field in critical_fields:
            if hasattr(Patient, field):
                print(f"OK - Поле {field} найдено")
            else:
                print(f"ПРОБЛЕМА - Поле {field} ОТСУТСТВУЕТ")
                missing_fields.append(field)
        
        if missing_fields:
            print(f"КРИТИЧЕСКАЯ ПРОБЛЕМА: Отсутствующие поля: {missing_fields}")
        
        # ШАГ 3: Проверка сервиса
        print("\nШАГ 3: Проверка PatientService")
        try:
            from app.modules.healthcare_records.service import PatientService
            print("OK - PatientService импортирован")
        except Exception as e:
            print(f"ОШИБКА импорта PatientService: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            return False
        
        # ШАГ 4: Тест создания пациента напрямую
        print("\nШАГ 4: Тест прямого создания в БД")
        async for session in get_db():
            try:
                security_manager = SecurityManager()
                
                # Создаем минимального пациента
                patient = Patient(
                    external_id=test_patient_data["identifier"][0]["value"],
                    mrn=f"MRN-{test_patient_data['identifier'][0]['value']}",
                    first_name_encrypted=security_manager.encrypt_data(test_patient_data["name"][0]["given"][0]),
                    last_name_encrypted=security_manager.encrypt_data(test_patient_data["name"][0]["family"]),
                    date_of_birth_encrypted=security_manager.encrypt_data(test_patient_data["birthDate"]),
                    data_classification="phi",  # использую строчными как в БД
                    consent_status={"status": "pending", "types": ["treatment"]}
                )
                
                session.add(patient)
                await session.commit()
                await session.refresh(patient)
                
                print(f"OK - Пациент создан напрямую в БД: {patient.id}")
                
                # Проверяем поля созданного пациента
                print("Поля созданного пациента:")
                for attr in ['id', 'external_id', 'mrn', 'created_at']:
                    if hasattr(patient, attr):
                        try:
                            value = getattr(patient, attr)
                            print(f"  {attr}: {value}")
                        except Exception as e:
                            print(f"  {attr}: ОШИБКА - {e}")
                
                # Проверяем проблемное поле tenant_id
                try:
                    tenant_id = getattr(patient, 'tenant_id', 'НЕ_НАЙДЕНО')
                    print(f"  tenant_id: {tenant_id}")
                except Exception as e:
                    print(f"  tenant_id: ОШИБКА ДОСТУПА - {e}")
                
            except Exception as e:
                print(f"ОШИБКА создания пациента: {e}")
                print(f"Traceback: {traceback.format_exc()}")
                return False
            
            break  # Выходим из цикла
        
        # ШАГ 5: Тест сервиса
        print("\nШАГ 5: Тест PatientService")
        try:
            from app.modules.healthcare_records.service import get_healthcare_service
            
            async for session in get_db():
                service = await get_healthcare_service(session=session)
                print("OK - Healthcare service создан")
                
                # Проверяем доступность patient_service
                if hasattr(service, 'patient_service'):
                    print("OK - patient_service найден в сервисе")
                else:
                    print("ПРОБЛЕМА - patient_service НЕ найден")
                
                break
            
        except Exception as e:
            print(f"ОШИБКА тестирования сервиса: {e}")
            print(f"Traceback: {traceback.format_exc()}")
        
        print("\n" + "=" * 50)
        print("ДИАГНОСТИКА ЗАВЕРШЕНА")
        return True
        
    except Exception as e:
        print(f"\nКРИТИЧЕСКАЯ ОШИБКА: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False

async def main():
    """Главная функция"""
    success = await diagnose_patient_creation()
    
    if success:
        print("\nДиагностика успешно завершена")
        return 0
    else:
        print("\nДиагностика выявила критические проблемы")
        return 1

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)