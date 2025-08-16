#!/usr/bin/env python3
"""
Simplified performance test to verify basic functionality works
"""

import pytest
import asyncio
import time
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database_performance import DatabasePerformanceMonitor, DatabaseConfig
from app.core.security import EncryptionService
from app.core.database_unified import DataClassification
from app.modules.healthcare_records.models import Patient
from datetime import date
import uuid

@pytest.mark.asyncio
async def test_simple_patient_performance(db_session: AsyncSession):
    """Simple patient registration performance test"""
    print("Starting simple patient performance test...")
    
    # Create required services
    db_config = DatabaseConfig()
    monitor = DatabasePerformanceMonitor(db_config)
    encryption_service = EncryptionService()
    
    # Test basic patient creation with encryption
    start_time = time.time()
    
    try:
        # Create a single patient with encrypted fields
        patient_data = {
            "first_name": "John",
            "last_name": "Doe", 
            "date_of_birth": "1990-01-01",
            "mrn": f"TEST{uuid.uuid4().hex[:8]}"
        }
        
        print("Encrypting patient data...")
        patient = Patient(
            first_name_encrypted=await encryption_service.encrypt(patient_data["first_name"]),
            last_name_encrypted=await encryption_service.encrypt(patient_data["last_name"]),
            date_of_birth_encrypted=await encryption_service.encrypt(patient_data["date_of_birth"]),
            mrn=patient_data["mrn"],
            external_id=f"EXT_{patient_data['mrn']}",
            active=True,
            data_classification=DataClassification.PHI
        )
        
        print("Adding patient to database...")
        db_session.add(patient)
        await db_session.flush()
        
        elapsed = time.time() - start_time
        print(f"✅ Patient creation took {elapsed:.3f}s")
        
        # Basic performance assertions
        assert elapsed < 5.0, f"Patient creation took too long: {elapsed:.3f}s"
        assert patient.id is not None, "Patient should have an ID after flush"
        assert patient.mrn == patient_data["mrn"], "MRN should match"
        
        print("✅ Simple patient performance test passed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    asyncio.run(test_simple_patient_performance())